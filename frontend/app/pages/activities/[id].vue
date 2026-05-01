<template>
  <div class="page-detail">
    <div class="page-header">
      <NuxtLink to="/activities" class="back-link">← 返回活动列表</NuxtLink>
    </div>

    <div v-if="store.loading && !activity" class="page-loading">
      <div class="spinner" />
      <span>加载中...</span>
    </div>

    <div v-else-if="!activity" class="page-error">
      <h2>活动未找到</h2>
      <p>请求的活动不存在或已被删除。</p>
      <NuxtLink to="/activities" class="btn btn--primary">返回活动列表</NuxtLink>
    </div>

    <template v-else>
      <div class="detail-header">
        <div class="detail-header__main">
          <h1>{{ activity.title }}</h1>
          <div class="detail-badges">
            <span class="badge" :class="`badge--${activity.difficulty_level}`">
              {{ difficultyLabel }}
            </span>
            <span v-if="activity.age_group" class="badge badge--outline">
              {{ activity.age_group }}
            </span>
            <span class="badge badge--mode">
              {{ activity.activity_mode === 'debate' ? '辩论模式' : '普通思维树' }}
            </span>
            <span v-if="!activity.is_active" class="badge badge--inactive">已停用</span>
          </div>
        </div>
        <div class="detail-header__actions">
          <NuxtLink :to="`/activities/${activity.id}/edit`" class="btn btn--primary">
            编辑
          </NuxtLink>
          <button class="btn btn--danger" @click="handleDelete">删除</button>
        </div>
      </div>

      <div class="detail-sections">
        <div v-if="activity.description" class="detail-section">
          <h3>活动描述</h3>
          <p>{{ activity.description }}</p>
        </div>

        <div v-if="activity.instructions" class="detail-section">
          <h3>活动指导</h3>
          <p class="pre-wrap">{{ activity.instructions }}</p>
        </div>

        <div v-if="activity.activity_mode === 'debate'" class="detail-section">
          <h3>辩论设置</h3>
          <dl class="detail-meta">
            <dt>正方</dt>
            <dd>{{ activity.debate_pro_label }}</dd>
            <dt>反方</dt>
            <dd>{{ activity.debate_con_label }}</dd>
          </dl>
        </div>

        <div class="detail-section">
          <h3>基本信息</h3>
          <dl class="detail-meta">
            <dt>创建时间</dt>
            <dd>{{ formatDateTime(activity.created_at) }}</dd>
            <dt>更新时间</dt>
            <dd>{{ formatDateTime(activity.updated_at) }}</dd>
            <dt>状态</dt>
            <dd>{{ activity.is_active ? '已启用' : '已停用' }}</dd>
          </dl>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { useActivityStore } from '~/stores/activity'
import { useTreeStore } from '~/stores/tree'

const route = useRoute()
const router = useRouter()
const store = useActivityStore()
const treeStore = useTreeStore()

const activityId = computed(() => Number(route.params.id))

const activity = computed(() => store.currentActivity)

watch(activity, (current) => {
  if (!current) return
  treeStore.setActivityContext({
    activityId: current.id,
    title: current.title,
    description: current.description,
    instructions: current.instructions,
    activityMode: current.activity_mode,
    debateProLabel: current.debate_pro_label,
    debateConLabel: current.debate_con_label,
  })
}, { immediate: true })

const difficultyLabels: Record<string, string> = {
  easy: '简单',
  medium: '中等',
  hard: '困难',
}

const difficultyLabel = computed(() => {
  if (!activity.value) return ''
  return difficultyLabels[activity.value.difficulty_level] || activity.value.difficulty_level
})

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function handleDelete() {
  if (!confirm('确定要删除此活动吗？此操作不可撤销。')) return
  const success = await store.deleteActivity(activityId.value)
  if (success) {
    router.push('/activities')
  }
}

useHead({
  title: computed(() => activity.value ? `${activity.value.title} - 儿童思维树` : '活动详情 - 儿童思维树'),
})

// Fetch activity on mount
onMounted(() => {
  store.fetchActivity(activityId.value)
})

// Refetch if route changes
watch(activityId, (newId) => {
  if (newId) {
    store.fetchActivity(newId)
  }
})
</script>

<style scoped>
.page-detail {
  max-width: 800px;
  margin: 0 auto;
}
.page-header {
  margin-bottom: 1.5rem;
}
.back-link {
  font-size: 0.875rem;
  color: #2563eb;
  text-decoration: none;
}
.back-link:hover {
  text-decoration: underline;
}
.page-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 4rem 0;
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
.page-error {
  text-align: center;
  padding: 4rem 0;
  color: #6b7280;
}
.page-error h2 {
  color: #111827;
  margin: 0 0 0.5rem;
}
.page-error .btn {
  margin-top: 1.5rem;
}
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 2rem;
}
.detail-header__main h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 0.75rem;
}
.detail-badges {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-weight: 500;
}
.badge--easy {
  background: #d1fae5;
  color: #065f46;
}
.badge--medium {
  background: #fef3c7;
  color: #92400e;
}
.badge--hard {
  background: #fee2e2;
  color: #991b1b;
}
.badge--outline {
  background: #fff;
  border: 1px solid #d1d5db;
  color: #374151;
}
.badge--inactive {
  background: #fee2e2;
  color: #991b1b;
}
.badge--mode {
  background: #edf6d0;
  color: #314325;
}
.detail-header__actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}
.detail-sections {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.detail-section {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 1.25rem;
}
.detail-section h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
  margin: 0 0 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f3f4f6;
}
.detail-section p {
  color: #4b5563;
  font-size: 0.9375rem;
  line-height: 1.6;
  margin: 0;
}
.pre-wrap {
  white-space: pre-wrap;
}
.detail-meta {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.5rem 1rem;
  margin: 0;
}
.detail-meta dt {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}
.detail-meta dd {
  font-size: 0.875rem;
  color: #111827;
  margin: 0;
}

/* Button styles */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  text-decoration: none;
  border: 1px solid transparent;
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
</style>
