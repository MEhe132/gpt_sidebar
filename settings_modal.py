import customtkinter as ctk
import webbrowser
from typing import Callable, Optional


class SettingsModal(ctk.CTkToplevel):
    def __init__(self, parent, config_manager, on_save_callback: Optional[Callable] = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.on_save_callback = on_save_callback

        self.title("AI Sidebar Settings")
        self.geometry("540x680")
        self.resizable(False, False)

        # Center on screen or parent
        self.update_idletasks()
        x = parent.winfo_x() - 560
        y = max(50, parent.winfo_y() + 50)
        if x < 10:
            x = max(10, (self.winfo_screenwidth() - 540) // 2)
        self.geometry(f"+{x}+{y}")

        self.attributes("-topmost", True)
        self.grab_set()  # Make modal

        self._show_keys = {"gemini": False, "deepseek": False, "openai": False}
        self._build_ui()

    def _build_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 10))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="⚙️ Preferences & API Keys",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_lbl.pack(side="left")

        # Scrollable container for settings sections
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        cfg = self.config_manager.config
        providers = cfg.get("providers", {})

        # --- Section 1: Active Provider ---
        sec1 = self._create_section(scroll, "🤖 Default AI Engine")

        active_prov_lbl = ctk.CTkLabel(sec1, text="Active Provider:")
        active_prov_lbl.pack(anchor="w", padx=12, pady=(8, 2))

        self.active_prov_var = ctk.StringVar(value=self.config_manager.get_active_provider())
        self.active_prov_menu = ctk.CTkOptionMenu(
            sec1,
            values=["gemini", "deepseek", "openai"],
            variable=self.active_prov_var,
            width=200
        )
        self.active_prov_menu.pack(anchor="w", padx=12, pady=(0, 10))

        # --- Section 2: Gemini Setup ---
        gemini_cfg = providers.get("gemini", {})
        sec_gemini = self._create_section(scroll, "🌟 Google Gemini (Free Tier Available)")

        g_link_btn = ctk.CTkButton(
            sec_gemini,
            text="Get Free Gemini Key ↗ (Google AI Studio)",
            fg_color="transparent",
            text_color="#3b82f6",
            hover_color="#1e293b",
            anchor="w",
            height=20,
            command=lambda: webbrowser.open("https://aistudio.google.com/app/apikey")
        )
        g_link_btn.pack(anchor="w", padx=10, pady=(2, 6))

        self.gemini_key_entry, self.gemini_eye_btn = self._create_key_row(
            sec_gemini, "Gemini API Key:", gemini_cfg.get("api_key", ""), "gemini"
        )

        gemini_models = gemini_cfg.get("available_models", ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"])
        self.gemini_model_var = ctk.StringVar(value=gemini_cfg.get("model", "gemini-2.5-flash"))
        self._create_model_dropdown(sec_gemini, "Gemini Model:", gemini_models, self.gemini_model_var)

        # --- Section 3: DeepSeek Setup ---
        deepseek_cfg = providers.get("deepseek", {})
        sec_deepseek = self._create_section(scroll, "🐋 DeepSeek (R1 & V3)")

        ds_link_btn = ctk.CTkButton(
            sec_deepseek,
            text="Get DeepSeek Key ↗ (Platform.deepseek.com)",
            fg_color="transparent",
            text_color="#3b82f6",
            hover_color="#1e293b",
            anchor="w",
            height=20,
            command=lambda: webbrowser.open("https://platform.deepseek.com/api_keys")
        )
        ds_link_btn.pack(anchor="w", padx=10, pady=(2, 6))

        self.deepseek_key_entry, self.deepseek_eye_btn = self._create_key_row(
            sec_deepseek, "DeepSeek API Key:", deepseek_cfg.get("api_key", ""), "deepseek"
        )

        ds_models = deepseek_cfg.get("available_models", ["deepseek-chat", "deepseek-reasoner"])
        self.deepseek_model_var = ctk.StringVar(value=deepseek_cfg.get("model", "deepseek-chat"))
        self._create_model_dropdown(sec_deepseek, "DeepSeek Model:", ds_models, self.deepseek_model_var)

        # --- Section 4: OpenAI Setup ---
        openai_cfg = providers.get("openai", {})
        sec_openai = self._create_section(scroll, "🟢 OpenAI (ChatGPT)")

        oa_link_btn = ctk.CTkButton(
            sec_openai,
            text="Get OpenAI Key ↗ (Platform.openai.com)",
            fg_color="transparent",
            text_color="#3b82f6",
            hover_color="#1e293b",
            anchor="w",
            height=20,
            command=lambda: webbrowser.open("https://platform.openai.com/api-keys")
        )
        oa_link_btn.pack(anchor="w", padx=10, pady=(2, 6))

        self.openai_key_entry, self.openai_eye_btn = self._create_key_row(
            sec_openai, "OpenAI API Key:", openai_cfg.get("api_key", ""), "openai"
        )

        oa_models = openai_cfg.get("available_models", ["gpt-4o-mini", "gpt-4o", "o3-mini"])
        self.openai_model_var = ctk.StringVar(value=openai_cfg.get("model", "gpt-4o-mini"))
        self._create_model_dropdown(sec_openai, "OpenAI Model:", oa_models, self.openai_model_var)

        # --- Section 5: Hotkey & Display ---
        sec_display = self._create_section(scroll, "⌨️ Hotkey & Window Behavior")

        hotkey_lbl = ctk.CTkLabel(sec_display, text="Global Hotkey (Toggle Sidebar):")
        hotkey_lbl.pack(anchor="w", padx=12, pady=(6, 2))
        self.hotkey_entry = ctk.CTkEntry(sec_display, width=220)
        self.hotkey_entry.insert(0, self.config_manager.get_hotkey())
        self.hotkey_entry.pack(anchor="w", padx=12, pady=(0, 8))

        self.always_on_top_var = ctk.BooleanVar(value=self.config_manager.get_always_on_top())
        topmost_check = ctk.CTkCheckBox(
            sec_display,
            text="Always on Top (Keep pinned over other windows)",
            variable=self.always_on_top_var
        )
        topmost_check.pack(anchor="w", padx=12, pady=(4, 8))

        # Bottom Actions Bar
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=24, pady=(10, 18))

        self.status_lbl = ctk.CTkLabel(bottom_bar, text="", text_color="#10b981")
        self.status_lbl.pack(side="left")

        save_btn = ctk.CTkButton(
            bottom_bar,
            text="💾 Save Preferences",
            font=ctk.CTkFont(weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            width=140,
            command=self._on_save
        )
        save_btn.pack(side="right")

    def _create_section(self, parent, title):
        frame = ctk.CTkFrame(parent, corner_radius=8)
        frame.pack(fill="x", pady=8)

        lbl = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=14, weight="bold"))
        lbl.pack(anchor="w", padx=12, pady=(10, 4))
        return frame

    def _create_key_row(self, parent, label_text, current_val, prov_key):
        lbl = ctk.CTkLabel(parent, text=label_text)
        lbl.pack(anchor="w", padx=12, pady=(4, 2))

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 6))

        entry = ctk.CTkEntry(row, show="•", placeholder_text="Enter API key...", width=360)
        if current_val:
            entry.insert(0, current_val)
        entry.pack(side="left", fill="x", expand=True)

        eye_btn = ctk.CTkButton(
            row,
            text="👁️",
            width=36,
            fg_color="#334155",
            hover_color="#475569",
            command=lambda: self._toggle_eye(entry, prov_key)
        )
        eye_btn.pack(side="left", padx=(6, 0))
        return entry, eye_btn

    def _toggle_eye(self, entry, prov_key):
        self._show_keys[prov_key] = not self._show_keys[prov_key]
        entry.configure(show="" if self._show_keys[prov_key] else "•")

    def _create_model_dropdown(self, parent, label_text, options, variable):
        lbl = ctk.CTkLabel(parent, text=label_text)
        lbl.pack(anchor="w", padx=12, pady=(4, 2))

        menu = ctk.CTkOptionMenu(parent, values=options, variable=variable, width=240)
        menu.pack(anchor="w", padx=12, pady=(0, 10))

    def _on_save(self):
        # Update active provider
        active_prov = self.active_prov_var.get()
        self.config_manager.set_active_provider(active_prov)

        # Update Gemini
        self.config_manager.set_provider_key("gemini", self.gemini_key_entry.get())
        self.config_manager.set_provider_model("gemini", self.gemini_model_var.get())

        # Update DeepSeek
        self.config_manager.set_provider_key("deepseek", self.deepseek_key_entry.get())
        self.config_manager.set_provider_model("deepseek", self.deepseek_model_var.get())

        # Update OpenAI
        self.config_manager.set_provider_key("openai", self.openai_key_entry.get())
        self.config_manager.set_provider_model("openai", self.openai_model_var.get())

        # Update Hotkey & Window
        self.config_manager.set_hotkey(self.hotkey_entry.get())
        self.config_manager.set_always_on_top(self.always_on_top_var.get())

        self.status_lbl.configure(text="✓ Settings Saved Successfully!")
        self.after(1200, lambda: self.status_lbl.configure(text=""))

        if self.on_save_callback:
            self.on_save_callback()
