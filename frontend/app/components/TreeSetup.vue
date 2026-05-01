<script setup lang="ts">
import { ref } from 'vue'

interface Direction {
  id: string
  name: string
  emoji: string
}

const emit = defineEmits<{
  complete: [data: { theme: string; directions: Direction[] }]
}>()

const theme = ref('')
const directions = ref<Direction[]>([
  { id: 'dir-1', name: '', emoji: '🌿' },
  { id: 'dir-2', name: '', emoji: '🌱' },
  { id: 'dir-3', name: '', emoji: '🍃' }
])

const emojiOptions = ['🌿', '🌱', '🍃', '🌳', '🌲', '🌴', '🎄', '🌻', '🌺', '🌸', '🍎', '🍊', '🍋', '💡', '❤️', '⭐']

function addDirection() {
  if (directions.value.length < 8) {
    directions.value.push({
      id: `dir-${Date.now()}`,
      name: '',
      emoji: emojiOptions[Math.floor(Math.random() * emojiOptions.length)]
    })
  }
}

function removeDirection(index: number) {
  if (directions.value.length > 1) {
    directions.value.splice(index, 1)
  }
}

function handleSubmit() {
  if (theme.value.trim() && directions.value.some(d => d.name.trim())) {
    const validDirections = directions.value.filter(d => d.name.trim())
    emit('complete', {
      theme: theme.value.trim(),
      directions: validDirections
    })
  }
}

const presets = [
  { theme: '一棵树', directions: ['外形', '生命', '朋友', '情绪', '用途'] },
  { theme: '我的校园', directions: ['建筑', '老师', '同学', '活动', '感受'] },
  { theme: '如果我是一只小鸟', directions: ['飞翔', '家园', '朋友', '冒险', '自由'] }
]

function applyPreset(preset: typeof presets[0]) {
  theme.value = preset.theme
  directions.value = preset.directions.map((name, i) => ({
    id: `dir-${i}`,
    name,
    emoji: emojiOptions[i % emojiOptions.length]
  }))
}
</script>

<template>
  <div class="setup-overlay">
    <div class="setup-card">
      <div class="setup-header">
        <h1>🌳 创建思维树</h1>
        <p>设置活动主题和思考方向，开始思维探索之旅</p>
      </div>

      <div class="setup-body">
        <div class="section">
          <h2>📝 活动主题</h2>
          <p class="hint">这是思维树的根节点，代表本次活动的核心主题</p>
          <input 
            v-model="theme" 
            placeholder="例如：一棵树、我的校园、如果我是一只小鸟..."
            class="theme-input"
          />
        </div>

        <div class="section">
          <h2>🌿 快速模板</h2>
          <div class="presets">
            <button 
              v-for="preset in presets" 
              :key="preset.theme"
              class="preset-btn"
              @click="applyPreset(preset)"
            >
              {{ preset.theme }}
            </button>
          </div>
        </div>

        <div class="section">
          <h2>🎯 思考方向</h2>
          <p class="hint">设置一级方向节点，引导儿童从不同角度思考</p>
          
          <div class="directions-list">
            <div 
              v-for="(dir, index) in directions" 
              :key="dir.id" 
              class="direction-item"
            >
              <select v-model="dir.emoji" class="emoji-select">
                <option v-for="emoji in emojiOptions" :key="emoji" :value="emoji">
                  {{ emoji }}
                </option>
              </select>
              
              <input 
                v-model="dir.name" 
                :placeholder="`方向 ${index + 1}，例如：外形、生命...`"
                class="direction-input"
              />
              
              <button 
                v-if="directions.length > 1"
                class="remove-btn"
                @click="removeDirection(index)"
              >
                ×
              </button>
            </div>
          </div>

          <button 
            v-if="directions.length < 8"
            class="add-btn" 
            @click="addDirection"
          >
            ＋ 添加方向
          </button>
        </div>
      </div>

      <div class="setup-footer">
        <button 
          class="start-btn" 
          :disabled="!theme.trim() || !directions.some(d => d.name.trim())"
          @click="handleSubmit"
        >
          🌱 开始创建思维树
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.setup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 50%, #A5D6A7 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}

.setup-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

.setup-header {
  text-align: center;
  padding: 30px 30px 20px;
  background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
  border-radius: 20px 20px 0 0;
  color: white;
}

.setup-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
}

.setup-header p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.setup-body {
  padding: 30px;
}

.section {
  margin-bottom: 24px;
}

.section h2 {
  margin: 0 0 8px;
  font-size: 18px;
  color: #2E7D32;
}

.hint {
  margin: 0 0 12px;
  font-size: 13px;
  color: #666;
}

.theme-input {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #E0E0E0;
  border-radius: 12px;
  font-size: 16px;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.theme-input:focus {
  outline: none;
  border-color: #4CAF50;
}

.presets {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.preset-btn {
  padding: 8px 16px;
  background: #F5F5F5;
  border: 2px solid #E0E0E0;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.preset-btn:hover {
  background: #E8F5E9;
  border-color: #4CAF50;
}

.directions-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.direction-item {
  display: flex;
  gap: 10px;
  align-items: center;
}

.emoji-select {
  padding: 10px;
  border: 2px solid #E0E0E0;
  border-radius: 8px;
  font-size: 18px;
  background: white;
  cursor: pointer;
}

.direction-input {
  flex: 1;
  padding: 10px 14px;
  border: 2px solid #E0E0E0;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.direction-input:focus {
  outline: none;
  border-color: #4CAF50;
}

.remove-btn {
  width: 32px;
  height: 32px;
  background: #FF5722;
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.remove-btn:hover {
  background: #E64A19;
}

.add-btn {
  width: 100%;
  padding: 12px;
  background: #E3F2FD;
  border: 2px dashed #90CAF9;
  border-radius: 8px;
  color: #1976D2;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 10px;
  transition: all 0.2s;
}

.add-btn:hover {
  background: #BBDEFB;
  border-color: #42A5F5;
}

.setup-footer {
  padding: 20px 30px 30px;
  text-align: center;
}

.start-btn {
  width: 100%;
  padding: 16px 32px;
  background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.start-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(76, 175, 80, 0.3);
}

.start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
