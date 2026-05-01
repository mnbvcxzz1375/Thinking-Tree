<script setup lang="ts">
/**
 * AudioRecorder.vue
 *
 * Audio recording component with real-time PCM conversion.
 * Supports AudioWorklet (Chrome, Safari, Edge) and ScriptProcessorNode fallback (Firefox).
 *
 * Features:
 * - Record/Stop/Pause/Resume controls with visual feedback
 * - Real-time audio level visualization
 * - Recording timer
 * - Browser capability detection
 * - Error handling with user-friendly messages
 * - PCM streaming with Base64 encoding
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useAudioRecorder } from '../composables/useAudioRecorder'
import type { PCMChunk } from '../composables/useAudioRecorder'

// ─── Props & Emits ──────────────────────────────────────────

interface Props {
  /** Target sample rate for PCM output (default: 16000) */
  targetSampleRate?: number
  /** Interval between PCM chunks in ms (default: 100) */
  chunkInterval?: number
  /** Maximum recording duration in seconds (0 = unlimited) */
  maxDurationSec?: number
  /** Show detailed stats panel */
  showStats?: boolean
  /** Show browser capability info */
  showCapabilities?: boolean
  /** Compact mode for embedding in smaller spaces */
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  targetSampleRate: 16000,
  chunkInterval: 100,
  maxDurationSec: 120,
  showStats: false,
  showCapabilities: false,
  compact: false,
})

const emit = defineEmits<{
  /** Fired when a new PCM chunk is available */
  'pcm-chunk': [chunk: PCMChunk]
  /** Fired when recording state changes */
  'state-change': [state: string]
  /** Fired when recording stops with all data */
  'recording-complete': [data: { base64: string; pcm: Int16Array; durationMs: number; sampleCount: number }]
  /** Fired on error */
  error: [message: string]
}>()

// ─── Composable ─────────────────────────────────────────────

const recorder = useAudioRecorder({
  targetSampleRate: props.targetSampleRate,
  chunkInterval: props.chunkInterval,
  maxChunks: 2000,
})

// ─── Local State ────────────────────────────────────────────

const canvasRef = ref<HTMLCanvasElement | null>(null)
let canvasCtx: CanvasRenderingContext2D | null = null
let drawFrameId: number | null = null

// Level history for smooth visualization
const levelHistory = ref<number[]>([])
const MAX_LEVEL_HISTORY = 60

// ─── Computed ───────────────────────────────────────────────

const levelPercent = computed(() => Math.min(100, Math.round(recorder.audioLevel.value * 300)))

const isMaxDurationReached = computed(() => {
  if (props.maxDurationSec <= 0) return false
  return recorder.elapsedMs.value / 1000 >= props.maxDurationSec
})

const statusLabel = computed(() => {
  switch (recorder.state.value) {
    case 'idle': return '准备就绪'
    case 'requesting': return '请求权限中...'
    case 'recording': return '录音中'
    case 'paused': return '已暂停'
    case 'stopped': return '录音完成'
    case 'error': return '出错了'
    default: return ''
  }
})

const statusColor = computed(() => {
  switch (recorder.state.value) {
    case 'idle': return '#9ca3af'
    case 'requesting': return '#f59e0b'
    case 'recording': return '#ef4444'
    case 'paused': return '#f59e0b'
    case 'stopped': return '#10b981'
    case 'error': return '#ef4444'
    default: return '#9ca3af'
  }
})

// ─── Canvas Visualization ───────────────────────────────────

function initCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return

  canvas.width = canvas.clientWidth * (window.devicePixelRatio || 1)
  canvas.height = canvas.clientHeight * (window.devicePixelRatio || 1)
  canvasCtx = canvas.getContext('2d')

  window.addEventListener('resize', handleResize)
}

function handleResize() {
  const canvas = canvasRef.value
  if (!canvas) return
  canvas.width = canvas.clientWidth * (window.devicePixelRatio || 1)
  canvas.height = canvas.clientHeight * (window.devicePixelRatio || 1)
}

function drawVisualization() {
  const canvas = canvasRef.value
  const ctx = canvasCtx
  if (!canvas || !ctx) return

  const dpr = window.devicePixelRatio || 1
  const width = canvas.width
  const height = canvas.height

  ctx.clearRect(0, 0, width, height)

  // Background
  ctx.fillStyle = 'rgba(0, 0, 0, 0.03)'
  ctx.fillRect(0, 0, width, height)

  // Center line
  ctx.strokeStyle = 'rgba(0, 0, 0, 0.06)'
  ctx.lineWidth = 1 * dpr
  ctx.beginPath()
  ctx.moveTo(0, height / 2)
  ctx.lineTo(width, height / 2)
  ctx.stroke()

  if (levelHistory.value.length < 2) {
    drawFrameId = requestAnimationFrame(drawVisualization)
    return
  }

  // Draw level bars
  const barCount = levelHistory.value.length
  const barWidth = width / MAX_LEVEL_HISTORY
  const gap = 2 * dpr

  for (let i = 0; i < barCount; i++) {
    const level = levelHistory.value[i] ?? 0
    const x = (MAX_LEVEL_HISTORY - barCount + i) * barWidth
    const barHeight = Math.max(2 * dpr, level * height * 0.8)
    const y = (height - barHeight) / 2

    // Gradient based on level
    const hue = level > 0.7 ? 0 : level > 0.3 ? 30 : 145
    const saturation = 70 + level * 30
    const lightness = 55 - level * 15
    ctx.fillStyle = `hsl(${hue}, ${saturation}%, ${lightness}%)`

    // Rounded bar
    const radius = Math.min(barWidth / 2 - gap / 2, 4 * dpr)
    const bw = barWidth - gap
    ctx.beginPath()
    ctx.moveTo(x + radius, y)
    ctx.lineTo(x + bw - radius, y)
    ctx.quadraticCurveTo(x + bw, y, x + bw, y + radius)
    ctx.lineTo(x + bw, y + barHeight - radius)
    ctx.quadraticCurveTo(x + bw, y + barHeight, x + bw - radius, y + barHeight)
    ctx.lineTo(x + radius, y + barHeight)
    ctx.quadraticCurveTo(x, y + barHeight, x, y + barHeight - radius)
    ctx.lineTo(x, y + radius)
    ctx.quadraticCurveTo(x, y, x + radius, y)
    ctx.closePath()
    ctx.fill()
  }

  drawFrameId = requestAnimationFrame(drawVisualization)
}

// ─── Watchers ───────────────────────────────────────────────

watch(() => recorder.audioLevel.value, (level) => {
  levelHistory.value.push(level)
  if (levelHistory.value.length > MAX_LEVEL_HISTORY) {
    levelHistory.value.shift()
  }
})

watch(() => recorder.state.value, (newState) => {
  emit('state-change', newState)

  if (newState === 'recording') {
    levelHistory.value = []
    drawVisualization()
  } else if (newState === 'stopped') {
    if (drawFrameId) {
      cancelAnimationFrame(drawFrameId)
      drawFrameId = null
    }

    // Emit recording complete
    const pcm = recorder.getAllPCMData()
    const base64 = recorder.getAllPCMBase64()
    emit('recording-complete', {
      base64,
      pcm,
      durationMs: recorder.metrics.value.durationMs,
      sampleCount: recorder.totalSamples.value,
    })
  } else if (newState === 'error') {
    emit('error', recorder.error.value || 'Unknown error')
  }
})

watch(() => recorder.pcmChunks.value.length, () => {
  const chunks = recorder.pcmChunks.value
  const lastChunk = chunks[chunks.length - 1]
  if (lastChunk) {
    emit('pcm-chunk', lastChunk)
  }
})

// Auto-stop on max duration
watch(() => recorder.elapsedMs.value, (ms) => {
  if (props.maxDurationSec > 0 && ms / 1000 >= props.maxDurationSec && recorder.isRecording.value) {
    recorder.stop()
  }
})

// ─── Actions ────────────────────────────────────────────────

async function handleRecord() {
  if (recorder.isPaused.value) {
    await recorder.resume()
    return
  }
  try {
    await recorder.start()
  } catch {
    // Error handled by composable
  }
}

function handlePause() {
  recorder.pause()
}

function handleStop() {
  recorder.stop()
}

function handleCancel() {
  recorder.cancel()
}

// ─── Lifecycle ──────────────────────────────────────────────

onMounted(() => {
  initCanvas()
})

onUnmounted(() => {
  if (drawFrameId) {
    cancelAnimationFrame(drawFrameId)
    drawFrameId = null
  }
  window.removeEventListener('resize', handleResize)
})

// ─── Expose ─────────────────────────────────────────────────

defineExpose({
  recorder,
  start: handleRecord,
  stop: handleStop,
  pause: handlePause,
  cancel: handleCancel,
})
</script>

<template>
  <div :class="['audio-recorder', { compact }]">
    <!-- Status Bar -->
    <div class="status-bar">
      <div class="status-indicator">
        <span
          class="status-dot"
          :style="{ backgroundColor: statusColor }"
          :class="{ pulse: recorder.isRecording.value }"
        />
        <span class="status-text">{{ statusLabel }}</span>
      </div>
      <div v-if="recorder.isRecording.value || recorder.isPaused.value" class="timer">
        {{ recorder.formattedTime.value }}
        <span v-if="maxDurationSec > 0" class="timer-limit">
          / {{ Math.floor(maxDurationSec / 60) }}:{{ (maxDurationSec % 60).toString().padStart(2, '0') }}
        </span>
      </div>
    </div>

    <!-- Error Banner -->
    <div v-if="recorder.hasError.value && recorder.error.value" class="error-banner">
      <span class="error-icon">⚠</span>
      <span class="error-text">{{ recorder.error.value }}</span>
      <button class="error-dismiss" @click="recorder.reset()">✕</button>
    </div>

    <!-- Audio Level Visualization -->
    <div class="visualization-container">
      <canvas ref="canvasRef" class="level-canvas" />
      <div v-if="!recorder.isRecording.value && !recorder.isPaused.value" class="canvas-overlay">
        <span class="mic-icon">🎤</span>
        <span class="canvas-hint">点击下方按钮开始录音</span>
      </div>
    </div>

    <!-- Level Meter -->
    <div v-if="recorder.isRecording.value" class="level-meter">
      <div class="level-bar-bg">
        <div
          class="level-bar-fill"
          :style="{ width: levelPercent + '%' }"
          :class="{ high: levelPercent > 70, mid: levelPercent > 30 && levelPercent <= 70 }"
        />
      </div>
      <span class="level-text">{{ levelPercent }}%</span>
    </div>

    <!-- Controls -->
    <div class="controls">
      <!-- Record / Resume Button -->
      <button
        v-if="!recorder.isRecording.value"
        :class="['btn', 'btn-record', { paused: recorder.isPaused.value }]"
        :disabled="recorder.state.value === 'requesting'"
        @click="handleRecord"
      >
        <span v-if="recorder.state.value === 'requesting'" class="btn-spinner" />
        <span v-else-if="recorder.isPaused.value" class="btn-icon">▶</span>
        <span v-else class="btn-icon record-dot" />
        <span class="btn-label">
          {{ recorder.state.value === 'requesting' ? '请求中...' : recorder.isPaused.value ? '继续录音' : '开始录音' }}
        </span>
      </button>

      <!-- Pause Button -->
      <button
        v-if="recorder.isRecording.value"
        class="btn btn-pause"
        @click="handlePause"
      >
        <span class="btn-icon">⏸</span>
        <span class="btn-label">暂停</span>
      </button>

      <!-- Stop Button -->
      <button
        v-if="recorder.isRecording.value || recorder.isPaused.value"
        class="btn btn-stop"
        @click="handleStop"
      >
        <span class="btn-icon">⏹</span>
        <span class="btn-label">停止</span>
      </button>

      <!-- Cancel Button -->
      <button
        v-if="recorder.isRecording.value || recorder.isPaused.value || recorder.state.value === 'stopped'"
        class="btn btn-cancel"
        @click="handleCancel"
      >
        <span class="btn-icon">✕</span>
        <span class="btn-label">取消</span>
      </button>
    </div>

    <!-- Stats Panel -->
    <div v-if="showStats && recorder.state.value !== 'idle'" class="stats-panel">
      <div class="stat">
        <span class="stat-value">{{ recorder.metrics.value.chunksSent }}</span>
        <span class="stat-label">数据块</span>
      </div>
      <div class="stat">
        <span class="stat-value">{{ recorder.formattedTime.value }}</span>
        <span class="stat-label">时长</span>
      </div>
      <div class="stat">
        <span class="stat-value">{{ recorder.totalSamples.value.toLocaleString() }}</span>
        <span class="stat-label">采样数</span>
      </div>
      <div class="stat">
        <span class="stat-value">{{ recorder.dataRateKbps.value.toFixed(1) }}</span>
        <span class="stat-label">KB/s</span>
      </div>
    </div>

    <!-- Browser Capabilities -->
    <div v-if="showCapabilities" class="capabilities-panel">
      <h4>浏览器兼容性</h4>
      <div class="cap-grid">
        <div class="cap-item">
          <span class="cap-label">浏览器</span>
          <span class="cap-value">
            {{ recorder.capabilities.value.browser.name }}
            {{ recorder.capabilities.value.browser.version || '' }}
          </span>
        </div>
        <div class="cap-item">
          <span class="cap-label">AudioWorklet</span>
          <span :class="['cap-value', recorder.capabilities.value.audioWorklet ? 'supported' : 'unsupported']">
            {{ recorder.capabilities.value.audioWorklet ? '✓ 支持' : '✗ 不支持' }}
          </span>
        </div>
        <div class="cap-item">
          <span class="cap-label">录音路径</span>
          <span class="cap-value">
            {{ recorder.capabilities.value.audioWorklet ? 'AudioWorklet (最优)' : 'ScriptProcessor (兼容)' }}
          </span>
        </div>
        <div class="cap-item">
          <span class="cap-label">采样率</span>
          <span class="cap-value">
            {{ recorder.currentSampleRate.value || recorder.capabilities.value.sampleRate || '—' }} Hz
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.audio-recorder {
  --ar-primary: #ef4444;
  --ar-primary-hover: #dc2626;
  --ar-success: #10b981;
  --ar-warning: #f59e0b;
  --ar-gray-50: #f9fafb;
  --ar-gray-100: #f3f4f6;
  --ar-gray-200: #e5e7eb;
  --ar-gray-300: #d1d5db;
  --ar-gray-400: #9ca3af;
  --ar-gray-500: #6b7280;
  --ar-gray-600: #4b5563;
  --ar-gray-700: #374151;
  --ar-gray-800: #1f2937;
  --ar-radius: 12px;
  --ar-radius-sm: 8px;

  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: white;
  border-radius: var(--ar-radius);
  border: 1px solid var(--ar-gray-200);
  padding: 20px;
  max-width: 400px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.audio-recorder.compact {
  padding: 12px;
  max-width: 300px;
}

/* ─── Status Bar ──────────────────────────────────────────── */

.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: background-color 0.3s;
}

.status-dot.pulse {
  animation: pulse-dot 1.2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}

.status-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--ar-gray-700);
}

.timer {
  font-family: 'SF Mono', 'Cascadia Code', Consolas, monospace;
  font-size: 18px;
  font-weight: 600;
  color: var(--ar-gray-800);
  letter-spacing: 1px;
}

.timer-limit {
  font-size: 12px;
  font-weight: 400;
  color: var(--ar-gray-400);
}

/* ─── Error Banner ────────────────────────────────────────── */

.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--ar-radius-sm);
  margin-bottom: 16px;
  font-size: 13px;
  color: #991b1b;
}

.error-icon {
  flex-shrink: 0;
}

.error-text {
  flex: 1;
}

.error-dismiss {
  background: none;
  border: none;
  color: #991b1b;
  cursor: pointer;
  padding: 2px;
  font-size: 14px;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.error-dismiss:hover {
  opacity: 1;
}

/* ─── Visualization ───────────────────────────────────────── */

.visualization-container {
  position: relative;
  margin-bottom: 12px;
}

.level-canvas {
  width: 100%;
  height: 80px;
  border-radius: var(--ar-radius-sm);
  background: var(--ar-gray-50);
  border: 1px solid var(--ar-gray-100);
  display: block;
}

.compact .level-canvas {
  height: 50px;
}

.canvas-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  pointer-events: none;
}

.mic-icon {
  font-size: 24px;
  opacity: 0.4;
}

.canvas-hint {
  font-size: 12px;
  color: var(--ar-gray-400);
}

.compact .canvas-hint {
  display: none;
}

/* ─── Level Meter ─────────────────────────────────────────── */

.level-meter {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.level-bar-bg {
  flex: 1;
  height: 6px;
  background: var(--ar-gray-100);
  border-radius: 3px;
  overflow: hidden;
}

.level-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.1s ease-out;
  background: var(--ar-success);
}

.level-bar-fill.mid {
  background: var(--ar-warning);
}

.level-bar-fill.high {
  background: var(--ar-primary);
}

.level-text {
  font-size: 11px;
  font-family: 'SF Mono', monospace;
  color: var(--ar-gray-500);
  width: 32px;
  text-align: right;
}

/* ─── Controls ────────────────────────────────────────────── */

.controls {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap; /* Allow wrapping on small screens */
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 14px 24px; /* Larger touch targets */
  border: none;
  border-radius: var(--ar-radius-sm);
  font-size: 16px; /* Slightly larger text */
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  min-width: 120px;
  /* Touch optimizations */
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  font-size: 14px;
  line-height: 1;
}

.btn-label {
  line-height: 1;
}

.btn-record {
  background: var(--ar-primary);
  color: white;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.btn-record:hover:not(:disabled) {
  background: var(--ar-primary-hover);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
  transform: translateY(-1px);
}

.btn-record.paused {
  background: var(--ar-success);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.btn-record.paused:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.record-dot {
  width: 10px;
  height: 10px;
  background: white;
  border-radius: 50%;
  display: inline-block;
}

.btn-pause {
  background: var(--ar-warning);
  color: #78350f;
}

.btn-pause:hover:not(:disabled) {
  background: #d97706;
}

.btn-stop {
  background: var(--ar-gray-700);
  color: white;
}

.btn-stop:hover:not(:disabled) {
  background: var(--ar-gray-800);
}

.btn-cancel {
  background: var(--ar-gray-100);
  color: var(--ar-gray-600);
  border: 1px solid var(--ar-gray-200);
  min-width: auto;
  padding: 10px 14px;
}

.btn-cancel:hover {
  background: var(--ar-gray-200);
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.compact .btn {
  padding: 8px 14px;
  font-size: 13px;
  min-width: 80px;
}

/* ─── Stats Panel ─────────────────────────────────────────── */

.stats-panel {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--ar-gray-100);
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 16px;
  font-weight: 700;
  font-family: 'SF Mono', monospace;
  color: var(--ar-gray-800);
}

.stat-label {
  display: block;
  font-size: 11px;
  color: var(--ar-gray-400);
  margin-top: 2px;
}

/* ─── Capabilities Panel ──────────────────────────────────── */

.capabilities-panel {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--ar-gray-100);
}

.capabilities-panel h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--ar-gray-600);
  margin-bottom: 10px;
}

.cap-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.cap-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: var(--ar-gray-50);
  border-radius: 6px;
  font-size: 12px;
}

.cap-label {
  color: var(--ar-gray-500);
}

.cap-value {
  font-weight: 500;
  color: var(--ar-gray-700);
}

.cap-value.supported {
  color: #059669;
}

.cap-value.unsupported {
  color: #dc2626;
}

/* ─── Responsive ──────────────────────────────────────────── */

@media (max-width: 768px) {
  .audio-recorder {
    padding: 16px;
    max-width: 100%;
    border-radius: var(--ar-radius) var(--ar-radius) 0 0;
    border-bottom: none;
    box-shadow: 0 -4px 12px rgba(0,0,0,0.1);
    /* Make it stick to bottom on mobile if not compact */
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 40;
  }

  .audio-recorder.compact {
    position: relative;
    border-radius: var(--ar-radius);
    border-bottom: 1px solid var(--ar-gray-200);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    max-width: 100%;
    width: 100%;
    margin-bottom: 16px;
  }

  .btn {
    padding: 12px 16px;
    font-size: 15px;
    flex: 1 1 calc(50% - 10px);
  }

  .stats-panel {
    grid-template-columns: repeat(2, 1fr);
  }

  .cap-grid {
    grid-template-columns: 1fr;
  }
}
</style>
