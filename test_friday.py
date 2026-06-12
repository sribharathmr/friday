import unittest
import os
import shutil
import json
from unittest.mock import patch, MagicMock

# Import our updated files
from memory import Memory
from brain import Brain
from skills import Skills
from main import parse_command

class TestFriday(unittest.TestCase):
    def setUp(self):
        # Use temporary files for testing memory
        self.temp_facts = "test_facts.json"
        self.temp_memory = "test_memory.json"
        if os.path.exists(self.temp_facts):
            os.remove(self.temp_facts)
        if os.path.exists(self.temp_memory):
            os.remove(self.temp_memory)
            
    def tearDown(self):
        if os.path.exists(self.temp_facts):
            os.remove(self.temp_facts)
        if os.path.exists(self.temp_memory):
            os.remove(self.temp_memory)
            
    def test_memory_facts(self):
        mem = Memory(path=self.temp_facts)
        res = mem.remember("my name", "Bharath")
        self.assertIn("remember that my name is Bharath", res)
        self.assertEqual(mem.recall("my name"), "Bharath")
        self.assertEqual(mem.recall("MY name"), "Bharath")
        self.assertEqual(mem.recall("nonexistent"), None)
        
    @patch('ollama.chat')
    def test_brain_memory_trimming(self, mock_chat):
        # Set up brain with mock ollama
        mock_chat.return_value = {
            'message': {
                'content': 'Test response'
            }
        }
        
        brain = Brain(model="llama3.2:3b")
        brain.memory_file = self.temp_memory
        
        # Verify default system prompt
        self.assertEqual(brain.messages[0]["role"], "system")
        self.assertIn("FRIDAY", brain.messages[0]["content"])
        
        # Let's think 25 times to trigger trimming
        for i in range(25):
            brain.think(f"User message {i}")
            
        # After thinking 25 times, there are 25 user and 25 assistant messages (50 total messages plus system prompt).
        # Memory trimming restricts messages to: system prompt + last max_pairs * 2 (which is 20 pairs = 40 messages).
        # Total messages in memory should be 41.
        self.assertEqual(len(brain.messages), 41)
        self.assertEqual(brain.messages[0]["role"], "system")
        # Ensure the last message matches the final interaction
        self.assertEqual(brain.messages[-1]["content"], "Test response")
        self.assertEqual(brain.messages[-2]["content"], "User message 24")

    def test_skills_calculate(self):
        skills = Skills()
        self.assertEqual(skills.calculate("12 times 8"), "The answer is 96.")
        self.assertEqual(skills.calculate("100 divided by 4"), "The answer is 25.0.")
        self.assertEqual(skills.calculate("10 plus 20 minus 5"), "The answer is 25.")
        self.assertEqual(skills.calculate("invalid expression"), "I couldn't find a valid mathematical expression to calculate.")

    def test_skills_check_internet(self):
        skills = Skills()
        res = skills.check_internet()
        self.assertTrue("Internet connection" in res or "offline" in res or "No internet" in res)

    def test_routing(self):
        skills = Skills()
        mem = Memory(path=self.temp_facts)
        
        # Test remember command
        res = parse_command("remember my favorite color is green", skills, mem)
        self.assertIn("remember that my favorite color is green", res)
        self.assertEqual(mem.recall("my favorite color"), "green")
        
        # Test what is from memory command
        res = parse_command("what is my favorite color", skills, mem)
        self.assertEqual(res, "my favorite color is green.")
        
        # Test what is math command
        res = parse_command("what is 3 times 5", skills, mem)
        self.assertEqual(res, "The answer is 15.")
        
        # Test calculate command
        res = parse_command("calculate 10 plus 15", skills, mem)
        self.assertEqual(res, "The answer is 25.")
        
        # Test volume down
        res = parse_command("please turn the volume down", skills, mem)
        # Note: adjust speaker volume might fail on some headless systems or succeed. It returns a string.
        self.assertTrue(isinstance(res, str))

if __name__ == '__main__':
    unittest.main()
