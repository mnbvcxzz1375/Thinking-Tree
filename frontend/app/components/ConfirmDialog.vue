<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="visible && candidate" class="dialog-overlay" @click.self="$emit('cancel')">
        <div class="dialog" role="dialog" aria-modal="true">
          <div class="dialog__header">
            <h3 class="dialog__title">确认候选节点</h3>
            <button class="dialog__close" @click="$emit('cancel')">×</button>
          </div>

          <div class="dialog__body">
            <!-- Transcript -->
            <div class="dialog__section">
              <label class="dialog__label">语音转录</label>
              <div class="dialog__transcript">
                <span class="dialog__quote">"</span>
                {{ candidate.transcript }}
                <span class="dialog__quote">"</span>
              </div>
            </div>

            <!-- Suggested Parent -->
            <div class="dialog__section">
              <label class="dialog__label">建议父节点</label>
              <div class="dialog__parent">
                <span class="dialog__parent-icon">🔗</span>
                <span>{{ parentLabel }}</span>
              </div>
            </div>

            <!-- Leaf Text (Editable) -->
            <div class="dialog__section">
              <label class="dialog__label" for="leaf-text">节点文本</label>
              <textarea
                id="leaf-text"
                v-model="editedText"
                class="dialog__textarea"
                rows="3"
                placeholder="编辑节点文本..."
              />
              <p class="dialog__hint">AI 建议: {{ candidate.leafText }}</p>
            </div>

            <!-- Follow-up Question -->
            <div v-if="candidate.followUpQuestion" class="dialog__section">
              <label class="dialog__label">追问问题</label>
              <p class="dialog__question">{{ candidate.followUpQuestion }}</p>
            </div>

            <!-- Confidence -->
            <div class="dialog__section">
              <label class="dialog__label">AI 置信度</label>
              <div class="dialog__confidence">
                <div class="dialog__confidence-bar">
                  <div
                    class="dialog__confidence-fill"
                    :style="{ width: `${candidate.confidence * 100}%` }"
                    :class="confidenceClass"
                  />
                </div>
                <span class="dialog__confidence-text">
                  {{ Math.round(candidate.confidence * 100) }}%
                </span>
              </div>
            </div>
          </div>

          <div class="dialog__footer">
            <button class="dialog__btn dialog__btn--cancel" @click="$emit('cancel')">
              取消
            </button>
            <button class="dialog__btn dialog__btn--reject" @click="$emit('reject', candidate.id)">
              拒绝
            </button>
            <button class="dialog__btn dialog__btn--move" @click="$emit('move', candidate.id)">
              移动
            </button>
            <button class="dialog__btn dialog__btn--confirm" @click="handleConfirm">
              {{ isEdited ? '编辑确认' : '确认' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { CandidateNode } from '~/stores/candidate'

interface Props {
  visible: boolean
  candidate: CandidateNode | null
  parentLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  parentLabel: '未指定',
})

const emit = defineEmits<{
  confirm: [id: string, text: string]
  edit: [id: string, text: string]
  move: [id: string]
  reject: [id: string]
  cancel: []
}>()

const editedText = ref('')

const isEdited = computed(() => {
  return props.candidate && editedText.value !== props.candidate.leafText
})

const confidenceClass = computed(() => {
  if (!props.candidate) return ''
  if (props.candidate.confidence >= 0.8) return 'dialog__confidence-fill--high'
  if (props.candidate.confidence >= 0.5) return 'dialog__confidence-fill--medium'
  return 'dialog__confidence-fill--low'
})

// Reset edited text when candidate changes
watch(
  () => props.candidate,
  (newCandidate) => {
    if (newCandidate) {
      editedText.value = newCandidate.leafText
    }
  },
  { immediate: true }
)

function handleConfirm() {
  if (!props.candidate) return
  emit('confirm', props.candidate.id, editedText.value)
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.dialog {
  width: 90%;
  max-width: 32rem;
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.dialog__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #eef2ff, #e0e7ff);
}

.dialog__title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #312e81;
}

.dialog__close {
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 0.375rem;
  background: transparent;
  color: #6b7280;
  font-size: 1.25rem;
  cursor: pointer;
  transition: background 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog__close:hover {
  background: rgba(99, 102, 241, 0.1);
}

.dialog__body {
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.dialog__section {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.dialog__label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.dialog__transcript {
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  color: #374151;
  line-height: 1.5;
  font-style: italic;
}

.dialog__quote {
  color: #9ca3af;
  font-size: 1.25rem;
}

.dialog__parent {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: #f3f4f6;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #374151;
}

.dialog__parent-icon {
  font-size: 1rem;
}

.dialog__textarea {
  width: 100%;
  padding: 0.625rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.9375rem;
  line-height: 1.5;
  resize: vertical;
  transition: border-color 0.15s;
  font-family: inherit;
}

.dialog__textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.dialog__hint {
  margin: 0;
  font-size: 0.75rem;
  color: #9ca3af;
}

.dialog__question {
  margin: 0;
  padding: 0.5rem 0.75rem;
  background: #eef2ff;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #4f46e5;
  line-height: 1.4;
}

.dialog__confidence {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.dialog__confidence-bar {
  flex: 1;
  height: 0.5rem;
  background: #e5e7eb;
  border-radius: 9999px;
  overflow: hidden;
}

.dialog__confidence-fill {
  height: 100%;
  border-radius: 9999px;
  transition: width 0.3s ease;
}

.dialog__confidence-fill--high {
  background: #10b981;
}

.dialog__confidence-fill--medium {
  background: #f59e0b;
}

.dialog__confidence-fill--low {
  background: #ef4444;
}

.dialog__confidence-text {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  min-width: 3rem;
  text-align: right;
}

.dialog__footer {
  padding: 1rem 1.25rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.5rem;
  background: #f9fafb;
}

.dialog__btn {
  flex: 1;
  padding: 0.625rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.dialog__btn--cancel {
  background: #f3f4f6;
  color: #6b7280;
}

.dialog__btn--cancel:hover {
  background: #e5e7eb;
}

.dialog__btn--reject {
  background: #fee2e2;
  color: #dc2626;
}

.dialog__btn--reject:hover {
  background: #fecaca;
}

.dialog__btn--move {
  background: #fef3c7;
  color: #d97706;
}

.dialog__btn--move:hover {
  background: #fde68a;
}

.dialog__btn--confirm {
  background: #10b981;
  color: white;
}

.dialog__btn--confirm:hover {
  background: #059669;
}

/* Transitions */
.dialog-enter-active,
.dialog-leave-active {
  transition: opacity 0.2s ease;
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}

.dialog-enter-active .dialog,
.dialog-leave-active .dialog {
  transition: transform 0.2s ease;
}

.dialog-enter-from .dialog,
.dialog-leave-to .dialog {
  transform: scale(0.95);
}
</style>
