/**
 * AudioRecorder.js
 * Main audio recorder class — orchestrates microphone capture, PCM conversion, and streaming.
 *
 * Supports:
 * - AudioWorklet (Chrome 66+, Edge 79+, Safari 14.1+) — preferred path
 * - ScriptProcessorNode (Firefox fallback)
 * - Automatic browser detection and feature negotiation
 * - Real-time PCM streaming via callbacks
 * - Base64 encoding for transmission
 * - Permission state management
 *
 * Target output: Int16 PCM, 16000Hz, mono
 *
 * Usage:
 *   const recorder = new AudioRecorder({ onPCMChunk: (chunk) => { ... } });
 *   await recorder.start();
 *   // ... recording ...
 *   recorder.stop();
 */

class AudioRecorder {
  /**
   * @param {Object} options
   * @param {Function} options.onPCMChunk       - Called with each PCM chunk: { data: Int16Array, base64: string, sampleRate, duration, timestamp }
   * @param {Function} options.onStateChange    - Called on state changes: (state) => {}
   * @param {Function} options.onError          - Called on errors: (error) => {}
   * @param {Function} options.onPermission     - Called on permission result: (granted) => {}
   * @param {number}   options.targetSampleRate - Default: 16000
   * @param {number}   options.chunkInterval    - Milliseconds between PCM chunks. Default: 100
   * @param {string}   options.resampleQuality  - 'low' | 'medium' | 'high'. Default: 'medium'
   * @param {Object}   options.constraints      - Override getUserMedia constraints
   */
  constructor(options = {}) {
    this._onPCMChunk = options.onPCMChunk || (() => {});
    this._onStateChange = options.onStateChange || (() => {});
    this._onError = options.onError || (() => {});
    this._onPermission = options.onPermission || (() => {});

    this._targetSampleRate = options.targetSampleRate || 16000;
    this._chunkInterval = options.chunkInterval || 100;
    this._resampleQuality = options.resampleQuality || 'medium';
    this._constraints = options.constraints || {
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    };

    // Internal state
    this._state = 'idle';                 // idle | requesting | recording | paused | stopped | error
    this._audioContext = null;
    this._stream = null;
    this._workletNode = null;
    this._scriptNode = null;
    this._sourceNode = null;

    // Browser capability flags — populated during start()
    this._capabilities = {
      audioWorklet: false,
      mediaRecorder: false,
      getUserMedia: false,
      sampleRate: 0,
      browser: this._detectBrowser(),
    };

    // Performance metrics
    this._metrics = {
      chunksSent: 0,
      totalSamplesCaptured: 0,
      startTime: 0,
      endTime: 0,
    };

    // Event cleanup
    this._cleanupFns = [];
  }

  // ─── Public API ────────────────────────────────────────────

  /**
   * Start recording: request permissions, set up audio graph, begin capture.
   */
  async start() {
    if (this._state === 'recording') {
      console.warn('[AudioRecorder] Already recording');
      return;
    }

    this._setState('requesting');

    try {
      // Step 1: Request microphone permission
      const stream = await this._requestMicrophone();
      this._stream = stream;

      // Step 2: Detect browser capabilities
      this._capabilities = this._probeCapabilities();
      console.log('[AudioRecorder] Browser capabilities:', this._capabilities);

      // Step 3: Create AudioContext
      this._audioContext = this._createAudioContext();

      // Step 4: Set up the audio graph
      if (this._capabilities.audioWorklet) {
        await this._setupAudioWorkletGraph(stream);
      } else {
        this._setupScriptProcessorGraph(stream);
      }

      // Step 5: Begin capture
      this._setState('recording');
      this._metrics.startTime = Date.now();

      console.log('[AudioRecorder] Recording started — target:', this._targetSampleRate + 'Hz, source:', this._audioContext.sampleRate + 'Hz');
    } catch (err) {
      this._setState('error');
      this._onError(err);
      throw err;
    }
  }

  /**
   * Pause recording without tearing down the audio graph.
   */
  pause() {
    if (this._state !== 'recording') return;

    if (this._workletNode) {
      this._workletNode.port.postMessage({ command: 'pause' });
    }
    if (this._audioContext && this._audioContext.state !== 'suspended') {
      this._audioContext.suspend();
    }
    this._setState('paused');
  }

  /**
   * Resume a paused recording.
   */
  async resume() {
    if (this._state !== 'paused') return;

    if (this._audioContext && this._audioContext.state === 'suspended') {
      await this._audioContext.resume();
    }
    if (this._workletNode) {
      this._workletNode.port.postMessage({ command: 'resume' });
    }
    this._setState('recording');
  }

  /**
   * Stop recording, flush remaining data, tear down audio graph.
   */
  stop() {
    if (this._state === 'idle' || this._state === 'stopped') return;

    // Signal the worklet to flush and stop
    if (this._workletNode) {
      this._workletNode.port.postMessage({ command: 'stop' });
    }

    this._teardown();
    this._metrics.endTime = Date.now();
    this._setState('stopped');

    console.log('[AudioRecorder] Stopped. Chunks:', this._metrics.chunksSent,
      'Duration:', (this._metrics.endTime - this._metrics.startTime) + 'ms');
  }

  /**
   * Cancel recording (no final flush).
   */
  cancel() {
    this._teardown();
    this._setState('stopped');
  }

  /** Current state: idle | requesting | recording | paused | stopped | error */
  get state() {
    return this._state;
  }

  /** Browser capability info */
  get capabilities() {
    return { ...this._capabilities };
  }

  /** Performance metrics */
  get metrics() {
    return { ...this._metrics };
  }

  /** Check if AudioWorklet is available */
  static isAudioWorkletSupported() {
    return typeof AudioWorkletNode !== 'undefined';
  }

  /** Check if getUserMedia is available */
  static isGetUserMediaSupported() {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  }

  /** Check if MediaRecorder is available */
  static isMediaRecorderSupported() {
    return typeof MediaRecorder !== 'undefined';
  }

  /** Get complete browser detection info */
  static detectBrowser() {
    const ua = navigator.userAgent;

    // Chrome
    if (/Chrome\//.test(ua) && !/Edge\//.test(ua) && !/OPR\//.test(ua)) {
      const match = ua.match(/Chrome\/(\d+)/);
      return {
        name: 'Chrome',
        version: match ? parseInt(match[1], 10) : null,
        mobile: /Mobi|Android/i.test(ua),
      };
    }

    // Safari
    if (/Safari\//.test(ua) && !/Chrome\//.test(ua)) {
      const match = ua.match(/Version\/(\d+)/);
      return {
        name: 'Safari',
        version: match ? parseInt(match[1], 10) : null,
        mobile: /iPhone|iPad|iPod/i.test(ua) || (/Macintosh/i.test(ua) && navigator.maxTouchPoints > 1),
      };
    }

    // Firefox
    if (/Firefox\//.test(ua)) {
      const match = ua.match(/Firefox\/(\d+)/);
      return {
        name: 'Firefox',
        version: match ? parseInt(match[1], 10) : null,
        mobile: /Mobi|Android/i.test(ua),
      };
    }

    // Edge (Chromium)
    if (/Edg\//.test(ua)) {
      const match = ua.match(/Edg\/(\d+)/);
      return {
        name: 'Edge',
        version: match ? parseInt(match[1], 10) : null,
        mobile: /Mobi|Android/i.test(ua),
      };
    }

    return { name: 'Unknown', version: null, mobile: false };
  }

  // ─── Private: Audio Graph Setup ────────────────────────────

  /**
   * Set up the AudioWorklet-based audio graph.
   * Chrome 66+, Edge 79+, Safari 14.1+, Opera 53+
   */
  async _setupAudioWorkletGraph(stream) {
    // Load the AudioWorklet module
    await this._audioContext.audioWorklet.addModule('PCMConversionWorklet.js');

    // Create AudioWorkletNode
    this._workletNode = new AudioWorkletNode(this._audioContext, 'pcm-conversion-processor', {
      numberOfInputs: 1,
      numberOfOutputs: 1,
      processorOptions: {
        targetSampleRate: this._targetSampleRate,
        chunkInterval: this._chunkInterval,
        channelCount: 1,
        resampleQuality: this._resampleQuality,
      },
    });

    // Handle PCM chunks from the worklet
    this._workletNode.port.onmessage = (event) => {
      const msg = event.data;
      if (msg.type === 'pcm_chunk') {
        this._handlePCMChunk(msg);
      } else if (msg.type === 'info') {
        console.log('[AudioRecorder] Worklet info:', msg);
      }
    };

    // Create source from microphone stream
    this._sourceNode = this._audioContext.createMediaStreamSource(stream);

    // Connect: mic → worklet → destination (pass-through for monitoring)
    this._sourceNode.connect(this._workletNode);
    // Connect to destination only if we want the user to hear themselves
    // Disabled by default to prevent feedback on mobile
    // this._workletNode.connect(this._audioContext.destination);
  }

  /**
   * Set up ScriptProcessorNode-based audio graph (Firefox fallback).
   */
  _setupScriptProcessorGraph(stream) {
    console.warn('[AudioRecorder] AudioWorklet not available — using ScriptProcessorNode fallback (Firefox mode)');

    // ScriptProcessorNode buffer size: must be a power of 2 (256, 512, 1024, 2048, 4096, 8192, 16384)
    const bufferSize = 4096;
    this._scriptNode = this._audioContext.createScriptProcessor(bufferSize, 1, 1);

    // Resampling state
    const sourceRate = this._audioContext.sampleRate;
    const targetRate = this._targetSampleRate;

    // Accumulation buffer for chunk-based emission
    let accumulated = new Float32Array(0);
    const samplesPerChunk = Math.floor(targetRate * (this._chunkInterval / 1000));

    this._scriptNode.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);
      if (!inputData || inputData.length === 0) return;

      // Step 1: Resample to target rate (linear interpolation)
      const resampled = this._resampleLinear(inputData, sourceRate, targetRate);

      // Step 2: Accumulate
      const newAcc = new Float32Array(accumulated.length + resampled.length);
      newAcc.set(accumulated, 0);
      newAcc.set(resampled, accumulated.length);
      accumulated = newAcc;

      // Step 3: Emit chunks at the configured interval
      if (accumulated.length >= samplesPerChunk) {
        const chunk = accumulated.slice(0, samplesPerChunk);
        const pcm = this._float32ToInt16(chunk);

        const msg = {
          type: 'pcm_chunk',
          data: pcm.buffer,
          sampleRate: targetRate,
          bitDepth: 16,
          channels: 1,
          sampleCount: pcm.length,
          durationMs: (pcm.length / targetRate) * 1000,
          timestamp: Date.now(),
        };

        this._handlePCMChunk(msg);

        // Keep remainder
        accumulated = accumulated.slice(samplesPerChunk);
      }
    };

    // Create source from microphone stream
    this._sourceNode = this._audioContext.createMediaStreamSource(stream);

    // Connect: mic → scriptProcessorNode → destination
    this._sourceNode.connect(this._scriptNode);
    this._scriptNode.connect(this._audioContext.destination);
  }

  // ─── Private: PCM Handling ─────────────────────────────────

  /**
   * Process an incoming PCM chunk from the worklet/scriptProcessor.
   * Creates an Int16Array view and Base64 encodes it for transmission.
   */
  _handlePCMChunk(msg) {
    const int16View = new Int16Array(msg.data);
    const base64 = this._int16ToBase64(int16View);

    // Update metrics
    this._metrics.chunksSent++;
    this._metrics.totalSamplesCaptured += msg.sampleCount;

    // Fire callback
    this._onPCMChunk({
      data: int16View,
      base64: base64,
      sampleRate: msg.sampleRate,
      bitDepth: msg.bitDepth,
      channels: msg.channels,
      sampleCount: msg.sampleCount,
      durationMs: msg.durationMs,
      timestamp: msg.timestamp,
    });
  }

  // ─── Private: Setup & Teardown ─────────────────────────────

  /**
   * Request microphone access from the user.
   * Also checks navigator.permissions if available.
   */
  async _requestMicrophone() {
    // Check if getUserMedia is available
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      this._onPermission(false);
      throw new Error('getUserMedia not supported in this browser');
    }

    // Check/query permission state (may not be available in all browsers)
    try {
      if (navigator.permissions && navigator.permissions.query) {
        const permissionStatus = await navigator.permissions.query({ name: 'microphone' });
        console.log('[AudioRecorder] Microphone permission state:', permissionStatus.state);

        // Listen for permission changes
        const onPermissionChange = () => {
          console.log('[AudioRecorder] Microphone permission changed to:', permissionStatus.state);
        };
        permissionStatus.addEventListener('change', onPermissionChange);
        this._cleanupFns.push(() => permissionStatus.removeEventListener('change', onPermissionChange));
      }
    } catch (e) {
      // navigator.permissions.query for 'microphone' not available (e.g., Firefox)
      console.log('[AudioRecorder] Permission query not available, will request directly');
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia(this._constraints);
      console.log('[AudioRecorder] Microphone access granted. Tracks:', stream.getAudioTracks().length);

      // Log track info
      stream.getAudioTracks().forEach((track, i) => {
        console.log(`[AudioRecorder] Track ${i}:`, {
          label: track.label,
          kind: track.kind,
          settings: track.getSettings ? track.getSettings() : 'N/A',
        });

        // Listen for track ended
        track.addEventListener('ended', () => {
          console.warn('[AudioRecorder] Audio track ended unexpectedly');
          if (this._state === 'recording') {
            this._setState('error');
            this._onError(new Error('Audio track ended unexpectedly'));
          }
        });
      });

      this._onPermission(true);
      return stream;
    } catch (err) {
      // Classify the error type
      let errorMessage;
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errorMessage = 'Microphone permission denied by user';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        errorMessage = 'No microphone device found';
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        errorMessage = 'Microphone is already in use by another application';
      } else if (err.name === 'OverconstrainedError') {
        errorMessage = 'Microphone does not satisfy requested constraints';
      } else {
        errorMessage = `Microphone access error: ${err.name} — ${err.message}`;
      }

      this._onPermission(false);
      throw new Error(errorMessage);
    }
  }

  /**
   * Create AudioContext with browser-specific settings.
   */
  _createAudioContext() {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) {
      throw new Error('AudioContext not supported in this browser');
    }

    const ctx = new AudioCtx({
      // Request specific sample rate if available
      sampleRate: this._targetSampleRate >= 44100 ? undefined : undefined, // Let browser choose
    });

    // Log actual sample rate (browser may differ from request)
    console.log('[AudioRecorder] AudioContext created. SampleRate:', ctx.sampleRate, 'State:', ctx.state);

    // iOS Safari: AudioContext is suspended until user gesture
    if (ctx.state === 'suspended') {
      console.log('[AudioRecorder] AudioContext suspended — will resume on user gesture');
    }

    return ctx;
  }

  /**
   * Tear down the audio graph and release resources.
   */
  _teardown() {
    // Disconnect and clean up nodes
    if (this._sourceNode) {
      this._sourceNode.disconnect();
      this._sourceNode = null;
    }

    if (this._workletNode) {
      this._workletNode.port.onmessage = null;
      this._workletNode.disconnect();
      this._workletNode = null;
    }

    if (this._scriptNode) {
      this._scriptNode.onaudioprocess = null;
      this._scriptNode.disconnect();
      this._scriptNode = null;
    }

    // Stop all media tracks
    if (this._stream) {
      this._stream.getTracks().forEach((track) => track.stop());
      this._stream = null;
    }

    // Close AudioContext
    if (this._audioContext) {
      this._audioContext.close().catch((e) => console.warn('[AudioRecorder] Error closing AudioContext:', e));
      this._audioContext = null;
    }

    // Clean up event listeners
    this._cleanupFns.forEach((fn) => {
      try { fn(); } catch (e) { /* ignore */ }
    });
    this._cleanupFns = [];
  }

  // ─── Private: Utilities ────────────────────────────────────

  /**
   * Detect browser name and version from user agent.
   */
  _detectBrowser() {
    return AudioRecorder.detectBrowser();
  }

  /**
   * Probe browser capabilities at runtime.
   */
  _probeCapabilities() {
    return {
      audioWorklet: typeof AudioWorkletNode !== 'undefined',
      mediaRecorder: typeof MediaRecorder !== 'undefined',
      getUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
      sampleRate: this._audioContext ? this._audioContext.sampleRate : 0,
      browser: this._capabilities.browser,
    };
  }

  /**
   * Linear resampling: converts audio from sourceRate to targetRate.
   *
   * For Firefox fallback — AudioWorklet handles resampling on the worklet thread.
   */
  _resampleLinear(source, sourceRate, targetRate) {
    const ratio = sourceRate / targetRate;
    const newLength = Math.floor(source.length / ratio);
    const result = new Float32Array(newLength);

    for (let i = 0; i < newLength; i++) {
      const srcIndex = i * ratio;
      const srcFloor = Math.floor(srcIndex);
      const srcCeil = Math.min(srcFloor + 1, source.length - 1);
      const fraction = srcIndex - srcFloor;
      result[i] = source[srcFloor] * (1 - fraction) + source[srcCeil] * fraction;
    }

    return result;
  }

  /**
   * Convert Float32Array to Int16Array.
   */
  _float32ToInt16(float32) {
    const length = float32.length;
    const int16 = new Int16Array(length);
    for (let i = 0; i < length; i++) {
      const s = Math.max(-1, Math.min(1, float32[i]));
      int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return int16;
  }

  /**
   * Convert Int16Array to Base64 string for transmission.
   */
  _int16ToBase64(int16Array) {
    // Convert to byte array (little-endian, 16-bit)
    const bytes = new Uint8Array(int16Array.buffer);
    let binary = '';
    const chunkSize = 8192; // Process in chunks to avoid stack overflow
    for (let i = 0; i < bytes.length; i += chunkSize) {
      const chunk = bytes.subarray(i, i + chunkSize);
      binary += String.fromCharCode.apply(null, chunk);
    }
    return btoa(binary);
  }

  /**
   * Update internal state and fire callback.
   */
  _setState(state) {
    const prev = this._state;
    this._state = state;
    if (prev !== state) {
      this._onStateChange(state);
    }
  }
}

// Export for module usage (works in both ESM and non-module contexts)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AudioRecorder;
}
if (typeof window !== 'undefined') {
  window.AudioRecorder = AudioRecorder;
}
