"""Quick test for Qwen Realtime API with text-only modality."""
import os
import json
import base64
import asyncio
import websockets
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY")
MODEL = os.getenv("QWEN_MODEL", "qwen3.5-omni-flash-realtime")
REGION = os.getenv("QWEN_REGION", "cn")

BASE_DOMAIN = "dashscope.aliyuncs.com" if REGION == "cn" else "dashscope-intl.aliyuncs.com"
WS_URL = f"wss://{BASE_DOMAIN}/api-ws/v1/realtime?model={MODEL}"

def generate_silent_pcm(duration_ms=500, sample_rate=16000, channels=1, bit_depth=16):
    """Generate silent PCM audio for testing."""
    sample_width = bit_depth // 8
    num_samples = int(sample_rate * duration_ms / 1000)
    return b'\x00' * (num_samples * channels * sample_width)


async def test_realtime():
    """Test Qwen Realtime API with text-only output."""
    print("=" * 60)
    print("QWEN REALTIME API FIX VERIFICATION")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"URL: {WS_URL}")
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        async with websockets.connect(WS_URL, additional_headers=headers, ping_interval=30, ping_timeout=10) as ws:
            print("\n[1] WebSocket connected")
            
            # Wait for session.created
            raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
            event = json.loads(raw)
            if event.get("type") == "session.created":
                session_id = event.get("session", {}).get("id", "unknown")
                print(f"[2] session.created received (id={session_id})")
            else:
                print(f"[2] Unexpected event: {event.get('type')}")
                return
            
            # Send session.update with text-only modality (FIXED)
            session_update = {
                "type": "session.update",
                "session": {
                    "modalities": ["text"],
                    "input_audio_format": "pcm",
                    "output_audio_format": "pcm",
                    "turn_detection": None,
                    "instructions": "你是谨慎的儿童思维树整理助手。听不清时要返回空转写和 low confidence，不要臆测。只输出 JSON。",
                }
            }
            await ws.send(json.dumps(session_update))
            print("[3] session.update sent (text-only, no voice)")
            
            # Wait for session.updated
            raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
            event = json.loads(raw)
            if event.get("type") == "session.updated":
                print("[4] session.updated received - SUCCESS!")
            elif event.get("type") == "error":
                error = event.get("error", {})
                print(f"[4] ERROR: {error.get('code')} - {error.get('message')}")
                return
            else:
                print(f"[4] Unexpected event: {event.get('type')}")
                return
            
            # Send test audio
            silent_audio = generate_silent_pcm(duration_ms=500)
            audio_b64 = base64.b64encode(silent_audio).decode("ascii")
            
            await ws.send(json.dumps({
                "type": "input_audio_buffer.append",
                "audio": audio_b64,
            }))
            print(f"[5] Audio sent ({len(silent_audio)} bytes)")
            
            # Commit and request response
            await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
            await ws.send(json.dumps({
                "type": "response.create",
                "response": {
                    "modalities": ["text"],
                    "instructions": "请分析这段音频，返回JSON：{\"rough_transcript\": \"转写\", \"leaf_text\": \"叶子文本\", \"confidence\": \"low\"}"
                }
            }))
            print("[6] Audio committed, response requested")
            
            # Wait for response
            print("[7] Waiting for response...")
            response_text = ""
            start = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start < 15:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    event = json.loads(raw)
                    event_type = event.get("type")
                    
                    if event_type == "response.text.delta":
                        response_text += event.get("delta", "")
                    elif event_type == "response.done":
                        print(f"[8] response.done received!")
                        print(f"    Response: {response_text[:200]}")
                        print("\n" + "=" * 60)
                        print("TEST PASSED - Realtime API working correctly!")
                        print("=" * 60)
                        return
                    elif event_type == "error":
                        error = event.get("error", {})
                        print(f"[8] ERROR: {error.get('code')} - {error.get('message')}")
                        print("\n" + "=" * 60)
                        print("TEST FAILED")
                        print("=" * 60)
                        return
                except asyncio.TimeoutError:
                    continue
            
            print("[8] Timeout waiting for response")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\n" + "=" * 60)
        print("TEST FAILED")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_realtime())
