<script setup lang="ts">
const route = useRoute()
const isTreeHome = computed(() => route.path === '/')
</script>

<template>
  <div class="layout-default" :class="{ 'layout-default--home': isTreeHome }">
    <header class="layout-header">
      <nav class="layout-nav">
        <NuxtLink to="/" class="logo">🌳 儿童思维树</NuxtLink>
        <div class="nav-links">
          <NuxtLink to="/" class="nav-link">首页</NuxtLink>
          <NuxtLink to="/activities" class="nav-link">活动管理</NuxtLink>
        </div>
      </nav>
    </header>
    <main class="layout-main">
      <slot />
    </main>
    <footer class="layout-footer">
      <p>© 2026 儿童思维树 Children's Thinking Tree</p>
    </footer>
  </div>
</template>

<style scoped>
.layout-default {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  background:
    linear-gradient(180deg, rgba(221, 212, 160, 0.54) 0%, rgba(164, 189, 165, 0.82) 50%, rgba(100, 148, 93, 0.92) 100%),
    radial-gradient(ellipse at 50% 8%, rgba(236, 230, 183, 0.74) 0%, rgba(236, 230, 183, 0) 42%),
    #a7b6a0;
}
.layout-header {
  position: sticky;
  top: 0;
  padding: 1.25rem 2rem 0;
  border-bottom: 0;
  z-index: 1000;
}
.layout-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.logo {
  display: inline-flex;
  align-items: center;
  min-height: 52px;
  padding: 0 24px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(241, 194, 232, 0.95) 0%, rgba(207, 107, 199, 0.92) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55), 0 16px 34px rgba(88, 54, 82, 0.18);
  font-size: 1.1rem;
  font-weight: 900;
  text-decoration: none;
  color: #fff9ff;
}
.nav-links {
  display: flex;
  gap: 4px;
  padding: 6px;
  border-radius: 999px;
  background: rgba(80, 82, 63, 0.25);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.26), 0 16px 32px rgba(40, 46, 30, 0.14);
  backdrop-filter: blur(18px);
}
.nav-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 88px;
  min-height: 40px;
  padding: 0 18px;
  border-radius: 999px;
  font-size: 0.9rem;
  font-weight: 900;
  color: rgba(255, 255, 237, 0.72);
  text-decoration: none;
  transition: color 0.15s;
}
.nav-link:hover {
  color: #fff9dc;
}
.nav-link.router-link-active {
  background: rgba(255, 255, 245, 0.9);
  color: #1f2a1c;
}
.layout-main {
  flex: 1;
  position: relative;
  z-index: 1;
  padding: 3.5rem 2.5rem 4.5rem;
}
.layout-footer {
  position: relative;
  z-index: 1;
  padding: 1rem 2rem 1.5rem;
  text-align: center;
  border-top: 0;
  color: rgba(255, 255, 237, 0.78);
  font-size: 0.875rem;
}

.layout-default--home {
  height: 100vh;
  overflow: hidden;
  background: #aeb49b;
}

.layout-default--home .layout-header {
  position: fixed;
  top: 30px;
  left: 38px;
  right: 38px;
  padding: 0;
  border-bottom: 0;
  pointer-events: none;
}

.layout-default--home .layout-nav {
  position: relative;
  min-height: 68px;
}

.layout-default--home .logo,
.layout-default--home .nav-links,
.layout-default--home .nav-link {
  pointer-events: auto;
}

.layout-default--home .logo {
  display: inline-flex;
  align-items: center;
  min-height: 58px;
  padding: 0 26px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(241, 194, 232, 0.95) 0%, rgba(207, 107, 199, 0.92) 100%);
  color: #fff9ff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55), 0 16px 34px rgba(88, 54, 82, 0.18);
  font-size: 18px;
  font-weight: 900;
}

.layout-default--home .nav-links {
  position: absolute;
  left: 50%;
  top: 8px;
  display: flex;
  gap: 4px;
  padding: 6px;
  border-radius: 999px;
  background: rgba(80, 82, 63, 0.25);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.26), 0 16px 32px rgba(40, 46, 30, 0.14);
  backdrop-filter: blur(18px);
  transform: translateX(-50%);
}

.layout-default--home .nav-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 88px;
  min-height: 44px;
  padding: 0 18px;
  border-radius: 999px;
  color: rgba(255, 255, 237, 0.72);
  font-size: 14px;
  font-weight: 900;
}

.layout-default--home .nav-link.router-link-active {
  background: rgba(255, 255, 245, 0.9);
  color: #1f2a1c;
}

.layout-default--home .layout-main {
  flex: none;
  width: 100vw;
  height: 100vh;
  padding: 0;
}

.layout-default--home .layout-footer {
  display: none;
}

@media (max-width: 768px) {
  .layout-header {
    padding: 0.875rem 1rem;
  }

  .layout-nav {
    align-items: flex-start;
    flex-direction: column;
  }

  .layout-default--home .layout-header {
    top: 18px;
    left: 16px;
    right: 16px;
  }

  .layout-default--home .layout-nav {
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
    min-height: 0;
  }

  .layout-default--home .logo {
    width: fit-content;
    min-height: 46px;
    padding: 0 18px;
    font-size: 15px;
  }

  .layout-default--home .nav-links {
    position: static;
    width: fit-content;
    transform: none;
  }

  .layout-default--home .nav-link {
    min-width: 74px;
    min-height: 36px;
    padding: 0 12px;
    font-size: 12px;
  }
}
</style>

<style>
.page-activities,
.page-create,
.page-detail,
.page-edit {
  width: min(1040px, calc(100vw - 64px));
  margin: 0 auto;
  padding: 34px;
  border: 1px solid rgba(255, 255, 255, 0.36);
  border-radius: 30px;
  background: rgba(255, 255, 242, 0.64);
  box-shadow: 0 24px 70px rgba(34, 42, 26, 0.18);
  backdrop-filter: blur(18px);
}

.page-create,
.page-edit {
  width: min(780px, calc(100vw - 64px));
}

.page-detail {
  width: min(900px, calc(100vw - 64px));
}

.page-header h1,
.detail-header__main h1 {
  color: #24301d !important;
  font-weight: 900 !important;
}

.page-subtitle,
.detail-section p,
.activity-card__desc,
.filter-count,
.filter-label {
  color: rgba(45, 54, 35, 0.72) !important;
}

.page-filters,
.page-content,
.detail-section,
.activity-card,
.activity-list__empty,
.activity-list__error {
  border: 1px solid rgba(255, 255, 255, 0.42) !important;
  border-radius: 22px !important;
  background: rgba(255, 255, 242, 0.72) !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.52), 0 14px 34px rgba(46, 54, 32, 0.1) !important;
}

.activity-list__grid {
  gap: 18px !important;
}

.activity-card {
  transition: transform 0.18s ease, box-shadow 0.18s ease !important;
}

.activity-card:hover {
  transform: translateY(-3px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.58), 0 20px 42px rgba(46, 54, 32, 0.16) !important;
}

.activity-card__title a,
.detail-section h3,
.detail-meta dd,
.page-error h2 {
  color: #26311f !important;
}

.activity-card__actions,
.detail-section h3,
.activity-form__actions {
  border-top-color: rgba(96, 113, 68, 0.16) !important;
}

.back-link,
.btn,
.btn--primary,
.btn--outline,
.btn--danger {
  border-radius: 999px !important;
  font-weight: 900 !important;
}

.back-link {
  display: inline-flex !important;
  align-items: center;
  min-height: 38px;
  padding: 0 16px;
  background: rgba(255, 255, 242, 0.58);
  color: #2b3722 !important;
  text-decoration: none !important;
}

.btn--primary {
  border-color: transparent !important;
  background: linear-gradient(180deg, #e6edb4 0%, #98bd55 100%) !important;
  color: #25351d !important;
}

.btn--outline {
  border-color: rgba(255, 255, 255, 0.54) !important;
  background: rgba(255, 255, 242, 0.76) !important;
  color: #2f3328 !important;
}

.btn--danger {
  border-color: rgba(160, 75, 55, 0.22) !important;
  background: rgba(255, 231, 208, 0.72) !important;
  color: #7b3020 !important;
}

.activity-card__badge,
.activity-card__tag,
.badge {
  border-radius: 999px !important;
  font-weight: 900 !important;
}

.activity-form__input,
.activity-form__textarea,
.activity-form__select,
.filter-checkbox {
  border-color: rgba(96, 113, 68, 0.2) !important;
  border-radius: 14px !important;
}

.activity-form__input:focus,
.activity-form__textarea:focus,
.activity-form__select:focus {
  border-color: #98bd55 !important;
  box-shadow: 0 0 0 3px rgba(152, 189, 85, 0.18) !important;
}

@media (max-width: 768px) {
  .page-activities,
  .page-create,
  .page-detail,
  .page-edit {
    width: calc(100vw - 28px);
    padding: 18px;
    border-radius: 24px;
  }
}
</style>
