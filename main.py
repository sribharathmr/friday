from voice import VoiceEngine
from brain import Brain
from listener import Listener
from skills import Skills
import re

def parse_command(command, skills):
    """Routes the voice command to a skill, or returns None if it should go to the AI brain"""
    cmd = command.lower()
    
    if "open youtube" in cmd:
        return skills.open_webpage("youtube")
    elif "play" in cmd and "youtube" in cmd:
        # e.g., "play mozart on youtube"
        query = cmd.replace("play", "").replace("on youtube", "").strip()
        return skills.play_music(query)
    elif "volume" in cmd:
        return skills.change_volume(cmd)
    elif "open calc" in cmd or "open writer" in cmd or "open impress" in cmd:
        return skills.open_libreoffice(cmd)
    elif "tell me about" in cmd:
        query = cmd.split("tell me about")[-1].strip()
        return skills.tell_about(query)
    elif "weather in" in cmd:
        city = cmd.split("weather in")[-1].strip()
        return skills.get_weather(city)
    elif "time" in cmd or "date" in cmd:
        # If they just ask generally about time or date, not part of a bigger sentence
        if len(cmd.split()) < 5:
            return skills.get_time_date(cmd)
    elif "alarm" in cmd:
        # Try to extract a number for seconds
        match = re.search(r'\d+', cmd)
        if match:
            seconds = int(match.group())
            return skills.set_alarm(seconds)
        else:
            return "Please specify how many seconds to set the alarm for."
    elif "internet speed" in cmd:
        return skills.get_internet_speed()
    elif "internet connection" in cmd or "internet availability" in cmd:
        return skills.check_internet()
    elif "news" in cmd:
        return skills.get_news()
    elif "spell" in cmd:
        # e.g., "spell the word animal"
        words = cmd.split()
        word_to_spell = words[-1]
        return skills.spell_word(word_to_spell)
        
    return None

def main():
    print("Initializing JARVIS/FRIDAY...")
    voice = VoiceEngine()
    brain = Brain(model="phi3:latest")
    listener = Listener()
    skills = Skills()

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
                    skill_response = parse_command(command, skills)
                    
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
