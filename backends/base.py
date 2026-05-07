"""
backends/base.py
Abstract base class for AI backends.
"""

from abc import ABC, abstractmethod


class BaseBackend(ABC):
    """Abstract interface for AI backends (OpenRouter, Ollama, etc.)"""

    @abstractmethod
    def analyze(self, messages: list[dict]) -> str:
        """
        Send messages (with optional screenshot) to the model.
        Returns the full response text.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is reachable and configured."""
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        """Return display info about the current model."""
        pass

    def stream_analyze(self, messages: list[dict], on_chunk: callable = None) -> str:
        """
        Stream response chunks. Default implementation calls analyze() without streaming.
        Override in backends that support streaming.
        """
        response = self.analyze(messages)
        if on_chunk:
            on_chunk(response)
        return response
