"""
AI Service: Handles user queries in natural conversational Hindi & English.
Integrates with Google Gemini API when GEMINI_API_KEY is available,
and provides a robust, transparent, rule-based expert engine when in demo mode.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from services.scheme_service import SchemeService


@dataclass
class SchemeSaathiResponse:
    mode: str  # "gemini_ai" | "demo_rule_based"
    reply_hi: str  # Conversational Hindi reply
    reply_en: str  # Conversational English reply
    follow_up_question_hi: Optional[str]
    follow_up_question_en: Optional[str]
    recommended_schemes: List[Dict[str, Any]]
    checklist_hi: List[str]
    checklist_en: List[str]
    missing_info_hi: List[str]
    missing_info_en: List[str]
    official_verification_needed: List[str]
    disclaimer_hi: str
    disclaimer_en: str
    is_unknown_domain: bool
    current_lang: str = "hi"

    @property
    def reply(self) -> str:
        return self.reply_en if self.current_lang == "en" else self.reply_hi

    @property
    def follow_up_question(self) -> Optional[str]:
        return self.follow_up_question_en if self.current_lang == "en" else self.follow_up_question_hi

    @property
    def checklist(self) -> List[str]:
        return self.checklist_en if self.current_lang == "en" else self.checklist_hi

    @property
    def missing_info(self) -> List[str]:
        return self.missing_info_en if self.current_lang == "en" else self.missing_info_hi

    @property
    def disclaimer(self) -> str:
        return self.disclaimer_en if self.current_lang == "en" else self.disclaimer_hi


class AIService:
    def __init__(self, scheme_service: Optional[SchemeService] = None):
        self.scheme_service = scheme_service or SchemeService()
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[AIService] Warning: Could not initialize Gemini Client: {e}")
                self.client = None

    def is_ai_available(self) -> bool:
        return self.client is not None and bool(self.api_key)

    def get_current_mode(self, lang: str = "hi") -> str:
        if self.is_ai_available():
            return f"🤖 Gemini AI ({self.model_name})"
        return "⚡ Smart Demo Mode" if lang == "en" else "⚡ स्मार्ट डेमो मोड (नियम आधारित)"

    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detects if user message is predominantly Hindi (Devanagari) or English (Latin).
        """
        devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
        latin_chars = len(re.findall(r"[a-zA-Z]", text))
        if devanagari_chars > latin_chars:
            return "hi"
        if latin_chars > 5:
            return "en"
        return "hi"

    def process_query(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        gathered_facts: Optional[Dict[str, Any]] = None,
        preferred_lang: Optional[str] = None
    ) -> SchemeSaathiResponse:
        """
        Main entry point for processing user queries. Supports preferred_lang ("hi" or "en").
        """
        user_message = user_message.strip() if user_message else ""
        gathered_facts = gathered_facts or {}
        conversation_history = conversation_history or []

        # Determine target language: explicit preference or detected
        lang = preferred_lang or self.detect_language(user_message)

        # If Gemini is available, attempt AI processing
        if self.is_ai_available():
            try:
                ai_resp = self._call_gemini(user_message, conversation_history, gathered_facts, lang)
                if ai_resp:
                    return ai_resp
            except Exception as e:
                print(f"[AIService] Gemini API error, falling back to Demo engine: {e}")

        # Transparent rule-based demo engine
        return self._run_demo_engine(user_message, conversation_history, gathered_facts, lang)

    def _call_gemini(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        gathered_facts: Dict[str, Any],
        lang: str
    ) -> Optional[SchemeSaathiResponse]:
        """
        Calls official Google GenAI SDK with grounded context from verified schemes.
        """
        schemes = self.scheme_service.get_all_schemes()
        schemes_context = []
        for s in schemes:
            schemes_context.append({
                "id": s["id"],
                "name": s["name"],
                "name_hi": s["name_hi"],
                "purpose": s.get("purpose", ""),
                "purpose_hi": s["purpose_hi"],
                "benefits": s.get("benefits", []),
                "benefits_hi": s["benefits_hi"],
                "eligibility": s.get("eligibility", []),
                "eligibility_hi": s["eligibility_hi"],
                "exclusions": s.get("exclusions", []),
                "required_documents": s.get("required_documents", []),
                "application_steps": s.get("application_steps", []),
                "official_source": s.get("official_source", ""),
                "helpline": s.get("helpline", ""),
                "last_verified": s.get("last_verified", "")
            })

        system_instruction = (
            f"You are Scheme Saathi (स्कीम साथी), an empathetic, truthful AI assistant helping Indian citizens "
            f"understand government welfare schemes in simple, conversational language.\n"
            f"Current target language is: {'English' if lang == 'en' else 'Hindi'}.\n"
            f"CRITICAL RULES:\n"
            f"1. Ground recommendations ONLY in the provided verified schemes database. Never fabricate rules or schemes.\n"
            f"2. Never guarantee eligibility or benefit disbursement. Always state that final approval depends on official government verification.\n"
            f"3. If query is out of scope (e.g. theft, private dispute, passport), state limits politely and direct to official myScheme portal (https://www.myscheme.gov.in/).\n"
            f"4. Ask AT MOST ONE concise follow-up question if essential info is missing.\n"
            f"5. Return both Hindi and English fields in the JSON response.\n"
        )

        prompt = f"""
Official Schemes Database:
{json.dumps(schemes_context, ensure_ascii=False, indent=2)}

Known User Facts:
{json.dumps(gathered_facts, ensure_ascii=False)}

User Input:
"{user_message}"

Generate a valid JSON object matching this schema:
{{
  "reply_hi": "Conversational Hindi explanation",
  "reply_en": "Conversational English explanation",
  "matched_scheme_ids": ["list", "of", "ids"],
  "follow_up_question_hi": "One question in Hindi or null",
  "follow_up_question_en": "One question in English or null",
  "missing_info_hi": ["list in Hindi"],
  "missing_info_en": ["list in English"],
  "checklist_hi": ["steps in Hindi"],
  "checklist_en": ["steps in English"],
  "official_verification_needed": ["verification steps"],
  "is_unknown_domain": false
}}
"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        )

        if not response or not response.text:
            return None

        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        data = json.loads(text)
        matched_ids = data.get("matched_scheme_ids", [])
        recommended_schemes = []
        for sid in matched_ids:
            scheme = self.scheme_service.get_scheme_by_id(sid)
            if scheme:
                assessment = self.scheme_service.assess_eligibility(scheme, gathered_facts)
                rec = dict(scheme)
                rec["assessment"] = assessment
                recommended_schemes.append(rec)

        disclaimer_hi = (
            "⚠️ महत्वपूर्ण सूचना: यह केवल एक प्रारंभिक मार्गदर्शन है। "
            "अंतिम पात्रता, सत्यापन और लाभ की स्वीकृति संबंधित सरकारी विभाग या बैंक के आधिकारिक नियमों के अधीन है।"
        )
        disclaimer_en = (
            "⚠️ Important Notice: Scheme Saathi provides preliminary guidance only. "
            "Final eligibility and benefit approval depend strictly on the relevant government department."
        )

        return SchemeSaathiResponse(
            mode=f"🤖 Gemini AI ({self.model_name})",
            reply_hi=data.get("reply_hi", ""),
            reply_en=data.get("reply_en", data.get("reply_hi", "")),
            follow_up_question_hi=data.get("follow_up_question_hi"),
            follow_up_question_en=data.get("follow_up_question_en"),
            recommended_schemes=recommended_schemes,
            checklist_hi=data.get("checklist_hi", []),
            checklist_en=data.get("checklist_en", []),
            missing_info_hi=data.get("missing_info_hi", []),
            missing_info_en=data.get("missing_info_en", []),
            official_verification_needed=data.get("official_verification_needed", ["भूमि खसरा-खतौनी", "Aadhaar Bank Seeding"]),
            disclaimer_hi=disclaimer_hi,
            disclaimer_en=disclaimer_en,
            is_unknown_domain=data.get("is_unknown_domain", False),
            current_lang=lang
        )

    def _run_demo_engine(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        gathered_facts: Dict[str, Any],
        lang: str = "hi"
    ) -> SchemeSaathiResponse:
        """
        Deterministic, intelligent rule-based engine covering all primary scenarios in Hindi and English.
        """
        search_results = self.scheme_service.search_schemes(user_message, gathered_facts)
        msg_lower = user_message.lower()
        updated_facts = dict(gathered_facts)

        # Detect crop damage
        if any(w in msg_lower for w in ["बारिश", "ओला", "नुकसान", "खराब", "बाढ़", "सूखा", "बरसात", "crop", "damage", "rain", "ruined", "destroyed"]):
            updated_facts["has_crop_damage"] = True

        # Detect land ownership
        if any(w in msg_lower for w in ["मेरी जमीन", "खुद की जमीन", "खतौनी", "जमीन है", "own land", "landowner", "land registered"]):
            updated_facts["is_landowner"] = True
        elif any(w in msg_lower for w in ["जमीन नहीं है", "भूमिहीन", "किराए पर", "landless", "tenant"]):
            updated_facts["is_landowner"] = False

        # Detect insurance status
        if any(w in msg_lower for w in ["बीमा कराया था", "बीमा है", "प्रीमियम कटा था", "insured", "have insurance"]):
            updated_facts["is_insured"] = True
        elif any(w in msg_lower for w in ["बीमा नहीं है", "बीमा नहीं कराया", "not insured", "no insurance"]):
            updated_facts["is_insured"] = False

        # Scenario C: Unknown Problem / Domain
        unknown_indicators = [
            "चोरी", "दुकान", "पासपोर्ट", "पुलिस", "विवाद", "झगड़ा", "कोर्ट", "गाड़ी चोरी", "व्यापार",
            "theft", "shop", "burglar", "passport", "police", "stolen", "robbery", "stole", "business loss"
        ]
        has_unknown = any(ind in msg_lower for ind in unknown_indicators) and not any(k in msg_lower for k in ["फसल", "किसान", "खेती", "आवास", "इलाज", "मनरेगा", "crop", "farmer", "farm", "kisan"])

        if has_unknown or not search_results:
            myscheme = self.scheme_service.get_myscheme_info()
            reply_hi = (
                "नमस्ते भाई जी। आपकी बताई गई समस्या को मैंने समझा। "
                "वर्तमान में मेरी जानकारी मुख्य रूप से केंद्र व राज्य सरकार की ग्रामीण व कृषि कल्याण योजनाओं "
                "(जैसे फसल बीमा, किसान सम्मान निधि, आयुष्मान स्वास्थ्य योजना, ग्रामीण आवास और मनरेगा) तक सीमित है।\n\n"
                "आपकी इस समस्या के लिए हमारे मौजूदा डेटाबेस में कोई सीधी योजना दर्ज नहीं है। "
                "कृपया निराश न हों — भारत सरकार के आधिकारिक **myScheme पोर्टल** पर 750 से अधिक योजनाएं उपलब्ध हैं, "
                "जहाँ आप अपनी श्रेणी चुनकर सही सरकारी मदद खोज सकते हैं।"
            )
            reply_en = (
                "Hello. I understand the issue you described. "
                "Currently, Scheme Saathi specializes in agricultural and rural welfare programs "
                "(such as Crop Insurance, PM-KISAN, Ayushman Bharat health insurance, rural housing, and MGNREGA).\n\n"
                "Your specific issue is not covered in our current localized dataset. "
                "However, you can explore over 750+ central and state schemes on the Government of India's official **myScheme Portal**."
            )
            checklist_hi = [
                "भारत सरकार के आधिकारिक 'myScheme' पोर्टल (https://www.myscheme.gov.in/) पर जाएं।",
                "'Find Schemes Based on You' (अपने लिए योजना खोजें) पर क्लिक करें।",
                "अपनी आयु, राज्य, जाति, और व्यवसाय का विवरण दर्ज करें।",
                "यदि यह आपराधिक मामला (जैसे चोरी) है, तो सर्वप्रथम निकटतम पुलिस थाने में प्राथमिकी (FIR) दर्ज कराएं।"
            ]
            checklist_en = [
                "Visit the Government of India's official myScheme portal (https://www.myscheme.gov.in/).",
                "Click on 'Find Schemes Based on You'.",
                "Enter your state, gender, age, and occupation to view tailored schemes.",
                "If this involves theft or criminal activity, file an FIR at your nearest police station first."
            ]

            return SchemeSaathiResponse(
                mode="⚡ Smart Demo Mode" if lang == "en" else "⚡ स्मार्ट डेमो मोड (Rule-Based Expert Engine)",
                reply_hi=reply_hi,
                reply_en=reply_en,
                follow_up_question_hi="क्या आपकी समस्या कृषि, स्वास्थ्य, मकान, या ग्रामीण मजदूरी से भी जुड़ी है?",
                follow_up_question_en="Is your query related to farming, healthcare, rural housing, or employment?",
                recommended_schemes=[],
                checklist_hi=checklist_hi,
                checklist_en=checklist_en,
                missing_info_hi=["क्या आप ग्रामीण या शहरी क्षेत्र से हैं?"],
                missing_info_en=["Are you looking for rural or urban welfare schemes?"],
                official_verification_needed=["पुलिस प्राथमिकी (FIR) अथवा संबंधित विभागीय कार्यालय"],
                disclaimer_hi="⚠️ महत्वपूर्ण सूचना: स्कीम साथी एक मार्गदर्शन सहायक है। अंतिम स्वीकृति अधिकृत सरकारी विभाग द्वारा ही तय की जाती है।",
                disclaimer_en="⚠️ Important Notice: Scheme Saathi provides advisory guidance only. Final decisions rest strictly with government authorities.",
                is_unknown_domain=True,
                current_lang=lang
            )

        # Matched schemes
        recommended_schemes = []
        for scheme, score in search_results[:2]:
            assessment = self.scheme_service.assess_eligibility(scheme, updated_facts)
            rec = dict(scheme)
            rec["assessment"] = assessment
            recommended_schemes.append(rec)

        top_scheme = recommended_schemes[0]
        top_id = top_scheme["id"]

        # Craft replies based on top scheme
        if top_id == "pmfby":
            reply_hi = (
                f"राम-राम भाई जी। आपकी बात सुनकर दुख हुआ कि आपकी फसल को नुकसान पहुंचा है।\n\n"
                f"इसके लिए केंद्र सरकार की **{top_scheme['name_hi']}** आपके काम आ सकती है। "
                f"इस योजना के तहत बेमौसम बारिश, ओलावृष्टि या जलभराव से हुए नुकसान की भरपाई का प्रावधान है।\n\n"
                f"⚠️ **अति आवश्यक ध्यान दें:** यदि बारिश या ओले से स्थानीय स्तर पर नुकसान हुआ है, "
                f"तो घटना के **72 घंटे (3 दिन) के भीतर** बीमा कंपनी, बैंक, या टोल-फ्री नंबर 14447 पर सूचना देना अनिवार्य होता है। "
                f"कृपया ध्यान रखें कि यह सहायता स्वचालित या गारंटीकृत नहीं है — नुकसान की भरपाई तभी होगी जब फसल बीमाकृत हो और सर्वे में नुकसान प्रमाणित हो।"
            )
            reply_en = (
                f"Greetings. I am sorry to hear about your crop damage.\n\n"
                f"The Government of India's **{top_scheme['name']} (PMFBY)** covers financial losses "
                f"arising from unforeseen natural calamities like unseasonal heavy rain, hailstorms, and waterlogging.\n\n"
                f"⚠️ **CRITICAL 72-HOUR RULE:** For localized natural calamities, intimation of loss **MUST be reported within 72 hours** "
                f"of the event to toll-free helpline **14447**, via the 'Crop Insurance App', or at your local bank branch. "
                f"Please note: Benefit approval is not guaranteed — it requires active crop insurance coverage and official joint field survey verification."
            )
            follow_up_hi = "आपकी फसल किस राज्य और ज़िले में है, तथा क्या आपने इस चालू मौसम में फसल का बीमा (PMFBY या KCC के माध्यम से) कराया था?"
            follow_up_en = "Which state and district is your farm located in, and was this crop insured under PMFBY or through a bank KCC for the current season?"
            checklist_hi = [
                "तुरंत टोल-फ्री हेल्पलाइन 14447 पर कॉल करें या 'Crop Insurance App' पर नुकसान दर्ज कराएं (72 घंटे के अंदर)।",
                "अपने खेत में फसल के नुकसान और जलभराव की स्पष्ट तस्वीरें अपने मोबाइल से खींचें।",
                "अपनी बैंक पासबुक, आधार कार्ड और खसरा-खतौनी की प्रति तैयार रखें।",
                "अपने गाँव के पटवारी, ग्राम सेवक अथवा ब्लॉक कृषि अधिकारी से संपर्क कर संयुक्त सर्वे (Field Survey) की जानकारी लें।"
            ]
            checklist_en = [
                "Immediately notify within 72 hours via Toll-Free Helpline 14447 or the official 'Crop Insurance App'.",
                "Capture clear, timestamped photos of the damaged standing or harvested crop.",
                "Keep your Khasra-Khatauni land record, bank passbook, and Aadhaar card ready.",
                "Coordinate with your local Agriculture Officer or Patwari for joint field verification."
            ]
            missing_info_hi = ["राज्य और ज़िला", "फसल बीमा पॉलिसी नंबर / बैंक केसीसी", "नुकसान की सटीक तारीख"]
            missing_info_en = ["State and District", "Crop Insurance policy / KCC details", "Exact date and time of loss"]

        elif top_id == "pm_kisan":
            reply_hi = (
                f"नमस्ते किसान भाई। खेती-बाड़ी में सहायता के लिए सरकार की सबसे प्रमुख योजना "
                f"**{top_scheme['name_hi']}** है।\n\n"
                f"इसके तहत पात्र किसान परिवारों को खाद, बीज और कृषि खर्चों के लिए हर वर्ष **₹6,000 की नकद सहायता** "
                f"तीन किस्तों (₹2,000 प्रत्येक) में सीधे बैंक खाते में दी जाती है।\n\n"
                f"इसके अतिरिक्त यदि आपको फसल बुआई के लिए कम ब्याज पर ऋण चाहिए, तो **किसान क्रेडिट कार्ड (KCC)** के तहत "
                f"मात्र 4% प्रभावी ब्याज दर पर ₹3 लाख तक का ऋण भी मिल सकता है।"
            )
            reply_en = (
                f"Hello. For agricultural financial assistance, the flagship scheme is "
                f"**{top_scheme['name']} (PM-KISAN)**.\n\n"
                f"It provides **₹6,000 per year** in 3 equal installments of ₹2,000 directly into the Aadhaar-linked bank accounts "
                f"of landholding farmer families for seeds, fertilizers, and farm inputs.\n\n"
                f"Additionally, for affordable crop loans, the **Kisan Credit Card (KCC)** scheme offers loans up to ₹3 Lakh at an effective subsidized interest rate of just 4%."
            )
            follow_up_hi = "क्या आपके या आपके परिवार के नाम पर ज़मीन (खसरा-खतौनी) दर्ज है, और क्या आपका बैंक खाता आधार से लिंक (e-KYC पूर्ण) है?"
            follow_up_en = "Do you have cultivable land registered in your name in land records, and is your bank account Aadhaar-seeded with e-KYC completed?"
            checklist_hi = [
                "अपने राज्य के भू-अभिलेख पोर्टल से अपने नाम की खसरा-खतौनी की सत्यापित नकल निकालें।",
                "सुनिश्चित करें कि आपका बैंक खाता आधार और डीबीटी (NPCI DBT) से सक्रिय रूप से जुड़ा है।",
                "pmkisan.gov.in पर जाकर 'New Farmer Registration' में ऑनलाइन आवेदन करें या सीएससी केंद्र जाएं।",
                "नज़दीकी कॉमन सर्विस सेंटर (CSC) पर बायोमेट्रिक या चेहरे के जरिए अनिवार्य e-KYC पूरा कराएं।"
            ]
            checklist_en = [
                "Verify your land ownership record (Khasra-Khatauni / RoR) on your state land records portal.",
                "Ensure your bank account is linked to Aadhaar with active NPCI DBT seeding.",
                "Register on https://pmkisan.gov.in under 'New Farmer Registration' or at a CSC center.",
                "Complete mandatory e-KYC via OTP or biometric face authentication."
            ]
            missing_info_hi = ["ज़मीन का स्वामित्व", "आयकर या सरकारी नौकरी की स्थिति"]
            missing_info_en = ["Land ownership status", "Any family member in government service or paying income tax"]

        elif top_id == "kcc":
            reply_hi = (
                f"नमस्ते किसान साथी। खेती और खाद-बीज के लिए आसान ऋण हेतु **{top_scheme['name_hi']}** उपलब्ध है। "
                f"इसमें समय पर अदायगी करने पर मात्र 4% वार्षिक ब्याज दर पर ₹3 लाख तक का सस्ता कर्ज उपलब्ध होता है।"
            )
            reply_en = (
                f"Hello. For timely credit support for seeds and farming inputs, **{top_scheme['name']} (KCC)** provides loans "
                f"up to ₹3 Lakh with prompt repayment interest as low as 4% per annum."
            )
            follow_up_hi = "क्या आप खुद की ज़मीन पर खेती करते हैं या बटाईदार हैं, और किस बैंक में आपका खाता है?"
            follow_up_en = "Do you cultivate owned land or are you a sharecropper, and which bank do you have an account with?"
            checklist_hi = ["बैंक से सरल 1-पेज का केसीसी फॉर्म लें।", "खसरा-खतौनी और आधार कार्ड संलग्न करें।", "बैंक शाखा में आवेदन जमा करें।"]
            checklist_en = ["Obtain the 1-page KCC form from your local bank branch.", "Attach Khasra-Khatauni land records and Aadhaar.", "Submit to branch manager."]
            missing_info_hi = ["ज़मीन का रकबा"]
            missing_info_en = ["Land acreage"]

        elif top_id == "pmay_g":
            reply_hi = (
                f"नमस्ते। पक्का मकान बनाने के लिए केंद्र सरकार की **{top_scheme['name_hi']}** उपलब्ध है। "
                f"इसमें ग्रामीण क्षेत्र में घर बनाने के लिए ₹1,20,000 (मैदानी क्षेत्र) या ₹1,30,000 (पहाड़ी क्षेत्र) "
                f"की अनुदान सहायता सीधे बैंक खाते में किस्तों में दी जाती है।"
            )
            reply_en = (
                f"Hello. For constructing a pucca house, **{top_scheme['name']} (PMAY-G)** provides financial grants "
                f"of ₹1,20,000 (plain areas) to ₹1,30,000 (hilly/difficult areas) directly into beneficiaries' bank accounts."
            )
            follow_up_hi = "क्या आपका नाम आपकी ग्राम पंचायत की 'आवास+' प्रतीक्षा सूची में पहले से दर्ज है?"
            follow_up_en = "Is your name listed on the Gram Panchayat's 'Awaas+' permanent waiting list?"
            checklist_hi = ["ग्राम पंचायत में आवास प्लस सूची में नाम देखें।", "आधार व बैंक पासबुक सचिव को दें।", "आवास ऐप से घर का फोटो खिंचवाएं।"]
            checklist_en = ["Check name in Gram Panchayat Awaas+ list.", "Submit Aadhaar and MGNREGA Job Card to Panchayat Secretary.", "Geo-tag photo verification."]
            missing_info_hi = ["आवास+ सूची की स्थिति"]
            missing_info_en = ["Awaas+ verification status"]

        elif top_id == "pmjay":
            reply_hi = (
                f"नमस्ते। अस्पताल और बीमारी के खर्च से सुरक्षा के लिए **{top_scheme['name_hi']}** (आयुष्मान भारत) "
                f"के अंतर्गत प्रत्येक पात्र परिवार को प्रति वर्ष ₹5 लाख तक का पूरी तरह मुफ्त इलाज मिलता है।"
            )
            reply_en = (
                f"Hello. For hospitalization and healthcare expenses, **{top_scheme['name']} (PM-JAY)** provides "
                f"cashless and paperless treatment up to ₹5,00,000 per family per year across empaneled hospitals."
            )
            follow_up_hi = "क्या आपके पास राशन कार्ड है अथवा क्या परिवार में कोई 70 वर्ष से अधिक आयु का सदस्य है?"
            follow_up_en = "Do you hold an active ration card, or is there a senior citizen aged 70 or above in your household?"
            checklist_hi = ["14555 पर या beneficiary.nha.gov.in पर नाम जांचें।", "सीएससी पर e-KYC कराएं।", "आयुष्मान कार्ड डाउनलोड करें।"]
            checklist_en = ["Verify eligibility at https://beneficiary.nha.gov.in or call 14555.", "Complete e-KYC at nearest CSC / hospital.", "Download Ayushman card."]
            missing_info_hi = ["राशन कार्ड संख्या"]
            missing_info_en = ["Ration card / Family ID"]

        elif top_id == "mgnrega":
            reply_hi = (
                f"नमस्ते। ग्रामीण रोजगार के लिए **{top_scheme['name_hi']}** के तहत हर ग्रामीण परिवार को "
                f"एक वित्तीय वर्ष में 100 दिन के अकुशल काम की कानूनी गारंटी प्राप्त है।"
            )
            reply_en = (
                f"Hello. For guaranteed rural livelihood, **{top_scheme['name']} (MGNREGA)** legally guarantees "
                f"at least 100 days of unskilled wage employment per household per financial year."
            )
            follow_up_hi = "क्या आपकी ग्राम पंचायत का बना हुआ मनरेगा जॉब कार्ड आपके पास है?"
            follow_up_en = "Do you hold an active MGNREGA Job Card issued by your Gram Panchayat?"
            checklist_hi = ["ग्राम रोजगार सहायक को काम की मांग का लिखित आवेदन दें।", "आवेदन की रसीद लें।", "15 दिन में काम पाएं।"]
            checklist_en = ["Submit written demand for work to Panchayat Rozgar Sahayak.", "Obtain dated receipt.", "Entitled to work within 15 days."]
            missing_info_hi = ["जॉब कार्ड विवरण"]
            missing_info_en = ["Job Card details"]

        else:
            reply_hi = f"नमस्ते। आपकी समस्या के लिए **{top_scheme['name_hi']}** उपयोगी हो सकती है।"
            reply_en = f"Hello. **{top_scheme['name']}** may be relevant to your requirements."
            follow_up_hi = "क्या आप इस योजना के बारे में विस्तार से जानना चाहते हैं?"
            follow_up_en = "Would you like to know more about the eligibility conditions for this scheme?"
            checklist_hi = ["योजना की पात्रता जांचें।", "आवश्यक दस्तावेज़ तैयार करें।"]
            checklist_en = ["Check scheme eligibility conditions.", "Prepare necessary identity and land documents."]
            missing_info_hi = ["व्यक्तिगत विवरण"]
            missing_info_en = ["Personal eligibility details"]

        disclaimer_hi = (
            "⚠️ महत्वपूर्ण सूचना: स्कीम साथी एक मार्गदर्शन सहायक है। "
            "अंतिम पात्रता और लाभ की स्वीकृति संबंधित सरकारी विभाग या बैंक के आधिकारिक नियमों के अधीन है।"
        )
        disclaimer_en = (
            "⚠️ Important Notice: Scheme Saathi provides advisory guidance only. "
            "Final eligibility and benefit disbursement depend strictly on verification by the competent government department."
        )

        return SchemeSaathiResponse(
            mode="⚡ Smart Demo Mode" if lang == "en" else "⚡ स्मार्ट डेमो मोड (Rule-Based Expert Engine)",
            reply_hi=reply_hi,
            reply_en=reply_en,
            follow_up_question_hi=follow_up_hi,
            follow_up_question_en=follow_up_en,
            recommended_schemes=recommended_schemes,
            checklist_hi=checklist_hi,
            checklist_en=checklist_en,
            missing_info_hi=missing_info_hi,
            missing_info_en=missing_info_en,
            official_verification_needed=["राजस्व व बैंक रिकॉर्ड"],
            disclaimer_hi=disclaimer_hi,
            disclaimer_en=disclaimer_en,
            is_unknown_domain=False,
            current_lang=lang
        )
