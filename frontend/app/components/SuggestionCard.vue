<template>
  <div
    class="suggestion-card"
    :class="{
      'suggestion-card--selected': isSelected,
      'suggestion-card--critical': suggestion.priority === 'critical',
      'suggestion-card--high': suggestion.priority === 'high',
    }"
    @click="$emit('select', suggestion.id)"
  >
    <div class="suggestion-card__header">
      <div class="suggestion-card__badges">
        <span class="suggestion-card__type-badge" :class="typeBadgeClass">
          {{ typeLabel }}
        </span>
        <span class="suggestion-card__priority-badge" :class="priorityBadgeClass">
          {{ priorityLabel }}
        </span>
      </div>
      <span class="suggestion-card__icon">{{ typeIcon }}</span>
    </div>

    <div class="suggestion-card__body">
      <h4 class="suggestion-card__title">{{ suggestion.title }}</h4>
      <p class="suggestion-card__description">{{ suggestion.description }}</p>

      <div v-if="suggestion.reasoning" class="suggestion-card__reasoning">
        <span class="suggestion-card__reasoning-label">💡 原因</span>
        <p class="suggestion-card__reasoning-text">{{ suggestion.reasoning }}</p>
      </div>

      <div v-if="suggestion.suggestedContent" class="suggestion-card__suggested">
        <span class="suggestion-card__suggested-label">📝 建议内容</span>
        <p class="suggestion-card__suggested-text">{{ suggestion.suggestedContent }}</p>
      </div>
    </div>

    <div class="suggestion-card__actions">
      <button
        class="suggestion-card__btn suggestion-card__btn--accept"
        @click.stop="$emit('accept', suggestion.id)"
      >
        ✓ 采纳
      </button>
      <button
        class="suggestion-card__btn suggestion-card__btn--reject"
        @click.stop="$emit('reject', suggestion.id)"
      >
        ✕ 拒绝
      </button>
      <button
        class="suggestion-card__btn suggestion-card__btn--dismiss"
        @click.stop="$emit('dismiss', suggestion.id)"
      >
        稍后
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Suggestion } from '~/stores/suggestions'

interface Props {
  suggestion: Suggestion
  selectedId?: number | null
}

const props = withDefaults(defineProps<Props>(), {
  selectedId: null,
})

defineEmits<{
  select: [id: number]
  accept: [id: number]
  reject: [id: number]
  dismiss: [id: number]
}>()

const isSelected = computed(() => props.selectedId === props.suggestion.id)

const typeBadgeClass = computed(() => {
  switch (props.suggestion.suggestionType) {
    case 'merge':
      return 'suggestion-card__type-badge--merge'
    case 'split':
      return 'suggestion-card__type-badge--split'
    case 'new_direction':
      return 'suggestion-card__type-badge--direction'
    case 'rebalance':
      return 'suggestion-card__type-badge--rebalance'
    case 'connect':
      return 'suggestion-card__type-badge--connect'
    default:
      return ''
  }
})

const typeLabel = computed(() => {
  switch (props.suggestion.suggestionType) {
    case 'merge':
      return '合并'
    case 'split':
      return '拆分'
    case 'new_direction':
      return '新方向'
    case 'rebalance':
      return '平衡'
    case 'connect':
      return '关联'
    default:
      return '建议'
  }
})

const typeIcon = computed(() => {
  switch (props.suggestion.suggestionType) {
    case 'merge':
      return '🔗'
    case 'split':
      return '✂️'
    case 'new_direction':
      return '🧭'
    case 'rebalance':
      return '⚖️'
    case 'connect':
      return '🕸️'
    default:
      return '💡'
  }
})

const priorityBadgeClass = computed(() => {
  switch (props.suggestion.priority) {
    case 'critical':
      return 'suggestion-card__priority-badge--critical'
    case 'high':
      return 'suggestion-card__priority-badge--high'
    case 'medium':
      return 'suggestion-card__priority-badge--medium'
    case 'low':
      return 'suggestion-card__priority-badge--low'
    default:
      return ''
  }
})

const priorityLabel = computed(() => {
  switch (props.suggestion.priority) {
    case 'critical':
      return '紧急'
    case 'high':
      return '重要'
    case 'medium':
      return '一般'
    case 'low':
      return '建议'
    default:
      return ''
  }
})
</script>

<style scoped>
.suggestion-card {
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
}

.suggestion-card:hover {
  border-color: #c7d2fe;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
}

.suggestion-card--selected {
  border-color: #818cf8;
  box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.2);
}

.suggestion-card--critical {
  border-left: 4px solid #ef4444;
}

.suggestion-card--high {
  border-left: 4px solid #f59e0b;
}

.suggestion-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.suggestion-card__badges {
  display: flex;
  gap: 0.5rem;
}

.suggestion-card__type-badge {
  font-size: 0.6875rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.suggestion-card__type-badge--merge {
  background: #dbeafe;
  color: #2563eb;
}

.suggestion-card__type-badge--split {
  background: #fce7f3;
  color: #db2777;
}

.suggestion-card__type-badge--direction {
  background: #d1fae5;
  color: #059669;
}

.suggestion-card__type-badge--rebalance {
  background: #fef3c7;
  color: #d97706;
}

.suggestion-card__type-badge--connect {
  background: #e0e7ff;
  color: #4f46e5;
}

.suggestion-card__priority-badge {
  font-size: 0.6875rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-weight: 500;
}

.suggestion-card__priority-badge--critical {
  background: #fef2f2;
  color: #dc2626;
}

.suggestion-card__priority-badge--high {
  background: #fffbeb;
  color: #d97706;
}

.suggestion-card__priority-badge--medium {
  background: #f3f4f6;
  color: #6b7280;
}

.suggestion-card__priority-badge--low {
  background: #f0fdf4;
  color: #16a34a;
}

.suggestion-card__icon {
  font-size: 1.5rem;
}

.suggestion-card__body {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.suggestion-card__title {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 600;
  color: #111827;
  line-height: 1.4;
}

.suggestion-card__description {
  margin: 0;
  font-size: 0.8125rem;
  color: #4b5563;
  line-height: 1.5;
}

.suggestion-card__reasoning {
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 0.375rem;
  border-left: 3px solid #e5e7eb;
}

.suggestion-card__reasoning-label {
  font-size: 0.6875rem;
  color: #9ca3af;
  font-weight: 500;
  display: block;
  margin-bottom: 0.25rem;
}

.suggestion-card__reasoning-text {
  margin: 0;
  font-size: 0.75rem;
  color: #6b7280;
  line-height: 1.5;
  font-style: italic;
}

.suggestion-card__suggested {
  padding: 0.5rem;
  background: #eff6ff;
  border-radius: 0.375rem;
  border-left: 3px solid #93c5fd;
}

.suggestion-card__suggested-label {
  font-size: 0.6875rem;
  color: #3b82f6;
  font-weight: 500;
  display: block;
  margin-bottom: 0.25rem;
}

.suggestion-card__suggested-text {
  margin: 0;
  font-size: 0.8125rem;
  color: #1e40af;
  line-height: 1.5;
}

.suggestion-card__actions {
  display: flex;
  gap: 0.375rem;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #f3f4f6;
}

.suggestion-card__btn {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.suggestion-card__btn--accept {
  background: #10b981;
  color: white;
}

.suggestion-card__btn--accept:hover {
  background: #059669;
}

.suggestion-card__btn--reject {
  background: #ef4444;
  color: white;
}

.suggestion-card__btn--reject:hover {
  background: #dc2626;
}

.suggestion-card__btn--dismiss {
  background: #f3f4f6;
  color: #6b7280;
}

.suggestion-card__btn--dismiss:hover {
  background: #e5e7eb;
}

@media (max-width: 768px) {
  .suggestion-card {
    padding: 0.875rem;
  }

  .suggestion-card__title {
    font-size: 1rem;
  }

  .suggestion-card__description {
    font-size: 0.875rem;
  }

  .suggestion-card__btn {
    padding: 0.625rem;
    font-size: 0.875rem;
    min-height: 44px;
  }
}
</style>
