<template>
  <div class="activity-list">
    <div v-if="loading" class="activity-list__loading">
      <div class="spinner" />
      <span>加载中...</span>
    </div>

    <div v-else-if="error" class="activity-list__error">
      <p>{{ error }}</p>
      <button class="btn btn--outline btn--sm" @click="$emit('retry')">重试</button>
    </div>

    <div v-else-if="activities.length === 0" class="activity-list__empty">
      <p class="activity-list__empty-title">暂无活动</p>
      <p class="activity-list__empty-copy">创建一个活动后，就可以按主题组织孩子的想法。</p>
      <NuxtLink to="/activities/create" class="btn btn--primary btn--sm">
        创建第一个活动
      </NuxtLink>
    </div>

    <div v-else class="activity-list__grid">
      <ActivityCard
        v-for="activity in activities"
        :key="activity.id"
        :activity="activity"
        @delete="$emit('delete', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Activity } from '~/stores/activity'

interface Props {
  activities: Activity[]
  loading?: boolean
  error?: string | null
}

withDefaults(defineProps<Props>(), {
  loading: false,
  error: null,
})

defineEmits<{
  delete: [id: number]
  retry: []
}>()
</script>

<style scoped>
.activity-list {
  min-height: 200px;
}
.activity-list__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3rem 0;
  color: #6b7280;
}
.spinner {
  width: 1.25rem;
  height: 1.25rem;
  border: 2px solid #e5e7eb;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.activity-list__error {
  text-align: center;
  padding: 3rem 0;
  color: #dc2626;
}
.activity-list__error .btn {
  margin-top: 0.75rem;
}
.activity-list__empty {
  text-align: center;
  display: grid;
  justify-items: center;
  gap: 0.55rem;
  padding: 4.5rem 1.5rem;
  color: rgba(45, 54, 35, 0.72);
}

.activity-list__empty-title {
  margin: 0;
  color: #26311f;
  font-size: 1.15rem;
  font-weight: 900;
}

.activity-list__empty-copy {
  max-width: 360px;
  margin: 0;
  line-height: 1.7;
}
.activity-list__empty .btn {
  margin-top: 0.7rem;
}
.activity-list__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
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
  text-decoration: none;
  border: 1px solid transparent;
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
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}
.btn--primary:hover {
  background: #1d4ed8;
}

/* Mobile responsive */
@media (max-width: 640px) {
  .activity-list__grid {
    grid-template-columns: 1fr;
  }
}
</style>
