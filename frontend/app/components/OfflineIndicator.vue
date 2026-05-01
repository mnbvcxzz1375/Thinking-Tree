/**
 * Offline indicator component.
 */
<template>
  <div
    v-if="!isOnline || hasPendingChanges"
    class="offline-indicator"
    :class="{ 'is-offline': !isOnline, 'has-pending': hasPendingChanges }"
  >
    <div class="offline-indicator__icon">
      <svg
        v-if="!isOnline"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <line x1="1" y1="1" x2="23" y2="23" />
        <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" />
        <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" />
        <path d="M10.71 5.05A16 16 0 0 1 22.56 9" />
        <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" />
        <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
        <line x1="12" y1="20" x2="12.01" y2="20" />
      </svg>
      <svg
        v-else
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <path d="M22 12A10 10 0 1 1 12 2" />
        <path d="M22 2L12 12" />
        <path d="M16 2h6v6" />
      </svg>
    </div>

    <div class="offline-indicator__text">
      <span v-if="!isOnline">You are offline</span>
      <span v-else-if="isSyncing">Syncing changes...</span>
      <span v-else>{{ pendingCount }} pending change{{ pendingCount !== 1 ? 's' : '' }}</span>
    </div>

    <button
      v-if="isOnline && hasPendingChanges && !isSyncing"
      class="offline-indicator__sync"
      @click="syncPendingChanges"
    >
      Sync Now
    </button>
  </div>
</template>

<script setup lang="ts">
import { useOffline } from '~/composables/useOffline'

const { isOnline, isSyncing, hasPendingChanges, pendingCount, syncPendingChanges } = useOffline()
</script>

<style scoped>
.offline-indicator {
  position: fixed;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.25rem;
  border-radius: 9999px;
  background-color: #f59e0b;
  color: #000;
  font-size: 0.875rem;
  font-weight: 500;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  z-index: 50;
  transition: all 0.3s ease;
}

.offline-indicator.is-offline {
  background-color: #ef4444;
  color: #fff;
}

.offline-indicator.has-pending {
  background-color: #3b82f6;
  color: #fff;
}

.offline-indicator__icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}

.offline-indicator__icon svg {
  width: 100%;
  height: 100%;
}

.offline-indicator__text {
  white-space: nowrap;
}

.offline-indicator__sync {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  background-color: rgba(255, 255, 255, 0.2);
  color: inherit;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.offline-indicator__sync:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

/* Animation */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.offline-indicator.is-offline .offline-indicator__icon {
  animation: pulse 2s infinite;
}
</style>
