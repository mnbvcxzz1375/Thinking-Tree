/**
 * Tree store with persistence and state synchronization.
 */
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

// Types
export interface TreeNode {
  id: string
  label: string
  content: string
  nodeType: 'question' | 'answer' | 'insight' | 'root' | 'branch' | 'direction'
  parentId: string | null
  children: TreeNode[]
  metadata?: Record<string, unknown>
  createdAt?: string
  updatedAt?: string
}

export interface TreeState {
  id: string | null
  title: string
  description: string
  instructions: string
  nodes: TreeNode[]
  selectedNodeId: string | null
  loading: boolean
  error: string | null
  lastSynced: string | null
  isDirty: boolean
  activityId: number | null
}

// Storage key
const STORAGE_KEY = 'thinking_tree_state'
const BACKUP_KEY = 'thinking_tree_backup'

/**
 * Load state from localStorage
 */
function loadFromStorage(): Partial<TreeState> | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.warn('Failed to load state from storage:', e)
  }
  return null
}

/**
 * Save state to localStorage
 */
function saveToStorage(state: TreeState): void {
  try {
    const serializable = {
      id: state.id,
        title: state.title,
        description: state.description,
        instructions: state.instructions,
        nodes: state.nodes,
      selectedNodeId: state.selectedNodeId,
      lastSynced: state.lastSynced,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(serializable))
  } catch (e) {
    console.warn('Failed to save state to storage:', e)
  }
}

/**
 * Create backup of current state
 */
function createBackup(state: TreeState): void {
  try {
    const backup = {
      timestamp: new Date().toISOString(),
      state: {
        id: state.id,
        title: state.title,
        nodes: state.nodes,
      },
    }
    localStorage.setItem(BACKUP_KEY, JSON.stringify(backup))
  } catch (e) {
    console.warn('Failed to create backup:', e)
  }
}

/**
 * Restore from backup
 */
function restoreFromBackup(): { id: string | null; title: string; nodes: TreeNode[] } | null {
  try {
    const backup = localStorage.getItem(BACKUP_KEY)
    if (backup) {
      const parsed = JSON.parse(backup)
      return parsed.state
    }
  } catch (e) {
    console.warn('Failed to restore from backup:', e)
  }
  return null
}

/**
 * Tree store with persistence
 */
export const useTreeStore = defineStore('tree', () => {
  // Load initial state from storage
  const stored = loadFromStorage()

  // State
  const id = ref<string | null>(stored?.id || null)
  const title = ref(stored?.title || 'New Thinking Tree')
  const description = ref(stored?.description || '')
  const instructions = ref((stored as Partial<TreeState>)?.instructions || '')
  const nodes = ref<TreeNode[]>(stored?.nodes || [])
  const selectedNodeId = ref<string | null>(stored?.selectedNodeId || null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastSynced = ref<string | null>(stored?.lastSynced || null)
  const isDirty = ref(false)
  const activityId = ref<number | null>(null)

  // Getters
  const nodeCount = computed(() => countNodes(nodes.value))
  const isEmpty = computed(() => nodes.value.length === 0)
  const selectedNode = computed(() => {
    if (!selectedNodeId.value) return null
    return findNode(nodes.value, selectedNodeId.value)
  })

  const hasUnsavedChanges = computed(() => isDirty.value)

  // Watch for state changes and persist
  watch(
    [id, title, description, instructions, nodes, selectedNodeId],
    () => {
      isDirty.value = true
      saveToStorage({
        id: id.value,
        title: title.value,
        description: description.value,
        instructions: instructions.value,
        nodes: nodes.value,
        selectedNodeId: selectedNodeId.value,
        loading: loading.value,
        error: error.value,
        lastSynced: lastSynced.value,
        isDirty: isDirty.value,
      })
    },
    { deep: true }
  )

  // Actions
  function setTree(tree: { id: string; title: string; description?: string; instructions?: string; nodes: TreeNode[]; activityId?: number | null }) {
    id.value = tree.id
    title.value = tree.title
    description.value = tree.description || ''
    instructions.value = tree.instructions || ''
    nodes.value = tree.nodes
    activityId.value = tree.activityId ?? null
    isDirty.value = false
    lastSynced.value = new Date().toISOString()
  }

  function addNode(parentId: string | null, node: TreeNode) {
    if (!parentId) {
      nodes.value.push(node)
    } else {
      const parent = findNode(nodes.value, parentId)
      if (parent) {
        parent.children.push(node)
      }
    }
    isDirty.value = true
  }

  function removeNode(nodeId: string) {
    nodes.value = removeNodeById(nodes.value, nodeId)
    if (selectedNodeId.value === nodeId) {
      selectedNodeId.value = null
    }
    isDirty.value = true
  }

  function updateNode(nodeId: string, updates: Partial<TreeNode>) {
    const node = findNode(nodes.value, nodeId)
    if (node) {
      Object.assign(node, updates)
      isDirty.value = true
    }
  }

  function selectNode(nodeId: string | null) {
    selectedNodeId.value = nodeId
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setError(value: string | null) {
    error.value = value
  }

  function markSynced() {
    isDirty.value = false
    lastSynced.value = new Date().toISOString()
  }

  function setActivityId(id: number | null) {
    activityId.value = id
  }

  function setActivityContext(context: {
    activityId?: number | null
    title?: string
    description?: string | null
    instructions?: string | null
  }) {
    if (context.activityId !== undefined) activityId.value = context.activityId
    if (context.title !== undefined) title.value = context.title
    if (context.description !== undefined) description.value = context.description || ''
    if (context.instructions !== undefined) instructions.value = context.instructions || ''
  }

  function reset() {
    // Create backup before reset
    createBackup({
      id: id.value,
      title: title.value,
      description: description.value,
      instructions: instructions.value,
      nodes: nodes.value,
      selectedNodeId: selectedNodeId.value,
      loading: loading.value,
      error: error.value,
      lastSynced: lastSynced.value,
      isDirty: isDirty.value,
    })

    id.value = null
    title.value = 'New Thinking Tree'
    description.value = ''
    instructions.value = ''
    nodes.value = []
    selectedNodeId.value = null
    loading.value = false
    error.value = null
    lastSynced.value = null
    isDirty.value = false
  }

  function restoreBackup(): boolean {
    const backup = restoreFromBackup()
    if (backup) {
      id.value = backup.id
      title.value = backup.title
      nodes.value = backup.nodes
      isDirty.value = true
      return true
    }
    return false
  }

  function exportState(): TreeState {
    return {
      id: id.value,
      title: title.value,
      description: description.value,
      instructions: instructions.value,
      nodes: nodes.value,
      selectedNodeId: selectedNodeId.value,
      loading: loading.value,
      error: error.value,
      lastSynced: lastSynced.value,
      isDirty: isDirty.value,
      activityId: activityId.value,
    }
  }

  function importState(state: TreeState) {
    id.value = state.id
    title.value = state.title
    description.value = state.description
    instructions.value = state.instructions || ''
    nodes.value = state.nodes
    selectedNodeId.value = state.selectedNodeId
    activityId.value = state.activityId
    isDirty.value = true
  }

  return {
    // State
    id,
    title,
    description,
    instructions,
    nodes,
    selectedNodeId,
    loading,
    error,
    lastSynced,
    isDirty,
    activityId,

    // Getters
    nodeCount,
    isEmpty,
    selectedNode,
    hasUnsavedChanges,

    // Actions
    setTree,
    addNode,
    removeNode,
    updateNode,
    selectNode,
    setLoading,
    setError,
    markSynced,
    setActivityId,
    setActivityContext,
    reset,
    restoreBackup,
    exportState,
    importState,
  }
})

// Tree helper functions
function countNodes(nodes: TreeNode[]): number {
  return nodes.reduce((count, node) => count + 1 + countNodes(node.children), 0)
}

function findNode(nodes: TreeNode[], id: string): TreeNode | null {
  for (const node of nodes) {
    if (node.id === id) return node
    const found = findNode(node.children, id)
    if (found) return found
  }
  return null
}

function removeNodeById(nodes: TreeNode[], id: string): TreeNode[] {
  return nodes
    .filter((node) => node.id !== id)
    .map((node) => ({
      ...node,
      children: removeNodeById(node.children, id),
    }))
}
