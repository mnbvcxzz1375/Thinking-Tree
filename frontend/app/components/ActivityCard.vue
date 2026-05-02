<template>
  <div class="activity-card" :class="{ 'activity-card--inactive': !activity.is_active }">
    <div class="activity-card__header">
      <h3 class="activity-card__title">
        <NuxtLink :to="`/activities/${activity.id}`">
          {{ activity.title }}
        </NuxtLink>
      </h3>
      <span class="activity-card__badge" :class="difficultyClass">
        {{ difficultyLabel }}
      </span>
      <span class="activity-card__badge activity-card__badge--mode">
        {{ activity.activity_mode === 'debate' ? '辩论' : '普通' }}
      </span>
    </div>

    <p v-if="activity.description" class="activity-card__desc">
      {{ activity.description }}
    </p>

    <div class="activity-card__meta">
      <span v-if="activity.age_group" class="activity-card__tag">
        {{ activity.age_group }}
      </span>
      <span v-if="activity.activity_mode === 'debate'" class="activity-card__tag activity-card__tag--debate">
        正：{{ activity.debate_pro_label }} / 反：{{ activity.debate_con_label }}
      </span>
      <span v-if="!activity.is_active" class="activity-card__tag activity-card__tag--inactive">
        已停用
      </span>
      <span class="activity-card__date">
        {{ formatDate(activity.created_at) }}
      </span>
    </div>

    <div class="activity-card__actions">
      <NuxtLink :to="`/activities/${activity.id}`" class="btn btn--sm btn--outline">
        查看
      </NuxtLink>
      <NuxtLink :to="`/activities/${activity.id}/edit`" class="btn btn--sm btn--primary">
        编辑
      </NuxtLink>
      <button class="btn btn--sm btn--danger" @click="$emit('delete', activity.id)">
        删除
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Activity } from '~/stores/activity'

interface Props {
  activity: Activity
}

const props = defineProps<Props>()

defineEmits<{
  delete: [id: number]
}>()

const difficultyLabels: Record<string, string> = {
  easy: '简单',
  medium: '中等',
  hard: '困难',
}

const difficultyLabel = computed(() => difficultyLabels[props.activity.difficulty_level] || props.activity.difficulty_level)

const difficultyClass = computed(() => `activity-card__badge--${props.activity.difficulty_level}`)

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}
</script>

<style scoped>
.activity-card {
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 1.25rem;
  background: #fff;
  transition: box-shadow 0.2s;
}
.activity-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.activity-card--inactive {
  opacity: 0.7;
}
.activity-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
}
.activity-card__title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}
.activity-card__title a {
  color: #111827;
  text-decoration: none;
}
.activity-card__title a:hover {
  color: #2563eb;
}
.activity-card__badge {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-weight: 500;
  white-space: nowrap;
}
.activity-card__badge--easy {
  background: #d1fae5;
  color: #065f46;
}
.activity-card__badge--medium {
  background: #fef3c7;
  color: #92400e;
}
.activity-card__badge--hard {
  background: #fee2e2;
  color: #991b1b;
}
.activity-card__badge--mode {
  background: #edf6d0;
  color: #314325;
}
.activity-card__desc {
  color: #6b7280;
  font-size: 0.875rem;
  margin: 0.75rem 0 0;
  line-height: 1.5;
}
.activity-card__meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  flex-wrap: wrap;
}
.activity-card__tag {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  background: #f3f4f6;
  color: #4b5563;
}
.activity-card__tag--inactive {
  background: #fee2e2;
  color: #991b1b;
}
.activity-card__tag--debate {
  background: #fff5d6;
  color: #5b4a1f;
}
.activity-card__date {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-left: auto;
}
.activity-card__actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f3f4f6;
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
.btn--danger {
  background: #fff;
  color: #dc2626;
  border-color: #fca5a5;
}
.btn--danger:hover {
  background: #fef2f2;
  border-color: #f87171;
}

/* Mobile responsive */
@media (max-width: 640px) {
  .activity-card {
    padding: 1rem;
  }
  .activity-card__header {
    flex-direction: column;
    gap: 0.5rem;
  }
  .activity-card__title {
    font-size: 1rem;
  }
  .activity-card__meta {
    flex-wrap: wrap;
  }
  .activity-card__actions {
    flex-wrap: wrap;
  }
  .activity-card__actions .btn {
    flex: 1;
    min-width: 0;
    justify-content: center;
  }
}
</style>
