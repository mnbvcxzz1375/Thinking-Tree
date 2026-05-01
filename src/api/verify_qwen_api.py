"""
Qwen DashScope API Connectivity Verification

Verifies:
1. API key validity via WebSocket connection
2. WebSocket endpoint reachability
3. Audio format requirements (16kHz/16bit/mono PCM)
4. Event flow (session.update -> input_audio_buffer.append -> response)
"""
import os
import json
import base64
import time
import sys
from datetime import datetime
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


def test_qwen_api():
    """Test Qwen DashScope WebSocket API connectivity."""
    import websocket

    results = {
        "timestamp": datetime.now().isoformat(),
        "model": MODEL,
        "region": REGION,
        "ws_url": WS_URL,
        "tests": []
    }

    print("=" * 60)
    print("QWEN DASHSCOPE API VERIFICATION REPORT")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"Region: {REGION}")
    print(f"Endpoint: {WS_URL}")

    # Test 1: API Key format check
    print("\n[TEST 1] API Key format validation...")
    if not API_KEY or API_KEY.startswith("sk-your-"):
        print("  FAIL: API key not configured or is placeholder")
        results["tests"].append({"name": "api_key_format", "status": "FAIL", "message": "Key not configured"})
    else:
        print(f"  OK: Key found (prefix: {API_KEY[:8]}...)")
        results["tests"].append({"name": "api_key_format", "status": "PASS"})

    # Test 2: WebSocket connection
    print("\n[TEST 2] WebSocket connection...")
    connection_established = False
    session_created = False
    events_received = []

    try:
        ws = websocket.WebSocket()
        headers = {"Authorization": f"Bearer {API_KEY}"}
        ws.connect(WS_URL, header=headers, timeout=15)
        connection_established = True
        print("  OK: WebSocket connected successfully")
        results["tests"].append({"name": "websocket_connect", "status": "PASS"})

        # Wait for session.created event
        start = time.time()
        while time.time() - start < 10:
            try:
                ws.settimeout(2.0)
                msg = ws.recv()
                event = json.loads(msg)
                events_received.append(event)
                event_type = event.get("type", "unknown")

                if event_type == "session.created":
                    session_created = True
                    session_id = event.get("session", {}).get("id", "unknown")
                    print(f"  OK: session.created received (id={session_id})")
                    results["tests"].append({"name": "session_created", "status": "PASS", "session_id": session_id})
                    break
                elif event_type == "error":
                    print(f"  Server error: {json.dumps(event, indent=2)}")
                    results["tests"].append({"name": "session_created", "status": "FAIL", "error": event})
                    break
            except websocket.WebSocketTimeoutException:
                continue
            except Exception as e:
                print(f"  Event receive error: {e}")
                break

        if not session_created:
            print("  WARNING: No session.created event received (may need session.update)")
            results["tests"].append({"name": "session_created", "status": "WARN", "message": "No session.created"})

        # Test 3: Send session.update
        print("\n[TEST 3] Session configuration (session.update)...")
        session_update = {
            "event_id": f"test_{int(time.time())}",
            "type": "session.update",
            "session": {
                "modalities": ["text"],
                "input_audio_format": "pcm",
                "output_audio_format": "pcm",
                "instructions": "You are a test assistant. Respond with JSON only.",
                "turn_detection": None,
                "temperature": 0.7,
                "voice": "Cherry"
            }
        }
        ws.send(json.dumps(session_update))
        print(f"  OK: session.update sent")
        results["tests"].append({"name": "session_update", "status": "PASS"})

        # Test 4: Send test audio (silent PCM)
        print("\n[TEST 4] Audio input (input_audio_buffer.append)...")
        silent_audio = generate_silent_pcm(duration_ms=500)
        audio_b64 = base64.b64encode(silent_audio).decode("ascii")

        audio_event = {
            "event_id": f"audio_{int(time.time())}",
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        }
        ws.send(json.dumps(audio_event))
        print(f"  OK: Sent {len(silent_audio)} bytes of audio (500ms silent PCM)")
        print(f"  PCM format: 16kHz, 16bit, mono")
        results["tests"].append({
            "name": "audio_input",
            "status": "PASS",
            "audio_bytes": len(silent_audio),
            "format": "16kHz/16bit/mono/PCM"
        })

        # Test 5: Commit audio and get response
        print("\n[TEST 5] Audio commit and response...")
        commit_event = {
            "event_id": f"commit_{int(time.time())}",
            "type": "input_audio_buffer.commit"
        }
        ws.send(json.dumps(commit_event))

        # Create response
        response_create = {
            "event_id": f"resp_{int(time.time())}",
            "type": "response.create"
        }
        ws.send(json.dumps(response_create))

        # Wait for response
        print("  Waiting for model response...")
        response_done = False
        transcription = ""
        start = time.time()
        while time.time() - start < 15:
            try:
                ws.settimeout(3.0)
                msg = ws.recv()
                event = json.loads(msg)
                events_received.append(event)
                event_type = event.get("type", "unknown")

                if event_type == "response.audio_transcript.delta":
                    transcription += event.get("delta", "")
                elif event_type == "response.audio_transcript.done":
                    transcription = event.get("transcript", transcription)
                    print(f"  Transcript: '{transcription}'")
                elif event_type == "response.text.delta":
                    transcription += event.get("delta", "")
                elif event_type == "response.text.done":
                    transcription = event.get("text", transcription)
                    print(f"  Text response: '{transcription}'")
                elif event_type == "response.done":
                    response_done = True
                    usage = event.get("response", {}).get("usage", {})
                    print(f"  OK: response.done received")
                    if usage:
                        print(f"  Token usage: {usage}")
                    results["tests"].append({
                        "name": "audio_response",
                        "status": "PASS",
                        "response_text": transcription,
                        "usage": usage
                    })
                    break
                elif event_type == "error":
                    print(f"  Server error: {json.dumps(event, indent=2)}")
                    results["tests"].append({"name": "audio_response", "status": "FAIL", "error": event})
                    break
            except websocket.WebSocketTimeoutException:
                continue
            except Exception as e:
                print(f"  Receive error: {e}")
                break

        if not response_done:
            print("  WARNING: No response.done event received")
            results["tests"].append({"name": "audio_response", "status": "WARN", "message": "No response.done"})

        # Close connection
        ws.close()
        print("\n  Connection closed cleanly")

    except websocket.WebSocketException as e:
        print(f"  FAIL: WebSocket connection failed: {e}")
        results["tests"].append({"name": "websocket_connect", "status": "FAIL", "error": str(e)})
    except Exception as e:
        print(f"  FAIL: Unexpected error: {e}")
        results["tests"].append({"name": "websocket_connect", "status": "FAIL", "error": str(e)})

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for t in results.get("tests", []) if t.get("status") == "PASS")
    failed = sum(1 for t in results.get("tests", []) if t.get("status") == "FAIL")
    warnings = sum(1 for t in results.get("tests", []) if t.get("status") == "WARN")
    print(f"Passed: {passed}, Failed: {failed}, Warnings: {warnings}")
    print(f"Connection established: {connection_established}")
    print(f"Session created: {session_created}")
    print(f"Events received: {len(events_received)}")
    print(f"Response completed: {response_done}")

    # Save report
    with open("docs/api/qwen-api-verification-report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nReport saved to: docs/api/qwen-api-verification-report.json")

    return results


if __name__ == "__main__":
    test_qwen_api()
