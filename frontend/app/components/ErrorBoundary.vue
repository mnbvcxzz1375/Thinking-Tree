<script setup lang="ts">
/**
 * ErrorBoundary - Catches and displays errors gracefully.
 * Provides retry functionality and error reporting.
 */
import { ref, onErrorCaptured, provide } from 'vue'

// Props
const props = defineProps<{
  /** Fallback component name for error display */
  fallbackTitle?: string
  /** Show technical details */
  showDetails?: boolean
}>()

// Emits
const emit = defineEmits<{
  error: [error: Error]
  retry: []
}>()

// State
const hasError = ref(false)
const errorMessage = ref('')
const errorStack = ref('')
const retryCount = ref(0)
const maxRetries = 3

// Error capture
onErrorCaptured((error: Error) => {
  hasError.value = true
  errorMessage.value = error.message || 'An unexpected error occurred'
  errorStack.value = error.stack || ''
  emit('error', error)

  // Prevent error from propagating
  return false
})

// Provide error state to children
provide('errorBoundary', {
  hasError,
  errorMessage,
  clearError,
})

// Methods
function retry() {
  if (retryCount.value >= maxRetries) return

  retryCount.value++
  hasError.value = false
  errorMessage.value = ''
  errorStack.value = ''
  emit('retry')
}

function clearError() {
  hasError.value = false
  errorMessage.value = ''
  errorStack.value = ''
}

function reloadPage() {
  window.location.reload()
}
</script>

<template>
  <div class="error-boundary">
    <!-- Error State -->
    <div
      v-if="hasError"
      class="error-fallback"
    >
      <div class="error-icon">⚠️</div>
      <h3 class="error-title">
        {{ fallbackTitle || 'Something went wrong' }}
      </h3>
      <p class="error-message">{{ errorMessage }}</p>

      <!-- Technical Details -->
      <details
        v-if="showDetails && errorStack"
        class="error-details"
      >
        <summary>Technical Details</summary>
        <pre class="error-stack">{{ errorStack }}</pre>
      </details>

      <!-- Actions -->
      <div class="error-actions">
        <button
          v-if="retryCount < maxRetries"
          class="retry-btn"
          @click="retry"
        >
          Try Again ({{ maxRetries - retryCount }} attempts left)
        </button>
        <button
          class="reload-btn"
          @click="reloadPage"
        >
          Reload Page
        </button>
      </div>
    </div>

    <!-- Normal Content -->
    <slot v-else />
  </div>
</template>

<style scoped>
.error-boundary {
  width: 100%;
  height: 100%;
}

.error-fallback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 24px;
  text-align: center;
  min-height: 200px;
}

.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.error-title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.error-message {
  margin: 0 0 16px;
  font-size: 14px;
  color: #6b7280;
  max-width: 400px;
}

.error-details {
  width: 100%;
  max-width: 500px;
  margin-bottom: 16px;
  text-align: left;
}

.error-details summary {
  cursor: pointer;
  font-size: 13px;
  color: #6b7280;
  padding: 8px 0;
}

.error-stack {
  margin: 8px 0 0;
  padding: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 12px;
  color: #374151;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.error-actions {
  display: flex;
  gap: 8px;
}

.retry-btn,
.reload-btn {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.retry-btn {
  background: #059669;
  color: white;
  border: none;
}

.retry-btn:hover {
  background: #047857;
}

.reload-btn {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.reload-btn:hover {
  background: #f9fafb;
}
</style>
