<template>
  <div class="candidate-panel" :class="{ 'candidate-panel--open': isOpen }">
    <div class="candidate-panel__header">
      <div class="candidate-panel__title-row">
        <h3 class="candidate-panel__title">
          AI 候选节点
          <span v-if="pendingCount > 0" class="candidate-panel__count">
            {{ pendingCount }}
          </span>
        </h3>
        <button class="candidate-panel__toggle" @click="$emit('toggle')">
          {{ isOpen ? '✕' : '✨' }}
        </button>
      </div>
      <p v-if="pendingCount > 0" class="candidate-panel__subtitle">
        等待确认的 AI 建议
      </p>
      <p v-else class="candidate-panel__subtitle candidate-panel__subtitle--empty">
        暂无候选节点
      </p>
    </div>

    <div v-if="isOpen" class="candidate-panel__body">
      <div v-if="pendingCount === 0" class="candidate-panel__empty">
        <span class="candidate-panel__empty-icon">🌳</span>
        <p>AI 正在分析孩子的发言...</p>
        <p class="candidate-panel__empty-hint">候选节点将在这里显示</p>
      </div>

      <div v-else class="candidate-panel__list">
        <CandidateCard
          v-for="candidate in pendingCandidates"
          :key="candidate.id"
          :candidate="candidate"
          :selected-id="selectedCandidateId"
          @select="$emit('select', $event)"
          @confirm="$emit('confirm', $event)"
          @edit="$emit('edit', $event)"
          @move="$emit('move', $event)"
          @reject="$emit('reject', $event)"
        />
      </div>

      <div v-if="pendingCount > 0" class="candidate-panel__footer">
        <button
          class="candidate-panel__btn candidate-panel__btn--confirm-all"
          @click="$emit('confirm-all')"
        >
          全部确认
        </button>
        <button
          class="candidate-panel__btn candidate-panel__btn--clear"
          @click="$emit('clear-all')"
        >
          清空
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useCandidateStore } from '~/stores/candidate'

interface Props {
  isOpen: boolean
}

defineProps<Props>()

defineEmits<{
  toggle: []
  select: [id: string]
  confirm: [id: string]
  edit: [id: string]
  move: [id: string]
  reject: [id: string]
  'confirm-all': []
  'clear-all': []
}>()

const candidateStore = useCandidateStore()
const { pendingCandidates, pendingCount, selectedCandidateId } = storeToRefs(candidateStore)
</script>

<style scoped>
.candidate-panel {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 20rem;
  background: white;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 50;
  display: flex;
  flex-direction: column;
}

.candidate-panel--open {
  transform: translateX(0);
}

.candidate-panel__header {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #eef2ff, #e0e7ff);
}

.candidate-panel__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.candidate-panel__title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #312e81;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.candidate-panel__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.375rem;
  border-radius: 9999px;
  background: #6366f1;
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
}

.candidate-panel__subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.8125rem;
  color: #6366f1;
}

.candidate-panel__subtitle--empty {
  color: #9ca3af;
}

.candidate-panel__toggle {
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 0.375rem;
  background: rgba(99, 102, 241, 0.1);
  color: #4f46e5;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.candidate-panel__toggle:hover {
  background: rgba(99, 102, 241, 0.2);
}

.candidate-panel__body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.candidate-panel__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  color: #6b7280;
}

.candidate-panel__empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.candidate-panel__empty p {
  margin: 0.25rem 0;
  font-size: 0.875rem;
}

.candidate-panel__empty-hint {
  font-size: 0.8125rem;
  color: #9ca3af;
}

.candidate-panel__list {
  flex: 1;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  overflow-y: auto;
}

.candidate-panel__footer {
  padding: 0.75rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.5rem;
}

.candidate-panel__btn {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.candidate-panel__btn--confirm-all {
  background: #10b981;
  color: white;
}

.candidate-panel__btn--confirm-all:hover {
  background: #059669;
}

.candidate-panel__btn--clear {
  background: #f3f4f6;
  color: #6b7280;
}

.candidate-panel__btn--clear:hover {
  background: #e5e7eb;
}
@media (max-width: 768px) {
  .candidate-panel {
    top: auto;
    bottom: 0;
    left: 0;
    right: 0;
    width: 100%;
    height: 60vh;
    border-radius: 20px 20px 0 0;
    transform: translateY(100%);
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
  }

  .candidate-panel--open {
    transform: translateY(0);
  }

  .candidate-panel__header {
    border-radius: 20px 20px 0 0;
    padding: 1rem 1.5rem;
  }
  
  .candidate-panel__title {
    font-size: 1.25rem;
  }
  
  .candidate-panel__toggle {
    padding: 12px;
    width: auto;
    height: auto;
    min-width: 44px;
    min-height: 44px;
  }
  
  .candidate-panel__btn {
    padding: 12px;
    font-size: 1rem;
    min-height: 44px;
  }
}
</style>
