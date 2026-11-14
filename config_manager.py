import os
import json
import copy

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
EXAMPLE_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.example.json")

DEFAULT_CONFIG = {
    "active_provider": "gemini",
    "hotkey": "windows+c",
    "sidebar_width": 430,
    "always_on_top": True,
    "theme": "dark",
    "font_size": 13,
    "providers": {
        "gemini": {
            "api_key": "",
            "model": "gemini-2.5-flash",
            "available_models": [
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-2.0-flash",
                "gemini-1.5-flash"
            ]
        },
        "deepseek": {
            "api_key": "",
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com",
            "available_models": [
                "deepseek-chat",
                "deepseek-reasoner"
            ]
        },
        "openai": {
            "api_key": "",
            "model": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
            "available_models": [
                "gpt-4o-mini",
                "gpt-4o",
                "o3-mini"
            ]
        }
    },
    "system_prompt": "You are a concise, helpful, and intelligent desktop AI sidebar assistant. Format answers cleanly using markdown."
}


class ConfigManager:
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path
        self.config = self.load()

    def load(self):
        if not os.path.exists(self.config_path):
            config = copy.deepcopy(DEFAULT_CONFIG)
            self.save(config)
            return config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Merge missing default keys
                merged = copy.deepcopy(DEFAULT_CONFIG)
                self._deep_update(merged, loaded)
                return merged
        except Exception as e:
            print(f"Error loading config: {e}. Falling back to default.")
            return copy.deepcopy(DEFAULT_CONFIG)

    def _deep_update(self, base, update):
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_update(base[k], v)
            else:
                base[k] = v

    def save(self, config=None):
        if config is not None:
            self.config = config
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_active_provider(self):
        return self.config.get("active_provider", "gemini")

    def set_active_provider(self, provider_name):
        if provider_name in self.config.get("providers", {}):
            self.config["active_provider"] = provider_name
            self.save()

    def get_provider_config(self, provider_name=None):
        if provider_name is None:
            provider_name = self.get_active_provider()
        return self.config.get("providers", {}).get(provider_name, {})

    def set_provider_key(self, provider_name, api_key):
        if provider_name in self.config.get("providers", {}):
            self.config["providers"][provider_name]["api_key"] = api_key.strip()
            self.save()

    def set_provider_model(self, provider_name, model_name):
        if provider_name in self.config.get("providers", {}):
            self.config["providers"][provider_name]["model"] = model_name
            self.save()

    def get_hotkey(self):
        return self.config.get("hotkey", "windows+c")

    def set_hotkey(self, hotkey_str):
        self.config["hotkey"] = hotkey_str.strip()
        self.save()

    def get_sidebar_width(self):
        return int(self.config.get("sidebar_width", 430))

    def get_always_on_top(self):
        return bool(self.config.get("always_on_top", True))

    def set_always_on_top(self, value):
        self.config["always_on_top"] = bool(value)
        self.save()

    def get_system_prompt(self):
        return self.config.get("system_prompt", DEFAULT_CONFIG["system_prompt"])
