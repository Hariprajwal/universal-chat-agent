"""
backends/manager.py
BackendManager — manages switching between OpenRouter and Ollama backends.
"""

import os
from dotenv import load_dotenv
from backends.base import BaseBackend
from backends.openrouter_backend import OpenRouterBackend
from backends.ollama_backend import OllamaBackend

load_dotenv()


class BackendManager:
    """
    Manages multiple AI backends and allows hot-switching.
    Provides a unified interface for the UI layer.
    """

    def __init__(self):
        self._backends: dict[str, BaseBackend] = {
            "openrouter": OpenRouterBackend(),
            "ollama": OllamaBackend(),
        }

        default = os.getenv("DEFAULT_BACKEND", "openrouter")
        self.current_name: str = default
        self._current: BaseBackend = self._backends[default]

    @property
    def current(self) -> BaseBackend:
        return self._current

    def switch(self, name: str):
        """Switch to a different backend by name."""
        if name not in self._backends:
            raise ValueError(f"Unknown backend: {name}")
        self.current_name = name
        self._current = self._backends[name]
        print(f"[BackendManager] Switched to: {name}")

    def analyze(self, messages: list[dict]) -> str:
        """Run analysis on current backend."""
        return self._current.analyze(messages)

    def stream(self, messages: list[dict], on_chunk: callable) -> str:
        """Stream response from current backend."""
        return self._current.stream_analyze(messages, on_chunk=on_chunk)

    def is_available(self) -> bool:
        return self._current.is_available()

    def get_model_info(self) -> dict:
        return self._current.get_model_info()

    def check_all_backends(self) -> dict[str, bool]:
        """Check availability of all backends."""
        return {
            name: backend.is_available()
            for name, backend in self._backends.items()
        }
