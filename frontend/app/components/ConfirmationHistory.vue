<template>
  <div class="history" :class="{ 'history--open': isOpen }">
    <div class="history__header">
      <div class="history__title-row">
        <h3 class="history__title">确认历史</h3>
        <button class="history__toggle" @click="$emit('toggle')">
          {{ isOpen ? '✕' : '📋' }}
        </button>
      </div>
      <p class="history__subtitle">
        {{ recentHistory.length }} 条记录
      </p>
    </div>

    <div v-if="isOpen" class="history__body">
      <div v-if="recentHistory.length === 0" class="history__empty">
        <span class="history__empty-icon">📝</span>
        <p>暂无确认记录</p>
      </div>

      <div v-else class="history__list">
        <div
          v-for="record in recentHistory"
          :key="record.id"
          class="history__item"
          :class="`history__item--${record.action}`"
        >
          <div class="history__item-header">
            <span class="history__action-badge" :class="`history__action-badge--${record.action}`">
              {{ actionLabel(record.action) }}
            </span>
            <span class="history__time">{{ formatTime(record.confirmedAt) }}</span>
          </div>

          <p class="history__text">
            {{ record.finalText || record.originalCandidate.leafText }}
          </p>

          <p class="history__transcript">
            "{{ record.originalCandidate.transcript }}"
          </p>

          <div class="history__item-actions">
            <button
              v-if="record.undoable"
              class="history__undo-btn"
              @click="$emit('undo', record.id)"
            >
              撤销
            </button>
            <span v-else class="history__undo-expired">已过期</span>
          </div>
        </div>
      </div>

      <div v-if="recentHistory.length > 0" class="history__footer">
        <button class="history__export-btn" @click="$emit('export')">
          导出日志
        </button>
        <button class="history__clear-btn" @click="$emit('clear')">
          清空历史
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
  undo: [recordId: string]
  export: []
  clear: []
}>()

const candidateStore = useCandidateStore()
const { recentHistory } = storeToRefs(candidateStore)

function actionLabel(action: string): string {
  switch (action) {
    case 'confirm':
      return '确认'
    case 'edit':
      return '编辑'
    case 'move':
      return '移动'
    case 'reject':
      return '拒绝'
    default:
      return action
  }
}

function formatTime(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays < 7) return `${diffDays} 天前`

  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.history {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 20rem;
  background: white;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.1);
  transform: translateX(-100%);
  transition: transform 0.3s ease;
  z-index: 50;
  display: flex;
  flex-direction: column;
}

.history--open {
  transform: translateX(0);
}

.history__header {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
}

.history__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.history__title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #92400e;
}

.history__subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.8125rem;
  color: #b45309;
}

.history__toggle {
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 0.375rem;
  background: rgba(245, 158, 11, 0.15);
  color: #d97706;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.history__toggle:hover {
  background: rgba(245, 158, 11, 0.25);
}

.history__body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.history__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  color: #6b7280;
}

.history__empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.history__empty p {
  margin: 0;
  font-size: 0.875rem;
}

.history__list {
  flex: 1;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  overflow-y: auto;
}

.history__item {
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: white;
  transition: all 0.15s;
}

.history__item:hover {
  border-color: #c7d2fe;
}

.history__item--confirm {
  border-left: 3px solid #10b981;
}

.history__item--edit {
  border-left: 3px solid #6366f1;
}

.history__item--move {
  border-left: 3px solid #f59e0b;
}

.history__item--reject {
  border-left: 3px solid #ef4444;
}

.history__item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.375rem;
}

.history__action-badge {
  font-size: 0.6875rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-weight: 500;
}

.history__action-badge--confirm {
  background: #d1fae5;
  color: #059669;
}

.history__action-badge--edit {
  background: #e0e7ff;
  color: #4f46e5;
}

.history__action-badge--move {
  background: #fef3c7;
  color: #d97706;
}

.history__action-badge--reject {
  background: #fee2e2;
  color: #dc2626;
}

.history__time {
  font-size: 0.6875rem;
  color: #9ca3af;
}

.history__text {
  margin: 0 0 0.25rem;
  font-size: 0.875rem;
  color: #111827;
  font-weight: 500;
  line-height: 1.4;
}

.history__transcript {
  margin: 0;
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
  line-height: 1.4;
}

.history__item-actions {
  margin-top: 0.5rem;
  display: flex;
  justify-content: flex-end;
}

.history__undo-btn {
  padding: 0.25rem 0.625rem;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  background: white;
  color: #374151;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
}

.history__undo-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.history__undo-expired {
  font-size: 0.6875rem;
  color: #9ca3af;
}

.history__footer {
  padding: 0.75rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.5rem;
}

.history__export-btn,
.history__clear-btn {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.history__export-btn {
  background: #6366f1;
  color: white;
}

.history__export-btn:hover {
  background: #4f46e5;
}

.history__clear-btn {
  background: #f3f4f6;
  color: #6b7280;
}

.history__clear-btn:hover {
  background: #e5e7eb;
}
</style>
