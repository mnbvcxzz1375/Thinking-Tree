"""Unified AI model adapter interface with provider pattern.

Defines the abstract base class and shared types for all AI model adapters
(Qwen, MiMo, etc.) used in the children's thinking tree system for speech analysis.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ProviderType(str, Enum):
    """Supported AI model providers."""

    QWEN = "qwen"
    MIMO = "mimo"


@dataclass
class AnalyzeSpeechInput:
    """Input data for speech analysis.

    Attributes:
        audio_data: Raw PCM audio bytes (16kHz, 16bit, mono).
        language: Language code ('zh' or 'en').
        context: Optional conversation/session context.
        child_age: Optional age of the child for age-appropriate responses.
        instructions: Optional custom instructions for the AI model.
    """

    audio_data: bytes
    language: str = "zh"
    context: Optional[str] = None
    child_age: Optional[int] = None
    instructions: Optional[str] = None


@dataclass
class AnalyzeSpeechOutput:
    """Standardized output from speech analysis.

    Attributes:
        transcription: The transcribed text from the audio.
        analysis: Structured analysis of the child's speech (thinking patterns, etc.).
        suggestions: List of follow-up suggestions for the teacher/parent.
        confidence: Confidence score (0.0 to 1.0).
        processing_time_ms: Total processing time in milliseconds.
        provider: Which AI provider was used (qwen/mimo).
        model: The specific model name used.
    """

    transcription: str
    analysis: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    confidence: float = 0.0
    processing_time_ms: float = 0.0
    provider: str = ""
    model: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert output to a serializable dict."""
        return {
            "transcription": self.transcription,
            "analysis": self.analysis,
            "suggestions": self.suggestions,
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
            "provider": self.provider,
            "model": self.model,
        }


class AIModelAdapter(ABC):
    """Abstract base class for all AI model adapters.

    Each provider (Qwen, MiMo) implements this interface to provide
    consistent speech analysis capabilities regardless of the underlying
    protocol (WebSocket, REST, etc.).
    """

    @abstractmethod
    async def analyze_speech(self, input_data: AnalyzeSpeechInput) -> AnalyzeSpeechOutput:
        """Analyze child speech audio and return structured results.

        Args:
            input_data: Audio data and analysis parameters.

        Returns:
            Structured analysis output with transcription and insights.

        Raises:
            ConnectionError: If connection to AI provider fails.
            TimeoutError: If the request times out.
            ValueError: If input data is invalid.
            RuntimeError: For other processing errors.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the AI provider is reachable and configured.

        Returns:
            True if the provider is healthy, False otherwise.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Release any resources held by the adapter (connections, sessions)."""
        ...

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the provider type identifier."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the specific model name in use."""
        ...

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Return whether the adapter supports streaming audio."""
        ...


class AdapterRegistry:
    """Registry for managing and selecting AI model adapters."""

    _adapters: dict[ProviderType, type[AIModelAdapter]] = {}

    @classmethod
    def register(cls, provider_type: ProviderType, adapter_cls: type[AIModelAdapter]) -> None:
        """Register an adapter class for a provider type."""
        cls._adapters[provider_type] = adapter_cls

    @classmethod
    def get(cls, provider_type: ProviderType) -> type[AIModelAdapter]:
        """Get an adapter class by provider type.

        Raises:
            KeyError: If no adapter is registered for the provider type.
        """
        if provider_type not in cls._adapters:
            raise KeyError(f"No adapter registered for provider: {provider_type}")
        return cls._adapters[provider_type]

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider types."""
        return [p.value for p in cls._adapters.keys()]

    @classmethod
    def is_registered(cls, provider_type: ProviderType) -> bool:
        """Check if a provider type has a registered adapter."""
        return provider_type in cls._adapters
