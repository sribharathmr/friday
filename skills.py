import os
import time
import datetime
import threading
import webbrowser
import requests
import speedtest
import wikipedia
import pywhatkit
import feedparser
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class Skills:
    def __init__(self):
        pass

    def open_webpage(self, url_or_name):
        """Opens a web page"""
        if "youtube" in url_or_name.lower():
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube."
        elif "google" in url_or_name.lower():
            webbrowser.open("https://www.google.com")
            return "Opening Google."
        else:
            webbrowser.open(f"https://www.google.com/search?q={url_or_name}")
            return f"Searching for {url_or_name}."

    def play_music(self, song):
        """Play music in Youtube"""
        pywhatkit.playonyt(song)
        return f"Playing {song} on YouTube."

    def change_volume(self, action):
        """Increase/decrease the speakers master volume"""
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            current_vol = volume.GetMasterVolumeLevelScalar()
            
            if "up" in action or "increase" in action:
                new_vol = min(1.0, current_vol + 0.2)
                volume.SetMasterVolumeLevelScalar(new_vol, None)
                return "Volume increased."
            elif "down" in action or "decrease" in action:
                new_vol = max(0.0, current_vol - 0.2)
                volume.SetMasterVolumeLevelScalar(new_vol, None)
                return "Volume decreased."
            elif "max" in action:
                volume.SetMasterVolumeLevelScalar(1.0, None)
                return "Volume set to maximum."
            elif "mute" in action:
                volume.SetMute(1, None)
                return "Speakers muted."
            elif "unmute" in action:
                volume.SetMute(0, None)
                return "Speakers unmuted."
        except Exception as e:
            return f"Failed to adjust volume: {e}"
        return "I didn't understand the volume command."

    def open_libreoffice(self, app):
        """Opens libreoffice suite applications"""
        app = app.lower()
        commands = {
            "calc": "start soffice --calc",
            "writer": "start soffice --writer",
            "impress": "start soffice --impress"
        }
        for key, cmd in commands.items():
            if key in app:
                os.system(cmd)
                return f"Opening {key.capitalize()}."
        return "I don't know that application."

    def tell_about(self, topic):
        """Tells about something, by searching on the internet"""
        try:
            summary = wikipedia.summary(topic, sentences=2)
            return summary
        except wikipedia.exceptions.DisambiguationError:
            return f"There are too many results for {topic}. Please be more specific."
        except wikipedia.exceptions.PageError:
            return f"I couldn't find any information about {topic}."
        except Exception:
            return "I had trouble searching the internet."

    def get_weather(self, location):
        """Tells the weather for a place"""
        try:
            res = requests.get(f"https://wttr.in/{location}?format=%C+and+%t")
            if res.status_code == 200:
                return f"The weather in {location} is currently {res.text}."
            return "I couldn't fetch the weather right now."
        except:
            return "I couldn't connect to the weather service."

    def get_time_date(self, command):
        """Tells the current time and/or date"""
        now = datetime.datetime.now()
        if "time" in command:
            return f"The current time is {now.strftime('%I:%M %p')}."
        elif "date" in command:
            return f"Today is {now.strftime('%B %d, %Y')}."
        return f"It is {now.strftime('%I:%M %p')} on {now.strftime('%B %d, %Y')}."

    def set_alarm(self, seconds):
        """Set an alarm (simplified to take seconds for this implementation)"""
        def alarm_thread():
            time.sleep(seconds)
            # Make a beep noise using windows api
            import winsound
            winsound.Beep(1000, 2000)
            
        t = threading.Thread(target=alarm_thread)
        t.start()
        return f"Alarm set for {seconds} seconds from now."

    def get_internet_speed(self):
        """Tells the internet speed (ping, uplink and downling)"""
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            ping = st.results.ping
            download = st.download() / 1_000_000  # Mbps
            upload = st.upload() / 1_000_000      # Mbps
            return f"Your ping is {ping:.0f} milliseconds, download is {download:.1f} megabits per second, and upload is {upload:.1f} megabits per second."
        except Exception as e:
            return "Speed test failed. Please ensure you are connected to the internet."

    def check_internet(self):
        """Tells the internet availability"""
        try:
            requests.get("https://www.google.com", timeout=3)
            return "Internet connection is live."
        except requests.ConnectionError:
            return "No internet connection detected."

    def get_news(self):
        """Tells the daily news"""
        try:
            url = "http://feeds.bbci.co.uk/news/rss.xml"
            feed = feedparser.parse(url)
            headlines = []
            for entry in feed.entries[:3]:
                headlines.append(entry.title)
            return "Here are the top headlines: " + ". ".join(headlines)
        except:
            return "I couldn't fetch the news right now."

    def spell_word(self, word):
        """Spells a word"""
        spelled = "-".join(list(word.upper()))
        return f"{word} is spelled: {spelled}."

    def open_app(self, app_name):
        """Opens any application on the system"""
        import subprocess
        try:
            subprocess.Popen(app_name, shell=True)
            return f"Opening {app_name}."
        except Exception as e:
            return f"I couldn't find {app_name} on your system."

    def take_screenshot(self):
        """Takes a screenshot and saves it as a file"""
        import pyautogui
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        try:
            pyautogui.screenshot(filename)
            return f"Screenshot saved as {filename}."
        except Exception as e:
            return f"Failed to take screenshot: {e}"

    def calculate(self, expression):
        """Evaluates a mathematical expression safely"""
        try:
            # Extract math from text
            expression = expression.lower().replace("times", "*").replace("plus", "+") \
                                   .replace("minus", "-").replace("divided by", "/")
            import re
            clean_expr = re.sub(r'[^0-9+\-*/().\s]', '', expression)
            if not clean_expr.strip():
                return "I couldn't find a valid mathematical expression to calculate."
            result = eval(clean_expr)
            return f"The answer is {result}."
        except Exception as e:
            return "I couldn't calculate that."
