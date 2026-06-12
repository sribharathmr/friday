import ollama
import json
import os

class Brain:
    def __init__(self, model="llama3.2:3b"):
        self.model = model
        self.memory_file = "memory.json"
        
        self.system_prompt = {
            "role": "system",
            "content": (
                "You are FRIDAY, a sharp, witty AI assistant inspired by Iron Man. "
                "You speak in SHORT sentences (1-2 max) because your output is read aloud. "
                "Never use markdown, bullet points, or lists. "
                "Be confident, slightly sarcastic, and always helpful. "
                "Address the user as 'Boss' occasionally."
            )
        }
        self.messages = self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    messages = json.load(f)
                    if messages and messages[0]["role"] == "system":
                        messages[0] = self.system_prompt
                    else:
                        messages = [self.system_prompt] + [m for m in messages if m["role"] != "system"]
                    return messages
            except:
                pass
        return [self.system_prompt]

    def _save_memory(self):
        with open(self.memory_file, 'w') as f:
            json.dump(self.messages, f)

    def _trim_memory(self, max_pairs=20):
        # Keep system prompt + last N user/assistant pairs
        non_system = [m for m in self.messages if m["role"] != "system"]
        trimmed = non_system[-(max_pairs * 2):]
        self.messages = [self.system_prompt] + trimmed

    def think(self, prompt):
        self.messages.append({"role": "user", "content": prompt})
        try:
            response = ollama.chat(model=self.model, messages=self.messages)
            reply = response['message']['content']
            self.messages.append({"role": "assistant", "content": reply})
            self._trim_memory()
            self._save_memory()
            return reply
        except Exception as e:
            print(f"Brain Error: {e}")
            return "I encountered an error accessing my core systems."

if __name__ == "__main__":
    brain = Brain()
    print("Jarvis:", brain.think("Who are you?"))
