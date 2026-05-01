"""Generate test PCM audio and test the speech API."""
import os
import json
import base64
import struct
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

def generate_test_pcm(duration_ms=2000, sample_rate=16000):
    """Generate a simple PCM audio with some variation (not just silence)."""
    import math
    
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    
    # Generate a simple tone pattern (440Hz + 880Hz)
    for i in range(num_samples):
        t = i / sample_rate
        # Mix two frequencies with some amplitude variation
        value = int(16000 * math.sin(2 * math.pi * 440 * t) * 0.5)
        value += int(16000 * math.sin(2 * math.pi * 880 * t) * 0.3)
        # Add some envelope
        envelope = min(1.0, t * 10) * max(0, 1 - (t - duration_ms/1000 * 0.8) * 5)
        value = int(value * envelope)
        # Clamp to 16-bit range
        value = max(-32768, min(32767, value))
        samples.append(value)
    
    # Convert to bytes (little-endian 16-bit)
    pcm_bytes = b''
    for sample in samples:
        pcm_bytes += struct.pack('<h', sample)
    
    return pcm_bytes


async def test_with_pcm():
    """Test speech API with generated PCM audio."""
    print("=" * 60)
    print("TESTING WITH PCM AUDIO (16kHz/16bit/mono)")
    print("=" * 60)
    
    # Generate PCM audio
    pcm_audio = generate_test_pcm(duration_ms=2000)
    audio_base64 = base64.b64encode(pcm_audio).decode("utf-8")
    
    print(f"PCM audio size: {len(pcm_audio)} bytes")
    print(f"Base64 size: {len(audio_base64)} chars")
    
    # Build request
    payload = {
        "audio_base64": audio_base64,
        "provider": "qwen",
        "sample_rate": 16000,
        "channels": 1,
        "bit_depth": 16,
        "activity_context": {
            "tree_id": "test-tree",
            "theme": "树木",
            "description": "关于树木的思维树",
            "root": {
                "id": "root",
                "label": "树木",
                "content": "树木"
            },
            "directions": [
                {
                    "id": "dir-1",
                    "label": "外形",
                    "content": "外形特征",
                    "children": []
                },
                {
                    "id": "dir-2",
                    "label": "生长",
                    "content": "生长过程",
                    "children": []
                },
                {
                    "id": "dir-3",
                    "label": "用途",
                    "content": "树木用途",
                    "children": []
                }
            ],
            "total_nodes": 4
        }
    }
    
    print("\nSending request to http://localhost:8765/api/speech/analyze ...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:8765/api/speech/analyze",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"\nResponse Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("\n" + "=" * 60)
                print("SUCCESS!")
                print("=" * 60)
                print(f"rough_transcript: {result.get('rough_transcript')}")
                print(f"leaf_text: {result.get('leaf_text')}")
                print(f"recommended_parent_id: {result.get('recommended_parent_id')}")
                print(f"recommended_parent_label: {result.get('recommended_parent_label')}")
                print(f"classification_reason: {result.get('classification_reason')}")
                print(f"follow_up_question: {result.get('follow_up_question')}")
                print(f"confidence: {result.get('confidence')}")
            else:
                print("\n" + "=" * 60)
                print("FAILED")
                print("=" * 60)
                try:
                    error = response.json()
                    print(f"Error: {json.dumps(error, ensure_ascii=False, indent=2)}")
                except:
                    print(f"Response: {response.text[:500]}")
                    
    except Exception as e:
        print(f"\nERROR: {e}")


if __name__ == "__main__":
    asyncio.run(test_with_pcm())
