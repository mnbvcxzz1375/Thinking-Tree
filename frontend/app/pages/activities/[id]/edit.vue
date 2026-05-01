<template>
  <div class="page-edit">
    <div class="page-header">
      <NuxtLink :to="`/activities/${activityId}`" class="back-link">← 返回活动详情</NuxtLink>
      <h1>编辑活动</h1>
      <p class="page-subtitle">修改活动信息</p>
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

    <div v-else class="page-content">
      <ActivityForm
        :activity="activity"
        submit-label="保存修改"
        :submitting="store.loading"
        :error="store.error"
        @submit="handleUpdate"
        @cancel="navigateBack"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useActivityStore } from '~/stores/activity'
import type { ActivityUpdateInput } from '~/stores/activity'

const route = useRoute()
const router = useRouter()
const store = useActivityStore()

const activityId = computed(() => Number(route.params.id))
const activity = computed(() => store.currentActivity)

function navigateBack() {
  router.push(`/activities/${activityId.value}`)
}

async function handleUpdate(data: ActivityUpdateInput) {
  store.clearError()
  const result = await store.updateActivity(activityId.value, data)
  if (result) {
    router.push(`/activities/${activityId.value}`)
  }
}

useHead({
  title: computed(() => activity.value ? `编辑 ${activity.value.title} - 儿童思维树` : '编辑活动 - 儿童思维树'),
})

// Fetch activity on mount
onMounted(() => {
  store.fetchActivity(activityId.value)
})

// Clear error on unmount
onUnmounted(() => {
  store.clearError()
})
</script>

<style scoped>
.page-edit {
  max-width: 720px;
  margin: 0 auto;
}
.page-header {
  margin-bottom: 2rem;
}
.back-link {
  font-size: 0.875rem;
  color: #2563eb;
  text-decoration: none;
  display: inline-block;
  margin-bottom: 0.75rem;
}
.back-link:hover {
  text-decoration: underline;
}
.page-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}
.page-subtitle {
  color: #6b7280;
  font-size: 0.875rem;
  margin: 0.25rem 0 0;
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
.page-content {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 1.5rem;
}

/* Button */
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
</style>
