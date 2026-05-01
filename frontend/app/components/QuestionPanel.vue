<template>
  <div class="question-panel" :class="{ 'question-panel--open': isOpen }">
    <!-- Header -->
    <div class="question-panel__header">
      <div class="question-panel__title-row">
        <h3 class="question-panel__title">
          💡 提问建议
          <span v-if="questionCount > 0" class="question-panel__count">
            {{ questionCount }}
          </span>
        </h3>
        <button class="question-panel__toggle" @click="$emit('toggle')">
          {{ isOpen ? '✕' : '💡' }}
        </button>
      </div>
      <p v-if="questionCount > 0" class="question-panel__subtitle">
        AI 为当前节点生成的提问建议
      </p>
      <p v-else class="question-panel__subtitle question-panel__subtitle--empty">
        选择一个节点以获取提问建议
      </p>
    </div>

    <!-- Body -->
    <div v-if="isOpen" class="question-panel__body">
      <!-- Search -->
      <div class="question-panel__search">
        <input
          v-model="searchInput"
          type="text"
          class="question-panel__search-input"
          placeholder="搜索问题..."
          @input="onSearchInput"
        />
        <button
          v-if="searchInput"
          class="question-panel__search-clear"
          @click="clearSearch"
        >
          ✕
        </button>
      </div>

      <!-- Category filters -->
      <div v-if="categories.length > 0" class="question-panel__filters">
        <button
          class="question-panel__filter-btn"
          :class="{ 'question-panel__filter-btn--active': !activeCategory }"
          @click="setCategory(null)"
        >
          全部
        </button>
        <button
          v-for="cat in categories"
          :key="cat"
          class="question-panel__filter-btn"
          :class="{ 'question-panel__filter-btn--active': activeCategory === cat }"
          @click="setCategory(cat)"
        >
          {{ getCategoryIcon(cat) }} {{ getCategoryLabel(cat) }}
        </button>
      </div>

      <!-- Empty state -->
      <div v-if="filteredQuestions.length === 0 && !loading" class="question-panel__empty">
        <span class="question-panel__empty-icon">🤔</span>
        <p v-if="searchInput">没有找到匹配的问题</p>
        <p v-else>暂无提问建议</p>
        <button
          class="question-panel__generate-btn"
          @click="$emit('generate')"
        >
          生成提问建议
        </button>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="question-panel__loading">
        <div class="question-panel__spinner"></div>
        <p>AI 正在思考...</p>
      </div>

      <!-- Question list -->
      <div v-if="filteredQuestions.length > 0" class="question-panel__list">
        <FollowUpQuestion
          v-for="question in filteredQuestions"
          :key="question.id"
          :question="question"
          :is-selected="selectedQuestionId === question.id"
          :is-used="usedQuestionIds.has(question.id)"
          @select="selectQuestion"
          @use="onUseQuestion"
          @use-variation="onUseVariation"
          @share="onShareQuestion"
        />
      </div>

      <!-- Footer with actions -->
      <div v-if="questionCount > 0" class="question-panel__footer">
        <button
          class="question-panel__footer-btn question-panel__footer-btn--refresh"
          @click="$emit('generate')"
        >
          🔄 刷新建议
        </button>
        <button
          class="question-panel__footer-btn question-panel__footer-btn--clear"
          @click="onClear"
        >
          清空
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useQuestionStore } from '~/stores/questions'
import type { FollowUpQuestion, QuestionCategory } from '~/stores/questions'
import { CATEGORY_LABELS, CATEGORY_ICONS } from '~/stores/questions'

interface Props {
  isOpen: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  toggle: []
  generate: []
  'use-question': [question: FollowUpQuestion]
  'share-question': [question: FollowUpQuestion]
}>()

const questionStore = useQuestionStore()
const {
  filteredQuestions,
  questionCount,
  selectedQuestionId,
  categories,
  activeCategory,
  usedQuestionIds,
  loading,
} = storeToRefs(questionStore)

const searchInput = ref('')

// Debounce search
let searchTimeout: ReturnType<typeof setTimeout> | null = null

function onSearchInput() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    questionStore.setSearch(searchInput.value)
  }, 200)
}

function clearSearch() {
  searchInput.value = ''
  questionStore.setSearch('')
}

function setCategory(cat: QuestionCategory | null) {
  questionStore.setCategory(cat)
}

function selectQuestion(id: string) {
  questionStore.selectQuestion(id === selectedQuestionId.value ? null : id)
}

function getCategoryLabel(cat: string): string {
  return CATEGORY_LABELS[cat as QuestionCategory] || cat
}

function getCategoryIcon(cat: string): string {
  return CATEGORY_ICONS[cat as QuestionCategory] || '❓'
}

function onUseQuestion(question: FollowUpQuestion) {
  questionStore.markAsUsed(question, null, '')
  emit('use-question', question)
}

function onUseVariation(variation: string) {
  // Create a temporary question object from variation
  const question: FollowUpQuestion = {
    id: `var_${Date.now()}`,
    question: variation,
    category: 'exploration',
    age_group: questionStore.ageGroup,
    relevance_score: 0.8,
    context: null,
    variations: [],
    created_at: new Date().toISOString(),
  }
  emit('use-question', question)
}

function onShareQuestion(question: FollowUpQuestion) {
  emit('share-question', question)
}

function onClear() {
  questionStore.clearQuestions()
  searchInput.value = ''
}

// Cleanup timeout on unmount
watch(
  () => searchInput.value,
  () => {
    // no-op, just tracking
  }
)
</script>

<style scoped>
.question-panel {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 22rem;
  background: white;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.1);
  transform: translateX(-100%);
  transition: transform 0.3s ease;
  z-index: 50;
  display: flex;
  flex-direction: column;
}

.question-panel--open {
  transform: translateX(0);
}

.question-panel__header {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #fef3c7, #fde68a);
}

.question-panel__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.question-panel__title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #92400e;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.question-panel__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.375rem;
  border-radius: 9999px;
  background: #f59e0b;
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
}

.question-panel__subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.8125rem;
  color: #b45309;
}

.question-panel__subtitle--empty {
  color: #9ca3af;
}

.question-panel__toggle {
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 0.375rem;
  background: rgba(245, 158, 11, 0.1);
  color: #b45309;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.question-panel__toggle:hover {
  background: rgba(245, 158, 11, 0.2);
}

.question-panel__body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* Search */
.question-panel__search {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
  position: relative;
}

.question-panel__search-input {
  width: 100%;
  padding: 0.5rem 2rem 0.5rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.15s;
  box-sizing: border-box;
}

.question-panel__search-input:focus {
  border-color: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
}

.question-panel__search-clear {
  position: absolute;
  right: 1.5rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0.25rem;
}

/* Category filters */
.question-panel__filters {
  padding: 0.5rem 1rem;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  gap: 0.375rem;
  flex-wrap: wrap;
}

.question-panel__filter-btn {
  padding: 0.25rem 0.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 9999px;
  background: white;
  font-size: 0.6875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  color: #6b7280;
  white-space: nowrap;
}

.question-panel__filter-btn:hover {
  background: #f3f4f6;
}

.question-panel__filter-btn--active {
  background: #f59e0b;
  color: white;
  border-color: #f59e0b;
}

/* Empty state */
.question-panel__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  color: #6b7280;
}

.question-panel__empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.question-panel__empty p {
  margin: 0.25rem 0;
  font-size: 0.875rem;
}

.question-panel__generate-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: #f59e0b;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}

.question-panel__generate-btn:hover {
  background: #d97706;
}

/* Loading state */
.question-panel__loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: #6b7280;
}

.question-panel__loading p {
  margin: 0;
  font-size: 0.875rem;
}

.question-panel__spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid #e5e7eb;
  border-top-color: #f59e0b;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Question list */
.question-panel__list {
  flex: 1;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  overflow-y: auto;
}

/* Footer */
.question-panel__footer {
  padding: 0.75rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.5rem;
}

.question-panel__footer-btn {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.question-panel__footer-btn--refresh {
  background: #f59e0b;
  color: white;
}

.question-panel__footer-btn--refresh:hover {
  background: #d97706;
}

.question-panel__footer-btn--clear {
  background: #f3f4f6;
  color: #6b7280;
}

.question-panel__footer-btn--clear:hover {
  background: #e5e7eb;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .question-panel {
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

  .question-panel--open {
    transform: translateY(0);
  }

  .question-panel__header {
    border-radius: 20px 20px 0 0;
    padding: 1rem 1.5rem;
  }

  .question-panel__title {
    font-size: 1.25rem;
  }

  .question-panel__toggle {
    padding: 12px;
    width: auto;
    height: auto;
    min-width: 44px;
    min-height: 44px;
  }

  .question-panel__filter-btn {
    padding: 0.375rem 0.75rem;
    font-size: 0.8125rem;
  }

  .question-panel__footer-btn {
    padding: 12px;
    font-size: 1rem;
    min-height: 44px;
  }
}
</style>
