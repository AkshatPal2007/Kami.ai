"""
AI Service: Handles user queries in natural conversational Hindi.
Integrates with Google Gemini API when GEMINI_API_KEY is available,
and provides a robust, transparent, rule-based expert engine when in demo mode.
"""

import os
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from services.scheme_service import SchemeService


@dataclass
class SchemeSaathiResponse:
    mode: str  # "gemini_ai" | "demo_rule_based"
    reply_hi: str  # Conversational Hindi reply
    follow_up_question_hi: Optional[str]  # 1 concise follow-up question
    recommended_schemes: List[Dict[str, Any]]  # List of matched scheme dicts with eligibility
    checklist: List[str]  # Step-by-step next actions
    missing_info: List[str]  # Facts needed to assess
    official_verification_needed: List[str]  # What user must verify in person
    disclaimer_hi: str  # Important legal disclaimer
    is_unknown_domain: bool  # True if query is outside current DB


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

    def get_current_mode(self) -> str:
        if self.is_ai_available():
            return f"🤖 Gemini AI ({self.model_name})"
        return "⚡ स्मार्ट डेमो मोड (Rule-Based Expert Engine)"

    def process_query(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        gathered_facts: Optional[Dict[str, Any]] = None
    ) -> SchemeSaathiResponse:
        """
        Main entry point for processing a user question.
        Uses Gemini if configured, otherwise falls back to the transparent Demo engine.
        """
        user_message = user_message.strip() if user_message else ""
        gathered_facts = gathered_facts or {}
        conversation_history = conversation_history or []

        # If Gemini is available, attempt AI processing
        if self.is_ai_available():
            try:
                ai_resp = self._call_gemini(user_message, conversation_history, gathered_facts)
                if ai_resp:
                    return ai_resp
            except Exception as e:
                print(f"[AIService] Gemini API error, falling back to Demo engine: {e}")

        # Transparent rule-based demo engine
        return self._run_demo_engine(user_message, conversation_history, gathered_facts)

    def _call_gemini(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        gathered_facts: Dict[str, Any]
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
                "purpose_hi": s["purpose_hi"],
                "benefits_hi": s["benefits_hi"],
                "eligibility_hi": s["eligibility_hi"],
                "exclusions_hi": s.get("exclusions_hi", []),
                "required_documents": s.get("required_documents", []),
                "application_steps_hi": s.get("application_steps_hi", []),
                "official_source": s.get("official_source", ""),
                "application_url": s.get("application_url", ""),
                "helpline": s.get("helpline", ""),
                "last_verified": s.get("last_verified", "")
            })

        system_instruction = (
            "You are Scheme Saathi (स्कीम साथी), an empathetic, truthful AI assistant helping rural Indian citizens "
            "understand government schemes in simple, clear, conversational Hindi.\n"
            "CRITICAL RULES:\n"
            "1. Ground your recommendations ONLY in the provided verified government schemes list. NEVER invent or fabricate schemes, rules, or amounts.\n"
            "2. NEVER guarantee eligibility or benefit approval. Always state that final approval depends on official government verification.\n"
            "3. If the user's problem is NOT covered by the provided schemes (e.g. theft, private dispute, passport, urban issue), honestly admit your current knowledge base is limited and direct them to the official myScheme portal (https://www.myscheme.gov.in/).\n"
            "4. Ask AT MOST ONE concise follow-up question if essential information (such as crop insurance status, land record, state) is missing.\n"
            "5. Always respond in warm, rural-friendly conversational Hindi (सरल और सम्मानजनक हिंदी).\n"
            "6. You MUST return your response as a valid JSON object matching the requested schema.\n"
        )

        prompt = f"""
Official Verified Schemes Database:
{json.dumps(schemes_context, ensure_ascii=False, indent=2)}

Known User Facts so far:
{json.dumps(gathered_facts, ensure_ascii=False)}

User Input:
"{user_message}"

Generate a valid JSON object with these EXACT keys:
{{
  "reply_hi": "Conversational Hindi explanation of the situation and how relevant schemes might help or why none match",
  "matched_scheme_ids": ["list", "of", "scheme_ids", "or", "empty"],
  "follow_up_question_hi": "One single concise question in Hindi to clarify missing info, or null if sufficient",
  "missing_info": ["list", "of", "specific", "facts", "needed"],
  "checklist": ["3 to 5 clear, actionable next steps in Hindi"],
  "official_verification_needed": ["list of items to verify at CSC/Panchayat/Bank"],
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

        # Parse JSON
        text = response.text.strip()
        # Clean potential markdown fences
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

        return SchemeSaathiResponse(
            mode=f"🤖 Gemini AI ({self.model_name})",
            reply_hi=data.get("reply_hi", ""),
            follow_up_question_hi=data.get("follow_up_question_hi"),
            recommended_schemes=recommended_schemes,
            checklist=data.get("checklist", []),
            missing_info=data.get("missing_info", []),
            official_verification_needed=data.get("official_verification_needed", ["भूमि खसरा-खतौनी की प्रति", "बैंक खाता आधार सीडिंग"]),
            disclaimer_hi=disclaimer_hi,
            is_unknown_domain=data.get("is_unknown_domain", False)
        )

    def _run_demo_engine(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        gathered_facts: Dict[str, Any]
    ) -> SchemeSaathiResponse:
        """
        Deterministic, intelligent rule-based engine covering all primary hackathon scenarios.
        """
        search_results = self.scheme_service.search_schemes(user_message, gathered_facts)
        msg_lower = user_message.lower()

        # Update gathered facts heuristically from message text
        updated_facts = dict(gathered_facts)

        # Detect crop damage
        if any(w in msg_lower for w in ["बारिश", "ओला", "नुकसान", "खराब", "बाढ़", "सूखा", "बरसात"]):
            updated_facts["has_crop_damage"] = True

        # Detect land ownership
        if any(w in msg_lower for w in ["मेरी जमीन", "खुद की जमीन", "खतौनी", "जमीन है"]):
            updated_facts["is_landowner"] = True
        elif any(w in msg_lower for w in ["जमीन नहीं है", "भूमिहीन", "किराए पर"]):
            updated_facts["is_landowner"] = False

        # Detect insurance status
        if any(w in msg_lower for w in ["बीमा कराया था", "बीमा है", "प्रीमियम कटा था"]):
            updated_facts["is_insured"] = True
        elif any(w in msg_lower for w in ["बीमा नहीं है", "बीमा नहीं कराया"]):
            updated_facts["is_insured"] = False

        # Scenario C: Unknown Problem / Domain
        unknown_indicators = ["चोरी", "दुकान", "पासपोर्ट", "पुलिस", "विवाद", "झगड़ा", "कोर्ट", "गाड़ी चोरी", "व्यापार"]
        has_unknown = any(ind in msg_lower for ind in unknown_indicators) and not any(k in msg_lower for k in ["फसल", "किसान", "खेती", "आवास", "इलाज", "मनरेगा"])

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
            checklist = [
                "भारत सरकार के आधिकारिक 'myScheme' पोर्टल (https://www.myscheme.gov.in/) पर जाएं।",
                "'Find Schemes Based on You' (अपने लिए योजना खोजें) पर क्लिक करें।",
                "अपनी आयु, राज्य, जाति, और व्यवसाय का विवरण दर्ज करें।",
                "यदि यह आपराधिक मामला (जैसे चोरी) है, तो सर्वप्रथम निकटतम पुलिस थाने में प्राथमिकी (FIR) दर्ज कराएं।"
            ]
            disclaimer_hi = (
                "⚠️ महत्वपूर्ण सूचना: स्कीम साथी एक मार्गदर्शन सहायक है। "
                "अंतिम पात्रता और लाभ की स्वीकृति संबंधित सरकारी विभाग या अधिकृत प्राधिकरण द्वारा ही तय की जाती है।"
            )

            return SchemeSaathiResponse(
                mode="⚡ स्मार्ट डेमो मोड (Rule-Based Expert Engine)",
                reply_hi=reply_hi,
                follow_up_question_hi="क्या आपकी समस्या कृषि, स्वास्थ्य, मकान, या ग्रामीण मजदूरी से भी जुड़ी है?",
                recommended_schemes=[],
                checklist=checklist,
                missing_info=["क्या आप ग्रामीण या शहरी क्षेत्र से हैं?", "क्या आपने आधिकारिक पोर्टल पर अन्य योजनाएं खोजी हैं?"],
                official_verification_needed=["संबंधित सरकारी विभाग अथवा पुलिस/प्रशासनिक दस्तावेज"],
                disclaimer_hi=disclaimer_hi,
                is_unknown_domain=True
            )

        # Matched schemes
        recommended_schemes = []
        for scheme, score in search_results[:2]:  # Take top 2 matches
            assessment = self.scheme_service.assess_eligibility(scheme, updated_facts)
            rec = dict(scheme)
            rec["assessment"] = assessment
            recommended_schemes.append(rec)

        top_scheme = recommended_schemes[0]
        top_id = top_scheme["id"]

        # Craft conversational reply and follow-up based on top scheme
        if top_id == "pmfby":
            # Scenario A: Crop Damage
            reply_hi = (
                f"राम-राम भाई जी। आपकी बात सुनकर दुख हुआ कि आपकी फसल को नुकसान पहुंचा है।\n\n"
                f"इसके लिए केंद्र सरकार की **{top_scheme['name_hi']}** आपके काम आ सकती है। "
                f"इस योजना के तहत बेमौसम बारिश, ओलावृष्टि या जलभराव से हुए नुकसान की भरपाई का प्रावधान है।\n\n"
                f"⚠️ **अति आवश्यक ध्यान दें:** यदि बारिश या ओले से स्थानीय स्तर पर नुकसान हुआ है, "
                f"तो घटना के **72 घंटे (3 दिन) के भीतर** बीमा कंपनी, बैंक, या टोल-फ्री नंबर 14447 पर सूचना देना अनिवार्य होता है। "
                f"यदि यह समय बीत जाए तो क्लेम मिलना कठिन हो सकता है। "
                f"कृपया ध्यान रखें कि यह सहायता स्वचालित या गारंटीकृत नहीं है — नुकसान की भरपाई केवल तभी होगी जब फसल बीमाकृत हो और सर्वे में नुकसान प्रमाणित हो।"
            )
            follow_up = "आपकी फसल किस राज्य और ज़िले में है, तथा क्या आपने इस चालू मौसम में फसल का बीमा (PMFBY या KCC के माध्यम से) कराया था?"
            checklist = [
                "तुरंत राष्ट्रीय टोल-फ्री हेल्पलाइन 14447 पर कॉल करें या 'Crop Insurance App' पर नुकसान की सूचना दर्ज करें (72 घंटे के अंदर)।",
                "अपने खेत में फसल के नुकसान और जलभराव की स्पष्ट तस्वीरें अपने मोबाइल से खींचें।",
                "अपनी बैंक पासबुक, आधार कार्ड और खसरा-खतौनी की प्रति तैयार रखें।",
                "अपने गाँव के पटवारी, ग्राम सेवक अथवा ब्लॉक कृषि अधिकारी से संपर्क कर संयुक्त सर्वे (Field Survey) की जानकारी लें।"
            ]
            missing_info = [
                "राज्य और ज़िला (क्या फसल अधिसूचित क्षेत्र में है?)",
                "फसल का नाम (खरीफ या रबी?)",
                "बीमा पॉलिसी नंबर या बैंक केसीसी विवरण",
                "नुकसान की सही तिथि व समय"
            ]
            verification_needed = [
                "पटवारी / राजस्व विभाग द्वारा फसल बुआई व नुकसान का पंचनामा",
                "बीमा कंपनी के सर्वेयर द्वारा खेत का भौतिक निरीक्षण"
            ]

        elif top_id == "pm_kisan":
            # Scenario B: Farmer Support
            reply_hi = (
                f"नमस्ते किसान भाई। खेती-बाड़ी में सहायता के लिए सरकार की सबसे प्रमुख योजना "
                f"**{top_scheme['name_hi']}** है।\n\n"
                f"इसके तहत पात्र किसान परिवारों को खाद, बीज और कृषि खर्चों के लिए हर वर्ष **₹6,000 की नकद सहायता** "
                f"तीन किस्तों (₹2,000 प्रत्येक) में सीधे बैंक खाते में दी जाती है।\n\n"
                f"इसके अतिरिक्त यदि आपको फसल बुआई के लिए कम ब्याज पर ऋण चाहिए, तो **किसान क्रेडिट कार्ड (KCC)** के तहत "
                f"मात्र 4% प्रभावी ब्याज दर पर ₹3 लाख तक का ऋण भी मिल सकता है।"
            )
            follow_up = "क्या आपके या आपके परिवार के नाम पर ज़मीन (खसरा-खतौनी) दर्ज है, और क्या आपका बैंक खाता आधार से लिंक (e-KYC पूर्ण) है?"
            checklist = [
                "अपने राज्य के भू-अभिलेख पोर्टल से अपने नाम की खसरा-खतौनी की सत्यापित नकल निकालें।",
                "सुनिश्चित करें कि आपका बैंक खाता आधार और डीबीटी (NPCI DBT) से सक्रिय रूप से जुड़ा है।",
                "pmkisan.gov.in पर जाकर 'New Farmer Registration' में ऑनलाइन आवेदन करें या सीएससी केंद्र जाएं।",
                "नज़दीकी कॉमन सर्विस सेंटर (CSC) पर बायोमेट्रिक या चेहरे के जरिए अनिवार्य e-KYC पूरा कराएं।"
            ]
            missing_info = [
                "क्या परिवार में कोई सरकारी सेवा या आयकर दाता है? (यह अपात्रता की श्रेणी में आता है)",
                "कृषि भूमि का सटीक रकबा/क्षेत्रफल"
            ]
            verification_needed = [
                "तहसील/पटवारी द्वारा भूमि स्वामित्व सत्यापन",
                "बैंक खाते की आधार एनपीसीआई मैपिंग"
            ]

        elif top_id == "kcc":
            reply_hi = (
                f"नमस्ते किसान साथी। खेती और खाद-बीज के लिए आसान ऋण हेतु **{top_scheme['name_hi']}** सर्वश्रेष्ठ विकल्प है। "
                f"इसमें समय पर अदायगी करने पर मात्र 4% वार्षिक ब्याज दर पर ₹3 लाख तक का सस्ता कर्ज उपलब्ध होता है।"
            )
            follow_up = "क्या आप खुद की ज़मीन पर खेती करते हैं या बटाईदार हैं, और किस बैंक में आपका खाता है?"
            checklist = [
                "अपनी बैंक शाखा से 1-पेज का सरल केसीसी फॉर्म प्राप्त करें।",
                "खसरा-खतौनी, आधार कार्ड और बैंक पासबुक संलग्न करें।",
                "शाखा प्रबंधक के पास आवेदन जमा कर पावती रसीद लें।"
            ]
            missing_info = ["खेती की ज़मीन का विवरण", "अन्य किसी बैंक में पूर्व बकाया"]
            verification_needed = ["बैंक द्वारा सिबिल/ऋण इतिहास और भूमि अभिलेख सत्यापन"]

        elif top_id == "pmay_g":
            reply_hi = (
                f"नमस्ते। पक्का मकान बनाने के लिए केंद्र सरकार की **{top_scheme['name_hi']}** उपलब्ध है। "
                f"इसमें ग्रामीण क्षेत्र में घर बनाने के लिए ₹1,20,000 (मैदानी क्षेत्र) या ₹1,30,000 (पहाड़ी क्षेत्र) "
                f"की अनुदान सहायता सीधे बैंक खाते में किस्तों में दी जाती है।"
            )
            follow_up = "क्या आपका नाम आपकी ग्राम पंचायत की 'आवास+' प्रतीक्षा सूची में पहले से दर्ज है?"
            checklist = [
                "अपनी ग्राम पंचायत के प्रधान या सचिव से मिलकर 'आवास प्लस सूची' में नाम की पुष्टि करें।",
                "आधार कार्ड, बैंक पासबुक और मनरेगा जॉब कार्ड जमा करें।",
                "आवास ऐप द्वारा अपने वर्तमान कच्चे मकान का जियो-टैगिंग फोटो खिंचवाएं।"
            ]
            missing_info = ["ग्राम पंचायत का नाम", "परिवार की वर्तमान आवास स्थिति"]
            verification_needed = ["ग्राम सभा द्वारा पात्रता अनुमोदन व आवास ऐप भौतिक सत्यापन"]

        elif top_id == "pmjay":
            reply_hi = (
                f"नमस्ते। अस्पताल और बीमारी के खर्च से सुरक्षा के लिए **{top_scheme['name_hi']}** (आयुष्मान भारत) "
                f"के अंतर्गत प्रत्येक पात्र परिवार को प्रति वर्ष ₹5 लाख तक का पूरी तरह मुफ्त इलाज मिलता है। "
                f"हाल ही में 70 वर्ष से ऊपर के सभी बुजुर्गों को भी इसमें शामिल कर लिया गया है।"
            )
            follow_up = "क्या आपके पास राशन कार्ड है अथवा क्या परिवार में कोई 70 वर्ष से अधिक आयु का सदस्य है?"
            checklist = [
                "टोल-फ्री नंबर 14555 पर कॉल करें या beneficiary.nha.gov.in पर पात्रता जांचें।",
                "आधार ओटीपी या सीएससी पर बायोमेट्रिक द्वारा e-KYC करें।",
                "अपना डिजिटल आयुष्मान कार्ड डाउनलोड करें।",
                "किसी भी सूचीबद्ध सरकारी या निजी अस्पताल में भर्ती के समय कार्ड दिखाएं।"
            ]
            missing_info = ["राशन कार्ड संख्या / परिवार आईडी", "मरीज़ की आयु"]
            verification_needed = ["आयुष्मान मित्र द्वारा अस्पताल में बायोमेट्रिक सत्यापन"]

        elif top_id == "mgnrega":
            reply_hi = (
                f"नमस्ते। ग्रामीण रोजगार के लिए **{top_scheme['name_hi']}** के तहत हर ग्रामीण परिवार को "
                f"एक वित्तीय वर्ष में 100 दिन के अकुशल काम की कानूनी गारंटी प्राप्त है।"
            )
            follow_up = "क्या आपकी ग्राम पंचायत का बना हुआ मनरेगा जॉब कार्ड आपके पास है?"
            checklist = [
                "ग्राम रोजगार सहायक या पंचायत सचिव को काम की मांग का लिखित आवेदन दें।",
                "आवेदन की दिनांकित पावती रसीद अवश्य लें।",
                "15 दिन के भीतर काम मिलना कानूनी अधिकार है, अन्यथा बेरोजगारी भत्ता देय होता है।"
            ]
            missing_info = ["जॉब कार्ड संख्या", "ग्राम पंचायत"]
            verification_needed = ["ग्राम पंचायत मस्टर रोल सत्यापन"]

        else:
            reply_hi = f"नमस्ते। आपकी समस्या के लिए **{top_scheme['name_hi']}** उपयोगी हो सकती है।"
            follow_up = "क्या आप इस योजना के बारे में विस्तार से जानना चाहते हैं?"
            checklist = ["योजना की पात्रता शर्तें जांचें।", "आवश्यक दस्तावेज़ तैयार करें।"]
            missing_info = ["व्यक्तिगत पात्रता विवरण"]
            verification_needed = ["संबंधित विभागीय कार्यालय"]

        disclaimer_hi = (
            "⚠️ महत्वपूर्ण सूचना: स्कीम साथी एक मार्गदर्शन सहायक है। "
            "अंतिम पात्रता और लाभ की स्वीकृति संबंधित सरकारी विभाग या बैंक के आधिकारिक नियमों के अधीन है। "
            "कोई भी लाभ गारंटीकृत नहीं है।"
        )

        return SchemeSaathiResponse(
            mode="⚡ स्मार्ट डेमो मोड (Rule-Based Expert Engine)",
            reply_hi=reply_hi,
            follow_up_question_hi=follow_up,
            recommended_schemes=recommended_schemes,
            checklist=checklist,
            missing_info=missing_info,
            official_verification_needed=verification_needed if 'verification_needed' in locals() else ["राजस्व व बैंक रिकॉर्ड"],
            disclaimer_hi=disclaimer_hi,
            is_unknown_domain=False
        )
