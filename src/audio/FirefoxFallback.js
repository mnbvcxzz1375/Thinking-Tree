/**
 * FirefoxFallback.js
 * Standalone ScriptProcessorNode-based PCM capture for Firefox and older browsers.
 *
 * Firefox limitations vs Chrome/Safari:
 * - No AudioWorklet support (as of Firefox 131)
 * - ScriptProcessorNode runs on the main thread → can cause jitter/glitches under heavy UI load
 * - AudioContext.sampleRate is commonly 44100 or 48000 → client-side resampling REQUIRED
 * - navigator.permissions.query('microphone') throws TypeError in some versions
 * - MediaRecorder only supports OGG/Opus (no WAV/PCM natively)
 *
 * Tradeoffs of ScriptProcessorNode:
 * + Universal browser support (Chrome 14+, Firefox 25+, Safari 6+)
 * + Simple API — fewer moving parts
 * - Runs on main thread — competes with UI rendering, animations, DOM updates
 * - Can drop audio data under heavy load (no automatic buffering)
 * - Fixed buffer sizes (power of 2: 256, 512, 1024, 2048, 4096, 8192, 16384)
 * - No zero-copy buffer transfer (data is copied, not transferred)
 *
 * Performance mitigation strategies:
 * 1. Use larger buffer sizes (4096+) to reduce callback frequency
 * 2. Offload PCM conversion to a Web Worker
 * 3. Minimize DOM updates during recording
 * 4. Use requestIdleCallback for non-critical processing
 * 5. Throttle UI rendering during active recording
 *
 * Usage:
 *   const fallback = new FirefoxFallback({
 *     onPCMChunk: (pcm) => { ... },
 *     targetSampleRate: 16000,
 *   });
 *   await fallback.start();
 *   // ... recording ...
 *   fallback.stop();
 */

class FirefoxFallback {
  /**
   * @param {Object} options
   * @param {Function} options.onPCMChunk       - Callback for each PCM chunk
   * @param {Function} options.onStateChange    - State change callback
   * @param {Function} options.onError          - Error callback
   * @param {number}   options.targetSampleRate - Target sample rate (default: 16000)
   * @param {number}   options.bufferSize       - ScriptProcessor buffer size (power of 2, default: 4096)
   * @param {boolean}  options.useWorker        - Offload conversion to Web Worker (default: false)
   * @param {number}   options.chunkInterval    - Chunk emission interval in ms (default: 100)
   */
  constructor(options = {}) {
    this._onPCMChunk = options.onPCMChunk || (() => {});
    this._onStateChange = options.onStateChange || (() => {});
    this._onError = options.onError || (() => {});
    this._targetSampleRate = options.targetSampleRate || 16000;
    this._bufferSize = options.bufferSize || 4096;
    this._useWorker = options.useWorker || false;
    this._chunkInterval = options.chunkInterval || 100;

    this._state = 'idle';
    this._audioContext = null;
    this._scriptNode = null;
    this._sourceNode = null;
    this._stream = null;
    this._worker = null;

    // Performance tracking
    this._perf = {
      callbackDurations: [],
      maxCallbackDuration: 0,
      droppedCallbacks: 0,
      totalCallbacks: 0,
      chunksEmitted: 0,
      rawSamplesProcessed: 0,
      resampledSamplesGenerated: 0,
      timeSpentInCallback: 0,
    };
  }

  // ─── Public API ────────────────────────────────────────────

  async start() {
    if (this._state === 'recording') return;
    this._setState('requesting');

    try {
      // Request microphone
      this._stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // Create AudioContext
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this._audioContext = new AudioCtx();
      console.log('[FirefoxFallback] AudioContext sampleRate:', this._audioContext.sampleRate);

      // Resolve AudioContext suspension (especially on iOS)
      if (this._audioContext.state === 'suspended') {
        await this._audioContext.resume();
      }

      // Set up ScriptProcessorNode
      this._scriptNode = this._audioContext.createScriptProcessor(this._bufferSize, 1, 1);

      // Accumulation buffer and resampling state
      let accumulated = new Float32Array(0);
      const sourceRate = this._audioContext.sampleRate;
      const targetRate = this._targetSampleRate;
      const samplesPerChunk = Math.floor(targetRate * (this._chunkInterval / 1000));
      const ratio = sourceRate / targetRate;

      // Start Web Worker for PCM conversion if requested
      if (this._useWorker) {
        this._worker = this._createConversionWorker();
      }

      this._scriptNode.onaudioprocess = (event) => {
        const cbStart = performance.now();
        this._perf.totalCallbacks++;

        const inputData = event.inputBuffer.getChannelData(0);
        if (!inputData || inputData.length === 0) return;

        this._perf.rawSamplesProcessed += inputData.length;

        // Step 1: Resample to target rate (linear interpolation)
        // Complexity: O(n) where n = inputData.length
        const newLength = Math.floor(inputData.length / ratio);
        const resampled = new Float32Array(newLength);
        for (let i = 0; i < newLength; i++) {
          const srcIdx = i * ratio;
          const floor = Math.floor(srcIdx);
          const ceil = Math.min(floor + 1, inputData.length - 1);
          const frac = srcIdx - floor;
          resampled[i] = inputData[floor] * (1 - frac) + inputData[ceil] * frac;
        }
        this._perf.resampledSamplesGenerated += resampled.length;

        // Step 2: Accumulate
        const newAcc = new Float32Array(accumulated.length + resampled.length);
        newAcc.set(accumulated, 0);
        newAcc.set(resampled, accumulated.length);
        accumulated = newAcc;

        // Step 3: Emit chunks at configured interval
        while (accumulated.length >= samplesPerChunk) {
          const chunk = accumulated.slice(0, samplesPerChunk);
          accumulated = accumulated.slice(samplesPerChunk);

          if (this._useWorker && this._worker) {
            // Offload PCM conversion to worker
            this._worker.postMessage({
              type: 'convert',
              data: chunk.buffer,
              id: this._perf.chunksEmitted,
            }, [chunk.buffer]);
          } else {
            // Convert on main thread
            const pcm = this._float32ToInt16(chunk);
            const base64 = this._int16ToBase64(pcm);

            this._onPCMChunk({
              data: pcm,
              base64: base64,
              sampleRate: targetRate,
              bitDepth: 16,
              channels: 1,
              sampleCount: pcm.length,
              durationMs: (pcm.length / targetRate) * 1000,
              timestamp: Date.now(),
              source: 'firefox-fallback',
            });
          }

          this._perf.chunksEmitted++;
        }

        // Track callback performance
        const cbDuration = performance.now() - cbStart;
        this._perf.callbackDurations.push(cbDuration);
        this._perf.maxCallbackDuration = Math.max(this._perf.maxCallbackDuration, cbDuration);
        this._perf.timeSpentInCallback += cbDuration;

        // Warn if callback is taking too long (> 5ms, risk of audio glitches at 4096 buffer)
        if (cbDuration > 5) {
          console.warn('[FirefoxFallback] Slow onaudioprocess callback:', cbDuration.toFixed(2) + 'ms');
        }

        // Detect dropped callbacks by comparing expected vs actual interval
        const expectedIntervalMs = (this._bufferSize / sourceRate) * 1000;
        if (cbDuration > expectedIntervalMs * 1.5) {
          this._perf.droppedCallbacks++;
        }
      };

      // Connect audio graph
      this._sourceNode = this._audioContext.createMediaStreamSource(this._stream);
      this._sourceNode.connect(this._scriptNode);
      this._scriptNode.connect(this._audioContext.destination);

      this._setState('recording');
      console.log('[FirefoxFallback] Recording started. Buffer:', this._bufferSize, 'Source rate:', sourceRate, 'Target rate:', targetRate);
    } catch (err) {
      this._setState('error');
      this._onError(err);
      throw err;
    }
  }

  stop() {
    if (this._state !== 'recording') return;

    // Process remaining accumulated data
    this._teardown();
    this._setState('stopped');

    // Log performance summary
    const avgCb = this._perf.callbackDurations.length > 0
      ? this._perf.timeSpentInCallback / this._perf.callbackDurations.length
      : 0;
    console.log('[FirefoxFallback] Performance summary:', {
      totalCallbacks: this._perf.totalCallbacks,
      droppedCallbacks: this._perf.droppedCallbacks,
      avgCallbackMs: avgCb.toFixed(2),
      maxCallbackMs: this._perf.maxCallbackDuration.toFixed(2),
      chunksEmitted: this._perf.chunksEmitted,
      totalTimeInCallbackMs: this._perf.timeSpentInCallback.toFixed(2),
    });
  }

  get state() { return this._state; }
  get performance() { return { ...this._perf }; }

  /**
   * Test if we should use AudioWorklet or fallback.
   * Returns a recommendation object.
   */
  static getRecommendation() {
    const hasAudioWorklet = typeof AudioWorkletNode !== 'undefined';
    const browser = AudioRecorder
      ? AudioRecorder.detectBrowser()
      : { name: 'Unknown' };

    if (hasAudioWorklet) {
      return {
        mode: 'audioworklet',
        reason: 'AudioWorklet available — optimal path (dedicated thread, zero-copy)',
        performance: 'excellent',
      };
    }

    return {
      mode: 'scriptprocessor',
      reason: `AudioWorklet not available in ${browser.name} — using ScriptProcessorNode fallback`,
      performance: browser.name === 'Firefox' ? 'good' : 'acceptable',
      caveats: [
        'Runs on main thread — may cause audio artifacts under heavy UI load',
        'Fixed buffer sizes — less flexible than AudioWorklet',
        'No zero-copy buffer transfer — higher memory overhead',
        'Recommend using larger buffer sizes (4096+) for stability',
      ],
    };
  }

  // ─── Private ───────────────────────────────────────────────

  _createConversionWorker() {
    const blob = new Blob([`
      self.onmessage = function(e) {
        if (e.data.type === 'convert') {
          const float32 = new Float32Array(e.data.data);
          const int16 = new Int16Array(float32.length);
          for (let i = 0; i < float32.length; i++) {
            const s = Math.max(-1, Math.min(1, float32[i]));
            int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
          }
          // Convert to Base64
          const bytes = new Uint8Array(int16.buffer);
          let binary = '';
          const chunkSize = 8192;
          for (let i = 0; i < bytes.length; i += chunkSize) {
            binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
          }
          const base64 = btoa(binary);
          self.postMessage({ id: e.data.id, data: int16.buffer, base64: base64 }, [int16.buffer]);
        }
      };
    `], { type: 'application/javascript' });

    const url = URL.createObjectURL(blob);
    const worker = new Worker(url);

    worker.onerror = (err) => {
      console.error('[FirefoxFallback] Worker error:', err);
    };

    worker.onmessage = (e) => {
      const pcm = new Int16Array(e.data.data);
      this._onPCMChunk({
        data: pcm,
        base64: e.data.base64,
        sampleRate: this._targetSampleRate,
        bitDepth: 16,
        channels: 1,
        sampleCount: pcm.length,
        durationMs: (pcm.length / this._targetSampleRate) * 1000,
        timestamp: Date.now(),
        source: 'firefox-fallback-worker',
      });
    };

    return worker;
  }

  _float32ToInt16(float32) {
    const int16 = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
      const s = Math.max(-1, Math.min(1, float32[i]));
      int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return int16;
  }

  _int16ToBase64(int16) {
    const bytes = new Uint8Array(int16.buffer);
    let binary = '';
    const chunkSize = 8192;
    for (let i = 0; i < bytes.length; i += chunkSize) {
      binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
    }
    return btoa(binary);
  }

  _teardown() {
    if (this._sourceNode) {
      this._sourceNode.disconnect();
      this._sourceNode = null;
    }
    if (this._scriptNode) {
      this._scriptNode.onaudioprocess = null;
      this._scriptNode.disconnect();
      this._scriptNode = null;
    }
    if (this._stream) {
      this._stream.getTracks().forEach((t) => t.stop());
      this._stream = null;
    }
    if (this._audioContext) {
      this._audioContext.close().catch(() => {});
      this._audioContext = null;
    }
    if (this._worker) {
      this._worker.terminate();
      this._worker = null;
    }
  }

  _setState(state) {
    const prev = this._state;
    this._state = state;
    if (prev !== state) {
      this._onStateChange(state);
    }
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = FirefoxFallback;
}
if (typeof window !== 'undefined') {
  window.FirefoxFallback = FirefoxFallback;
}
