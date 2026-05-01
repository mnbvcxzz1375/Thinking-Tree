<template>
  <div class="timeline-view">
    <div class="timeline-header">
      <h3 class="timeline-title">
        <span class="timeline-icon">📅</span>
        活动时间线
      </h3>
      <div class="timeline-controls">
        <button
          class="btn btn--sm"
          :class="viewMode === 'daily' ? 'btn--primary' : 'btn--outline'"
          @click="viewMode = 'daily'"
        >
          日视图
        </button>
        <button
          class="btn btn--sm"
          :class="viewMode === 'weekly' ? 'btn--primary' : 'btn--outline'"
          @click="viewMode = 'weekly'"
        >
          周视图
        </button>
      </div>
    </div>

    <div v-if="timeData.length > 0" class="timeline-content">
      <!-- Chart Area -->
      <div class="chart-container">
        <div class="chart-y-axis">
          <span v-for="tick in yTicks" :key="tick" class="chart-tick">{{ tick }}</span>
        </div>
        <div class="chart-bars">
          <div
            v-for="(item, index) in displayData"
            :key="index"
            class="chart-bar-group"
            :title="`${item.label}: ${item.value} 个节点`"
          >
            <div
              class="chart-bar"
              :style="{ height: barHeight(item.value) + '%' }"
              :class="{ 'chart-bar--today': item.isToday }"
            ></div>
            <span class="chart-bar-label" :class="{ 'chart-bar-label--today': item.isToday }">
              {{ item.shortLabel }}
            </span>
          </div>
        </div>
      </div>

      <!-- Summary -->
      <div class="timeline-summary">
        <div class="summary-item">
          <span class="summary-label">总节点</span>
          <span class="summary-value">{{ totalCreated }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">活跃天数</span>
          <span class="summary-value">{{ activeDays }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">日均节点</span>
          <span class="summary-value">{{ avgPerDay }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">最活跃</span>
          <span class="summary-value">{{ peakDay }}</span>
        </div>
      </div>

      <!-- Daily Detail List -->
      <div class="timeline-list">
        <div
          v-for="(item, index) in sortedData"
          :key="index"
          class="timeline-item"
          :class="{ 'timeline-item--today': isToday(item.date) }"
        >
          <div class="timeline-dot-container">
            <div class="timeline-dot" :class="{ 'timeline-dot--active': item.count > 0 }"></div>
            <div v-if="index < sortedData.length - 1" class="timeline-line"></div>
          </div>
          <div class="timeline-item__content">
            <div class="timeline-item__header">
              <span class="timeline-item__date">{{ formatDate(item.date) }}</span>
              <span class="timeline-item__count">{{ item.count }} 个节点</span>
            </div>
            <div v-if="item.count > 0" class="timeline-item__bar">
              <div
                class="timeline-item__fill"
                :style="{ width: (item.count / maxCount * 100) + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="timeline-empty">
      <p>暂无时间分布数据。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { TimeDistribution } from '~/stores/statistics'

interface Props {
  timeData: TimeDistribution[]
}

const props = defineProps<Props>()

const viewMode = ref<'daily' | 'weekly'>('daily')

interface DisplayItem {
  label: string
  shortLabel: string
  value: number
  isToday: boolean
}

const sortedData = computed(() => {
  return [...props.timeData].sort((a, b) => b.date.localeCompare(a.date))
})

const maxCount = computed(() => {
  return Math.max(...props.timeData.map(d => d.count), 1)
})

const totalCreated = computed(() => {
  return props.timeData.reduce((sum, d) => sum + d.count, 0)
})

const activeDays = computed(() => {
  return props.timeData.filter(d => d.count > 0).length
})

const avgPerDay = computed(() => {
  if (props.timeData.length === 0) return '0'
  return (totalCreated.value / props.timeData.length).toFixed(1)
})

const peakDay = computed(() => {
  if (props.timeData.length === 0) return '-'
  const peak = props.timeData.reduce((max, d) => d.count > max.count ? d : max, props.timeData[0])
  return formatDateShort(peak.date)
})

// Aggregate by week if in weekly view
const displayData = computed<DisplayItem[]>(() => {
  const today = new Date().toISOString().split('T')[0]

  if (viewMode.value === 'daily') {
    // Show last 14 days
    const recent = sortedData.value.slice(0, 14).reverse()
    return recent.map(d => ({
      label: d.date,
      shortLabel: d.date.slice(5), // MM-DD
      value: d.count,
      isToday: d.date === today,
    }))
  }

  // Weekly aggregation
  const weekMap = new Map<string, number>()
  for (const d of props.timeData) {
    const date = new Date(d.date)
    const weekStart = new Date(date)
    weekStart.setDate(date.getDate() - date.getDay())
    const key = weekStart.toISOString().split('T')[0]
    weekMap.set(key, (weekMap.get(key) ?? 0) + d.count)
  }

  const weeks = Array.from(weekMap.entries())
    .sort((a, b) => b[0].localeCompare(a[0]))
    .slice(0, 8)
    .reverse()

  return weeks.map(([week, count]) => ({
    label: week,
    shortLabel: week.slice(5),
    value: count,
    isToday: false,
  }))
})

const yTicks = computed(() => {
  const max = Math.max(...displayData.value.map(d => d.value), 1)
  const step = Math.ceil(max / 4)
  return [step * 4, step * 3, step * 2, step, 0]
})

function barHeight(value: number): number {
  const max = Math.max(...displayData.value.map(d => d.value), 1)
  return (value / max) * 100
}

function isToday(dateStr: string): boolean {
  return dateStr === new Date().toISOString().split('T')[0]
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  })
}

function formatDateShort(dateStr: string): string {
  return dateStr.slice(5) // MM-DD
}
</script>

<style scoped>
.timeline-view {
  padding: 1.5rem;
  max-width: 960px;
  margin: 0 auto;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.timeline-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.timeline-icon {
  font-size: 1.125rem;
}

.timeline-controls {
  display: flex;
  gap: 0.375rem;
}

.timeline-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: #6b7280;
}

/* Chart */
.chart-container {
  display: flex;
  gap: 0.5rem;
  height: 200px;
  margin-bottom: 1.5rem;
  padding-bottom: 2rem;
  position: relative;
}

.chart-y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 30px;
  text-align: right;
}

.chart-tick {
  font-size: 0.6875rem;
  color: #9ca3af;
}

.chart-bars {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: 4px;
  border-left: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
  padding: 0 4px;
}

.chart-bar-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  justify-content: flex-end;
}

.chart-bar {
  width: 100%;
  max-width: 40px;
  background: linear-gradient(180deg, #818cf8, #6366f1);
  border-radius: 4px 4px 0 0;
  transition: height 0.4s ease;
  min-height: 2px;
}

.chart-bar--today {
  background: linear-gradient(180deg, #34d399, #10b981);
}

.chart-bar-label {
  font-size: 0.625rem;
  color: #9ca3af;
  margin-top: 0.375rem;
  white-space: nowrap;
}

.chart-bar-label--today {
  color: #10b981;
  font-weight: 600;
}

/* Summary */
.timeline-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.summary-item {
  background: #f9fafb;
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
  text-align: center;
}

.summary-label {
  display: block;
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.summary-value {
  display: block;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
}

/* Timeline List */
.timeline-list {
  display: flex;
  flex-direction: column;
}

.timeline-item {
  display: flex;
  gap: 1rem;
  min-height: 48px;
}

.timeline-item--today {
  background: #f0fdf4;
  border-radius: 0.5rem;
  margin: -0.25rem -0.5rem;
  padding: 0.25rem 0.5rem;
}

.timeline-dot-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 16px;
  flex-shrink: 0;
}

.timeline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #d1d5db;
  flex-shrink: 0;
  margin-top: 6px;
}

.timeline-dot--active {
  background: #6366f1;
}

.timeline-line {
  width: 2px;
  flex: 1;
  background: #e5e7eb;
  margin-top: 4px;
}

.timeline-item__content {
  flex: 1;
  padding-bottom: 0.75rem;
}

.timeline-item__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.375rem;
}

.timeline-item__date {
  font-size: 0.875rem;
  color: #374151;
}

.timeline-item__count {
  font-size: 0.75rem;
  color: #6b7280;
  background: #f3f4f6;
  padding: 0.0625rem 0.375rem;
  border-radius: 9999px;
}

.timeline-item__bar {
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
}

.timeline-item__fill {
  height: 100%;
  background: #818cf8;
  border-radius: 2px;
  transition: width 0.4s ease;
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

.btn--outline:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.btn--primary {
  background: #6366f1;
  color: #fff;
  border-color: #6366f1;
}

.btn--primary:hover {
  background: #4f46e5;
}
</style>
