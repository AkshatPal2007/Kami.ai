"""
Scheme Service: Loads, searches, and assesses eligibility for verified government schemes.
Adheres strictly to official scheme guidelines without fabricating rules.
"""

import json
import os
import re
from typing import Dict, List, Optional, Any, Tuple


class SchemeService:
    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "schemes.json")
        self.data_path = data_path
        self._load_data()

    def _load_data(self):
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.schemes: List[Dict[str, Any]] = data.get("schemes", [])
            self.myscheme_portal: Dict[str, Any] = data.get("myscheme_portal", {})
            self._scheme_map = {s["id"]: s for s in self.schemes}

    def get_all_schemes(self) -> List[Dict[str, Any]]:
        return self.schemes

    def get_scheme_by_id(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        return self._scheme_map.get(scheme_id)

    def get_myscheme_info(self) -> Dict[str, Any]:
        return self.myscheme_portal

    def search_schemes(self, query: str, gathered_facts: Optional[Dict[str, Any]] = None) -> List[Tuple[Dict[str, Any], float]]:
        """
        Searches schemes matching natural Hindi or English user queries.
        Returns a list of tuples: (scheme_dict, relevance_score) sorted by score descending.
        """
        if not query or not query.strip():
            return []

        cleaned_query = query.lower()
        # Tokenize words in Hindi and English
        tokens = set(re.findall(r"[\w\u0900-\u097F]+", cleaned_query))

        results = []
        for scheme in self.schemes:
            score = 0.0

            # Match against keywords
            keywords = scheme.get("keywords", [])
            matched_keywords = [kw for kw in keywords if kw.lower() in cleaned_query or any(t == kw.lower() for t in tokens)]
            score += len(matched_keywords) * 2.5

            # Match against Hindi purpose and name
            name_hi = scheme.get("name_hi", "").lower()
            name_en = scheme.get("name", "").lower()
            purpose_hi = scheme.get("purpose_hi", "").lower()

            for token in tokens:
                if len(token) > 2:
                    if token in name_hi or token in name_en:
                        score += 3.0
                    if token in purpose_hi:
                        score += 1.5

            # Domain specific heuristics based on common rural Indian expressions
            # Crop loss / Rain / Hailstorm -> PMFBY
            if scheme["id"] == "pmfby":
                crop_loss_markers = ["बारिश", "पानी", "ओला", "ओलावृष्टि", "खराब", "फसल", "नुकसान", "बाढ़", "सूखा", "बरसात", "कीड़े", "crop loss", "rain", "damaged", "destroyed"]
                if any(m in cleaned_query for m in crop_loss_markers):
                    score += 4.0
                if "फसल" in cleaned_query and any(w in cleaned_query for w in ["खराब", "नुकसान", "बर्बाद", "मर गई", "नष्ट"]):
                    score += 6.0

            # Direct farmer income support -> PM-KISAN
            if scheme["id"] == "pm_kisan":
                kisan_income_markers = ["किसान", "सम्मान निधि", "6000", "खाद", "बीज", "किस्त", "खेती के लिए", "आर्थिक मदद", "सरकारी सहायता"]
                if any(m in cleaned_query for m in kisan_income_markers):
                    score += 3.5
                if "किसान" in cleaned_query and "सहायता" in cleaned_query and "बारिश" not in cleaned_query:
                    score += 5.0

            # Credit / Loan -> KCC
            if scheme["id"] == "kcc":
                credit_markers = ["कर्ज", "ऋण", "लोन", "क्रेडिट कार्ड", "केसीसी", "पैसा चाहिए", "उधार"]
                if any(m in cleaned_query for m in credit_markers):
                    score += 5.0

            # Pension -> PM-KMY
            if scheme["id"] == "pm_kmy":
                pension_markers = ["पेंशन", "बुढ़ापा", "वृद्धावस्था", "60 साल", "रिटायरमेंट"]
                if any(m in cleaned_query for m in pension_markers):
                    score += 5.0

            # Housing -> PMAY-G
            if scheme["id"] == "pmay_g":
                house_markers = ["मकान", "घर", "आवास", "कच्चा", "छत", "पक्का घर", "रहने"]
                if any(m in cleaned_query for m in house_markers):
                    score += 5.0

            # Healthcare -> PMJAY
            if scheme["id"] == "pmjay":
                health_markers = ["इलाज", "अस्पताल", "बीमारी", "दवा", "डॉक्टर", "ऑपरेशन", "आयुष्मान"]
                if any(m in cleaned_query for m in health_markers):
                    score += 5.0

            # Employment / Labor -> MGNREGA
            if scheme["id"] == "mgnrega":
                job_markers = ["काम", "रोजगार", "मजदूरी", "मनरेगा", "जॉब कार्ड", "दिहाड़ी", "100 दिन"]
                if any(m in cleaned_query for m in job_markers):
                    score += 5.0

            if score > 0:
                results.append((scheme, round(score, 2)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def assess_eligibility(self, scheme: Dict[str, Any], user_facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assesses eligibility status strictly without falsely guaranteeing approval.
        Returns:
            status: 'potentially_eligible' | 'apparently_ineligible' | 'insufficient_information'
            status_label_hi: Hindi friendly text
            reasons_hi: list of fulfilled or qualifying facts
            missing_info_hi: list of facts still required
            disclaimer_hi: legal disclaimer
        """
        scheme_id = scheme["id"]
        reasons_hi = []
        missing_info_hi = []
        ineligible_reasons_hi = []

        # Check Scheme Specific Logic
        if scheme_id == "pm_kisan":
            is_landowner = user_facts.get("is_landowner")
            is_taxpayer = user_facts.get("is_taxpayer")
            is_govt_employee = user_facts.get("is_govt_employee")
            has_aadhaar = user_facts.get("has_aadhaar")

            if is_taxpayer is True:
                ineligible_reasons_hi.append("परिवार में कोई सदस्य आयकर (Income Tax) देता है, जो बहिष्करण (Exclusion) श्रेणी में आता है।")
            if is_govt_employee is True:
                ineligible_reasons_hi.append("परिवार में कोई सदस्य नियमित सरकारी सेवा में है, जो पीएम-किसान के नियमों के तहत पात्र नहीं है।")

            if is_landowner is True:
                reasons_hi.append("आपके नाम पर कृषि योग्य भूमि (खतौनी) दर्ज है।")
            elif is_landowner is False:
                ineligible_reasons_hi.append("पीएम-किसान केवल उन किसानों के लिए है जिनके नाम पर राजस्व रिकॉर्ड में ज़मीन दर्ज हो (भूमिहीन किसान इसके पात्र नहीं हैं)।")
            else:
                missing_info_hi.append("क्या आपके या आपके परिवार के नाम पर ज़मीन (खसरा-खतौनी) दर्ज है?")

            if has_aadhaar is True:
                reasons_hi.append("आपके पास अनिवार्य आधार कार्ड उपलब्ध है।")
            elif has_aadhaar is None:
                missing_info_hi.append("क्या आपका बैंक खाता आधार से लिंक और ई-केवाईसी पूर्ण है?")

        elif scheme_id == "pmfby":
            has_crop_damage = user_facts.get("has_crop_damage")
            is_insured = user_facts.get("is_insured")
            loss_within_72h = user_facts.get("loss_within_72h")
            state = user_facts.get("state")
            crop_name = user_facts.get("crop_name")

            if has_crop_damage is True:
                reasons_hi.append("प्राकृतिक आपदा (बारिश/ओला/बाढ़) से फसल नुकसान का संकेत मिला है।")
            elif has_crop_damage is None:
                missing_info_hi.append("फसल किस प्राकृतिक आपदा (जैसे भारी बारिश या ओला) से खराब हुई है?")

            if is_insured is True:
                reasons_hi.append("फसल का बीमा (PMFBY या KCC के माध्यम से) कराया हुआ है।")
            elif is_insured is False:
                ineligible_reasons_hi.append("यदि इस चालू सीजन के लिए फसल का बीमा कट-ऑफ तारीख से पहले नहीं कराया गया था, तो पीएमएफबीवाई के तहत सीधे बीमा क्लेम मिलना कठिन होगा।")
            else:
                missing_info_hi.append("क्या आपकी इस फसल का बीमा (PMFBY या बैंक केसीसी के जरिए) चालू सीजन में कराया हुआ है?")

            if loss_within_72h is True:
                reasons_hi.append("घटना के 72 घंटे के भीतर सूचना देने की अनिवार्य समय सीमा का पालन किया जा रहा है।")
            elif loss_within_72h is False:
                missing_info_hi.append("महत्वपूर्ण: स्थानीय आपदा (ओला/अत्यधिक जलभराव) के लिए 72 घंटे की समय सीमा बीत चुकी है; तुरंत अपने कृषि अधिकारी या टोल-फ्री 14447 पर मार्गदर्शन लें।")
            else:
                missing_info_hi.append("फसल नुकसान की घटना को कितने घंटे/दिन हुए हैं? (स्थानीय आपदा के लिए 72 घंटे में सूचना देना अनिवार्य है)")

            if not state:
                missing_info_hi.append("आप किस राज्य और ज़िले से हैं? (यह जांचने के लिए कि आपकी फसल व ज़िला अधिसूचित है या नहीं)")

        elif scheme_id == "kcc":
            is_farmer = user_facts.get("is_farmer")
            has_default = user_facts.get("has_loan_default")

            if has_default is True:
                ineligible_reasons_hi.append("बैंक में पुराना जानबूझकर ऋण डिफ़ॉल्ट होने पर नया केसीसी स्वीकृत होने में बाधा आ सकती है।")

            if is_farmer is True:
                reasons_hi.append("आप कृषि या संबद्ध कार्य में संलग्न हैं।")
            else:
                missing_info_hi.append("क्या आप खुद की या पट्टे/बटाई की ज़मीन पर खेती अथवा पशुपालन करते हैं?")

        elif scheme_id == "pm_kmy":
            age = user_facts.get("age")
            land_size_hectares = user_facts.get("land_size_hectares")

            if age is not None:
                if 18 <= age <= 40:
                    reasons_hi.append(f"आपकी आयु ({age} वर्ष) योजना की पात्रता सीमा (18-40 वर्ष) के अंतर्गत है।")
                else:
                    ineligible_reasons_hi.append(f"आपकी आयु ({age} वर्ष) है। यह योजना केवल 18 से 40 वर्ष की आयु के किसानों के लिए है।")
            else:
                missing_info_hi.append("आपकी वर्तमान आयु कितनी है? (यह योजना 18 से 40 वर्ष की आयु के लिए है)")

            if land_size_hectares is not None:
                if land_size_hectares <= 2.0:
                    reasons_hi.append("आपकी कुल भूमि 2 हेक्टेयर या उससे कम (छोटे/सीमांत किसान) है।")
                else:
                    ineligible_reasons_hi.append("आपकी भूमि 2 हेक्टेयर से अधिक है (यह योजना केवल 2 हेक्टेयर तक वाले छोटे/सीमांत किसानों के लिए है)।")
            else:
                missing_info_hi.append("आपकी कुल कृषि भूमि कितनी है? (अधिकतम 2 हेक्टेयर / 5 एकड़ सीमा)")

        elif scheme_id == "pmay_g":
            has_pucca_house = user_facts.get("has_pucca_house")
            in_awaas_plus = user_facts.get("in_awaas_plus")

            if has_pucca_house is True:
                ineligible_reasons_hi.append("यदि परिवार के पास पहले से पक्का मकान है, तो वह पीएमएवाई-जी का पात्र नहीं माना जाता।")
            elif has_pucca_house is False:
                reasons_hi.append("परिवार के पास पक्का आवास नहीं है (कच्चा/जर्जर घर में निवास)।")
            else:
                missing_info_hi.append("क्या आपके पास पहले से कोई पक्का मकान है या आप कच्चे घर में रहते हैं?")

            if in_awaas_plus is True:
                reasons_hi.append("ग्राम पंचायत की आवास प्रतीक्षा सूची (Awaas+) में नाम दर्ज है।")
            elif in_awaas_plus is None:
                missing_info_hi.append("क्या आपका नाम ग्राम पंचायत की 'आवास+' प्रतीक्षा सूची में है?")

        elif scheme_id == "pmjay":
            has_ration_card = user_facts.get("has_ration_card")
            senior_70_plus = user_facts.get("senior_70_plus")

            if senior_70_plus is True:
                reasons_hi.append("परिवार में 70 वर्ष या उससे अधिक आयु के वरिष्ठ नागरिक हैं (जो आय सीमा के बिना ₹5 लाख कवर के सीधे पात्र हैं)।")
            if has_ration_card is True:
                reasons_hi.append("आपके पास पात्र राशन कार्ड / परिवार पहचान पत्र है।")
            elif has_ration_card is None and senior_70_plus is None:
                missing_info_hi.append("क्या आपके पास राशन कार्ड है अथवा परिवार में कोई 70 वर्ष या उससे अधिक आयु का सदस्य है?")

        elif scheme_id == "mgnrega":
            is_rural = user_facts.get("is_rural")
            willing_manual_work = user_facts.get("willing_manual_work")

            if is_rural is False:
                ineligible_reasons_hi.append("मनरेगा केवल ग्रामीण ग्राम पंचायत क्षेत्रों के लिए लागू है (शहरी क्षेत्रों में नहीं)।")
            if willing_manual_work is True:
                reasons_hi.append("परिवार का सदस्य अकुशल शारीरिक श्रम करने को तैयार है।")
            elif willing_manual_work is None:
                missing_info_hi.append("क्या परिवार का कोई वयस्क सदस्य अकुशल शारीरिक काम करने का इच्छुक है?")

        # Determine Final Status
        if ineligible_reasons_hi:
            status = "apparently_ineligible"
            status_label_hi = "❌ संभावित अपात्र (नियमों के अनुसार शर्तें पूरी नहीं होतीं)"
        elif missing_info_hi and not reasons_hi:
            status = "insufficient_information"
            status_label_hi = "❓ अपर्याप्त जानकारी (पात्रता तय करने के लिए विवरण आवश्यक)"
        elif missing_info_hi and reasons_hi:
            status = "potentially_eligible"
            status_label_hi = "🟡 संभावित पात्र (कुछ मुख्य शर्तें पूरी हैं, अंतिम पुष्टि बाकी)"
        else:
            status = "potentially_eligible"
            status_label_hi = "✅ संभावित पात्र (दी गई जानकारी के अनुसार योजना अनुकूल है)"

        disclaimer_hi = (
            "⚠️ महत्वपूर्ण सूचना: यह केवल एक प्रारंभिक मार्गदर्शन है। "
            "अंतिम पात्रता, सत्यापन और लाभ की स्वीकृति संबंधित सरकारी विभाग या बैंक के आधिकारिक नियमों के अधीन है। "
            "कोई भी लाभ गारंटीकृत नहीं है।"
        )

        return {
            "status": status,
            "status_label_hi": status_label_hi,
            "reasons_hi": reasons_hi,
            "ineligible_reasons_hi": ineligible_reasons_hi,
            "missing_info_hi": missing_info_hi,
            "disclaimer_hi": disclaimer_hi
        }

    def get_single_next_question(self, scheme_id: str, gathered_facts: Dict[str, Any]) -> Optional[str]:
        """
        Returns ONE concise follow-up question in Hindi for the user,
        avoiding overwhelming rural users.
        """
        scheme = self.get_scheme_by_id(scheme_id)
        if not scheme:
            return None

        assessment = self.assess_eligibility(scheme, gathered_facts)
        missing = assessment.get("missing_info_hi", [])
        if missing:
            return missing[0]
        return None
