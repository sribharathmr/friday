import os
import sys
import json
import time
import zipfile
import urllib.request

import pyaudio
import numpy as np
import speech_recognition as sr
from vosk import Model, KaldiRecognizer

# ── Audio parameters ───────────────────────────────────────────────────────────
CHUNK           = 1024
FORMAT          = pyaudio.paInt16
CHANNELS        = 1
RATE            = 16000

# Clap detection thresholds
CLAP_THRESHOLD  = 8500   # RMS amplitude — high enough to ignore room noise
CLAP_MAX_DELAY  = 1.0    # seconds: max gap between two claps to count as a double-clap
CLAP_MIN_DELAY  = 0.2    # seconds: min gap (ignores single sustained loud noise)

# Vosk model
VOSK_MODEL_DIR  = "model"
VOSK_MODEL_URL  = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
VOSK_MODEL_ZIP  = "vosk_model.zip"
VOSK_MODEL_NAME = "vosk-model-small-en-us-0.15"

# All phrases that wake Friday up.
# Include common mis-recognitions of "Friday" and "Jarvis" that Vosk produces.
WAKE_WORDS = {
    "friday", "hey friday",
    "jarvis", "hey jarvis",
    "travis", "jervis", "drivers",   # common Vosk mis-hearings of "jarvis"
}


class Listener:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self._ensure_vosk_model()
        self.model      = Model(VOSK_MODEL_DIR)
        self.recognizer = KaldiRecognizer(self.model, RATE)
        self.recognizer.SetWords(False)
        self.sr_recognizer = sr.Recognizer()

    # ── Vosk model bootstrap ──────────────────────────────────────────────────

    def _ensure_vosk_model(self):
        if not os.path.exists(VOSK_MODEL_DIR):
            print("[Listener] Downloading offline wake-word model (one-time setup)...")
            urllib.request.urlretrieve(VOSK_MODEL_URL, VOSK_MODEL_ZIP)
            print("[Listener] Extracting...")
            with zipfile.ZipFile(VOSK_MODEL_ZIP, 'r') as zf:
                zf.extractall(".")
            os.rename(VOSK_MODEL_NAME, VOSK_MODEL_DIR)
            os.remove(VOSK_MODEL_ZIP)
            print("[Listener] Model ready.")

    # ── Wake detection ────────────────────────────────────────────────────────

    def listen_for_wake(self) -> bool:
        """
        Blocks until a double-clap OR a wake word is detected.
        Returns True when triggered.
        Handles stream cleanup safely in all exit paths.
        """
        print("\n[Listener] Waiting for wake word or double clap...")
        stream = self.p.open(
            format=FORMAT, channels=CHANNELS, rate=RATE,
            input=True, frames_per_buffer=CHUNK
        )
        stream.start_stream()
        self.recognizer.Reset()
        last_clap_time = 0.0

        try:
            while True:
                data = stream.read(CHUNK, exception_on_overflow=False)

                # ── 1. Clap detection (amplitude spike) ──────────────────────
                audio_np = np.frombuffer(data, dtype=np.int16)
                rms = float(np.sqrt(np.mean(np.square(audio_np.astype(np.float32)))))

                if rms > CLAP_THRESHOLD:
                    now = time.time()
                    gap = now - last_clap_time
                    if CLAP_MIN_DELAY < gap < CLAP_MAX_DELAY:
                        print(f"[Listener] Double clap detected (RMS={rms:.0f})")
                        return True
                    if gap >= CLAP_MAX_DELAY:
                        last_clap_time = now  # first clap of a potential pair

                # ── 2. Wake word via Vosk (offline, low-latency) ─────────────
                if self.recognizer.AcceptWaveform(data):
                    result_text = json.loads(self.recognizer.Result()).get("text", "").lower()
                    if result_text:
                        print(f"[Listener] Heard: {result_text}", end='\r')
                    if any(w in result_text for w in WAKE_WORDS):
                        print(f"\n[Listener] Wake word in final result: '{result_text}'")
                        return True
                else:
                    # Also check partial results for faster response
                    partial_text = json.loads(self.recognizer.PartialResult()).get("partial", "").lower()
                    if partial_text:
                        print(f"[Listener] Hearing: {partial_text}      ", end='\r')
                    if any(w in partial_text for w in WAKE_WORDS):
                        print(f"\n[Listener] Wake word in partial: '{partial_text}'")
                        return True

        except KeyboardInterrupt:
            print("\n[Listener] Interrupted.")
            sys.exit(0)
        except Exception as e:
            print(f"\n[Listener] Audio error: {e}")
            return False
        finally:
            # Always clean up the stream, even on exception
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass

    # ── Command recognition ───────────────────────────────────────────────────

    def listen_for_command(self) -> str:
        """
        Listens for the actual spoken command using Google Speech Recognition.
        Falls back to an empty string on timeout or recognition failure.
        """
        print("[Listener] Listening for your command...")
        try:
            with sr.Microphone(sample_rate=RATE) as source:
                self.sr_recognizer.adjust_for_ambient_noise(source, duration=0.4)
                print("[Listener] Speak now...")
                try:
                    audio = self.sr_recognizer.listen(source, timeout=5, phrase_time_limit=10)
                except sr.WaitTimeoutError:
                    print("[Listener] No speech detected (timeout).")
                    return ""

            print("[Listener] Processing...")
            text = self.sr_recognizer.recognize_google(audio)
            print(f"[Listener] Recognized: '{text}'")
            return text

        except sr.UnknownValueError:
            print("[Listener] Could not understand audio.")
            return ""
        except sr.RequestError as e:
            print(f"[Listener] Google STT error: {e}")
            return ""
        except Exception as e:
            print(f"[Listener] Unexpected error: {e}")
            return ""


if __name__ == "__main__":
    l = Listener()
    if l.listen_for_wake():
        cmd = l.listen_for_command()
        print(f"You said: {cmd}")