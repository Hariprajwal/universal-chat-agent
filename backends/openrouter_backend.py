"""
backends/openrouter_backend.py
OpenRouter API backend with auto vision-model selection.
Supports streaming responses.
"""

import os
import json
import requests
from dotenv import load_dotenv
from backends.base import BaseBackend

load_dotenv()

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Priority order of vision models to try
VISION_MODEL_PRIORITY = [
    "google/gemini-2.0-flash-001",
    "google/gemini-flash-1.5",
    "openai/gpt-4o-mini",
    "anthropic/claude-3-haiku",
    "meta-llama/llama-3.2-11b-vision-instruct",
    "microsoft/phi-3.5-vision-instruct",
]


class OpenRouterBackend(BaseBackend):
    """
    OpenRouter API backend.
    Auto-selects best available vision model from priority list.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self._model_override = os.getenv("OPENROUTER_MODEL", "auto")
        self._selected_model: str | None = None
        self._available_models: list[str] = []

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://screen-agent.local",
            "X-Title": "Chat Agent",
        }

    def _resolve_model(self) -> str:
        """Resolve which model to use — respects override or auto-selects."""
        if self._model_override and self._model_override != "auto":
            return self._model_override

        if self._selected_model:
            return self._selected_model

        # Try to auto-select from priority list
        for model in VISION_MODEL_PRIORITY:
            if self._test_model(model):
                self._selected_model = model
                print(f"[OpenRouter] Auto-selected model: {model}")
                return model

        # Fallback to first in list
        self._selected_model = VISION_MODEL_PRIORITY[0]
        return self._selected_model

    def _test_model(self, model_id: str) -> bool:
        """Quick check if model exists in OpenRouter's available list."""
        try:
            resp = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers=self._get_headers(),
                timeout=5
            )
            if resp.status_code == 200:
                models_data = resp.json().get("data", [])
                available_ids = {m["id"] for m in models_data}
                return model_id in available_ids
        except Exception:
            pass
        return False

    def fetch_available_models(self) -> list[dict]:
        """Fetch and return all available models from OpenRouter."""
        try:
            resp = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers=self._get_headers(),
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json().get("data", [])
        except Exception as e:
            print(f"[OpenRouter] Failed to fetch models: {e}")
        return []

    def analyze(self, messages: list[dict]) -> str:
        """Send messages to OpenRouter, return full response text."""
        model = self._resolve_model()

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.2,
        }

        try:
            resp = requests.post(
                OPENROUTER_API_URL,
                headers=self._get_headers(),
                json=payload,
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as e:
            # Try fallback model
            if self._selected_model:
                self._selected_model = None  # Reset to trigger re-selection
            raise RuntimeError(f"OpenRouter API error: {e}\n{resp.text}")
        except Exception as e:
            raise RuntimeError(f"OpenRouter request failed: {e}")

    def stream_analyze(self, messages: list[dict], on_chunk: callable = None) -> str:
        """Stream response chunks in real-time."""
        model = self._resolve_model()

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.2,
            "stream": True,
        }

        full_response = ""
        try:
            with requests.post(
                OPENROUTER_API_URL,
                headers=self._get_headers(),
                json=payload,
                stream=True,
                timeout=90
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    line_text = line.decode("utf-8")
                    if line_text.startswith("data: "):
                        chunk_data = line_text[6:]
                        if chunk_data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(chunk_data)
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_response += content
                                if on_chunk:
                                    on_chunk(content)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            raise RuntimeError(f"OpenRouter streaming failed: {e}")

        return full_response

    def is_available(self) -> bool:
        """Check if API key is set and OpenRouter is reachable."""
        if not self.api_key:
            return False
        try:
            resp = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers=self._get_headers(),
                timeout=5
            )
            return resp.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> dict:
        model = self._resolve_model()
        return {
            "backend": "OpenRouter",
            "model": model,
            "type": "cloud",
            "vision": True,
        }


if __name__ == "__main__":
    backend = OpenRouterBackend()
    print("Available:", backend.is_available())
    print("Model info:", backend.get_model_info())

    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in one sentence."}
    ]
    response = backend.analyze(test_messages)
    print("Response:", response)
