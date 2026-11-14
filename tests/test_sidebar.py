import os
import sys
import unittest
import tempfile
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config_manager import ConfigManager, DEFAULT_CONFIG
from ai_service import AIService
from hotkey_manager import HotkeyManager


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "test_config.json")
        self.cm = ConfigManager(self.config_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_config_generated(self):
        self.assertTrue(os.path.exists(self.config_path))
        self.assertEqual(self.cm.get_active_provider(), "gemini")
        self.assertEqual(self.cm.get_hotkey(), "alt+c")

    def test_update_provider_key(self):
        self.cm.set_provider_key("gemini", "test_gemini_key_123")
        prov_cfg = self.cm.get_provider_config("gemini")
        self.assertEqual(prov_cfg.get("api_key"), "test_gemini_key_123")

        # Reload from disk to verify persistence
        new_cm = ConfigManager(self.config_path)
        self.assertEqual(new_cm.get_provider_config("gemini").get("api_key"), "test_gemini_key_123")

    def test_update_active_provider(self):
        self.cm.set_active_provider("deepseek")
        self.assertEqual(self.cm.get_active_provider(), "deepseek")

        self.cm.set_active_provider("openai")
        self.assertEqual(self.cm.get_active_provider(), "openai")

        self.cm.set_active_provider("groq")
        self.assertEqual(self.cm.get_active_provider(), "groq")

    def test_update_hotkey(self):
        self.cm.set_hotkey("ctrl+shift+a")
        self.assertEqual(self.cm.get_hotkey(), "ctrl+shift+a")

    def test_dock_side_and_width(self):
        self.assertEqual(self.cm.get_dock_side(), "right")
        self.cm.set_dock_side("left")
        self.assertEqual(self.cm.get_dock_side(), "left")

        self.cm.set_sidebar_width(520)
        self.assertEqual(self.cm.get_sidebar_width(), 520)


class TestAIService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "test_config.json")
        self.cm = ConfigManager(self.config_path)
        self.service = AIService(self.cm)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_api_key_error(self):
        # Empty API key should immediately trigger on_error with helpful message
        err_msg = []
        self.service.stream_chat(
            messages=[{"role": "user", "content": "Hello"}],
            on_chunk=lambda x: None,
            on_complete=lambda x: None,
            on_error=lambda err: err_msg.append(err),
            override_provider="gemini"
        )
        self.assertEqual(len(err_msg), 1)
        self.assertIn("Missing API Key for Gemini", err_msg[0])

        groq_err = []
        self.service.stream_chat(
            messages=[{"role": "user", "content": "Hello"}],
            on_chunk=lambda x: None,
            on_complete=lambda x: None,
            on_error=lambda err: groq_err.append(err),
            override_provider="groq"
        )
        self.assertEqual(len(groq_err), 1)
        self.assertIn("Missing API Key for Groq", groq_err[0])


class TestHotkeyManager(unittest.TestCase):
    def test_init_and_update(self):
        hm = HotkeyManager("windows+c", lambda: None)
        self.assertEqual(hm.hotkey_str, "windows+c")
        hm.update_hotkey("alt+space")
        self.assertEqual(hm.hotkey_str, "alt+space")
        hm.stop()


if __name__ == "__main__":
    unittest.main()
