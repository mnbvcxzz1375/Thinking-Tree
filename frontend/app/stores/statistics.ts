/**
 * Statistics store for activity review and analytics.
 * Tracks real-time stats, stores historical data, generates reports.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// ── Types ──────────────────────────────────────────────────────────────

export interface NodeCountByType {
  question: number
  answer: number
  insight: number
  root: number
  branch: number
  total: number
}

export interface TimeDistribution {
  date: string
  count: number
}

export interface BranchStats {
  node_id: number
  content: string
  depth: number
  node_count: number
  last_activity: string | null
}

export interface ActivityStats {
  activity_id: number
  activity_title: string
  node_counts: NodeCountByType
  max_depth: number
  avg_depth: number
  total_speech_records: number
  total_reviews: number
  approved_reviews: number
  participation_rate: number
  most_active_branches: BranchStats[]
  time_distribution: TimeDistribution[]
  created_at: string | null
  last_node_at: string | null
}

export interface InsightItem {
  category: string
  title: string
  description: string
  severity: 'info' | 'success' | 'warning'
}

export interface ActivityInsights {
  activity_id: number
  insights: InsightItem[]
  summary: string
}

export interface OverviewStats {
  total_activities: number
  active_activities: number
  total_nodes: number
  total_speech_records: number
  total_reviews: number
  avg_nodes_per_activity: number
  recent_activities: ActivityStats[]
}

export interface StatisticsState {
  overview: OverviewStats | null
  activityStats: Map<number, ActivityStats>
  activityInsights: Map<number, ActivityInsights>
  historicalData: ActivityStats[]
  loading: boolean
  error: string | null
  lastFetched: string | null
}

// Storage key
const HISTORY_KEY = 'statistics_history'

/**
 * Load historical data from localStorage
 */
function loadHistory(): ActivityStats[] {
  try {
    const stored = localStorage.getItem(HISTORY_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.warn('Failed to load statistics history:', e)
  }
  return []
}

/**
 * Save historical data to localStorage
 */
function saveHistory(data: ActivityStats[]): void {
  try {
    // Keep only last 100 entries
    const trimmed = data.slice(-100)
    localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmed))
  } catch (e) {
    console.warn('Failed to save statistics history:', e)
  }
}

// ── Store ──────────────────────────────────────────────────────────────

export const useStatisticsStore = defineStore('statistics', () => {
  // State
  const overview = ref<OverviewStats | null>(null)
  const activityStats = ref<Map<number, ActivityStats>>(new Map())
  const activityInsights = ref<Map<number, ActivityInsights>>(new Map())
  const historicalData = ref<ActivityStats[]>(loadHistory())
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastFetched = ref<string | null>(null)

  // Getters
  const totalNodes = computed(() => overview.value?.total_nodes ?? 0)
  const totalActivities = computed(() => overview.value?.total_activities ?? 0)
  const activeActivities = computed(() => overview.value?.active_activities ?? 0)

  const getActivityStats = computed(() => {
    return (activityId: number) => activityStats.value.get(activityId) ?? null
  })

  const getActivityInsights = computed(() => {
    return (activityId: number) => activityInsights.value.get(activityId) ?? null
  })

  const recentActivityStats = computed(() => {
    return overview.value?.recent_activities ?? []
  })

  // Actions
  async function fetchOverview() {
    loading.value = true
    error.value = null
    try {
      const api = useApi()
      const response = await api.get<OverviewStats>('/api/stats/overview')
      if (response.data) {
        overview.value = response.data
        lastFetched.value = new Date().toISOString()
      } else if (response.error) {
        error.value = response.error.message
      }
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch overview stats'
      console.error('Error fetching overview stats:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchActivityStats(activityId: number) {
    loading.value = true
    error.value = null
    try {
      const api = useApi()
      const response = await api.get<ActivityStats>(`/api/stats/activities/${activityId}`)
      if (response.data) {
        activityStats.value.set(activityId, response.data)
        // Add to historical data
        historicalData.value.push(response.data)
        saveHistory(historicalData.value)
        lastFetched.value = new Date().toISOString()
      } else if (response.error) {
        error.value = response.error.message
      }
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch activity stats'
      console.error('Error fetching activity stats:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchActivityInsights(activityId: number) {
    loading.value = true
    error.value = null
    try {
      const api = useApi()
      const response = await api.get<ActivityInsights>(`/api/stats/activities/${activityId}/insights`)
      if (response.data) {
        activityInsights.value.set(activityId, response.data)
        lastFetched.value = new Date().toISOString()
      } else if (response.error) {
        error.value = response.error.message
      }
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch activity insights'
      console.error('Error fetching activity insights:', err)
    } finally {
      loading.value = false
    }
  }

  function exportReport(activityId: number): string {
    const stats = activityStats.value.get(activityId)
    if (!stats) return ''

    const report = {
      title: `活动统计报告 - ${stats.activity_title}`,
      generated_at: new Date().toISOString(),
      statistics: stats,
      insights: activityInsights.value.get(activityId) ?? null,
    }

    return JSON.stringify(report, null, 2)
  }

  function exportCSV(activityId: number): string {
    const stats = activityStats.value.get(activityId)
    if (!stats) return ''

    const rows: string[] = []
    rows.push('指标,数值')
    rows.push(`活动名称,${stats.activity_title}`)
    rows.push(`总节点数,${stats.node_counts.total}`)
    rows.push(`问题节点,${stats.node_counts.question}`)
    rows.push(`回答节点,${stats.node_counts.answer}`)
    rows.push(`洞察节点,${stats.node_counts.insight}`)
    rows.push(`最大深度,${stats.max_depth}`)
    rows.push(`平均深度,${stats.avg_depth}`)
    rows.push(`语音互动次数,${stats.total_speech_records}`)
    rows.push(`教师评价数,${stats.total_reviews}`)
    rows.push(`通过评价数,${stats.approved_reviews}`)
    rows.push(`参与率,${(stats.participation_rate * 100).toFixed(1)}%`)
    rows.push('')
    rows.push('时间分布')
    rows.push('日期,节点数')
    for (const td of stats.time_distribution) {
      rows.push(`${td.date},${td.count}`)
    }

    return rows.join('\n')
  }

  function downloadReport(activityId: number, format: 'json' | 'csv' = 'json') {
    let content: string
    let filename: string
    let mimeType: string

    if (format === 'csv') {
      content = exportCSV(activityId)
      filename = `activity_${activityId}_stats.csv`
      mimeType = 'text/csv;charset=utf-8'
    } else {
      content = exportReport(activityId)
      filename = `activity_${activityId}_stats.json`
      mimeType = 'application/json'
    }

    if (!content) return

    // Add BOM for CSV to ensure Chinese characters display correctly in Excel
    const blob = format === 'csv'
      ? new Blob(['\uFEFF' + content], { type: mimeType })
      : new Blob([content], { type: mimeType })

    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  function clearError() {
    error.value = null
  }

  function reset() {
    overview.value = null
    activityStats.value = new Map()
    activityInsights.value = new Map()
    historicalData.value = []
    loading.value = false
    error.value = null
    lastFetched.value = null
    localStorage.removeItem(HISTORY_KEY)
  }

  return {
    // State
    overview,
    activityStats,
    activityInsights,
    historicalData,
    loading,
    error,
    lastFetched,

    // Getters
    totalNodes,
    totalActivities,
    activeActivities,
    getActivityStats,
    getActivityInsights,
    recentActivityStats,

    // Actions
    fetchOverview,
    fetchActivityStats,
    fetchActivityInsights,
    exportReport,
    exportCSV,
    downloadReport,
    clearError,
    reset,
  }
})
