/**
 * Offline support composable with change queue and sync.
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'

// Types
export interface OfflineChange {
  id: string
  type: 'create' | 'update' | 'delete'
  resource: string
  resourceId?: string
  data?: unknown
  timestamp: string
  synced: boolean
}

// Storage keys
const QUEUE_KEY = 'offline_changes_queue'
const STATUS_KEY = 'offline_status'

/**
 * Offline support composable
 */
export function useOffline() {
  // State - use false as default for SSR safety
  const isOnline = ref(true) // Will be updated on mount
  const isSyncing = ref(false)
  const lastSyncAttempt = ref<string | null>(null)
  const syncError = ref<string | null>(null)
  const pendingChanges = ref<OfflineChange[]>([])

  // Load queue from storage
  function loadQueue(): OfflineChange[] {
    try {
      const stored = localStorage.getItem(QUEUE_KEY)
      if (stored) {
        return JSON.parse(stored)
      }
    } catch (e) {
      console.warn('Failed to load offline queue:', e)
    }
    return []
  }

  // Save queue to storage
  function saveQueue(): void {
    try {
      localStorage.setItem(QUEUE_KEY, JSON.stringify(pendingChanges.value))
    } catch (e) {
      console.warn('Failed to save offline queue:', e)
    }
  }

  // Generate unique ID
  function generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  // Event handlers
  function handleOnline() {
    isOnline.value = true
    syncPendingChanges()
  }

  function handleOffline() {
    isOnline.value = false
  }

  // Add change to queue
  function addChange(change: Omit<OfflineChange, 'id' | 'timestamp' | 'synced'>): OfflineChange {
    const newChange: OfflineChange = {
      ...change,
      id: generateId(),
      timestamp: new Date().toISOString(),
      synced: false,
    }

    pendingChanges.value.push(newChange)
    saveQueue()

    return newChange
  }

  // Mark change as synced
  function markSynced(changeId: string): void {
    const change = pendingChanges.value.find(c => c.id === changeId)
    if (change) {
      change.synced = true
      saveQueue()
    }
  }

  // Remove synced changes
  function clearSyncedChanges(): void {
    pendingChanges.value = pendingChanges.value.filter(c => !c.synced)
    saveQueue()
  }

  // Get pending changes for a resource
  function getPendingChanges(resource?: string): OfflineChange[] {
    if (resource) {
      return pendingChanges.value.filter(c => c.resource === resource && !c.synced)
    }
    return pendingChanges.value.filter(c => !c.synced)
  }

  // Sync pending changes
  async function syncPendingChanges(): Promise<void> {
    if (!isOnline.value || isSyncing.value) return

    isSyncing.value = true
    syncError.value = null
    lastSyncAttempt.value = new Date().toISOString()

    try {
      // This would typically call the API to sync changes
      // For now, we'll just mark them as synced
      const unsynced = pendingChanges.value.filter(c => !c.synced)

      for (const change of unsynced) {
        try {
          // Simulate sync - in real app, this would call the API
          await new Promise(resolve => setTimeout(resolve, 100))
          markSynced(change.id)
        } catch (e) {
          syncError.value = `Failed to sync change ${change.id}`
          break
        }
      }

      // Clear synced changes
      clearSyncedChanges()
    } catch (e) {
      syncError.value = e instanceof Error ? e.message : 'Sync failed'
    } finally {
      isSyncing.value = false
    }
  }

  // Check if there are pending changes
  const hasPendingChanges = computed(() => {
    return pendingChanges.value.some(c => !c.synced)
  })

  // Count pending changes
  const pendingCount = computed(() => {
    return pendingChanges.value.filter(c => !c.synced).length
  })

  // Lifecycle
  onMounted(() => {
    // Set online status from browser API
    isOnline.value = navigator.onLine

    // Load queue
    pendingChanges.value = loadQueue()

    // Add event listeners
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Sync if online and have pending changes
    if (isOnline.value && hasPendingChanges.value) {
      syncPendingChanges()
    }
  })

  onUnmounted(() => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  })

  return {
    // State
    isOnline,
    isSyncing,
    lastSyncAttempt,
    syncError,
    pendingChanges,

    // Getters
    hasPendingChanges,
    pendingCount,

    // Actions
    addChange,
    markSynced,
    clearSyncedChanges,
    getPendingChanges,
    syncPendingChanges,
  }
}
