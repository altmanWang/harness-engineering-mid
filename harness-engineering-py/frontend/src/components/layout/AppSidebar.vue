<template>
  <aside class="app-sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-brand">
      <button class="brand-button" type="button" @click="goHome">
        <span class="brand-mark">H</span>
        <span v-if="!isCollapsed" class="brand-name">Harness</span>
      </button>
    </div>

    <nav class="sidebar-nav" aria-label="主导航">
      <div
        class="nav-item"
        :class="{ active: activeRoute === '/skills' }"
        index="/skills"
        @click="go('/skills')"
      >
        <el-icon><MagicStick /></el-icon>
        <span v-if="!isCollapsed">Skills</span>
      </div>
      <div
        class="nav-item"
        :class="{ active: activeRoute === '/agents' }"
        index="/agents"
        @click="go('/agents')"
      >
        <el-icon><Service /></el-icon>
        <span v-if="!isCollapsed">Agents</span>
      </div>
      <div
        class="nav-item"
        :class="{ active: activeRoute === '/stock' }"
        index="/stock"
        @click="go('/stock')"
      >
        <el-icon><TrendCharts /></el-icon>
        <span v-if="!isCollapsed">Stock</span>
      </div>
    </nav>

    <section class="history-section" aria-label="历史会话">
      <div class="history-heading">
        <div class="history-title">
          <el-icon><Clock /></el-icon>
          <span v-if="!isCollapsed">历史会话</span>
        </div>
        <div class="history-actions">
          <el-button
            v-if="!isCollapsed && selectedSessionIds.length >= 2"
            size="small"
            text
            type="primary"
            @click="handleCompare"
          >
            对比 ({{ selectedSessionIds.length }})
          </el-button>
          <el-button
            v-if="!isCollapsed"
            :icon="Plus"
            size="small"
            text
            circle
            @click="handleNewSession"
          />
        </div>
      </div>

      <div v-if="!isCollapsed" class="history-list">
        <button
          v-for="session in recentSessions"
          :key="session.id"
          type="button"
          class="history-item"
          :class="{ active: session.id === chatStore.currentSessionId }"
          @click="handleSelectSession(session.id)"
        >
          <el-checkbox
            v-if="session.type === 'stock_diagnosis'"
            :model-value="selectedSessionIds.includes(session.id)"
            size="small"
            @click.stop
            @change="toggleSelectSession(session.id)"
          />
          <el-icon size="14" class="history-type-icon">
            <TrendCharts v-if="session.type === 'stock_diagnosis'" />
            <ChatDotSquare v-else />
          </el-icon>
          <span class="history-name">{{ session.title || '新会话' }}</span>
          <el-button
            class="history-delete"
            :icon="Delete"
            size="small"
            text
            circle
            @click.stop="handleDeleteSession(session.id)"
          />
        </button>
        <div v-if="recentSessions.length === 0" class="history-empty">暂无会话</div>
      </div>
    </section>

    <div v-if="!isCollapsed" class="sidebar-engine">
      <EngineInfo
        engine-name="OpenCode"
        :model-name="chatStore.model"
        :models="availableModels"
      />
    </div>

    <div class="sidebar-actions">
      <el-button
        class="icon-action"
        :icon="isDark ? Sunny : Moon"
        text
        circle
        @click="toggleTheme"
      />
      <el-button
        class="icon-action"
        :icon="isCollapsed ? Expand : Fold"
        text
        circle
        @click="isCollapsed = !isCollapsed"
      />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatDotSquare, Clock, Delete, Expand, Fold, MagicStick, Moon, Plus, Service, Sunny, TrendCharts } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { useEngineStore } from '@/stores/engine'
import EngineInfo from '@/components/workflow/EngineInfo.vue'
import type { ModelInfo } from '@/types/chat'

const router = useRouter()
const route = useRoute()
const chatStore = useChatStore()
const engineStore = useEngineStore()
const isCollapsed = ref(false)
const isDark = ref(false)
const availableModels = ref<ModelInfo[]>([])

const activeRoute = computed(() => {
  if (route.path.startsWith('/skills')) return '/skills'
  if (route.path.startsWith('/agents')) return '/agents'
  if (route.path.startsWith('/stock')) return '/stock'
  return ''
})

const recentSessions = computed(() => chatStore.sessions.slice(0, 8))

onMounted(async () => {
  chatStore.loadSessions().catch((err) => {
    console.error('Failed to load sessions:', err)
  })
  await engineStore.fetchAvailability()
  if (engineStore.engineInfo) {
    availableModels.value = engineStore.engineInfo.models || []
  }
})

function go(path: string) {
  router.push(path)
}

function goHome() {
  chatStore.clearSession()
  router.push('/')
}

async function handleNewSession() {
  try {
    await chatStore.createSession()
    router.push('/')
  } catch (err) {
    console.error('Failed to create session:', err)
  }
}

const selectedSessionIds = ref<string[]>([])

function toggleSelectSession(id: string) {
  const idx = selectedSessionIds.value.indexOf(id)
  if (idx >= 0) {
    selectedSessionIds.value.splice(idx, 1)
  } else {
    selectedSessionIds.value.push(id)
  }
}

function handleCompare() {
  if (selectedSessionIds.value.length >= 2) {
    router.push(`/stock?compare=${selectedSessionIds.value.join(',')}`)
  }
}

function handleSelectSession(id: string) {
  chatStore.selectSession(id)
  const session = chatStore.sessions.find(s => s.id === id)
  if (session?.type === 'stock_diagnosis') {
    router.push('/stock')
  } else {
    router.push('/')
  }
}

async function handleDeleteSession(id: string) {
  try {
    await chatStore.deleteSession(id)
  } catch (err) {
    console.error('Failed to delete session:', err)
  }
}

function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
}
</script>

<style scoped>
.app-sidebar {
  width: 248px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border-right: 1px solid #e8e8e2;
  background: rgba(255, 255, 255, 0.85);
  transition: width 0.18s ease;
}
.app-sidebar.collapsed {
  width: 64px;
}
.sidebar-brand {
  padding: 14px 12px 10px;
}
.brand-button {
  width: 100%;
  height: 40px;
  border: 0;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px;
  border-radius: 12px;
  cursor: pointer;
  color: var(--el-text-color-primary);
}
.brand-button:hover {
  background: var(--el-fill-color-light);
}
.brand-mark {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color);
  font-weight: 700;
}
.brand-name {
  font-size: 16px;
  font-weight: 650;
}
.sidebar-nav {
  padding: 4px 10px;
}
.nav-item {
  height: 40px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 10px;
  margin-bottom: 4px;
  border-radius: 12px;
  cursor: pointer;
  color: var(--el-text-color-regular);
  font-size: 14px;
}
.nav-item:hover,
.nav-item.active {
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
}
.history-section {
  margin-top: auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 8px 10px;
}
.history-heading {
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  padding: 0 6px;
}
.history-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.history-list {
  min-height: 0;
  max-height: 260px;
  overflow-y: auto;
}
.history-item {
  width: 100%;
  height: 34px;
  border: 0;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 4px 0 10px;
  border-radius: 10px;
  cursor: pointer;
  color: var(--el-text-color-regular);
  text-align: left;
}
.history-item:hover,
.history-item.active {
  background: var(--el-fill-color-light);
}
.history-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}
.history-delete {
  opacity: 0;
  transition: opacity 0.12s ease;
}
.history-item:hover .history-delete {
  opacity: 1;
}
.history-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
.history-type-icon {
  flex-shrink: 0;
  color: var(--el-text-color-secondary);
}
.history-empty {
  padding: 12px 10px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
.sidebar-actions {
  display: flex;
  gap: 4px;
  padding: 8px 12px 14px;
  border-top: 1px solid var(--el-border-color-extra-light);
}
.app-sidebar.collapsed .sidebar-actions {
  flex-direction: column;
  align-items: center;
}
.icon-action {
  color: var(--el-text-color-secondary);
}
@media (max-width: 900px) {
  .app-sidebar {
    width: 64px;
  }
  .app-sidebar:not(.collapsed) {
    width: 64px;
  }
}
</style>
