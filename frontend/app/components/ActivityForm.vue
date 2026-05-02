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
        placeholder="示例：围绕“放走蚂蚁/踩扁蚂蚁”展开讨论，引导孩子说出自己的理由、感受和可能的后果。"
        rows="3"
      />
    </div>

    <div class="activity-form__group">
      <label for="instructions" class="activity-form__label">活动指导</label>
      <textarea
        id="instructions"
        v-model="form.instructions"
        class="activity-form__textarea"
        placeholder="示例：先让孩子自由表达，不急着判断对错；追问“为什么这么想？”“还有别的可能吗？”；把相近想法合并到同一片叶子。"
        rows="4"
      />
    </div>

    <div class="activity-form__group">
      <label class="activity-form__label">活动模式</label>
      <div class="activity-form__mode-tabs">
        <button
          type="button"
          class="activity-form__mode-tab"
          :class="{ 'activity-form__mode-tab--active': form.activity_mode === 'normal' }"
          @click="form.activity_mode = 'normal'"
        >
          普通思维树
        </button>
        <button
          type="button"
          class="activity-form__mode-tab"
          :class="{ 'activity-form__mode-tab--active': form.activity_mode === 'debate' }"
          @click="form.activity_mode = 'debate'"
        >
          辩论模式
        </button>
      </div>
      <p class="activity-form__hint">
        辩论模式会在树模板中生成左右正反方，并影响录音归类提示。
      </p>
    </div>

    <div v-if="form.activity_mode === 'debate'" class="activity-form__row">
      <div class="activity-form__group">
        <label for="debate_pro_label" class="activity-form__label">
          正方观点 <span class="required">*</span>
        </label>
        <input
          id="debate_pro_label"
          v-model="form.debate_pro_label"
          type="text"
          class="activity-form__input"
          placeholder="例如：放走蚂蚁"
          maxlength="255"
        />
        <span v-if="errors.debate_pro_label" class="activity-form__error">{{ errors.debate_pro_label }}</span>
      </div>

      <div class="activity-form__group">
        <label for="debate_con_label" class="activity-form__label">
          反方观点 <span class="required">*</span>
        </label>
        <input
          id="debate_con_label"
          v-model="form.debate_con_label"
          type="text"
          class="activity-form__input"
          placeholder="例如：踩扁蚂蚁"
          maxlength="255"
        />
        <span v-if="errors.debate_con_label" class="activity-form__error">{{ errors.debate_con_label }}</span>
      </div>
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
  activity_mode: (props.activity?.activity_mode ?? 'normal') as 'normal' | 'debate',
  debate_pro_label: props.activity?.debate_pro_label ?? '放走蚂蚁',
  debate_con_label: props.activity?.debate_con_label ?? '踩扁蚂蚁',
  difficulty_level: (props.activity?.difficulty_level ?? 'medium') as 'easy' | 'medium' | 'hard',
  age_group: props.activity?.age_group ?? '',
  is_active: props.activity?.is_active ?? true,
})

const errors = reactive({
  title: '',
  debate_pro_label: '',
  debate_con_label: '',
})

// Watch for external activity changes (e.g., when data loads)
watch(
  () => props.activity,
  (newActivity) => {
    if (newActivity) {
      form.title = newActivity.title
      form.description = newActivity.description ?? ''
      form.instructions = newActivity.instructions ?? ''
      form.activity_mode = newActivity.activity_mode ?? 'normal'
      form.debate_pro_label = newActivity.debate_pro_label ?? '放走蚂蚁'
      form.debate_con_label = newActivity.debate_con_label ?? '踩扁蚂蚁'
      form.difficulty_level = newActivity.difficulty_level
      form.age_group = newActivity.age_group ?? ''
      form.is_active = newActivity.is_active
    }
  },
  { deep: true }
)

function validate(): boolean {
  errors.title = ''
  errors.debate_pro_label = ''
  errors.debate_con_label = ''
  if (!form.title.trim()) {
    errors.title = '请输入活动标题'
    return false
  }
  if (form.activity_mode === 'debate') {
    if (!form.debate_pro_label.trim()) {
      errors.debate_pro_label = '请输入正方观点'
      return false
    }
    if (!form.debate_con_label.trim()) {
      errors.debate_con_label = '请输入反方观点'
      return false
    }
  }
  return true
}

function handleSubmit() {
  if (!validate()) return

  const data: ActivityCreateInput = {
    title: form.title.trim(),
    description: form.description.trim() || undefined,
    instructions: form.instructions.trim() || undefined,
    activity_mode: form.activity_mode,
    debate_pro_label: form.activity_mode === 'debate' ? form.debate_pro_label.trim() : undefined,
    debate_con_label: form.activity_mode === 'debate' ? form.debate_con_label.trim() : undefined,
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
  width: 100%;
  padding-bottom: 1.25rem;
}
.activity-form__group {
  margin-bottom: 1.5rem;
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
  box-sizing: border-box;
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
.activity-form__mode-tabs {
  display: inline-flex;
  gap: 0;
  padding: 0.4rem;
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 999px;
  background: rgba(159, 181, 126, 0.32);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
  flex-wrap: wrap;
}
.activity-form__mode-tab {
  border: 0;
  border-radius: 999px;
  padding: 0.55rem 1rem;
  background: transparent;
  color: #556347;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
}
.activity-form__mode-tab--active {
  background: #fbfaf0;
  color: #25351f;
  box-shadow: 0 6px 16px rgba(76, 88, 57, 0.16), inset 0 1px 0 rgba(255, 255, 255, 0.68);
}
.activity-form__hint {
  margin: 0.45rem 0 0;
  color: #718064;
  font-size: 0.8125rem;
  line-height: 1.5;
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
  flex-wrap: wrap;
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
  min-width: 80px;
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

/* Mobile responsive */
@media (max-width: 640px) {
  .activity-form__row {
    grid-template-columns: 1fr;
  }
  .activity-form__mode-tabs {
    width: 100%;
    justify-content: center;
  }
  .activity-form__actions {
    flex-direction: column;
  }
  .activity-form__actions .btn {
    width: 100%;
  }
}
</style>
