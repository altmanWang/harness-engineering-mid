<template>
  <div id="app-root">
    <Navbar />
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import Navbar from '@/components/layout/Navbar.vue'
</script>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
}
#app-root {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.app-main {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: var(--el-bg-color-page);
}
</style>
