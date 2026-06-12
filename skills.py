import os
import re
import time
import datetime
import threading
import webbrowser
import subprocess

import requests
import wikipedia
import pywhatkit
import feedparser
import pyautogui

try:
    import speedtest as _speedtest_lib
    SPEEDTEST_AVAILABLE = True
except ImportError:
    SPEEDTEST_AVAILABLE = False

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False


# ── App name → executable(s) mapping ──────────────────────────────────────────
# Each entry is a list so we can try them in order until one works.
APP_MAP = {
    "notepad":        ["notepad.exe"],
    "calculator":     ["calc.exe"],
    "paint":          ["mspaint.exe"],
    "chrome":         ["chrome.exe",
                       r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                       r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    "firefox":        ["firefox.exe"],
    "edge":           ["msedge.exe"],
    "file explorer":  ["explorer.exe"],
    "explorer":       ["explorer.exe"],
    "task manager":   ["taskmgr.exe"],
    "control panel":  ["control.exe"],
    "settings":       ["ms-settings:"],          # URI — shell=True handles it
    "snipping tool":  ["SnippingTool.exe", "SnipSketch.exe"],
    "vlc":            ["vlc.exe",
                       r"C:\Program Files\VideoLAN\VLC\vlc.exe"],
    "spotify":        ["Spotify.exe"],
    "discord":        ["Discord.exe"],
    "vs code":        ["code.exe"],
    "vscode":         ["code.exe"],
    "code":           ["code.exe"],
    "terminal":       ["wt.exe", "cmd.exe"],
    "command prompt": ["cmd.exe"],
    "cmd":            ["cmd.exe"],
    "word":           ["WINWORD.EXE"],
    "excel":          ["EXCEL.EXE"],
    "powerpoint":     ["POWERPNT.EXE"],
}


class Skills:

    # ── Web & Media ────────────────────────────────────────────────────────────

    def open_webpage(self, url_or_name: str) -> str:
        known = {
            "youtube": "https://www.youtube.com",
            "google":  "https://www.google.com",
            "github":  "https://www.github.com",
            "reddit":  "https://www.reddit.com",
            "twitter": "https://www.twitter.com",
            "x":       "https://www.x.com",
        }
        key = url_or_name.lower().strip()
        url = known.get(key, f"https://www.{key}.com")
        webbrowser.open(url)
        return f"Opening {key.capitalize()}."

    def search_web(self, query: str) -> str:
        if not query:
            webbrowser.open("https://www.google.com")
            return "Opening Google."
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        return f"Searching for {query}."

    def play_music(self, song: str) -> str:
        if not song:
            return "What would you like me to play?"
        try:
            pywhatkit.playonyt(song)
            return f"Playing {song} on YouTube."
        except Exception:
            # Fallback: open YouTube search directly
            webbrowser.open(f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}")
            return f"Opening YouTube search for {song}."

    # ── Volume ─────────────────────────────────────────────────────────────────

    def change_volume(self, action: str) -> str:
        if not PYCAW_AVAILABLE:
            return "Volume control is not available on this system."
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            current = volume.GetMasterVolumeLevelScalar()

            if "up" in action or "increase" in action:
                volume.SetMasterVolumeLevelScalar(min(1.0, current + 0.2), None)
                return "Volume increased."
            elif "down" in action or "decrease" in action:
                volume.SetMasterVolumeLevelScalar(max(0.0, current - 0.2), None)
                return "Volume decreased."
            elif "max" in action:
                volume.SetMasterVolumeLevelScalar(1.0, None)
                return "Volume at maximum."
            elif "unmute" in action:
                volume.SetMute(0, None)
                return "Speakers unmuted."
            elif "mute" in action:
                volume.SetMute(1, None)
                return "Speakers muted."
        except Exception as e:
            return f"Could not adjust volume: {e}"
        return "Volume command not understood."

    # ── Applications ───────────────────────────────────────────────────────────

    def open_app(self, app_name: str) -> str:
        """
        Open a named application.
        Checks APP_MAP first, then tries the raw name, then falls back to
        a Windows Run command.
        """
        name = app_name.lower().strip()

        for key, executables in APP_MAP.items():
            if key in name:
                for exe in executables:
                    try:
                        subprocess.Popen(exe, shell=True)
                        return f"Opening {key}."
                    except Exception:
                        continue

        # Try it as a raw command (works if it's in PATH)
        try:
            subprocess.Popen(app_name, shell=True)
            return f"Trying to open {app_name}."
        except Exception:
            pass

        return f"I couldn't find {app_name} on your system."

    def open_libreoffice(self, app: str) -> str:
        """
        Open a LibreOffice app, falling back to Microsoft Office.
        BUG FIX: the original code called os.system() for BOTH apps simultaneously.
        We now try LibreOffice first, and only fall back if it isn't found.
        """
        app = app.lower().strip()
        options = {
            "calc":    ("--calc",    ["EXCEL.EXE"]),
            "writer":  ("--writer",  ["WINWORD.EXE"]),
            "impress": ("--impress", ["POWERPNT.EXE"]),
        }
        if app not in options:
            return "I don't know that LibreOffice application."

        flag, ms_fallbacks = options[app]

        # Try LibreOffice
        for cmd in ["soffice", "soffice.exe"]:
            try:
                subprocess.Popen([cmd, flag])
                return f"Opening LibreOffice {app.capitalize()}."
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"[Skills] LibreOffice error: {e}")

        # Fall back to Microsoft Office
        for ms_exe in ms_fallbacks:
            try:
                subprocess.Popen(ms_exe, shell=True)
                return f"Opening Microsoft {app.capitalize()}."
            except Exception:
                continue

        return f"Neither LibreOffice nor Microsoft Office found for {app}."

    # ── Screenshot ─────────────────────────────────────────────────────────────

    def take_screenshot(self) -> str:
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            os.makedirs(desktop, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(desktop, f"screenshot_{ts}.png")
            pyautogui.screenshot().save(path)
            return f"Screenshot saved to your Desktop as screenshot_{ts}.png"
        except Exception as e:
            return f"Screenshot failed: {e}"

    # ── Knowledge ──────────────────────────────────────────────────────────────

    def tell_about(self, topic: str) -> str:
        if not topic:
            return "What would you like to know about?"
        try:
            summary = wikipedia.summary(topic, sentences=2, auto_suggest=True)
            return summary
        except wikipedia.exceptions.DisambiguationError as e:
            options = e.options[:3]
            return f"Multiple results for {topic}. Did you mean: {', '.join(options)}?"
        except wikipedia.exceptions.PageError:
            return f"I couldn't find information about {topic}. Try rephrasing."
        except Exception:
            return "I had trouble searching for that."

    # ── Weather ────────────────────────────────────────────────────────────────

    def get_weather(self, location: str) -> str:
        location = (location or "Chennai").strip()
        try:
            res = requests.get(
                f"https://wttr.in/{location.replace(' ', '+')}?format=%C,+%t",
                timeout=5
            )
            if res.status_code == 200:
                return f"The weather in {location} is {res.text.strip()}."
            return "I couldn't retrieve the weather right now."
        except Exception:
            return "I couldn't connect to the weather service."

    # ── Time & Date ────────────────────────────────────────────────────────────

    def get_time_date(self, command: str) -> str:
        now = datetime.datetime.now()
        if "time" in command and "date" not in command:
            return f"The current time is {now.strftime('%I:%M %p')}."
        elif "date" in command and "time" not in command:
            return f"Today is {now.strftime('%A, %B %d, %Y')}."
        return f"It is {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}."

    # ── Alarms ─────────────────────────────────────────────────────────────────

    def set_alarm_from_cmd(self, cmd: str) -> str:
        """
        Parse natural phrases like:
          'set alarm for 5 minutes'
          'alarm in 30 seconds'
          'set a 2 minute alarm'
        BUG FIX: original only handled raw seconds; this handles minutes too.
        """
        m = re.search(r'(\d+)\s*(minute|min|second|sec)', cmd, re.IGNORECASE)
        if not m:
            return "Please say how long, for example: set alarm for 5 minutes."
        amount = int(m.group(1))
        unit = m.group(2).lower()
        if unit.startswith('m'):
            seconds = amount * 60
            label = f"{amount} minute{'s' if amount != 1 else ''}"
        else:
            seconds = amount
            label = f"{amount} second{'s' if amount != 1 else ''}"
        return self._set_alarm(seconds, label)

    def _set_alarm(self, seconds: int, label: str) -> str:
        def _ring():
            time.sleep(seconds)
            try:
                import winsound
                for _ in range(3):
                    winsound.Beep(1000, 600)
                    time.sleep(0.3)
            except Exception:
                pass
            print(f"\n🔔  ALARM: {label} is up!")
        threading.Thread(target=_ring, daemon=True).start()
        return f"Alarm set for {label} from now."

    # ── Reminders ──────────────────────────────────────────────────────────────

    def set_reminder_from_cmd(self, cmd: str) -> str:
        """Parse: 'remind me to call John in 10 minutes'"""
        m = re.search(
            r'remind\s+me\s+(?:to\s+)?(.+?)\s+in\s+(\d+)\s*(minute|min|second|sec|hour)',
            cmd, re.IGNORECASE
        )
        if not m:
            return "Please say: remind me to [task] in [N] minutes."
        task = m.group(1).strip()
        amount = int(m.group(2))
        unit = m.group(3).lower()
        multipliers = {"minute": 60, "min": 60, "second": 1, "sec": 1, "hour": 3600}
        seconds = amount * multipliers.get(unit, 60)
        return self._set_reminder(task, seconds, amount, unit)

    def _set_reminder(self, task: str, seconds: int, amount: int, unit: str) -> str:
        def _remind():
            time.sleep(seconds)
            print(f"\n🔔  REMINDER: {task}")
        threading.Thread(target=_remind, daemon=True).start()
        return f"I'll remind you to {task} in {amount} {unit}{'s' if amount != 1 else ''}."

    # ── Internet ───────────────────────────────────────────────────────────────

    def check_internet(self) -> str:
        """
        BUG FIX: original used https://8.8.8.8 which has no SSL cert.
        Using http:// instead, or a proper domain.
        """
        try:
            requests.get("http://8.8.8.8", timeout=3)
            return "The internet connection is working."
        except requests.ConnectionError:
            return "The internet connection appears to be offline."
        except Exception:
            return "I couldn't check the internet connection."

    def get_internet_speed(self) -> str:
        if not SPEEDTEST_AVAILABLE:
            return "Speedtest module is not installed."
        print("[Skills] Running speed test, this takes about 30 seconds...")
        try:
            st = _speedtest_lib.Speedtest(secure=True)
            st.get_best_server()
            dl = st.download() / 1_000_000
            ul = st.upload() / 1_000_000
            ping = st.results.ping
            return (f"Ping {ping:.0f} milliseconds, "
                    f"download {dl:.1f} megabits per second, "
                    f"upload {ul:.1f} megabits per second.")
        except Exception:
            return "Speed test failed. Please check your internet connection."

    # ── News ───────────────────────────────────────────────────────────────────

    def get_news(self) -> str:
        try:
            feed = feedparser.parse("http://feeds.bbci.co.uk/news/rss.xml")
            if not feed.entries:
                return "I couldn't fetch the news right now."
            headlines = [e.title for e in feed.entries[:3]]
            return "Here are the top three headlines. " + ". Next, ".join(headlines) + "."
        except Exception:
            return "I couldn't fetch the news right now."

    # ── Utilities ──────────────────────────────────────────────────────────────

    def spell_word(self, word: str) -> str:
        if not word:
            return "What word would you like me to spell?"
        spelled = " - ".join(list(word.upper()))
        return f"{word} is spelled: {spelled}."