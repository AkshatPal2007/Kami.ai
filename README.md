# 🌾 Scheme Saathi (स्कीम साथी)
### AI-Powered Government Scheme Assistant for Rural India
> *"आपकी समस्या, सरकारी मदद का सही रास्ता।"*

Scheme Saathi is an AI-powered conversational government-benefits assistant designed for rural Indians and citizens with limited digital literacy. It allows a user to explain their problem in simple, conversational Hindi (via text or voice) and receive truthful, grounded guidance on relevant government schemes without misleading promises.

---

## 🌟 Key Features

1. **Hindi-First Conversational Interface (हिंदी-प्रथम अनुभव):**
   - Welcomes users in warm, empathetic Hindi.
   - Accepts both typed input and **voice input** via browser microphone.
   - Speaks answers aloud via **Hindi Text-to-Speech (TTS)**.
2. **Dual AI Engine (Gemini AI + Smart Demo Mode):**
   - **Google Gemini API** integration (`google-genai` SDK) when configured.
   - **Smart Demo Mode (Rule-Based Expert Engine):** Runs 100% out-of-the-box without crashing when no API key is set.
3. **Verified Government Scheme Knowledge Base:**
   - Grounded strictly in verified government data:
     - **PM-KISAN:** Pradhan Mantri Kisan Samman Nidhi (https://pmkisan.gov.in/)
     - **PMFBY:** Pradhan Mantri Fasal Bima Yojana (https://pmfby.gov.in/)
     - **KCC:** Kisan Credit Card (https://www.myscheme.gov.in/schemes/kcc)
     - **PM-KMY:** Pradhan Mantri Kisan Maandhan Yojana (https://maandhan.in/)
     - **PMAY-G:** Pradhan Mantri Awaas Yojana - Gramin (https://pmayg.nic.in/)
     - **PM-JAY:** Ayushman Bharat (https://nha.gov.in/PM-JAY)
     - **MGNREGA:** Mahatma Gandhi NREGS (https://nrega.nic.in/)
     - **myScheme Portal:** Single-window national discovery portal (https://www.myscheme.gov.in/)
4. **Transparent Eligibility & Next Steps:**
   - Distinguishes between *Potentially Eligible*, *Apparently Ineligible*, and *Insufficient Information*.
   - Never makes false guarantees; highlights that final approval rests with the relevant government authority.
   - Highlights the critical **72-hour reporting deadline** for crop damage under PMFBY.
   - Provides step-by-step actionable checklists and official links.
5. **Interactive Document Checklist:**
   - Helps rural users track essential documents (Aadhaar, Khasra-Khatauni land records, bank passbook, sowing certificates).
6. **Future Telephone Architecture (Toll-Free IVR):**
   - Complete technical roadmap and interactive simulator for incoming feature phone calls via Indian telecom providers like Exotel.

---

## 🛠️ Technology Stack

- **Frontend & App Framework:** Python 3.10+, Streamlit
- **AI / LLM:** Google Gemini 2.5 Flash / 1.5 Flash via official `google-genai` SDK
- **Speech Recognition:** Web Speech API (`SpeechRecognition` with `hi-IN`)
- **Speech Synthesis:** Web Speech API (`SpeechSynthesis`) & `gTTS`
- **Testing:** Pytest (11/11 automated tests passing)

---

## 🚀 Quick Start Guide (Windows PowerShell)

### Step 1: Open Terminal and Navigate to Project Directory
```powershell
cd C:\Users\Akshat\Desktop\Hackathon\Techutsav
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Run the Automated Test Suite
Verify that all unit tests and scenarios pass:
```powershell
pytest -v
```

### Step 4: Launch the Web Application
```powershell
streamlit run app.py
```
The application will open automatically in your browser at `http://localhost:8501`.

---

## 🔑 Running with or without Gemini API Key

### Option A: Running in Demo Mode (No API Key Required)
Simply launch the app without configuring an API key:
```powershell
streamlit run app.py
```
The app will display the badge: `⚡ सक्रिय: स्मार्ट डेमो मोड (नियम आधारित)` in the sidebar. All test scenarios (Scenarios A, B, C, D, E) function seamlessly.

### Option B: Running with Gemini API Key
You can provide your Gemini API key in any of three ways:

1. **Via PowerShell Environment Variable:**
   ```powershell
   $env:GEMINI_API_KEY="your_actual_gemini_api_key_here"
   streamlit run app.py
   ```
2. **Via `.env` file:**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```
3. **Directly in the App UI:**
   In the Streamlit sidebar, open **⚙️ AI एवं API सेटिंग्स (Settings)** and paste your API key into the input field.

---

## 🧪 Hackathon Demo Scenarios

The app includes one-click demo buttons at the top of the chat screen for these exact scenarios:

### Scenario A: Crop Damage (फसल नुकसान)
- **User Input:** *"मेरी फसल बारिश से खराब हो गई है। मुझे सरकारी मदद चाहिए।"*
- **Assistant Behavior:**
  - Identifies **PMFBY (Pradhan Mantri Fasal Bima Yojana)**.
  - Explains that compensation applies to insured notified crops in notified areas.
  - **Crucial Rule:** Warns the user that localized calamity damage must be reported **within 72 hours** to 14447 or via the Crop Insurance App.
  - Does NOT promise compensation; advises field inspection steps.

### Scenario B: Farmer Support (किसान सहायता)
- **User Input:** *"मैं किसान हूँ। मुझे खेती के लिए सरकारी सहायता चाहिए।"*
- **Assistant Behavior:**
  - Explores **PM-KISAN** (₹6,000/year income support) and **KCC** (Kisan Credit Card 4% interest loan).
  - Asks a concise follow-up question regarding land ownership (Khasra-Khatauni) and e-KYC status.

### Scenario C: Unknown Problem (अन्य समस्या)
- **User Input:** *"मेरी दुकान में चोरी हो गई है, मुझे मुआवजा चाहिए।"*
- **Assistant Behavior:**
  - Transparently explains that shop theft is outside the current agricultural/rural welfare database.
  - Does NOT invent a fake scheme.
  - Directs the user to the official **myScheme Portal** (https://www.myscheme.gov.in/) and recommends filing an FIR.

### Scenario D: No API Key (बिना API की)
- The application launches gracefully, detects the absence of the API key, and switches to the clearly labeled Demo Mode without crashing.

### Scenario E: Voice Unsupported / Typing Fallback
- If the browser does not support `webkitSpeechRecognition` or microphone permission is denied, the voice widget displays a clear Hindi message and the user can type normally in the text area.

---

## 📞 Future Telephony Architecture (Phone Calling Vision)

While the hackathon deliverable is a functional web application, the backend is architected in a modular fashion to support incoming telephone calls from basic feature phones:

```
[ Rural Citizen (Feature Phone) ]
       │
       ▼ (Dials Toll-Free 1800-XXX-XXXX)
[ Telecom Network (PSTN / Jio / Airtel / BSNL) ]
       │
       ▼ (Inbound SIP Webhook)
[ Cloud Telephony Gateway (Exotel / Twilio Voice) ]
       │
       ├── 1. Streaming Hindi ASR (Google Cloud Speech-to-Text / Whisper 'hi-IN')
       │      └── Converts voice to Hindi text
       │
       ├── 2. Scheme Saathi Core Engine (AIService + SchemeService)
       │      └── Determines relevant scheme & generates 1 concise follow-up question
       │
       ├── 3. Neural Hindi TTS (Google Cloud Neural2 'hi-IN' / ElevenLabs)
       │      └── Synthesizes Hindi audio back into the phone call channel
       │
       └── 4. Automated SMS Follow-up
              └── Sends official portal link and helpline to the caller's mobile via SMS
```

An interactive simulator of this phone conversation is available under the **"📞 फोन कॉल सेवा"** tab in the app.

---

## 📁 Project Structure

```
Techutsav/
├── app.py                      # Main Streamlit web application
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment file (no secrets)
├── .gitignore                  # Git exclusions for secrets and caches
├── README.md                   # Complete documentation and launch guide
├── data/
│   └── schemes.json            # Structured verified government schemes database
├── services/
│   ├── __init__.py
│   ├── scheme_service.py       # Scheme retrieval, search & eligibility engine
│   ├── ai_service.py           # Gemini LLM integration + Demo fallback engine
│   ├── tts_service.py          # Hindi Text-to-Speech audio generator
│   └── telephony_service.py    # Inbound call IVR architecture & state machine
└── tests/
    ├── __init__.py
    ├── test_scheme_service.py  # Unit tests for scheme matching & eligibility
    └── test_ai_service.py      # Unit tests for AI responses & demo mode
```

---

## ⚖️ Data Accuracy and Trust Notice

- **Official Sources Only:** All scheme rules, benefit amounts, helpline numbers, and URLs are sourced directly from verified government domains (`.gov.in` and `.nic.in`).
- **No False Guarantees:** Scheme Saathi is an informational guidance tool. It does not possess direct access to private government databases and cannot officially approve or reject scheme claims.
- **Privacy First:** Scheme Saathi never collects real Aadhaar numbers, bank account numbers, passwords, or OTPs.
