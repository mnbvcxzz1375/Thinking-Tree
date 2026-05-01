<template>
  <div class="page-home">
    <ThinkingTree />
  </div>
</template>

<script setup lang="ts">
import ThinkingTree from '../components/ThinkingTree.vue'

useHead({
  title: '首页 - 儿童思维树 (Thinking Tree)',
})
</script>

<style>
body {
  margin: 0;
  overflow: hidden;
}
</style>

<style scoped>
.page-home {
  width: 100vw;
  height: 100vh;
}
</style>
