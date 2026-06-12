import re
import pyttsx3


class VoiceEngine:
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 170)    # words per minute (170 feels natural)
            self.engine.setProperty('volume', 1.0)
            self._select_voice()
        except Exception as e:
            print(f"[Voice] Initialization error: {e}")
            self.engine = None

    def _select_voice(self):
        """
        Voice preference order:
          1. Microsoft Zira (Windows female voice)
          2. Any voice with 'female' or 'woman' in the name
          3. First available voice (silent fallback — never crashes)
        """
        voices = self.engine.getProperty('voices')
        if not voices:
            return

        for voice in voices:
            if 'zira' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                print(f"[Voice] Using: {voice.name}")
                return

        for voice in voices:
            if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                print(f"[Voice] Using: {voice.name}")
                return

        # Fallback: whatever is available
        self.engine.setProperty('voice', voices[0].id)
        print(f"[Voice] Using: {voices[0].name}")

    def _clean_for_speech(self, text: str) -> str:
        """
        Strip symbols that sound awful when the LLM response is read aloud:
          - Markdown: * _ ` # [ ] ( )
          - Bullet points and dashes used as list markers
          - Excessive whitespace
        """
        text = re.sub(r'[*_`#\[\]()\-]+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def speak(self, text: str):
        if not text:
            return
        text = self._clean_for_speech(str(text))
        print(f"FRIDAY: {text}")
        if not self.engine:
            return
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"[Voice] Speech error: {e}")
            # Try one reinit before giving up
            try:
                self.engine = pyttsx3.init()
                self._select_voice()
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception:
                pass


if __name__ == "__main__":
    engine = VoiceEngine()
    engine.speak("Hello, I am Friday. All systems are operational.")