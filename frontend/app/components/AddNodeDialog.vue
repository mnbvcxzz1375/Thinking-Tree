<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="visible" class="dialog-overlay" @click.self="$emit('cancel')">
        <div class="dialog" role="dialog" aria-modal="true">
          <div class="dialog__header">
            <h3 class="dialog__title">{{ title }}</h3>
            <button class="dialog__close" @click="$emit('cancel')">×</button>
          </div>

          <div class="dialog__body">
            <TreeNodeForm
              :initial-content="initialContent"
              :initial-type="initialType"
              :submit-label="submitLabel"
              @submit="handleSubmit"
              @cancel="$emit('cancel')"
            />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import type { TreeNodeCreateInput, TreeNodeUpdateInput } from '~/stores/tree'

interface Props {
  visible: boolean
  title?: string
  initialContent?: string
  initialType?: string
  submitLabel?: string
}

withDefaults(defineProps<Props>(), {
  title: '添加节点',
  initialContent: '',
  initialType: 'question',
  submitLabel: '添加',
})

const emit = defineEmits<{
  submit: [data: TreeNodeCreateInput | TreeNodeUpdateInput]
  cancel: []
}>()

function handleSubmit(data: TreeNodeCreateInput | TreeNodeUpdateInput) {
  emit('submit', data)
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
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
}

.dialog {
  width: 90%;
  max-width: 28rem;
  background: #fff;
  border-radius: 0.75rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.dialog__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e5e7eb;
}

.dialog__title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
}

.dialog__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 1.25rem;
  cursor: pointer;
  background: transparent;
  color: #6b7280;
  transition: background 0.15s;
}

.dialog__close:hover {
  background: #f3f4f6;
}

.dialog__body {
  padding: 1.25rem;
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
