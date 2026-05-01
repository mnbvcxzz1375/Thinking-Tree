import { defineStore } from 'pinia'

// Types matching backend schemas
export interface Activity {
  id: number
  title: string
  description: string | null
  instructions: string | null
  difficulty_level: 'easy' | 'medium' | 'hard'
  age_group: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ActivityCreateInput {
  title: string
  description?: string
  instructions?: string
  difficulty_level?: 'easy' | 'medium' | 'hard'
  age_group?: string
  is_active?: boolean
}

export interface ActivityUpdateInput {
  title?: string
  description?: string
  instructions?: string
  difficulty_level?: 'easy' | 'medium' | 'hard'
  age_group?: string
  is_active?: boolean
}

export interface ActivityState {
  activities: Activity[]
  currentActivity: Activity | null
  loading: boolean
  error: string | null
}

export const useActivityStore = defineStore('activity', {
  state: (): ActivityState => ({
    activities: [],
    currentActivity: null,
    loading: false,
    error: null,
  }),

  getters: {
    activeActivities: (state) => state.activities.filter((a) => a.is_active),
    activityCount: (state) => state.activities.length,
    getActivityById: (state) => {
      return (id: number) => state.activities.find((a) => a.id === id)
    },
    difficultyLabel: () => {
      return (level: string) => {
        const labels: Record<string, string> = {
          easy: '简单',
          medium: '中等',
          hard: '困难',
        }
        return labels[level] || level
      }
    },
  },

  actions: {
    /**
     * Fetch all activities from the API.
     */
    async fetchActivities(params?: { skip?: number; limit?: number; active_only?: boolean }) {
      this.loading = true
      this.error = null
      try {
        const api = useApi()
        const queryParams: Record<string, number | boolean> = {}
        if (params?.skip !== undefined) queryParams.skip = params.skip
        if (params?.limit !== undefined) queryParams.limit = params.limit
        if (params?.active_only !== undefined) queryParams.active_only = params.active_only

        this.activities = await api.get<Activity[]>('/api/activities', queryParams)
      } catch (err: unknown) {
        this.error = err instanceof Error ? err.message : 'Failed to fetch activities'
        console.error('Error fetching activities:', err)
      } finally {
        this.loading = false
      }
    },

    /**
     * Fetch a single activity by ID.
     */
    async fetchActivity(id: number) {
      this.loading = true
      this.error = null
      try {
        const api = useApi()
        this.currentActivity = await api.get<Activity>(`/api/activities/${id}`)
        return this.currentActivity
      } catch (err: unknown) {
        this.error = err instanceof Error ? err.message : 'Failed to fetch activity'
        console.error('Error fetching activity:', err)
        return null
      } finally {
        this.loading = false
      }
    },

    /**
     * Create a new activity.
     */
    async createActivity(data: ActivityCreateInput) {
      this.loading = true
      this.error = null
      try {
        const api = useApi()
        const newActivity = await api.post<Activity>('/api/activities', data)
        this.activities.unshift(newActivity)
        return newActivity
      } catch (err: unknown) {
        this.error = err instanceof Error ? err.message : 'Failed to create activity'
        console.error('Error creating activity:', err)
        return null
      } finally {
        this.loading = false
      }
    },

    /**
     * Update an existing activity.
     */
    async updateActivity(id: number, data: ActivityUpdateInput) {
      this.loading = true
      this.error = null
      try {
        const api = useApi()
        const updated = await api.put<Activity>(`/api/activities/${id}`, data)

        // Update in list
        const index = this.activities.findIndex((a) => a.id === id)
        if (index !== -1) {
          this.activities[index] = updated
        }

        // Update current if viewing
        if (this.currentActivity?.id === id) {
          this.currentActivity = updated
        }

        return updated
      } catch (err: unknown) {
        this.error = err instanceof Error ? err.message : 'Failed to update activity'
        console.error('Error updating activity:', err)
        return null
      } finally {
        this.loading = false
      }
    },

    /**
     * Delete an activity.
     */
    async deleteActivity(id: number) {
      this.loading = true
      this.error = null
      try {
        const api = useApi()
        await api.del(`/api/activities/${id}`)

        // Remove from list
        this.activities = this.activities.filter((a) => a.id !== id)

        // Clear current if it was deleted
        if (this.currentActivity?.id === id) {
          this.currentActivity = null
        }

        return true
      } catch (err: unknown) {
        this.error = err instanceof Error ? err.message : 'Failed to delete activity'
        console.error('Error deleting activity:', err)
        return false
      } finally {
        this.loading = false
      }
    },

    /**
     * Clear error state.
     */
    clearError() {
      this.error = null
    },

    /**
     * Reset store state.
     */
    reset() {
      this.activities = []
      this.currentActivity = null
      this.loading = false
      this.error = null
    },
  },
})
