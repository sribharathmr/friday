import json
import os

class Memory:
    def __init__(self, path="facts.json"):
        self.path = path
        self.facts = self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Memory load error: {e}")
        return {}

    def remember(self, key, value):
        self.facts[key.lower().strip()] = value.strip()
        try:
            with open(self.path, "w") as f:
                json.dump(self.facts, f, indent=4)
            return f"Got it, I'll remember that {key} is {value}."
        except Exception as e:
            return f"I had trouble saving that. Error: {e}"

    def recall(self, key):
        return self.facts.get(key.lower().strip(), None)
