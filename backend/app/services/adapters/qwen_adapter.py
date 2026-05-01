"""Qwen Omni adapter via DashScope WebSocket realtime API.

Establishes a WebSocket connection to DashScope, streams audio data,
and returns structured analysis of children's speech.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from typing import Any, Optional

import websockets
from websockets.exceptions import ConnectionClosed

from app.config import settings
from app.services.ai_adapter import (
    AIModelAdapter,
    AnalyzeSpeechInput,
    AnalyzeSpeechOutput,
    ProviderType,
)

logger = logging.getLogger(__name__)

# Default voice for Qwen Omni models
_VOICE_MAP: dict[str, str] = {
    "qwen3.5-omni": "Tina",
    "qwen3-omni": "Cherry",
    "qwen-omni-turbo": "Chelsie",
}

# Default instructions for children's thinking tree analysis
_DEFAULT_INSTRUCTIONS = (
    "你是一个儿童思维树系统的AI助手。请分析孩子的语音输入，识别孩子的思考模式，"
    "并用鼓励性的语言给予反馈。请用JSON格式输出，包含以下字段："
    'transcription（语音转文字）、thinking_type（思考类型）、'
    'key_concepts（关键概念列表）、suggestions（后续引导建议列表）。'
    "请使用适合儿童的语言风格，保持积极正面的语调。"
)


def _get_default_voice(model: str) -> str:
    """Get default voice based on model prefix."""
    for prefix, voice in _VOICE_MAP.items():
        if model.startswith(prefix):
            return voice
    return "Cherry"


def _parse_analysis_response(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Parse accumulated WebSocket events into structured analysis output.

    Extracts transcription, extracts any structured JSON from the response,
    and organizes into analysis fields.
    """
    transcript = ""
    response_text = ""
    usage: dict[str, Any] = {}

    for event in events:
        event_type = event.get("type", "")

        if event_type == "response.audio_transcript.done":
            transcript = event.get("transcript", "")
        elif event_type == "response.audio_transcript.delta":
            transcript += event.get("delta", "")
        elif event_type == "response.text.delta":
            response_text += event.get("delta", "")
        elif event_type == "response.text.done":
            resp = event.get("response", {})
            outputs = resp.get("output", [])
            for output in outputs:
                content = output.get("content", [])
                for item in content:
                    if item.get("content_type") == "text":
                        text_val = item.get("text", "")
                        if text_val:
                            response_text = text_val
        elif event_type == "response.done":
            usage = event.get("response", {}).get("usage", {})

    # Try to parse structured JSON from response text
    analysis: dict[str, Any] = {
        "raw_response": response_text,
        "thinking_type": "unknown",
        "key_concepts": [],
        "emotion": "neutral",
    }
    suggestions: list[str] = []

    # Attempt to extract JSON block from response
    try:
        # Look for JSON in code blocks or inline
        text = response_text.strip()
        json_start = text.find("{")
        json_end = text.rfind("}")
        if json_start >= 0 and json_end > json_start:
            json_str = text[json_start : json_end + 1]
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                analysis.update(
                    {
                        "thinking_type": parsed.get("thinking_type", "unknown"),
                        "key_concepts": parsed.get("key_concepts", []),
                        "emotion": parsed.get("emotion", "neutral"),
                    }
                )
                suggestions = parsed.get("suggestions", [])
    except (json.JSONDecodeError, ValueError):
        # Fallback: extract suggestions from response text
        if response_text:
            sentences = response_text.replace("\n", " ").split("。")
            suggestions = [s.strip() for s in sentences if s.strip()][:5]

    analysis["usage"] = usage
    return analysis, suggestions


class QwenAdapter(AIModelAdapter):
    """Qwen Omni adapter using DashScope WebSocket realtime API.

    Connects to Alibaba Cloud DashScope for real-time speech-to-text
    and analysis. Uses WebSocket protocol for low-latency audio streaming.
    """

    def __init__(self) -> None:
        """Initialize Qwen adapter with configuration from settings."""
        self._model: str = settings.qwen_model
        self._api_key: str = settings.dashscope_api_key
        self._region: str = settings.qwen_region
        self._voice: str = _get_default_voice(self._model)

        base_domain = (
            "dashscope.aliyuncs.com"
            if self._region == "cn"
            else "dashscope-intl.aliyuncs.com"
        )
        self._ws_url: str = (
            f"wss://{base_domain}/api-ws/v1/realtime?model={self._model}"
        )

        self._ws: Optional[websockets.WebSocketClientProtocol] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.QWEN

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def supports_streaming(self) -> bool:
        return True

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    async def _connect(self) -> None:
        """Establish WebSocket connection to DashScope."""
        try:
            headers = {"Authorization": f"Bearer {self._api_key}"}
            self._ws = await websockets.connect(
                self._ws_url,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
            )
            logger.info("Qwen adapter connected to DashScope: %s", self._ws_url)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to DashScope: {e}") from e

    async def _configure_session(self, instructions: Optional[str] = None) -> None:
        """Send session.update to configure the model session."""
        if self._ws is None:
            raise RuntimeError("Not connected to DashScope")

        session_config: dict[str, Any] = {
            "modalities": ["text"],
            "input_audio_format": "pcm",
            "output_audio_format": "pcm",
            "turn_detection": None,
            "temperature": 0.7,
            "instructions": instructions or _DEFAULT_INSTRUCTIONS,
        }

        event = {
            "event_id": f"evt_config_{int(time.time() * 1000)}",
            "type": "session.update",
            "session": session_config,
        }
        await self._ws.send(json.dumps(event))
        logger.info("Qwen session configured")

    async def _send_audio(self, audio_data: bytes) -> None:
        """Send audio chunk to DashScope as base64-encoded PCM."""
        if self._ws is None:
            raise RuntimeError("Not connected to DashScope")

        audio_b64 = base64.b64encode(audio_data).decode("ascii")
        event = {
            "event_id": f"evt_audio_{int(time.time() * 1000)}",
            "type": "input_audio_buffer.append",
            "audio": audio_b64,
        }
        await self._ws.send(json.dumps(event))

    async def _commit_and_request(self) -> None:
        """Commit audio buffer and request AI response."""
        if self._ws is None:
            raise RuntimeError("Not connected to DashScope")

        await self._ws.send(
            json.dumps(
                {
                    "event_id": f"evt_commit_{int(time.time() * 1000)}",
                    "type": "input_audio_buffer.commit",
                }
            )
        )
        await self._ws.send(
            json.dumps(
                {
                    "event_id": f"evt_resp_{int(time.time() * 1000)}",
                    "type": "response.create",
                }
            )
        )
        logger.info("Audio committed, response requested")

    async def _collect_events(self, timeout: float = 30.0) -> list[dict[str, Any]]:
        """Collect response events from DashScope until response.done."""
        if self._ws is None:
            raise RuntimeError("Not connected to DashScope")

        events: list[dict[str, Any]] = []
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            try:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Timeout waiting for response.done event")

                raw = await asyncio.wait_for(self._ws.recv(), timeout=min(remaining, 10.0))
                event = json.loads(raw)
                events.append(event)

                event_type = event.get("type", "")
                if event_type == "response.done":
                    break
                elif event_type == "error":
                    error_info = event.get("error", {})
                    raise RuntimeError(
                        f"DashScope error: {error_info.get('message', str(event))}"
                    )

            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for DashScope event")
                break
            except ConnectionClosed as e:
                raise ConnectionError(f"DashScope connection closed: {e.code}") from e

        return events

    # ------------------------------------------------------------------
    # Core analysis method
    # ------------------------------------------------------------------

    async def analyze_speech(self, input_data: AnalyzeSpeechInput) -> AnalyzeSpeechOutput:
        """Analyze child speech audio using Qwen Omni.

        Establishes a fresh WebSocket connection, streams audio,
        and collects the AI analysis response.

        Args:
            input_data: Audio data and analysis parameters.

        Returns:
            Structured analysis with transcription and insights.

        Raises:
            ConnectionError: If DashScope connection fails.
            TimeoutError: If the analysis times out.
            ValueError: If input is invalid.
        """
        if not input_data.audio_data:
            raise ValueError("Audio data is empty")

        if not self._api_key:
            raise ConnectionError("Qwen API key not configured")

        start_time = time.monotonic()
        events: list[dict[str, Any]] = []

        try:
            # Phase 1: Connect and configure
            await self._connect()
            await self._configure_session(instructions=input_data.instructions)

            # Phase 2: Receive session.created confirmation
            raw = await asyncio.wait_for(
                self._ws.recv(), timeout=10.0  # type: ignore[union-attr]
            )
            confirm = json.loads(raw)
            if confirm.get("type") == "error":
                error_info = confirm.get("error", {})
                raise ConnectionError(
                    f"Session creation failed: {error_info.get('message', str(confirm))}"
                )

            # Phase 3: Send audio data
            await self._send_audio(input_data.audio_data)
            await self._commit_and_request()

            # Phase 4: Collect response events
            events = await self._collect_events(timeout=settings.ai_timeout_seconds)

        except TimeoutError:
            raise
        except ConnectionError:
            raise
        except ValueError:
            raise
        except Exception as e:
            if isinstance(e, (ConnectionError, TimeoutError, ValueError)):
                raise
            raise RuntimeError(f"Qwen analysis failed: {e}") from e
        finally:
            await self.close()

        # Phase 5: Parse results
        elapsed_ms = (time.monotonic() - start_time) * 1000
        analysis, suggestions = _parse_analysis_response(events)

        # Determine confidence from usage or event count
        confidence = min(0.95, max(0.5, len(events) / 20.0))

        return AnalyzeSpeechOutput(
            transcription=analysis.get("transcription", ""),
            analysis=analysis,
            suggestions=suggestions,
            confidence=confidence,
            processing_time_ms=elapsed_ms,
            provider=ProviderType.QWEN.value,
            model=self._model,
        )

    async def health_check(self) -> bool:
        """Verify Qwen/DashScope connectivity and API key validity."""
        if not self._api_key:
            logger.warning("Qwen health check: API key not configured")
            return False

        try:
            await self._connect()
            await self._ws.send(  # type: ignore[union-attr]
                json.dumps(
                    {
                        "event_id": f"evt_health_{int(time.time() * 1000)}",
                        "type": "session.update",
                        "session": {
                            "modalities": ["text"],
                            "instructions": "Health check - please respond 'OK'.",
                        },
                    }
                )
            )
            raw = await asyncio.wait_for(
                self._ws.recv(), timeout=10.0  # type: ignore[union-attr]
            )
            event = json.loads(raw)
            return event.get("type") == "session.created"
        except Exception as e:
            logger.warning("Qwen health check failed: %s", e)
            return False
        finally:
            await self.close()

    async def close(self) -> None:
        """Close the WebSocket connection and release resources."""
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None
