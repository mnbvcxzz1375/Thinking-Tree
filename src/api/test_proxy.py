"""
Test script for WebSocket proxy - sends test PCM audio and measures performance.
"""
import os
import json
import base64
import time
import asyncio
import websockets
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PROXY_URL = f"ws://{os.getenv('HOST', '127.0.0.1')}:{os.getenv('PORT', '8765')}/ws"


def generate_test_pcm(duration_ms=1000, sample_rate=16000):
    """Generate simple test PCM audio (sine wave at 440Hz)."""
    import math
    import struct
    
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    for i in range(num_samples):
        # 440Hz sine wave at 25% amplitude
        t = i / sample_rate
        value = int(16384 * math.sin(2 * math.pi * 440 * t))
        samples.append(struct.pack('<h', value))
    
    return b''.join(samples)


async def test_proxy_streaming():
    """Test audio streaming through the WebSocket proxy."""
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "proxy_url": PROXY_URL,
        "tests": [],
        "events_received": 0,
        "transcription": "",
        "total_latency_ms": 0,
    }

    print("=" * 60)
    print("WEBSOCKET PROXY TEST")
    print("=" * 60)
    print(f"Proxy URL: {PROXY_URL}")

    try:
        async with websockets.connect(PROXY_URL) as ws:
            print("\n[1] Connected to proxy")

            # Wait for connected message
            msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(msg)
            print(f"  Received: {data.get('type')}")
            if data.get("type") == "connected":
                print(f"  OK: Session created: {data.get('session_id')}")
                metrics["tests"].append({"name": "proxy_connect", "status": "PASS"})
                metrics["tests"].append({"name": "session_created", "status": "PASS"})
            elif data.get("type") == "error":
                print(f"  FAIL: {data.get('message')}")
                metrics["tests"].append({"name": "proxy_connect", "status": "FAIL", "error": data})
                return metrics

            # Configure session for text-only
            print("\n[2] Configuring session (text-only)...")
            configure_msg = {
                "type": "configure",
                "instructions": "You are a children's thinking tree assistant. When you hear a child speak, summarize their thought in 6-12 Chinese characters. Output JSON: {\"leafText\": \"...\"}",
                "modalities": ["text"],
                "temperature": 0.7,
            }
            await ws.send(json.dumps(configure_msg))
            print("  OK: Configuration sent")
            metrics["tests"].append({"name": "session_configure", "status": "PASS"})

            # Send test audio
            print("\n[3] Sending test PCM audio...")
            test_audio = generate_test_pcm(duration_ms=500)
            audio_b64 = base64.b64encode(test_audio).decode("ascii")
            
            audio_msg = {
                "type": "audio",
                "data": audio_b64,
            }
            send_time = time.time()
            await ws.send(json.dumps(audio_msg))
            print(f"  OK: Sent {len(test_audio)} bytes of audio")
            metrics["tests"].append({
                "name": "audio_send", 
                "status": "PASS", 
                "audio_bytes": len(test_audio)
            })

            # Commit and request response
            print("\n[4] Committing audio and requesting response...")
            await ws.send(json.dumps({"type": "commit"}))
            print("  OK: Commit sent")

            # Wait for response events
            print("\n[5] Waiting for model response...")
            response_received = False
            transcription = ""
            start_time = time.time()

            while time.time() - start_time < 20:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                    data = json.loads(msg)
                    metrics["events_received"] += 1
                    msg_type = data.get("type", "")
                    
                    if msg_type == "transcription":
                        text = data.get("text", "")
                        transcription += text
                        if data.get("final"):
                            print(f"  [FINAL] Transcription: '{text}'")
                        else:
                            print(f"  [Delta] {text}", end="", flush=True)
                    
                    elif msg_type == "response_done":
                        response_received = True
                        latency = (time.time() - send_time) * 1000
                        metrics["total_latency_ms"] = latency
                        usage = data.get("usage", {})
                        print(f"\n  OK: Response done in {latency:.0f}ms")
                        print(f"  Usage: {usage}")
                        metrics["tests"].append({
                            "name": "response_received",
                            "status": "PASS",
                            "latency_ms": latency,
                            "usage": usage,
                        })
                        break
                    
                    elif msg_type == "error":
                        print(f"  ERROR: {data.get('message')}")
                        metrics["tests"].append({
                            "name": "response_received", 
                            "status": "FAIL", 
                            "error": data
                        })
                        break
                    
                    elif msg_type == "event":
                        dash_event = data.get("dashscope_event", {})
                        event_type = dash_event.get("type", "")
                        if event_type not in ("input_audio_buffer.status",):
                            print(f"  [Event] {event_type}")
                
                except asyncio.TimeoutError:
                    continue

            metrics["transcription"] = transcription
            if not response_received:
                metrics["tests"].append({
                    "name": "response_received",
                    "status": "WARN",
                    "message": "No response.done received within 20s"
                })

            # Clean close
            await ws.send(json.dumps({"type": "close"}))
            print("\n[6] Connection closed cleanly")
            metrics["tests"].append({"name": "clean_close", "status": "PASS"})

    except websockets.exceptions.ConnectionClosed as e:
        print(f"  Connection closed unexpectedly: {e}")
        metrics["tests"].append({"name": "proxy_connect", "status": "FAIL", "error": str(e)})
    except Exception as e:
        print(f"  Test failed: {e}")
        metrics["tests"].append({"name": "proxy_connect", "status": "FAIL", "error": str(e)})

    # Summary
    print("\n" + "=" * 60)
    print("PROXY TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for t in metrics.get("tests", []) if t.get("status") == "PASS")
    failed = sum(1 for t in metrics.get("tests", []) if t.get("status") == "FAIL")
    print(f"Passed: {passed}, Failed: {failed}")
    print(f"Events received: {metrics['events_received']}")
    print(f"Latency: {metrics['total_latency_ms']:.0f}ms")
    print(f"Transcription: '{metrics['transcription']}'")

    # Save report
    with open("docs/api/proxy-test-report.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nReport saved to: docs/api/proxy-test-report.json")

    return metrics


if __name__ == "__main__":
    asyncio.run(test_proxy_streaming())
