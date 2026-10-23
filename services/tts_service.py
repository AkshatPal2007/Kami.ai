"""
TTS Service: Provides Hindi text-to-speech audio generation using gTTS as a reliable backend,
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
    def generate_hindi_audio(text: str) -> Optional[bytes]:
        """
        Generates MP3 audio bytes using gTTS (Hindi lang 'hi').
        Returns bytes or None on error.
        """
        speech_text = TTSService.clean_text_for_speech(text)
        if not speech_text:
            return None

        try:
            from gtts import gTTS
            fp = io.BytesIO()
            tts = gTTS(text=speech_text, lang="hi", slow=False)
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception as e:
            print(f"[TTSService] gTTS error: {e}")
            return None

    @staticmethod
    def get_browser_speech_js(text: str) -> str:
        """
        Returns safe JavaScript snippet for Web Speech API SpeechSynthesis.
        """
        cleaned = TTSService.clean_text_for_speech(text)
        # Escape for JS string literal
        escaped = cleaned.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
        return f"""
        <script>
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance('{escaped}');
                utterance.lang = 'hi-IN';
                utterance.rate = 0.95;
                window.speechSynthesis.speak(utterance);
            }} else {{
                alert('आपके ब्राउज़र में आवाज़ (Speech Synthesis) समर्थित नहीं है।');
            }}
        </script>
        """
