<template>
  <form class="node-form" @submit.prevent="handleSubmit">
    <div class="node-form__field">
      <label class="node-form__label" for="node-content">节点内容</label>
      <textarea
        id="node-content"
        v-model="form.content"
        class="node-form__textarea"
        placeholder="输入节点内容..."
        rows="3"
        required
      />
    </div>

    <div class="node-form__field">
      <label class="node-form__label">节点类型</label>
      <div class="node-form__types">
        <label
          v-for="t in nodeTypes"
          :key="t.value"
          class="node-form__type-option"
          :class="{ 'node-form__type-option--active': form.node_type === t.value }"
        >
          <input
            v-model="form.node_type"
            type="radio"
            :value="t.value"
            class="node-form__radio"
          />
          <span class="node-form__type-icon">{{ t.icon }}</span>
          <span class="node-form__type-label">{{ t.label }}</span>
        </label>
      </div>
    </div>

    <div class="node-form__actions">
      <button type="button" class="btn btn--outline" @click="$emit('cancel')">
        取消
      </button>
      <button type="submit" class="btn btn--primary" :disabled="!isValid">
        {{ submitLabel }}
      </button>
    </div>
  </form>
</template>

<script setup lang="ts">
import { reactive, computed } from 'vue'
import type { TreeNodeCreateInput, TreeNodeUpdateInput } from '~/stores/tree'

interface Props {
  initialContent?: string
  initialType?: string
  submitLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  initialContent: '',
  initialType: 'question',
  submitLabel: '保存',
})

const emit = defineEmits<{
  submit: [data: TreeNodeCreateInput | TreeNodeUpdateInput]
  cancel: []
}>()

const nodeTypes = [
  { value: 'question', label: '问题', icon: '❓' },
  { value: 'answer', label: '回答', icon: '💡' },
  { value: 'insight', label: '洞察', icon: '⭐' },
]

const form = reactive({
  content: props.initialContent,
  node_type: props.initialType,
})

const isValid = computed(() => form.content.trim().length > 0)

function handleSubmit() {
  if (!isValid.value) return
  emit('submit', {
    content: form.content.trim(),
    node_type: form.node_type,
  })
}
</script>

<style scoped>
.node-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.node-form__field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.node-form__label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.node-form__textarea {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.9375rem;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s;
}

.node-form__textarea:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
}

.node-form__types {
  display: flex;
  gap: 0.5rem;
}

.node-form__type-option {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 0.875rem;
}

.node-form__type-option:hover {
  border-color: #9ca3af;
}

.node-form__type-option--active {
  border-color: #2563eb;
  background: #eff6ff;
}

.node-form__radio {
  display: none;
}

.node-form__type-icon {
  font-size: 1rem;
}

.node-form__type-label {
  color: #374151;
}

.node-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
}

.btn--outline {
  background: #fff;
  border-color: #d1d5db;
  color: #374151;
}

.btn--outline:hover {
  background: #f9fafb;
}

.btn--primary {
  background: #2563eb;
  color: #fff;
}

.btn--primary:hover {
  background: #1d4ed8;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
