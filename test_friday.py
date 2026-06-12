import unittest
import os
import re
from unittest.mock import patch, MagicMock

# Import updated files
from brain import Brain
from skills import Skills
from main import build_dispatch

class TestFriday(unittest.TestCase):
    def setUp(self):
        self.temp_memory = "test_memory.json"
        if os.path.exists(self.temp_memory):
            os.remove(self.temp_memory)
            
    def tearDown(self):
        if os.path.exists(self.temp_memory):
            os.remove(self.temp_memory)
            
    @patch('ollama.chat')
    def test_brain_memory_trimming(self, mock_chat):
        mock_chat.return_value = {
            'message': {
                'content': 'Test response'
            }
        }
        
        brain = Brain(model="phi3:latest")
        brain.memory_file = self.temp_memory
        
        # Test default load is empty
        self.assertEqual(len(brain.messages), 0)
        
        # Call think 25 times
        for i in range(25):
            brain.think(f"User message {i}")
            
        # The history length should be capped at 21 (due to trim before append)
        self.assertEqual(len(brain.messages), 21)
        # Verify it saved the last assistant response
        self.assertEqual(brain.messages[-1]["content"], "Test response")
        # Verify it trimmed oldest (first element is now the assistant response of the oldest pair)
        self.assertEqual(brain.messages[0]["content"], "Test response")
        self.assertEqual(brain.messages[1]["content"], "User message 15")

    def test_brain_clear_memory(self):
        brain = Brain()
        brain.memory_file = self.temp_memory
        brain.messages = [{"role": "user", "content": "hello"}]
        with open(self.temp_memory, 'w') as f:
            f.write("[]")
        self.assertTrue(os.path.exists(self.temp_memory))
        
        brain.clear_memory()
        self.assertEqual(len(brain.messages), 0)
        self.assertFalse(os.path.exists(self.temp_memory))

    def test_dispatch_routing(self):
        skills = MagicMock()
        dispatch = build_dispatch(skills)
        
        # Helper to find which trigger matches
        def find_handler(cmd):
            for trigger, handler in dispatch:
                if trigger(cmd):
                    return handler
            return None

        # Test youtube open
        handler = find_handler("open youtube")
        self.assertIsNotNone(handler)
        handler("open youtube")
        skills.open_webpage.assert_called_with("youtube")
        
        # Test music play
        handler = find_handler("play a classic song on youtube")
        self.assertIsNotNone(handler)
        handler("play a classic song on youtube")
        skills.play_music.assert_called_with("a classic")

        # Test alarm
        handler = find_handler("set an alarm for 5 minutes")
        self.assertIsNotNone(handler)
        handler("set an alarm for 5 minutes")
        skills.set_alarm_from_cmd.assert_called_with("set an alarm for 5 minutes")

        # Test reminder
        handler = find_handler("remind me to stretch in 20 minutes")
        self.assertIsNotNone(handler)
        handler("remind me to stretch in 20 minutes")
        skills.set_reminder_from_cmd.assert_called_with("remind me to stretch in 20 minutes")

    def test_skills_spell_word(self):
        skills = Skills()
        res = skills.spell_word("hello")
        self.assertEqual(res, "hello is spelled: H - E - L - L - O.")
        
    def test_skills_get_time_date(self):
        skills = Skills()
        res = skills.get_time_date("what time is it")
        self.assertIn("The current time is", res)

if __name__ == '__main__':
    unittest.main()
