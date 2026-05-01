"""
WebSocket proxy for Qwen real-time audio streaming.
Handles browser WebSocket connections and proxies to DashScope API.
"""
import asyncio
import base64
import io
import json
import logging
import websockets
import wave
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

QWEN_AUDIO_CHUNK_CHARS = 64_000


class SpeechAnalyzeRequest(BaseModel):
    """Request body for non-streaming speech analysis."""

    audio_base64: str = Field(..., min_length=1)
    provider: str = "qwen"
    activity_context: dict | None = None
    sample_rate: int = 16000
    channels: int = 1
    bit_depth: int = 16


def _pcm16_base64_to_wav_data_url(audio_base64: str, sample_rate: int, channels: int) -> str:
    """Wrap browser PCM16 recording data in a WAV container for DashScope."""
    raw_base64 = audio_base64.split(",", 1)[1] if "," in audio_base64 else audio_base64
    try:
        pcm_bytes = base64.b64decode(raw_base64, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="录音数据格式无效，请重新录音。") from exc

    if not pcm_bytes:
        raise HTTPException(status_code=422, detail="没有收到录音数据，请重新录音。")

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)

    wav_base64 = base64.b64encode(wav_buffer.getvalue()).decode("ascii")
    return f"data:audio/wav;base64,{wav_base64}"


def _normalize_audio_base64(audio_base64: str) -> str:
    return audio_base64.split(",", 1)[1] if "," in audio_base64 else audio_base64


def _iter_base64_chunks(audio_base64: str, chunk_chars: int = QWEN_AUDIO_CHUNK_CHARS):
    chunk_chars = max(4, chunk_chars - (chunk_chars % 4))
    for start in range(0, len(audio_base64), chunk_chars):
        yield audio_base64[start:start + chunk_chars]


async def _send_audio_append_chunks(ws, audio_base64: str) -> None:
    raw_audio = _normalize_audio_base64(audio_base64)
    for chunk in _iter_base64_chunks(raw_audio):
        await ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": chunk,
        }))


def _compact_tree_context(activity_context: dict | None) -> str:
    """Create a short, model-readable summary of the current thinking tree."""
    if not activity_context:
        return "当前没有可用的思维树上下文。"

    theme = activity_context.get("theme") or "未命名主题"
    description = activity_context.get("description") or ""
    instructions = activity_context.get("instructions") or ""
    total_nodes = activity_context.get("total_nodes", 0)
    directions = activity_context.get("directions") or []

    lines = [
        f"主题：{theme}",
        f"说明：{description}" if description else "",
        f"活动指导：{instructions}" if instructions else "",
        f"当前节点数：{total_nodes}",
        "完整树结构（id: label [类型]）：",
    ]

    # 限制最大节点数避免 prompt 过长
    max_nodes = 50
    node_count = 0

    def format_node(node: dict, depth: int = 0) -> None:
        nonlocal node_count
        if node_count >= max_nodes:
            if depth <= 1:
                lines.append(f"{'  ' * depth}... 省略其余节点")
            return
        
        node_count += 1
        node_id = node.get("id")
        label = node.get("label") or node.get("content") or node_id
        node_type = node.get("nodeType", "")
        metadata = node.get("metadata") or {}
        
        # 添加类型标签帮助 AI 理解节点层级
        type_tag = ""
        if node_type == "direction":
            type_tag = " [方向]"
        elif node_type in ("answer", "insight"):
            type_tag = " [叶子]"
        if metadata.get("debateLabel"):
            stance_label = metadata.get("debateStanceLabel")
            type_tag += f" [{metadata.get('debateLabel')}: {stance_label}]" if stance_label else f" [{metadata.get('debateLabel')}]"
        elif metadata.get("debateRole") == "pro":
            type_tag += " [正方]"
        elif metadata.get("debateRole") == "con":
            type_tag += " [反方]"
        
        indent = "  " * depth
        lines.append(f"{indent}- {node_id}: {label}{type_tag}")
        
        for child in node.get("children") or []:
            format_node(child, depth + 1)

    for direction in directions:
        format_node(direction, 0)

    return "\n".join([line for line in lines if line])


def _extract_message_text(result: dict) -> str:
    """Extract assistant text from DashScope multimodal response shapes."""
    choices = result.get("output", {}).get("choices", [])
    if not choices:
        return ""

    content = choices[0].get("message", {}).get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts).strip()
    return ""


def _parse_analysis_json(content: str) -> dict:
    """Parse JSON from model text, including fenced JSON blocks."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"AI返回内容不是有效JSON：{content[:120]}") from exc

    transcript = str(parsed.get("rough_transcript") or "").strip()
    leaf_text = str(parsed.get("leaf_text") or "").strip()
    if not transcript and not leaf_text:
        raise HTTPException(status_code=422, detail="AI没有听清录音内容，请靠近麦克风重新录一次。")

    return {
        "rough_transcript": transcript,
        "leaf_text": leaf_text or transcript[:12],
        "follow_up_question": str(parsed.get("follow_up_question") or "你能再说详细一点吗？").strip(),
        "confidence": str(parsed.get("confidence") or "medium").strip(),
        "recommended_parent_id": parsed.get("recommended_parent_id"),
        "recommended_parent_label": parsed.get("recommended_parent_label"),
        "similar_node_ids": parsed.get("similar_node_ids") or [],
        "classification_reason": parsed.get("classification_reason"),
    }


def _dashscope_error_detail(result: dict, status_code: int) -> str:
    code = result.get("code") or result.get("error", {}).get("code")
    message = result.get("message") or result.get("error", {}).get("message")
    if code == "Throttling.AllocationQuota":
        return "DashScope 免费额度已用完，请更换 API Key、开通/充值额度，或切换可用语音模型后再录音。"
    if code or message:
        return f"语音模型调用失败：{code or status_code}，{message or '请检查模型权限和 API Key。'}"
    return f"语音模型调用失败：{status_code}"


async def _analyze_with_qwen_realtime(audio_base64: str, prompt: str, api_key: str, model: str) -> dict:
    url = f"{QWEN_REALTIME_URL}?model={model}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    instructions = "你是谨慎的儿童思维树整理助手。听不清时要返回空转写和 low confidence，不要臆测。只输出 JSON。"
    assistant_text_parts: list[str] = []
    input_transcript_parts: list[str] = []

    try:
        async with websockets.connect(url, additional_headers=headers, ping_interval=30, ping_timeout=30) as ws:
            await ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "modalities": ["text"],
                    "input_audio_format": "pcm",
                    "output_audio_format": "pcm",
                    "turn_detection": None,
                    "instructions": instructions,
                }
            }))

            while True:
                event = json.loads(await asyncio.wait_for(ws.recv(), timeout=settings.ai_timeout_seconds))
                event_type = event.get("type")
                if event_type == "session.updated":
                    break
                if event_type == "error":
                    error = event.get("error") or {}
                    raise HTTPException(
                        status_code=502,
                        detail=f"Realtime 会话配置失败：{error.get('code') or 'error'}，{error.get('message') or event}",
                    )

            await _send_audio_append_chunks(ws, audio_base64)
            await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
            await ws.send(json.dumps({
                "type": "response.create",
                "response": {
                    "modalities": ["text"],
                    "instructions": prompt,
                }
            }))

            while True:
                event = json.loads(await asyncio.wait_for(ws.recv(), timeout=settings.ai_timeout_seconds))
                event_type = event.get("type")
                logger.info("DashScope event: %s", event_type)
                if event_type == "response.text.delta":
                    assistant_text_parts.append(event.get("delta", ""))
                elif event_type == "response.audio_transcript.delta":
                    assistant_text_parts.append(event.get("delta", ""))
                elif event_type == "response.audio_transcript.done":
                    transcript = event.get("transcript")
                    if transcript:
                        assistant_text_parts.append(transcript)
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = event.get("transcript")
                    if transcript:
                        input_transcript_parts.append(transcript)
                elif event_type == "response.done":
                    break
                elif event_type == "error":
                    error = event.get("error") or {}
                    raise HTTPException(
                        status_code=502,
                        detail=f"Realtime 语音模型调用失败：{error.get('code') or 'error'}，{error.get('message') or event}",
                    )
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Realtime 语音模型响应超时，请稍后重试。") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Qwen realtime speech analysis failed")
        raise HTTPException(status_code=502, detail=f"Realtime 语音模型连接失败：{exc}") from exc

    content = "".join(assistant_text_parts).strip()
    if not content:
        transcript = " ".join(input_transcript_parts).strip()
        if transcript:
            raise HTTPException(status_code=502, detail=f"模型只完成了转写但未返回分类 JSON：{transcript}")
        raise HTTPException(status_code=422, detail="AI没有返回可识别内容，请重新录音。")
    return _parse_analysis_json(content)

# Qwen Realtime API endpoints
QWEN_REALTIME_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
QWEN_REALTIME_URL_INTL = "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime"


class QwenRealtimeProxy:
    """Proxy between browser WebSocket and Qwen DashScope API."""
    
    def __init__(self, api_key: str, model: str = "qwen3.5-omni-plus-realtime"):
        self.api_key = api_key
        self.model = model
        self.ws_url = QWEN_REALTIME_URL
        
    async def connect(self) -> websockets.WebSocketClientProtocol:
        """Connect to Qwen DashScope API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Connect with model in query params
        url = f"{self.ws_url}?model={self.model}"
        
        try:
            ws = await websockets.connect(
                url,
                additional_headers=headers,
                ping_interval=30,
                ping_timeout=10
            )
            logger.info(f"Connected to Qwen Realtime API: {self.model}")
            return ws
        except Exception as e:
            logger.error(f"Failed to connect to Qwen API: {e}")
            raise
    
    async def send_session_config(self, ws: websockets.WebSocketClientProtocol):
        """Send session configuration to Qwen API."""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "voice": "Chelsie",
                "instructions": """你是一个儿童课堂活动中的思维整理助手。
你的任务不是替儿童生成答案，而是帮助教师理解儿童刚刚说的话。
请用简短文字转写儿童主要表达，保留儿童原意，不能成人化。
叶子文本控制在6-12个中文字符。""",
                "input_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "gummy-realtime-v1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "silence_duration_ms": 900
                }
            }
        }
        await ws.send(json.dumps(config))
        logger.info("Sent session configuration to Qwen API")


@router.websocket("/ws/audio")
async def audio_websocket_proxy(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio streaming.
    
    Browser connects here, and we proxy to Qwen DashScope API.
    """
    await websocket.accept()
    logger.info("Browser WebSocket connected")
    
    # Create Qwen proxy
    proxy = QwenRealtimeProxy(
        api_key=settings.get_qwen_api_key(),
        model=settings.qwen_model or "qwen3.5-omni-plus-realtime"
    )
    
    qwen_ws = None
    
    try:
        # Connect to Qwen API
        qwen_ws = await proxy.connect()
        await proxy.send_session_config(qwen_ws)
        
        # Create tasks for bidirectional proxying
        async def proxy_browser_to_qwen():
            """Forward audio from browser to Qwen API."""
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "input_audio_buffer.append":
                        await _send_audio_append_chunks(qwen_ws, message.get("audio") or "")
                    elif message.get("type") == "input_audio_buffer.commit":
                        # Commit audio and request response
                        await qwen_ws.send(json.dumps(message))
                        await qwen_ws.send(json.dumps({"type": "response.create"}))
                    elif message.get("type") == "session.update":
                        # Update session config
                        await qwen_ws.send(json.dumps(message))
                    else:
                        # Forward other messages as-is
                        await qwen_ws.send(json.dumps(message))
                        
            except WebSocketDisconnect:
                logger.info("Browser disconnected")
            except Exception as e:
                logger.error(f"Error proxying browser->qwen: {e}")
        
        async def proxy_qwen_to_browser():
            """Forward responses from Qwen API to browser."""
            try:
                async for message in qwen_ws:
                    if isinstance(message, str):
                        data = json.loads(message)
                        
                        # Handle different message types
                        if data.get("type") == "response.text.delta":
                            # Text chunk
                            await websocket.send_json({
                                "type": "transcript",
                                "text": data.get("delta", ""),
                                "is_final": False
                            })
                        elif data.get("type") == "response.audio.delta":
                            # Audio response chunk
                            await websocket.send_json({
                                "type": "audio_response",
                                "audio": data.get("delta", "")
                            })
                        elif data.get("type") == "response.done":
                            # Response complete
                            await websocket.send_json({
                                "type": "response_complete",
                                "response": data.get("response", {})
                            })
                        elif data.get("type") == "error":
                            # Error from Qwen
                            logger.error(f"Qwen API error: {data}")
                            await websocket.send_json({
                                "type": "error",
                                "error": data.get("error", {}).get("message", "Unknown error")
                            })
                        else:
                            # Forward other messages
                            await websocket.send_json(data)
                            
            except websockets.exceptions.ConnectionClosed:
                logger.info("Qwen WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error proxying qwen->browser: {e}")
        
        # Run both proxy tasks concurrently
        await asyncio.gather(
            proxy_browser_to_qwen(),
            proxy_qwen_to_browser(),
            return_exceptions=True
        )
        
    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}")
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })
    finally:
        if qwen_ws:
            await qwen_ws.close()
        logger.info("WebSocket proxy closed")


@router.post("/api/speech/analyze")
async def analyze_speech_rest(request: SpeechAnalyzeRequest):
    """
    REST endpoint for analyzing audio (non-streaming).
    
    For real-time streaming, use the WebSocket endpoint instead.
    """
    import httpx
    
    provider = request.provider
    audio_base64 = request.audio_base64
    tree_context = _compact_tree_context(request.activity_context)

    if provider == "qwen":
        api_key = settings.get_qwen_api_key()
        if not api_key:
            raise HTTPException(status_code=500, detail="后端未配置 DashScope API Key。")

        # Use Qwen Audio for batch speech understanding.
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""你是儿童课堂活动中的思维整理助手。

当前思维树进度：
{tree_context}

节点类型说明：[方向]是主分支，[叶子]是具体想法。recommended_parent_id 可以是任意层级节点的 id，不限于一级方向。
如果树结构里出现[正方]、[反方]，这是辩论模式：先判断孩子表达支持哪一方，再在该方下面选择最合适的方向或叶子；不要把正方理由挂到反方下面，也不要把反方理由挂到正方下面。

任务：
1. 转写孩子录音里的主要表达。
2. 生成叶子文本（6-12字）。
3. 选择最合适的挂载位置：
   - 先看所有层级的[叶子]，如果新想法是某个叶子概念的细分或例子，必须挂到那个叶子下面。例如已有“很小”，新录音“叶子很小/树干很小”应挂到“很小”下面。
   - 如果新想法与某个[叶子]节点含义几乎相同或高度相似，recommended_parent_id 返回那个相似节点的父节点，并在 similar_node_ids 中列出相似节点，由老师决定是否仍然加入。
   - 只有找不到合适叶子时，才挂到最相关的[方向]节点下。
4. 只检查 recommended_parent_id 对应父节点下的同层节点是否相似，不要跨层乱报。
5. 给教师一个追问问题。

只返回 JSON：
{{
  "rough_transcript": "转写内容",
  "leaf_text": "叶子文本",
  "recommended_parent_id": "最匹配节点的id",
  "recommended_parent_label": "节点名称",
  "similar_node_ids": ["相似节点id"],
  "classification_reason": "选择原因",
  "follow_up_question": "追问",
  "confidence": "high/medium/low"
}}"""

        if settings.qwen_audio_model.endswith("-realtime"):
            return await _analyze_with_qwen_realtime(
                audio_base64=audio_base64,
                prompt=prompt,
                api_key=api_key,
                model=settings.qwen_audio_model,
            )

        audio_data_url = _pcm16_base64_to_wav_data_url(
            request.audio_base64,
            sample_rate=request.sample_rate,
            channels=request.channels,
        )
        
        payload = {
            "model": settings.qwen_audio_model,
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": [
                            {"text": "你是谨慎的儿童思维树整理助手。听不清时要返回空转写和 low confidence，不要臆测。"}
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "audio": audio_data_url
                            },
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code >= 400:
                try:
                    error_result = response.json()
                except json.JSONDecodeError:
                    error_result = {"message": response.text[:500]}
                logger.warning("DashScope speech analysis failed: %s %s", response.status_code, error_result)
                raise HTTPException(status_code=502, detail=_dashscope_error_detail(error_result, response.status_code))
            result = response.json()
            
            content = _extract_message_text(result)
            if not content:
                logger.warning("DashScope returned empty content: %s", result)
                raise HTTPException(status_code=422, detail="AI没有返回可识别内容，请重新录音。")
            return _parse_analysis_json(content)
    
    elif provider == "mimo":
        # Use MiMo API
        url = "https://api.xiaomimimo.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.mimo_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "mimo-v2.5",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": f"data:audio/wav;base64,{audio_base64}",
                                "format": "wav"
                            }
                        },
                        {
                            "type": "text",
                            "text": "请分析这段儿童录音，返回JSON格式：{\"rough_transcript\": \"转写\", \"leaf_text\": \"叶子文本(6-12字)\", \"follow_up_question\": \"追问\", \"confidence\": \"high/medium/low\"}"
                        }
                    ]
                }
            ]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30)
            result = response.json()
            
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "rough_transcript": content,
                    "leaf_text": content[:12] if len(content) > 12 else content,
                    "follow_up_question": "你能再说详细一点吗？",
                    "confidence": "medium"
                }
    
    return {"error": "Unknown provider"}
