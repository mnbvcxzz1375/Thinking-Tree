/**
 * Follow-up question store.
 * Manages AI-generated questions for teachers, tracks history,
 * and provides filtering/search capabilities.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Types
export interface FollowUpQuestion {
  id: string
  question: string
  category: string
  age_group: string
  relevance_score: number
  context: string | null
  variations: string[]
  created_at: string
}

export interface QuestionResponse {
  questions: FollowUpQuestion[]
  source_node_content: string
  age_group: string
  category: string | null
}

export interface QuestionHistoryEntry {
  question: FollowUpQuestion
  usedAt: string
  nodeId: string | null
  nodeContent: string
}

export type QuestionCategory =
  | 'exploration'
  | 'connection'
  | 'reflection'
  | 'challenge'
  | 'creative'
  | 'empty_branch'

// Storage keys
const QUESTIONS_KEY = 'followup_questions'
const HISTORY_KEY = 'question_history'

// Category labels (Chinese)
export const CATEGORY_LABELS: Record<QuestionCategory, string> = {
  exploration: '探索',
  connection: '联系',
  reflection: '反思',
  challenge: '挑战',
  creative: '创意',
  empty_branch: '空白分支',
}

// Category icons
export const CATEGORY_ICONS: Record<QuestionCategory, string> = {
  exploration: '🔍',
  connection: '🔗',
  reflection: '💭',
  challenge: '⚡',
  creative: '🎨',
  empty_branch: '🌱',
}

/**
 * Load questions from localStorage
 */
function loadQuestions(): FollowUpQuestion[] {
  try {
    const stored = localStorage.getItem(QUESTIONS_KEY)
    if (stored) return JSON.parse(stored)
  } catch (e) {
    console.warn('Failed to load questions:', e)
  }
  return []
}

/**
 * Load history from localStorage
 */
function loadHistory(): QuestionHistoryEntry[] {
  try {
    const stored = localStorage.getItem(HISTORY_KEY)
    if (stored) return JSON.parse(stored)
  } catch (e) {
    console.warn('Failed to load history:', e)
  }
  return []
}

/**
 * Save questions to localStorage
 */
function saveQuestions(questions: FollowUpQuestion[]): void {
  try {
    localStorage.setItem(QUESTIONS_KEY, JSON.stringify(questions))
  } catch (e) {
    console.warn('Failed to save questions:', e)
  }
}

/**
 * Save history to localStorage
 */
function saveHistory(history: QuestionHistoryEntry[]): void {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
  } catch (e) {
    console.warn('Failed to save history:', e)
  }
}

/**
 * Question store for managing follow-up questions
 */
export const useQuestionStore = defineStore('questions', () => {
  // State
  const questions = ref<FollowUpQuestion[]>(loadQuestions())
  const history = ref<QuestionHistoryEntry[]>(loadHistory())
  const selectedQuestionId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const activeCategory = ref<QuestionCategory | null>(null)
  const searchQuery = ref('')
  const ageGroup = ref<string>('7-9')

  // Getters
  const selectedQuestion = computed(() => {
    if (!selectedQuestionId.value) return null
    return questions.value.find((q) => q.id === selectedQuestionId.value) || null
  })

  const categories = computed(() => {
    const cats = new Set(questions.value.map((q) => q.category))
    return Array.from(cats) as QuestionCategory[]
  })

  const filteredQuestions = computed(() => {
    let result = [...questions.value]

    // Filter by category
    if (activeCategory.value) {
      result = result.filter((q) => q.category === activeCategory.value)
    }

    // Filter by search query
    if (searchQuery.value.trim()) {
      const query = searchQuery.value.toLowerCase()
      result = result.filter(
        (q) =>
          q.question.toLowerCase().includes(query) ||
          (q.context && q.context.toLowerCase().includes(query))
      )
    }

    // Sort by relevance score descending
    result.sort((a, b) => b.relevance_score - a.relevance_score)

    return result
  })

  const questionCount = computed(() => questions.value.length)

  const usedQuestionIds = computed(() => new Set(history.value.map((h) => h.question.id)))

  const recentHistory = computed(() =>
    [...history.value]
      .sort((a, b) => new Date(b.usedAt).getTime() - new Date(a.usedAt).getTime())
      .slice(0, 50)
  )

  // Actions
  function setQuestions(newQuestions: FollowUpQuestion[]) {
    questions.value = newQuestions
    saveQuestions(questions.value)
  }

  function addQuestions(newQuestions: FollowUpQuestion[]) {
    questions.value.push(...newQuestions)
    saveQuestions(questions.value)
  }

  function selectQuestion(id: string | null) {
    selectedQuestionId.value = id
  }

  function setCategory(category: QuestionCategory | null) {
    activeCategory.value = category
  }

  function setSearch(query: string) {
    searchQuery.value = query
  }

  function setAgeGroup(group: string) {
    ageGroup.value = group
  }

  function markAsUsed(question: FollowUpQuestion, nodeId: string | null, nodeContent: string) {
    const entry: QuestionHistoryEntry = {
      question,
      usedAt: new Date().toISOString(),
      nodeId,
      nodeContent,
    }
    history.value.push(entry)
    saveHistory(history.value)
  }

  function removeQuestion(id: string) {
    questions.value = questions.value.filter((q) => q.id !== id)
    if (selectedQuestionId.value === id) {
      selectedQuestionId.value = null
    }
    saveQuestions(questions.value)
  }

  function clearQuestions() {
    questions.value = []
    selectedQuestionId.value = null
    saveQuestions([])
  }

  function clearHistory() {
    history.value = []
    saveHistory([])
  }

  function exportHistory(): string {
    return JSON.stringify(history.value, null, 2)
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setError(value: string | null) {
    error.value = value
  }

  function reset() {
    questions.value = []
    history.value = []
    selectedQuestionId.value = null
    loading.value = false
    error.value = null
    activeCategory.value = null
    searchQuery.value = ''
    saveQuestions([])
    saveHistory([])
  }

  return {
    // State
    questions,
    history,
    selectedQuestionId,
    loading,
    error,
    activeCategory,
    searchQuery,
    ageGroup,

    // Getters
    selectedQuestion,
    categories,
    filteredQuestions,
    questionCount,
    usedQuestionIds,
    recentHistory,

    // Actions
    setQuestions,
    addQuestions,
    selectQuestion,
    setCategory,
    setSearch,
    setAgeGroup,
    markAsUsed,
    removeQuestion,
    clearQuestions,
    clearHistory,
    exportHistory,
    setLoading,
    setError,
    reset,
  }
})
