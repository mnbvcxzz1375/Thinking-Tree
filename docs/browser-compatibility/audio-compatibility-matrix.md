# Browser Audio Compatibility Matrix

> Task 0.3 — Wave 0: Legal & Technical Verification
> Last Updated: 2026-04-30

## Quick Reference

| Feature                    | Chrome Desktop | Chrome Mobile | Safari Desktop | Safari iOS | Firefox Desktop | Edge Desktop |
|----------------------------|:-------------:|:-------------:|:--------------:|:----------:|:---------------:|:------------:|
| **getUserMedia**           | ✅ 53+        | ✅ 53+        | ✅ 11+         | ✅ 11+     | ✅ 36+          | ✅ 79+       |
| **AudioWorklet**           | ✅ 66+        | ✅ 66+        | ✅ 14.1+       | ✅ 14.5+   | ❌              | ✅ 79+       |
| **AudioContext**           | ✅ 35+        | ✅ 37+        | ✅ 7.1+        | ✅ 7.1+    | ✅ 25+          | ✅ 79+       |
| **MediaRecorder**          | ✅ 49+        | ✅ 49+        | ✅ 14.1+       | ✅ 14.5+   | ✅ 25+          | ✅ 79+       |
| **ScriptProcessorNode**    | ⚠️ 24+ (dep)  | ⚠️ 24+ (dep)  | ⚠️ 6+ (dep)    | ⚠️ 6+ (dep)| ✅ 25+          | ⚠️ 79+ (dep) |
| **Permissions API**        | ✅ 43+        | ✅ 43+        | ✅ 16+         | ✅ 16+     | ⚠️ partial      | ✅ 79+       |

### Legend
- ✅ **Fully supported** — Works without issues
- ⚠️ **Limited/Deprecated** — Works but with caveats (see notes)
- ❌ **Not supported** — Not available in this browser

---

## Detailed Per-Browser Analysis

### 1. Google Chrome (Desktop & Mobile)

| Aspect | Status | Notes |
|--------|--------|-------|
| **Version tested** | 130+ | Latest stable |
| **AudioWorklet** | ✅ | Fully supported since Chrome 66 (2018) |
| **AudioContext.sampleRate** | 44100 / 48000 Hz | Depends on OS audio settings. Cannot be forced via constructor. |
| **MediaRecorder MIME Types** | `audio/webm;codecs=opus`, `audio/webm` | Opus codec in WebM container. No native WAV/PCM output from MediaRecorder. |
| **Resampling** | ✅ via AudioWorklet | Zero-jitter on dedicated thread. Recommended path. |
| **Permission query** | ✅ | `navigator.permissions.query({name:'microphone'})` supported |
| **Echo cancellation** | ✅ | Works well with default constraints |
| **Noise suppression** | ✅ | Built-in, good quality |
| **Auto gain control** | ✅ | Available |

**Chrome Mobile Notes:**
- AudioContext may be suspended until user gesture on Android
- `sampleRate` on Android is commonly 44100 Hz
- Battery optimization may throttle background tabs
- PWA audio capture works in foreground only on some Android versions

**Recommendation:** Primary target. Use AudioWorklet path.

---

### 2. Apple Safari (Desktop & iOS)

| Aspect | Status | Notes |
|--------|--------|-------|
| **Version tested** | 18+ (desktop), 17+ (iOS) | |
| **AudioWorklet** | ✅ (14.1+) | Supported since Safari 14.1 (2021) |
| **AudioContext.sampleRate** | 44100 Hz | Fixed at 44100 on all Apple devices. Consistent across iPhone/iPad/Mac. |
| **MediaRecorder MIME Types** | `audio/mp4`, `audio/aac` | AAC in MP4 container. No native WAV/PCM. |
| **Resampling** | ✅ via AudioWorklet | Works well. 44100 → 16000 downsampling needed. |
| **Permission query** | ✅ (16+) | Supported |
| **Echo cancellation** | ✅ | Available |
| **Noise suppression** | ✅ | Available, but less aggressive than Chrome |
| **Auto gain control** | ✅ | Available |

**iOS Safari Critical Limitations:**
1. **AudioContext is ALWAYS suspended initially** — requires explicit `resume()` call after user gesture
2. **No persistent background audio** — audio capture stops when Safari goes to background
3. **iPadOS may report as "Macintosh"** — `navigator.platform` is `"MacIntel"` on iPadOS 13+. Use `navigator.maxTouchPoints > 1` to detect iPad.
4. **No `navigator.mediaDevices` in WKWebView** — hybrid apps must use native audio bridge
5. **Stereo-only constraint issues** — explicitly request `channelCount: 1` for mono
6. **Sample rate is always 44100 Hz** — resampling to 16000 Hz required

**iOS Safari Permission UX:**
- Permission prompt appears at first `getUserMedia()` call
- User must explicitly tap "Allow"
- Once denied, user must go to Settings → Safari → Microphone to reset
- No "Ask Next Time" — it's binary Allow/Deny

**Recommendation:** Full support with iOS-specific handling. Always `resume()` AudioContext after touch event.

---

### 3. Mozilla Firefox (Desktop)

| Aspect | Status | Notes |
|--------|--------|-------|
| **Version tested** | 131+ (latest) | |
| **AudioWorklet** | ❌ **NOT SUPPORTED** | MDN confirms no AudioWorklet as of Firefox 131. Tracked in [bug 1572634](https://bugzilla.mozilla.org/show_bug.cgi?id=1572634) |
| **AudioContext.sampleRate** | 44100 / 48000 Hz | OS-dependent |
| **MediaRecorder MIME Types** | `audio/ogg;codecs=opus`, `audio/webm` | OGG/Opus container. No WAV/PCM. |
| **Resampling** | ⚠️ ScriptProcessorNode | **Must use ScriptProcessorNode fallback** — runs on main thread |
| **Permission query** | ⚠️ Partial | `navigator.permissions.query({name:'microphone'})` throws `TypeError` in some versions. Must catch and fall back to direct `getUserMedia()`. |
| **Echo cancellation** | ✅ | Available |
| **Noise suppression** | ✅ | Available |
| **Auto gain control** | ✅ | Available |

**Firefox-Specific Issues:**
1. **No AudioWorklet** — must use ScriptProcessorNode (deprecated in spec but still functional)
2. **`permissions.query` for microphone unavailable** — always wraps in try/catch
3. **MediaRecorder `dataavailable` fires differently** — smaller chunks, different timing
4. **`AudioContext.sampleRate` defaults to different rates** on Windows (44100) vs Linux (48000)
5. **Constructor `sampleRate` option** may be ignored — never assume requested rate is honored

**Recommendation:** Designate as fallback path with ScriptProcessorNode. Accept slightly reduced performance.

---

### 4. Microsoft Edge (Desktop, Chromium-based)

| Aspect | Status | Notes |
|--------|--------|-------|
| **Version tested** | 130+ | Chromium-based since Edge 79 (Jan 2020) |
| **AudioWorklet** | ✅ (79+) | Same Chromium engine as Chrome |
| **AudioContext.sampleRate** | 44100 / 48000 Hz | Same as Chrome |
| **MediaRecorder MIME Types** | `audio/webm;codecs=opus` | Same as Chrome |
| **Resampling** | ✅ via AudioWorklet | Same as Chrome |
| **Permission query** | ✅ | Same as Chrome |
| **Echo cancellation** | ✅ | Same as Chrome |

**Edge Notes:**
- Functionally identical to Chrome for audio APIs (same Chromium base)
- Edge Legacy (pre-Chromium, version 44 and below) should be treated as unsupported
- Windows audio subsystem may introduce additional latency on some devices

**Recommendation:** Treat identically to Chrome. Use AudioWorklet path.

---

## MediaRecorder Output Format Comparison

This is relevant for recording-based approaches (alternative to raw PCM streaming):

| Browser | Container | Audio Codec | MIME Type | PCM Possible? |
|---------|-----------|-------------|-----------|:---:|
| Chrome | WebM | Opus | `audio/webm;codecs=opus` | ❌ |
| Chrome | WebM | PCM (rare) | `audio/webm;codecs=pcm` | ⚠️ Unreliable |
| Safari | MP4 | AAC | `audio/mp4` | ❌ |
| Safari | MP4 | PCM via WAV | `audio/wav` | ⚠️ iOS only |
| Firefox | OGG | Opus | `audio/ogg;codecs=opus` | ❌ |
| Firefox | WebM | Opus | `audio/webm` | ❌ |
| Edge | WebM | Opus | `audio/webm;codecs=opus` | ❌ |

**Key Insight:** MediaRecorder in ALL browsers defaults to lossy compressed formats (Opus/AAC). For raw PCM needed by AI speech-to-text APIs, we MUST use the AudioWorklet/ScriptProcessor path to capture raw Float32 samples.

---

## Permissions API Behavior

| Browser | `navigator.permissions.query({name:'microphone'})` | State Values |
|---------|-----------------------------------------------------|--------------|
| Chrome | ✅ Returns PermissionStatus | `granted`, `denied`, `prompt` |
| Safari | ✅ Returns PermissionStatus | `granted`, `denied`, `prompt` |
| Firefox | ❌ Throws TypeError | N/A — query unavailable |
| Edge | ✅ Returns PermissionStatus | `granted`, `denied`, `prompt` |

**Error Handling Matrix:**

| Error Type | Chrome | Safari | Firefox | Edge |
|-----------|:------:|:------:|:-------:|:----:|
| User denies | `NotAllowedError` | `NotAllowedError` | `NotAllowedError` | `NotAllowedError` |
| No microphone | `NotFoundError` | `NotFoundError` | `NotFoundError` | `NotFoundError` |
| Mic in use | `NotReadableError` | `NotReadableError` | `NotReadableError` | `NotReadableError` |
| Permission already denied | `NotAllowedError` | `NotAllowedError` | `NotAllowedError` | `NotAllowedError` |

---

## AudioContext Sample Rate Behavior

| Platform | Default SampleRate | Notes |
|----------|-------------------|-------|
| Windows Chrome | 44100 / 48000 | OS default audio device |
| macOS Chrome | 44100 | Usually 44100 |
| macOS Safari | 44100 | Always 44100 on Apple hardware |
| iOS Safari | 44100 | Fixed at 44100 |
| Android Chrome | 44100 / 48000 | Device-dependent |
| Linux Firefox | 48000 | Varies with PulseAudio/ALSA |

**Our target: 16000 Hz mono.** This always requires downsampling, regardless of platform.

---

## Resampling Performance Comparison

| Method | Thread | Quality | Overhead | Notes |
|--------|--------|---------|----------|-------|
| AudioWorklet (linear interp) | Dedicated audio thread | Good | ~0.05ms/128 samples | ✅ Primary path |
| AudioWorklet (anti-alias) | Dedicated audio thread | Excellent | ~0.12ms/128 samples | For high-quality |
| ScriptProcessorNode | Main thread | Acceptable | ~0.3-2ms/chunk | ⚠️ Firefox fallback |
| Web Worker (offloaded) | Worker thread | Good | ~1-3ms/chunk (transfer cost) | Firefox+Worker hybrid |

---

## Feature Detection Code Reference

```javascript
// Complete browser audio capability detection
const audioCapabilities = {
  // Core APIs
  getUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
  audioContext: !!(window.AudioContext || window.webkitAudioContext),

  // AudioWorklet (preferred path)
  audioWorklet: typeof AudioWorkletNode !== 'undefined',

  // MediaRecorder (alternative path — lossy codecs only)
  mediaRecorder: typeof MediaRecorder !== 'undefined',

  // Permissions
  permissionsQuery: (() => {
    try {
      return !!(navigator.permissions && navigator.permissions.query);
    } catch(e) { return false; }
  })(),

  // Recommended path
  recommendedPath: typeof AudioWorkletNode !== 'undefined'
    ? 'audioworklet'
    : 'scriptprocessor',

  // Browser info
  browser: (() => {
    const ua = navigator.userAgent;
    if (/Chrome\//.test(ua) && !/Edge\//.test(ua)) return 'chrome';
    if (/Safari\//.test(ua) && !/Chrome\//.test(ua)) return 'safari';
    if (/Firefox\//.test(ua)) return 'firefox';
    if (/Edg\//.test(ua)) return 'edge';
    return 'unknown';
  })(),
};
```

---

## iOS Safari WebKit Behavior

### WKWebView (in-app browser)
- `navigator.mediaDevices.getUserMedia` **may not be available** depending on iOS version and WKWebView configuration
- Requires `NSMicrophoneUsageDescription` in app's Info.plist
- Audio capture stops when the WebView loses focus
- No AudioWorklet in iOS 13.x and earlier

### SFSafariViewController
- Same capabilities as Safari.app
- AudioContext still starts suspended

### iPadOS PWA (added to Home Screen)
- Runs in Safari rendering engine
- AudioContext remains suspended until gesture
- Audio capture will stop if app is backgrounded

---

## Decision Tree: Choosing the Audio Path

```
Browser audio capture needed?
│
├─ AudioWorklet available? (Chrome 66+, Safari 14.1+, Edge 79+)
│  └─ YES → Use AudioWorklet path
│     ├─ PCMConversionWorklet.js handles resampling on audio thread
│     ├─ Zero-copy buffer transfer via MessagePort with transferables
│     └─ Optimal: no main-thread jitter, dedicated audio priority
│
└─ AudioWorklet NOT available? (Firefox, older browsers)
   └─ Use ScriptProcessorNode fallback
      ├─ FirefoxFallback.js handles resampling on main thread
      ├─ Accept performance tradeoff
      ├─ Consider larger buffer sizes (4096+) to reduce callback frequency
      └─ Optional: Web Worker offload for PCM conversion
```

---

## Recommendations for Production

1. **Prioritize Chrome/Edge** — AudioWorklet provides the best experience
2. **Test Safari early** — iOS limitations are the most restrictive
3. **Firefox as graceful degradation** — ScriptProcessorNode works, just slightly less efficient
4. **Always request mono** — `channelCount: 1` in constraints
5. **Always resample to 16000 Hz** — target sample rate for speech-to-text APIs
6. **Handle AudioContext suspension** — especially on iOS
7. **Test on real devices** — emulated browsers may not expose real audio hardware limitations
8. **Provide clear error messages** — help users understand microphone permission issues
