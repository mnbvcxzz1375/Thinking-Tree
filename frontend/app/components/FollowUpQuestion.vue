<template>
  <div
    class="follow-up-question"
    :class="{
      'follow-up-question--selected': isSelected,
      'follow-up-question--used': isUsed,
      [`follow-up-question--${question.category}`]: true,
    }"
    @click="$emit('select', question.id)"
  >
    <!-- Category badge -->
    <div class="follow-up-question__header">
      <span class="follow-up-question__category">
        {{ categoryIcon }} {{ categoryLabel }}
      </span>
      <span class="follow-up-question__score" :title="`相关度: ${Math.round(question.relevance_score * 100)}%`">
        {{ relevanceDots }}
      </span>
    </div>

    <!-- Question text -->
    <p class="follow-up-question__text">{{ question.question }}</p>

    <!-- Context -->
    <p v-if="question.context" class="follow-up-question__context">
      {{ question.context }}
    </p>

    <!-- Variations (expandable) -->
    <div v-if="question.variations.length > 0" class="follow-up-question__variations">
      <button
        class="follow-up-question__expand-btn"
        @click.stop="showVariations = !showVariations"
      >
        {{ showVariations ? '收起' : `其他问法 (${question.variations.length})` }}
      </button>
      <ul v-if="showVariations" class="follow-up-question__variation-list">
        <li
          v-for="(variation, idx) in question.variations"
          :key="idx"
          class="follow-up-question__variation-item"
          @click.stop="$emit('use-variation', variation)"
        >
          {{ variation }}
        </li>
      </ul>
    </div>

    <!-- Actions -->
    <div class="follow-up-question__actions">
      <button
        class="follow-up-question__action-btn follow-up-question__action-btn--use"
        :disabled="isUsed"
        @click.stop="$emit('use', question)"
      >
        {{ isUsed ? '✓ 已使用' : '使用此问题' }}
      </button>
      <button
        class="follow-up-question__action-btn follow-up-question__action-btn--copy"
        @click.stop="copyQuestion"
        :title="copyTooltip"
      >
        {{ copied ? '✓ 已复制' : '复制' }}
      </button>
      <button
        v-if="showShare"
        class="follow-up-question__action-btn follow-up-question__action-btn--share"
        @click.stop="$emit('share', question)"
      >
        分享
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FollowUpQuestion } from '~/stores/questions'
import { CATEGORY_LABELS, CATEGORY_ICONS } from '~/stores/questions'
import type { QuestionCategory } from '~/stores/questions'

interface Props {
  question: FollowUpQuestion
  isSelected?: boolean
  isUsed?: boolean
  showShare?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSelected: false,
  isUsed: false,
  showShare: false,
})

defineEmits<{
  select: [id: string]
  use: [question: FollowUpQuestion]
  'use-variation': [variation: string]
  share: [question: FollowUpQuestion]
}>()

const showVariations = ref(false)
const copied = ref(false)
const copyTooltip = ref('复制问题到剪贴板')

const categoryLabel = computed(
  () => CATEGORY_LABELS[props.question.category as QuestionCategory] || props.question.category
)

const categoryIcon = computed(
  () => CATEGORY_ICONS[props.question.category as QuestionCategory] || '❓'
)

const relevanceDots = computed(() => {
  const score = Math.round(props.question.relevance_score * 5)
  return '●'.repeat(score) + '○'.repeat(5 - score)
})

async function copyQuestion() {
  try {
    await navigator.clipboard.writeText(props.question.question)
    copied.value = true
    copyTooltip.value = '已复制!'
    setTimeout(() => {
      copied.value = false
      copyTooltip.value = '复制问题到剪贴板'
    }, 2000)
  } catch {
    // Fallback for environments without clipboard API
    const textArea = document.createElement('textarea')
    textArea.value = props.question.question
    textArea.style.position = 'fixed'
    textArea.style.left = '-9999px'
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  }
}
</script>

<style scoped>
.follow-up-question {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.follow-up-question:hover {
  border-color: #a5b4fc;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
}

.follow-up-question--selected {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.follow-up-question--used {
  opacity: 0.6;
  background: #f9fafb;
}

/* Category color accents */
.follow-up-question--exploration { border-left: 4px solid #3b82f6; }
.follow-up-question--connection { border-left: 4px solid #8b5cf6; }
.follow-up-question--reflection { border-left: 4px solid #f59e0b; }
.follow-up-question--challenge { border-left: 4px solid #ef4444; }
.follow-up-question--creative { border-left: 4px solid #ec4899; }
.follow-up-question--empty_branch { border-left: 4px solid #10b981; }

.follow-up-question__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.follow-up-question__category {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6366f1;
  background: #eef2ff;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
}

.follow-up-question__score {
  font-size: 0.625rem;
  color: #6366f1;
  letter-spacing: 1px;
}

.follow-up-question__text {
  margin: 0;
  font-size: 0.9375rem;
  line-height: 1.5;
  color: #1f2937;
  font-weight: 500;
}

.follow-up-question__context {
  margin: 0;
  font-size: 0.75rem;
  color: #6b7280;
  line-height: 1.4;
  padding-left: 0.5rem;
  border-left: 2px solid #e5e7eb;
}

.follow-up-question__variations {
  margin-top: 0.25rem;
}

.follow-up-question__expand-btn {
  background: none;
  border: none;
  color: #6366f1;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.follow-up-question__expand-btn:hover {
  color: #4f46e5;
}

.follow-up-question__variation-list {
  margin: 0.375rem 0 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.follow-up-question__variation-item {
  font-size: 0.8125rem;
  color: #4b5563;
  padding: 0.375rem 0.5rem;
  background: #f3f4f6;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

.follow-up-question__variation-item:hover {
  background: #e5e7eb;
}

.follow-up-question__actions {
  display: flex;
  gap: 0.375rem;
  margin-top: 0.25rem;
}

.follow-up-question__action-btn {
  flex: 1;
  padding: 0.375rem 0.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  background: white;
  color: #374151;
}

.follow-up-question__action-btn:hover:not(:disabled) {
  background: #f3f4f6;
}

.follow-up-question__action-btn:disabled {
  cursor: default;
  opacity: 0.7;
}

.follow-up-question__action-btn--use {
  background: #6366f1;
  color: white;
  border-color: #6366f1;
}

.follow-up-question__action-btn--use:hover:not(:disabled) {
  background: #4f46e5;
}

.follow-up-question__action-btn--use:disabled {
  background: #10b981;
  border-color: #10b981;
  color: white;
}

.follow-up-question__action-btn--copy.copied {
  background: #10b981;
  color: white;
  border-color: #10b981;
}

@media (max-width: 768px) {
  .follow-up-question {
    padding: 0.75rem;
  }

  .follow-up-question__text {
    font-size: 0.875rem;
  }

  .follow-up-question__action-btn {
    padding: 0.5rem;
    min-height: 40px;
  }
}
</style>
