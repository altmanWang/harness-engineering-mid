<template>
  <div id="app-root" class="app-shell">
    <AppSidebar v-if="showSidebar" />
    <main class="app-main" :class="{ 'full-width': !showSidebar }">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import AppSidebar from '@/components/layout/AppSidebar.vue'

const route = useRoute()
const chatStore = useChatStore()

const showSidebar = computed(() => {
  if (route.path !== '/') return true
  return !!chatStore.currentSessionId
})
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
  background: #f7f7f4;
}

.app-shell {
  display: flex;
  height: 100%;
  min-width: 0;
  background: #f7f7f4;
}

.app-main {
  flex: 1;
  min-width: 0;
  height: 100vh;
  overflow: auto;
  background: #f7f7f4;
}

.app-main.full-width {
  width: 100%;
}
</style>
