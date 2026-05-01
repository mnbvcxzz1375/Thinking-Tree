<script setup lang="ts">
/**
 * ExportDialog - Modal dialog for exporting tree visualizations.
 * Supports PNG, PDF, Markdown, and JSON formats with preview and settings.
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useExportStore, formatFileSize } from '../stores/export'
import type { ExportFormat } from '../stores/export'
import ExportPreview from './ExportPreview.vue'

// Props
const props = defineProps<{
  /** Whether the dialog is visible */
  modelValue: boolean
  /** SVG element to export (for PNG/PDF) */
  svgElement?: SVGSVGElement | null
  /** Activity ID for data exports */
  activityId?: number
  /** Tree title */
  title?: string
  /** Node count for size estimates */
  nodeCount?: number
}>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  exported: [format: ExportFormat]
  error: [message: string]
}>()

// Store
const exportStore = useExportStore()

// Local state
const showPreview = ref(false)
const selectedTab = ref<'format' | 'settings' | 'history'>('format')

// Format options
const formats = [
  {
    key: 'png' as ExportFormat,
    label: 'PNG Image',
    icon: '🖼️',
    description: 'High-resolution image, great for presentations',
    requiresSvg: true,
  },
  {
    key: 'pdf' as ExportFormat,
    label: 'PDF Document',
    icon: '📄',
    description: 'Printable document with title and metadata',
    requiresSvg: true,
  },
  {
    key: 'markdown' as ExportFormat,
    label: 'Markdown',
    icon: '📝',
    description: 'Structured text format, easy to edit',
    requiresSvg: false,
  },
  {
    key: 'json' as ExportFormat,
    label: 'JSON Data',
    icon: '📊',
    description: 'Machine-readable data format',
    requiresSvg: false,
  },
]

// Computed
const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const currentFormat = computed(() =>
  formats.find((f) => f.key === exportStore.options.format)
)

const needsSvg = computed(() =>
  exportStore.options.format === 'png' || exportStore.options.format === 'pdf'
)

const canExport = computed(() => {
  if (needsSvg.value && !props.svgElement) return false
  if (
    (exportStore.options.format === 'markdown' || exportStore.options.format === 'json') &&
    !props.activityId
  )
    return false
  return !exportStore.exporting
})

const scaleLabel = computed(() => {
  const scale = exportStore.options.scale
  if (scale <= 1) return 'Standard (72 DPI)'
  if (scale <= 2) return 'High (144 DPI)'
  if (scale <= 3) return 'Very High (216 DPI)'
  return 'Ultra (288 DPI)'
})

// Watchers
watch(
  () => exportStore.options.format,
  () => {
    if (props.nodeCount) {
      exportStore.fetchSizeEstimate(exportStore.options.format, props.nodeCount)
    }
  }
)

// Methods
function selectFormat(format: ExportFormat) {
  exportStore.setFormat(format)
  showPreview.value = false
}

async function handleExport() {
  if (!canExport.value) return

  const success = await exportStore.doExport(
    props.svgElement || undefined,
    props.activityId
  )

  if (success) {
    emit('exported', exportStore.options.format)
  } else if (exportStore.error) {
    emit('error', exportStore.error)
  }
}

function closeDialog() {
  isOpen.value = false
  showPreview.value = false
  exportStore.clearError()
}

function togglePreview() {
  showPreview.value = !showPreview.value
}

// Initialize size estimate
onMounted(() => {
  if (props.nodeCount) {
    exportStore.fetchSizeEstimate(exportStore.options.format, props.nodeCount)
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog-fade">
      <div
        v-if="isOpen"
        class="export-overlay"
        @click.self="closeDialog"
      >
        <div class="export-dialog" role="dialog" aria-label="Export Tree">
          <!-- Header -->
          <div class="dialog-header">
            <h2 class="dialog-title">🌳 Export Tree</h2>
            <button
              class="close-btn"
              @click="closeDialog"
              aria-label="Close dialog"
            >
              ✕
            </button>
          </div>

          <!-- Tabs -->
          <div class="tab-bar">
            <button
              :class="['tab', { active: selectedTab === 'format' }]"
              @click="selectedTab = 'format'"
            >
              Format
            </button>
            <button
              :class="['tab', { active: selectedTab === 'settings' }]"
              @click="selectedTab = 'settings'"
            >
              Settings
            </button>
            <button
              :class="['tab', { active: selectedTab === 'history' }]"
              @click="selectedTab = 'history'"
            >
              History
              <span
                v-if="exportStore.recentHistory.length"
                class="tab-badge"
              >
                {{ exportStore.recentHistory.length }}
              </span>
            </button>
          </div>

          <!-- Content -->
          <div class="dialog-content">
            <!-- Format Selection Tab -->
            <div v-if="selectedTab === 'format'" class="format-grid">
              <button
                v-for="fmt in formats"
                :key="fmt.key"
                :class="[
                  'format-card',
                  { selected: exportStore.options.format === fmt.key },
                ]"
                @click="selectFormat(fmt.key)"
              >
                <span class="format-icon">{{ fmt.icon }}</span>
                <span class="format-label">{{ fmt.label }}</span>
                <span class="format-desc">{{ fmt.description }}</span>
                <span
                  v-if="fmt.requiresSvg && !svgElement"
                  class="format-unavailable"
                >
                  Requires tree view
                </span>
              </button>
            </div>

            <!-- Settings Tab -->
            <div v-if="selectedTab === 'settings'" class="settings-panel">
              <!-- Scale setting (for PNG/PDF) -->
              <div v-if="needsSvg" class="setting-group">
                <label class="setting-label">Resolution</label>
                <div class="scale-control">
                  <input
                    type="range"
                    :value="exportStore.options.scale"
                    min="0.5"
                    max="4"
                    step="0.5"
                    class="scale-slider"
                    @input="
                      exportStore.setScale(
                        parseFloat(($event.target as HTMLInputElement).value)
                      )
                    "
                  />
                  <span class="scale-value">{{ scaleLabel }}</span>
                </div>
              </div>

              <!-- Metadata toggle -->
              <div class="setting-group">
                <label class="setting-label">
                  <input
                    type="checkbox"
                    :checked="exportStore.options.includeMetadata"
                    @change="
                      exportStore.setIncludeMetadata(
                        ($event.target as HTMLInputElement).checked
                      )
                    "
                  />
                  Include metadata (timestamps, node types)
                </label>
              </div>

              <!-- Auto download -->
              <div class="setting-group">
                <label class="setting-label">
                  <input
                    type="checkbox"
                    :checked="exportStore.preferences.autoDownload"
                    @change="
                      exportStore.setAutoDownload(
                        ($event.target as HTMLInputElement).checked
                      )
                    "
                  />
                  Auto-download after export
                </label>
              </div>

              <!-- Title (for PDF) -->
              <div v-if="exportStore.options.format === 'pdf'" class="setting-group">
                <label class="setting-label">Document Title</label>
                <input
                  type="text"
                  :value="exportStore.options.title || title || 'Thinking Tree'"
                  class="title-input"
                  placeholder="Enter document title"
                  @input="
                    exportStore.setTitle(
                      ($event.target as HTMLInputElement).value
                    )
                  "
                />
              </div>

              <!-- Size estimate -->
              <div v-if="exportStore.sizeEstimate" class="size-estimate">
                <span class="estimate-label">Estimated size:</span>
                <span
                  :class="[
                    'estimate-value',
                    { warning: exportStore.isLargeExport },
                  ]"
                >
                  {{ exportStore.sizeEstimate.estimatedSizeKb }} KB
                </span>
                <span
                  v-if="!exportStore.sizeEstimate.withinLimit"
                  class="estimate-error"
                >
                  ⚠️ Exceeds size limit
                </span>
              </div>
            </div>

            <!-- History Tab -->
            <div v-if="selectedTab === 'history'" class="history-panel">
              <div
                v-if="!exportStore.hasHistory"
                class="history-empty"
              >
                No exports yet
              </div>
              <div
                v-for="entry in exportStore.recentHistory"
                :key="entry.id"
                :class="['history-item', { failed: !entry.success }]"
              >
                <span class="history-format">{{
                  formats.find((f) => f.key === entry.format)?.icon || '📁'
                }}</span>
                <span class="history-name">{{ entry.filename }}</span>
                <span class="history-size">{{
                  formatFileSize(entry.sizeBytes)
                }}</span>
                <span class="history-time">{{
                  new Date(entry.timestamp).toLocaleString()
                }}</span>
                <button
                  class="history-remove"
                  @click="exportStore.removeHistoryEntry(entry.id)"
                  aria-label="Remove entry"
                >
                  ✕
                </button>
              </div>
              <button
                v-if="exportStore.hasHistory"
                class="clear-history-btn"
                @click="exportStore.clearHistory()"
              >
                Clear History
              </button>
            </div>

            <!-- Preview -->
            <ExportPreview
              v-if="showPreview && svgElement"
              :svg-element="svgElement"
              :format="exportStore.options.format"
              :scale="exportStore.options.scale"
            />
          </div>

          <!-- Error display -->
          <div v-if="exportStore.error" class="error-banner">
            <span>{{ exportStore.error }}</span>
            <button @click="exportStore.clearError()">✕</button>
          </div>

          <!-- Footer -->
          <div class="dialog-footer">
            <button
              v-if="needsSvg && svgElement"
              class="preview-btn"
              @click="togglePreview"
            >
              {{ showPreview ? 'Hide Preview' : 'Preview' }}
            </button>
            <div class="footer-spacer" />
            <button class="cancel-btn" @click="closeDialog">Cancel</button>
            <button
              class="export-btn"
              :disabled="!canExport"
              @click="handleExport"
            >
              <span
                v-if="exportStore.exporting"
                class="spinner"
              />
              {{
                exportStore.exporting
                  ? `Exporting... ${exportStore.progress}%`
                  : `Export as ${currentFormat?.label || 'File'}`
              }}
            </button>
          </div>

          <!-- Progress bar -->
          <div
            v-if="exportStore.exporting"
            class="progress-bar"
          >
            <div
              class="progress-fill"
              :style="{ width: `${exportStore.progress}%` }"
            />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.export-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.export-dialog {
  background: white;
  border-radius: 16px;
  width: 90vw;
  max-width: 560px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.dialog-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #f3f4f6;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  transition: all 0.15s;
}

.close-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.tab-bar {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  padding: 0 16px;
}

.tab {
  padding: 10px 16px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab:hover {
  color: #374151;
}

.tab.active {
  color: #059669;
  border-bottom-color: #059669;
}

.tab-badge {
  background: #059669;
  color: white;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 10px;
}

.dialog-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

/* Format Grid */
.format-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.format-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px 12px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  background: white;
  cursor: pointer;
  transition: all 0.15s;
}

.format-card:hover {
  border-color: #a7f3d0;
  background: #f0fdf4;
}

.format-card.selected {
  border-color: #059669;
  background: #ecfdf5;
}

.format-card.unavailable {
  opacity: 0.5;
  cursor: not-allowed;
}

.format-icon {
  font-size: 28px;
}

.format-label {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.format-desc {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
}

.format-unavailable {
  font-size: 11px;
  color: #dc2626;
  background: #fef2f2;
  padding: 2px 8px;
  border-radius: 4px;
}

/* Settings */
.settings-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setting-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.setting-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 8px;
}

.setting-label input[type='checkbox'] {
  width: 16px;
  height: 16px;
  accent-color: #059669;
}

.scale-control {
  display: flex;
  align-items: center;
  gap: 12px;
}

.scale-slider {
  flex: 1;
  height: 6px;
  accent-color: #059669;
}

.scale-value {
  font-size: 13px;
  color: #6b7280;
  min-width: 120px;
  text-align: right;
}

.title-input {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
}

.title-input:focus {
  border-color: #059669;
  box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.1);
}

.size-estimate {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 8px;
  font-size: 13px;
}

.estimate-label {
  color: #6b7280;
}

.estimate-value {
  font-weight: 600;
  color: #059669;
}

.estimate-value.warning {
  color: #d97706;
}

.estimate-error {
  color: #dc2626;
  font-weight: 500;
}

/* History */
.history-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-empty {
  text-align: center;
  padding: 24px;
  color: #9ca3af;
  font-size: 14px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 8px;
  font-size: 13px;
}

.history-item.failed {
  background: #fef2f2;
}

.history-format {
  font-size: 18px;
}

.history-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #1f2937;
}

.history-size {
  color: #6b7280;
  min-width: 60px;
  text-align: right;
}

.history-time {
  color: #9ca3af;
  font-size: 12px;
  min-width: 100px;
}

.history-remove {
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  cursor: pointer;
  color: #9ca3af;
  font-size: 14px;
  border-radius: 4px;
  transition: all 0.15s;
}

.history-remove:hover {
  background: #fee2e2;
  color: #dc2626;
}

.clear-history-btn {
  padding: 8px;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #6b7280;
  transition: all 0.15s;
}

.clear-history-btn:hover {
  border-color: #fca5a5;
  color: #dc2626;
}

/* Error Banner */
.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #fef2f2;
  border-top: 1px solid #fecaca;
  color: #dc2626;
  font-size: 13px;
}

.error-banner button {
  border: none;
  background: none;
  cursor: pointer;
  color: #dc2626;
  font-size: 16px;
}

/* Footer */
.dialog-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid #e5e7eb;
}

.footer-spacer {
  flex: 1;
}

.preview-btn,
.cancel-btn {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  transition: all 0.15s;
}

.preview-btn:hover,
.cancel-btn:hover {
  background: #f9fafb;
}

.export-btn {
  padding: 8px 20px;
  border: none;
  background: #059669;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  color: white;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.export-btn:hover:not(:disabled) {
  background: #047857;
}

.export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Progress bar */
.progress-bar {
  height: 3px;
  background: #e5e7eb;
}

.progress-fill {
  height: 100%;
  background: #059669;
  transition: width 0.3s ease;
}

/* Transitions */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.2s ease;
}

.dialog-fade-enter-active .export-dialog,
.dialog-fade-leave-active .export-dialog {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-fade-enter-from .export-dialog,
.dialog-fade-leave-to .export-dialog {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}

/* Mobile */
@media (max-width: 640px) {
  .export-dialog {
    width: 95vw;
    max-height: 90vh;
  }

  .format-grid {
    grid-template-columns: 1fr;
  }

  .history-time {
    display: none;
  }

  .dialog-footer {
    flex-wrap: wrap;
  }

  .export-btn {
    flex: 1;
    justify-content: center;
  }
}
</style>
