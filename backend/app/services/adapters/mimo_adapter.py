"""MiMo adapter via REST API.

Integrates with the MiMo API for speech-to-text and semantic analysis
of children's speech. Uses standard REST/HTTP protocol with JSON payloads.
"""
from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any, Optional

import httpx

from app.config import settings
from app.services.ai_adapter import (
    AIModelAdapter,
    AnalyzeSpeechInput,
    AnalyzeSpeechOutput,
    ProviderType,
)

logger = logging.getLogger(__name__)

# Default instructions for children's thinking tree analysis
_DEFAULT_INSTRUCTIONS = (
    "你是一个儿童思维树系统的AI助手。请分析孩子的语音输入，识别孩子的思考模式，"
    "并用鼓励性的语言给予反馈。请用JSON格式输出，包含以下字段："
    'transcription（语音转文字）、thinking_type（思考类型）、'
    'key_concepts（关键概念列表）、suggestions（后续引导建议列表）。'
    "请使用适合儿童的语言风格，保持积极正面的语调。"
)


def _parse_mimo_response(response_data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Parse MiMo API response into structured analysis.

    Args:
        response_data: Raw response from MiMo API.

    Returns:
        Tuple of (analysis dict, suggestions list).
    """
    analysis: dict[str, Any] = {
        "raw_response": "",
        "thinking_type": "unknown",
        "key_concepts": [],
        "emotion": "neutral",
    }
    suggestions: list[str] = []

    # Extract content from MiMo response format
    choices = response_data.get("choices", [])
    if choices:
        message = choices[0].get("message", {})
        content = message.get("content", "")
        analysis["raw_response"] = content

        # Try to parse structured JSON from content
        try:
            json_start = content.find("{")
            json_end = content.rfind("}")
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start : json_end + 1]
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    analysis.update(
                        {
                            "transcription": parsed.get("transcription", ""),
                            "thinking_type": parsed.get("thinking_type", "unknown"),
                            "key_concepts": parsed.get("key_concepts", []),
                            "emotion": parsed.get("emotion", "neutral"),
                        }
                    )
                    suggestions = parsed.get("suggestions", [])
        except (json.JSONDecodeError, ValueError):
            if content:
                sentences = content.replace("\n", " ").split("。")
                suggestions = [s.strip() for s in sentences if s.strip()][:5]

    # Include usage info
    usage = response_data.get("usage", {})
    analysis["usage"] = usage

    return analysis, suggestions


class MiMoAdapter(AIModelAdapter):
    """MiMo adapter using REST HTTP API.

    Communicates with the MiMo API via standard HTTP POST requests.
    Supports both audio URL and base64-encoded audio input.
    """

    def __init__(self) -> None:
        """Initialize MiMo adapter with configuration from settings."""
        self._model: str = settings.mimo_model
        self._api_key: str = settings.mimo_api_key
        self._base_url: str = settings.mimo_base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.MIMO

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def supports_streaming(self) -> bool:
        return False

    # ------------------------------------------------------------------
    # Client management
    # ------------------------------------------------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create an HTTP client for MiMo API calls."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=float(settings.ai_timeout_seconds),
                    write=10.0,
                    pool=10.0,
                ),
            )
        return self._client

    # ------------------------------------------------------------------
    # Core analysis method
    # ------------------------------------------------------------------

    async def analyze_speech(self, input_data: AnalyzeSpeechInput) -> AnalyzeSpeechOutput:
        """Analyze child speech audio using MiMo API.

        Sends the audio data (as base64) along with analysis instructions
        to the MiMo REST API and parses the structured response.

        Args:
            input_data: Audio data and analysis parameters.

        Returns:
            Structured analysis with transcription and insights.

        Raises:
            ConnectionError: If MiMo API connection fails.
            TimeoutError: If the request times out.
            ValueError: If input is invalid.
        """
        if not input_data.audio_data:
            raise ValueError("Audio data is empty")

        if not self._api_key:
            raise ConnectionError("MiMo API key not configured")

        start_time = time.monotonic()

        # Build instructions context
        instructions = input_data.instructions or _DEFAULT_INSTRUCTIONS
        if input_data.child_age:
            instructions += f" 孩子年龄：{input_data.child_age}岁。"
        if input_data.context:
            instructions += f" 上下文：{input_data.context}"

        # Encode audio as base64
        audio_b64 = base64.b64encode(input_data.audio_data).decode("ascii")
        audio_mime = "audio/wav"  # MiMo expects WAV format header

        # Build request payload - MiMo audio chat format
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": instructions,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "audio",
                            "audio": audio_b64,
                            "mime_type": audio_mime,
                        },
                        {
                            "type": "text",
                            "text": "请分析这段语音，给出转录文本和分析结果。",
                        },
                    ],
                },
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        try:
            client = await self._get_client()
            response = await client.post("/chat/completions", json=payload)

            if response.status_code == 401:
                raise ConnectionError("MiMo API authentication failed. Check API key.")
            if response.status_code == 429:
                raise RuntimeError("MiMo API rate limit exceeded. Try again later.")
            if response.status_code >= 500:
                raise ConnectionError(
                    f"MiMo API server error: {response.status_code}"
                )

            response.raise_for_status()
            response_data = response.json()

        except httpx.TimeoutException as e:
            raise TimeoutError(f"MiMo API request timed out: {e}") from e
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to MiMo API: {e}") from e
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"MiMo API returned error: {e.response.status_code}") from e

        # Parse results
        elapsed_ms = (time.monotonic() - start_time) * 1000
        analysis, suggestions = _parse_mimo_response(response_data)

        # Calculate confidence from response metadata
        usage = response_data.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)
        confidence = min(0.95, max(0.3, total_tokens / 500.0)) if total_tokens > 0 else 0.5

        return AnalyzeSpeechOutput(
            transcription=analysis.get("transcription", ""),
            analysis=analysis,
            suggestions=suggestions,
            confidence=confidence,
            processing_time_ms=elapsed_ms,
            provider=ProviderType.MIMO.value,
            model=self._model,
        )

    async def health_check(self) -> bool:
        """Verify MiMo API connectivity and API key validity."""
        if not self._api_key:
            logger.warning("MiMo health check: API key not configured")
            return False

        try:
            client = await self._get_client()
            # Use a lightweight health check: list models or a simple status endpoint
            response = await client.get("/models", timeout=10.0)
            return response.status_code < 500
        except Exception as e:
            logger.warning("MiMo health check failed: %s", e)
            return False

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
