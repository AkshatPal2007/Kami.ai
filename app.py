"""
Scheme Saathi (स्कीम साथी) — AI Government Benefits Assistant for Rural India
"आपकी समस्या, सरकारी मदद का सही रास्ता।" | "Your Problem, The Right Path to Government Support."

Bilingual (English & Hindi) conversational assistant for rural and low-literacy citizens.
Decluttered, high-accessibility UI with voice input, audio speech synthesis,
actionable checklists, verified scheme data, and telephony architecture.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Automatically load environment variables from .env file
load_dotenv()

import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.scheme_service import SchemeService
from services.ai_service import AIService, SchemeSaathiResponse
from services.tts_service import TTSService
from services.telephony_service import TelephonyService


# --- STREAMLIT CONFIGURATION ---
st.set_page_config(
    page_title="Scheme Saathi | AI Government Scheme Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- BILINGUAL UI DICTIONARY ---
UI = {
    "en": {
        "title": "Scheme Saathi",
        "tagline": "AI Government Benefits Assistant for Rural India",
        "desc": "Explain your situation in plain English or Hindi. We match you with verified government welfare schemes.",
        "assistant_tab": "💬 Assistant",
        "schemes_tab": "📋 Schemes Directory",
        "checklist_tab": "✅ Document Checklist",
        "phone_tab": "📞 Phone Call (IVR)",
        "quick_label": "💡 Try a sample question (Click to run):",
        "chip_a": "🌧️ Crop Damage (Rain)",
        "chip_b": "🚜 Farmer Support",
        "chip_c": "🏥 Medical / Hospital",
        "chip_d": "🏠 Rural Housing",
        "chip_e": "🏪 Other / Out of Scope",
        "text_a": "My crop was damaged by heavy rainfall. I need government assistance.",
        "text_b": "I am a farmer. I need government assistance for farming.",
        "text_c": "Need financial assistance for family medical treatment in hospital.",
        "text_d": "Looking for government assistance to build a pucca house in village.",
        "text_e": "My shop was burglarized, I need compensation.",
        "input_label": "Describe your problem or requirement:",
        "input_placeholder": "e.g., My paddy crop is ruined due to heavy rains, what government help can I get?",
        "ask_btn": "🔍 Get Advice & Schemes",
        "clear_btn": "Clear",
        "listen_btn": "🔊 Listen Audio",
        "recommendations_title": "🎯 Recommended Government Schemes",
        "next_steps_title": "📋 Actionable Next Steps",
        "follow_up_title": "❓ One Quick Question to Confirm Details:",
        "official_source": "Official Portal",
        "helpline": "Helpline",
        "verified_badge": "Verified Gov Portal",
        "disclaimer_text": "⚠️ Important: Scheme Saathi provides advisory guidance only. Final eligibility and benefit disbursement depend strictly on verification by the competent government department.",
        "mode_demo": "⚡ Mode: Smart Demo (Offline / Rule-Based)",
        "mode_gemini": "🤖 Mode: Gemini AI",
        "reset_btn": "🔄 Clear & Reset Conversation",
        "myscheme_card_title": "🌐 Explore 750+ Welfare Schemes on myScheme",
        "myscheme_card_text": "Your query is not covered in our agricultural database. Use the Government of India's single-window portal:",
        "myscheme_btn": "Open myScheme.gov.in",
        "checklist_title": "📑 Essential Documents Checklist",
        "checklist_desc": "Tick the documents you already possess to evaluate your application readiness:",
        "checklist_score": "Application Readiness Score:",
        "telephony_title": "📞 Future Vision: Toll-Free Telephone Helpline (IVR)",
        "telephony_desc": "Long-term vision: A simple 1800 toll-free number where rural citizens can speak via standard feature phones without internet.",
        "sim_title": "🎧 Interactive Call Simulator",
        "sim_btn": "▶️ Simulate Incoming Phone Call"
    },
    "hi": {
        "title": "स्कीम साथी (Scheme Saathi)",
        "tagline": "आपकी समस्या, सरकारी मदद का सही रास्ता।",
        "desc": "अपनी समस्या सरल हिंदी या अंग्रेजी में बताएं। हम आपको सही व सत्यापित सरकारी योजनाओं से जोड़ते हैं।",
        "assistant_tab": "💬 योजना सहायक",
        "schemes_tab": "📋 सभी योजनाएं",
        "checklist_tab": "✅ दस्तावेज़ चेकलिस्ट",
        "phone_tab": "📞 फोन कॉल सेवा (IVR)",
        "quick_label": "💡 तुरंत पूछने के लिए कोई एक उदाहरण चुनें:",
        "chip_a": "🌧️ फसल नुकसान (बारिश)",
        "chip_b": "🚜 किसान सहायता",
        "chip_c": "🏥 अस्पताल इलाज",
        "chip_d": "🏠 ग्रामीण आवास",
        "chip_e": "🏪 अन्य समस्या (दुकान)",
        "text_a": "मेरी फसल बारिश से खराब हो गई है। मुझे सरकारी मदद चाहिए।",
        "text_b": "मैं किसान हूँ। मुझे खेती के लिए सरकारी सहायता चाहिए।",
        "text_c": "परिवार में बीमारी के इलाज और अस्पताल के खर्च के लिए सरकारी मदद चाहिए।",
        "text_d": "गाँव में पक्का मकान बनाने के लिए सरकारी सहायता चाहिए।",
        "text_e": "मेरी दुकान में चोरी हो गई है, मुझे मुआवजा चाहिए।",
        "input_label": "अपनी समस्या यहाँ सरल शब्दों में लिखें:",
        "input_placeholder": "उदाहरण: मेरी धान की फसल बारिश से खराब हो गई है, मुझे क्या सरकारी मदद मिलेगी?",
        "ask_btn": "🔍 योजना खोजें एवं सलाह लें",
        "clear_btn": "साफ करें",
        "listen_btn": "🔊 सुनें (ऑडियो)",
        "recommendations_title": "🎯 संबंधित सरकारी योजनाएं",
        "next_steps_title": "📋 आगे क्या करें — आसान चेकलिस्ट",
        "follow_up_title": "❓ एक ज़रूरी सवाल:",
        "official_source": "आधिकारिक पोर्टल",
        "helpline": "हेल्पलाइन",
        "verified_badge": "सत्यापित सरकारी पोर्टल",
        "disclaimer_text": "⚠️ महत्वपूर्ण सूचना: स्कीम साथी एक मार्गदर्शन सहायक है। अंतिम पात्रता और लाभ की स्वीकृति संबंधित सरकारी विभाग या बैंक के नियमों के अधीन है।",
        "mode_demo": "⚡ मोड: स्मार्ट डेमो (नियम आधारित)",
        "mode_gemini": "🤖 मोड: Gemini AI",
        "reset_btn": "🔄 नई बातचीत",
        "myscheme_card_title": "🌐 myScheme पोर्टल पर 750+ योजनाएं खोजें",
        "myscheme_card_text": "आपकी समस्या वर्तमान कृषि डेटाबेस में नहीं है। भारत सरकार के राष्ट्रीय पोर्टल पर खोजें:",
        "myscheme_btn": "myScheme.gov.in खोलें",
        "checklist_title": "📑 ज़रूरी दस्तावेज़ चेकलिस्ट",
        "checklist_desc": "आवेदन की तैयारी जांचने के लिए अपने तैयार दस्तावेज़ों पर टिक लगाएं:",
        "checklist_score": "दस्तावेज़ तैयारी स्कोर:",
        "telephony_title": "📞 भविष्य का विजन: टोल-फ्री फोन कॉल हेल्पलाइन (IVR)",
        "telephony_desc": "दीर्घकालिक लक्ष्य: एक टोल-फ्री नंबर जिस पर ग्रामीण नागरिक बिना इंटरनेट वाले सामान्य फोन से कॉल कर सकें।",
        "sim_title": "🎧 फोन कॉल बातचीत सिमुलेटर",
        "sim_btn": "▶️ कॉल वार्तालाप चलाएं"
    }
}

# --- SESSION STATE INITIALIZATION ---
if "lang" not in st.session_state:
    st.session_state.lang = "en"  # Default English with instant Hindi toggle
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "gathered_facts" not in st.session_state:
    st.session_state.gathered_facts = {}
if "user_input_val" not in st.session_state:
    st.session_state.user_input_val = ""
if "custom_api_key" not in st.session_state:
    st.session_state.custom_api_key = os.getenv("GEMINI_API_KEY", "")

L = UI[st.session_state.lang]

# --- SERVICES SETUP ---
@st.cache_resource
def get_scheme_service():
    return SchemeService()

scheme_svc = get_scheme_service()
ai_svc = AIService(scheme_service=scheme_svc)

api_key = st.session_state.custom_api_key or os.getenv("GEMINI_API_KEY", "")
if api_key:
    ai_svc.api_key = api_key
    try:
        from google import genai
        ai_svc.client = genai.Client(api_key=api_key)
    except Exception:
        pass


# --- MODERN MINIMALIST STYLING ---
CLEAN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Mukta:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', 'Mukta', sans-serif !important;
}

/* Header Navbar */
.nav-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.8rem 1.4rem;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    margin-bottom: 1.2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.brand-title {
    font-size: 1.55rem;
    font-weight: 800;
    color: #15803D;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.brand-tagline {
    font-size: 0.9rem;
    color: #64748B;
    margin: 0;
}

/* Mode Pills */
.pill-demo {
    background: #FEF3C7;
    color: #B45309;
    border: 1px solid #FDE68A;
    padding: 4px 10px;
    border-radius: 16px;
    font-size: 0.82rem;
    font-weight: 600;
}
.pill-gemini {
    background: #DCFCE7;
    color: #15803D;
    border: 1px solid #BBF7D0;
    padding: 4px 10px;
    border-radius: 16px;
    font-size: 0.82rem;
    font-weight: 600;
}

/* Clean Cards */
.card-clean {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}
.card-alert {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}

/* Checklist step items */
.step-item {
    background: #F8FAFC;
    border-left: 3px solid #16A34A;
    padding: 0.6rem 0.9rem;
    margin-bottom: 0.4rem;
    border-radius: 0 6px 6px 0;
    font-size: 0.96rem;
}

/* Buttons */
.stButton > button {
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.15s ease-in-out !important;
}

/* Footer disclaimer */
.disclaimer-clean {
    font-size: 0.85rem;
    color: #64748B;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    padding: 0.7rem 1rem;
    border-radius: 8px;
    margin-top: 1rem;
}
</style>
"""
st.markdown(CLEAN_CSS, unsafe_allow_html=True)


# --- TOP BAR: BRAND + LANGUAGE TOGGLE + MODE BADGE ---
top_col1, top_col2, top_col3 = st.columns([5, 3, 2])

with top_col1:
    st.markdown(f"""
    <div>
        <h2 class="brand-title">🌾 {L['title']}</h2>
        <p class="brand-tagline">{L['tagline']}</p>
    </div>
    """, unsafe_allow_html=True)

with top_col2:
    is_gemini = ai_svc.is_ai_available()
    badge_html = f'<span class="pill-gemini">{L["mode_gemini"]}</span>' if is_gemini else f'<span class="pill-demo">{L["mode_demo"]}</span>'
    st.markdown(f"<div style='text-align: right; margin-top: 8px;'>{badge_html}</div>", unsafe_allow_html=True)

with top_col3:
    lang_choice = st.radio(
        "Language / भाषा",
        ["English", "हिंदी"],
        index=0 if st.session_state.lang == "en" else 1,
        horizontal=True,
        label_visibility="collapsed"
    )
    new_lang = "en" if lang_choice == "English" else "hi"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()


# --- SIDEBAR (SETTINGS & HELPLINES ONLY - OUT OF THE WAY) ---
with st.sidebar:
    st.markdown(f"### ⚙️ {('Settings' if st.session_state.lang == 'en' else 'सेटिंग्स')}")
    st.caption("Scheme Saathi runs seamlessly out-of-the-box in Demo Mode without requiring an API key.")

    user_key = st.text_input(
        "Gemini API Key (Optional)",
        value=st.session_state.custom_api_key,
        type="password"
    )
    if user_key != st.session_state.custom_api_key:
        st.session_state.custom_api_key = user_key
        st.rerun()

    model_sel = st.selectbox("AI Model", ["gemini-2.5-flash", "gemini-1.5-flash"], index=0)
    ai_svc.model_name = model_sel

    st.markdown("---")
    st.markdown(f"### 📞 {('Emergency Helplines' if st.session_state.lang == 'en' else 'सरकारी हेल्पलाइन')}")
    st.markdown("""
    - 🌾 **PMFBY Crop Insurance:** `14447`
    - 🚜 **PM-KISAN Helpline:** `155261`
    - 🩺 **Ayushman Health:** `14555`
    - 🏠 **Rural Housing:** `1800-11-6446`
    - 🌐 **myScheme Portal:** [myscheme.gov.in](https://www.myscheme.gov.in/)
    """)

    if st.button(L["reset_btn"], use_container_width=True):
        st.session_state.conversation = []
        st.session_state.gathered_facts = {}
        st.session_state.user_input_val = ""
        st.rerun()


# --- STREAMLINED TABS (EASY TO ACCESS) ---
tab_chat, tab_schemes, tab_checklist, tab_ivr = st.tabs([
    L["assistant_tab"],
    L["schemes_tab"],
    L["checklist_tab"],
    L["phone_tab"]
])


# ==============================================================================
# TAB 1: CONVERSATION ASSISTANT (CLEAN, MINIMAL, FAST)
# ==============================================================================
with tab_chat:
    # 1. Quick Example Chips (Clean 1-Click Access)
    st.markdown(f"**{L['quick_label']}**")
    chip_cols = st.columns(5)
    chips = [
        (chip_cols[0], L["chip_a"], L["text_a"]),
        (chip_cols[1], L["chip_b"], L["text_b"]),
        (chip_cols[2], L["chip_c"], L["text_c"]),
        (chip_cols[3], L["chip_d"], L["text_d"]),
        (chip_cols[4], L["chip_e"], L["text_e"]),
    ]
    for col, label, query_text in chips:
        if col.button(label, use_container_width=True):
            st.session_state.user_input_val = query_text
            st.rerun()

    # 2. Compact Voice & Text Input
    rec_lang = "en-IN" if st.session_state.lang == "en" else "hi-IN"
    mic_label = "🎙️ Speak in English" if st.session_state.lang == "en" else "🎙️ हिंदी में बोलें"

    voice_html = f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 14px; margin: 10px 0;">
        <span style="font-size: 14px; color: #475569; font-weight: 500;">
            🎤 {('Browser Voice Input (Speech-to-Text)' if st.session_state.lang == 'en' else 'ब्राउज़र माइक (बोलकर पूछें)')}
        </span>
        <button id="mic-btn" style="background: #16A34A; color: white; border: none; padding: 6px 14px; border-radius: 20px; font-size: 14px; font-weight: 600; cursor: pointer;">
            {mic_label}
        </button>
    </div>
    <div id="mic-status" style="font-size: 13px; color: #64748B; margin-left: 6px; display: none;"></div>

    <script>
    const btn = document.getElementById('mic-btn');
    const status = document.getElementById('mic-status');
    let listening = false;
    let rec;

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        rec = new SR();
        rec.lang = '{rec_lang}';
        rec.continuous = false;

        rec.onstart = function() {{
            listening = true;
            btn.style.background = '#DC2626';
            btn.innerText = '🛑 Listening...';
            status.style.display = 'block';
            status.innerText = 'Listening to your microphone...';
        }};

        rec.onresult = function(e) {{
            const text = e.results[0][0].transcript;
            status.style.color = '#15803D';
            status.innerText = 'Recorded: "' + text + '" (Copy or paste into input below)';
            // Attempt to update textarea if accessible
            const textareas = window.parent.document.querySelectorAll('textarea');
            if (textareas.length > 0) {{
                textareas[0].value = text;
                textareas[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        }};

        rec.onerror = function(e) {{
            listening = false;
            btn.style.background = '#16A34A';
            btn.innerText = '{mic_label}';
            status.style.color = '#DC2626';
            status.innerText = 'Mic notice: ' + e.error + '. You can type directly below.';
        }};

        rec.onend = function() {{
            listening = false;
            btn.style.background = '#16A34A';
            btn.innerText = '{mic_label}';
        }};

        btn.onclick = function() {{
            if (listening) {{ rec.stop(); }} else {{ rec.start(); }}
        }};
    }} else {{
        btn.disabled = true;
        btn.style.background = '#94A3B8';
        btn.innerText = 'Voice Unsupported';
        status.style.display = 'block';
        status.innerText = 'Speech recognition not supported in this browser. Please type below.';
    }}
    </script>
    """
    components.html(voice_html, height=75)

    with st.form("main_query_form", clear_on_submit=False):
        user_text = st.text_area(
            L["input_label"],
            value=st.session_state.user_input_val,
            height=70,
            placeholder=L["input_placeholder"],
            label_visibility="collapsed"
        )
        col_btn1, col_btn2 = st.columns([4, 1])
        with col_btn1:
            submit_pressed = st.form_submit_button(L["ask_btn"], use_container_width=True)
        with col_btn2:
            clear_pressed = st.form_submit_button(L["clear_btn"], use_container_width=True)

    if clear_pressed:
        st.session_state.user_input_val = ""
        st.rerun()

    # Process Query
    if submit_pressed and user_text.strip():
        query = user_text.strip()
        st.session_state.user_input_val = ""

        st.session_state.conversation.append({"role": "user", "content": query})

        with st.spinner("Analyzing request..." if st.session_state.lang == "en" else "विश्लेषण हो रहा है..."):
            resp = ai_svc.process_query(
                user_message=query,
                conversation_history=[{"role": c["role"], "content": c["content"]} for c in st.session_state.conversation],
                gathered_facts=st.session_state.gathered_facts,
                preferred_lang=st.session_state.lang
            )

        st.session_state.conversation.append({
            "role": "assistant",
            "content": resp.reply,
            "response_obj": resp
        })
        st.rerun()

    # Conversation Display
    if not st.session_state.conversation:
        st.markdown(f"""
        <div class="card-clean" style="text-align: center; padding: 2rem;">
            <h3 style="color: #15803D; margin-bottom: 0.5rem;">🌾 {L['title']}</h3>
            <p style="color: #475569; font-size: 1.05rem; max-width: 650px; margin: 0 auto;">
                {L['desc']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for idx, item in enumerate(st.session_state.conversation):
            if item["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(f"**You:** {item['content']}")
            else:
                resp: SchemeSaathiResponse = item.get("response_obj")
                with st.chat_message("assistant", avatar="🌾"):
                    # Main Reply
                    st.markdown(resp.reply)

                    # Audio Player Control
                    aud_col, _ = st.columns([2, 5])
                    with aud_col:
                        if st.button(f"{L['listen_btn']} #{idx}", key=f"tts_btn_{idx}"):
                            aud_bytes = TTSService.generate_audio(resp.reply, lang=st.session_state.lang)
                            if aud_bytes:
                                st.audio(aud_bytes, format="audio/mp3", autoplay=True)

                    # Scenario C: Out of Scope / myScheme Redirection
                    if resp.is_unknown_domain:
                        myscheme = scheme_svc.get_myscheme_info()
                        st.markdown(f"""
                        <div class="card-alert">
                            <strong>{L['myscheme_card_title']}</strong>
                            <p style="margin: 6px 0;">{myscheme.get('description' if st.session_state.lang == 'en' else 'description_hi')}</p>
                            <a href="{myscheme.get('official_url')}" target="_blank" style="display: inline-block; background: #0F172A; color: white; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 0.9rem; font-weight: 600;">
                                {L['myscheme_btn']} ↗
                            </a>
                        </div>
                        """, unsafe_allow_html=True)

                    # Follow-up Question
                    if resp.follow_up_question:
                        st.markdown(f"""
                        <div class="card-alert">
                            <strong style="color: #B45309;">{L['follow_up_title']}</strong>
                            <div style="font-size: 1.02rem; font-weight: 600; margin-top: 4px;">{resp.follow_up_question}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Recommended Schemes Cards
                    if resp.recommended_schemes:
                        st.markdown(f"#### {L['recommendations_title']}")
                        for s in resp.recommended_schemes:
                            assessment = s.get("assessment", {})
                            status_badge = assessment.get("status_label_en" if st.session_state.lang == "en" else "status_label_hi", "Eligible")
                            scheme_title = s["name"] if st.session_state.lang == "en" else s["name_hi"]
                            scheme_purpose = s.get("purpose", s.get("purpose_hi")) if st.session_state.lang == "en" else s.get("purpose_hi")
                            benefits_list = s.get("benefits", []) if st.session_state.lang == "en" else s.get("benefits_hi", [])

                            with st.expander(f"🏛️ {scheme_title} — {status_badge}", expanded=True):
                                st.markdown(f"**{('Summary' if st.session_state.lang == 'en' else 'उद्देश्य')}:** {scheme_purpose}")

                                b_col1, b_col2 = st.columns(2)
                                with b_col1:
                                    st.markdown(f"**{('Key Benefits' if st.session_state.lang == 'en' else 'प्रमुख लाभ')}:**")
                                    for b in benefits_list[:2]:
                                        st.write(f"- {b}")
                                with b_col2:
                                    st.markdown(f"**{('Official Links & Contact' if st.session_state.lang == 'en' else 'आधिकारिक संपर्क')}:**")
                                    st.write(f"📞 {L['helpline']}: `{s.get('helpline', '1800-180-1551')}`")
                                    st.markdown(f"🔗 [{L['official_source']}]({s.get('official_source', '#')})")

                    # Next Steps Checklist
                    if resp.checklist:
                        st.markdown(f"#### {L['next_steps_title']}")
                        for step_i, step_text in enumerate(resp.checklist, 1):
                            st.markdown(f"""
                            <div class="step-item">
                                <strong>{step_i}.</strong> {step_text}
                            </div>
                            """, unsafe_allow_html=True)

                    # Disclaimer
                    st.markdown(f"<div class='disclaimer-clean'>{resp.disclaimer}</div>", unsafe_allow_html=True)


# ==============================================================================
# TAB 2: SCHEMES DIRECTORY (CLEAN & SCANNABLE)
# ==============================================================================
with tab_schemes:
    st.markdown(f"### 📋 {('Verified Government Schemes' if st.session_state.lang == 'en' else 'सत्यापित सरकारी योजनाएं')}")
    st.caption("All scheme conditions, financial amounts, and helpline numbers are verified against official .gov.in portals.")

    search_term = st.text_input(
        "Search Schemes / योजना खोजें",
        placeholder="Type scheme name or keyword (e.g., crop, PM-KISAN, housing, loan)..."
    )

    all_schemes = scheme_svc.get_all_schemes()
    if search_term.strip():
        all_schemes = [s for s in all_schemes if search_term.lower() in s["name"].lower() or search_term.lower() in s["name_hi"].lower() or search_term.lower() in " ".join(s.get("keywords", [])).lower()]

    for s in all_schemes:
        name_show = s["name"] if st.session_state.lang == "en" else s["name_hi"]
        purpose_show = s.get("purpose", s.get("purpose_hi")) if st.session_state.lang == "en" else s.get("purpose_hi")
        benefits_show = s.get("benefits", []) if st.session_state.lang == "en" else s.get("benefits_hi", [])

        st.markdown(f"""
        <div class="card-clean">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h4 style="color:#15803D; margin:0;">🏛️ {name_show}</h4>
                <span class="pill-gemini">Verified: {s.get('last_verified', 'Oct 2024')}</span>
            </div>
            <p style="color:#475569; margin:6px 0 10px 0;">{purpose_show}</p>
            <div style="display:flex; gap:20px; font-size:0.9rem; flex-wrap:wrap;">
                <span>📞 <strong>{L['helpline']}:</strong> {s.get('helpline', '1800-180-1551')}</span>
                <span>🌐 <a href="{s.get('official_source')}" target="_blank">{L['official_source']}</a></span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ==============================================================================
# TAB 3: DOCUMENT CHECKLIST (DECLUTTERED)
# ==============================================================================
with tab_checklist:
    st.markdown(f"### {L['checklist_title']}")
    st.write(L["checklist_desc"])

    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown(f"**{('Farming & Agriculture' if st.session_state.lang == 'en' else 'कृषि एवं किसान योजनाएं')}**")
        d1 = st.checkbox("Aadhaar Card (आधार कार्ड)", value=True, key="c_aadhaar")
        d2 = st.checkbox("Land Ownership Record / Khasra-Khatauni (खसरा-खतौनी)", key="c_land")
        d3 = st.checkbox("Aadhaar-Seeded Bank Passbook (आधार लिंक बैंक पासबुक)", key="c_bank")
        d4 = st.checkbox("Sowing Certificate / Patwari Declaration (बुआई प्रमाण पत्र)", key="c_sowing")
        d5 = st.checkbox("Crop Damage Photos (within 72 hrs for PMFBY)", key="c_photo_damage")

    with c_right:
        st.markdown(f"**{('Housing, Health & Jobs' if st.session_state.lang == 'en' else 'आवास, स्वास्थ्य एवं मजदूरी')}**")
        d6 = st.checkbox("Ration Card / Family ID (राशन कार्ड)", key="c_ration")
        d7 = st.checkbox("MGNREGA Job Card (मनरेगा जॉब कार्ड)", key="c_jobcard")
        d8 = st.checkbox("Current Kutcha House Geo-Tagged Photo (AwaasApp)", key="c_house")
        d9 = st.checkbox("Passport Photographs (पासपोर्ट फोटो)", key="c_passport")
        d10 = st.checkbox("Active Aadhaar-Linked Mobile Number (सक्रिय मोबाइल नंबर)", value=True, key="c_mobile")

    score = sum([d1, d2, d3, d4, d5, d6, d7, d8, d9, d10])
    st.progress(score / 10.0)
    st.info(f"{L['checklist_score']} {score} / 10 documents prepared.")


# ==============================================================================
# TAB 4: TELEPHONY & IVR ARCHITECTURE
# ==============================================================================
with tab_ivr:
    st.markdown(f"### {L['telephony_title']}")
    st.write(L["telephony_desc"])

    telephony_svc = TelephonyService()

    col_sim_ctrl, col_sim_view = st.columns([1, 1])

    with col_sim_ctrl:
        st.markdown(f"#### {L['sim_title']}")
        scenario_ivr = st.selectbox(
            "Select Call Scenario:",
            ["Crop Damage Call (PMFBY)", "Farmer Income Support (PM-KISAN)", "Silence / Unresponsive Caller"]
        )
        if st.button(L["sim_btn"], use_container_width=True):
            if "Crop" in scenario_ivr:
                st.success("🗣️ **Caller:** 'Hello sir, my crop is underwater after yesterday\\'s heavy rain. Can I get government compensation?'")
                st.info("🤖 **Scheme Saathi IVR:** 'Greetings. For flood and rain loss, you can claim under PMFBY. You must report this within 72 hours on toll-free 14447. Was your crop insured this season?'")
            elif "Farmer" in scenario_ivr:
                st.success("🗣️ **Caller:** 'I need the ₹6000 financial support scheme for farming.'")
                st.info("🤖 **Scheme Saathi IVR:** 'Hello. That is PM-KISAN. Do you have land registered in your name and an Aadhaar-linked bank account?'")
            else:
                resp = telephony_svc.handle_silence_or_timeout("DEMO_CALL")
                st.warning(f"🤖 **Scheme Saathi IVR:** '{resp['prompt_text_hi']}'")

    with col_sim_view:
        st.markdown("#### Modular Architecture Blueprint:")
        st.code(telephony_svc.SYSTEM_ARCHITECTURE[:650] + "\n...", language="text")
