"""Modern Edge-Docked AI Sidebar Popup with Resizing and Left/Right Docking."""

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

    def clear_text(self):
        self.content = ""
        self.text_box.configure(state="normal")
        self.text_box.delete("1.0", "end")
        self.text_box.configure(state="disabled")

    def append_chunk(self, chunk: str):
        self.content += chunk
        self.text_box.configure(state="normal")
        self.text_box.insert("end", chunk)
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
        self._quit_callback = None

        self._init_window()
        self._build_layout_containers()
        self._build_header()
        self._build_toolbar()
        self._build_chat_area()
        self._build_quick_chips()
        self._build_input_area()
        self._layout_frames()

        # Automatically place cursor in input box on launch
        self.after(100, self.focus_input)

    def set_quit_callback(self, cb):
        self._quit_callback = cb

    def _init_window(self):
        self.title("AI Sidebar")
        self.overrideredirect(True)  # Frameless docked sidebar
        self.attributes("-topmost", self.config_manager.get_always_on_top())

        # Retrieve Screen Work Area (Physical pixels)
        wx, wy, ww, wh = get_screen_work_area()
        self.work_x = wx
        self.work_y = wy
        self.work_w = ww
        self.work_h = wh

        self.dock_side = self.config_manager.get_dock_side()  # "right" or "left"
        self.sidebar_w = self.config_manager.get_sidebar_width()
        self.sidebar_h = self.work_h
        self.sidebar_y = self.work_y

        if self.dock_side == "right":
            self.sidebar_x = self.work_x + self.work_w - self.sidebar_w
        else:
            self.sidebar_x = self.work_x

        self.set_window_geometry(self.sidebar_w, self.sidebar_h, self.sidebar_x, self.sidebar_y)
        self.configure(fg_color="#0f172a")

    def set_window_geometry(self, width, height, x, y):
        """Bypasses CustomTkinter DPI multiplier to keep window position pixel-perfect with screen edges."""
        self.sidebar_w = int(width)
        self.sidebar_h = int(height)
        self.sidebar_x = int(x)
        self.sidebar_y = int(y)
        tk.Tk.geometry(self, f"{self.sidebar_w}x{self.sidebar_h}+{self.sidebar_x}+{self.sidebar_y}")

    def _build_layout_containers(self):
        # Resize Grip Strip on inner edge
        self.resize_grip = tk.Frame(self, bg="#334155", width=6, cursor="size_we")
        self.resize_grip.bind("<Enter>", lambda e: self.resize_grip.configure(bg="#3b82f6"))
        self.resize_grip.bind("<Leave>", lambda e: self.resize_grip.configure(bg="#334155"))
        self.resize_grip.bind("<Button-1>", self._on_resize_start)
        self.resize_grip.bind("<B1-Motion>", self._on_resize_drag)
        self.resize_grip.bind("<ButtonRelease-1>", self._on_resize_end)

        # Main content container
        self.main_container = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=0)

    def _layout_frames(self):
        self.resize_grip.pack_forget()
        self.main_container.pack_forget()

        if self.dock_side == "right":
            # Grip on the left edge of sidebar
            self.resize_grip.pack(side="left", fill="y")
            self.main_container.pack(side="right", fill="both", expand=True)
        else:
            # Grip on the right edge of sidebar
            self.resize_grip.pack(side="right", fill="y")
            self.main_container.pack(side="left", fill="both", expand=True)

    def _on_resize_start(self, event):
        self._resize_start_x = event.x_root
        self._resize_start_w = self.sidebar_w

    def _on_resize_drag(self, event):
        if self.dock_side == "right":
            # Dragging left increases width
            dx = self._resize_start_x - event.x_root
        else:
            # Dragging right increases width
            dx = event.x_root - self._resize_start_x

        new_w = max(280, min(self.work_w - 60, self._resize_start_w + dx))
        self.sidebar_w = new_w

        if self.dock_side == "right":
            self.sidebar_x = self.work_x + self.work_w - self.sidebar_w
        else:
            self.sidebar_x = self.work_x

        self.set_window_geometry(self.sidebar_w, self.sidebar_h, self.sidebar_x, self.sidebar_y)

    def _on_resize_end(self, event):
        self.config_manager.set_sidebar_width(self.sidebar_w)

    def toggle_dock_side(self):
        """Swaps docking position between Right and Left edges of screen."""
        self.dock_side = "left" if self.dock_side == "right" else "right"
        self.config_manager.set_dock_side(self.dock_side)

        if self.dock_side == "right":
            self.sidebar_x = self.work_x + self.work_w - self.sidebar_w
            self.dock_btn.configure(text="◀ Left")
        else:
            self.sidebar_x = self.work_x
            self.dock_btn.configure(text="Right ▶")

        self._layout_frames()
        self.set_window_geometry(self.sidebar_w, self.sidebar_h, self.sidebar_x, self.sidebar_y)

    def _force_windows_foreground(self):
        """Forces the Tkinter window to become the active foreground window in Windows OS using AttachThreadInput."""
        try:
            hwnd = self.winfo_id()
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            # Find top-level OS window ancestor (GA_ROOT = 2)
            top_hwnd = user32.GetAncestor(hwnd, 2)
            if not top_hwnd:
                top_hwnd = hwnd

            fore_hwnd = user32.GetForegroundWindow()
            fore_thread = user32.GetWindowThreadProcessId(fore_hwnd, None)
            cur_thread = kernel32.GetCurrentThreadId()

            if fore_thread and fore_thread != cur_thread:
                user32.AttachThreadInput(cur_thread, fore_thread, True)
                user32.BringWindowToTop(top_hwnd)
                user32.SetForegroundWindow(top_hwnd)
                user32.SetActiveWindow(top_hwnd)
                user32.SwitchToThisWindow(top_hwnd, True)
                user32.AttachThreadInput(cur_thread, fore_thread, False)
            else:
                user32.BringWindowToTop(top_hwnd)
                user32.SetForegroundWindow(top_hwnd)
                user32.SetActiveWindow(top_hwnd)
                user32.SwitchToThisWindow(top_hwnd, True)
        except Exception:
            pass

    def toggle_visibility(self):
        """Toggle hide/show sidebar on hotkey press (Alt + C)."""
        if self._is_visible:
            self.withdraw()
            self._is_visible = False
        else:
            self.deiconify()
            self._is_visible = True
            self.focus_input()

    def focus_input(self):
        """Brings window to foreground and places typing cursor directly in the prompt text box."""
        try:
            self.lift()
            self.attributes("-topmost", True)
            self._force_windows_foreground()

            def _apply():
                try:
                    if hasattr(self.input_box, "_textbox"):
                        self.input_box._textbox.focus_force()
                        self.input_box._textbox.mark_set("insert", "end")
                    else:
                        self.input_box.focus_set()
                except Exception:
                    pass

            _apply()
            # Staggered focus passes to ensure Windows finishes processing the physical Alt+C release
            self.after(30, _apply)
            self.after(80, _apply)
            self.after(160, _apply)
        except Exception:
            pass

    def quit_app(self):
        """Completely terminates and closes the application."""
        if self._quit_callback:
            self._quit_callback()
        else:
            try:
                self.ai_service.stop_stream()
            except Exception:
                pass
            self.destroy()
            os._exit(0)

    def _build_header(self):
        header_frame = ctk.CTkFrame(self.main_container, fg_color="#1e293b", corner_radius=0, height=52)
        header_frame.pack(fill="x", side="top")

        # 1. First pack right-side control buttons directly into header_frame from right-to-left:
        # Prominent Close (✕) button: always anchored to the very top-right edge
        close_btn = ctk.CTkButton(
            header_frame,
            text="✕",
            width=28,
            height=28,
            fg_color="#dc2626",
            hover_color="#ef4444",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.quit_app
        )
        close_btn.pack(side="right", padx=(2, 6), pady=8)

        # Minimize / Hide button (hides to Alt+C)
        min_btn = ctk.CTkButton(
            header_frame,
            text="—",
            width=26,
            height=28,
            fg_color="#475569",
            hover_color="#64748b",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.toggle_visibility
        )
        min_btn.pack(side="right", padx=2, pady=8)

        # Settings
        settings_btn = ctk.CTkButton(
            header_frame,
            text="⚙️",
            width=26,
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            command=self.open_settings
        )
        settings_btn.pack(side="right", padx=2, pady=8)

        # Clear chat
        clear_btn = ctk.CTkButton(
            header_frame,
            text="🗑️",
            width=26,
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            command=self.clear_chat
        )
        clear_btn.pack(side="right", padx=2, pady=8)

        # Dock Shift button (Left <-> Right)
        dock_txt = "◀ Left" if self.dock_side == "right" else "Right ▶"
        self.dock_btn = ctk.CTkButton(
            header_frame,
            text=dock_txt,
            width=50,
            height=28,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            command=self.toggle_dock_side
        )
        self.dock_btn.pack(side="right", padx=2, pady=8)

        # Title & Logo (packed side="left", truncates cleanly if narrow)
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=8, pady=8, fill="x", expand=True)

        logo_lbl = ctk.CTkLabel(
            title_box,
            text="⚡ AI Sidebar",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#f8fafc",
            anchor="w"
        )
        logo_lbl.pack(side="left")

    def _build_toolbar(self):
        # Provider Switcher Toolbar
        toolbar = ctk.CTkFrame(self.main_container, fg_color="#182234", corner_radius=0, height=38)
        toolbar.pack(fill="x", side="top")

        lbl_prov = ctk.CTkLabel(toolbar, text="Model:", font=ctk.CTkFont(size=12), text_color="#94a3b8")
        lbl_prov.pack(side="left", padx=(10, 4), pady=6)

        self.provider_var = ctk.StringVar(value=self.config_manager.get_active_provider())
        self.provider_seg = ctk.CTkSegmentedButton(
            toolbar,
            values=["gemini", "groq", "deepseek", "openai"],
            variable=self.provider_var,
            command=self._on_provider_change,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.provider_seg.pack(side="left", padx=2, pady=6)

        self.model_badge = ctk.CTkLabel(
            toolbar,
            text=self._get_current_model_display(),
            font=ctk.CTkFont(size=11),
            text_color="#38bdf8"
        )
        self.model_badge.pack(side="right", padx=10, pady=6)

    def _get_current_model_display(self):
        prov = self.config_manager.get_active_provider()
        model = self.config_manager.get_provider_config(prov).get("model", "")
        return model

    def _on_provider_change(self, selected_provider):
        self.config_manager.set_active_provider(selected_provider)
        self.model_badge.configure(text=self._get_current_model_display())

    def _build_chat_area(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=8, pady=6)
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
            f"• Press `{hotkey.upper()}` to toggle show/hide.\n"
            f"• Drag the inner vertical edge to increase/decrease width.\n"
            f"• Click '◀ Left' / 'Right ▶' in the header to shift sides.\n"
            f"• Click '✕' in the top-right corner to exit the app.\n"
            f"• Click ⚙️ to configure your API keys."
        )
        w_body = ctk.CTkLabel(welcome_frame, text=msg, justify="left", font=ctk.CTkFont(size=12), text_color="#cbd5e1")
        w_body.pack(anchor="w", padx=12, pady=(0, 10))

    def _build_quick_chips(self):
        chips_frame = ctk.CTkFrame(self.main_container, fg_color="transparent", height=32)
        chips_frame.pack(fill="x", side="top", padx=8, pady=(2, 6))

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
        input_container = ctk.CTkFrame(self.main_container, fg_color="#1e293b", corner_radius=12)
        input_container.pack(fill="x", side="bottom", padx=8, pady=(4, 10))

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

        # Action button container permanently locked to the RIGHT edge so it never disappears on shrink
        self.btn_actions = ctk.CTkFrame(btn_row, fg_color="transparent")
        self.btn_actions.pack(side="right")

        self.send_btn = ctk.CTkButton(
            self.btn_actions,
            text="Send ➔",
            width=68,
            height=26,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.send_message
        )
        self.send_btn.pack(side="right")

        self.stop_btn = ctk.CTkButton(
            self.btn_actions,
            text="⏹ Stop",
            width=65,
            height=26,
            fg_color="#dc2626",
            hover_color="#ef4444",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._stop_generation
        )
        # Initially not packed; appears in btn_actions when streaming

        self.hint_lbl = ctk.CTkLabel(
            btn_row,
            text="Enter to send • Shift+Enter newline",
            font=ctk.CTkFont(size=10),
            text_color="#64748b",
            anchor="w"
        )
        self.hint_lbl.pack(side="left", padx=4, fill="x", expand=True)

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
        self.after(0, lambda: self._update_stream_ui(chunk))

    def _update_stream_ui(self, chunk: str):
        if not self.is_streaming:
            return
        self.streamed_content += chunk
        if self.current_stream_card:
            if self.current_stream_card.content == "Thinking...":
                self.current_stream_card.clear_text()
            self.current_stream_card.append_chunk(chunk)
        self._throttled_scroll()

    def _throttled_scroll(self):
        if not hasattr(self, "_scroll_job") or self._scroll_job is None:
            self._scroll_job = self.after(60, self._do_scroll)

    def _do_scroll(self):
        self._scroll_job = None
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
        self.attributes("-topmost", self.config_manager.get_always_on_top())
        self.provider_var.set(self.config_manager.get_active_provider())
        self.model_badge.configure(text=self._get_current_model_display())
