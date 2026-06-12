import os
import sys
import pyaudio
import numpy as np
import time
import json
import urllib.request
import zipfile
import speech_recognition as sr
from vosk import Model, KaldiRecognizer

# Parameters for Audio and Clap Detection
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CLAP_THRESHOLD = 8500  # Lowered to 8500 so you can clap from further away, but still high enough to ignore background noise
CLAP_MAX_DELAY = 1.0   # max seconds between claps
CLAP_MIN_DELAY = 0.2   # min seconds between claps

class Listener:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.model_path = "model"
        self._ensure_vosk_model()
        self.model = Model(self.model_path)
        self.recognizer = KaldiRecognizer(self.model, RATE)
        self.recognizer.SetWords(False)
        self.r = sr.Recognizer()

    def _ensure_vosk_model(self):
        """Downloads the Vosk lightweight english model if it doesn't exist."""
        if not os.path.exists(self.model_path):
            print("Downloading offline language model (Vosk). Please wait...")
            url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
            zip_path = "vosk_model.zip"
            urllib.request.urlretrieve(url, zip_path)
            print("Extracting model...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(".")
            os.rename("vosk-model-small-en-us-0.15", self.model_path)
            os.remove(zip_path)
            print("Model downloaded and extracted!")

    def listen_for_wake(self):
        """Listens continuously for a Double Clap or the word 'Jarvis'"""
        print("\nListening for wake word 'Jarvis' or a Double Clap...")
        stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        stream.start_stream()

        last_clap_time = 0

        # Reset recognizer just in case
        self.recognizer.Reset()

        try:
            while True:
                data = stream.read(CHUNK, exception_on_overflow=False)
                
                # 1. Check for Clap (Amplitude Spike)
                audio_data = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))
                
                if rms > CLAP_THRESHOLD:
                    current_time = time.time()
                    time_since_last_clap = current_time - last_clap_time
                    if CLAP_MIN_DELAY < time_since_last_clap < CLAP_MAX_DELAY:
                        print(f"Double clap detected! (RMS: {rms:.2f})")
                        stream.stop_stream()
                        stream.close()
                        return True
                    elif time_since_last_clap >= CLAP_MAX_DELAY:
                        last_clap_time = current_time

                # 2. Check for Wake Word 'Jarvis' or 'Friday' using Vosk
                wake_words = ["jarvis", "friday", "travis", "jervis", "drivers"]
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower()
                    if text: 
                        print(f"[Debug] Mic heard: {text}", end='\r')
                    if any(w in text for w in wake_words):
                        print("\nWake word detected in final result!")
                        stream.stop_stream()
                        stream.close()
                        return True
                else:
                    # Also check partial results for faster response
                    partial = json.loads(self.recognizer.PartialResult())
                    text = partial.get("partial", "").lower()
                    if text:
                        print(f"[Debug] Mic hearing: {text}", end='\r')
                    if any(w in text for w in wake_words):
                        print("\nWake word detected instantly!")
                        stream.stop_stream()
                        stream.close()
                        return True
                        
        except KeyboardInterrupt:
            stream.stop_stream()
            stream.close()
            sys.exit(0)

    def listen_for_command(self):
        """Listens for the actual command after waking up using SpeechRecognition."""
        print("Listening for your command...")
        
        with sr.Microphone(sample_rate=RATE) as source:
            # Dynamically adjust to background noise so we don't listen forever
            self.r.adjust_for_ambient_noise(source, duration=0.5)
            print("Speak now...")
            try:
                # Listen for up to 10 seconds of speech, timing out if silent for 5 seconds
                audio = self.r.listen(source, timeout=5, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                print("Timeout: No speech detected.")
                return ""
        
        print("Processing audio...")
        try:
            # Use Google's free online API for blazing fast and perfectly accurate command recognition
            text = self.r.recognize_google(audio)
            print(f"Recognized Command: '{text}'")
            return text
        except sr.UnknownValueError:
            print("Could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return ""

if __name__ == "__main__":
    l = Listener()
    if l.listen_for_wake():
        cmd = l.listen_for_command()
        print(f"You said: {cmd}")
