<template>
  <Teleport to="body">
    <div class="notifications">
      <TransitionGroup name="notification">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          class="notification"
          :class="`notification--${notification.type}`"
        >
          <span class="notification__icon">{{ icon(notification.type) }}</span>
          <span class="notification__message">{{ notification.message }}</span>
          <button class="notification__close" @click="$emit('dismiss', notification.id)">
            ×
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import type { Notification } from '~/composables/useTeacherConfirmation'

defineProps<{
  notifications: Notification[]
}>()

defineEmits<{
  dismiss: [id: string]
}>()

function icon(type: string): string {
  switch (type) {
    case 'success':
      return '✓'
    case 'error':
      return '✕'
    case 'warning':
      return '⚠'
    case 'info':
      return 'ℹ'
    default:
      return 'ℹ'
  }
}
</script>

<style scoped>
.notifications {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1100;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 24rem;
}

.notification {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease;
}

.notification--success {
  border-left: 4px solid #10b981;
}

.notification--error {
  border-left: 4px solid #ef4444;
}

.notification--warning {
  border-left: 4px solid #f59e0b;
}

.notification--info {
  border-left: 4px solid #6366f1;
}

.notification__icon {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  flex-shrink: 0;
}

.notification--success .notification__icon {
  background: #d1fae5;
  color: #059669;
}

.notification--error .notification__icon {
  background: #fee2e2;
  color: #dc2626;
}

.notification--warning .notification__icon {
  background: #fef3c7;
  color: #d97706;
}

.notification--info .notification__icon {
  background: #e0e7ff;
  color: #4f46e5;
}

.notification__message {
  flex: 1;
  font-size: 0.875rem;
  color: #374151;
  line-height: 1.4;
}

.notification__close {
  width: 1.5rem;
  height: 1.5rem;
  border: none;
  border-radius: 0.25rem;
  background: transparent;
  color: #9ca3af;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.notification__close:hover {
  background: #f3f4f6;
  color: #6b7280;
}

/* Transitions */
.notification-enter-active {
  animation: slideIn 0.3s ease;
}

.notification-leave-active {
  animation: slideOut 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideOut {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}
</style>
