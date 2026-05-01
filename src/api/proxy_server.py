"""
FastAPI WebSocket Proxy for Qwen-Omni-Realtime API

Architecture:
    Browser (no auth) --> local WS proxy --> DashScope WS (with Authorization header)

Features:
    - Browser connects to local WebSocket without custom headers
    - Proxy adds Authorization header to DashScope connection
    - Real-time audio streaming (16kHz/16bit/mono PCM)
    - Error handling and reconnection
    - Text-only mode for thinking tree use case
"""
import os
import json
import base64
import asyncio
import time
import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
MODEL = os.getenv("QWEN_MODEL", "qwen3.5-omni-flash-realtime")

# Voice defaults per model series
VOICE_MAP = {
    "qwen3.5-omni": "Tina",
    "qwen3-omni": "Cherry",
    "qwen-omni-turbo": "Chelsie",
}
DEFAULT_VOICE = "Cherry"
for prefix, voice in VOICE_MAP.items():
    if MODEL.startswith(prefix):
        DEFAULT_VOICE = voice
        break
REGION = os.getenv("QWEN_REGION", "cn")
BASE_DOMAIN = "dashscope.aliyuncs.com" if REGION == "cn" else "dashscope-intl.aliyuncs.com"
DASHSCOPE_WS_URL = f"wss://{BASE_DOMAIN}/api-ws/v1/realtime?model={MODEL}"

AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
AUDIO_BIT_DEPTH = int(os.getenv("AUDIO_BIT_DEPTH", "16"))
AUDIO_CHANNELS = int(os.getenv("AUDIO_CHANNELS", "1"))
AUDIO_CHUNK_SIZE = int(os.getenv("AUDIO_CHUNK_SIZE", "3200"))  # 100ms at 16kHz/16bit/mono

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("qwen-proxy")

# Event ID counter
_event_counter = 0

def next_event_id() -> str:
    global _event_counter
    _event_counter += 1
    return f"evt_{int(time.time()*1000)}_{_event_counter}"


# ---------------------------------------------------------------------------
# Session state for proxy connections
# ---------------------------------------------------------------------------
class ProxySession:
    """Manages one browser-to-DashScope proxy session."""

    def __init__(self, browser_ws: WebSocket):
        self.browser_ws = browser_ws
        self.dashscope_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None
        self.is_connected = False
        self.created_at = datetime.now().isoformat()
        self.audio_bytes_sent = 0
        self.audio_bytes_received = 0
        self.event_count = 0
        self.last_activity = time.time()
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def connect_to_dashscope(self) -> bool:
        """Establish WebSocket connection to DashScope with Authorization."""
        try:
            headers = {"Authorization": f"Bearer {API_KEY}"}
            self.dashscope_ws = await websockets.connect(
                DASHSCOPE_WS_URL,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
            )
            self.is_connected = True
            logger.info(f"[{self.session_id}] Connected to DashScope: {DASHSCOPE_WS_URL}")
            return True
        except Exception as e:
            logger.error(f"[{self.session_id}] DashScope connection failed: {e}")
            self.is_connected = False
            return False

    async def configure_session(self, instructions: str = None, modalities: list = None, **kwargs):
        """Send session.update to DashScope with model configuration."""
        if modalities is None:
            modalities = ["text"]  # Text-only for thinking tree

        session_config = {
            "modalities": modalities,
            "input_audio_format": "pcm",
            "output_audio_format": "pcm",
            "turn_detection": None,  # Manual mode
            "temperature": kwargs.get("temperature", 0.7),
        }

        if instructions:
            session_config["instructions"] = instructions

        # Add voice if audio output is requested
        if "audio" in modalities:
            session_config["voice"] = kwargs.get("voice", DEFAULT_VOICE)

        event = {
            "event_id": next_event_id(),
            "type": "session.update",
            "session": session_config,
        }

        await self.dashscope_ws.send(json.dumps(event))
        logger.info(f"[{self.session_id}] session.update sent: modalities={modalities}")

    async def send_audio(self, audio_data: bytes):
        """Send audio chunk to DashScope (base64-encoded PCM)."""
        audio_b64 = base64.b64encode(audio_data).decode("ascii")
        event = {
            "event_id": next_event_id(),
            "type": "input_audio_buffer.append",
            "audio": audio_b64,
        }
        await self.dashscope_ws.send(json.dumps(event))
        self.audio_bytes_sent += len(audio_data)
        self.event_count += 1

    async def commit_audio(self):
        """Commit audio buffer and request response."""
        commit_event = {
            "event_id": next_event_id(),
            "type": "input_audio_buffer.commit",
        }
        await self.dashscope_ws.send(json.dumps(commit_event))

        response_event = {
            "event_id": next_event_id(),
            "type": "response.create",
        }
        await self.dashscope_ws.send(json.dumps(response_event))
        logger.info(f"[{self.session_id}] Audio committed, response requested")

    async def cancel_response(self):
        """Cancel an in-progress response."""
        event = {
            "event_id": next_event_id(),
            "type": "response.cancel",
        }
        await self.dashscope_ws.send(json.dumps(event))

    async def close(self):
        """Clean up the session."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self.dashscope_ws:
            try:
                await self.dashscope_ws.close()
            except Exception:
                pass
            self.is_connected = False
        logger.info(f"[{self.session_id}] Session closed. Audio sent: {self.audio_bytes_sent}B")


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("Qwen WebSocket Proxy starting...")
    logger.info(f"Model: {MODEL}")
    logger.info(f"DashScope: {DASHSCOPE_WS_URL}")
    logger.info(f"API Key: {'configured' if API_KEY else 'MISSING!'}")
    logger.info("=" * 50)
    yield
    logger.info("Proxy shutting down...")


app = FastAPI(title="Qwen-Omni WebSocket Proxy", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "model": MODEL,
        "api_configured": bool(API_KEY),
        "dashscope_url": DASHSCOPE_WS_URL,
    }


@app.get("/api/status")
async def api_status():
    """Detailed API status."""
    return {
        "provider": "qwen",
        "model": MODEL,
        "region": REGION,
        "endpoint": DASHSCOPE_WS_URL,
        "api_key_configured": bool(API_KEY),
        "audio_config": {
            "sample_rate": AUDIO_SAMPLE_RATE,
            "bit_depth": AUDIO_BIT_DEPTH,
            "channels": AUDIO_CHANNELS,
            "chunk_size": AUDIO_CHUNK_SIZE,
        },
    }


# ---------------------------------------------------------------------------
# WebSocket Endpoint
# ---------------------------------------------------------------------------
@app.websocket("/ws")
async def websocket_proxy(browser_ws: WebSocket):
    """
    Main WebSocket proxy endpoint.
    
    Browser connects here without auth. Proxy forwards to DashScope with auth.
    
    Protocol Messages (Browser <-> Proxy):
      {"type": "configure", "instructions": "...", "modalities": ["text"]}
      {"type": "audio", "data": "<base64-pcm>"}
      {"type": "commit"}
      {"type": "cancel"}
      {"type": "close"}
      
    Protocol Messages (Proxy -> Browser):
      {"type": "connected", "session_id": "..."}
      {"type": "event", "dashscope_event": {...}}
      {"type": "transcription", "text": "..."}
      {"type": "response_done", "usage": {...}}
      {"type": "error", "message": "...", "code": "..."}
    """
    await browser_ws.accept()
    session = ProxySession(browser_ws)
    session._running = True

    try:
        # Step 1: Connect to DashScope
        logger.info("New browser connection, connecting to DashScope...")
        if not await session.connect_to_dashscope():
            await browser_ws.send_json({
                "type": "error",
                "code": "DASHSCOPE_CONNECTION_FAILED",
                "message": "Cannot connect to Qwen API. Check API key and network.",
            })
            return

        # Step 2: Wait for session.created from DashScope
        try:
            raw = await asyncio.wait_for(session.dashscope_ws.recv(), timeout=10.0)
            event = json.loads(raw)
            if event.get("type") == "session.created":
                session.session_id = event.get("session", {}).get("id", "unknown")
                session.event_count += 1
                logger.info(f"Session created: {session.session_id}")
                await browser_ws.send_json({
                    "type": "connected",
                    "session_id": session.session_id,
                    "model": MODEL,
                })
        except asyncio.TimeoutError:
            await browser_ws.send_json({
                "type": "error",
                "code": "SESSION_TIMEOUT",
                "message": "No session.created event from DashScope within 10s",
            })
            return

        # Step 3: Start bidirectional relay
        # Task: DashScope -> Browser (server events)
        async def relay_dashscope_to_browser():
            try:
                while session._running and session.is_connected:
                    try:
                        raw = await asyncio.wait_for(
                            session.dashscope_ws.recv(), timeout=30.0
                        )
                        event = json.loads(raw)
                        session.event_count += 1
                        session.last_activity = time.time()
                        event_type = event.get("type", "unknown")

                        # Forward full event to browser
                        await browser_ws.send_json({
                            "type": "event",
                            "dashscope_event": event,
                        })

                        # Also send simplified messages for specific events
                        if event_type == "response.audio_transcript.done":
                            transcript = event.get("transcript", "")
                            logger.info(f"[{session.session_id}] Transcript: {transcript[:100]}")
                            await browser_ws.send_json({
                                "type": "transcription",
                                "text": transcript,
                                "final": True,
                            })
                        elif event_type == "response.audio_transcript.delta":
                            await browser_ws.send_json({
                                "type": "transcription",
                                "text": event.get("delta", ""),
                                "final": False,
                            })
                        elif event_type == "response.done":
                            usage = event.get("response", {}).get("usage", {})
                            logger.info(f"[{session.session_id}] Response done. Usage: {usage}")
                            await browser_ws.send_json({
                                "type": "response_done",
                                "usage": usage,
                            })
                        elif event_type == "error":
                            error_msg = event.get("error", {}).get("message", str(event))
                            logger.error(f"[{session.session_id}] DashScope error: {error_msg}")
                            await browser_ws.send_json({
                                "type": "error",
                                "code": "DASHSCOPE_ERROR",
                                "message": error_msg,
                                "dashscope_event": event,
                            })

                    except asyncio.TimeoutError:
                        continue
                    except ConnectionClosed as e:
                        logger.info(f"[{session.session_id}] DashScope connection closed: code={e.code}")
                        await browser_ws.send_json({
                            "type": "disconnected",
                            "code": e.code,
                            "reason": str(e.reason),
                        })
                        session.is_connected = False
                        break
                    except Exception as e:
                        logger.error(f"[{session.session_id}] Relay error: {e}")
                        break
            except Exception as e:
                logger.error(f"[{session.session_id}] Relay task crashed: {e}")

        # Task: Browser -> DashScope (client commands)
        async def relay_browser_to_dashscope():
            try:
                while session._running and session.is_connected:
                    try:
                        msg = await asyncio.wait_for(
                            browser_ws.receive_text(), timeout=30.0
                        )
                        session.last_activity = time.time()
                        data = json.loads(msg)
                        cmd_type = data.get("type", "")

                        if cmd_type == "configure":
                            instructions = data.get("instructions", "")
                            modalities = data.get("modalities", ["text"])
                            voice = data.get("voice", DEFAULT_VOICE)
                            await session.configure_session(
                                instructions=instructions,
                                modalities=modalities,
                                voice=voice,
                            )
                            logger.info(f"[{session.session_id}] Configured: modalities={modalities}")

                        elif cmd_type == "audio":
                            audio_b64 = data.get("data", "")
                            if audio_b64:
                                audio_bytes = base64.b64decode(audio_b64)
                                await session.send_audio(audio_bytes)

                        elif cmd_type == "commit":
                            await session.commit_audio()

                        elif cmd_type == "cancel":
                            await session.cancel_response()

                        elif cmd_type == "close":
                            logger.info(f"[{session.session_id}] Browser requested close")
                            break

                        else:
                            logger.warning(f"[{session.session_id}] Unknown command: {cmd_type}")

                    except asyncio.TimeoutError:
                        continue
                    except WebSocketDisconnect:
                        logger.info(f"[{session.session_id}] Browser disconnected")
                        break
                    except json.JSONDecodeError:
                        await browser_ws.send_json({
                            "type": "error",
                            "code": "INVALID_JSON",
                            "message": "Invalid JSON message from browser",
                        })
                    except Exception as e:
                        logger.error(f"[{session.session_id}] Browser relay error: {e}")
                        traceback.print_exc()
                        break
            except Exception as e:
                logger.error(f"[{session.session_id}] Browser relay task crashed: {e}")

        # Run both relay directions concurrently
        dash_to_browser_task = asyncio.create_task(relay_dashscope_to_browser())
        browser_to_dash_task = asyncio.create_task(relay_browser_to_dashscope())
        session._tasks = [dash_to_browser_task, browser_to_dash_task]

        # Wait for either task to complete
        done, pending = await asyncio.wait(
            [dash_to_browser_task, browser_to_dash_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()

        # Check for exceptions
        for task in done:
            try:
                await task
            except Exception as e:
                logger.error(f"Task exception: {e}")

    except WebSocketDisconnect:
        logger.info(f"[{session.session_id}] Browser WebSocket disconnected")
    except Exception as e:
        logger.error(f"[{session.session_id}] Fatal error: {e}")
        traceback.print_exc()
        try:
            await browser_ws.send_json({
                "type": "error",
                "code": "INTERNAL_ERROR",
                "message": str(e),
            })
        except Exception:
            pass
    finally:
        await session.close()


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8765"))
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
