import time
from voice import VoiceEngine
from brain import Brain
from listener import Listener
from skills import Skills


# ── Exit phrases ───────────────────────────────────────────────────────────────
# If any of these appear in a command, Friday says goodbye and exits cleanly.
EXIT_WORDS = {"stop", "exit", "goodbye", "bye", "shutdown", "quit", "terminate", "close"}


# ── Skill dispatch table ───────────────────────────────────────────────────────
# Each entry: (trigger_fn, handler_fn)
#   trigger_fn(cmd: str) -> bool  — True if this skill should handle the command
#   handler_fn(cmd: str) -> str   — executes the skill and returns the spoken response
#
# Rules are checked in order; first match wins.
# Commands that match nothing fall through to the AI brain.

def build_dispatch(skills: Skills) -> list:

    def has(*words):
        """All words must appear in cmd."""
        return lambda cmd: all(w in cmd for w in words)

    def has_any(*words):
        """At least one word must appear in cmd."""
        return lambda cmd: any(w in cmd for w in words)

    return [

        # ── Web & media ───────────────────────────────────────────────────────
        (has("open", "youtube"),
         lambda cmd: skills.open_webpage("youtube")),

        (has("open", "google"),
         lambda cmd: skills.open_webpage("google")),

        (lambda cmd: "play" in cmd and any(k in cmd for k in ["youtube", "song", "music"]),
         lambda cmd: skills.play_music(
             cmd.replace("play", "").replace("on youtube", "")
                .replace("youtube", "").replace("song", "").replace("music", "").strip()
         )),

        (lambda cmd: any(k in cmd for k in ["search for", "search", "look up", "google"]) and "open" not in cmd,
         lambda cmd: skills.search_web(
             re.strip_prefixes(cmd, ["search for", "search", "look up", "google"])
         )),

        # ── Volume ────────────────────────────────────────────────────────────
        (lambda cmd: "volume" in cmd and any(k in cmd for k in ["up", "increase", "louder", "raise"]),
         lambda cmd: skills.change_volume("up")),

        (lambda cmd: "volume" in cmd and any(k in cmd for k in ["down", "decrease", "lower", "quieter"]),
         lambda cmd: skills.change_volume("down")),

        (lambda cmd: "unmute" in cmd,
         lambda cmd: skills.change_volume("unmute")),

        (lambda cmd: "mute" in cmd,
         lambda cmd: skills.change_volume("mute")),

        (lambda cmd: "volume" in cmd and "max" in cmd,
         lambda cmd: skills.change_volume("max")),

        # ── LibreOffice / Office ──────────────────────────────────────────────
        (lambda cmd: "open" in cmd and any(k in cmd for k in ["calc", "spreadsheet"]),
         lambda cmd: skills.open_libreoffice("calc")),

        (lambda cmd: "open" in cmd and any(k in cmd for k in ["writer", "document"]),
         lambda cmd: skills.open_libreoffice("writer")),

        (lambda cmd: "open" in cmd and any(k in cmd for k in ["impress", "presentation", "slideshow"]),
         lambda cmd: skills.open_libreoffice("impress")),

        # ── Generic app opener (keep AFTER specific LibreOffice rules) ────────
        (lambda cmd: "open" in cmd,
         lambda cmd: skills.open_app(cmd.replace("open", "").strip())),

        # ── Screenshot ────────────────────────────────────────────────────────
        (lambda cmd: "screenshot" in cmd or "screen shot" in cmd,
         lambda cmd: skills.take_screenshot()),

        # ── Weather ───────────────────────────────────────────────────────────
        (lambda cmd: "weather" in cmd,
         lambda cmd: skills.get_weather(
             cmd.split("weather in")[-1].strip() if "weather in" in cmd
             else cmd.replace("weather", "").strip()
         )),

        # ── Time & Date ───────────────────────────────────────────────────────
        (lambda cmd: any(k in cmd for k in ["what time", "current time", "what's the time",
                                             "what date", "today's date", "what day"]),
         lambda cmd: skills.get_time_date(cmd)),

        # ── Alarm ─────────────────────────────────────────────────────────────
        (lambda cmd: "alarm" in cmd,
         lambda cmd: skills.set_alarm_from_cmd(cmd)),

        # ── Reminder ──────────────────────────────────────────────────────────
        (lambda cmd: "remind" in cmd,
         lambda cmd: skills.set_reminder_from_cmd(cmd)),

        # ── Internet ──────────────────────────────────────────────────────────
        (lambda cmd: "internet speed" in cmd or "speed test" in cmd,
         lambda cmd: skills.get_internet_speed()),

        (lambda cmd: "internet" in cmd and any(k in cmd for k in ["connection", "working", "available"]),
         lambda cmd: skills.check_internet()),

        # ── News ──────────────────────────────────────────────────────────────
        (lambda cmd: "news" in cmd,
         lambda cmd: skills.get_news()),

        # ── Spell ─────────────────────────────────────────────────────────────
        (lambda cmd: "spell" in cmd,
         lambda cmd: skills.spell_word(cmd.split()[-1])),

        # ── Knowledge ─────────────────────────────────────────────────────────
        (lambda cmd: any(k in cmd for k in ["tell me about", "what is", "who is", "what are"]),
         lambda cmd: skills.tell_about(
             re.strip_prefixes(cmd, ["tell me about", "what is", "who is", "what are"])
         )),

        # ── Memory ────────────────────────────────────────────────────────────
        (lambda cmd: "clear" in cmd and "memory" in cmd,
         lambda cmd: "Memory cleared."),   # brain.clear_memory() called in main
    ]


# ── Small helper (avoids importing re just for this) ─────────────────────────
class re:  # noqa — shadow stdlib re to avoid an import for this one helper
    @staticmethod
    def strip_prefixes(text: str, prefixes: list) -> str:
        """Remove the first matching prefix and return the remainder."""
        for p in prefixes:
            if p in text:
                return text.split(p, 1)[-1].strip()
        return text.strip()


# ── Main loop ────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print(" Initializing FRIDAY...")
    print("=" * 50)

    voice    = VoiceEngine()
    brain    = Brain(model="phi3:latest")
    listener = Listener()
    skills   = Skills()
    dispatch = build_dispatch(skills)

    voice.speak("System online. How can I help you?")

    while True:
        try:
            # ── 1. Wait for wake word or double clap ──────────────────────────
            woke = listener.listen_for_wake()
            if not woke:
                continue

            voice.speak("Yes?")
            # Brief pause so the TTS output doesn't bleed into the mic
            time.sleep(0.4)

            # ── 2. Listen for the command ─────────────────────────────────────
            command = listener.listen_for_command()
            if not command or len(command.strip()) < 3:
                voice.speak("I didn't catch that.")
                continue

            cmd = command.lower().strip()
            print(f"\n→ Command: {command}")

            # ── 3. Check for exit ─────────────────────────────────────────────
            if any(word in cmd for word in EXIT_WORDS):
                voice.speak("Goodbye. Shutting down.")
                break

            # ── 4. Special: clear memory ──────────────────────────────────────
            if "clear" in cmd and "memory" in cmd:
                brain.clear_memory()
                voice.speak("Memory cleared.")
                continue

            # ── 5. Try skill dispatch ─────────────────────────────────────────
            response = None
            for trigger, handler in dispatch:
                try:
                    if trigger(cmd):
                        response = handler(cmd)
                        break
                except Exception as e:
                    print(f"[Skill error] {e}")

            # ── 6. Fall back to AI brain ──────────────────────────────────────
            if response is None:
                print("[Brain] Thinking...")
                response = brain.think(command)

            if response:
                voice.speak(response)

        except KeyboardInterrupt:
            print("\nInterrupted.")
            voice.speak("Goodbye.")
            break
        except Exception as e:
            print(f"[Main] Unexpected error: {e}")
            voice.speak("Something went wrong. Please try again.")


if __name__ == "__main__":
    main()