/**
 * useAudioRecorder composable
 *
 * Vue 3 Composition API wrapper around the AudioRecorder / AudioWorklet pipeline.
 * Handles microphone capture, real-time PCM conversion, browser detection,
 * permission management, and Firefox fallback.
 *
 * Target output: Int16 PCM, 16000Hz, mono
 *
 * Usage:
 *   const { state, start, stop, pcmChunks, audioLevel } = useAudioRecorder()
 *   await start()
 *   // ... recording ...
 *   stop()
 */
import { ref, computed, readonly, onUnmounted } from 'vue'

// ─── Types ─────────────────────────────────────────────────

export type RecordingState = 'idle' | 'requesting' | 'recording' | 'paused' | 'stopped' | 'error'

export interface BrowserInfo {
  name: string
  version: number | null
  mobile: boolean
}

export interface BrowserCapabilities {
  audioWorklet: boolean
  mediaRecorder: boolean
  getUserMedia: boolean
  sampleRate: number
  browser: BrowserInfo
}

export interface PCMChunk {
  data: Int16Array
  base64: string
  sampleRate: number
  bitDepth: number
  channels: number
  sampleCount: number
  durationMs: number
  timestamp: number
}

export interface RecordingMetrics {
  chunksSent: number
  totalSamplesCaptured: number
  startTime: number
  endTime: number
  durationMs: number
}

export interface UseAudioRecorderOptions {
  targetSampleRate?: number
  chunkInterval?: number
  resampleQuality?: 'low' | 'medium' | 'high'
  maxChunks?: number
  constraints?: MediaStreamConstraints
}

// ─── Browser Detection ─────────────────────────────────────

function detectBrowser(): BrowserInfo {
  if (typeof navigator === 'undefined') {
    return { name: 'Unknown', version: null, mobile: false }
  }
  const ua = navigator.userAgent

  if (/Chrome\//.test(ua) && !/Edge\//.test(ua) && !/OPR\//.test(ua)) {
    const match = ua.match(/Chrome\/(\d+)/)
    return {
      name: 'Chrome',
      version: match && match[1] ? parseInt(match[1], 10) : null,
      mobile: /Mobi|Android/i.test(ua),
    }
  }

  if (/Safari\//.test(ua) && !/Chrome\//.test(ua)) {
    const match = ua.match(/Version\/(\d+)/)
    return {
      name: 'Safari',
      version: match && match[1] ? parseInt(match[1], 10) : null,
      mobile: /iPhone|iPad|iPod/i.test(ua) || (/Macintosh/i.test(ua) && navigator.maxTouchPoints > 1),
    }
  }

  if (/Firefox\//.test(ua)) {
    const match = ua.match(/Firefox\/(\d+)/)
    return {
      name: 'Firefox',
      version: match && match[1] ? parseInt(match[1], 10) : null,
      mobile: /Mobi|Android/i.test(ua),
    }
  }

  if (/Edg\//.test(ua)) {
    const match = ua.match(/Edg\/(\d+)/)
    return {
      name: 'Edge',
      version: match && match[1] ? parseInt(match[1], 10) : null,
      mobile: /Mobi|Android/i.test(ua),
    }
  }

  return { name: 'Unknown', version: null, mobile: false }
}

// ─── PCM Utilities ─────────────────────────────────────────

function float32ToInt16(float32: Float32Array): Int16Array {
  const int16 = new Int16Array(float32.length)
  for (let i = 0; i < float32.length; i++) {
    const sample = float32[i] ?? 0
    const s = Math.max(-1, Math.min(1, sample))
    int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
  }
  return int16
}

function int16ToBase64(int16: Int16Array): string {
  const bytes = new Uint8Array(int16.buffer)
  let binary = ''
  const chunkSize = 8192
  for (let i = 0; i < bytes.length; i += chunkSize) {
    const chunk = bytes.subarray(i, i + chunkSize)
    binary += String.fromCharCode.apply(null, chunk as unknown as number[])
  }
  return btoa(binary)
}

function resampleLinear(source: Float32Array, sourceRate: number, targetRate: number): Float32Array {
  const ratio = sourceRate / targetRate
  const newLength = Math.floor(source.length / ratio)
  const result = new Float32Array(newLength)

  for (let i = 0; i < newLength; i++) {
    const srcIndex = i * ratio
    const srcFloor = Math.floor(srcIndex)
    const srcCeil = Math.min(srcFloor + 1, source.length - 1)
    const fraction = srcIndex - srcFloor
    const sampleFloor = source[srcFloor] ?? 0
    const sampleCeil = source[srcCeil] ?? 0
    result[i] = sampleFloor * (1 - fraction) + sampleCeil * fraction
  }

  return result
}

// ─── Composable ─────────────────────────────────────────────

export function useAudioRecorder(options: UseAudioRecorderOptions = {}) {
  const {
    targetSampleRate = 16000,
    chunkInterval = 100,
    resampleQuality = 'medium',
    maxChunks = 1000,
    constraints = {
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    },
  } = options

  // ─── Reactive State ──────────────────────────────────────

  const state = ref<RecordingState>('idle')
  const error = ref<string | null>(null)
  const permissionGranted = ref<boolean | null>(null)
  const capabilities = ref<BrowserCapabilities>({
    audioWorklet: false,
    mediaRecorder: false,
    getUserMedia: false,
    sampleRate: 0,
    browser: detectBrowser(),
  })

  const pcmChunks = ref<PCMChunk[]>([])
  const audioLevel = ref(0) // 0.0 - 1.0 RMS level
  const currentSampleRate = ref(0)

  const metrics = ref<RecordingMetrics>({
    chunksSent: 0,
    totalSamplesCaptured: 0,
    startTime: 0,
    endTime: 0,
    durationMs: 0,
  })

  // Recording timer
  const elapsedMs = ref(0)
  let timerInterval: ReturnType<typeof setInterval> | null = null

  // ─── Internal State ──────────────────────────────────────

  let audioContext: AudioContext | null = null
  let stream: MediaStream | null = null
  let workletNode: AudioWorkletNode | null = null
  let scriptNode: ScriptProcessorNode | null = null
  let sourceNode: MediaStreamAudioSourceNode | null = null
  let analyserNode: AnalyserNode | null = null
  let animationFrameId: number | null = null

  // ─── Computed ────────────────────────────────────────────

  const isRecording = computed(() => state.value === 'recording')
  const isPaused = computed(() => state.value === 'paused')
  const isIdle = computed(() => state.value === 'idle')
  const hasError = computed(() => state.value === 'error')
  const canRecord = computed(() => state.value === 'idle' || state.value === 'stopped' || state.value === 'paused')
  const canPause = computed(() => state.value === 'recording')
  const canStop = computed(() => state.value === 'recording' || state.value === 'paused')

  const formattedTime = computed(() => {
    const totalSeconds = Math.floor(elapsedMs.value / 1000)
    const minutes = Math.floor(totalSeconds / 60)
    const seconds = totalSeconds % 60
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  })

  const totalDataBytes = computed(() =>
    pcmChunks.value.reduce((sum, chunk) => sum + chunk.data.byteLength, 0)
  )

  const totalSamples = computed(() =>
    pcmChunks.value.reduce((sum, chunk) => sum + chunk.sampleCount, 0)
  )

  const dataRateKbps = computed(() => {
    const durationSec = elapsedMs.value / 1000
    if (durationSec <= 0) return 0
    return totalDataBytes.value / 1024 / durationSec
  })

  // ─── Probe Capabilities ──────────────────────────────────

  function probeCapabilities(): BrowserCapabilities {
    let sampleRate = 0
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
      if (AudioCtx) {
        const ctx = new AudioCtx()
        sampleRate = ctx.sampleRate
        ctx.close()
      }
    } catch {
      // ignore
    }

    return {
      audioWorklet: typeof AudioWorkletNode !== 'undefined',
      mediaRecorder: typeof MediaRecorder !== 'undefined',
      getUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
      sampleRate,
      browser: detectBrowser(),
    }
  }

  // ─── Timer Management ────────────────────────────────────

  function startTimer() {
    stopTimer()
    timerInterval = setInterval(() => {
      if (state.value === 'recording') {
        elapsedMs.value = Date.now() - metrics.value.startTime
      }
    }, 100)
  }

  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval)
      timerInterval = null
    }
  }

  // ─── Audio Level Monitoring ──────────────────────────────

  function startLevelMonitor() {
    if (!analyserNode) return

    const dataArray = new Float32Array(analyserNode.fftSize)

    function updateLevel() {
      if (!analyserNode || (state.value !== 'recording' && state.value !== 'paused')) {
        audioLevel.value = 0
        return
      }

      analyserNode.getFloatTimeDomainData(dataArray)

      let sum = 0
      for (let i = 0; i < dataArray.length; i++) {
        const sample = dataArray[i] ?? 0
        sum += sample * sample
      }
      audioLevel.value = Math.sqrt(sum / dataArray.length)

      animationFrameId = requestAnimationFrame(updateLevel)
    }

    updateLevel()
  }

  function stopLevelMonitor() {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId)
      animationFrameId = null
    }
    audioLevel.value = 0
  }

  // ─── PCM Chunk Handler ───────────────────────────────────

  function handlePCMChunk(chunk: PCMChunk) {
    // Trim old chunks if we exceed max
    if (pcmChunks.value.length >= maxChunks) {
      pcmChunks.value.shift()
    }

    pcmChunks.value.push(chunk)

    metrics.value.chunksSent++
    metrics.value.totalSamplesCaptured += chunk.sampleCount
  }

  // ─── Audio Graph Setup ───────────────────────────────────

  async function setupAudioWorkletGraph(mediaStream: MediaStream) {
    if (!audioContext) throw new Error('AudioContext not created')

    // Load the AudioWorklet module
    await audioContext.audioWorklet.addModule('/PCMConversionWorklet.js')

    // Create AudioWorkletNode
    workletNode = new AudioWorkletNode(audioContext, 'pcm-conversion-processor', {
      numberOfInputs: 1,
      numberOfOutputs: 1,
      processorOptions: {
        targetSampleRate,
        chunkInterval,
        channelCount: 1,
        resampleQuality,
      },
    })

    // Handle PCM chunks from the worklet
    workletNode.port.onmessage = (event) => {
      const msg = event.data
      if (msg.type === 'pcm_chunk') {
        const int16View = new Int16Array(msg.data)
        const base64 = int16ToBase64(int16View)

        handlePCMChunk({
          data: int16View,
          base64,
          sampleRate: msg.sampleRate,
          bitDepth: msg.bitDepth,
          channels: msg.channels,
          sampleCount: msg.sampleCount,
          durationMs: msg.durationMs,
          timestamp: msg.timestamp,
        })
      }
    }

    // Create source from microphone stream
    sourceNode = audioContext.createMediaStreamSource(mediaStream)

    // Create analyser for level monitoring
    analyserNode = audioContext.createAnalyser()
    analyserNode.fftSize = 2048

    // Connect: mic → analyser → worklet
    sourceNode.connect(analyserNode)
    analyserNode.connect(workletNode)
  }

  function setupScriptProcessorGraph(mediaStream: MediaStream) {
    if (!audioContext) throw new Error('AudioContext not created')

    console.warn('[useAudioRecorder] AudioWorklet not available — using ScriptProcessorNode fallback')

    const bufferSize = 4096
    scriptNode = audioContext.createScriptProcessor(bufferSize, 1, 1)

    const sourceRate = audioContext.sampleRate
    const samplesPerChunk = Math.floor(targetSampleRate * (chunkInterval / 1000))
    const ratio = sourceRate / targetSampleRate

    let accumulated = new Float32Array(0)

    scriptNode.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0)
      if (!inputData || inputData.length === 0) return

      // Resample
      const resampled = resampleLinear(inputData, sourceRate, targetSampleRate)

      // Accumulate
      const newAcc = new Float32Array(accumulated.length + resampled.length)
      newAcc.set(accumulated, 0)
      newAcc.set(resampled, accumulated.length)
      accumulated = newAcc

      // Emit chunks
      while (accumulated.length >= samplesPerChunk) {
        const chunk = accumulated.slice(0, samplesPerChunk)
        accumulated = accumulated.slice(samplesPerChunk)

        const pcm = float32ToInt16(chunk)
        const base64 = int16ToBase64(pcm)

        handlePCMChunk({
          data: pcm,
          base64,
          sampleRate: targetSampleRate,
          bitDepth: 16,
          channels: 1,
          sampleCount: pcm.length,
          durationMs: (pcm.length / targetSampleRate) * 1000,
          timestamp: Date.now(),
        })
      }
    }

    // Create source from microphone stream
    sourceNode = audioContext.createMediaStreamSource(mediaStream)

    // Create analyser for level monitoring
    analyserNode = audioContext.createAnalyser()
    analyserNode.fftSize = 2048

    // Connect: mic → analyser → scriptProcessor → destination
    sourceNode.connect(analyserNode)
    analyserNode.connect(scriptNode)
    scriptNode.connect(audioContext.destination)
  }

  // ─── Teardown ────────────────────────────────────────────

  function teardown() {
    stopLevelMonitor()
    stopTimer()

    if (sourceNode) {
      sourceNode.disconnect()
      sourceNode = null
    }

    if (workletNode) {
      workletNode.port.onmessage = null
      workletNode.disconnect()
      workletNode = null
    }

    if (scriptNode) {
      scriptNode.onaudioprocess = null
      scriptNode.disconnect()
      scriptNode = null
    }

    if (analyserNode) {
      analyserNode.disconnect()
      analyserNode = null
    }

    if (stream) {
      stream.getTracks().forEach((track) => track.stop())
      stream = null
    }

    if (audioContext) {
      audioContext.close().catch((e) => console.warn('[useAudioRecorder] Error closing AudioContext:', e))
      audioContext = null
    }
  }

  // ─── Public API ──────────────────────────────────────────

  async function start() {
    if (state.value === 'recording') {
      console.warn('[useAudioRecorder] Already recording')
      return
    }

    // Reset state
    error.value = null
    state.value = 'requesting'
    pcmChunks.value = []
    elapsedMs.value = 0
    metrics.value = {
      chunksSent: 0,
      totalSamplesCaptured: 0,
      startTime: 0,
      endTime: 0,
      durationMs: 0,
    }

    try {
      // Probe capabilities
      capabilities.value = probeCapabilities()

      // Request microphone
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('getUserMedia not supported in this browser')
      }

      stream = await navigator.mediaDevices.getUserMedia(constraints)
      permissionGranted.value = true

      // Create AudioContext
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
      if (!AudioCtx) {
        throw new Error('AudioContext not supported in this browser')
      }
      audioContext = new AudioCtx()
      currentSampleRate.value = audioContext.sampleRate

      // Resume if suspended (iOS Safari)
      if (audioContext.state === 'suspended') {
        await audioContext.resume()
      }

      // Set up audio graph
      if (capabilities.value.audioWorklet) {
        await setupAudioWorkletGraph(stream)
      } else {
        setupScriptProcessorGraph(stream)
      }

      // Start recording
      state.value = 'recording'
      metrics.value.startTime = Date.now()
      startTimer()
      startLevelMonitor()

      console.log('[useAudioRecorder] Recording started — target:', targetSampleRate + 'Hz, source:', audioContext.sampleRate + 'Hz')
    } catch (err: any) {
      state.value = 'error'

      // Classify error
      let errorMessage: string
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errorMessage = '麦克风权限被拒绝，请在浏览器设置中允许麦克风访问'
        permissionGranted.value = false
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        errorMessage = '未检测到麦克风设备，请连接麦克风后重试'
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        errorMessage = '麦克风正被其他应用使用，请关闭其他应用后重试'
      } else if (err.name === 'OverconstrainedError') {
        errorMessage = '麦克风不满足所需约束条件'
      } else {
        errorMessage = `录音错误: ${err.message || err}`
      }

      error.value = errorMessage
      teardown()
      throw new Error(errorMessage)
    }
  }

  function pause() {
    if (state.value !== 'recording') return

    if (workletNode) {
      workletNode.port.postMessage({ command: 'pause' })
    }
    if (audioContext && audioContext.state !== 'suspended') {
      audioContext.suspend()
    }

    state.value = 'paused'
    stopLevelMonitor()
  }

  async function resume() {
    if (state.value !== 'paused') return

    if (audioContext && audioContext.state === 'suspended') {
      await audioContext.resume()
    }
    if (workletNode) {
      workletNode.port.postMessage({ command: 'resume' })
    }

    state.value = 'recording'
    startLevelMonitor()
  }

  function stop() {
    if (state.value === 'idle' || state.value === 'stopped') return

    // Signal worklet to flush
    if (workletNode) {
      workletNode.port.postMessage({ command: 'stop' })
    }

    metrics.value.endTime = Date.now()
    metrics.value.durationMs = metrics.value.endTime - metrics.value.startTime
    elapsedMs.value = metrics.value.durationMs

    teardown()
    state.value = 'stopped'
  }

  function cancel() {
    teardown()
    pcmChunks.value = []
    state.value = 'idle'
    elapsedMs.value = 0
  }

  function reset() {
    cancel()
    error.value = null
    permissionGranted.value = null
  }

  /**
   * Get all PCM data as a single concatenated Base64 string.
   * Useful for sending the complete recording.
   */
  function getAllPCMBase64(): string {
    if (pcmChunks.value.length === 0) return ''

    // Concatenate all Int16 data
    const totalLength = pcmChunks.value.reduce((sum, chunk) => sum + chunk.data.length, 0)
    const combined = new Int16Array(totalLength)
    let offset = 0
    for (const chunk of pcmChunks.value) {
      combined.set(chunk.data, offset)
      offset += chunk.data.length
    }

    return int16ToBase64(combined)
  }

  /**
   * Get all PCM data as a single Int16Array.
   */
  function getAllPCMData(): Int16Array {
    if (pcmChunks.value.length === 0) return new Int16Array(0)

    const totalLength = pcmChunks.value.reduce((sum, chunk) => sum + chunk.data.length, 0)
    const combined = new Int16Array(totalLength)
    let offset = 0
    for (const chunk of pcmChunks.value) {
      combined.set(chunk.data, offset)
      offset += chunk.data.length
    }

    return combined
  }

  // ─── Cleanup ─────────────────────────────────────────────

  onUnmounted(() => {
    if (state.value === 'recording' || state.value === 'paused') {
      cancel()
    }
  })

  // ─── Return ──────────────────────────────────────────────

  return {
    // State
    state: readonly(state),
    error: readonly(error),
    permissionGranted: readonly(permissionGranted),
    capabilities: readonly(capabilities),
    currentSampleRate: readonly(currentSampleRate),

    // Recording data
    pcmChunks: readonly(pcmChunks),
    audioLevel: readonly(audioLevel),
    elapsedMs: readonly(elapsedMs),
    formattedTime,

    // Metrics
    metrics: readonly(metrics),
    totalDataBytes,
    totalSamples,
    dataRateKbps,

    // Computed
    isRecording,
    isPaused,
    isIdle,
    hasError,
    canRecord,
    canPause,
    canStop,

    // Actions
    start,
    pause,
    resume,
    stop,
    cancel,
    reset,

    // Data access
    getAllPCMBase64,
    getAllPCMData,

    // Capabilities
    probeCapabilities,
  }
}
