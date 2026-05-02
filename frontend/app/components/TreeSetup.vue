<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface Direction {
  id: string
  name: string
  emoji: string
  children?: Direction[]
  metadata?: Record<string, unknown>
}

type TreeMode = 'normal' | 'debate'

const props = withDefaults(defineProps<{
  initialTheme?: string
  initialMode?: TreeMode
  initialProLabel?: string
  initialConLabel?: string
}>(), {
  initialTheme: '',
  initialMode: 'normal',
  initialProLabel: '放走蚂蚁',
  initialConLabel: '踩扁蚂蚁',
})

const emit = defineEmits<{
  complete: [data: { theme: string; mode: TreeMode; directions: Direction[]; proLabel?: string; conLabel?: string }]
}>()

const mode = ref<TreeMode>(props.initialMode)
const theme = ref(props.initialTheme)
const proLabel = ref(props.initialProLabel)
const conLabel = ref(props.initialConLabel)
const directions = ref<Direction[]>([
  { id: 'dir-1', name: '', emoji: '🌿' },
  { id: 'dir-2', name: '', emoji: '🍃' },
  { id: 'dir-3', name: '', emoji: '🌱' },
])
const debateDirections = ref<Direction[]>([
  { id: 'debate-reason', name: '理由', emoji: '💬' },
  { id: 'debate-result', name: '后果', emoji: '🌾' },
  { id: 'debate-feeling', name: '感受', emoji: '💛' },
  { id: 'debate-example', name: '例子', emoji: '🔎' },
])

const emojiOptions = ['🌿', '🍃', '🌱', '🌾', '🌵', '🌳', '🌸', '🌼', '🍀', '🍂', '💬', '💛', '🔎', '⭐']

const activeDirections = computed(() => (mode.value === 'debate' ? debateDirections.value : directions.value))
const canSubmit = computed(() => {
  if (!theme.value.trim()) return false
  if (mode.value === 'debate' && (!proLabel.value.trim() || !conLabel.value.trim())) return false
  return activeDirections.value.some((d) => d.name.trim())
})

watch(mode, (newMode) => {
  if (newMode === 'debate' && !theme.value.trim()) {
    theme.value = '放走蚂蚁 / 踩扁蚂蚁'
  }
})

watch(
  () => [props.initialTheme, props.initialMode, props.initialProLabel, props.initialConLabel] as const,
  ([nextTheme, nextMode, nextProLabel, nextConLabel]) => {
    if (nextTheme && !theme.value.trim()) theme.value = nextTheme
    if (nextMode) mode.value = nextMode
    if (nextProLabel) proLabel.value = nextProLabel
    if (nextConLabel) conLabel.value = nextConLabel
  }
)

function addDirection() {
  const target = activeDirections.value
  if (target.length < 8) {
    target.push({
      id: `${mode.value}-dir-${Date.now()}`,
      name: '',
      emoji: emojiOptions[Math.floor(Math.random() * emojiOptions.length)] || '🌿',
    })
  }
}

function removeDirection(index: number) {
  const target = activeDirections.value
  if (target.length > 1) {
    target.splice(index, 1)
  }
}

function createDebateSideDirections(role: 'pro' | 'con', stanceLabel: string) {
  const prefix = role === 'pro' ? 'debate-pro' : 'debate-con'
  return debateDirections.value
    .filter((d) => d.name.trim())
    .map((d, index) => ({
      id: `${prefix}-${d.id || index}`,
      name: d.name.trim(),
      emoji: d.emoji,
      metadata: {
        debateRole: role,
        debateLevel: 'direction',
        debateLabel: role === 'pro' ? '正方' : '反方',
        debateStanceLabel: stanceLabel,
      },
    }))
}

function handleSubmit() {
  if (!canSubmit.value) return

  if (mode.value === 'debate') {
    const proText = proLabel.value.trim()
    const conText = conLabel.value.trim()
    emit('complete', {
      theme: theme.value.trim(),
      mode: 'debate',
      proLabel: proText,
      conLabel: conText,
      directions: [
        ...createDebateSideDirections('pro', proText),
        ...createDebateSideDirections('con', conText),
      ],
    })
    return
  }

  emit('complete', {
    theme: theme.value.trim(),
    mode: 'normal',
    directions: directions.value.filter((d) => d.name.trim()).map((d) => ({ ...d, name: d.name.trim() })),
  })
}

const presets = [
  { theme: '一棵树', directions: ['外形', '生命', '朋友', '情绪', '用途'] },
  { theme: '我的校园', directions: ['建筑', '老师', '同学', '活动', '感受'] },
  { theme: '如果我是一只小鸟', directions: ['飞翔', '家园', '朋友', '冒险', '自由'] },
]

function applyPreset(preset: typeof presets[0]) {
  mode.value = 'normal'
  theme.value = preset.theme
  directions.value = preset.directions.map((name, i) => ({
    id: `dir-${i}`,
    name,
    emoji: emojiOptions[i % emojiOptions.length] || '🌿',
  }))
}

function applyDebatePreset() {
  mode.value = 'debate'
  theme.value = '放走蚂蚁 / 踩扁蚂蚁'
  proLabel.value = '放走蚂蚁'
  conLabel.value = '踩扁蚂蚁'
  debateDirections.value = [
    { id: 'reason', name: '理由', emoji: '💬' },
    { id: 'life', name: '生命', emoji: '🌱' },
    { id: 'result', name: '后果', emoji: '🌾' },
    { id: 'feeling', name: '感受', emoji: '💛' },
  ]
}
</script>

<template>
  <div class="setup-overlay">
    <div class="setup-card">
      <div class="setup-header">
        <h1>🌳 创建思维树</h1>
        <p>设置活动主题和思考结构，开始孩子的表达整理</p>
      </div>

      <div class="setup-scroll">
        <div class="setup-body">
          <div class="section">
            <h2>模式</h2>
            <div class="mode-tabs">
              <button :class="{ active: mode === 'normal' }" @click="mode = 'normal'">普通思维树</button>
              <button :class="{ active: mode === 'debate' }" @click="mode = 'debate'">辩论模式</button>
            </div>
          </div>

          <div class="section">
            <h2>活动主题</h2>
            <p class="hint">这是根节点，代表本次活动或辩论题目。</p>
            <input
              v-model="theme"
              placeholder="例如：放走蚂蚁 / 踩扁蚂蚁"
              class="theme-input"
            />
          </div>

          <div class="section">
            <h2>快速模板</h2>
            <div class="presets">
              <button v-for="preset in presets" :key="preset.theme" class="preset-btn" @click="applyPreset(preset)">
                {{ preset.theme }}
              </button>
              <button class="preset-btn preset-btn--debate" @click="applyDebatePreset">
                放走蚂蚁 / 踩扁蚂蚁
              </button>
            </div>
          </div>

          <div v-if="mode === 'debate'" class="section debate-panel">
            <h2>正反方观点</h2>
            <div class="stance-grid">
              <label>
                <span>正方</span>
                <input v-model="proLabel" placeholder="例如：放走蚂蚁" />
              </label>
              <label>
                <span>反方</span>
                <input v-model="conLabel" placeholder="例如：踩扁蚂蚁" />
              </label>
            </div>
          </div>

          <div class="section">
            <h2>{{ mode === 'debate' ? '双方共用的方向叶子' : '思考方向' }}</h2>
            <p class="hint">
              {{ mode === 'debate' ? '这些方向会同时生成到正方和反方下面，后续还能继续往下延展。' : '设置一级方向节点，引导孩子从不同角度思考。' }}
            </p>

            <div class="directions-list">
              <div v-for="(dir, index) in activeDirections" :key="dir.id" class="direction-item">
                <select v-model="dir.emoji" class="emoji-select">
                  <option v-for="emoji in emojiOptions" :key="emoji" :value="emoji">{{ emoji }}</option>
                </select>

                <input
                  v-model="dir.name"
                  :placeholder="mode === 'debate' ? `方向 ${index + 1}：例如理由、后果、感受` : `方向 ${index + 1}：例如外形、生命`"
                  class="direction-input"
                />

                <button v-if="activeDirections.length > 1" class="remove-btn" @click="removeDirection(index)">×</button>
              </div>
            </div>

            <button v-if="activeDirections.length < 8" class="add-btn" @click="addDirection">＋ 添加方向</button>
          </div>
        </div>

        <div class="setup-footer">
          <button class="start-btn" :disabled="!canSubmit" @click="handleSubmit">
            🌱 开始创建思维树
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.setup-overlay {
  position: fixed;
  inset: 0;
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 50%, #a5d6a7 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}

.setup-card {
  background: rgba(255, 255, 245, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-radius: 22px;
  box-shadow: 0 24px 70px rgba(50, 62, 35, 0.2);
  max-width: 680px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.setup-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: scroll;
  overscroll-behavior: contain;
  scrollbar-width: thin;
  scrollbar-color: rgba(92, 122, 62, 0.42) rgba(237, 244, 213, 0.5);
}

.setup-scroll::-webkit-scrollbar {
  width: 10px;
}

.setup-scroll::-webkit-scrollbar-track {
  margin: 14px 6px 14px 0;
  background: rgba(237, 244, 213, 0.5);
  border-radius: 999px;
}

.setup-scroll::-webkit-scrollbar-thumb {
  background: rgba(92, 122, 62, 0.42);
  border-radius: 999px;
  border: 3px solid transparent;
  background-clip: padding-box;
}

.setup-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(92, 122, 62, 0.62);
  border: 3px solid transparent;
  background-clip: padding-box;
}

.setup-header {
  text-align: center;
  padding: 30px 30px 20px;
  background: linear-gradient(135deg, #759b46 0%, #2f6b3a 100%);
  border-radius: 22px 22px 0 0;
  color: white;
}

.setup-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
}

.setup-header p {
  margin: 0;
  opacity: 0.92;
  font-size: 14px;
}

.setup-body {
  padding: 28px 36px;
}

.section {
  margin-bottom: 28px;
}

.section h2 {
  margin: 0 0 8px;
  font-size: 18px;
  color: #2e4726;
}

.hint {
  margin: 0 0 12px;
  font-size: 13px;
  color: #68705c;
}

.mode-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  padding: 7px;
  border: 1px solid rgba(255, 255, 255, 0.48);
  border-radius: 999px;
  background: rgba(120, 139, 87, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.44);
}

.mode-tabs button {
  border: 0;
  border-radius: 999px;
  padding: 13px 16px;
  background: transparent;
  color: #415034;
  font-weight: 800;
  cursor: pointer;
}

.mode-tabs button.active {
  background: rgba(255, 255, 244, 0.94);
  box-shadow: 0 8px 18px rgba(55, 67, 38, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.theme-input,
.direction-input,
.stance-grid input {
  width: 100%;
  padding: 12px 14px;
  border: 2px solid rgba(117, 155, 70, 0.22);
  border-radius: 12px;
  font-size: 15px;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.88);
}

.theme-input:focus,
.direction-input:focus,
.stance-grid input:focus {
  outline: none;
  border-color: #8fbd47;
  box-shadow: 0 0 0 3px rgba(143, 189, 71, 0.18);
}

.presets {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.preset-btn {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid rgba(117, 155, 70, 0.2);
  border-radius: 20px;
  color: #405030;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.preset-btn:hover,
.preset-btn--debate {
  background: #eef5c4;
  border-color: #97bb4d;
}

.debate-panel {
  padding: 16px;
  border-radius: 18px;
  background: rgba(236, 242, 196, 0.58);
}

.stance-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stance-grid label {
  display: grid;
  gap: 6px;
  color: #2e3f28;
  font-size: 13px;
  font-weight: 800;
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
  width: 54px;
  padding: 10px;
  border: 2px solid rgba(117, 155, 70, 0.22);
  border-radius: 12px;
  font-size: 18px;
  background: white;
  cursor: pointer;
}

.remove-btn {
  width: 34px;
  height: 34px;
  background: #d86f55;
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
}

.add-btn {
  width: 100%;
  padding: 12px;
  background: rgba(227, 242, 253, 0.66);
  border: 2px dashed #8bbbd7;
  border-radius: 12px;
  color: #23617d;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  margin-top: 10px;
}

.setup-footer {
  padding: 0 36px 32px;
  text-align: center;
}

.start-btn {
  width: 100%;
  padding: 16px 32px;
  background: linear-gradient(135deg, #cce979 0%, #8fbd47 100%);
  color: #24341f;
  border: none;
  border-radius: 16px;
  font-size: 18px;
  font-weight: 900;
  cursor: pointer;
}

.start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .stance-grid,
  .mode-tabs {
    grid-template-columns: 1fr;
    border-radius: 18px;
  }
}
</style>
