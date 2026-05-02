<template>
  <div class="page-create">
    <div class="page-header">
      <NuxtLink to="/activities" class="back-link">← 返回活动列表</NuxtLink>
      <h1>创建新活动</h1>
      <p class="page-subtitle">创建一个新的思维树活动</p>
    </div>

    <div class="page-content">
      <ActivityForm
        submit-label="创建活动"
        :submitting="store.loading"
        :error="store.error"
        @submit="handleCreate"
        @cancel="navigateBack"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useActivityStore } from '~/stores/activity'
import type { ActivityCreateInput } from '~/stores/activity'

useHead({
  title: '创建活动 - 儿童思维树',
})

const store = useActivityStore()
const router = useRouter()

function navigateBack() {
  router.push('/activities')
}

async function handleCreate(data: ActivityCreateInput) {
  store.clearError()
  const result = await store.createActivity(data)
  if (result) {
    router.push(`/activities/${result.id}`)
  }
}

// Clear error on unmount
onUnmounted(() => {
  store.clearError()
})
</script>

<style scoped>
.page-create {
  max-width: 720px;
  margin: 0 auto;
  height: calc(100vh - 9.5rem);
  max-height: 980px;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}
.page-header {
  margin-bottom: 1.5rem;
  flex-shrink: 0;
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
.page-content {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
  overscroll-behavior: contain;
  scrollbar-width: thin;
  scrollbar-color: rgba(92, 122, 62, 0.42) rgba(237, 244, 213, 0.48);
}

.page-content::-webkit-scrollbar {
  width: 10px;
}

.page-content::-webkit-scrollbar-track {
  margin: 12px 6px 12px 0;
  background: rgba(237, 244, 213, 0.48);
  border-radius: 999px;
}

.page-content::-webkit-scrollbar-thumb {
  background: rgba(92, 122, 62, 0.42);
  border-radius: 999px;
  border: 3px solid transparent;
  background-clip: padding-box;
}

.page-content::-webkit-scrollbar-thumb:hover {
  background: rgba(92, 122, 62, 0.62);
  border: 3px solid transparent;
  background-clip: padding-box;
}

.page-content :deep(.activity-form) {
  max-width: none;
}

@media (max-width: 768px) {
  .page-create {
    height: calc(100vh - 7.5rem);
  }
}
</style>
