/**
 * Candidate node store for teacher confirmation workflow.
 * Manages AI-generated candidate nodes pending teacher review.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Types
export interface CandidateNode {
  id: string
  /** Raw transcript from child's speech */
  transcript: string
  /** AI-generated leaf text */
  leafText: string
  /** AI-generated follow-up question */
  followUpQuestion: string
  /** Suggested parent node ID */
  suggestedParentId: string | null
  /** Confidence score from AI (0-1) */
  confidence: number
  /** Node type suggestion */
  nodeType: 'question' | 'answer' | 'insight'
  /** Creation timestamp */
  createdAt: string
  /** Current status */
  status: 'pending' | 'confirmed' | 'edited' | 'moved' | 'rejected'
}

export interface ConfirmationRecord {
  id: string
  candidateId: string
  action: 'confirm' | 'edit' | 'move' | 'reject'
  /** Original candidate data */
  originalCandidate: CandidateNode
  /** Final text after edit (if edited) */
  finalText?: string
  /** Final parent ID after move (if moved) */
  finalParentId?: string | null
  /** Teacher who confirmed */
  confirmedBy?: string
  /** Timestamp */
  confirmedAt: string
  /** Can undo within time limit */
  undoable: boolean
}

export interface CandidateState {
  candidates: CandidateNode[]
  history: ConfirmationRecord[]
  selectedCandidateId: string | null
  loading: boolean
  error: string | null
}

// Storage keys
const STORAGE_KEY = 'candidate_state'
const HISTORY_KEY = 'confirmation_history'
const UNDO_WINDOW_MS = 5 * 60 * 1000 // 5 minutes

/**
 * Load candidates from localStorage
 */
function loadCandidates(): CandidateNode[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.warn('Failed to load candidates:', e)
  }
  return []
}

/**
 * Load history from localStorage
 */
function loadHistory(): ConfirmationRecord[] {
  try {
    const stored = localStorage.getItem(HISTORY_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.warn('Failed to load history:', e)
  }
  return []
}

/**
 * Save candidates to localStorage
 */
function saveCandidates(candidates: CandidateNode[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(candidates))
  } catch (e) {
    console.warn('Failed to save candidates:', e)
  }
}

/**
 * Save history to localStorage
 */
function saveHistory(history: ConfirmationRecord[]): void {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
  } catch (e) {
    console.warn('Failed to save history:', e)
  }
}

/**
 * Generate unique ID
 */
function generateId(): string {
  return `cand_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
}

/**
 * Candidate store for managing AI-generated candidate nodes
 */
export const useCandidateStore = defineStore('candidate', () => {
  // State
  const candidates = ref<CandidateNode[]>(loadCandidates())
  const history = ref<ConfirmationRecord[]>(loadHistory())
  const selectedCandidateId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const pendingCandidates = computed(() =>
    candidates.value.filter((c) => c.status === 'pending')
  )

  const pendingCount = computed(() => pendingCandidates.value.length)

  const selectedCandidate = computed(() => {
    if (!selectedCandidateId.value) return null
    return candidates.value.find((c) => c.id === selectedCandidateId.value) || null
  })

  const recentHistory = computed(() =>
    [...history.value]
      .sort((a, b) => new Date(b.confirmedAt).getTime() - new Date(a.confirmedAt).getTime())
      .slice(0, 50)
  )

  const undoableRecords = computed(() => {
    const now = Date.now()
    return history.value.filter((r) => {
      if (!r.undoable) return false
      const elapsed = now - new Date(r.confirmedAt).getTime()
      return elapsed < UNDO_WINDOW_MS
    })
  })

  // Actions
  function addCandidate(candidate: Omit<CandidateNode, 'id' | 'createdAt' | 'status'>): CandidateNode {
    const newCandidate: CandidateNode = {
      ...candidate,
      id: generateId(),
      createdAt: new Date().toISOString(),
      status: 'pending',
    }
    candidates.value.push(newCandidate)
    saveCandidates(candidates.value)
    return newCandidate
  }

  function addCandidates(batch: Omit<CandidateNode, 'id' | 'createdAt' | 'status'>[]): CandidateNode[] {
    const newCandidates = batch.map((c) => ({
      ...c,
      id: generateId(),
      createdAt: new Date().toISOString(),
      status: 'pending' as const,
    }))
    candidates.value.push(...newCandidates)
    saveCandidates(candidates.value)
    return newCandidates
  }

  function selectCandidate(id: string | null) {
    selectedCandidateId.value = id
  }

  function confirmCandidate(candidateId: string, confirmedBy?: string): ConfirmationRecord | null {
    const candidate = candidates.value.find((c) => c.id === candidateId)
    if (!candidate || candidate.status !== 'pending') return null

    candidate.status = 'confirmed'

    const record: ConfirmationRecord = {
      id: `hist_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
      candidateId,
      action: 'confirm',
      originalCandidate: { ...candidate },
      confirmedBy,
      confirmedAt: new Date().toISOString(),
      undoable: true,
    }

    history.value.push(record)
    saveCandidates(candidates.value)
    saveHistory(history.value)

    return record
  }

  function editAndConfirm(
    candidateId: string,
    newText: string,
    confirmedBy?: string
  ): ConfirmationRecord | null {
    const candidate = candidates.value.find((c) => c.id === candidateId)
    if (!candidate || candidate.status !== 'pending') return null

    candidate.status = 'edited'

    const record: ConfirmationRecord = {
      id: `hist_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
      candidateId,
      action: 'edit',
      originalCandidate: { ...candidate },
      finalText: newText,
      confirmedBy,
      confirmedAt: new Date().toISOString(),
      undoable: true,
    }

    history.value.push(record)
    saveCandidates(candidates.value)
    saveHistory(history.value)

    return record
  }

  function moveAndConfirm(
    candidateId: string,
    newParentId: string | null,
    confirmedBy?: string
  ): ConfirmationRecord | null {
    const candidate = candidates.value.find((c) => c.id === candidateId)
    if (!candidate || candidate.status !== 'pending') return null

    candidate.status = 'moved'

    const record: ConfirmationRecord = {
      id: `hist_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
      candidateId,
      action: 'move',
      originalCandidate: { ...candidate },
      finalParentId: newParentId,
      confirmedBy,
      confirmedAt: new Date().toISOString(),
      undoable: true,
    }

    history.value.push(record)
    saveCandidates(candidates.value)
    saveHistory(history.value)

    return record
  }

  function rejectCandidate(candidateId: string, confirmedBy?: string): ConfirmationRecord | null {
    const candidate = candidates.value.find((c) => c.id === candidateId)
    if (!candidate || candidate.status !== 'pending') return null

    candidate.status = 'rejected'

    const record: ConfirmationRecord = {
      id: `hist_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
      candidateId,
      action: 'reject',
      originalCandidate: { ...candidate },
      confirmedBy,
      confirmedAt: new Date().toISOString(),
      undoable: true,
    }

    history.value.push(record)
    saveCandidates(candidates.value)
    saveHistory(history.value)

    return record
  }

  function undoConfirmation(recordId: string): CandidateNode | null {
    const record = history.value.find((r) => r.id === recordId)
    if (!record || !record.undoable) return null

    const now = Date.now()
    const elapsed = now - new Date(record.confirmedAt).getTime()
    if (elapsed >= UNDO_WINDOW_MS) {
      record.undoable = false
      saveHistory(history.value)
      return null
    }

    // Restore candidate to pending
    const candidate = candidates.value.find((c) => c.id === record.candidateId)
    if (candidate) {
      candidate.status = 'pending'
    }

    // Remove from history
    history.value = history.value.filter((r) => r.id !== recordId)
    saveCandidates(candidates.value)
    saveHistory(history.value)

    return candidate || null
  }

  function removeCandidate(candidateId: string) {
    candidates.value = candidates.value.filter((c) => c.id !== candidateId)
    if (selectedCandidateId.value === candidateId) {
      selectedCandidateId.value = null
    }
    saveCandidates(candidates.value)
  }

  function clearHistory() {
    history.value = []
    saveHistory(history.value)
  }

  function clearPending() {
    candidates.value = candidates.value.filter((c) => c.status !== 'pending')
    saveCandidates(candidates.value)
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
    candidates.value = []
    history.value = []
    selectedCandidateId.value = null
    loading.value = false
    error.value = null
    saveCandidates([])
    saveHistory([])
  }

  return {
    // State
    candidates,
    history,
    selectedCandidateId,
    loading,
    error,

    // Getters
    pendingCandidates,
    pendingCount,
    selectedCandidate,
    recentHistory,
    undoableRecords,

    // Actions
    addCandidate,
    addCandidates,
    selectCandidate,
    confirmCandidate,
    editAndConfirm,
    moveAndConfirm,
    rejectCandidate,
    undoConfirmation,
    removeCandidate,
    clearHistory,
    clearPending,
    exportHistory,
    setLoading,
    setError,
    reset,
  }
})
