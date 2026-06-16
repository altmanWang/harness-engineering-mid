<template>
  <el-menu
    :default-active="activeRoute"
    mode="horizontal"
    :ellipsis="false"
    class="navbar-menu"
    @select="handleSelect"
  >
    <div class="navbar-brand">
      <span class="brand-text">Harness</span>
    </div>
    <div class="navbar-items">
      <el-menu-item index="/skills">
        <el-icon><MagicStick /></el-icon>
        <span>Skills</span>
      </el-menu-item>
      <el-menu-item index="/agents">
        <el-icon><Robot /></el-icon>
        <span>Agents</span>
      </el-menu-item>
      <el-menu-item index="/workflow">
        <el-icon><Connection /></el-icon>
        <span>工作流</span>
      </el-menu-item>
    </div>
    <div class="navbar-actions">
      <el-switch
        v-model="isDark"
        :active-action-icon="Sunny"
        :inactive-action-icon="Moon"
        inline-prompt
        @change="toggleTheme"
      />
    </div>
  </el-menu>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { MagicStick, Robot, Connection, Sunny, Moon } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const isDark = ref(false)

const activeRoute = computed(() => {
  const path = route.path
  if (path.startsWith('/skills')) return '/skills'
  if (path.startsWith('/agents')) return '/agents'
  if (path.startsWith('/workflow')) return '/workflow'
  return '/skills'
})

function handleSelect(index: string) {
  router.push(index)
}

function toggleTheme(val: boolean) {
  document.documentElement.classList.toggle('dark', val)
}
</script>

<style scoped>
.navbar-menu {
  display: flex;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  border-bottom: 1px solid var(--el-border-color-light);
}
.navbar-brand {
  margin-right: 16px;
}
.brand-text {
  font-size: 18px;
  font-weight: 600;
}
.navbar-items {
  display: flex;
  flex: 1;
  border-bottom: none !important;
}
.navbar-items .el-menu-item {
  border-bottom: none !important;
}
.navbar-actions {
  margin-left: auto;
}
</style>
