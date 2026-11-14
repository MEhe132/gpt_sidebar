"""Unified AI Streaming Service for Gemini, DeepSeek, and OpenAI."""

import threading
from typing import List, Dict, Callable, Optional


class AIService:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self._stop_requested = False
        self._current_thread: Optional[threading.Thread] = None
        self._gemini_client = None
        self._gemini_key = None
        self._openai_clients = {}

    def stop_stream(self):
        """Signals the current streaming generator to stop immediately."""
        self._stop_requested = True

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        on_chunk: Callable[[str], None],
        on_complete: Callable[[str], None],
        on_error: Callable[[str], None],
        override_provider: Optional[str] = None
    ):
        """Spawns a worker thread to stream completions to avoid freezing the GUI."""
        self._stop_requested = False

        provider = override_provider or self.config_manager.get_active_provider()
        provider_cfg = self.config_manager.get_provider_config(provider)
        api_key = provider_cfg.get("api_key", "").strip()
        model = provider_cfg.get("model", "")
        system_prompt = self.config_manager.get_system_prompt()

        if not api_key:
            on_error(
                f"Missing API Key for {provider.capitalize()}.\n\n"
                f"👉 Click the Settings (⚙️) button at the top to paste your {provider.capitalize()} API key."
            )
            return

        def _worker():
            accumulated_text = ""
            try:
                if provider == "gemini":
                    self._stream_gemini(api_key, model, system_prompt, messages, on_chunk, accumulated_callback=lambda txt: non_local_set(txt))
                elif provider in ("deepseek", "openai", "groq"):
                    base_url = provider_cfg.get("base_url")
                    self._stream_openai_compatible(
                        api_key=api_key,
                        base_url=base_url,
                        model=model,
                        system_prompt=system_prompt,
                        messages=messages,
                        on_chunk=on_chunk,
                        accumulated_callback=lambda txt: non_local_set(txt)
                    )
                else:
                    on_error(f"Unsupported provider: '{provider}'")
                    return

                if not self._stop_requested:
                    on_complete(non_local_get())
                else:
                    on_complete(non_local_get() + "\n\n*(Generation stopped)*")

            except Exception as e:
                err_msg = str(e)
                if "API_KEY_INVALID" in err_msg or "Incorrect API key" in err_msg or "401" in err_msg:
                    on_error(f"Authentication Failed: Invalid API key for {provider.capitalize()}.\nPlease verify your key in Settings ⚙️.")
                elif "402" in err_msg or "Insufficient Balance" in err_msg:
                    on_error(f"Insufficient Balance on {provider.capitalize()} (Error 402).\nYour account has $0 prepaid balance. Please top up your API credits at {provider.capitalize()}'s developer dashboard.")
                elif "insufficient_quota" in err_msg:
                    on_error(f"Quota Exceeded for {provider.capitalize()}.\nYour credit balance is $0 or your trial has expired. Please check your billing dashboard.")
                elif "RESOURCE_EXHAUSTED" in err_msg or "rate limit" in err_msg.lower() or "429" in err_msg:
                    on_error(f"Rate Limit Exceeded for {provider.capitalize()}.\nPlease wait a moment or switch to another model/provider.")
                else:
                    on_error(f"Error ({provider.capitalize()}): {err_msg}")

        holder = {"text": ""}
        def non_local_set(t):
            holder["text"] = t
        def non_local_get():
            return holder["text"]

        self._current_thread = threading.Thread(target=_worker, daemon=True)
        self._current_thread.start()

    def _stream_gemini(self, api_key: str, model: str, system_prompt: str, messages: List[Dict[str, str]], on_chunk: Callable[[str], None], accumulated_callback):
        from google import genai
        from google.genai import types

        # Reuse client to avoid SSL handshake penalty on every request
        if self._gemini_client is None or self._gemini_key != api_key:
            self._gemini_client = genai.Client(api_key=api_key)
            self._gemini_key = api_key

        client = self._gemini_client

        formatted_contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            formatted_contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )

        # Eliminate thinking latency (thinking_budget=0) for ultra-fast instant answers
        thinking_cfg = None
        try:
            thinking_cfg = types.ThinkingConfig(thinking_budget=0)
        except Exception:
            pass

        config = types.GenerateContentConfig(
            system_instruction=system_prompt if system_prompt else None,
            temperature=0.7,
            thinking_config=thinking_cfg,
        )

        response = client.models.generate_content_stream(
            model=model or "gemini-3.8-flash",
            contents=formatted_contents,
            config=config,
        )

        full_text = ""
        for chunk in response:
            if self._stop_requested:
                break
            if chunk.text:
                full_text += chunk.text
                accumulated_callback(full_text)
                on_chunk(chunk.text)

    def _stream_openai_compatible(self, api_key: str, base_url: Optional[str], model: str, system_prompt: str, messages: List[Dict[str, str]], on_chunk: Callable[[str], None], accumulated_callback):
        from openai import OpenAI

        cache_key = (api_key, base_url)
        if cache_key not in self._openai_clients:
            self._openai_clients[cache_key] = OpenAI(
                api_key=api_key,
                base_url=base_url if base_url else None
            )

        client = self._openai_clients[cache_key]

        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            payload_messages.append({"role": msg["role"], "content": msg["content"]})

        stream = client.chat.completions.create(
            model=model,
            messages=payload_messages,
            stream=True,
            temperature=0.7,
        )

        full_text = ""
        for chunk in stream:
            if self._stop_requested:
                break
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    full_text += delta
                    accumulated_callback(full_text)
                    on_chunk(delta)
