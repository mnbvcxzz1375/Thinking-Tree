<template>
  <div class="activity-review">
    <div class="review-header">
      <h2 class="review-title">
        <span class="review-icon">📊</span>
        活动回顾
      </h2>
      <div class="review-actions">
        <button class="btn btn--outline btn--sm" @click="refreshStats" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span v-else>刷新</span>
        </button>
        <button class="btn btn--outline btn--sm" @click="exportJSON">
          导出 JSON
        </button>
        <button class="btn btn--outline btn--sm" @click="exportCSV">
          导出 CSV
        </button>
      </div>
    </div>

    <div v-if="error" class="review-error">
      <span>⚠️</span> {{ error }}
    </div>

    <div v-if="stats" class="review-content">
      <!-- Summary Cards -->
      <div class="stats-grid">
        <div class="stat-card stat-card--primary">
          <div class="stat-value">{{ stats.node_counts.total }}</div>
          <div class="stat-label">总节点数</div>
        </div>
        <div class="stat-card stat-card--depth">
          <div class="stat-value">{{ stats.max_depth }}</div>
          <div class="stat-label">最大深度</div>
        </div>
        <div class="stat-card stat-card--speech">
          <div class="stat-value">{{ stats.total_speech_records }}</div>
          <div class="stat-label">语音互动</div>
        </div>
        <div class="stat-card stat-card--review">
          <div class="stat-value">{{ stats.total_reviews }}</div>
          <div class="stat-label">教师评价</div>
        </div>
      </div>

      <!-- Node Type Breakdown -->
      <div class="section">
        <h3 class="section-title">节点类型分布</h3>
        <div class="type-bars">
          <div class="type-bar" v-for="(item, index) in nodeTypeData" :key="index">
            <div class="type-bar__label">
              <span class="type-bar__icon">{{ item.icon }}</span>
              <span>{{ item.label }}</span>
            </div>
            <div class="type-bar__track">
              <div
                class="type-bar__fill"
                :style="{ width: item.percentage + '%', backgroundColor: item.color }"
              ></div>
            </div>
            <div class="type-bar__value">{{ item.count }}</div>
          </div>
        </div>
      </div>

      <!-- Participation & Depth -->
      <div class="section-row">
        <div class="section">
          <h3 class="section-title">参与度</h3>
          <div class="progress-ring-container">
            <svg class="progress-ring" viewBox="0 0 120 120">
              <circle
                class="progress-ring__bg"
                cx="60" cy="60" r="50"
                fill="none" stroke="#e5e7eb" stroke-width="10"
              />
              <circle
                class="progress-ring__fill"
                cx="60" cy="60" r="50"
                fill="none"
                :stroke="participationColor"
                stroke-width="10"
                stroke-linecap="round"
                :stroke-dasharray="circumference"
                :stroke-dashoffset="participationOffset"
              />
            </svg>
            <div class="progress-ring__text">
              {{ (stats.participation_rate * 100).toFixed(0) }}%
            </div>
          </div>
        </div>

        <div class="section">
          <h3 class="section-title">深度信息</h3>
          <div class="depth-info">
            <div class="depth-item">
              <span class="depth-label">最大深度</span>
              <span class="depth-value">{{ stats.max_depth }} 层</span>
            </div>
            <div class="depth-item">
              <span class="depth-label">平均深度</span>
              <span class="depth-value">{{ stats.avg_depth }} 层</span>
            </div>
            <div class="depth-visual">
              <div
                v-for="i in Math.min(stats.max_depth, 8)"
                :key="i"
                class="depth-level"
                :style="{ marginLeft: (i - 1) * 20 + 'px', opacity: 1 - (i - 1) * 0.1 }"
              >
                <span class="depth-level__dot"></span>
                <span class="depth-level__line"></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Insights -->
      <div v-if="insights && insights.insights.length > 0" class="section">
        <h3 class="section-title">💡 洞察分析</h3>
        <div class="insights-list">
          <div
            v-for="(insight, index) in insights.insights"
            :key="index"
            class="insight-card"
            :class="'insight-card--' + insight.severity"
          >
            <div class="insight-header">
              <span class="insight-icon">{{ insightIcon(insight.severity) }}</span>
              <span class="insight-title">{{ insight.title }}</span>
            </div>
            <p class="insight-desc">{{ insight.description }}</p>
          </div>
        </div>
        <div v-if="insights.summary" class="insight-summary">
          <strong>总结：</strong>{{ insights.summary }}
        </div>
      </div>

      <!-- Most Active Branches -->
      <div v-if="stats.most_active_branches.length > 0" class="section">
        <h3 class="section-title">🌳 最活跃分支</h3>
        <div class="branches-list">
          <div
            v-for="branch in stats.most_active_branches"
            :key="branch.node_id"
            class="branch-item"
          >
            <div class="branch-content">{{ branch.content }}</div>
            <div class="branch-meta">
              <span class="branch-badge">{{ branch.node_count }} 节点</span>
              <span class="branch-badge">深度 {{ branch.depth }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!loading && !error" class="review-empty">
      <p>暂无统计数据，请选择一个活动查看。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useStatisticsStore } from '~/stores/statistics'
import type { ActivityStats, ActivityInsights } from '~/stores/statistics'

interface Props {
  activityId: number
}

const props = defineProps<Props>()

const statisticsStore = useStatisticsStore()

const loading = computed(() => statisticsStore.loading)
const error = computed(() => statisticsStore.error)
const stats = computed<ActivityStats | null>(() => statisticsStore.getActivityStats(props.activityId))
const insights = computed<ActivityInsights | null>(() => statisticsStore.getActivityInsights(props.activityId))

const circumference = 2 * Math.PI * 50 // r=50

const participationOffset = computed(() => {
  const rate = stats.value?.participation_rate ?? 0
  return circumference * (1 - rate)
})

const participationColor = computed(() => {
  const rate = stats.value?.participation_rate ?? 0
  if (rate >= 0.7) return '#10b981'
  if (rate >= 0.3) return '#f59e0b'
  return '#ef4444'
})

interface NodeTypeDatum {
  label: string
  icon: string
  count: number
  percentage: number
  color: string
}

const nodeTypeData = computed<NodeTypeDatum[]>(() => {
  if (!stats.value) return []
  const nc = stats.value.node_counts
  const total = nc.total || 1
  return [
    { label: '问题', icon: '❓', count: nc.question, percentage: (nc.question / total) * 100, color: '#3b82f6' },
    { label: '回答', icon: '💬', count: nc.answer, percentage: (nc.answer / total) * 100, color: '#10b981' },
    { label: '洞察', icon: '💡', count: nc.insight, percentage: (nc.insight / total) * 100, color: '#f59e0b' },
    { label: '根节点', icon: '🌳', count: nc.root, percentage: (nc.root / total) * 100, color: '#8b5cf6' },
    { label: '分支', icon: '🌿', count: nc.branch, percentage: (nc.branch / total) * 100, color: '#ec4899' },
  ].filter(d => d.count > 0)
})

function insightIcon(severity: string): string {
  switch (severity) {
    case 'success': return '✅'
    case 'warning': return '⚠️'
    default: return 'ℹ️'
  }
}

async function refreshStats() {
  await Promise.all([
    statisticsStore.fetchActivityStats(props.activityId),
    statisticsStore.fetchActivityInsights(props.activityId),
  ])
}

function exportJSON() {
  statisticsStore.downloadReport(props.activityId, 'json')
}

function exportCSV() {
  statisticsStore.downloadReport(props.activityId, 'csv')
}

onMounted(() => {
  if (!stats.value) {
    refreshStats()
  }
})
</script>

<style scoped>
.activity-review {
  padding: 1.5rem;
  max-width: 960px;
  margin: 0 auto;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.review-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.review-icon {
  font-size: 1.25rem;
}

.review-actions {
  display: flex;
  gap: 0.5rem;
}

.review-error {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #991b1b;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.review-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: #6b7280;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: #fff;
  border-radius: 0.75rem;
  padding: 1.25rem;
  text-align: center;
  border: 1px solid #e5e7eb;
  transition: box-shadow 0.2s;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.stat-card--primary .stat-value { color: #2563eb; }
.stat-card--depth .stat-value { color: #8b5cf6; }
.stat-card--speech .stat-value { color: #10b981; }
.stat-card--review .stat-value { color: #f59e0b; }

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
}

/* Sections */
.section {
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 1rem;
  color: #1f2937;
}

.section-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

@media (max-width: 640px) {
  .section-row {
    grid-template-columns: 1fr;
  }
}

/* Type Bars */
.type-bars {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.type-bar {
  display: grid;
  grid-template-columns: 100px 1fr 50px;
  align-items: center;
  gap: 0.75rem;
}

.type-bar__label {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.875rem;
  color: #374151;
}

.type-bar__icon {
  font-size: 1rem;
}

.type-bar__track {
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.type-bar__fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

.type-bar__value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  text-align: right;
}

/* Progress Ring */
.progress-ring-container {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto;
}

.progress-ring {
  transform: rotate(-90deg);
  width: 100%;
  height: 100%;
}

.progress-ring__fill {
  transition: stroke-dashoffset 0.6s ease;
}

.progress-ring__text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
}

/* Depth Info */
.depth-info {
  background: #f9fafb;
  border-radius: 0.5rem;
  padding: 1rem;
}

.depth-item {
  display: flex;
  justify-content: space-between;
  padding: 0.375rem 0;
}

.depth-label {
  color: #6b7280;
  font-size: 0.875rem;
}

.depth-value {
  font-weight: 600;
  color: #1f2937;
  font-size: 0.875rem;
}

.depth-visual {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e5e7eb;
}

.depth-level {
  display: flex;
  align-items: center;
  height: 20px;
}

.depth-level__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #8b5cf6;
  flex-shrink: 0;
}

.depth-level__line {
  flex: 1;
  height: 2px;
  background: #d8b4fe;
  margin-left: 4px;
}

/* Insights */
.insights-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.insight-card {
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid;
}

.insight-card--info {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.insight-card--success {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.insight-card--warning {
  background: #fffbeb;
  border-color: #fde68a;
}

.insight-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.375rem;
}

.insight-icon {
  font-size: 1rem;
}

.insight-title {
  font-weight: 600;
  font-size: 0.9375rem;
  color: #1f2937;
}

.insight-desc {
  margin: 0;
  font-size: 0.875rem;
  color: #4b5563;
  line-height: 1.5;
}

.insight-summary {
  margin-top: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: #374151;
  line-height: 1.6;
}

/* Branches */
.branches-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.branch-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  gap: 1rem;
}

.branch-content {
  font-size: 0.875rem;
  color: #374151;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.branch-meta {
  display: flex;
  gap: 0.375rem;
  flex-shrink: 0;
}

.branch-badge {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  background: #e0e7ff;
  color: #4338ca;
  border-radius: 9999px;
  white-space: nowrap;
}

/* Button styles */
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
  background: none;
}

.btn--sm {
  padding: 0.25rem 0.625rem;
  font-size: 0.8125rem;
}

.btn--outline {
  background: #fff;
  border-color: #d1d5db;
  color: #374151;
}

.btn--outline:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #9ca3af;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #d1d5db;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
