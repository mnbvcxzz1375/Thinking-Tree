<template>
  <div class="page-activities">
    <div class="page-header">
      <div>
        <h1>活动管理</h1>
        <p class="page-subtitle">管理思维树活动，创建和组织学习内容</p>
      </div>
      <NuxtLink to="/activities/create" class="btn btn--primary">
        + 创建活动
      </NuxtLink>
    </div>

    <div class="page-filters">
      <label class="filter-label">
        <input
          v-model="activeOnly"
          type="checkbox"
          class="filter-checkbox"
          @change="handleFilterChange"
        />
        仅显示已启用
      </label>
      <span class="filter-count">
        共 {{ store.activityCount }} 个活动
      </span>
    </div>

    <ActivityList
      :activities="displayedActivities"
      :loading="store.loading"
      :error="store.error"
      @delete="handleDelete"
      @retry="fetchActivities"
    />
  </div>
</template>

<script setup lang="ts">
import { useActivityStore } from '~/stores/activity'

useHead({
  title: '活动管理 - 儿童思维树',
})

const store = useActivityStore()
const activeOnly = ref(false)

const displayedActivities = computed(() => {
  if (activeOnly.value) {
    return store.activeActivities
  }
  return store.activities
})

function fetchActivities() {
  store.fetchActivities({ active_only: activeOnly.value })
}

function handleFilterChange() {
  fetchActivities()
}

async function handleDelete(id: number) {
  if (!confirm('确定要删除此活动吗？此操作不可撤销。')) return
  const success = await store.deleteActivity(id)
  if (success) {
    // Activity removed from store automatically
  }
}

// Fetch on mount
onMounted(() => {
  fetchActivities()
})
</script>

<style scoped>
.page-activities {
  max-width: 960px;
  margin: 0 auto;
  padding: 0.75rem 1.75rem 2rem;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  gap: 1rem;
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
  margin: 0.45rem 0 0;
}
.page-filters {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.35rem;
  padding: 1rem 1.25rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.filter-label {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
}
.filter-checkbox {
  width: 1rem;
  height: 1rem;
  accent-color: #2563eb;
}
.filter-count {
  font-size: 0.8125rem;
  color: #6b7280;
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
  white-space: nowrap;
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
  .page-activities {
    padding: 0.5rem 0.75rem 1.5rem;
  }
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  .page-header h1 {
    font-size: 1.25rem;
  }
  .page-header .btn {
    width: 100%;
    justify-content: center;
  }
  .page-filters {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
