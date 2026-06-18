<template>
  <div id="app-root" class="app-shell">
    <AppSidebar />
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import AppSidebar from '@/components/layout/AppSidebar.vue'
</script>

<style>
html,
body,
#app {
  margin: 0;
  padding: 0;
  height: 100%;
}

* {
  box-sizing: border-box;
}

body {
  background: #f5f5f1;
}

.app-shell {
  display: flex;
  height: 100%;
  min-width: 0;
  background: #f5f5f1;
}

.app-main {
  flex: 1;
  min-width: 0;
  height: 100vh;
  overflow: auto;
  background: #f5f5f1;
}
</style>
