<script setup lang="ts">
/**
 * ExportPreview - Shows a preview of the tree before export.
 * Renders a scaled-down version of the SVG for visual confirmation.
 */
import { ref, computed, onMounted, watch } from 'vue'
import type { ExportFormat } from '../stores/export'

// Props
const props = defineProps<{
  /** SVG element to preview */
  svgElement: SVGSVGElement
  /** Export format */
  format: ExportFormat
  /** Scale factor */
  scale: number
}>()

// Refs
const previewContainer = ref<HTMLDivElement | null>(null)

// Computed
const formatLabel = computed(() => {
  const labels: Record<ExportFormat, string> = {
    png: 'PNG Preview',
    pdf: 'PDF Preview',
    markdown: 'Markdown Preview',
    json: 'JSON Preview',
  }
  return labels[props.format] || 'Preview'
})

const resolutionLabel = computed(() => {
  const scale = props.scale
  if (scale <= 1) return '72 DPI'
  if (scale <= 2) return '144 DPI'
  if (scale <= 3) return '216 DPI'
  return '288 DPI'
})

const estimatedDimensions = computed(() => {
  if (!props.svgElement) return { width: 0, height: 0 }
  const viewBox = props.svgElement.viewBox?.baseVal
  const width = viewBox?.width || parseFloat(props.svgElement.getAttribute('width') || '800')
  const height = viewBox?.height || parseFloat(props.svgElement.getAttribute('height') || '600')
  return {
    width: Math.round(width * props.scale),
    height: Math.round(height * props.scale),
  }
})

// Methods
function renderPreview() {
  if (!previewContainer.value || !props.svgElement) return

  // Clear previous preview
  previewContainer.value.innerHTML = ''

  // Clone SVG for preview
  const clone = props.svgElement.cloneNode(true) as SVGSVGElement

  // Adjust for preview container
  clone.removeAttribute('width')
  clone.removeAttribute('height')
  clone.style.width = '100%'
  clone.style.height = 'auto'
  clone.style.maxHeight = '300px'

  // Remove animations for static preview
  const animatedElements = clone.querySelectorAll('[style*="animation"]')
  animatedElements.forEach((el) => {
    el.removeAttribute('style')
  })

  previewContainer.value.appendChild(clone)
}

// Lifecycle
onMounted(() => {
  renderPreview()
})

watch(
  () => props.svgElement,
  () => {
    renderPreview()
  },
  { deep: true }
)
</script>

<template>
  <div class="export-preview">
    <div class="preview-header">
      <span class="preview-label">{{ formatLabel }}</span>
      <span class="preview-meta">
        {{ estimatedDimensions.width }} × {{ estimatedDimensions.height }} px
        · {{ resolutionLabel }}
      </span>
    </div>
    <div
      ref="previewContainer"
      class="preview-content"
    />
    <div class="preview-footer">
      <span class="preview-note">
        Preview is scaled down. Actual export will be higher resolution.
      </span>
    </div>
  </div>
</template>

<style scoped>
.export-preview {
  margin-top: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.preview-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.preview-meta {
  font-size: 12px;
  color: #6b7280;
}

.preview-content {
  padding: 12px;
  background: white;
  min-height: 120px;
  max-height: 300px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-content :deep(svg) {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.preview-footer {
  padding: 8px 14px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.preview-note {
  font-size: 11px;
  color: #9ca3af;
  font-style: italic;
}
</style>
