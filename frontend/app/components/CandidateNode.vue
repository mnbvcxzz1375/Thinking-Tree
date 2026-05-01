<template>
  <div
    class="candidate-node"
    :class="{
      'candidate-node--selected': isSelected,
      'candidate-node--high-confidence': candidate.confidence >= 0.8,
      'candidate-node--low-confidence': candidate.confidence < 0.5,
    }"
    @click.stop="$emit('select', candidate.id)"
  >
    <div class="candidate-node__glow" />
    <div class="candidate-node__content">
      <span class="candidate-node__icon">✨</span>
      <span class="candidate-node__text">{{ candidate.leafText }}</span>
      <span class="candidate-node__confidence">{{ Math.round(candidate.confidence * 100) }}%</span>
    </div>
    <div class="candidate-node__actions">
      <button
        class="candidate-node__btn candidate-node__btn--confirm"
        title="确认"
        @click.stop="$emit('confirm', candidate.id)"
      >
        ✓
      </button>
      <button
        class="candidate-node__btn candidate-node__btn--reject"
        title="拒绝"
        @click.stop="$emit('reject', candidate.id)"
      >
        ✕
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
  reject: [id: string]
}>()

const isSelected = computed(() => props.selectedId === props.candidate.id)
</script>

<style scoped>
.candidate-node {
  position: relative;
  cursor: pointer;
  padding: 0.5rem 0.75rem;
  border: 2px dashed rgba(99, 102, 241, 0.4);
  border-radius: 0.5rem;
  background: rgba(99, 102, 241, 0.08);
  transition: all 0.2s ease;
  animation: candidatePulse 2s ease-in-out infinite;
}

.candidate-node:hover {
  border-color: rgba(99, 102, 241, 0.6);
  background: rgba(99, 102, 241, 0.12);
}

.candidate-node--selected {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.15);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}

.candidate-node__glow {
  position: absolute;
  inset: -4px;
  border-radius: 0.75rem;
  background: radial-gradient(
    ellipse at center,
    rgba(99, 102, 241, 0.15) 0%,
    transparent 70%
  );
  pointer-events: none;
  animation: glowPulse 2s ease-in-out infinite;
}

.candidate-node__content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  z-index: 1;
}

.candidate-node__icon {
  font-size: 1rem;
  animation: sparkle 1.5s ease-in-out infinite;
}

.candidate-node__text {
  flex: 1;
  font-size: 0.875rem;
  color: #4338ca;
  font-weight: 500;
}

.candidate-node__confidence {
  font-size: 0.75rem;
  padding: 0.125rem 0.375rem;
  border-radius: 9999px;
  background: rgba(99, 102, 241, 0.15);
  color: #4338ca;
  font-weight: 600;
}

.candidate-node--high-confidence .candidate-node__confidence {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}

.candidate-node--low-confidence .candidate-node__confidence {
  background: rgba(245, 158, 11, 0.15);
  color: #d97706;
}

.candidate-node__actions {
  display: flex;
  gap: 0.25rem;
  margin-top: 0.375rem;
  opacity: 0;
  transition: opacity 0.15s;
}

.candidate-node:hover .candidate-node__actions {
  opacity: 1;
}

.candidate-node__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
}

.candidate-node__btn--confirm {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}

.candidate-node__btn--confirm:hover {
  background: #10b981;
  color: white;
}

.candidate-node__btn--reject {
  background: rgba(239, 68, 68, 0.15);
  color: #dc2626;
}

.candidate-node__btn--reject:hover {
  background: #ef4444;
  color: white;
}

@keyframes candidatePulse {
  0%, 100% {
    opacity: 0.8;
  }
  50% {
    opacity: 1;
  }
}

@keyframes glowPulse {
  0%, 100% {
    opacity: 0.5;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.02);
  }
}

@keyframes sparkle {
  0%, 100% {
    transform: scale(1) rotate(0deg);
  }
  50% {
    transform: scale(1.2) rotate(10deg);
  }
}
</style>
