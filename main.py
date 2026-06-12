from voice import VoiceEngine
from brain import Brain
from listener import Listener
from skills import Skills
from memory import Memory
import re

def parse_command(command, skills, memory):
    """Routes the voice command to a skill or memory store, or returns None if it should go to the AI brain"""
    cmd = command.lower()
    
    # 1. Long-term factual memory routing
    if "remember" in cmd:
        # Extract key and value from e.g. "remember my favorite color is blue" or "remember that my name is Bharath"
        clean_cmd = cmd.replace("remember that", "").replace("remember", "").strip()
        parts = clean_cmd.split(" is ")
        if len(parts) == 2:
            return memory.remember(parts[0].strip(), parts[1].strip())
        return "I didn't catch that. What should I remember?"

    if "what is" in cmd:
        query = cmd.replace("what is", "").strip()
        # Check memory first
        fact = memory.recall(query)
        if fact:
            return f"{query} is {fact}."
        
        # Check if math calculation
        math_keywords = ["plus", "minus", "times", "divided by", "+", "-", "*", "/"]
        if any(kw in query for kw in math_keywords) and any(c.isdigit() for c in query):
            return skills.calculate(query)
            
    # 2. General mathematical calculation routing
    if "calculate" in cmd or "compute" in cmd:
        expr = cmd.replace("calculate", "").replace("compute", "").strip()
        return skills.calculate(expr)

    # 3. Keyword-based skill routing
    SKILL_ROUTES = [
        ("youtube", lambda c, s: s.open_webpage("youtube")),
        ("google", lambda c, s: s.open_webpage("google")),
        ("weather in", lambda c, s: s.get_weather(c.split("weather in")[-1].strip())),
        ("news", lambda c, s: s.get_news()),
        ("internet speed", lambda c, s: s.get_internet_speed()),
        ("screenshot", lambda c, s: s.take_screenshot()),
        ("volume up", lambda c, s: s.change_volume("up")),
        ("volume down", lambda c, s: s.change_volume("down")),
        ("mute", lambda c, s: s.change_volume("mute")),
        ("unmute", lambda c, s: s.change_volume("unmute")),
        ("spell", lambda c, s: s.spell_word(c.split()[-1])),
        ("tell me about", lambda c, s: s.tell_about(c.split("tell me about")[-1].strip())),
        ("play", lambda c, s: s.play_music(c.replace("play", "").replace("on youtube", "").strip())),
        ("alarm", lambda c, s: s.set_alarm(int(re.search(r'\d+', c).group())) if re.search(r'\d+', c) else "Please specify how many seconds to set the alarm for."),
        ("time", lambda c, s: s.get_time_date(c) if len(c.split()) < 5 else None),
        ("date", lambda c, s: s.get_time_date(c) if len(c.split()) < 5 else None),
        ("internet connection", lambda c, s: s.check_internet()),
        ("internet availability", lambda c, s: s.check_internet()),
        ("open calc", lambda c, s: s.open_libreoffice(c)),
        ("open writer", lambda c, s: s.open_libreoffice(c)),
        ("open impress", lambda c, s: s.open_libreoffice(c)),
        ("open ", lambda c, s: s.open_app(c.replace("open", "").strip())),
    ]

    for keyword, action in SKILL_ROUTES:
        if keyword in cmd:
            res = action(cmd, skills)
            if res:
                return res
                
    return None

def main():
    print("Initializing JARVIS/FRIDAY...")
    voice = VoiceEngine()
    brain = Brain(model="llama3.2:3b")
    listener = Listener()
    skills = Skills()
    memory = Memory()

    voice.speak("System is online and ready.")

    while True:
        try:
            # 1. Wait for Wake Word or Clap
            woke_up = listener.listen_for_wake()
            
            if woke_up:
                voice.speak("Yes?")
                
                # 2. Listen for command
                command = listener.listen_for_command()
                
                if command and len(command.strip()) > 2:
                    print(f"Routing Command: {command}")
                    
                    # 3. Check if it's a built-in skill
                    skill_response = parse_command(command, skills, memory)
                    
                    if skill_response:
                        voice.speak(skill_response)
                    else:
                        # 4. If no skill matched, Process with Brain
                        response = brain.think(command)
                        voice.speak(response)
                    
        except KeyboardInterrupt:
            print("\nShutting down.")
            voice.speak("Goodbye.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            voice.speak("I encountered an error.")

if __name__ == "__main__":
    main()
