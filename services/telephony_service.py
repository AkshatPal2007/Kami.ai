"""
Telephony Service: Architectural blueprint and modular integration layer
for connecting Scheme Saathi to real telephone numbers (IVR / Inbound Calling)
using Indian telecommunication providers such as Exotel or Twilio.
"""

from typing import Dict, Any, Optional
import json


class TelephonyService:
    """
    Modular telephony engine enabling the same Scheme Saathi AI core
    to interface with PSTN/cellular phone calls for rural Indians.
    """

    SYSTEM_ARCHITECTURE = """
    ========================================================================================
                 SCHEME SAATHI — TOLL-FREE TELEPHONE ARCHITECTURE (IVR)
    ========================================================================================

    [ Rural Citizen ] (Normal Mobile / Feature Phone, No Internet Required)
           │
           ▼ (Dials Toll-Free Number e.g. 1800-XXX-XXXX)
    [ Indian Telecom PSTN / Cellular Network (Jio / Airtel / BSNL) ]
           │
           ▼ (SIP Trunking / Inbound Call Webhook)
    [ Cloud Telephony Platform: Exotel / Twilio Voice ]
           │
           ├──▶ 1. Inbound Webhook (Caller ID, Call SID, Location)
           │
           ▼
    [ Scheme Saathi Voice Gateway (FastAPI / WebSockets) ]
           │
           ├──▶ 2. Real-Time Audio Stream (8kHz/16kHz PCM)
           │      │
           │      ▼
           │    [ Hindi ASR / Speech-to-Text ]
           │    (Google Cloud Speech-to-Text 'hi-IN' / OpenAI Whisper Realtime)
           │      │
           │      ▼ (Transcribed Hindi Text)
           │
           ├──▶ 3. Scheme Saathi Core AI Engine (AIService & SchemeService)
           │      │
           │      ├── Discovers Relevant Verified Schemes (PM-KISAN, PMFBY, etc.)
           │      ├── Identifies Missing Details & Generates 1 Follow-up Question
           │      └── Formulates Concise Conversational Hindi Guidance
           │      │
           │      ▼ (Hindi Response Text)
           │
           ├──▶ 4. Neural Hindi TTS (Text-to-Speech)
           │    (Google Cloud Text-to-Speech 'hi-IN-Neural2' / ElevenLabs Hindi)
           │      │
           │      ▼ (8kHz Audio Stream for Phone)
           │
           ▼ (Plays Audio into Call Channel with Barge-In / Interruption Support)
    [ Cloud Telephony Call Leg ]
           │
           ▼ (Audio plays on caller's phone speaker)
    [ Rural Citizen Hears Clear Hindi Advice ]
           │
           ▼ (On Call Disconnect)
    [ Automated SMS Follow-up Gateway (SMS Gupshup / Exotel SMS) ]
           └── Sends SMS with Official Portal Link, Helpline No. & Checklist to Caller's Phone!
    ========================================================================================
    """

    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def handle_inbound_call_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes initial incoming call webhook from telecom provider (Exotel/Twilio).
        Initializes session and returns initial greeting IVR response.
        """
        call_sid = payload.get("CallSid") or payload.get("CallSid", "DEMO_CALL_123")
        caller_phone = payload.get("From") or payload.get("Caller", "9876543210")

        # Initialize session state
        self.active_sessions[call_sid] = {
            "call_sid": call_sid,
            "caller_phone": caller_phone,
            "state": "GREETING",
            "silence_counter": 0,
            "gathered_facts": {},
            "conversation_history": []
        }

        greeting_hi = (
            "नमस्ते। स्कीम साथी में आपका स्वागत है। "
            "आप अपनी खेती या सरकारी सहायता की समस्या बताएं, हम आपकी मदद करेंगे। "
            "कृपया बीप के बाद बोलें।"
        )

        # Returns standard Telephony Control XML / JSON
        return {
            "action": "play_and_record",
            "prompt_text_hi": greeting_hi,
            "record_max_duration_seconds": 15,
            "silence_timeout_seconds": 3,
            "barge_in_allowed": True,
            "callback_url": f"/api/telephony/process-speech?call_sid={call_sid}"
        }

    def handle_silence_or_timeout(self, call_sid: str) -> Dict[str, Any]:
        """
        Gracefully handles rural callers who may pause, have network drops, or hesitate.
        """
        session = self.active_sessions.get(call_sid, {})
        silence_count = session.get("silence_counter", 0) + 1
        session["silence_counter"] = silence_count

        if silence_count == 1:
            prompt = "नमस्ते भाई जी, क्या आप हमें सुन पा रहे हैं? आप अपनी समस्या बेझिझक बताएं।"
            return {"action": "reprompt", "prompt_text_hi": prompt, "end_call": False}
        elif silence_count == 2:
            prompt = "आपकी आवाज़ नहीं आ पा रही है। कृपया नेटवर्क में आकर पुनः प्रयास करें या बीप के बाद बोलें।"
            return {"action": "reprompt", "prompt_text_hi": prompt, "end_call": False}
        else:
            prompt = "नेटवर्क में समस्या के कारण कॉल समाप्त हो रही है। हम आपके नंबर पर एसएमएस द्वारा जानकारी भेज रहे हैं। धन्यवाद।"
            return {"action": "hangup", "prompt_text_hi": prompt, "end_call": True}

    def generate_post_call_sms(self, matched_scheme_name: str, helpline: str, official_url: str) -> str:
        """
        Generates simple SMS text in Hindi sent to caller's phone after the call.
        """
        return (
            f"स्कीम साथी: आपके लिए योजना - {matched_scheme_name}। "
            f"आधिकारिक हेल्पलाइन: {helpline}। "
            f"वेबसाइट: {official_url}। "
            f"अंतिम पात्रता सरकारी नियमों के अधीन है।"
        )
