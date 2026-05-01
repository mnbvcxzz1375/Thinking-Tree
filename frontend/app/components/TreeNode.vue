<template>
  <div
    class="tree-node"
    :class="{
      'tree-node--selected': isSelected,
      'tree-node--dragging': isDragging,
      [`tree-node--${node.node_type}`]: true,
    }"
    :draggable="true"
    @click.stop="handleSelect"
    @dragstart="handleDragStart"
    @dragover.prevent="handleDragOver"
    @dragleave="handleDragLeave"
    @drop.prevent="handleDrop"
  >
    <div class="tree-node__header">
      <span class="tree-node__icon">{{ nodeIcon }}</span>

      <div v-if="!isEditing" class="tree-node__content" @dblclick="startEditing">
        {{ node.content }}
      </div>

      <input
        v-else
        ref="editInput"
        v-model="editContent"
        class="tree-node__input"
        @keydown.enter="commitEdit"
        @keydown.escape="cancelEdit"
        @blur="commitEdit"
      />

      <div class="tree-node__actions">
        <button
          class="tree-node__btn tree-node__btn--add"
          title="添加子节点"
          @click.stop="$emit('add-child', node.id)"
        >
          +
        </button>
        <button
          class="tree-node__btn tree-node__btn--edit"
          title="编辑"
          @click.stop="startEditing"
        >
          ✎
        </button>
        <button
          class="tree-node__btn tree-node__btn--delete"
          title="删除"
          @click.stop="$emit('delete', node.id)"
        >
          ×
        </button>
      </div>
    </div>

    <div v-if="node.children && node.children.length > 0" class="tree-node__children">
      <TreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :selected-id="selectedId"
        @select="$emit('select', $event)"
        @add-child="$emit('add-child', $event)"
        @delete="$emit('delete', $event)"
        @update-content="(id, content) => $emit('update-content', id, content)"
        @move="(nodeId, parentId) => $emit('move', nodeId, parentId)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed } from 'vue'
import type { TreeNode } from '~/stores/tree'

interface Props {
  node: TreeNode
  selectedId?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  selectedId: null,
})

const emit = defineEmits<{
  select: [nodeId: string]
  'add-child': [parentId: string]
  delete: [nodeId: string]
  'update-content': [nodeId: string, content: string]
  move: [nodeId: string, newParentId: string | null]
}>()

const isSelected = computed(() => props.selectedId === props.node.id)

const nodeIcon = computed(() => {
  switch (props.node.node_type) {
    case 'question':
      return '❓'
    case 'answer':
      return '💡'
    case 'insight':
      return '⭐'
    default:
      return '🔵'
  }
})

// ── Editing ────────────────────────────────────────────────────────

const isEditing = ref(false)
const editContent = ref('')
const editInput = ref<HTMLInputElement | null>(null)

function startEditing() {
  editContent.value = props.node.content
  isEditing.value = true
  nextTick(() => editInput.value?.focus())
}

function commitEdit() {
  if (!isEditing.value) return
  const trimmed = editContent.value.trim()
  if (trimmed && trimmed !== props.node.content) {
    emit('update-content', props.node.id, trimmed)
  }
  isEditing.value = false
}

function cancelEdit() {
  isEditing.value = false
}

// ── Selection ──────────────────────────────────────────────────────

function handleSelect() {
  emit('select', props.node.id)
}

// ── Drag & Drop (basic reorder) ───────────────────────────────────

const isDragging = ref(false)

function handleDragStart(e: DragEvent) {
  isDragging.value = true
  e.dataTransfer?.setData('text/plain', props.node.id)
  e.dataTransfer?.setDragImage(e.target as HTMLElement, 0, 0)
}

function handleDragOver(e: DragEvent) {
  ;(e.currentTarget as HTMLElement).classList.add('tree-node--drop-target')
}

function handleDragLeave(e: DragEvent) {
  ;(e.currentTarget as HTMLElement).classList.remove('tree-node--drop-target')
}

function handleDrop(e: DragEvent) {
  ;(e.currentTarget as HTMLElement).classList.remove('tree-node--drop-target')
  isDragging.value = false
  const draggedId = e.dataTransfer?.getData('text/plain')
  if (draggedId && draggedId !== props.node.id) {
    emit('move', draggedId, props.node.id)
  }
}
</script>

<style scoped>
.tree-node {
  position: relative;
  margin-left: 1.5rem;
  padding-left: 1rem;
  border-left: 2px solid #d1d5db;
  margin-bottom: 0.5rem;
}

.tree-node--drop-target {
  border-left-color: #2563eb;
  background: rgba(37, 99, 235, 0.05);
}

.tree-node--selected > .tree-node__header {
  background: #eff6ff;
  border-color: #2563eb;
}

.tree-node--dragging {
  opacity: 0.5;
}

.tree-node__header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  user-select: none;
}

.tree-node__header:hover {
  border-color: #9ca3af;
}

.tree-node__icon {
  font-size: 1.125rem;
  flex-shrink: 0;
}

.tree-node__content {
  flex: 1;
  font-size: 0.9375rem;
  color: #111827;
  line-height: 1.4;
}

.tree-node__input {
  flex: 1;
  font-size: 0.9375rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid #2563eb;
  border-radius: 0.25rem;
  outline: none;
}

.tree-node__actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.15s;
}

.tree-node__header:hover .tree-node__actions {
  opacity: 1;
}

.tree-node__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.15s;
  background: transparent;
  color: #6b7280;
}

.tree-node__btn:hover {
  background: #f3f4f6;
}

.tree-node__btn--delete:hover {
  background: #fee2e2;
  color: #dc2626;
}

.tree-node__btn--add:hover {
  background: #d1fae5;
  color: #059669;
}

.tree-node__children {
  margin-top: 0.25rem;
}

/* Node type styling */
.tree-node--question > .tree-node__header {
  border-left: 3px solid #3b82f6;
}

.tree-node--answer > .tree-node__header {
  border-left: 3px solid #10b981;
}

.tree-node--insight > .tree-node__header {
  border-left: 3px solid #f59e0b;
}
</style>
