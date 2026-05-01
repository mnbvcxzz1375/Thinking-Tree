<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  node: {
    id: string
    label: string
    content: string
    nodeType: string
  } | null
  position: { x: number; y: number }
  isNew?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  save: [data: { id: string; label: string; content: string }]
  delete: [id: string]
  addChild: [parentId: string]
  close: []
}>()

const editLabel = ref('')
const editContent = ref('')
const isEditing = ref(false)

watch(() => props.node, (newNode) => {
  if (newNode) {
    editLabel.value = newNode.label
    editContent.value = newNode.content
    isEditing.value = true
  } else {
    isEditing.value = false
  }
}, { immediate: true })

function handleSave() {
  if (props.node && editLabel.value.trim()) {
    emit('save', {
      id: props.node.id,
      label: editLabel.value.trim(),
      content: editContent.value.trim()
    })
    isEditing.value = false
  }
}

function handleDelete() {
  if (props.node && confirm('确定要删除这个节点吗？')) {
    emit('delete', props.node.id)
    isEditing.value = false
  }
}

function handleAddChild() {
  if (props.node) {
    emit('addChild', props.node.id)
    isEditing.value = false
  }
}

function handleClose() {
  isEditing.value = false
  emit('close')
}
</script>

<template>
  <div 
    v-if="isEditing && node" 
    class="node-editor"
    :style="{ left: position.x + 'px', top: position.y + 'px' }"
  >
    <div class="editor-header">
      <span class="editor-title">{{ isNew ? '添加节点' : '编辑节点' }}</span>
      <button class="close-btn" @click="handleClose">×</button>
    </div>
    
    <div class="editor-body">
      <div class="form-group">
        <label>标题</label>
        <input 
          v-model="editLabel" 
          placeholder="输入节点标题..."
          @keyup.enter="handleSave"
          autofocus
        />
      </div>
      
      <div class="form-group">
        <label>内容</label>
        <textarea 
          v-model="editContent" 
          placeholder="输入详细内容..."
          rows="3"
        />
      </div>
      
      <div class="node-type-badge" v-if="node.nodeType">
        {{ node.nodeType === 'root' ? '🌳 主题' : node.nodeType === 'direction' ? '🌿 方向' : node.nodeType === 'insight' ? '🤖 AI' : '💭 想法' }}
      </div>
    </div>
    
    <div class="editor-actions">
      <button class="btn-save" @click="handleSave">💾 保存</button>
      <button class="btn-add" @click="handleAddChild">➕ 添加子节点</button>
      <button class="btn-delete" @click="handleDelete" v-if="node.nodeType !== 'root'">🗑️ 删除</button>
    </div>
  </div>
</template>

<style scoped>
.node-editor {
  position: fixed;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  min-width: 280px;
  max-width: 350px;
  z-index: 1000;
  overflow: hidden;
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
  color: white;
}

.editor-title {
  font-weight: 600;
  font-size: 14px;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.editor-body {
  padding: 16px;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 4px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 2px solid #E0E0E0;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #4CAF50;
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
}

.node-type-badge {
  display: inline-block;
  padding: 4px 10px;
  background: #F5F5F5;
  border-radius: 12px;
  font-size: 12px;
  color: #666;
}

.editor-actions {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background: #FAFAFA;
  border-top: 1px solid #E0E0E0;
}

.editor-actions button {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-save {
  background: #4CAF50;
  color: white;
}

.btn-save:hover {
  background: #43A047;
}

.btn-add {
  background: #2196F3;
  color: white;
}

.btn-add:hover {
  background: #1976D2;
}

.btn-delete {
  background: #FF5722;
  color: white;
}

.btn-delete:hover {
  background: #E64A19;
}
</style>
