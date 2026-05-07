"""
backends/ollama_backend.py
Local Ollama backend for vision + chat models.
Auto-detects best available vision model.
"""

import os
import json
import requests
from dotenv import load_dotenv
from backends.base import BaseBackend

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llava")

# Vision-capable Ollama models in priority order
VISION_MODEL_PRIORITY = [
    "llava",
    "llava:13b",
    "minicpm-v",
    "moondream",
    "bakllava",
    "llava-phi3",
]


class OllamaBackend(BaseBackend):
    """
    Local Ollama backend. Auto-detects available vision models.
    Falls back gracefully if Ollama is not running.
    """

    def __init__(self):
        self.host = OLLAMA_HOST
        self._model_override = os.getenv("OLLAMA_MODEL", "auto")
        self._selected_model: str | None = None

    def _get_running_models(self) -> list[str]:
        """Get list of locally available Ollama models."""
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                return [m["name"] for m in models]
        except Exception:
            pass
        return []

    def _resolve_model(self) -> str:
        """Pick best available vision model."""
        if self._model_override and self._model_override != "auto":
            return self._model_override

        if self._selected_model:
            return self._selected_model

        available = self._get_running_models()
        if not available:
            return DEFAULT_OLLAMA_MODEL

        # Pick from priority list
        for model in VISION_MODEL_PRIORITY:
            for avail in available:
                if model in avail:
                    self._selected_model = avail
                    print(f"[Ollama] Auto-selected: {avail}")
                    return avail

        # Use whatever is available
        self._selected_model = available[0]
        return self._selected_model

    def analyze(self, messages: list[dict]) -> str:
        """Send messages to Ollama, return full response."""
        model = self._resolve_model()

        # Convert OpenAI-style messages to Ollama format
        ollama_messages = self._convert_messages(messages)

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_ctx": 4096,
            }
        }

        try:
            resp = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=120
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "❌ Cannot connect to Ollama.\n"
                "Make sure Ollama is running: run 'ollama serve' in a terminal."
            )
        except Exception as e:
            raise RuntimeError(f"Ollama request failed: {e}")

    def stream_analyze(self, messages: list[dict], on_chunk: callable = None) -> str:
        """Stream response from Ollama."""
        model = self._resolve_model()
        ollama_messages = self._convert_messages(messages)

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": True,
            "options": {"temperature": 0.2}
        }

        full_response = ""
        try:
            with requests.post(
                f"{self.host}/api/chat",
                json=payload,
                stream=True,
                timeout=120
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line.decode("utf-8"))
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            full_response += content
                            if on_chunk:
                                on_chunk(content)
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except requests.exceptions.ConnectionError:
            raise RuntimeError("❌ Ollama not running. Run 'ollama serve' first.")
        except Exception as e:
            raise RuntimeError(f"Ollama streaming failed: {e}")

        return full_response

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """Convert OpenAI-style messages (with image_url) to Ollama format."""
        converted = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if isinstance(content, list):
                # Multi-modal message
                text_parts = []
                images = []
                for part in content:
                    if part["type"] == "text":
                        text_parts.append(part["text"])
                    elif part["type"] == "image_url":
                        url = part["image_url"]["url"]
                        if url.startswith("data:image"):
                            # Extract base64 data
                            b64 = url.split(",", 1)[1]
                            images.append(b64)

                converted.append({
                    "role": role,
                    "content": " ".join(text_parts),
                    "images": images
                })
            else:
                converted.append({"role": role, "content": content})

        return converted

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> dict:
        model = self._resolve_model()
        available = self._get_running_models()
        return {
            "backend": "Ollama (Local)",
            "model": model,
            "type": "local",
            "vision": True,
            "available_models": available,
        }


if __name__ == "__main__":
    backend = OllamaBackend()
    print("Available:", backend.is_available())
    print("Model info:", backend.get_model_info())
