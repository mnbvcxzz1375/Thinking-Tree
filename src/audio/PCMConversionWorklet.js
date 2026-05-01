/**
 * PCMConversionWorklet.js
 * AudioWorklet processor for capturing raw audio and converting to Int16 PCM.
 *
 * Pipeline: Float32Array (input) → Downsample to 16kHz → Int16 PCM → MessagePort (main thread)
 *
 * This runs on the high-priority AudioWorklet thread, ensuring zero-jitter capture.
 *
 * Key features:
 * - Zero-latency pass-through (passes audio through to output)
 * - Configurable target sample rate (default: 16000)
 * - Accumulates buffers and sends them back via MessagePort
 * - Supports real-time streaming via configurable chunk interval
 */

class PCMConversionProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super(options);

    // Configurable parameters via processorOptions
    this._targetSampleRate = (options && options.processorOptions && options.processorOptions.targetSampleRate) || 16000;
    this._chunkInterval = (options && options.processorOptions && options.processorOptions.chunkInterval) || 100; // ms
    this._channelCount = (options && options.processorOptions && options.processorOptions.channelCount) || 1;
    this._resampleQuality = (options && options.processorOptions && options.processorOptions.resampleQuality) || 'medium';

    // State
    this._buffer = new Float32Array(0);
    this._chunkCounter = 0;
    this._isCapturing = true;

    // Resampling state
    this._resampleRatio = sampleRate / this._targetSampleRate;
    this._resampleAccumulator = 0;

    // Port message handler — main thread can send commands
    this.port.onmessage = (event) => {
      const msg = event.data;
      switch (msg.command) {
        case 'stop':
          this._isCapturing = false;
          // Flush remaining buffer
          this._flushBuffer();
          break;
        case 'pause':
          this._isCapturing = false;
          break;
        case 'resume':
          this._isCapturing = true;
          break;
        case 'set_target_rate':
          this._targetSampleRate = msg.value;
          this._resampleRatio = sampleRate / this._targetSampleRate;
          break;
        case 'get_info':
          this.port.postMessage({
            type: 'info',
            sampleRate: sampleRate,
            targetSampleRate: this._targetSampleRate,
            resampleRatio: this._resampleRatio,
            channelCount: this._channelCount,
          });
          break;
        default:
          break;
      }
    };
  }

  /**
   * Main processing loop — called by the Web Audio API every render quantum (128 frames).
   *
   * @param {Float32Array[][]} inputs  — inputs[channelIndex][sampleIndex]
   * @param {Float32Array[][]} outputs — outputs[channelIndex][sampleIndex]
   * @param {Object} parameters — AudioParam automation data
   * @returns {boolean} — keep processor alive
   */
  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || input.length === 0 || !this._isCapturing) {
      // Pass-through silence
      return true;
    }

    // Use the first channel (mono)
    const channelData = input[0];
    if (!channelData || channelData.length === 0) {
      return true;
    }

    // Accumulate raw audio samples
    this._accumulateSamples(channelData);

    // Decide when to send a chunk based on time interval
    const currentChunk = Math.floor((currentTime * 1000) / this._chunkInterval);
    if (currentChunk > this._chunkCounter) {
      this._chunkCounter = currentChunk;
      this._sendChunk();
    }

    // Pass-through: copy input to output so the user hears their own voice
    // (optional — can be disabled for echo prevention)
    const output = outputs[0];
    if (output && output.length > 0) {
      for (let ch = 0; ch < Math.min(input.length, output.length); ch++) {
        const outCh = output[ch];
        const inCh = input[ch];
        if (outCh && inCh) {
          outCh.set(inCh);
        }
      }
    }

    // Always keep the processor alive
    return true;
  }

  /**
   * Accumulate raw Float32 samples into the internal buffer.
   */
  _accumulateSamples(channelData) {
    const newBuffer = new Float32Array(this._buffer.length + channelData.length);
    newBuffer.set(this._buffer, 0);
    newBuffer.set(channelData, this._buffer.length);
    this._buffer = newBuffer;
  }

  /**
   * Downsample accumulated buffer from source rate to target rate,
   * convert to Int16 PCM, and send to main thread.
   *
   * Resampling strategy depends on quality setting:
   * - 'low': simple decimation (every Nth sample)
   * - 'medium': linear interpolation
   * - 'high': linear interpolation with anti-aliasing (simple moving average pre-filter)
   */
  _sendChunk() {
    if (this._buffer.length === 0) return;

    const sourceRate = sampleRate;
    const targetRate = this._targetSampleRate;

    if (sourceRate === targetRate) {
      // No resampling needed — direct conversion
      const pcm = this._float32ToInt16(this._buffer);
      this._postPCM(pcm);
    } else {
      // Downsample
      const ratio = sourceRate / targetRate;
      const outputLength = Math.floor(this._buffer.length / ratio);
      const resampled = new Float32Array(outputLength);

      if (this._resampleQuality === 'low') {
        // Simple decimation
        for (let i = 0; i < outputLength; i++) {
          resampled[i] = this._buffer[Math.floor(i * ratio)];
        }
      } else if (this._resampleQuality === 'medium') {
        // Linear interpolation
        for (let i = 0; i < outputLength; i++) {
          const srcIndex = i * ratio;
          const srcIndexFloor = Math.floor(srcIndex);
          const srcIndexCeil = Math.min(srcIndexFloor + 1, this._buffer.length - 1);
          const fraction = srcIndex - srcIndexFloor;
          resampled[i] = this._buffer[srcIndexFloor] * (1 - fraction) + this._buffer[srcIndexCeil] * fraction;
        }
      } else {
        // 'high': linear interpolation with anti-aliasing pre-filter
        const filtered = this._applyAntiAliasFilter(this._buffer, ratio);
        for (let i = 0; i < outputLength; i++) {
          const srcIndex = i * ratio;
          const srcIndexFloor = Math.floor(srcIndex);
          const srcIndexCeil = Math.min(srcIndexFloor + 1, filtered.length - 1);
          const fraction = srcIndex - srcIndexFloor;
          resampled[i] = filtered[srcIndexFloor] * (1 - fraction) + filtered[srcIndexCeil] * fraction;
        }
      }

      const pcm = this._float32ToInt16(resampled);
      this._postPCM(pcm);
    }

    // Clear buffer after sending
    this._buffer = new Float32Array(0);
  }

  /**
   * Simple moving-average anti-aliasing filter.
   * Window size = floor(ratio) to attenuate frequencies above the new Nyquist frequency.
   */
  _applyAntiAliasFilter(samples, ratio) {
    const windowSize = Math.max(2, Math.floor(ratio));
    const halfWindow = Math.floor(windowSize / 2);
    const output = new Float32Array(samples.length);

    for (let i = 0; i < samples.length; i++) {
      let sum = 0;
      let count = 0;
      for (let j = -halfWindow; j <= halfWindow; j++) {
        const idx = i + j;
        if (idx >= 0 && idx < samples.length) {
          sum += samples[idx];
          count++;
        }
      }
      output[i] = count > 0 ? sum / count : samples[i];
    }

    return output;
  }

  /**
   * Convert Float32Array (-1.0 to 1.0) to Int16Array PCM.
   * Clamps values and applies optional gain before conversion.
   */
  _float32ToInt16(float32Array) {
    const length = float32Array.length;
    const int16Array = new Int16Array(length);

    for (let i = 0; i < length; i++) {
      // Clamp to [-1.0, 1.0] to prevent distortion
      const clamped = Math.max(-1.0, Math.min(1.0, float32Array[i]));
      // Convert to 16-bit integer range [-32768, 32767]
      int16Array[i] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7FFF;
    }

    return int16Array;
  }

  /**
   * Flush any remaining buffer data — called on stop.
   */
  _flushBuffer() {
    if (this._buffer.length > 0) {
      this._sendChunk();
    }
  }

  /**
   * Post PCM data to the main thread via MessagePort.
   * Includes metadata about the chunk for streaming coordination.
   */
  _postPCM(pcmData) {
    this.port.postMessage({
      type: 'pcm_chunk',
      data: pcmData.buffer,          // Transferable ArrayBuffer
      sampleRate: this._targetSampleRate,
      bitDepth: 16,
      channels: this._channelCount,
      sampleCount: pcmData.length,
      durationMs: (pcmData.length / this._targetSampleRate) * 1000,
      timestamp: Date.now(),
    }, [pcmData.buffer]); // Transfer ownership for zero-copy
  }
}

// Register the processor under a name used by AudioWorkletNode
registerProcessor('pcm-conversion-processor', PCMConversionProcessor);
