"""
MiMo-V2.5 API Connectivity Verification

Verifies:
1. API key validity
2. REST API endpoint
3. Audio URL and Base64 input methods
"""
import os
import json
import base64
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MIMO_API_KEY = os.getenv("MIMO_API_KEY")
MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
MIMO_MODEL = os.getenv("MIMO_MODEL", "MiMo-V2.5")


def generate_silent_pcm_base64(duration_ms=300, sample_rate=16000):
    """Generate silent PCM audio and return base64."""
    num_samples = int(sample_rate * duration_ms / 1000)
    audio = b'\x00' * (num_samples * 2)  # 16bit = 2 bytes per sample
    return base64.b64encode(audio).decode("ascii")


def test_mimo_api():
    """Test MiMo-V2.5 API connectivity."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "model": MIMO_MODEL,
        "base_url": MIMO_BASE_URL,
        "tests": []
    }

    print("=" * 60)
    print("MIMO-V2.5 API VERIFICATION REPORT")
    print("=" * 60)
    print(f"Model: {MIMO_MODEL}")
    print(f"Base URL: {MIMO_BASE_URL}")
    print(f"Key prefix: {MIMO_API_KEY[:8] if MIMO_API_KEY else 'NOT SET'}...")

    # Test 1: API key format
    print("\n[TEST 1] API Key format validation...")
    if not MIMO_API_KEY or MIMO_API_KEY.startswith("tp-your-"):
        print("  FAIL: API key not configured or is placeholder")
        results["tests"].append({"name": "api_key_format", "status": "FAIL", "message": "Key not configured"})
    else:
        print(f"  OK: Key found")
        results["tests"].append({"name": "api_key_format", "status": "PASS"})

    # Test 2: API Key validation via models endpoint
    print("\n[TEST 2] API Key validation (list models)...")
    key_valid = False
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{MIMO_BASE_URL}/models",
                headers={"Authorization": f"Bearer {MIMO_API_KEY}"}
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                import_key_valid = True
                models = response.json()
                print(f"  OK: {len(models.get('data', []) if isinstance(models, dict) else models)} models available")
                results["tests"].append({"name": "models_list", "status": "PASS"})
            elif response.status_code == 401:
                print(f"  FAIL: Unauthorized (401) - Invalid API key")
                results["tests"].append({"name": "models_list", "status": "FAIL", "http_status": 401, "message": "Unauthorized"})
            elif response.status_code == 403:
                print(f"  FAIL: Forbidden (403)")
                results["tests"].append({"name": "models_list", "status": "FAIL", "http_status": 403})
            else:
                print(f"  Response: {response.text[:500]}")
                results["tests"].append({
                    "name": "models_list",
                    "status": "WARN",
                    "http_status": response.status_code,
                    "response_sample": response.text[:300]
                })
    except httpx.ConnectError as e:
        print(f"  FAIL: Connection error: {e}")
        results["tests"].append({"name": "models_list", "status": "FAIL", "error": "Connection error"})
    except Exception as e:
        print(f"  FAIL: {e}")
        results["tests"].append({"name": "models_list", "status": "FAIL", "error": str(e)})

    # Test 3: Chat completions endpoint
    print("\n[TEST 3] Chat completions endpoint...")
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{MIMO_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {MIMO_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MIMO_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant. Always respond in JSON format."},
                        {"role": "user", "content": "Say hello in one word."}
                    ],
                    "max_tokens": 50
                }
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"  OK: Response received: '{content}'")
                results["tests"].append({
                    "name": "chat_completion",
                    "status": "PASS",
                    "response_sample": content[:100]
                })
            else:
                print(f"  Response: {response.text[:300]}")
                results["tests"].append({
                    "name": "chat_completion",
                    "status": "WARN",
                    "http_status": response.status_code,
                    "response_sample": response.text[:300]
                })
    except httpx.ConnectError as e:
        print(f"  FAIL: Connection error: {e}")
        results["tests"].append({"name": "chat_completion", "status": "FAIL", "error": "Connection error"})
    except Exception as e:
        print(f"  FAIL: {e}")
        results["tests"].append({"name": "chat_completion", "status": "FAIL", "error": str(e)})

    # Test 4: Audio understanding endpoint (Base64)
    print("\n[TEST 4] Audio understanding (Base64 input)...")
    try:
        silent_audio_b64 = generate_silent_pcm_base64(duration_ms=300)
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{MIMO_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {MIMO_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MIMO_MODEL,
                    "messages": [
                        {"role": "system", "content": "Analyze the audio and describe what you hear."},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "What do you hear in this audio?"},
                                {
                                    "type": "audio_url",
                                    "audio_url": {
                                        "url": f"data:audio/wav;base64,{silent_audio_b64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 200
                }
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"  OK: Audio analysis response: '{content[:200]}'")
                results["tests"].append({
                    "name": "audio_base64",
                    "status": "PASS",
                    "response_sample": content[:200]
                })
            else:
                print(f"  Response: {response.text[:400]}")
                results["tests"].append({
                    "name": "audio_base64",
                    "status": "WARN",
                    "http_status": response.status_code,
                    "response_sample": response.text[:300]
                })
    except Exception as e:
        print(f"  FAIL: {e}")
        results["tests"].append({"name": "audio_base64", "status": "FAIL", "error": str(e)})

    # Summary
    print("\n" + "=" * 60)
    print("MIMO TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for t in results.get("tests", []) if t.get("status") == "PASS")
    failed = sum(1 for t in results.get("tests", []) if t.get("status") == "FAIL")
    warnings = sum(1 for t in results.get("tests", []) if t.get("status") == "WARN")
    print(f"Passed: {passed}, Failed: {failed}, Warnings: {warnings}")

    # Save report
    with open("docs/api/mimo-api-verification-report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nReport saved to: docs/api/mimo-api-verification-report.json")

    return results


if __name__ == "__main__":
    test_mimo_api()
