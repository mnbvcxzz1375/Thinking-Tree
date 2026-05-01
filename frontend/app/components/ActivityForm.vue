<template>
  <form class="activity-form" @submit.prevent="handleSubmit">
    <div class="activity-form__group">
      <label for="title" class="activity-form__label">
        活动标题 <span class="required">*</span>
      </label>
      <input
        id="title"
        v-model="form.title"
        type="text"
        class="activity-form__input"
        placeholder="请输入活动标题"
        required
        maxlength="255"
      />
      <span v-if="errors.title" class="activity-form__error">{{ errors.title }}</span>
    </div>

    <div class="activity-form__group">
      <label for="description" class="activity-form__label">活动描述</label>
      <textarea
        id="description"
        v-model="form.description"
        class="activity-form__textarea"
        placeholder="请输入活动描述"
        rows="3"
      />
    </div>

    <div class="activity-form__group">
      <label for="instructions" class="activity-form__label">活动指导</label>
      <textarea
        id="instructions"
        v-model="form.instructions"
        class="activity-form__textarea"
        placeholder="请输入活动指导说明"
        rows="4"
      />
    </div>

    <div class="activity-form__row">
      <div class="activity-form__group">
        <label for="difficulty" class="activity-form__label">难度等级</label>
        <select
          id="difficulty"
          v-model="form.difficulty_level"
          class="activity-form__select"
        >
          <option value="easy">简单</option>
          <option value="medium">中等</option>
          <option value="hard">困难</option>
        </select>
      </div>

      <div class="activity-form__group">
        <label for="age_group" class="activity-form__label">适用年龄</label>
        <input
          id="age_group"
          v-model="form.age_group"
          type="text"
          class="activity-form__input"
          placeholder="例如: 6-8岁"
        />
      </div>
    </div>

    <div class="activity-form__group activity-form__group--checkbox">
      <label class="activity-form__checkbox-label">
        <input
          v-model="form.is_active"
          type="checkbox"
          class="activity-form__checkbox"
        />
        <span>启用活动</span>
      </label>
    </div>

    <div v-if="error" class="activity-form__alert">
      {{ error }}
    </div>

    <div class="activity-form__actions">
      <button type="button" class="btn btn--outline" @click="$emit('cancel')">
        取消
      </button>
      <button type="submit" class="btn btn--primary" :disabled="submitting">
        {{ submitting ? '保存中...' : submitLabel }}
      </button>
    </div>
  </form>
</template>

<script setup lang="ts">
import type { Activity, ActivityCreateInput, ActivityUpdateInput } from '~/stores/activity'

interface Props {
  activity?: Activity | null
  submitLabel?: string
  submitting?: boolean
  error?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  activity: null,
  submitLabel: '保存',
  submitting: false,
  error: null,
})

const emit = defineEmits<{
  submit: [data: ActivityCreateInput | ActivityUpdateInput]
  cancel: []
}>()

const form = reactive({
  title: props.activity?.title ?? '',
  description: props.activity?.description ?? '',
  instructions: props.activity?.instructions ?? '',
  difficulty_level: (props.activity?.difficulty_level ?? 'medium') as 'easy' | 'medium' | 'hard',
  age_group: props.activity?.age_group ?? '',
  is_active: props.activity?.is_active ?? true,
})

const errors = reactive({
  title: '',
})

// Watch for external activity changes (e.g., when data loads)
watch(
  () => props.activity,
  (newActivity) => {
    if (newActivity) {
      form.title = newActivity.title
      form.description = newActivity.description ?? ''
      form.instructions = newActivity.instructions ?? ''
      form.difficulty_level = newActivity.difficulty_level
      form.age_group = newActivity.age_group ?? ''
      form.is_active = newActivity.is_active
    }
  },
  { deep: true }
)

function validate(): boolean {
  errors.title = ''
  if (!form.title.trim()) {
    errors.title = '请输入活动标题'
    return false
  }
  return true
}

function handleSubmit() {
  if (!validate()) return

  const data: ActivityCreateInput = {
    title: form.title.trim(),
    description: form.description.trim() || undefined,
    instructions: form.instructions.trim() || undefined,
    difficulty_level: form.difficulty_level,
    age_group: form.age_group.trim() || undefined,
    is_active: form.is_active,
  }

  emit('submit', data)
}
</script>

<style scoped>
.activity-form {
  max-width: 640px;
}
.activity-form__group {
  margin-bottom: 1.25rem;
}
.activity-form__group--checkbox {
  margin-top: 0.5rem;
}
.activity-form__label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.375rem;
}
.required {
  color: #dc2626;
}
.activity-form__input,
.activity-form__textarea,
.activity-form__select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #111827;
  background: #fff;
  transition: border-color 0.15s;
}
.activity-form__input:focus,
.activity-form__textarea:focus,
.activity-form__select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
}
.activity-form__textarea {
  resize: vertical;
  min-height: 80px;
}
.activity-form__select {
  appearance: auto;
}
.activity-form__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
.activity-form__checkbox-label {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
}
.activity-form__checkbox {
  width: 1rem;
  height: 1rem;
  accent-color: #2563eb;
}
.activity-form__error {
  display: block;
  font-size: 0.75rem;
  color: #dc2626;
  margin-top: 0.25rem;
}
.activity-form__alert {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #991b1b;
  padding: 0.75rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}
.activity-form__actions {
  display: flex;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

/* Button styles */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1.25rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn--outline {
  background: #fff;
  border-color: #d1d5db;
  color: #374151;
}
.btn--outline:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #9ca3af;
}
.btn--primary {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}
.btn--primary:hover:not(:disabled) {
  background: #1d4ed8;
}
</style>
