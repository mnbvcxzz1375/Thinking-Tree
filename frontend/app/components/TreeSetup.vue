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
  { id: 'dir-1', name: '', emoji: '' },
  { id: 'dir-2', name: '', emoji: '' },
  { id: 'dir-3', name: '', emoji: '' },
])
const debateDirections = ref<Direction[]>([
  { id: 'debate-reason', name: '理由', emoji: '' },
  { id: 'debate-result', name: '后果', emoji: '' },
  { id: 'debate-feeling', name: '感受', emoji: '' },
  { id: 'debate-example', name: '例子', emoji: '' },
])

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
      emoji: '',
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
    emoji: '',
  }))
}

function applyDebatePreset() {
  mode.value = 'debate'
  theme.value = '放走蚂蚁 / 踩扁蚂蚁'
  proLabel.value = '放走蚂蚁'
  conLabel.value = '踩扁蚂蚁'
  debateDirections.value = [
    { id: 'reason', name: '理由', emoji: '' },
    { id: 'life', name: '生命', emoji: '' },
    { id: 'result', name: '后果', emoji: '' },
    { id: 'feeling', name: '感受', emoji: '' },
  ]
}
</script>

<template>
  <div class="setup-overlay">
    <div class="setup-card">
      <div class="setup-header">
        <h1>创建思维树</h1>
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
            开始创建思维树
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
  background:
    linear-gradient(180deg, rgba(65, 56, 102, 0.08) 0%, rgba(32, 28, 46, 0.16) 100%),
    url('/images/itw-night-bg.png') center center / cover no-repeat,
    #201c2e;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  z-index: 2000;
  padding: 96px 32px 32px;
  overflow: hidden;
}

.setup-overlay::before,
.setup-overlay::after {
  content: "";
  position: absolute;
  pointer-events: none;
}

.setup-overlay::before {
  inset: 0;
  background: rgba(18, 14, 28, 0.08);
}

.setup-overlay::after {
  display: none;
}

.setup-card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 242, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.36);
  border-radius: 30px;
  box-shadow: 0 24px 70px rgba(34, 42, 26, 0.18);
  backdrop-filter: blur(18px);
  max-width: 920px;
  width: 100%;
  max-height: calc(100vh - 128px);
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
  text-align: left;
  padding: 34px 42px 22px;
  background: transparent;
  color: #24301d;
}

.setup-header h1 {
  margin: 0 0 8px;
  font-size: 30px;
  font-weight: 900;
}

.setup-header p {
  margin: 0;
  color: rgba(45, 54, 35, 0.72);
  font-size: 15px;
}

.setup-body {
  margin: 0 42px 22px;
  padding: 28px 32px;
  border: 1px solid rgba(255, 255, 255, 0.42);
  border-radius: 24px;
  background: rgba(255, 255, 242, 0.88);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.52), 0 14px 34px rgba(46, 54, 32, 0.1);
  backdrop-filter: blur(14px);
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
  padding: 6px;
  border: 1px solid rgba(255, 255, 255, 0.38);
  border-radius: 999px;
  background: rgba(74, 78, 61, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3), 0 16px 30px rgba(43, 50, 34, 0.12);
  backdrop-filter: blur(18px);
}

.mode-tabs button {
  border: 0;
  border-radius: 999px;
  min-height: 44px;
  padding: 0 16px;
  background: transparent;
  color: rgba(43, 58, 33, 0.72);
  font-size: 15px;
  font-weight: 900;
  cursor: pointer;
}

.mode-tabs button.active {
  background: rgba(255, 255, 244, 0.96);
  color: #24341f;
  box-shadow: 0 12px 24px rgba(55, 67, 38, 0.16), inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.theme-input,
.direction-input,
.stance-grid input {
  width: 100%;
  min-height: 52px;
  padding: 0 18px;
  border: 1px solid rgba(96, 113, 68, 0.2);
  border-radius: 18px;
  font-size: 16px;
  transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.76), 0 8px 18px rgba(43, 50, 34, 0.05);
  color: #283520;
}

.theme-input:focus,
.direction-input:focus,
.stance-grid input:focus {
  outline: none;
  border-color: rgba(143, 189, 71, 0.72);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 0 0 4px rgba(143, 189, 71, 0.16), inset 0 1px 0 rgba(255, 255, 255, 0.84);
}

.presets {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.preset-btn {
  min-height: 42px;
  padding: 0 18px;
  background: rgba(255, 255, 245, 0.78);
  border: 1px solid rgba(117, 155, 70, 0.22);
  border-radius: 20px;
  color: #405030;
  font-size: 15px;
  font-weight: 900;
  cursor: pointer;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.64), 0 8px 18px rgba(43, 50, 34, 0.06);
}

.preset-btn:hover,
.preset-btn--debate {
  background: rgba(238, 245, 196, 0.88);
  border-color: rgba(151, 187, 77, 0.8);
}

.debate-panel {
  padding: 16px;
  border-radius: 18px;
  background: rgba(236, 242, 196, 0.52);
  border: 1px solid rgba(255, 255, 255, 0.36);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.44);
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

.remove-btn {
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  background: linear-gradient(180deg, rgba(225, 125, 99, 0.95) 0%, rgba(206, 96, 73, 0.96) 100%);
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35), 0 10px 20px rgba(142, 64, 45, 0.16);
}

.add-btn {
  width: 100%;
  min-height: 52px;
  padding: 0 16px;
  background: rgba(227, 242, 253, 0.5);
  border: 2px dashed rgba(139, 187, 215, 0.78);
  border-radius: 18px;
  color: #23617d;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
  margin-top: 10px;
}

.setup-footer {
  padding: 0 42px 34px;
  text-align: center;
}

.start-btn {
  width: 100%;
  min-height: 58px;
  padding: 0 32px;
  background: linear-gradient(180deg, #dceea2 0%, #a8ca58 100%);
  color: #24341f;
  border: none;
  border-radius: 20px;
  font-size: 18px;
  font-weight: 900;
  cursor: pointer;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.48), 0 14px 26px rgba(28, 37, 22, 0.12);
}

.start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 640px) {
  .setup-overlay {
    padding: 92px 14px 18px;
  }

  .setup-card {
    max-height: calc(100vh - 110px);
    border-radius: 24px;
  }

  .setup-header {
    padding: 24px 22px 16px;
  }

  .setup-body {
    margin: 0 18px 18px;
    padding: 22px 18px;
  }

  .setup-footer {
    padding: 0 18px 24px;
  }

  .stance-grid,
  .mode-tabs {
    grid-template-columns: 1fr;
    border-radius: 18px;
  }
}
</style>
