/**
 * Suggestion store for managing tree suggestions.
 * Tracks AI-generated suggestions, teacher actions, and learning from preferences.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Types
export type SuggestionType = 'merge' | 'split' | 'new_direction' | 'rebalance' | 'connect'
export type SuggestionPriority = 'low' | 'medium' | 'high' | 'critical'
export type SuggestionStatus = 'pending' | 'accepted' | 'rejected' | 'dismissed'

export interface Suggestion {
  id: number
  activityId: number
  suggestionType: SuggestionType
  priority: SuggestionPriority
  title: string
  description: string
  reasoning: string
  status: SuggestionStatus
  relatedNodeIds: number[]
  suggestedContent: string | null
  suggestedParentId: number | null
  createdAt: string
  resolvedAt: string | null
}

export interface SuggestionAction {
  id: number
  suggestionId: number
  action: 'accept' | 'reject' | 'dismiss'
  feedback: string | null
  timestamp: string
}

export interface TreeAnalysis {
  totalNodes: number
  maxDepth: number
  balanceScore: number
  nodeTypeDistribution: Record<string, number>
  orphanCount: number
  deepBranchCount: number
  suggestions: Suggestion[]
}

export interface SuggestionState {
  suggestions: Suggestion[]
  actionHistory: SuggestionAction[]
  currentAnalysis: TreeAnalysis | null
  selectedSuggestionId: number | null
  loading: boolean
  error: string | null
  lastAnalyzedActivityId: number | null
  autoSuggestEnabled: boolean
  autoSuggestThreshold: number // N nodes before auto-suggest
}

// Storage keys
const STORAGE_KEY = 'suggestion_state'
const HISTORY_KEY = 'suggestion_action_history'
const PREFERENCES_KEY = 'suggestion_preferences'

/**
 * Load state from localStorage
 */
function loadState(): Partial<SuggestionState> | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.warn('Failed to load suggestion state:', e)
  }
  return null
}

/**
 * Load action history from localStorage
 */
function loadHistory(): SuggestionAction[] {
  try {
    const stored = localStorage.getItem(HISTORY_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.warn('Failed to load suggestion history:', e)
  }
  return []
}

/**
 * Save state to localStorage
 */
function saveState(state: Partial<SuggestionState>): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (e) {
    console.warn('Failed to save suggestion state:', e)
  }
}

/**
 * Save history to localStorage
 */
function saveHistory(history: SuggestionAction[]): void {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
  } catch (e) {
    console.warn('Failed to save suggestion history:', e)
  }
}

/**
 * Load preferences
 */
function loadPreferences(): { autoSuggestEnabled: boolean; autoSuggestThreshold: number } {
  try {
    const stored = localStorage.getItem(PREFERENCES_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.warn('Failed to load preferences:', e)
  }
  return { autoSuggestEnabled: true, autoSuggestThreshold: 5 }
}

/**
 * Save preferences
 */
function savePreferences(prefs: { autoSuggestEnabled: boolean; autoSuggestThreshold: number }): void {
  try {
    localStorage.setItem(PREFERENCES_KEY, JSON.stringify(prefs))
  } catch (e) {
    console.warn('Failed to save preferences:', e)
  }
}

/**
 * Suggestion store for managing tree suggestions
 */
export const useSuggestionStore = defineStore('suggestions', () => {
  // Load initial state
  const stored = loadState()
  const prefs = loadPreferences()

  // State
  const suggestions = ref<Suggestion[]>(stored?.suggestions || [])
  const actionHistory = ref<SuggestionAction[]>(loadHistory())
  const currentAnalysis = ref<TreeAnalysis | null>(stored?.currentAnalysis || null)
  const selectedSuggestionId = ref<number | null>(stored?.selectedSuggestionId || null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastAnalyzedActivityId = ref<number | null>(stored?.lastAnalyzedActivityId || null)
  const autoSuggestEnabled = ref(prefs.autoSuggestEnabled)
  const autoSuggestThreshold = ref(prefs.autoSuggestThreshold)

  // Getters
  const pendingSuggestions = computed(() =>
    suggestions.value.filter((s) => s.status === 'pending')
  )

  const pendingCount = computed(() => pendingSuggestions.value.length)

  const highPrioritySuggestions = computed(() =>
    pendingSuggestions.value.filter((s) => s.priority === 'high' || s.priority === 'critical')
  )

  const selectedSuggestion = computed(() => {
    if (!selectedSuggestionId.value) return null
    return suggestions.value.find((s) => s.id === selectedSuggestionId.value) || null
  })

  const suggestionsByType = computed(() => {
    const grouped: Record<SuggestionType, Suggestion[]> = {
      merge: [],
      split: [],
      new_direction: [],
      rebalance: [],
      connect: [],
    }
    for (const s of pendingSuggestions.value) {
      grouped[s.suggestionType].push(s)
    }
    return grouped
  })

  const recentActions = computed(() =>
    [...actionHistory.value]
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 20)
  )

  const acceptanceRate = computed(() => {
    const total = actionHistory.value.length
    if (total === 0) return 0
    const accepted = actionHistory.value.filter((a) => a.action === 'accept').length
    return accepted / total
  })

  // Actions
  function setSuggestions(newSuggestions: Suggestion[]) {
    suggestions.value = newSuggestions
    saveState({
      suggestions: suggestions.value,
      currentAnalysis: currentAnalysis.value,
      selectedSuggestionId: selectedSuggestionId.value,
      lastAnalyzedActivityId: lastAnalyzedActivityId.value,
    })
  }

  function setAnalysis(analysis: TreeAnalysis) {
    currentAnalysis.value = analysis
    suggestions.value = analysis.suggestions
    lastAnalyzedActivityId.value = analysis.suggestions[0]?.activityId ?? null
    saveState({
      suggestions: suggestions.value,
      currentAnalysis: currentAnalysis.value,
      selectedSuggestionId: selectedSuggestionId.value,
      lastAnalyzedActivityId: lastAnalyzedActivityId.value,
    })
  }

  function selectSuggestion(id: number | null) {
    selectedSuggestionId.value = id
  }

  function acceptSuggestion(id: number, feedback?: string): SuggestionAction | null {
    const suggestion = suggestions.value.find((s) => s.id === id)
    if (!suggestion || suggestion.status !== 'pending') return null

    suggestion.status = 'accepted'
    suggestion.resolvedAt = new Date().toISOString()

    const action: SuggestionAction = {
      id: Date.now(),
      suggestionId: id,
      action: 'accept',
      feedback: feedback || null,
      timestamp: new Date().toISOString(),
    }

    actionHistory.value.push(action)
    saveState({
      suggestions: suggestions.value,
      currentAnalysis: currentAnalysis.value,
      selectedSuggestionId: selectedSuggestionId.value,
      lastAnalyzedActivityId: lastAnalyzedActivityId.value,
    })
    saveHistory(actionHistory.value)

    return action
  }

  function rejectSuggestion(id: number, feedback?: string): SuggestionAction | null {
    const suggestion = suggestions.value.find((s) => s.id === id)
    if (!suggestion || suggestion.status !== 'pending') return null

    suggestion.status = 'rejected'
    suggestion.resolvedAt = new Date().toISOString()

    const action: SuggestionAction = {
      id: Date.now(),
      suggestionId: id,
      action: 'reject',
      feedback: feedback || null,
      timestamp: new Date().toISOString(),
    }

    actionHistory.value.push(action)
    saveState({
      suggestions: suggestions.value,
      currentAnalysis: currentAnalysis.value,
      selectedSuggestionId: selectedSuggestionId.value,
      lastAnalyzedActivityId: lastAnalyzedActivityId.value,
    })
    saveHistory(actionHistory.value)

    return action
  }

  function dismissSuggestion(id: number): SuggestionAction | null {
    const suggestion = suggestions.value.find((s) => s.id === id)
    if (!suggestion || suggestion.status !== 'pending') return null

    suggestion.status = 'dismissed'
    suggestion.resolvedAt = new Date().toISOString()

    const action: SuggestionAction = {
      id: Date.now(),
      suggestionId: id,
      action: 'dismiss',
      feedback: null,
      timestamp: new Date().toISOString(),
    }

    actionHistory.value.push(action)
    saveState({
      suggestions: suggestions.value,
      currentAnalysis: currentAnalysis.value,
      selectedSuggestionId: selectedSuggestionId.value,
      lastAnalyzedActivityId: lastAnalyzedActivityId.value,
    })
    saveHistory(actionHistory.value)

    return action
  }

  function clearPending() {
    suggestions.value = suggestions.value.filter((s) => s.status !== 'pending')
    saveState({
      suggestions: suggestions.value,
      currentAnalysis: currentAnalysis.value,
      selectedSuggestionId: selectedSuggestionId.value,
      lastAnalyzedActivityId: lastAnalyzedActivityId.value,
    })
  }

  function setAutoSuggest(enabled: boolean, threshold?: number) {
    autoSuggestEnabled.value = enabled
    if (threshold !== undefined) {
      autoSuggestThreshold.value = threshold
    }
    savePreferences({
      autoSuggestEnabled: autoSuggestEnabled.value,
      autoSuggestThreshold: autoSuggestThreshold.value,
    })
  }

  function shouldAutoSuggest(nodeCount: number): boolean {
    if (!autoSuggestEnabled.value) return false
    return nodeCount > 0 && nodeCount % autoSuggestThreshold.value === 0
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setError(value: string | null) {
    error.value = value
  }

  function reset() {
    suggestions.value = []
    actionHistory.value = []
    currentAnalysis.value = null
    selectedSuggestionId.value = null
    loading.value = false
    error.value = null
    lastAnalyzedActivityId.value = null
    saveState({})
    saveHistory([])
  }

  // API calls
  async function fetchSuggestions(activityId: number) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/suggestions/${activityId}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch suggestions: ${response.statusText}`)
      }

      const data = await response.json()
      suggestions.value = data.suggestions.map(mapSuggestionFromApi)
      lastAnalyzedActivityId.value = activityId

      saveState({
        suggestions: suggestions.value,
        currentAnalysis: currentAnalysis.value,
        selectedSuggestionId: selectedSuggestionId.value,
        lastAnalyzedActivityId: lastAnalyzedActivityId.value,
      })
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
    } finally {
      loading.value = false
    }
  }

  async function analyzeTree(activityId: number) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/suggestions/analyze/${activityId}`, {
        method: 'POST',
      })
      if (!response.ok) {
        throw new Error(`Failed to analyze tree: ${response.statusText}`)
      }

      const data = await response.json()
      const analysis: TreeAnalysis = {
        totalNodes: data.total_nodes,
        maxDepth: data.max_depth,
        balanceScore: data.balance_score,
        nodeTypeDistribution: data.node_type_distribution,
        orphanCount: data.orphan_count,
        deepBranchCount: data.deep_branch_count,
        suggestions: data.suggestions.map(mapSuggestionFromApi),
      }

      setAnalysis(analysis)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
    } finally {
      loading.value = false
    }
  }

  async function resolveSuggestionApi(id: number, action: 'accept' | 'reject' | 'dismiss', feedback?: string) {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`/api/suggestions/${id}/resolve`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, feedback }),
      })

      if (!response.ok) {
        throw new Error(`Failed to resolve suggestion: ${response.statusText}`)
      }

      // Update local state
      if (action === 'accept') {
        acceptSuggestion(id, feedback)
      } else if (action === 'reject') {
        rejectSuggestion(id, feedback)
      } else {
        dismissSuggestion(id)
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
    } finally {
      loading.value = false
    }
  }

  function mapSuggestionFromApi(raw: Record<string, unknown>): Suggestion {
    return {
      id: raw.id as number,
      activityId: raw.activity_id as number,
      suggestionType: raw.suggestion_type as SuggestionType,
      priority: raw.priority as SuggestionPriority,
      title: raw.title as string,
      description: raw.description as string,
      reasoning: raw.reasoning as string,
      status: raw.status as SuggestionStatus,
      relatedNodeIds: (raw.related_node_ids as string || '').split(',').filter(Boolean).map(Number),
      suggestedContent: (raw.suggested_content as string) || null,
      suggestedParentId: (raw.suggested_parent_id as number) || null,
      createdAt: raw.created_at as string,
      resolvedAt: (raw.resolved_at as string) || null,
    }
  }

  return {
    // State
    suggestions,
    actionHistory,
    currentAnalysis,
    selectedSuggestionId,
    loading,
    error,
    lastAnalyzedActivityId,
    autoSuggestEnabled,
    autoSuggestThreshold,

    // Getters
    pendingSuggestions,
    pendingCount,
    highPrioritySuggestions,
    selectedSuggestion,
    suggestionsByType,
    recentActions,
    acceptanceRate,

    // Actions
    setSuggestions,
    setAnalysis,
    selectSuggestion,
    acceptSuggestion,
    rejectSuggestion,
    dismissSuggestion,
    clearPending,
    setAutoSuggest,
    shouldAutoSuggest,
    setLoading,
    setError,
    reset,

    // API
    fetchSuggestions,
    analyzeTree,
    resolveSuggestionApi,
  }
})
