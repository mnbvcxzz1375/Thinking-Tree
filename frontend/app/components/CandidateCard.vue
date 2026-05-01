<template>
  <div
    class="candidate-card"
    :class="{
      'candidate-card--selected': isSelected,
      'candidate-card--high': candidate.confidence >= 0.8,
      'candidate-card--low': candidate.confidence < 0.5,
    }"
    @click="$emit('select', candidate.id)"
  >
    <div class="candidate-card__header">
      <span class="candidate-card__badge" :class="badgeClass">
        {{ badgeLabel }}
      </span>
      <span class="candidate-card__confidence">
        {{ Math.round(candidate.confidence * 100) }}%
      </span>
    </div>

    <div class="candidate-card__body">
      <div class="candidate-card__section">
        <span class="candidate-card__label">语音转录</span>
        <p class="candidate-card__transcript">"{{ candidate.transcript }}"</p>
      </div>

      <div class="candidate-card__section">
        <span class="candidate-card__label">AI 建议</span>
        <p class="candidate-card__text">{{ candidate.leafText }}</p>
      </div>

      <div v-if="candidate.followUpQuestion" class="candidate-card__section">
        <span class="candidate-card__label">追问</span>
        <p class="candidate-card__question">{{ candidate.followUpQuestion }}</p>
      </div>
    </div>

    <div class="candidate-card__actions">
      <button
        class="candidate-card__btn candidate-card__btn--confirm"
        @click.stop="$emit('confirm', candidate.id)"
      >
        确认
      </button>
      <button
        class="candidate-card__btn candidate-card__btn--edit"
        @click.stop="$emit('edit', candidate.id)"
      >
        编辑
      </button>
      <button
        class="candidate-card__btn candidate-card__btn--move"
        @click.stop="$emit('move', candidate.id)"
      >
        移动
      </button>
      <button
        class="candidate-card__btn candidate-card__btn--reject"
        @click.stop="$emit('reject', candidate.id)"
      >
        拒绝
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CandidateNode } from '~/stores/candidate'

interface Props {
  candidate: CandidateNode
  selectedId?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  selectedId: null,
})

defineEmits<{
  select: [id: string]
  confirm: [id: string]
  edit: [id: string]
  move: [id: string]
  reject: [id: string]
}>()

const isSelected = computed(() => props.selectedId === props.candidate.id)

const badgeClass = computed(() => {
  switch (props.candidate.nodeType) {
    case 'question':
      return 'candidate-card__badge--question'
    case 'answer':
      return 'candidate-card__badge--answer'
    case 'insight':
      return 'candidate-card__badge--insight'
    default:
      return ''
  }
})

const badgeLabel = computed(() => {
  switch (props.candidate.nodeType) {
    case 'question':
      return '问题'
    case 'answer':
      return '回答'
    case 'insight':
      return '洞察'
    default:
      return '节点'
  }
})
</script>

<style scoped>
.candidate-card {
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: white;
  cursor: pointer;
  transition: all 0.15s ease;
}

.candidate-card:hover {
  border-color: #c7d2fe;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.1);
}

.candidate-card--selected {
  border-color: #818cf8;
  box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.2);
}

.candidate-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.candidate-card__badge {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-weight: 500;
}

.candidate-card__badge--question {
  background: #dbeafe;
  color: #2563eb;
}

.candidate-card__badge--answer {
  background: #d1fae5;
  color: #059669;
}

.candidate-card__badge--insight {
  background: #fef3c7;
  color: #d97706;
}

.candidate-card__confidence {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 600;
}

.candidate-card--high .candidate-card__confidence {
  color: #059669;
}

.candidate-card--low .candidate-card__confidence {
  color: #d97706;
}

.candidate-card__body {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.candidate-card__section {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.candidate-card__label {
  font-size: 0.6875rem;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.candidate-card__transcript {
  font-size: 0.8125rem;
  color: #6b7280;
  font-style: italic;
  margin: 0;
  line-height: 1.4;
}

.candidate-card__text {
  font-size: 0.875rem;
  color: #111827;
  font-weight: 500;
  margin: 0;
  line-height: 1.4;
}

.candidate-card__question {
  font-size: 0.8125rem;
  color: #4f46e5;
  margin: 0;
  line-height: 1.4;
}

.candidate-card__actions {
  display: flex;
  gap: 0.375rem;
  margin-top: 0.625rem;
  padding-top: 0.625rem;
  border-top: 1px solid #f3f4f6;
}

.candidate-card__btn {
  flex: 1;
  padding: 0.375rem 0.5rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.candidate-card__btn--confirm {
  background: #10b981;
  color: white;
}

.candidate-card__btn--confirm:hover {
  background: #059669;
}

.candidate-card__btn--edit {
  background: #6366f1;
  color: white;
}

.candidate-card__btn--edit:hover {
  background: #4f46e5;
}

.candidate-card__btn--move {
  background: #f59e0b;
  color: white;
}

.candidate-card__btn--move:hover {
  background: #d97706;
}

.candidate-card__btn--reject {
  background: #ef4444;
  color: white;
}

.candidate-card__btn--reject:hover {
  background: #dc2626;
}
</style>
