import ollama
import json
import os

class Brain:
    def __init__(self, model="phi3:latest"):
        self.model = model
        self.memory_file = "memory.json"
        
        self.system_prompt = {
            "role": "system",
            "content": "You are Friday, a helpful and witty AI assistant. Keep all answers extremely brief, ideally 1 short sentence. Never output long paragraphs."
        }
        self.messages = self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return [self.system_prompt]

    def _save_memory(self):
        with open(self.memory_file, 'w') as f:
            json.dump(self.messages, f)

    def think(self, prompt):
        self.messages.append({"role": "user", "content": prompt})
        try:
            response = ollama.chat(model=self.model, messages=self.messages)
            reply = response['message']['content']
            self.messages.append({"role": "assistant", "content": reply})
            
            # Save memory after each interaction
            self._save_memory()
            
            return reply
        except Exception as e:
            print(f"Brain Error: {e}")
            return "I encountered an error accessing my core systems."

if __name__ == "__main__":
    brain = Brain()
    print("Jarvis:", brain.think("Who are you?"))
