"""
TTS Service: Provides Hindi and English text-to-speech audio generation using gTTS,
and generates client-side Web Speech API JavaScript for instant browser playback.
"""

import io
import re
from typing import Optional


class TTSService:
    @staticmethod
    def clean_text_for_speech(text: str, max_chars: int = 400) -> str:
        """
        Cleans markdown formatting, links, and trims long text
        so audio playback is natural and doesn't drone on.
        """
        if not text:
            return ""

        # Remove markdown formatting like **, __, #, URLs
        cleaned = re.sub(r"https?://\S+", "", text)
        cleaned = re.sub(r"[*_#`\[\]]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Trim to max_chars at word boundary
        if len(cleaned) > max_chars:
            trimmed = cleaned[:max_chars]
            last_space = trimmed.rfind(" ")
            if last_space > 0:
                cleaned = trimmed[:last_space] + "..."
            else:
                cleaned = trimmed + "..."

        return cleaned

    @staticmethod
    def generate_audio(text: str, lang: str = "hi") -> Optional[bytes]:
        """
        Generates MP3 audio bytes using gTTS (supports 'hi' or 'en').
        """
        speech_text = TTSService.clean_text_for_speech(text)
        if not speech_text:
            return None

        # Normalize lang code
        tts_lang = "en" if lang.startswith("en") else "hi"

        try:
            from gtts import gTTS
            fp = io.BytesIO()
            tts = gTTS(text=speech_text, lang=tts_lang, slow=False)
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception as e:
            print(f"[TTSService] gTTS error: {e}")
            return None

    @staticmethod
    def generate_hindi_audio(text: str) -> Optional[bytes]:
        """Backward compatibility wrapper."""
        return TTSService.generate_audio(text, lang="hi")

    @staticmethod
    def get_browser_speech_js(text: str, lang: str = "hi") -> str:
        """
        Returns safe JavaScript snippet for Web Speech API SpeechSynthesis.
        """
        cleaned = TTSService.clean_text_for_speech(text)
        escaped = cleaned.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
        speech_lang = "en-IN" if lang.startswith("en") else "hi-IN"
        return f"""
        <script>
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance('{escaped}');
                utterance.lang = '{speech_lang}';
                utterance.rate = 0.95;
                window.speechSynthesis.speak(utterance);
            }}
        </script>
        """
