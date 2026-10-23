"""
Scheme Saathi (स्कीम साथी) — AI-Powered Government Scheme Assistant for Rural India
"आपकी समस्या, सरकारी मदद का सही रास्ता।"

A conversational Hindi-first assistant designed for rural citizens with low digital literacy.
Supports browser Hindi speech recognition, text-to-speech audio, official scheme matching,
eligibility assessment, actionable checklists, and future telephony architecture.
"""

import os
import sys
import json
import base64
import streamlit as st
import streamlit.components.v1 as components

# Ensure local imports work reliably
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.scheme_service import SchemeService
from services.ai_service import AIService, SchemeSaathiResponse
from services.tts_service import TTSService
from services.telephony_service import TelephonyService


# --- STREAMLIT PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Scheme Saathi | स्कीम साथी — सरकारी योजना सहायक",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR RURAL-FRIENDLY ACCESSIBLE DESIGN ---
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Mukta:wght@300;400;500;600;700;800&family=Poppins:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Mukta', 'Poppins', sans-serif !important;
}

/* Color Variables */
:root {
    --primary-green: #1B5E20;
    --accent-orange: #E65100;
    --saffron: #FF9800;
    --light-bg: #FBF9F5;
    --card-border: #E0E0E0;
    --text-dark: #212121;
}

/* Header Banner */
.main-header {
    background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 60%, #E65100 100%);
    color: white;
    padding: 1.8rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
}
.main-header h1 {
    font-size: 2.4rem;
    font-weight: 800;
    margin-bottom: 0.3rem;
    color: #FFFFFF !important;
}
.main-header p {
    font-size: 1.25rem;
    opacity: 0.95;
    margin-bottom: 0.5rem;
    color: #FFF3E0 !important;
}
.header-badge {
    display: inline-block;
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.4);
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.9rem;
    margin-right: 0.5rem;
}

/* Mode Badges */
.badge-demo {
    background-color: #FFF3E0;
    color: #E65100;
    border: 1px solid #FFE0B2;
    padding: 6px 14px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.95rem;
    display: inline-block;
}
.badge-gemini {
    background-color: #E8F5E9;
    color: #1B5E20;
    border: 1px solid #C8E6C9;
    padding: 6px 14px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.95rem;
    display: inline-block;
}

/* Rural Accessible Cards */
.saathi-card {
    background: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-left: 6px solid #2E7D32;
    border-radius: 12px;
    padding: 1.4rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.saathi-card-alert {
    background: #FFF8E1;
    border: 1px solid #FFE082;
    border-left: 6px solid #FF8F00;
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 1.2rem;
}

/* Large Accessible Buttons */
.stButton > button {
    font-family: 'Mukta', sans-serif !important;
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.4rem !important;
    min-height: 48px !important;
    transition: all 0.2s ease-in-out !important;
}

/* Scheme Title Box */
.scheme-header {
    background: #F1F8E9;
    border-radius: 8px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 1rem;
    border-left: 4px solid #33691E;
}

/* Checklist Items */
.checklist-item {
    background: #FAFAFA;
    border: 1px solid #EEEEEE;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 1.05rem;
}

/* Disclaimer Footer */
.disclaimer-box {
    background: #ECEFF1;
    border-left: 4px solid #607D8B;
    padding: 0.8rem 1.2rem;
    border-radius: 8px;
    font-size: 0.9rem;
    color: #455A64;
    margin-top: 1.5rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --- SESSION STATE INITIALIZATION ---
if "conversation" not in st.session_state:
    st.session_state.conversation = []  # list of dicts: {"role": "user"|"assistant", "content": ..., "response_obj": ...}
if "gathered_facts" not in st.session_state:
    st.session_state.gathered_facts = {}
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "voice_input_text" not in st.session_state:
    st.session_state.voice_input_text = ""
if "checked_documents" not in st.session_state:
    st.session_state.checked_documents = {}
if "custom_api_key" not in st.session_state:
    st.session_state.custom_api_key = os.getenv("GEMINI_API_KEY", "")


# --- INITIALIZE SERVICES ---
@st.cache_resource
def get_scheme_service():
    return SchemeService()

scheme_svc = get_scheme_service()

# AIService handles dynamic API key updates
api_key_to_use = st.session_state.custom_api_key or os.getenv("GEMINI_API_KEY", "")
ai_svc = AIService(scheme_service=scheme_svc)
if api_key_to_use:
    ai_svc.api_key = api_key_to_use
    try:
        from google import genai
        ai_svc.client = genai.Client(api_key=api_key_to_use)
    except Exception:
        pass


# --- SIDEBAR: CONTROLS, HELPLINES, AND SETTINGS ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/wheat.png", width=70)
    st.title("स्कीम साथी (Scheme Saathi)")
    st.caption("ग्रामीण भारत के लिए AI सरकारी योजना सहायक")

    # Mode Status Badge
    is_gemini = ai_svc.is_ai_available()
    if is_gemini:
        st.markdown(f'<div class="badge-gemini">🤖 सक्रिय: Gemini AI ({ai_svc.model_name})</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge-demo">⚡ सक्रिय: स्मार्ट डेमो मोड (नियम आधारित)</div>', unsafe_allow_html=True)
        st.caption("ℹ️ बिना API Key के सभी मुख्य परिदृश्य (Scenarios A, B, C) 100% कार्यशील हैं।")

    st.markdown("---")

    # Settings Accordion
    with st.expander("⚙️ AI एवं API सेटिंग्स (Settings)", expanded=False):
        user_key = st.text_input(
            "Gemini API Key (वैकल्पिक)",
            value=st.session_state.custom_api_key,
            type="password",
            help="यदि आपके पास Google Gemini API key है, तो यहाँ दर्ज करें। अन्यथा ऐप डेमो मोड में चलता रहेगा।"
        )
        if user_key != st.session_state.custom_api_key:
            st.session_state.custom_api_key = user_key
            st.rerun()

        model_choice = st.selectbox(
            "AI मॉडल चुनें",
            ["gemini-2.5-flash", "gemini-1.5-flash"],
            index=0
        )
        ai_svc.model_name = model_choice

    # Official Helpline Directory
    st.markdown("### 📞 प्रमुख सरकारी हेल्पलाइन")
    st.markdown("""
    - 🌾 **फसल बीमा (PMFBY):** `14447` (टोल-फ्री)
    - 🚜 **किसान सम्मान निधि:** `155261` / `1800-115-526`
    - 🩺 **आयुष्मान भारत:** `14555`
    - 🏠 **ग्रामीण आवास (PMAY-G):** `1800-11-6446`
    - 👷 **मनरेगा (MGNREGA):** `1800-345-6565`
    - 🌐 **राष्ट्रीय myScheme पोर्टल:** [myscheme.gov.in](https://www.myscheme.gov.in/)
    """)

    st.markdown("---")
    if st.button("🔄 बातचीत पुनः आरंभ करें (Reset)", use_container_width=True):
        st.session_state.conversation = []
        st.session_state.gathered_facts = {}
        st.session_state.voice_input_text = ""
        st.session_state.checked_documents = {}
        st.rerun()


# --- MAIN HEADER BANNER ---
st.markdown("""
<div class="main-header">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
        <div>
            <h1>🌾 स्कीम साथी (Scheme Saathi)</h1>
            <p>आपकी समस्या, सरकारी मदद का सही रास्ता।</p>
            <div>
                <span class="header-badge">🗣️ सरल हिंदी में समझें</span>
                <span class="header-badge">🎤 बोलकर पूछें (Voice Enabled)</span>
                <span class="header-badge">🏛️ 100% सत्यापित सरकारी स्रोत</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# --- MAIN TABS ---
tab_chat, tab_schemes, tab_documents, tab_telephony, tab_about = st.tabs([
    "💬 योजना सहायक (Chat Assistant)",
    "📚 सरकारी योजनाएं (Scheme Directory)",
    "📑 दस्तावेज़ चेकलिस्ट (Document Checklist)",
    "📞 फोन कॉल सेवा (Future Telephony)",
    "ℹ️ स्कीम साथी के बारे में (About)"
])


# ==============================================================================
# TAB 1: CHAT ASSISTANT & VOICE JOURNEY
# ==============================================================================
with tab_chat:
    # Quick Test Scenario Chips (For Hackathon Judges)
    st.markdown("##### ⚡ तुरंत पूछने के लिए कोई एक उदाहरण चुनें (Click to Demo):")
    sc1, sc2, sc3, sc4 = st.columns([1, 1, 1, 1])

    with sc1:
        if st.button("🌧️ Scenario A: फसल खराब", help="मेरी फसल बारिश से खराब हो गई है। मुझे सरकारी मदद चाहिए।", use_container_width=True):
            st.session_state.voice_input_text = "मेरी फसल बारिश से खराब हो गई है। मुझे सरकारी मदद चाहिए।"
            st.rerun()
    with sc2:
        if st.button("🚜 Scenario B: किसान सहायता", help="मैं किसान हूँ। मुझे खेती के लिए सरकारी सहायता चाहिए।", use_container_width=True):
            st.session_state.voice_input_text = "मैं किसान हूँ। मुझे खेती के लिए सरकारी सहायता चाहिए।"
            st.rerun()
    with sc3:
        if sc3.button("🏪 Scenario C: अन्य समस्या", help="मेरी दुकान में चोरी हो गई है, मुझे मुआवजा चाहिए।", use_container_width=True):
            st.session_state.voice_input_text = "मेरी दुकान में चोरी हो गई है, मुझे मुआवजा चाहिए।"
            st.rerun()
    with sc4:
        if sc4.button("🏥 अस्पताल इलाज सहायता", help="परिवार के इलाज के लिए अस्पताल का खर्च चाहिए।", use_container_width=True):
            st.session_state.voice_input_text = "परिवार के इलाज के लिए अस्पताल का खर्च चाहिए।"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Browser Web Speech API Voice Input Widget
    st.markdown("#### 🎤 बोलकर बताएं या लिखकर पूछें:")

    voice_html = """
    <div style="background: #F1F8E9; border: 2px dashed #4CAF50; border-radius: 12px; padding: 16px; text-align: center; font-family: 'Mukta', sans-serif;">
        <button id="start-record-btn" style="background: #E65100; color: white; border: none; padding: 12px 24px; border-radius: 30px; font-size: 18px; font-weight: bold; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 4px 10px rgba(230,81,0,0.3);">
            <span id="mic-icon">🎤</span> <span id="btn-text">यहाँ दबाकर हिंदी में बोलें</span>
        </button>
        <p id="record-status" style="margin-top: 10px; color: #555; font-size: 15px; font-weight: 500;">
            माइक बटन दबाएं और स्पष्ट हिंदी में अपनी समस्या बताएं।
        </p>
        <div id="transcript-display" style="display: none; background: white; border: 1px solid #C8E6C9; border-radius: 8px; padding: 10px; margin-top: 10px; font-size: 16px; color: #1B5E20; text-align: left;">
            <strong>सुनाई दिया:</strong> <span id="transcript-text"></span>
        </div>
    </div>

    <script>
    const recordBtn = document.getElementById('start-record-btn');
    const recordStatus = document.getElementById('record-status');
    const transcriptDisplay = document.getElementById('transcript-display');
    const transcriptText = document.getElementById('transcript-text');
    let recognizing = false;
    let recognition;

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRec();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'hi-IN';

        recognition.onstart = function() {
            recognizing = true;
            recordBtn.style.background = '#D32F2F';
            recordBtn.innerHTML = '🛑 <span>सुन रहे हैं... (बोलना बंद करने पर रुकेगा)</span>';
            recordStatus.innerText = 'कृपया बोलिए, आपकी आवाज़ रिकॉर्ड हो रही है...';
            recordStatus.style.color = '#D32F2F';
        };

        recognition.onresult = function(event) {
            let interimTranscript = '';
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
            const currentText = finalTranscript || interimTranscript;
            if (currentText) {
                transcriptDisplay.style.display = 'block';
                transcriptText.innerText = currentText;
            }
        };

        recognition.onerror = function(event) {
            recognizing = false;
            recordBtn.style.background = '#E65100';
            recordBtn.innerHTML = '🎤 <span>पुनः प्रयास करें</span>';
            if (event.error === 'not-allowed') {
                recordStatus.innerText = '⚠️ माइक्रोफोन की अनुमति नहीं मिली। कृपया ब्राउज़र में माइक की अनुमति दें या नीचे टाइप करें।';
            } else {
                recordStatus.innerText = 'सूचना: आवाज़ पकड़ने में समस्या हुई (' + event.error + ')। आप नीचे लिखकर भी पूछ सकते हैं।';
            }
            recordStatus.style.color = '#C62828';
        };

        recognition.onend = function() {
            recognizing = false;
            recordBtn.style.background = '#2E7D32';
            recordBtn.innerHTML = '✅ <span>आवाज़ दर्ज हुई (नीचे बॉक्स में देखें)</span>';
            recordStatus.innerText = 'यदि आपकी आवाज़ सही से दर्ज हुई है, तो नीचे दिए गए बॉक्स में जाँच कर "पूछें" दबाएं।';
            recordStatus.style.color = '#2E7D32';
        };

        recordBtn.onclick = function() {
            if (recognizing) {
                recognition.stop();
            } else {
                recognition.start();
            }
        };
    } else {
        recordBtn.disabled = true;
        recordBtn.style.background = '#9E9E9E';
        recordBtn.innerHTML = '⚠️ <span>ब्राउज़र में वॉइस सपोर्ट उपलब्ध नहीं</span>';
        recordStatus.innerText = 'आपके ब्राउज़र में Web Speech API समर्थित नहीं है। आप नीचे दिए गए इनपुट बॉक्स में आसानी से टाइप कर सकते हैं।';
    }
    </script>
    """
    components.html(voice_html, height=185)

    # Text Input Form
    with st.form("query_form", clear_on_submit=False):
        user_input = st.text_area(
            "अपनी समस्या यहाँ सरल शब्दों में लिखें (Type your question in Hindi):",
            value=st.session_state.voice_input_text,
            height=90,
            placeholder="उदाहरण: मेरी फसल बारिश से खराब हो गई है, क्या मुझे मुआवजा मिलेगा?"
        )
        col_submit, col_clear = st.columns([3, 1])
        with col_submit:
            submitted = st.form_submit_button("🔍 योजना खोजें एवं सलाह लें (Ask Scheme Saathi)", use_container_width=True)
        with col_clear:
            clear_pressed = st.form_submit_button("साफ करें", use_container_width=True)

    if clear_pressed:
        st.session_state.voice_input_text = ""
        st.rerun()

    # Process Query Submission
    if submitted and user_input.strip():
        query_text = user_input.strip()
        st.session_state.voice_input_text = ""

        # Append to conversation history
        st.session_state.conversation.append({
            "role": "user",
            "content": query_text
        })

        with st.spinner("🤖 स्कीम साथी आपकी समस्या का विश्लेषण कर रहे हैं..."):
            response_obj = ai_svc.process_query(
                user_message=query_text,
                conversation_history=[{"role": c["role"], "content": c["content"]} for c in st.session_state.conversation],
                gathered_facts=st.session_state.gathered_facts
            )

        st.session_state.conversation.append({
            "role": "assistant",
            "content": response_obj.reply_hi,
            "response_obj": response_obj
        })
        st.rerun()

    # Display Conversation History
    if not st.session_state.conversation:
        st.markdown("""
        <div class="saathi-card">
            <h3>🙏 राम-राम भाई जी! स्कीम साथी में आपका स्वागत है।</h3>
            <p style="font-size: 1.15rem; color: #424242;">
                हम ग्रामीण भारत के किसान भाइयों, मजदूर परिवारों और जरूरतमंद नागरिकों को 
                सरकारी योजनाओं की सही और प्रमाणित जानकारी सरल हिंदी में देते हैं।
            </p>
            <p style="font-size: 1.1rem; color: #2E7D32; font-weight: 600;">
                आप बेझिझक बोलकर या लिखकर बताएं — जैसे फसल नुकसान, खाद-बीज का खर्च, पक्का मकान, या बीमारी का मुफ्त इलाज!
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### 💬 आपकी बातचीत (Conversation History)")

        for idx, msg in enumerate(st.session_state.conversation):
            if msg["role"] == "user":
                with st.chat_message("user", avatar="👨‍🌾"):
                    st.markdown(f"**आप:** {msg['content']}")
            else:
                resp_obj: SchemeSaathiResponse = msg.get("response_obj")
                with st.chat_message("assistant", avatar="🌾"):
                    # Mode indicator
                    st.caption(f"स्रोत: {resp_obj.mode}")

                    # Main Conversational Hindi Reply
                    st.markdown(f"### 🌾 स्कीम साथी का सुझाव:")
                    st.markdown(resp_obj.reply_hi)

                    # Text-to-Speech Controls
                    speech_text = resp_obj.reply_hi
                    if resp_obj.follow_up_question_hi:
                        speech_text += " " + resp_obj.follow_up_question_hi

                    tts_col1, tts_col2 = st.columns([1, 3])
                    with tts_col1:
                        if st.button(f"🔊 सुनें (Listen Audio) #{idx}", key=f"audio_btn_{idx}"):
                            audio_bytes = TTSService.generate_hindi_audio(speech_text)
                            if audio_bytes:
                                st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                            else:
                                st.info("ऑडियो तैयार किया जा रहा है...")

                    # Unknown Problem Guidance (Scenario C)
                    if resp_obj.is_unknown_domain:
                        myscheme = scheme_svc.get_myscheme_info()
                        st.markdown(f"""
                        <div class="saathi-card-alert">
                            <h4>🌐 आधिकारिक myScheme पोर्टल पर खोजें:</h4>
                            <p>{myscheme.get('description_hi', '')}</p>
                            <a href="{myscheme.get('official_url')}" target="_blank" style="display: inline-block; background: #E65100; color: white; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-weight: bold;">
                                🔗 myScheme पोर्टल खोलें ({myscheme.get('official_url')})
                            </a>
                        </div>
                        """, unsafe_allow_html=True)

                    # Follow-up Question Section (1 concise question)
                    if resp_obj.follow_up_question_hi:
                        st.markdown(f"""
                        <div class="saathi-card-alert">
                            <h4 style="margin-top:0; color: #E65100;">❓ स्कीम साथी का एक ज़रूरी सवाल:</h4>
                            <p style="font-size: 1.15rem; font-weight: 600; margin-bottom: 0.5rem;">
                                {resp_obj.follow_up_question_hi}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                        # Quick reply options for common follow-ups
                        q_col1, q_col2, q_col3 = st.columns(3)
                        with q_col1:
                            if st.button("✅ हाँ, मेरे नाम ज़मीन है", key=f"ans_yes_land_{idx}"):
                                st.session_state.gathered_facts["is_landowner"] = True
                                st.session_state.voice_input_text = "हाँ, मेरे नाम पर ज़मीन (खतौनी) दर्ज है।"
                                st.rerun()
                        with q_col2:
                            if st.button("⏱️ नुकसान 72 घंटे के अंदर हुआ है", key=f"ans_72h_{idx}"):
                                st.session_state.gathered_facts["loss_within_72h"] = True
                                st.session_state.voice_input_text = "हाँ, फसल नुकसान को अभी 72 घंटे नहीं हुए हैं।"
                                st.rerun()
                        with q_col3:
                            if st.button("💳 बैंक खाता आधार से लिंक है", key=f"ans_aadhaar_{idx}"):
                                st.session_state.gathered_facts["has_aadhaar"] = True
                                st.session_state.voice_input_text = "हाँ, मेरा बैंक खाता आधार से लिंक है।"
                                st.rerun()

                    # Recommended Schemes Cards
                    if resp_obj.recommended_schemes:
                        st.markdown("#### 🎯 संबंधित सरकारी योजनाएं (Recommended Schemes):")

                        for s in resp_obj.recommended_schemes:
                            assessment = s.get("assessment", {})
                            status_label = assessment.get("status_label_hi", "संभावित पात्र")

                            with st.expander(f"🏛️ {s['name_hi']} — {status_label}", expanded=True):
                                # Scheme Metadata & Last Verified
                                m_col1, m_col2 = st.columns([2, 1])
                                with m_col1:
                                    st.caption(f"मंत्रालय: {s.get('ministry_hi', s.get('ministry', ''))}")
                                with m_col2:
                                    st.caption(f"✅ सत्यापित तिथि: {s.get('last_verified', 'अक्टूबर 2024')}")

                                # Scheme Details Sub-tabs
                                sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
                                    "💰 लाभ एवं फायदे",
                                    "🎯 पात्रता व शर्तें",
                                    "📑 आवश्यक दस्तावेज़",
                                    "🚀 आवेदन कैसे करें"
                                ])

                                with sub_tab1:
                                    st.markdown(f"**उद्देश्य:** {s['purpose_hi']}")
                                    st.markdown("**योजना के प्रमुख लाभ:**")
                                    for b in s.get("benefits_hi", []):
                                        st.markdown(f"- {b}")

                                with sub_tab2:
                                    st.markdown(f"**पात्रता स्थिति:** {status_label}")
                                    if assessment.get("reasons_hi"):
                                        st.success("✅ पूरी की गई शर्तें:")
                                        for r in assessment["reasons_hi"]:
                                            st.markdown(f"- {r}")

                                    if assessment.get("ineligible_reasons_hi"):
                                        st.error("❌ अपात्रता के कारण:")
                                        for ir in assessment["ineligible_reasons_hi"]:
                                            st.markdown(f"- {ir}")

                                    if assessment.get("missing_info_hi"):
                                        st.warning("⚠️ पुष्टि के लिए आवश्यक जानकारी:")
                                        for mi in assessment["missing_info_hi"]:
                                            st.markdown(f"- {mi}")

                                    st.markdown("**आधिकारिक पात्रता नियम:**")
                                    for el in s.get("eligibility_hi", []):
                                        st.markdown(f"- {el}")

                                    if s.get("exclusions_hi"):
                                        st.markdown("**कौन पात्र नहीं हैं (बहिष्करण):**")
                                        for ex in s["exclusions_hi"]:
                                            st.markdown(f"- {ex}")

                                with sub_tab3:
                                    st.markdown("**आवेदन के लिए आवश्यक दस्तावेज़:**")
                                    for doc in s.get("required_documents", []):
                                        st.markdown(f"- 📄 {doc}")

                                with sub_tab4:
                                    st.markdown("**आवेदन करने के चरण:**")
                                    for stp in s.get("application_steps_hi", []):
                                        st.markdown(stp)

                                    st.markdown("---")
                                    link_col1, link_col2 = st.columns([1, 1])
                                    with link_col1:
                                        st.markdown(f"🌐 **आधिकारिक पोर्टल:** [{s['official_source']}]({s['official_source']})")
                                    with link_col2:
                                        st.markdown(f"📞 **हेल्पलाइन नंबर:** `{s.get('helpline', '1800-180-1551')}`")

                    # Step-by-Step Action Checklist
                    if resp_obj.checklist:
                        st.markdown("#### ✅ आगे क्या करें — आसान चेकलिस्ट (Next Steps):")
                        for idx_step, step in enumerate(resp_obj.checklist, 1):
                            st.markdown(f"""
                            <div class="checklist-item">
                                <strong>कदम {idx_step}:</strong> {step}
                            </div>
                            """, unsafe_allow_html=True)

                    # Disclaimer
                    st.markdown(f"""
                    <div class="disclaimer-box">
                        {resp_obj.disclaimer_hi}
                    </div>
                    """, unsafe_allow_html=True)


# ==============================================================================
# TAB 2: COMPREHENSIVE SCHEMES DIRECTORY
# ==============================================================================
with tab_schemes:
    st.markdown("### 📚 सत्यापित सरकारी योजनाओं की डायरेक्टरी")
    st.write("स्कीम साथी के ज्ञानकोष में दर्ज सभी योजनाएं आधिकारिक सरकारी स्रोतों (Official Government Portals) से सत्यापित हैं।")

    all_schemes = scheme_svc.get_all_schemes()

    category_filter = st.selectbox(
        "योजना की श्रेणी चुनें (Filter by Category):",
        ["सभी योजनाएं (All)", "कृषि एवं फसल बीमा (Agriculture & Insurance)", "स्वास्थ्य एवं सामाजिक सुरक्षा (Health & Social Security)", "ग्रामीण आवास एवं रोजगार (Housing & Jobs)"]
    )

    filtered = all_schemes
    if "कृषि" in category_filter:
        filtered = [s for s in all_schemes if s["id"] in ["pm_kisan", "pmfby", "kcc"]]
    elif "स्वास्थ्य" in category_filter:
        filtered = [s for s in all_schemes if s["id"] in ["pmjay", "pm_kmy"]]
    elif "आवास" in category_filter:
        filtered = [s for s in all_schemes if s["id"] in ["pmay_g", "mgnrega"]]

    for s in filtered:
        with st.container():
            st.markdown(f"""
            <div class="saathi-card">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <h3 style="color: #1B5E20; margin: 0;">🏛️ {s['name_hi']}</h3>
                    <span style="background: #E8F5E9; color: #2E7D32; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 0.85rem;">
                        सत्यापित: {s.get('last_verified', 'अक्टूबर 2024')}
                    </span>
                </div>
                <p style="color: #616161; margin-top: 4px;"><em>{s['name']} — {s.get('ministry_hi', '')}</em></p>
                <p style="font-size: 1.1rem; color: #212121;">{s['purpose_hi']}</p>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                st.markdown("**💰 मुख्य लाभ:**")
                for b in s.get("benefits_hi", [])[:2]:
                    st.write(f"- {b}")
            with c2:
                st.markdown("**🎯 कौन पात्र है:**")
                for el in s.get("eligibility_hi", [])[:2]:
                    st.write(f"- {el}")
            with c3:
                st.markdown("**🌐 आधिकारिक संपर्क:**")
                st.write(f"📞 हेल्पलाइन: `{s.get('helpline', 'उपलब्ध नहीं')}`")
                st.markdown(f"[🔗 आधिकारिक वेबसाइट]({s.get('official_source', '#')})")
            st.markdown("---")

    # myScheme Portal Banner
    myscheme = scheme_svc.get_myscheme_info()
    st.markdown(f"""
    <div class="saathi-card-alert" style="text-align: center;">
        <h3>🌐 क्या आप अन्य 750+ सरकारी योजनाएं खोजना चाहते हैं?</h3>
        <p>{myscheme.get('description_hi')}</p>
        <a href="{myscheme.get('official_url')}" target="_blank" style="background: #E65100; color: white; padding: 10px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1.1rem; display: inline-block;">
            🇮🇳 myScheme आधिकारिक पोर्टल खोलें
        </a>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# TAB 3: DOCUMENT CHECKLIST (INTERACTIVE)
# ==============================================================================
with tab_documents:
    st.markdown("### 📑 सरकारी योजनाओं के लिए ज़रूरी दस्तावेज़ चेकलिस्ट")
    st.write("सरकारी योजनाओं का लाभ लेने के लिए अपने दस्तावेज़ पहले से तैयार रखें। आप नीचे टिक लगाकर अपनी तैयारी जांच सकते हैं:")

    col_docs1, col_docs2 = st.columns(2)

    with col_docs1:
        st.markdown("#### 🌾 कृषि एवं किसान योजनाएं (PM-KISAN, PMFBY, KCC)")
        st.checkbox("1. आधार कार्ड (Aadhaar Card - अनिवार्य)", key="doc_aadhaar")
        st.checkbox("2. ज़मीन का भू-अभिलेख / खसरा-खतौनी नकल (Khasra/Khatauni)", key="doc_land")
        st.checkbox("3. आधार लिंक बैंक पासबुक (Aadhaar Seeded Bank Account)", key="doc_bank")
        st.checkbox("4. बुआई प्रमाण पत्र / पटवारी घोषणा पत्र (Sowing Certificate)", key="doc_sowing")
        st.checkbox("5. फसल नुकसान की फोटो (72 घंटे के अंदर पीएमएफबीवाई हेतु)", key="doc_damage_photo")

    with col_docs2:
        st.markdown("#### 🏠 आवास, स्वास्थ्य एवं सामाजिक सुरक्षा (PM-JAY, PMAY-G, MGNREGA)")
        st.checkbox("6. राशन कार्ड / परिवार पहचान पत्र (Family ID / NFSA Ration Card)", key="doc_ration")
        st.checkbox("7. मनरेगा जॉब कार्ड (MGNREGA Job Card)", key="doc_mgnrega_card")
        st.checkbox("8. कच्चे मकान की वर्तमान फोटो (AwaasApp Verification हेतु)", key="doc_kutcha_house")
        st.checkbox("9. पासपोर्ट साइज़ फोटोग्राफ (Passport Size Photos)", key="doc_photo")
        st.checkbox("10. सक्रिय मोबाइल नंबर (ओटीपी एवं ई-केवाईसी हेतु)", key="doc_mobile")

    # Document Preparedness Score
    docs_checked = sum([
        st.session_state.get("doc_aadhaar", False),
        st.session_state.get("doc_land", False),
        st.session_state.get("doc_bank", False),
        st.session_state.get("doc_sowing", False),
        st.session_state.get("doc_damage_photo", False),
        st.session_state.get("doc_ration", False),
        st.session_state.get("doc_mgnrega_card", False),
        st.session_state.get("doc_kutcha_house", False),
        st.session_state.get("doc_photo", False),
        st.session_state.get("doc_mobile", False),
    ])
    st.progress(docs_checked / 10.0)
    st.info(f"📊 आपकी दस्तावेज़ तैयारी: 10 में से {docs_checked} दस्तावेज़ तैयार हैं।")

    st.markdown("""
    > [!IMPORTANT]
    > **गोपनीयता सूचना (Privacy Note):** स्कीम साथी एक डेमो व मार्गदर्शन प्रणाली है। हम कभी भी आपका असली आधार नंबर, बैंक खाता संख्या, पासवर्ड या ओटीपी नहीं मांगते। किसी भी अनधिकृत व्यक्ति को अपना बैंक विवरण न दें।
    """)


# ==============================================================================
# TAB 4: TELEPHONY & IVR FUTURE ARCHITECTURE
# ==============================================================================
with tab_telephony:
    st.markdown("### 📞 भविष्य का विजन: सामान्य फोन कॉल हेल्पलाइन (Toll-Free IVR)")
    st.markdown("""
    **दीर्घकालिक लक्ष्य:** ग्रामीण भारत में कई बुजुर्गों और नागरिकों के पास स्मार्टफोन या इंटरनेट नहीं होता। 
    हमारा उद्देश्य एक **टोल-फ्री फोन नंबर (जैसे 1800-XXX-XXXX)** प्रदान करना है, जिस पर कोई भी सामान्य फीचर फोन से कॉल करके 
    स्कीम साथी के इसी AI इंजन से शुद्ध हिंदी में बातचीत कर सके।
    """)

    # Interactive Telephony Flow Simulator
    st.markdown("#### 🎧 फोन कॉल बातचीत सिमुलेटर (Interactive Call Simulator):")

    telephony_svc = TelephonyService()

    sim_col1, sim_col2 = st.columns([1, 1])

    with sim_col1:
        st.markdown("""
        <div style="background: #263238; color: white; border-radius: 12px; padding: 1.2rem; font-family: monospace;">
            <p style="color: #4CAF50; font-weight: bold;">📞 INCOMING CALL DETECTED: +91 98765-XXXXX</p>
            <p>1. [PSTN Carrier] -> Call Received via Exotel/Twilio SIP Trunk</p>
            <p>2. [IVR Greeting] -> "नमस्ते। स्कीम साथी में आपका स्वागत है। आप अपनी समस्या बताएं..."</p>
            <p>3. [Hindi ASR] -> Streaming Audio -> Google Cloud Speech-to-Text / Whisper</p>
            <p>4. [Scheme Saathi Core] -> AI Context Grounding & 1 Follow-up Question</p>
            <p>5. [Neural Hindi TTS] -> Synthesizing Voice -> Streamed back to caller leg</p>
            <p>6. [Post Call SMS] -> Sending scheme link & helpline via SMS to caller</p>
        </div>
        """, unsafe_allow_html=True)

    with sim_col2:
        st.markdown("**कॉल सिमुलेशन चलाएं:**")
        call_scenario = st.selectbox(
            "सिमुलेशन परिदृश्य चुनें:",
            ["फसल नुकसान कॉल (PMFBY Call)", "किसान सम्मान निधि कॉल (PM-KISAN Call)", "शांति/मौन कॉल (Silence Timeout Handling)"]
        )

        if st.button("▶️ कॉल वार्तालाप चलाएं (Simulate Audio Call)", use_container_width=True):
            if "फसल नुकसान" in call_scenario:
                st.audio("https://raw.githubusercontent.com/datasets/gdp/master/data/gdp.csv", format="audio/mp3") if False else None
                st.success("🗣️ **कॉलर (किसान):** 'हैलो साब, हमारी धान की फसल भारी बारिश से पानी में डूब गई है, क्या करें?'")
                st.info("🤖 **स्कीम साथी IVR:** 'राम-राम भाई जी। यदि आपकी धान की फसल पानी में डूबी है तो 72 घंटे के भीतर टोल-फ्री 14447 पर तुरंत सूचना दर्ज कराएं। क्या आपकी फसल का बीमा कराया हुआ था?'")
            elif "सम्मान निधि" in call_scenario:
                st.success("🗣️ **कॉलर (किसान):** 'हमें खाद-बीज के लिए 6000 रुपये वाली सरकारी योजना का लाभ लेना है।'")
                st.info("🤖 **स्कीम साथी IVR:** 'नमस्ते। यह पीएम-किसान योजना है। क्या आपके नाम पर ज़मीन की खतौनी दर्ज है और बैंक में आधार लिंक है?'")
            else:
                silence_resp = telephony_svc.handle_silence_or_timeout("DEMO_CALL")
                st.warning(f"🤖 **स्कीम साथी IVR (मौन हैंडलिंग):** '{silence_resp['prompt_text_hi']}'")

    # Complete Telephony Architecture Diagram
    st.markdown("#### 📐 तकनीकी वास्तुकला (Technical Architecture):")
    st.code(telephony_svc.SYSTEM_ARCHITECTURE, language="text")

    st.markdown("""
    **लागत एवं व्यवहार्यता (Cost & Feasibility in India):**
    - **क्लाउड टेलीफोनी:** Exotel / Airtel IQ / Twilio Inbound Voice (~₹0.30 - ₹0.50 प्रति मिनट)
    - **स्पीच-टू-टेक्स्ट (ASR):** Google Cloud Speech-to-Text 'hi-IN' (~₹0.20 प्रति मिनट)
    - **AI रीजनिंग:** Google Gemini 2.5 Flash (~₹0.01 प्रति वार्तालाप)
    - **टेक्स्ट-टू-स्पीच (TTS):** Google Cloud Neural2 Hindi (~₹0.10 प्रति मिनट)
    - **कुल अनुमानित लागत:** मात्र ~₹1.00 प्रति 2 मिनट की कॉल, जिससे ग्रामीण किसानों को बिना इंटरनेट के सशक्त बनाया जा सकता है।
    """)


# ==============================================================================
# TAB 5: ABOUT & CREDITS
# ==============================================================================
with tab_about:
    st.markdown("### 🌾 स्कीम साथी (Scheme Saathi) के बारे में")
    st.markdown("""
    **प्रोजेक्ट का उद्देश्य:** 
    डिजिटल साक्षरता की कमी और भाषा की जटिलता के कारण भारत के लाखों ग्रामीण नागरिक उन सरकारी लाभों से वंचित रह जाते हैं जिनके वे कानूनी हकदार हैं।
    स्कीम साथी इस खाई को आर्टिफिशियल इंटेलिजेंस, सरल हिंदी भाषा और वॉइस तकनीक के जरिए पाटता है।

    **मुख्य विशेषताएं:**
    - 🗣️ **हिंदी-प्रथम इंटरफ़ेस:** बिना किसी तकनीकी जटिलता के शुद्ध सरल हिंदी में संवाद।
    - 🎤 **ब्राउज़र वॉइस इनपुट:** बोलने और सुनने की पूर्ण सुविधा (Web Speech API + gTTS)।
    - 🏛️ **सत्यापित डेटाबेस:** केवल pmkisan.gov.in, pmfby.gov.in, और myscheme.gov.in जैसे आधिकारिक पोर्टल्स पर आधारित तथ्य।
    - 🛡️ **भ्रम-मुक्त व पारदर्शी:** कोई झूठी मंजूरी की गारंटी नहीं; आधिकारिक सत्यापन की आवश्यकता को स्पष्ट रेखांकित करता है।
    - ⚡ **डुअल-इंजन आर्किटेक्चर:** Gemini AI उपलब्ध होने पर अत्याधुनिक LLM, अथवा शून्य-लागत स्मार्ट नियम-आधारित डेमो मोड।
    - 📞 **मॉड्यूलर टेलीफोनी रेडीनेस:** भविष्य में बिना इंटरनेट वाले फीचर फोन पर टोल-फ्री आईवीआर नंबर से जुड़ने की पूर्ण रूपरेखा।

    **तकनीकी स्टैक (Tech Stack):**
    - **फ्रंटएंड व बैकएंड:** Python, Streamlit
    - **आर्टिफिशियल इंटेलिजेंस:** Google Gemini 2.5 Flash (`google-genai` SDK)
    - **ध्वनि प्रसंस्करण (Audio/Voice):** Web Speech API (SpeechRecognition & SpeechSynthesis), gTTS
    - **परीक्षण (Testing):** Pytest (11/11 automated tests passed)
    """)

    st.markdown("""
    <div class="disclaimer-box">
        <strong>⚠️ वैधानिक अस्वीकरण (Legal Disclaimer):</strong><br>
        स्कीम साथी एक मार्गदर्शन और सूचनात्मक सहायक है। यह किसी भी सरकारी एजेंसी का अधिकृत अंग नहीं है और न ही आधिकारिक स्वीकृति प्रदान करता है। 
        अंतिम पात्रता, दस्तावेजों का सत्यापन और लाभ का वितरण केवल भारत सरकार और राज्य सरकारों के सक्षम विभागों के अधिकार क्षेत्र में है।
    </div>
    """, unsafe_allow_html=True)
