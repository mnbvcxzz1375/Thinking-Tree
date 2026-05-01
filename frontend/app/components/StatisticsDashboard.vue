<template>
  <div class="stats-dashboard">
    <div class="dashboard-header">
      <h2 class="dashboard-title">
        <span class="dashboard-icon">📈</span>
        统计概览
      </h2>
      <button class="btn btn--outline btn--sm" @click="refreshOverview" :disabled="loading">
        <span v-if="loading" class="spinner"></span>
        <span v-else>刷新数据</span>
      </button>
    </div>

    <div v-if="error" class="dashboard-error">
      <span>⚠️</span> {{ error }}
    </div>

    <div v-if="overview" class="dashboard-content">
      <!-- Overview Cards -->
      <div class="overview-grid">
        <div class="overview-card overview-card--blue">
          <div class="overview-card__icon">📚</div>
          <div class="overview-card__data">
            <div class="overview-card__value">{{ overview.total_activities }}</div>
            <div class="overview-card__label">总活动数</div>
          </div>
        </div>
        <div class="overview-card overview-card--green">
          <div class="overview-card__icon">✅</div>
          <div class="overview-card__data">
            <div class="overview-card__value">{{ overview.active_activities }}</div>
            <div class="overview-card__label">进行中</div>
          </div>
        </div>
        <div class="overview-card overview-card--purple">
          <div class="overview-card__icon">🌳</div>
          <div class="overview-card__data">
            <div class="overview-card__value">{{ overview.total_nodes }}</div>
            <div class="overview-card__label">总节点数</div>
          </div>
        </div>
        <div class="overview-card overview-card--amber">
          <div class="overview-card__icon">🎙️</div>
          <div class="overview-card__data">
            <div class="overview-card__value">{{ overview.total_speech_records }}</div>
            <div class="overview-card__label">语音记录</div>
          </div>
        </div>
        <div class="overview-card overview-card--rose">
          <div class="overview-card__icon">👩‍🏫</div>
          <div class="overview-card__data">
            <div class="overview-card__value">{{ overview.total_reviews }}</div>
            <div class="overview-card__label">教师评价</div>
          </div>
        </div>
        <div class="overview-card overview-card--teal">
          <div class="overview-card__icon">📊</div>
          <div class="overview-card__data">
            <div class="overview-card__value">{{ overview.avg_nodes_per_activity }}</div>
            <div class="overview-card__label">平均节点/活动</div>
          </div>
        </div>
      </div>

      <!-- Recent Activities -->
      <div class="section">
        <h3 class="section-title">最近活动统计</h3>
        <div v-if="overview.recent_activities.length > 0" class="recent-list">
          <div
            v-for="activity in overview.recent_activities"
            :key="activity.activity_id"
            class="recent-item"
            @click="$emit('select-activity', activity.activity_id)"
          >
            <div class="recent-item__header">
              <h4 class="recent-item__title">{{ activity.activity_title }}</h4>
              <span class="recent-item__nodes">{{ activity.node_counts.total }} 节点</span>
            </div>
            <div class="recent-item__stats">
              <span class="recent-stat">
                <span class="recent-stat__icon">❓</span>
                {{ activity.node_counts.question }}
              </span>
              <span class="recent-stat">
                <span class="recent-stat__icon">💬</span>
                {{ activity.node_counts.answer }}
              </span>
              <span class="recent-stat">
                <span class="recent-stat__icon">💡</span>
                {{ activity.node_counts.insight }}
              </span>
              <span class="recent-stat">
                <span class="recent-stat__icon">📏</span>
                深度 {{ activity.max_depth }}
              </span>
            </div>
            <div class="recent-item__progress">
              <div class="progress-bar">
                <div
                  class="progress-bar__fill"
                  :style="{ width: Math.min(activity.participation_rate * 100, 100) + '%' }"
                ></div>
              </div>
              <span class="progress-label">
                参与率 {{ (activity.participation_rate * 100).toFixed(0) }}%
              </span>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          暂无活动数据
        </div>
      </div>

      <!-- Comparison Chart (ASCII-style bar chart) -->
      <div v-if="overview.recent_activities.length > 1" class="section">
        <h3 class="section-title">活动对比</h3>
        <div class="comparison-chart">
          <div
            v-for="activity in comparisonData"
            :key="activity.id"
            class="comparison-row"
          >
            <div class="comparison-label">{{ activity.name }}</div>
            <div class="comparison-bar-track">
              <div
                class="comparison-bar-fill"
                :style="{ width: activity.percentage + '%' }"
              ></div>
            </div>
            <div class="comparison-value">{{ activity.value }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!loading && !error" class="dashboard-empty">
      <p>点击"刷新数据"加载统计信息。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useStatisticsStore } from '~/stores/statistics'
import type { OverviewStats } from '~/stores/statistics'

const emit = defineEmits<{
  'select-activity': [id: number]
}>()

const statisticsStore = useStatisticsStore()

const loading = computed(() => statisticsStore.loading)
const error = computed(() => statisticsStore.error)
const overview = computed<OverviewStats | null>(() => statisticsStore.overview)

const comparisonData = computed(() => {
  if (!overview.value) return []
  const activities = overview.value.recent_activities
  if (activities.length === 0) return []

  const maxNodes = Math.max(...activities.map(a => a.node_counts.total), 1)

  return activities.map(a => ({
    id: a.activity_id,
    name: a.activity_title.length > 10 ? a.activity_title.slice(0, 10) + '...' : a.activity_title,
    value: a.node_counts.total,
    percentage: (a.node_counts.total / maxNodes) * 100,
  }))
})

async function refreshOverview() {
  await statisticsStore.fetchOverview()
}

onMounted(() => {
  if (!overview.value) {
    refreshOverview()
  }
})
</script>

<style scoped>
.stats-dashboard {
  padding: 1.5rem;
  max-width: 960px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.dashboard-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.dashboard-icon {
  font-size: 1.25rem;
}

.dashboard-error {
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

.dashboard-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: #6b7280;
}

/* Overview Grid */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.overview-card {
  background: #fff;
  border-radius: 0.75rem;
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  border: 1px solid #e5e7eb;
  transition: box-shadow 0.2s;
}

.overview-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.overview-card__icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.overview-card__value {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
}

.overview-card--blue .overview-card__value { color: #2563eb; }
.overview-card--green .overview-card__value { color: #16a34a; }
.overview-card--purple .overview-card__value { color: #7c3aed; }
.overview-card--amber .overview-card__value { color: #d97706; }
.overview-card--rose .overview-card__value { color: #e11d48; }
.overview-card--teal .overview-card__value { color: #0d9488; }

.overview-card__label {
  font-size: 0.8125rem;
  color: #6b7280;
  margin-top: 0.125rem;
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

/* Recent List */
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.recent-item {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 1rem 1.25rem;
  cursor: pointer;
  transition: all 0.15s;
}

.recent-item:hover {
  border-color: #93c5fd;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.recent-item__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.recent-item__title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  color: #1f2937;
}

.recent-item__nodes {
  font-size: 0.8125rem;
  background: #eff6ff;
  color: #2563eb;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
}

.recent-item__stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.recent-stat {
  font-size: 0.8125rem;
  color: #4b5563;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.recent-stat__icon {
  font-size: 0.75rem;
}

.recent-item__progress {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #f3f4f6;
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar__fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #10b981);
  border-radius: 3px;
  transition: width 0.6s ease;
}

.progress-label {
  font-size: 0.75rem;
  color: #6b7280;
  white-space: nowrap;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
  background: #f9fafb;
  border-radius: 0.5rem;
}

/* Comparison Chart */
.comparison-chart {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.comparison-row {
  display: grid;
  grid-template-columns: 100px 1fr 50px;
  align-items: center;
  gap: 0.75rem;
}

.comparison-label {
  font-size: 0.8125rem;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.comparison-bar-track {
  height: 12px;
  background: #f3f4f6;
  border-radius: 6px;
  overflow: hidden;
}

.comparison-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #818cf8, #6366f1);
  border-radius: 6px;
  transition: width 0.6s ease;
  min-width: 4px;
}

.comparison-value {
  font-size: 0.8125rem;
  font-weight: 600;
  color: #374151;
  text-align: right;
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
