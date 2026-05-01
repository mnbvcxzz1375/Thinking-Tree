<template>
  <div class="tree-node-children">
    <div v-if="children.length === 0" class="tree-node-children__empty">
      <p class="tree-node-children__hint">暂无子节点</p>
      <button
        class="btn btn--sm btn--primary"
        @click="$emit('add-child', parentId)"
      >
        + 添加子节点
      </button>
    </div>

    <div v-else class="tree-node-children__list">
      <div
        v-for="(child, index) in children"
        :key="child.id"
        class="tree-node-children__item"
        :class="{ 'tree-node-children__item--first': index === 0 }"
      >
        <div class="tree-node-children__connector" />
        <div class="tree-node-children__node">
          <div class="tree-node-children__header" @click="$emit('select', child.id)">
            <span class="tree-node-children__icon">{{ getIcon(child.node_type) }}</span>
            <span class="tree-node-children__content">{{ child.content }}</span>
            <span class="tree-node-children__badge">{{ getTypeLabel(child.node_type) }}</span>
          </div>
          <div class="tree-node-children__actions">
            <button
              class="tree-node-children__btn"
              title="添加子节点"
              @click="$emit('add-child', child.id)"
            >
              +
            </button>
            <button
              class="tree-node-children__btn tree-node-children__btn--delete"
              title="删除"
              @click="$emit('delete', child.id)"
            >
              ×
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TreeNodeFlat } from '~/stores/tree'

interface Props {
  parentId: string | null
  children: TreeNodeFlat[]
}

defineProps<Props>()

defineEmits<{
  select: [nodeId: string]
  'add-child': [parentId: string]
  delete: [nodeId: string]
}>()

function getIcon(type: string): string {
  switch (type) {
    case 'question':
      return '❓'
    case 'answer':
      return '💡'
    case 'insight':
      return '⭐'
    default:
      return '🔵'
  }
}

function getTypeLabel(type: string): string {
  switch (type) {
    case 'question':
      return '问题'
    case 'answer':
      return '回答'
    case 'insight':
      return '洞察'
    default:
      return type
  }
}
</script>

<style scoped>
.tree-node-children {
  margin-left: 1rem;
}

.tree-node-children__empty {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px dashed #d1d5db;
  border-radius: 0.5rem;
  color: #9ca3af;
}

.tree-node-children__hint {
  margin: 0;
  font-size: 0.875rem;
}

.tree-node-children__list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tree-node-children__item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  position: relative;
}

.tree-node-children__connector {
  width: 1.5rem;
  height: 1.25rem;
  border-left: 2px solid #d1d5db;
  border-bottom: 2px solid #d1d5db;
  border-bottom-left-radius: 0.5rem;
  flex-shrink: 0;
  margin-top: 0;
}

.tree-node-children__node {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: #fff;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.tree-node-children__node:hover {
  border-color: #9ca3af;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.tree-node-children__header {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.tree-node-children__icon {
  font-size: 1rem;
}

.tree-node-children__content {
  font-size: 0.9375rem;
  color: #111827;
}

.tree-node-children__badge {
  font-size: 0.6875rem;
  padding: 0.125rem 0.375rem;
  border-radius: 9999px;
  background: #f3f4f6;
  color: #6b7280;
}

.tree-node-children__actions {
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.15s;
}

.tree-node-children__node:hover .tree-node-children__actions {
  opacity: 1;
}

.tree-node-children__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
  border: none;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  cursor: pointer;
  background: transparent;
  color: #6b7280;
  transition: background 0.15s;
}

.tree-node-children__btn:hover {
  background: #f3f4f6;
}

.tree-node-children__btn--delete:hover {
  background: #fee2e2;
  color: #dc2626;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
}

.btn--sm {
  padding: 0.25rem 0.625rem;
  font-size: 0.8125rem;
}

.btn--primary {
  background: #2563eb;
  color: #fff;
}

.btn--primary:hover {
  background: #1d4ed8;
}
</style>
