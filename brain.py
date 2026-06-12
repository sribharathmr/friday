import ollama
import json
import os
import re
import datetime

# Keep the last N messages (user + assistant pairs).
# 20 messages = 10 full exchanges — plenty of context without overflowing phi3.
MAX_HISTORY = 20


class Brain:
    def __init__(self, model: str = "phi3:latest"):
        self.model = model
        self.memory_file = "memory.json"
        # Load only non-system messages — system prompt is rebuilt fresh each call
        self.messages = self._load_memory()

    # ── System prompt ──────────────────────────────────────────────────────────

    def _system_prompt(self) -> dict:
        """Rebuilt every call so Friday always knows the current date and time."""
        now = datetime.datetime.now().strftime("%A, %B %d %Y, %I:%M %p")
        return {
            "role": "system",
            "content": (
                f"You are Friday, a helpful and witty AI voice assistant. "
                f"Today is {now}. "
                "Keep every answer extremely brief — one short sentence, two at most. "
                "Never use bullet points, markdown, asterisks, or long paragraphs. "
                "Speak naturally as if talking to a person."
            )
        }

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load_memory(self) -> list:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    msgs = json.load(f)
                # Drop any saved system prompts — we always prepend a fresh one
                return [m for m in msgs if m.get("role") != "system"]
            except Exception:
                pass
        return []

    def _save_memory(self):
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.messages, f, indent=2)
        except Exception as e:
            print(f"[Brain] Memory save error: {e}")

    def _trim_memory(self):
        """Discard oldest messages beyond MAX_HISTORY to prevent context overflow."""
        if len(self.messages) > MAX_HISTORY:
            self.messages = self.messages[-MAX_HISTORY:]

    # ── Inference ──────────────────────────────────────────────────────────────

    def think(self, prompt: str) -> str:
        self.messages.append({"role": "user", "content": prompt})
        self._trim_memory()

        # Always prepend a fresh system prompt so date/time is current
        full_messages = [self._system_prompt()] + self.messages

        try:
            response = ollama.chat(model=self.model, messages=full_messages)
            reply = response['message']['content'].strip()

            # Strip markdown that sounds terrible when read aloud by TTS
            reply = re.sub(r'[*_`#\[\]()\-]+', ' ', reply)
            reply = re.sub(r'\s+', ' ', reply).strip()

            self.messages.append({"role": "assistant", "content": reply})
            self._save_memory()
            return reply

        except Exception as e:
            print(f"[Brain] Error: {e}")
            # Don't commit the failed user message
            self.messages.pop()
            return "I encountered an error accessing my core systems."

    def clear_memory(self):
        """Wipe conversation history — useful for a fresh session."""
        self.messages = []
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)
        return "Memory cleared."


if __name__ == "__main__":
    brain = Brain()
    print("Friday:", brain.think("Who are you?"))