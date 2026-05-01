<template>
  <div class="suggestion-panel" :class="{ 'suggestion-panel--open': isOpen }">
    <div class="suggestion-panel__header">
      <div class="suggestion-panel__title-row">
        <h3 class="suggestion-panel__title">
          🌟 智能建议
          <span v-if="pendingCount > 0" class="suggestion-panel__count">
            {{ pendingCount }}
          </span>
        </h3>
        <button class="suggestion-panel__toggle" @click="$emit('toggle')">
          {{ isOpen ? '✕' : '💡' }}
        </button>
      </div>
      <p v-if="pendingCount > 0" class="suggestion-panel__subtitle">
        AI 发现了 {{ pendingCount }} 条改进建议
      </p>
      <p v-else class="suggestion-panel__subtitle suggestion-panel__subtitle--empty">
        暂无建议
      </p>
    </div>

    <div v-if="isOpen" class="suggestion-panel__body">
      <!-- Analysis Summary -->
      <div v-if="currentAnalysis" class="suggestion-panel__summary">
        <div class="suggestion-panel__stats">
          <div class="suggestion-panel__stat">
            <span class="suggestion-panel__stat-value">{{ currentAnalysis.totalNodes }}</span>
            <span class="suggestion-panel__stat-label">节点</span>
          </div>
          <div class="suggestion-panel__stat">
            <span class="suggestion-panel__stat-value">{{ currentAnalysis.maxDepth }}</span>
            <span class="suggestion-panel__stat-label">深度</span>
          </div>
          <div class="suggestion-panel__stat">
            <span class="suggestion-panel__stat-value">
              {{ Math.round(currentAnalysis.balanceScore * 100) }}%
            </span>
            <span class="suggestion-panel__stat-label">平衡</span>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="pendingCount === 0 && !loading" class="suggestion-panel__empty">
        <span class="suggestion-panel__empty-icon">🌳</span>
        <p>思维树看起来不错！</p>
        <p class="suggestion-panel__empty-hint">点击下方按钮分析树结构</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="suggestion-panel__loading">
        <div class="suggestion-panel__spinner"></div>
        <p>正在分析思维树...</p>
      </div>

      <!-- Suggestion List -->
      <div v-if="pendingCount > 0" class="suggestion-panel__list">
        <SuggestionCard
          v-for="suggestion in pendingSuggestions"
          :key="suggestion.id"
          :suggestion="suggestion"
          :selected-id="selectedSuggestionId"
          @select="$emit('select', $event)"
          @accept="$emit('accept', $event)"
          @reject="$emit('reject', $event)"
          @dismiss="$emit('dismiss', $event)"
        />
      </div>

      <!-- Footer Actions -->
      <div class="suggestion-panel__footer">
        <button
          class="suggestion-panel__btn suggestion-panel__btn--analyze"
          :disabled="loading"
          @click="$emit('analyze')"
        >
          {{ loading ? '分析中...' : '🔍 分析树结构' }}
        </button>
        <button
          v-if="pendingCount > 0"
          class="suggestion-panel__btn suggestion-panel__btn--clear"
          @click="$emit('clear-all')"
        >
          清空建议
        </button>
      </div>

      <!-- Auto-suggest Toggle -->
      <div class="suggestion-panel__settings">
        <label class="suggestion-panel__toggle-label">
          <input
            type="checkbox"
            :checked="autoSuggestEnabled"
            @change="$emit('toggle-auto-suggest')"
          />
          <span>自动建议（每 {{ autoSuggestThreshold }} 个节点）</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useSuggestionStore } from '~/stores/suggestions'

interface Props {
  isOpen: boolean
}

defineProps<Props>()

defineEmits<{
  toggle: []
  select: [id: number]
  accept: [id: number]
  reject: [id: number]
  dismiss: [id: number]
  analyze: []
  'clear-all': []
  'toggle-auto-suggest': []
}>()

const suggestionStore = useSuggestionStore()
const {
  pendingSuggestions,
  pendingCount,
  selectedSuggestionId,
  currentAnalysis,
  loading,
  autoSuggestEnabled,
  autoSuggestThreshold,
} = storeToRefs(suggestionStore)
</script>

<style scoped>
.suggestion-panel {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 22rem;
  background: white;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 50;
  display: flex;
  flex-direction: column;
}

.suggestion-panel--open {
  transform: translateX(0);
}

.suggestion-panel__header {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #fefce8, #fef9c3);
}

.suggestion-panel__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.suggestion-panel__title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #854d0e;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.suggestion-panel__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.375rem;
  border-radius: 9999px;
  background: #f59e0b;
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
}

.suggestion-panel__subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.8125rem;
  color: #a16207;
}

.suggestion-panel__subtitle--empty {
  color: #9ca3af;
}

.suggestion-panel__toggle {
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 0.375rem;
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.suggestion-panel__toggle:hover {
  background: rgba(245, 158, 11, 0.2);
}

.suggestion-panel__body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.suggestion-panel__summary {
  padding: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
  background: #fffbeb;
}

.suggestion-panel__stats {
  display: flex;
  justify-content: space-around;
}

.suggestion-panel__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.125rem;
}

.suggestion-panel__stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #92400e;
}

.suggestion-panel__stat-label {
  font-size: 0.6875rem;
  color: #a16207;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.suggestion-panel__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  color: #6b7280;
}

.suggestion-panel__empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.suggestion-panel__empty p {
  margin: 0.25rem 0;
  font-size: 0.875rem;
}

.suggestion-panel__empty-hint {
  font-size: 0.8125rem;
  color: #9ca3af;
}

.suggestion-panel__loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  gap: 1rem;
  color: #6b7280;
}

.suggestion-panel__spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid #e5e7eb;
  border-top-color: #f59e0b;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.suggestion-panel__loading p {
  margin: 0;
  font-size: 0.875rem;
}

.suggestion-panel__list {
  flex: 1;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  overflow-y: auto;
}

.suggestion-panel__footer {
  padding: 0.75rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.5rem;
}

.suggestion-panel__btn {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.suggestion-panel__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.suggestion-panel__btn--analyze {
  background: #f59e0b;
  color: white;
}

.suggestion-panel__btn--analyze:hover:not(:disabled) {
  background: #d97706;
}

.suggestion-panel__btn--clear {
  background: #f3f4f6;
  color: #6b7280;
}

.suggestion-panel__btn--clear:hover {
  background: #e5e7eb;
}

.suggestion-panel__settings {
  padding: 0.75rem;
  border-top: 1px solid #f3f4f6;
  background: #f9fafb;
}

.suggestion-panel__toggle-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #6b7280;
  cursor: pointer;
}

.suggestion-panel__toggle-label input[type="checkbox"] {
  width: 1rem;
  height: 1rem;
  accent-color: #f59e0b;
}

@media (max-width: 768px) {
  .suggestion-panel {
    top: auto;
    bottom: 0;
    left: 0;
    right: 0;
    width: 100%;
    height: 70vh;
    border-radius: 20px 20px 0 0;
    transform: translateY(100%);
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
  }

  .suggestion-panel--open {
    transform: translateY(0);
  }

  .suggestion-panel__header {
    border-radius: 20px 20px 0 0;
    padding: 1rem 1.5rem;
  }

  .suggestion-panel__title {
    font-size: 1.25rem;
  }

  .suggestion-panel__toggle {
    padding: 12px;
    width: auto;
    height: auto;
    min-width: 44px;
    min-height: 44px;
  }

  .suggestion-panel__btn {
    padding: 12px;
    font-size: 1rem;
    min-height: 44px;
  }

  .suggestion-panel__toggle-label {
    font-size: 0.875rem;
  }
}
</style>
