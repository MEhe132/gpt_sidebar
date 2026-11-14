"""Global Hotkey Manager for Windows."""

import threading
import keyboard
from typing import Callable, Optional


class HotkeyManager:
    def __init__(self, hotkey_str: str, on_triggered: Callable[[], None]):
        self.hotkey_str = hotkey_str.strip()
        self.on_triggered = on_triggered
        self._hook = None
        self._registered = False

    def start(self):
        self._register()

    def _register(self):
        try:
            self.stop()
            # Register using keyboard library
            self._hook = keyboard.add_hotkey(self.hotkey_str, self._handle_press, suppress=False)
            self._registered = True
            print(f"[Hotkey] Successfully registered global hotkey: '{self.hotkey_str}'")
        except Exception as e:
            print(f"[Hotkey] Warning: Could not register hotkey '{self.hotkey_str}': {e}")
            # Fallback to alt+space if windows+c fails (some Windows builds block win key hotkeys)
            if self.hotkey_str.lower() in ("windows+c", "win+c"):
                fallback = "alt+space"
                try:
                    self._hook = keyboard.add_hotkey(fallback, self._handle_press, suppress=False)
                    self._registered = True
                    print(f"[Hotkey] Registered fallback hotkey: '{fallback}'")
                except Exception as ex2:
                    print(f"[Hotkey] Fallback registration failed: {ex2}")

    def update_hotkey(self, new_hotkey_str: str):
        if new_hotkey_str and new_hotkey_str != self.hotkey_str:
            self.hotkey_str = new_hotkey_str.strip()
            self._register()

    def _handle_press(self):
        if self.on_triggered:
            try:
                self.on_triggered()
            except Exception as e:
                print(f"[Hotkey] Error executing hotkey callback: {e}")

    def stop(self):
        if self._hook is not None:
            try:
                keyboard.remove_hotkey(self._hook)
            except Exception:
                pass
            self._hook = None
            self._registered = False
