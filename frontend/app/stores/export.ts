/**
 * Export store for managing tree export operations.
 * Handles format selection, export history, preferences, and download management.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Types
export type ExportFormat = 'png' | 'pdf' | 'markdown' | 'json'

export interface ExportOptions {
  format: ExportFormat
  /** PNG/PDF scale factor (1-4) */
  scale: number
  /** Include metadata in Markdown/JSON */
  includeMetadata: boolean
  /** Activity ID for data exports */
  activityId?: number
  /** Custom title for PDF */
  title?: string
}

export interface ExportHistoryEntry {
  id: string
  format: ExportFormat
  filename: string
  sizeBytes: number
  timestamp: string
  success: boolean
  error?: string
}

export interface ExportPreferences {
  defaultFormat: ExportFormat
  defaultScale: number
  includeMetadata: boolean
  autoDownload: boolean
}

export interface SizeEstimate {
  format: string
  nodeCount: number
  estimatedSizeKb: number
  estimatedSizeMb: number
  maxSizeMb: number
  withinLimit: boolean
}

export interface ExportState {
  /** Current export options */
  options: ExportOptions
  /** Export in progress */
  exporting: boolean
  /** Current export progress (0-100) */
  progress: number
  /** Error message */
  error: string | null
  /** Export history */
  history: ExportHistoryEntry[]
  /** User preferences */
  preferences: ExportPreferences
  /** Size estimate for current selection */
  sizeEstimate: SizeEstimate | null
  /** Preview SVG data */
  previewSvg: string | null
}

// Storage keys
const PREFS_KEY = 'export_preferences'
const HISTORY_KEY = 'export_history'

// Max history entries
const MAX_HISTORY = 50

// Default preferences
const DEFAULT_PREFERENCES: ExportPreferences = {
  defaultFormat: 'png',
  defaultScale: 2,
  includeMetadata: true,
  autoDownload: true,
}

/**
 * Load preferences from localStorage
 */
function loadPreferences(): ExportPreferences {
  try {
    const stored = localStorage.getItem(PREFS_KEY)
    if (stored) {
      return { ...DEFAULT_PREFERENCES, ...JSON.parse(stored) }
    }
  } catch (e) {
    console.warn('Failed to load export preferences:', e)
  }
  return { ...DEFAULT_PREFERENCES }
}

/**
 * Save preferences to localStorage
 */
function savePreferences(prefs: ExportPreferences): void {
  try {
    localStorage.setItem(PREFS_KEY, JSON.stringify(prefs))
  } catch (e) {
    console.warn('Failed to save export preferences:', e)
  }
}

/**
 * Load history from localStorage
 */
function loadHistory(): ExportHistoryEntry[] {
  try {
    const stored = localStorage.getItem(HISTORY_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.warn('Failed to load export history:', e)
  }
  return []
}

/**
 * Save history to localStorage
 */
function saveHistory(history: ExportHistoryEntry[]): void {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
  } catch (e) {
    console.warn('Failed to save export history:', e)
  }
}

/**
 * Generate unique ID
 */
function generateId(): string {
  return `exp_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

/**
 * Export store
 */
export const useExportStore = defineStore('export', () => {
  // Load saved data
  const savedPrefs = loadPreferences()

  // State
  const options = ref<ExportOptions>({
    format: savedPrefs.defaultFormat,
    scale: savedPrefs.defaultScale,
    includeMetadata: savedPrefs.includeMetadata,
  })
  const exporting = ref(false)
  const progress = ref(0)
  const error = ref<string | null>(null)
  const history = ref<ExportHistoryEntry[]>(loadHistory())
  const preferences = ref<ExportPreferences>(savedPrefs)
  const sizeEstimate = ref<SizeEstimate | null>(null)
  const previewSvg = ref<string | null>(null)

  // Getters
  const recentHistory = computed(() =>
    [...history.value]
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 20)
  )

  const successfulExports = computed(() =>
    history.value.filter((h) => h.success)
  )

  const totalExportSize = computed(() =>
    history.value
      .filter((h) => h.success)
      .reduce((sum, h) => sum + h.sizeBytes, 0)
  )

  const hasHistory = computed(() => history.value.length > 0)

  const isLargeExport = computed(() => {
    if (!sizeEstimate.value) return false
    return sizeEstimate.value.estimatedSizeMb > 5
  })

  // Actions
  function setFormat(format: ExportFormat) {
    options.value.format = format
    preferences.value.defaultFormat = format
    savePreferences(preferences.value)
  }

  function setScale(scale: number) {
    options.value.scale = Math.max(0.5, Math.min(4, scale))
    preferences.value.defaultScale = options.value.scale
    savePreferences(preferences.value)
  }

  function setIncludeMetadata(include: boolean) {
    options.value.includeMetadata = include
    preferences.value.includeMetadata = include
    savePreferences(preferences.value)
  }

  function setActivityId(id: number | undefined) {
    options.value.activityId = id
  }

  function setTitle(title: string) {
    options.value.title = title
  }

  function setAutoDownload(auto: boolean) {
    preferences.value.autoDownload = auto
    savePreferences(preferences.value)
  }

  function setPreviewSvg(svg: string | null) {
    previewSvg.value = svg
  }

  function updateSizeEstimate(estimate: SizeEstimate) {
    sizeEstimate.value = estimate
  }

  function startExport() {
    exporting.value = true
    progress.value = 0
    error.value = null
  }

  function updateExportProgress(value: number) {
    progress.value = Math.max(0, Math.min(100, value))
  }

  function completeExport(entry: Omit<ExportHistoryEntry, 'id' | 'timestamp'>) {
    exporting.value = false
    progress.value = 100

    const record: ExportHistoryEntry = {
      ...entry,
      id: generateId(),
      timestamp: new Date().toISOString(),
    }

    history.value.push(record)

    // Trim history
    if (history.value.length > MAX_HISTORY) {
      history.value = history.value.slice(-MAX_HISTORY)
    }

    saveHistory(history.value)

    if (!entry.success) {
      error.value = entry.error || 'Export failed'
    }
  }

  function failExport(errorMessage: string) {
    exporting.value = false
    progress.value = 0
    error.value = errorMessage

    const record: ExportHistoryEntry = {
      id: generateId(),
      format: options.value.format,
      filename: 'unknown',
      sizeBytes: 0,
      timestamp: new Date().toISOString(),
      success: false,
      error: errorMessage,
    }

    history.value.push(record)
    saveHistory(history.value)
  }

  function clearError() {
    error.value = null
  }

  function clearHistory() {
    history.value = []
    saveHistory([])
  }

  function removeHistoryEntry(id: string) {
    history.value = history.value.filter((h) => h.id !== id)
    saveHistory(history.value)
  }

  /**
   * Download a blob as a file
   */
  function downloadBlob(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  /**
   * Export tree as PNG via backend
   */
  async function exportAsPng(svgElement: SVGSVGElement | null): Promise<boolean> {
    if (!svgElement) {
      failExport('No SVG element found')
      return false
    }

    startExport()
    updateExportProgress(10)

    try {
      // Serialize SVG
      const serializer = new XMLSerializer()
      const svgString = serializer.serializeToString(svgElement)
      updateExportProgress(30)

      // Send to backend
      const config = useRuntimeConfig()
      const baseURL = config.public.apiBase as string

      const response = await fetch(`${baseURL}/api/data/export/png`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          svg_data: svgString,
          scale: options.value.scale,
        }),
      })

      updateExportProgress(80)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Export failed' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const blob = await response.blob()
      const filename = `thinking_tree_${new Date().toISOString().slice(0, 10)}.png`

      if (preferences.value.autoDownload) {
        downloadBlob(blob, filename)
      }

      completeExport({
        format: 'png',
        filename,
        sizeBytes: blob.size,
        success: true,
      })

      return true
    } catch (e) {
      failExport(e instanceof Error ? e.message : 'PNG export failed')
      return false
    }
  }

  /**
   * Export tree as PDF via backend
   */
  async function exportAsPdf(svgElement: SVGSVGElement | null): Promise<boolean> {
    if (!svgElement) {
      failExport('No SVG element found')
      return false
    }

    startExport()
    updateExportProgress(10)

    try {
      const serializer = new XMLSerializer()
      const svgString = serializer.serializeToString(svgElement)
      updateExportProgress(30)

      const config = useRuntimeConfig()
      const baseURL = config.public.apiBase as string
      const title = encodeURIComponent(options.value.title || 'Thinking Tree')

      const response = await fetch(
        `${baseURL}/api/data/export/pdf?title=${title}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            svg_data: svgString,
            scale: options.value.scale,
          }),
        }
      )

      updateExportProgress(80)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Export failed' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const blob = await response.blob()
      const filename = `thinking_tree_${new Date().toISOString().slice(0, 10)}.pdf`

      if (preferences.value.autoDownload) {
        downloadBlob(blob, filename)
      }

      completeExport({
        format: 'pdf',
        filename,
        sizeBytes: blob.size,
        success: true,
      })

      return true
    } catch (e) {
      failExport(e instanceof Error ? e.message : 'PDF export failed')
      return false
    }
  }

  /**
   * Export tree as Markdown via backend
   */
  async function exportAsMarkdown(activityId: number): Promise<boolean> {
    startExport()
    updateExportProgress(20)

    try {
      const config = useRuntimeConfig()
      const baseURL = config.public.apiBase as string
      const meta = options.value.includeMetadata ? 'true' : 'false'

      const response = await fetch(
        `${baseURL}/api/data/export/markdown/${activityId}?include_metadata=${meta}`
      )

      updateExportProgress(70)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Export failed' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const blob = await response.blob()
      const filename = `thinking_tree_${activityId}_${new Date().toISOString().slice(0, 10)}.md`

      if (preferences.value.autoDownload) {
        downloadBlob(blob, filename)
      }

      completeExport({
        format: 'markdown',
        filename,
        sizeBytes: blob.size,
        success: true,
      })

      return true
    } catch (e) {
      failExport(e instanceof Error ? e.message : 'Markdown export failed')
      return false
    }
  }

  /**
   * Export tree as JSON via backend
   */
  async function exportAsJson(activityId: number): Promise<boolean> {
    startExport()
    updateExportProgress(20)

    try {
      const config = useRuntimeConfig()
      const baseURL = config.public.apiBase as string

      const response = await fetch(
        `${baseURL}/api/data/export/json/${activityId}?pretty=true`
      )

      updateExportProgress(70)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Export failed' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const blob = await response.blob()
      const filename = `thinking_tree_${activityId}_${new Date().toISOString().slice(0, 10)}.json`

      if (preferences.value.autoDownload) {
        downloadBlob(blob, filename)
      }

      completeExport({
        format: 'json',
        filename,
        sizeBytes: blob.size,
        success: true,
      })

      return true
    } catch (e) {
      failExport(e instanceof Error ? e.message : 'JSON export failed')
      return false
    }
  }

  /**
   * Export based on current options
   */
  async function doExport(
    svgElement?: SVGSVGElement | null,
    activityId?: number
  ): Promise<boolean> {
    const format = options.value.format

    if (format === 'png') {
      return exportAsPng(svgElement || null)
    }
    if (format === 'pdf') {
      return exportAsPdf(svgElement || null)
    }
    if (format === 'markdown') {
      if (!activityId) {
        failExport('Activity ID required for Markdown export')
        return false
      }
      return exportAsMarkdown(activityId)
    }
    if (format === 'json') {
      if (!activityId) {
        failExport('Activity ID required for JSON export')
        return false
      }
      return exportAsJson(activityId)
    }

    failExport(`Unsupported format: ${format}`)
    return false
  }

  /**
   * Fetch size estimate from backend
   */
  async function fetchSizeEstimate(format: ExportFormat, nodeCount: number) {
    try {
      const config = useRuntimeConfig()
      const baseURL = config.public.apiBase as string

      const response = await fetch(
        `${baseURL}/api/data/export/size-estimate/${format}/${nodeCount}`
      )

      if (response.ok) {
        const data = await response.json()
        sizeEstimate.value = data
      }
    } catch (e) {
      console.warn('Failed to fetch size estimate:', e)
    }
  }

  /**
   * Reset store state
   */
  function reset() {
    options.value = {
      format: preferences.value.defaultFormat,
      scale: preferences.value.defaultScale,
      includeMetadata: preferences.value.includeMetadata,
    }
    exporting.value = false
    progress.value = 0
    error.value = null
    sizeEstimate.value = null
    previewSvg.value = null
  }

  return {
    // State
    options,
    exporting,
    progress,
    error,
    history,
    preferences,
    sizeEstimate,
    previewSvg,

    // Getters
    recentHistory,
    successfulExports,
    totalExportSize,
    hasHistory,
    isLargeExport,

    // Actions
    setFormat,
    setScale,
    setIncludeMetadata,
    setActivityId,
    setTitle,
    setAutoDownload,
    setPreviewSvg,
    updateSizeEstimate,
    startExport,
    updateExportProgress,
    completeExport,
    failExport,
    clearError,
    clearHistory,
    removeHistoryEntry,
    downloadBlob,
    exportAsPng,
    exportAsPdf,
    exportAsMarkdown,
    exportAsJson,
    doExport,
    fetchSizeEstimate,
    reset,
  }
})
