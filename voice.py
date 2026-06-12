import win32com.client

class VoiceEngine:
    def __init__(self):
        self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
        self.speaker.Rate = -1
        self.speaker.Volume = 100

        # Force the voice to female (Zira)
        voices = self.speaker.GetVoices()
        for i in range(voices.Count):
            voice = voices.Item(i)
            if "zira" in voice.GetDescription().lower():
                self.speaker.Voice = voice
                break
                
    def speak(self, text):
        print(f"JARVIS: {text}")
        self.speaker.Speak(text)

if __name__ == "__main__":
    engine = VoiceEngine()
    engine.speak("Hello, I am Jarvis. System is fully operational.")

