# Audio Processing Pipeline

> Complete data flow from microphone to AI API — PCM capture, conversion, streaming, and error handling.
> Target audience: Developers integrating the audio subsystem into the children's thinking tree application.

---

## Table of Contents

1. [Pipeline Overview](#1-pipeline-overview)
2. [Stage 1: Permission & Device Setup](#2-stage-1-permission--device-setup)
3. [Stage 2: Raw Audio Capture](#3-stage-2-raw-audio-capture)
4. [Stage 3: PCM Conversion](#4-stage-3-pcm-conversion)
5. [Stage 4: Encoding & Transmission](#5-stage-4-encoding--transmission)
6. [Firefox Fallback Path](#6-firefox-fallback-path)
7. [Error Handling](#7-error-handling)
8. [Performance Optimization](#8-performance-optimization)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AUDIO PROCESSING PIPELINE                     │
├──────────┬──────────┬────────────┬──────────┬────────────┬───────────┤
│Microphone│ getUser  │AudioContext│AudioWork │ Float32 →  │ Base64    │
│ Hardware │  Media   │  (Source)  │  let or  │  Int16 PCM │ Encode →  │
│          │          │            │ScriptProc│  16kHz/mono │  API      │
├──────────┼──────────┼────────────┼──────────┼────────────┼───────────┤
│Physical  │Permission│ Creates    │Dedicated │Resampling  │Binary-safe│
│mic input │  prompt  │AudioGraph  │audio     │+ format    │transport  │
│          │          │            │thread    │conversion  │           │
└──────────┴──────────┴────────────┴──────────┴────────────┴───────────┘
```

### Data Flow Summary

| Stage | Input | Output | Location | Latency |
|-------|-------|--------|----------|---------|
| Capture | Microphone analog signal | Float32Array (raw samples) | Browser audio stack | Hardware-dependent (~5-20ms) |
| Resample | Float32Array at source rate (44100/48000 Hz) | Float32Array at 16000 Hz | AudioWorklet thread (or main thread for Firefox) | ~0.1-0.5ms |
| Convert | Float32Array (-1.0 to 1.0) | Int16Array (-32768 to 32767) | AudioWorklet thread | ~0.05ms |
| Chunk | Accumulated Int16Array | Chunked Int16Array (100ms default) | AudioWorklet → main thread (MessagePort) | Transfer time: ~0ms (zero-copy) |
| Encode | Int16Array (binary) | Base64 string | Main thread | ~0.2ms per 3200 bytes |
| Transmit | Base64 string | WebSocket / HTTP POST → backend | Network | Network-dependent |

### Key Parameters

| Parameter | Value | Reason |
|-----------|-------|--------|
| **Target Sample Rate** | 16000 Hz | Standard for speech-to-text APIs (Qwen, Whisper, etc.) |
| **Bit Depth** | 16-bit signed integer | Industry standard for speech audio |
| **Channels** | 1 (mono) | Speech is mono; stereo provides no benefit |
| **Chunk Interval** | 100ms | Balance between latency (shorter) and efficiency (longer) |
| **Output Format** | Int16 PCM | Raw uncompressed audio — required by AI models |
| **Transmission Encoding** | Base64 | Safe for JSON/WebSocket transport |

---

## 2. Stage 1: Permission & Device Setup

### Flow

```
User clicks "Record"
  │
  ├─ navigator.permissions.query({name:'microphone'})
  │   ├─ granted → proceed
  │   ├─ denied → show error (user must change browser settings)
  │   └─ prompt → will trigger on getUserMedia()
  │
  ├─ navigator.mediaDevices.getUserMedia({audio: {...}})
  │   ├─ success → MediaStream
  │   │   └─ Log track info: label, sampleRate, channelCount
  │   └─ failure → classify error (denied / not found / in use)
  │
  └─ AudioContext creation
      ├─ new AudioContext() or new webkitAudioContext()
      ├─ Check ctx.state === 'suspended' (iOS!)
      │   └─ await ctx.resume() after user gesture
      └─ Log ctx.sampleRate (may differ from target)
```

### Constraints Configuration

```javascript
const DEFAULT_CONSTRAINTS = {
  audio: {
    channelCount: 1,          // Force mono
    echoCancellation: true,   // Reduce echo (important for children)
    noiseSuppression: true,   // Reduce background noise
    autoGainControl: true,    // Normalize volume levels
    sampleRate: { ideal: 16000 }, // Request 16kHz (browser may ignore)
  }
};
```

### iOS Safari Special Handling

```javascript
// After user gesture (click/tap)
async function startRecordingIOS() {
  const ctx = new AudioContext();
  if (ctx.state === 'suspended') {
    await ctx.resume();  // REQUIRED on iOS
  }
  // Now safe to create audio graph
}
```

### Error Classification

```javascript
function classifyError(err) {
  const mapping = {
    'NotAllowedError': 'PERMISSION_DENIED',
    'PermissionDeniedError': 'PERMISSION_DENIED',
    'NotFoundError': 'NO_MICROPHONE',
    'DevicesNotFoundError': 'NO_MICROPHONE',
    'NotReadableError': 'MIC_IN_USE',
    'TrackStartError': 'MIC_IN_USE',
    'OverconstrainedError': 'CONSTRAINT_UNSATISFIED',
  };
  return {
    code: mapping[err.name] || 'UNKNOWN',
    message: err.message,
    recoverable: err.name === 'NotAllowedError' ? false : true,
  };
}
```

---

## 3. Stage 2: Raw Audio Capture

### Route Selection

```
                    ┌─ AudioWorklet available? ─┐
                    │                            │
                    YES                          NO
                    │                            │
            ┌───────▼────────┐         ┌────────▼─────────┐
            │ AudioWorklet   │         │ ScriptProcessor  │
            │ Path            │         │ Path (Firefox)   │
            └───────┬────────┘         └────────┬─────────┘
                    │                            │
           Dedicated audio              Main thread
           thread, zero-jitter         (risk of jitter)
```

### AudioWorklet Path (Chrome, Safari, Edge)

```
MediaStreamSource → AudioWorkletNode → (optional) AudioContext.destination
                         │
                    process() callback
                    every 128 samples (~2.9ms at 44100Hz)
                         │
                    Accumulate samples internally
                    Send chunks every ~100ms
```

### ScriptProcessorNode Path (Firefox)

```
MediaStreamSource → ScriptProcessorNode → AudioContext.destination
                         │
                    onaudioprocess callback
                    every bufferSize samples (4096 default)
                         │
                    Resample + accumulate on main thread
                    Send chunks every ~100ms
```

---

## 4. Stage 3: PCM Conversion

### Conversion Formula

```
Float32Array sample (range: -1.0 to 1.0)
    │
    ├─ Clamp to [-1.0, 1.0]
    │
    └─ Convert:
         if sample >= 0: int16 = sample × 32767
         if sample < 0:  int16 = sample × 32768
    │
    └─ Result: Int16Array (range: -32768 to 32767)
```

### Resampling Methods

| Method | Quality | Cost | When to Use |
|--------|---------|------|-------------|
| **Linear Interpolation** | Good | Low | Default for all browsers |
| **Linear + Anti-Alias Filter** | Excellent | Medium | High-quality recording for training data |
| **Simple Decimation** | Acceptable | Lowest | Low-power devices, background capture |

### Resampling Implementation

```javascript
// Source rate: 44100 Hz, Target rate: 16000 Hz
// Ratio: 44100 / 16000 = 2.75625
// For every output sample, interpolate between two input samples

function resampleLinear(input, sourceRate, targetRate) {
  const ratio = sourceRate / targetRate;
  const outputLength = Math.floor(input.length / ratio);
  const output = new Float32Array(outputLength);

  for (let i = 0; i < outputLength; i++) {
    const srcIndex = i * ratio;
    const srcFloor = Math.floor(srcIndex);
    const srcCeil = Math.min(srcFloor + 1, input.length - 1);
    const fraction = srcIndex - srcFloor;
    output[i] = input[srcFloor] * (1 - fraction) + input[srcCeil] * fraction;
  }

  return output;
}
```

### Chunk Size Calculation

```
Chunk interval: 100ms
Target sample rate: 16000 Hz
Samples per chunk: 16000 × 0.1 = 1600 samples
Bytes per chunk (Int16): 1600 × 2 = 3200 bytes
Base64 size: 3200 × 4/3 ≈ 4267 characters
```

---

## 5. Stage 4: Encoding & Transmission

### Base64 Encoding

```javascript
/**
 * Convert Int16Array → Base64 string
 * Process in 8192-byte chunks to avoid call stack overflow
 */
function int16ToBase64(int16Array) {
  const bytes = new Uint8Array(int16Array.buffer);
  const CHUNK_SIZE = 8192;
  let binary = '';

  for (let i = 0; i < bytes.length; i += CHUNK_SIZE) {
    const chunk = bytes.subarray(i, i + CHUNK_SIZE);
    binary += String.fromCharCode.apply(null, chunk);
  }

  return btoa(binary);
}
```

### Message Format (WebSocket)

```json
{
  "type": "audio",
  "format": "pcm_int16",
  "sampleRate": 16000,
  "channels": 1,
  "bitDepth": 16,
  "data": "<base64-encoded-pcm>",
  "sequence": 42,
  "timestamp": 1714500000000,
  "durationMs": 100
}
```

### Streaming Architecture

```
Browser                          Backend (FastAPI)                     AI API (Qwen)
  │                                  │                                    │
  │── WS Connect ────────────────────▶│                                    │
  │◀── WS Connected ─────────────────│                                    │
  │                                  │                                    │
  │── audio chunk #1 (base64) ──────▶│── PCM base64 → API ──────────────▶│
  │── audio chunk #2 (base64) ──────▶│── PCM base64 → API ──────────────▶│
  │── audio chunk #3 (base64) ──────▶│── PCM base64 → API ──────────────▶│
  │        ...                       │        ...                        │
  │── end_of_audio ─────────────────▶│── finalize ──────────────────────▶│
  │                                  │                                    │
  │◀── transcription result ────────│◀── STT result ────────────────────│
```

---

## 6. Firefox Fallback Path

### Architecture

```
Firefox Browser
├── getUserMedia() ✅
├── AudioContext ✅
├── AudioWorklet ❌ (not available)
├── ScriptProcessorNode ⚠️ (deprecated but functional)
└── Web Worker for PCM conversion (optional)
```

### Performance Impact Analysis

| Metric | AudioWorklet | ScriptProcessorNode | Impact |
|--------|-------------|---------------------|--------|
| **Thread** | Dedicated audio thread | Main thread | **Medium** — May cause frame drops with heavy UI |
| **Buffer Size** | 128 frames (fixed) | Configurable (256-16384) | **Low** — Larger buffers reduce callback overhead |
| **Callback Overhead** | ~0.01ms | ~0.3-2ms | **Medium** — Cumulative under load |
| **Memory** | Zero-copy transfer | Copy per callback | **Low** — Small buffers (< 16KB) |
| **Jitter Risk** | None | Present under UI load | **High** — Avoid DOM updates during recording |
| **Stability** | Excellent | Good | **Medium** — More callback drops possible |

### Mitigation Strategies

1. **Larger Buffer Size:** Use 4096 samples instead of default to reduce callback frequency by 32× vs AudioWorklet
2. **Throttle UI Updates:** Pause all non-essential DOM rendering during recording
3. **Web Worker Offload:** Move Float32→Int16 conversion to a Web Worker
4. **RequestIdleCallback:** Batch non-critical processing during idle periods
5. **Monitor Performance:** Track `onaudioprocess` callback duration and warn if > 5ms

### Detection and Switch

```javascript
function selectAudioPath() {
  if (typeof AudioWorkletNode !== 'undefined') {
    return 'audioworklet'; // Chrome, Safari, Edge
  }

  if (typeof AudioContext !== 'undefined' ||
      typeof webkitAudioContext !== 'undefined') {
    return 'scriptprocessor'; // Firefox fallback
  }

  throw new Error('Audio capture not supported in this browser');
}
```

---

## 7. Error Handling

### Error Categories

| Category | Severity | Recovery | User Message |
|----------|----------|----------|--------------|
| Permission Denied | Critical | Manual | "Please enable microphone access in browser settings" |
| No Microphone | Critical | Plugin device | "No microphone found — please connect one" |
| Microphone in Use | Critical | Retry possible | "Microphone is being used by another app" |
| Browser Not Supported | Critical | Change browser | "Please use Chrome, Safari, or Edge" |
| AudioContext Failed | Critical | Reload page | "Audio system unavailable — try refreshing" |
| Worklet Load Failed | High | Retry | "Audio engine load failed — retrying..." |
| PCM Chunk Lost | Low | Auto-recover | (Silent — stream continues) |
| Buffer Overflow | Medium | Reduce recording | Internal recovery — no user-facing error |

### Error State Machine

```
                    ┌─────────┐
          ┌────────▶│  idle   │◀─────────┐
          │         └────┬────┘          │
          │              │               │
   ┌──────┴──────┐  ┌───▼────┐    ┌─────┴─────┐
   │   error     │  │request │    │  stopped  │
   │(unrecover)  │  │  ing   │    │           │
   └─────────────┘  └───┬────┘    └─────▲─────┘
                         │              │
                    ┌────▼────┐    ┌────┴────┐
                    │recording│───▶│  paused  │
                    │         │◀───│          │
                    └─────────┘    └─────────┘
```

### Recovery Strategies

```javascript
// Retry with exponential backoff for transient errors
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (!isRecoverable(err) || i === maxRetries - 1) throw err;
      await new Promise(r => setTimeout(r, Math.pow(2, i) * 500));
    }
  }
}
```

---

## 8. Performance Optimization

### Data Rate Calculation

```
Sample rate: 16000 samples/second
Bits per sample: 16 (2 bytes)
Channels: 1

Raw PCM data rate: 16000 × 2 × 1 = 32,000 bytes/second = ~31.25 KB/s

Base64 overhead: ×4/3
Transmission data rate: 31.25 × 4/3 ≈ 41.67 KB/s

Per 100ms chunk: ~3.2 KB raw, ~4.3 KB base64
Per minute: ~1.875 MB raw, ~2.5 MB base64
Per hour: ~112.5 MB raw, ~150 MB base64
```

### Optimization Techniques

1. **Zero-Copy Transfer**
   ```javascript
   // Transfer buffer ownership instead of copying
   port.postMessage({ data: buffer }, [buffer]); // buffer is now empty in sender
   ```

2. **Buffer Pooling**
   ```javascript
   // Reuse pre-allocated buffers instead of creating new ones
   const bufferPool = [];
   function getBuffer(size) {
     return bufferPool.pop() || new Float32Array(size);
   }
   function releaseBuffer(buf) {
     bufferPool.push(buf);
   }
   ```

3. **Chunk Interval Tuning**
   ```
   Shorter interval (50ms) → Lower latency, more network overhead
   Longer interval (200ms) → Higher latency, fewer network calls
   Recommended: 100ms as sweet spot for real-time speech
   ```

4. **Memory Management**
   ```javascript
   // Clear references to allow GC
   chunk.data = null; // Release Int16Array reference after sending
   ```

5. **Resampling Quality Budget**
   ```
   'low':   ~0.02ms per 128 samples — acceptable for most use cases
   'medium': ~0.05ms per 128 samples — recommended default
   'high':  ~0.12ms per 128 samples — for training data or critical recordings
   ```

### Performance Budget

| Scenario | Budget | Target |
|----------|--------|--------|
| AudioWorklet callback | < 1ms | ✅ Always met |
| ScriptProcessor callback | < 3ms | ⚠️ Monitor under load |
| PCM conversion (main thread) | < 0.5ms | ✅ Always met |
| Base64 encoding | < 1ms per chunk | ✅ Always met |
| UI frame budget during recording | 16.67ms (60fps) | Record + render ~5ms = 60fps feasible |

---

## 9. Testing Strategy

### Unit Tests (Vitest/Jest)

```javascript
describe('Audio Processing Pipeline', () => {
  test('Float32 to Int16 conversion', () => {
    const input = new Float32Array([0, 0.5, -0.5, 1.0, -1.0]);
    const output = float32ToInt16(input);
    expect(output[0]).toBe(0);
    expect(output[1]).toBeCloseTo(16384, -1);
    expect(output[2]).toBeCloseTo(-16384, -1);
    expect(output[3]).toBe(32767);
    expect(output[4]).toBe(-32768);
  });

  test('Resampling preserves frequency content', () => {
    // Generate 440Hz sine at 44100Hz
    const source = generateSine(440, 44100, 44100);
    const resampled = resampleLinear(source, 44100, 16000);
    // Verify output length
    expect(resampled.length).toBe(16000);
  });

  test('Base64 round-trip', () => {
    const original = new Int16Array([0, 1000, -1000, 32767, -32768]);
    const base64 = int16ToBase64(original);
    const decoded = base64ToInt16(base64);
    expect(decoded).toEqual(original);
  });

  test('Chunk timing matches configured interval', () => {
    // Mock audio processing
  });
});
```

### Browser Integration Tests

| Test Case | Browsers | Expected |
|-----------|----------|----------|
| Microphone permission flow | Chrome, Safari, Firefox, Edge | Permission prompt appears, audio track created |
| Recording 5 seconds | All | 50 chunks (±5) of ~1600 samples each |
| PCM format verification | All | Int16 range [-32768, 32767], 16000 sample rate metadata |
| Base64 encoding | All | Valid base64, decodable back to PCM |
| Pause/Resume | All | No data loss, continuous sample counts |
| Firefox fallback | Firefox | Uses ScriptProcessorNode, same output format |
| iOS Safari AudioContext resume | Safari iOS | Recording works after user gesture |
| Error: mic denied | All | Correct error message displayed |
| Error: no mic | All | Correct error message displayed |
| Memory: 5-minute recording | All | No leaks, stable memory profile |
| Concurrent: multiple tabs | Chrome | Only one active recording context |

### Quick Verification Script

```javascript
// Paste into browser console to verify audio setup
async function verifyAudioSetup() {
  console.log('Browser:', AudioRecorder.detectBrowser());

  // Check APIs
  console.log('AudioWorklet:', typeof AudioWorkletNode !== 'undefined');
  console.log('MediaRecorder:', typeof MediaRecorder !== 'undefined');
  console.log('getUserMedia:', !!navigator.mediaDevices?.getUserMedia);

  // Test AudioContext
  const ctx = new AudioContext();
  console.log('Sample rate:', ctx.sampleRate);
  console.log('State:', ctx.state);

  // Test permission
  try {
    const status = await navigator.permissions.query({name:'microphone'});
    console.log('Mic permission:', status.state);
  } catch(e) {
    console.log('Permission query not available');
  }

  // Test microphone
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio:true});
    console.log('Mic access: OK. Tracks:', stream.getAudioTracks().length);
    stream.getTracks().forEach(t => t.stop());
  } catch(e) {
    console.error('Mic access error:', e.name, e.message);
  }

  ctx.close();
}
```
