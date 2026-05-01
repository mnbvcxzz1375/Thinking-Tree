/**
 * Composable for teacher confirmation workflow.
 * Provides visual feedback, notifications, and workflow orchestration.
 */
import { ref, computed } from 'vue'
import { useCandidateStore } from '~/stores/candidate'
import { useTreeStore } from '~/stores/tree'
import type { CandidateNode, ConfirmationRecord } from '~/stores/candidate'
import type { TreeNode } from '~/stores/tree'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'info' | 'warning'
  message: string
  duration?: number
}

export function useTeacherConfirmation() {
  const candidateStore = useCandidateStore()
  const treeStore = useTreeStore()

  // UI State
  const isPanelOpen = ref(false)
  const isHistoryOpen = ref(false)
  const isConfirmDialogOpen = ref(false)
  const activeCandidate = ref<CandidateNode | null>(null)
  const notifications = ref<Notification[]>([])

  // Computed
  const hasPendingCandidates = computed(() => candidateStore.pendingCount > 0)

  // Notification helpers
  function addNotification(type: Notification['type'], message: string, duration = 3000) {
    const id = `notif_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
    const notification: Notification = { id, type, message, duration }
    notifications.value.push(notification)

    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, duration)
    }
  }

  function removeNotification(id: string) {
    notifications.value = notifications.value.filter((n) => n.id !== id)
  }

  // Panel controls
  function togglePanel() {
    isPanelOpen.value = !isPanelOpen.value
    if (isPanelOpen.value) {
      isHistoryOpen.value = false
    }
  }

  function toggleHistory() {
    isHistoryOpen.value = !isHistoryOpen.value
    if (isHistoryOpen.value) {
      isPanelOpen.value = false
    }
  }

  // Dialog controls
  function openConfirmDialog(candidateId: string) {
    const candidate = candidateStore.candidates.find((c) => c.id === candidateId)
    if (candidate) {
      activeCandidate.value = candidate
      isConfirmDialogOpen.value = true
    }
  }

  function closeConfirmDialog() {
    isConfirmDialogOpen.value = false
    activeCandidate.value = null
  }

  // Confirmation actions
  function handleConfirm(candidateId: string, editedText?: string) {
    const candidate = candidateStore.candidates.find((c) => c.id === candidateId)
    if (!candidate) return

    // Determine final text
    const finalText = editedText || candidate.leafText
    const isEdited = editedText && editedText !== candidate.leafText

    // Add to tree
    const newNode: TreeNode = {
      id: `node_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
      label: finalText.slice(0, 20),
      content: finalText,
      nodeType: candidate.nodeType,
      parentId: candidate.suggestedParentId,
      children: [],
      createdAt: new Date().toISOString(),
    }

    treeStore.addNode(candidate.suggestedParentId, newNode)

    // Record confirmation
    if (isEdited) {
      candidateStore.editAndConfirm(candidateId, finalText)
      addNotification('success', `节点已编辑确认: ${finalText.slice(0, 30)}...`)
    } else {
      candidateStore.confirmCandidate(candidateId)
      addNotification('success', `节点已确认: ${finalText.slice(0, 30)}...`)
    }

    closeConfirmDialog()
  }

  function handleReject(candidateId: string) {
    candidateStore.rejectCandidate(candidateId)
    addNotification('info', '候选节点已拒绝')
    closeConfirmDialog()
  }

  function handleMove(candidateId: string) {
    // For now, just mark as moved with null parent
    // In a real implementation, this would open a tree picker
    candidateStore.moveAndConfirm(candidateId, null)
    addNotification('warning', '节点已标记移动 - 请选择新的父节点')
    closeConfirmDialog()
  }

  function handleUndo(recordId: string) {
    const restored = candidateStore.undoConfirmation(recordId)
    if (restored) {
      addNotification('info', '操作已撤销')
    } else {
      addNotification('error', '撤销窗口已过期')
    }
  }

  function handleConfirmAll() {
    const pending = candidateStore.pendingCandidates
    let confirmed = 0

    for (const candidate of pending) {
      const newNode: TreeNode = {
        id: `node_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
        label: candidate.leafText.slice(0, 20),
        content: candidate.leafText,
        nodeType: candidate.nodeType,
        parentId: candidate.suggestedParentId,
        children: [],
        createdAt: new Date().toISOString(),
      }

      treeStore.addNode(candidate.suggestedParentId, newNode)
      candidateStore.confirmCandidate(candidate.id)
      confirmed++
    }

    if (confirmed > 0) {
      addNotification('success', `已确认 ${confirmed} 个候选节点`)
    }
  }

  function handleClearAll() {
    candidateStore.clearPending()
    addNotification('info', '已清空所有候选节点')
  }

  function handleExportHistory() {
    const data = candidateStore.exportHistory()
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `confirmation_history_${new Date().toISOString().slice(0, 10)}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    addNotification('success', '历史记录已导出')
  }

  function handleClearHistory() {
    candidateStore.clearHistory()
    addNotification('info', '历史记录已清空')
  }

  // Simulate AI generating candidates (for testing)
  function simulateAICandidates() {
    const mockCandidates = [
      {
        transcript: '我觉得小兔子应该帮助小熊',
        leafText: '帮助他人是美德',
        followUpQuestion: '为什么帮助别人很重要呢？',
        suggestedParentId: treeStore.nodes[0]?.id || null,
        nodeType: 'insight' as const,
        confidence: 0.85,
      },
      {
        transcript: '因为如果我不帮他，他会很伤心',
        leafText: '共情能力',
        followUpQuestion: '你能感受到别人的心情吗？',
        suggestedParentId: treeStore.nodes[0]?.id || null,
        nodeType: 'answer' as const,
        confidence: 0.72,
      },
      {
        transcript: '我们要像超人一样勇敢',
        leafText: '勇敢面对困难',
        followUpQuestion: '什么时候你觉得需要勇敢？',
        suggestedParentId: treeStore.nodes[0]?.id || null,
        nodeType: 'question' as const,
        confidence: 0.68,
      },
    ]

    candidateStore.addCandidates(mockCandidates)
    addNotification('info', `AI 生成了 ${mockCandidates.length} 个候选节点`)
    isPanelOpen.value = true
  }

  return {
    // State
    isPanelOpen,
    isHistoryOpen,
    isConfirmDialogOpen,
    activeCandidate,
    notifications,
    hasPendingCandidates,

    // Actions
    togglePanel,
    toggleHistory,
    openConfirmDialog,
    closeConfirmDialog,
    handleConfirm,
    handleReject,
    handleMove,
    handleUndo,
    handleConfirmAll,
    handleClearAll,
    handleExportHistory,
    handleClearHistory,
    simulateAICandidates,
    addNotification,
    removeNotification,
  }
}
