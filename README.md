# AI Desktop Sidebar ⚡🤖

[![CI/CD Pipeline](https://github.com/MEhe132/gpt_sidebar/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/MEhe132/gpt_sidebar/actions/workflows/ci-cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **A modern, ultra-responsive desktop AI sidebar popup pinned to the right edge of your Windows screen.**  
> Seamlessly switch between **Google Gemini**, **DeepSeek (R1 / V3)**, and **OpenAI (ChatGPT)** with real-time streaming responses, summoned anytime with **`Alt + C`**!

---

## ✨ Highlights & Features

- 🪟 **Right-Edge Docked Sidebar**: Pinned smoothly to the right border of your desktop without covering your taskbar, always ready when you need it.
- ⌨️ **Global Hotkey (`Alt + C`)**: Toggle open or minimize the sidebar instantly from any application or full-screen game.
- 🧠 **Multi-Provider AI Switching**:
  - **Google Gemini**: Super-fast with free-tier access (`gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.0-flash`).
  - **DeepSeek**: Deep reasoning models (`deepseek-chat`, `deepseek-reasoner` / R1) via standard API.
  - **OpenAI (ChatGPT)**: Industry-standard models (`gpt-4o-mini`, `gpt-4o`, `o3-mini`).
- ⚡ **Real-Time Token Streaming**: Words appear on your screen as they are generated, powered by multi-threaded background workers (zero UI freezing).
- 📋 **Quick Chips & Clipboard Integration**:
  - One-click **"📋 Paste & Ask"** to inspect whatever you just copied.
  - Quick action prompts: **💡 Explain Code**, **🐛 Fix Bug**, **📝 Summarize**.
  - One-click **"📋 Copy"** button on every AI answer.
- ⚙️ **In-App Settings Drawer**: Enter and securely manage your API keys, change models, and customize hotkeys without touching code.
- 🎨 **Modern Dark UI**: Built with `CustomTkinter` with high DPI awareness on Windows.

---

## 🚀 Quick Start

### 1. Requirements
- Windows 10 or 11
- Python 3.9+

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/MEhe132/gpt_sidebar.git
cd gpt_sidebar

# Install dependencies
pip install -r requirements.txt
```

### 3. Launching
- **With Console Output**: Double-click `run.bat` or run:
  ```bash
  python main.py
  ```
- **Silent Background Mode** (No terminal window): Double-click `run_silent.vbs`.

---

## 🔑 Adding API Keys

1. Click the **⚙️ (Settings)** icon in the top right corner of the sidebar.
2. Paste your API key(s):
   - **Gemini Key**: [Get free key at Google AI Studio](https://aistudio.google.com/app/apikey)
   - **DeepSeek Key**: [Get key at DeepSeek Platform](https://platform.deepseek.com/api_keys)
   - **OpenAI Key**: [Get key at OpenAI Platform](https://platform.openai.com/api-keys)
3. Click **💾 Save Preferences**.

Your keys are stored locally on your machine in `config.json` (which is safely ignored by `.gitignore` so your keys are never committed to GitHub).

---

## ⌨️ Hotkey Customization

- Default: **`Alt + C`**
- If you want to change it (e.g. to `Alt + Space`, `Ctrl + Shift + A`, or `Ctrl + Space`), simply open **⚙️ Settings**, type your preferred shortcut in the **Global Hotkey** field, and click **Save**.

---

## 📂 Project Structure

```text
gpt_sidebar/
├── main.py              # Main entry point & hotkey listener
├── sidebar_ui.py        # CustomTkinter right-docked sidebar UI
├── settings_modal.py    # Preferences & API key management modal
├── ai_service.py        # Streaming client for Gemini, DeepSeek, & OpenAI
├── config_manager.py    # Configuration loader & persistent JSON manager
├── hotkey_manager.py    # Global hotkey hook for Windows
├── config.example.json  # Safe template configuration
├── requirements.txt     # Python package dependencies
├── run.bat              # Standard launch batch script
├── run_silent.vbs       # Invisible background launch script
└── README.md            # Documentation & setup guide
```

---

## 📜 License
MIT License. Created by [MEhe132](https://github.com/MEhe132).
