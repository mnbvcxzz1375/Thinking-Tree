"""Test the /api/speech/analyze endpoint with real audio file."""
import os
import json
import base64
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Read the test MP3 file
test_audio_path = r"E:\VScodeProject\Tree\src\test\测试录音.mp3"

async def test_speech_analyze():
    """Test the speech analyze endpoint."""
    print("=" * 60)
    print("TESTING /api/speech/analyze ENDPOINT")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(test_audio_path):
        print(f"ERROR: Test audio file not found: {test_audio_path}")
        return
    
    # Read and encode audio
    with open(test_audio_path, "rb") as f:
        audio_bytes = f.read()
    
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    print(f"Audio file: {test_audio_path}")
    print(f"Audio size: {len(audio_bytes)} bytes")
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
    asyncio.run(test_speech_analyze())
