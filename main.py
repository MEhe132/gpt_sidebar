"""AI Desktop Sidebar - Main Entry Point."""

import sys
import os
import ctypes

from config_manager import ConfigManager
from sidebar_ui import AISidebarApp
from hotkey_manager import HotkeyManager

# Enable Per-Monitor DPI Awareness on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def main():
    print("=" * 50)
    print("🚀 Starting AI Desktop Sidebar...")
    print("=" * 50)

    config_mgr = ConfigManager()
    app = AISidebarApp(config_mgr)

    # Setup Global Hotkey
    hotkey = config_mgr.get_hotkey()

    def toggle_callback():
        app.after(0, app.toggle_visibility)

    hotkey_mgr = HotkeyManager(hotkey, toggle_callback)
    hotkey_mgr.start()

    # Rebind hotkey if changed in settings
    orig_on_settings_saved = app._on_settings_saved

    def wrapped_on_settings_saved():
        orig_on_settings_saved()
        new_hotkey = config_mgr.get_hotkey()
        hotkey_mgr.update_hotkey(new_hotkey)

    app._on_settings_saved = wrapped_on_settings_saved

    print(f"✨ Ready! Press [{hotkey.upper()}] to toggle the sidebar anytime.")

    def on_closing():
        print("Shutting down AI Sidebar...")
        hotkey_mgr.stop()
        app.destroy()
        sys.exit(0)

    app.protocol("WM_DELETE_WINDOW", on_closing)

    try:
        app.mainloop()
    finally:
        hotkey_mgr.stop()


if __name__ == "__main__":
    main()
