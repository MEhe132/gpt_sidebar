"""Modern Right-Edge AI Sidebar Popup built with CustomTkinter."""

import os
import sys
import ctypes
from ctypes import wintypes
import tkinter as tk
import customtkinter as ctk
from typing import List, Dict, Optional

from settings_modal import SettingsModal
from ai_service import AIService

# Set default theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def get_screen_work_area():
    """Retrieves usable desktop work area (excluding taskbar) using Win32 API."""
    try:
        rect = wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
    except Exception:
        pass
    # Fallback if Win32 API is unavailable
    root = tk.Tk()
    root.withdraw()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.destroy()
    return 0, 0, sw, sh


class MessageCard(ctk.CTkFrame):
    """Modern chat bubble card for User and AI responses."""

    def __init__(self, parent, role: str, content: str, provider_name: str = "", model_name: str = ""):
        is_user = (role == "user")
        fg_color = "#1e3a8a" if is_user else "#1e293b"
        border_color = "#3b82f6" if is_user else "#334155"

        super().__init__(
            parent,
            fg_color=fg_color,
            border_color=border_color,
            border_width=1,
            corner_radius=12
        )
        self.role = role
        self.content = content
        self.provider_name = provider_name
        self.model_name = model_name

        self._build_card(is_user)

    def _build_card(self, is_user: bool):
        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(8, 4))

        if is_user:
            title = ctk.CTkLabel(
                header,
                text="👤 You",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#93c5fd"
            )
            title.pack(side="right")
        else:
            model_info = f" • {self.model_name}" if self.model_name else ""
            prov_str = f"🤖 {self.provider_name.capitalize()}{model_info}"
            title = ctk.CTkLabel(
                header,
                text=prov_str,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#60a5fa"
            )
            title.pack(side="left")

            # Copy button for Assistant messages
            copy_btn = ctk.CTkButton(
                header,
                text="📋 Copy",
                width=50,
                height=22,
                font=ctk.CTkFont(size=11),
                fg_color="#334155",
                hover_color="#475569",
                command=self.copy_content
            )
            copy_btn.pack(side="right")

        # Text container
        self.text_box = ctk.CTkTextbox(
            self,
            fg_color="transparent",
            text_color="#f8fafc",
            font=ctk.CTkFont(size=13),
            wrap="word",
            activate_scrollbars=False
        )
        self.text_box.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        self.text_box.insert("1.0", self.content)
        self.text_box.configure(state="disabled")
        self._adjust_height()

    def update_text(self, new_text: str):
        self.content = new_text
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", self.content)
        self.text_box.configure(state="disabled")
        self._adjust_height()

    def _adjust_height(self):
        lines = self.content.count("\n") + int(len(self.content) / 42) + 1
        calculated_h = max(38, min(450, lines * 22))
        self.text_box.configure(height=calculated_h)

    def copy_content(self):
        self.clipboard_clear()
        self.clipboard_append(self.content)


class AISidebarApp(ctk.CTk):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.ai_service = AIService(config_manager)

        self.messages: List[Dict[str, str]] = []
        self.current_stream_card: Optional[MessageCard] = None
        self.is_streaming = False
        self._is_visible = True

        self._init_window()
        self._build_header()
        self._build_chat_area()
        self._build_quick_chips()
        self._build_input_area()

    def _init_window(self):
        self.title("AI Sidebar")
        self.overrideredirect(True)  # Frameless docked sidebar
        self.attributes("-topmost", self.config_manager.get_always_on_top())

        # Calculate Right-Edge Screen Work Area
        wx, wy, ww, wh = get_screen_work_area()
        self.sidebar_w = self.config_manager.get_sidebar_width()
        self.sidebar_h = wh
        self.sidebar_x = wx + ww - self.sidebar_w
        self.sidebar_y = wy

        self.geometry(f"{self.sidebar_w}x{self.sidebar_h}+{self.sidebar_x}+{self.sidebar_y}")

        # Dark border outline for frameless window
        self.configure(fg_color="#0f172a")

    def toggle_visibility(self):
        """Toggle hide/show right-edge sidebar on hotkey press."""
        if self._is_visible:
            self.withdraw()
            self._is_visible = False
        else:
            self.deiconify()
            self.lift()
            self.focus_force()
            self._is_visible = True
            # Focus prompt entry
            self.input_box.focus_set()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=0, height=52)
        header_frame.pack(fill="x", side="top")

        # Title & Logo
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=12, pady=8)

        logo_lbl = ctk.CTkLabel(
            title_box,
            text="⚡ AI Sidebar",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#f8fafc"
        )
        logo_lbl.pack(side="left")

        # Right control buttons
        controls = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls.pack(side="right", padx=10, pady=8)

        # Clear chat
        clear_btn = ctk.CTkButton(
            controls,
            text="🗑️",
            width=32,
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            command=self.clear_chat
        )
        clear_btn.pack(side="left", padx=3)

        # Settings
        settings_btn = ctk.CTkButton(
            controls,
            text="⚙️",
            width=32,
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            command=self.open_settings
        )
        settings_btn.pack(side="left", padx=3)

        # Minimize / Hide button
        hide_btn = ctk.CTkButton(
            controls,
            text="✕",
            width=32,
            height=28,
            fg_color="#dc2626",
            hover_color="#ef4444",
            command=self.toggle_visibility
        )
        hide_btn.pack(side="left", padx=3)

        # Provider Switcher Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="#182234", corner_radius=0, height=38)
        toolbar.pack(fill="x", side="top")

        lbl_prov = ctk.CTkLabel(toolbar, text="Model:", font=ctk.CTkFont(size=12), text_color="#94a3b8")
        lbl_prov.pack(side="left", padx=(12, 6), pady=6)

        self.provider_var = ctk.StringVar(value=self.config_manager.get_active_provider())
        self.provider_seg = ctk.CTkSegmentedButton(
            toolbar,
            values=["gemini", "deepseek", "openai"],
            variable=self.provider_var,
            command=self._on_provider_change,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.provider_seg.pack(side="left", padx=4, pady=6)

        self.model_badge = ctk.CTkLabel(
            toolbar,
            text=self._get_current_model_display(),
            font=ctk.CTkFont(size=11),
            text_color="#38bdf8"
        )
        self.model_badge.pack(side="right", padx=12, pady=6)

    def _get_current_model_display(self):
        prov = self.config_manager.get_active_provider()
        model = self.config_manager.get_provider_config(prov).get("model", "")
        return model

    def _on_provider_change(self, selected_provider):
        self.config_manager.set_active_provider(selected_provider)
        self.model_badge.configure(text=self._get_current_model_display())

    def _build_chat_area(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=8)

        # Welcome Card
        self._add_welcome_card()

    def _add_welcome_card(self):
        welcome_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#1e293b", corner_radius=12)
        welcome_frame.pack(fill="x", pady=6, padx=4)

        w_title = ctk.CTkLabel(
            welcome_frame,
            text="👋 Welcome to your AI Sidebar!",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38bdf8"
        )
        w_title.pack(anchor="w", padx=12, pady=(10, 4))

        hotkey = self.config_manager.get_hotkey()
        msg = (
            f"• Press `{hotkey.upper()}` anytime to toggle this sidebar.\n"
            f"• Switch between Gemini, DeepSeek, and OpenAI at the top.\n"
            f"• Click ⚙️ to configure your API keys.\n"
            f"• Ask coding questions, debug errors, or summarize text!"
        )
        w_body = ctk.CTkLabel(welcome_frame, text=msg, justify="left", font=ctk.CTkFont(size=12), text_color="#cbd5e1")
        w_body.pack(anchor="w", padx=12, pady=(0, 10))

    def _build_quick_chips(self):
        chips_frame = ctk.CTkFrame(self, fg_color="transparent", height=32)
        chips_frame.pack(fill="x", side="top", padx=10, pady=(2, 6))

        chips = [
            ("📋 Paste & Ask", self._paste_from_clipboard),
            ("💡 Explain", lambda: self._insert_chip_prompt("Explain this code step-by-step:\n")),
            ("🐛 Fix Bug", lambda: self._insert_chip_prompt("Identify and fix the bug in this code:\n")),
            ("📝 Summarize", lambda: self._insert_chip_prompt("Summarize the following text concisely:\n")),
        ]

        for text, cmd in chips:
            btn = ctk.CTkButton(
                chips_frame,
                text=text,
                height=24,
                font=ctk.CTkFont(size=11),
                fg_color="#1e293b",
                hover_color="#334155",
                text_color="#94a3b8",
                corner_radius=12,
                command=cmd
            )
            btn.pack(side="left", padx=2)

    def _insert_chip_prompt(self, prefix):
        current = self.input_box.get("1.0", "end").strip()
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", prefix + current)
        self.input_box.focus_set()

    def _paste_from_clipboard(self):
        try:
            clip = self.clipboard_get()
            if clip:
                current = self.input_box.get("1.0", "end").strip()
                to_insert = f"{current}\n{clip}" if current else clip
                self.input_box.delete("1.0", "end")
                self.input_box.insert("1.0", to_insert)
                self.input_box.focus_set()
        except Exception:
            pass

    def _build_input_area(self):
        input_container = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        input_container.pack(fill="x", side="bottom", padx=10, pady=(4, 12))

        # Text input
        self.input_box = ctk.CTkTextbox(
            input_container,
            height=70,
            fg_color="transparent",
            text_color="#f8fafc",
            font=ctk.CTkFont(size=13),
            wrap="word",
            activate_scrollbars=True
        )
        self.input_box.pack(fill="x", padx=8, pady=(8, 4))
        self.input_box.bind("<Return>", self._on_enter_pressed)
        self.input_box.bind("<Shift-Return>", lambda e: None)  # Allow newline

        # Bottom row inside input box: Hint & Buttons
        btn_row = ctk.CTkFrame(input_container, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(0, 6))

        hint_lbl = ctk.CTkLabel(
            btn_row,
            text="Enter to send • Shift+Enter newline",
            font=ctk.CTkFont(size=10),
            text_color="#64748b"
        )
        hint_lbl.pack(side="left", padx=4)

        self.stop_btn = ctk.CTkButton(
            btn_row,
            text="⏹ Stop",
            width=65,
            height=26,
            fg_color="#dc2626",
            hover_color="#ef4444",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._stop_generation
        )
        # Initially hidden

        self.send_btn = ctk.CTkButton(
            btn_row,
            text="Send ➔",
            width=70,
            height=26,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.send_message
        )
        self.send_btn.pack(side="right")

    def _on_enter_pressed(self, event):
        if not (event.state & 0x0001):  # Shift key NOT pressed
            self.send_message()
            return "break"  # Prevent default newline

    def send_message(self):
        if self.is_streaming:
            return

        user_text = self.input_box.get("1.0", "end").strip()
        if not user_text:
            return

        self.input_box.delete("1.0", "end")

        # Add to history
        self.messages.append({"role": "user", "content": user_text})

        # Render User Bubble
        user_card = MessageCard(self.scroll_frame, role="user", content=user_text)
        user_card.pack(fill="x", pady=4, padx=4)

        # Setup Assistant Bubble for streaming
        active_prov = self.config_manager.get_active_provider()
        model_name = self.config_manager.get_provider_config(active_prov).get("model", "")

        self.current_stream_card = MessageCard(
            self.scroll_frame,
            role="assistant",
            content="Thinking...",
            provider_name=active_prov,
            model_name=model_name
        )
        self.current_stream_card.pack(fill="x", pady=4, padx=4)
        self._scroll_to_bottom()

        # Update UI to streaming state
        self.is_streaming = True
        self.send_btn.pack_forget()
        self.stop_btn.pack(side="right")

        self.streamed_content = ""

        # Trigger streaming service in background
        self.ai_service.stream_chat(
            messages=self.messages,
            on_chunk=self._on_stream_chunk,
            on_complete=self._on_stream_complete,
            on_error=self._on_stream_error,
            override_provider=active_prov
        )

    def _on_stream_chunk(self, chunk: str):
        # Post to main Tkinter thread
        self.after(0, lambda: self._update_stream_ui(chunk))

    def _update_stream_ui(self, chunk: str):
        if not self.is_streaming:
            return
        self.streamed_content += chunk
        if self.current_stream_card:
            self.current_stream_card.update_text(self.streamed_content)
        self._scroll_to_bottom()

    def _on_stream_complete(self, final_text: str):
        self.after(0, lambda: self._finish_streaming(final_text))

    def _finish_streaming(self, final_text: str):
        self.is_streaming = False
        self.stop_btn.pack_forget()
        self.send_btn.pack(side="right")

        if self.current_stream_card:
            self.current_stream_card.update_text(final_text)
            self.messages.append({"role": "assistant", "content": final_text})

        self.current_stream_card = None
        self._scroll_to_bottom()

    def _on_stream_error(self, error_message: str):
        self.after(0, lambda: self._handle_error_ui(error_message))

    def _handle_error_ui(self, error_message: str):
        self.is_streaming = False
        self.stop_btn.pack_forget()
        self.send_btn.pack(side="right")

        if self.current_stream_card:
            self.current_stream_card.update_text(f"⚠️ {error_message}")

        self.current_stream_card = None
        self._scroll_to_bottom()

    def _stop_generation(self):
        self.ai_service.stop_stream()
        self.is_streaming = False
        self.stop_btn.pack_forget()
        self.send_btn.pack(side="right")

    def _scroll_to_bottom(self):
        self.update_idletasks()
        try:
            self.scroll_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def clear_chat(self):
        self.messages.clear()
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self._add_welcome_card()

    def open_settings(self):
        SettingsModal(self, self.config_manager, on_save_callback=self._on_settings_saved)

    def _on_settings_saved(self):
        # Refresh UI according to newly saved config
        self.attributes("-topmost", self.config_manager.get_always_on_top())
        self.provider_var.set(self.config_manager.get_active_provider())
        self.model_badge.configure(text=self._get_current_model_display())
