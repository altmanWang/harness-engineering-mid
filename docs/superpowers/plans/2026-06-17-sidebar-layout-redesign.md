# Sidebar Layout Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the top navigation with a collapsible Kimi-inspired left sidebar that shows Skills/Agents navigation and Workflow history, while making Workflow the default homepage.

**Architecture:** The root Vue shell will own a new `AppSidebar.vue` beside the route content. Workflow session CRUD moves into the Pinia chat store so both the application sidebar and Workflow view share one source of truth. Workflow becomes a chat-only main area with a small top bar for session title and model selection.

**Tech Stack:** Vue 3, TypeScript, Vite, Pinia, Vue Router, Element Plus, `@element-plus/icons-vue`.

---

## File Structure

### Create

- `harness-engineering-py/frontend/scripts/verify-sidebar-layout.mjs` — static smoke test for route/layout/sidebar source contracts.
- `harness-engineering-py/frontend/src/components/layout/AppSidebar.vue` — application left sidebar with nav, history, collapse, theme toggle.

### Modify

- `harness-engineering-py/frontend/package.json` — add `verify:sidebar-layout` script.
- `harness-engineering-py/frontend/src/router/index.ts` — redirect `/` to `/workflow`.
- `harness-engineering-py/frontend/src/App.vue` — replace top-nav shell with sidebar app shell.
- `harness-engineering-py/frontend/src/stores/chat.ts` — move session CRUD and current-session state into store actions.
- `harness-engineering-py/frontend/src/views/WorkflowView.vue` — rely on store actions, auto-create session on first send, refresh sessions after done.
- `harness-engineering-py/frontend/src/components/workflow/ChatLayout.vue` — remove `ChatSidebar`, add top bar and model selector.
- `harness-engineering-py/frontend/src/composables/useChatStream.ts` — add optional `onDone` callback so Workflow can refresh session history.

### Leave Unused Unless Imported Elsewhere

- `harness-engineering-py/frontend/src/components/layout/Navbar.vue` — no longer referenced by `App.vue`; delete only after confirming no imports remain.
- `harness-engineering-py/frontend/src/components/workflow/ChatSidebar.vue` — no longer referenced by `ChatLayout.vue`; keep for now unless no imports remain.

---

## Task 1: Add Sidebar Layout Verification Script

**Files:**
- Create: `harness-engineering-py/frontend/scripts/verify-sidebar-layout.mjs`
- Modify: `harness-engineering-py/frontend/package.json`

- [ ] **Step 1: Create the failing verification script**

Create `harness-engineering-py/frontend/scripts/verify-sidebar-layout.mjs`:

```js
import fs from 'node:fs'
import path from 'node:path'
import process from 'node:process'

const root = process.cwd()

function read(file) {
  return fs.readFileSync(path.join(root, file), 'utf8')
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message)
  }
}

const router = read('src/router/index.ts')
const app = read('src/App.vue')
const chatLayout = read('src/components/workflow/ChatLayout.vue')

assert(router.includes("redirect: '/workflow'"), 'root route must redirect to /workflow')
assert(fs.existsSync(path.join(root, 'src/components/layout/AppSidebar.vue')), 'AppSidebar.vue must exist')
assert(app.includes('<AppSidebar />'), 'App.vue must render AppSidebar')
assert(!app.includes('<Navbar />'), 'App.vue must not render Navbar')
assert(!app.includes("@/components/layout/Navbar.vue"), 'App.vue must not import Navbar')
assert(chatLayout.includes('workflow-topbar'), 'ChatLayout must include a Workflow top bar')
assert(!chatLayout.includes('<ChatSidebar'), 'ChatLayout must not render ChatSidebar')
assert(!chatLayout.includes("import ChatSidebar"), 'ChatLayout must not import ChatSidebar')

const sidebar = read('src/components/layout/AppSidebar.vue')
assert(sidebar.includes("index=\"/skills\""), 'AppSidebar must include Skills nav item')
assert(sidebar.includes("index=\"/agents\""), 'AppSidebar must include Agents nav item')
assert(!sidebar.includes("index=\"/workflow\""), 'AppSidebar must not include Workflow as a primary nav item')
assert(sidebar.includes('history-section'), 'AppSidebar must include bottom history section')
assert(sidebar.includes('isCollapsed'), 'AppSidebar must support collapsed state')

console.log('Sidebar layout source checks passed')
```

- [ ] **Step 2: Add the npm script**

Modify `harness-engineering-py/frontend/package.json` scripts block to include `verify:sidebar-layout`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview",
    "verify:sidebar-layout": "node scripts/verify-sidebar-layout.mjs"
  }
}
```

Keep the existing package fields and dependencies unchanged.

- [ ] **Step 3: Run verification and confirm it fails for the expected reason**

Run:

```bash
cd harness-engineering-py/frontend
npm run verify:sidebar-layout
```

Expected: FAIL with an error like `root route must redirect to /workflow` or `AppSidebar.vue must exist`. This proves the verification script detects the old layout.

- [ ] **Step 4: Commit the failing verification script**

```bash
git add harness-engineering-py/frontend/scripts/verify-sidebar-layout.mjs harness-engineering-py/frontend/package.json
git commit -m "test: add sidebar layout verification script" \
  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Move Root Route to Workflow

**Files:**
- Modify: `harness-engineering-py/frontend/src/router/index.ts`

- [ ] **Step 1: Update the root redirect**

Change the `/` route in `src/router/index.ts` from `/skills` to `/workflow`:

```ts
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/workflow',
    },
    {
      path: '/skills',
      name: 'Skills',
      component: () => import('@/views/SkillsView.vue'),
    },
    {
      path: '/agents',
      name: 'Agents',
      component: () => import('@/views/AgentsView.vue'),
    },
    {
      path: '/workflow',
      name: 'Workflow',
      component: () => import('@/views/WorkflowView.vue'),
    },
  ],
})

export default router
```

- [ ] **Step 2: Run the focused verification**

Run:

```bash
cd harness-engineering-py/frontend
npm run verify:sidebar-layout
```

Expected: still FAIL, but no longer because of the root route. The next expected failure is `AppSidebar.vue must exist`.

- [ ] **Step 3: Commit the route change**

```bash
git add harness-engineering-py/frontend/src/router/index.ts
git commit -m "feat: make workflow the default route" \
  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Centralize Chat Session CRUD in Pinia Store

**Files:**
- Modify: `harness-engineering-py/frontend/src/stores/chat.ts`

- [ ] **Step 1: Replace `src/stores/chat.ts` with store actions**

Replace the file with:

```ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatSession, ChatMessage, PermissionRequest } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<string | null>(null)
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref(false)
  const pendingPermission = ref<PermissionRequest | null>(null)
  const model = ref('claude-sonnet-4-6')
  const agentSessionId = ref<string | undefined>(undefined)

  function setSessions(list: ChatSession[]) {
    sessions.value = list
  }

  async function loadSessions() {
    const res = await fetch('/api/chat/sessions')
    const data = await res.json()
    setSessions(data.sessions || [])
  }

  function selectSession(id: string) {
    currentSessionId.value = id
    const session = sessions.value.find(s => s.id === id)
    if (session) {
      messages.value = session.messages
      agentSessionId.value = session.agentSessionId
      model.value = session.model
    }
  }

  async function createSession() {
    const res = await fetch('/api/chat/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ engine: 'opencode', model: model.value }),
    })
    const data = await res.json()
    const session = data.session as ChatSession
    setSessions([session, ...sessions.value])
    selectSession(session.id)
    messages.value = []
    return session
  }

  async function deleteSession(id: string) {
    await fetch('/api/chat/sessions', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    })
    setSessions(sessions.value.filter(s => s.id !== id))
    if (currentSessionId.value === id) {
      clearSession()
    }
  }

  function clearSession() {
    currentSessionId.value = null
    messages.value = []
    agentSessionId.value = undefined
  }

  function setModel(nextModel: string) {
    model.value = nextModel
  }

  function setAgentSessionId(id: string) {
    agentSessionId.value = id
    const session = sessions.value.find(s => s.id === currentSessionId.value)
    if (session) {
      session.agentSessionId = id
    }
  }

  return {
    sessions,
    currentSessionId,
    messages,
    isStreaming,
    pendingPermission,
    model,
    agentSessionId,
    setSessions,
    loadSessions,
    selectSession,
    createSession,
    deleteSession,
    clearSession,
    setModel,
    setAgentSessionId,
  }
})
```

- [ ] **Step 2: Run TypeScript build check**

Run:

```bash
cd harness-engineering-py/frontend
npm run build
```

Expected: may FAIL because `WorkflowView.vue` still has duplicate local session CRUD and direct store field mutation patterns. The failure should be TypeScript/template integration related, not a syntax error in `chat.ts`.

- [ ] **Step 3: Commit store centralization**

Only commit if `npm run build` either passes or the failure is clearly from later tasks. If committing with known later-task failures, mention it in the task handoff notes.

```bash
git add harness-engineering-py/frontend/src/stores/chat.ts
git commit -m "feat: centralize chat sessions in store" \
  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Create the Application Sidebar

**Files:**
- Create: `harness-engineering-py/frontend/src/components/layout/AppSidebar.vue`

- [ ] **Step 1: Create `AppSidebar.vue`**

Create `src/components/layout/AppSidebar.vue`:

```vue
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
    </nav>

    <section class="history-section" aria-label="历史会话">
      <div class="history-heading">
        <div class="history-title">
          <el-icon><Clock /></el-icon>
          <span v-if="!isCollapsed">历史会话</span>
        </div>
        <el-button
          v-if="!isCollapsed"
          :icon="Plus"
          size="small"
          text
          circle
          @click="handleNewSession"
        />
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
import { Clock, Delete, Expand, Fold, MagicStick, Moon, Plus, Service, Sunny } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'

const router = useRouter()
const route = useRoute()
const chatStore = useChatStore()
const isCollapsed = ref(false)
const isDark = ref(false)

const activeRoute = computed(() => {
  if (route.path.startsWith('/skills')) return '/skills'
  if (route.path.startsWith('/agents')) return '/agents'
  return ''
})

const recentSessions = computed(() => chatStore.sessions.slice(0, 8))

onMounted(() => {
  chatStore.loadSessions().catch((err) => {
    console.error('Failed to load sessions:', err)
  })
})

function go(path: string) {
  router.push(path)
}

function goHome() {
  router.push('/workflow')
}

async function handleNewSession() {
  await chatStore.createSession()
  router.push('/workflow')
}

function handleSelectSession(id: string) {
  chatStore.selectSession(id)
  router.push('/workflow')
}

async function handleDeleteSession(id: string) {
  await chatStore.deleteSession(id)
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
  border-right: 1px solid var(--el-border-color-lighter);
  background: rgba(255, 255, 255, 0.92);
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
```

- [ ] **Step 2: Run focused verification**

Run:

```bash
cd harness-engineering-py/frontend
npm run verify:sidebar-layout
```

Expected: still FAIL because `App.vue` has not yet rendered `<AppSidebar />`, and `ChatLayout.vue` still renders `ChatSidebar`.

- [ ] **Step 3: Run build to catch component syntax issues**

Run:

```bash
cd harness-engineering-py/frontend
npm run build
```

Expected: PASS or fail only because later tasks have not updated consumers. Fix syntax/import errors in `AppSidebar.vue` before continuing.

- [ ] **Step 4: Commit AppSidebar**

```bash
git add harness-engineering-py/frontend/src/components/layout/AppSidebar.vue
git commit -m "feat: add application sidebar" \
  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Replace App Root Shell

**Files:**
- Modify: `harness-engineering-py/frontend/src/App.vue`

- [ ] **Step 1: Replace App shell code**

Replace `src/App.vue` with:

```vue
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
</style>
```

- [ ] **Step 2: Run focused verification**

Run:

```bash
cd harness-engineering-py/frontend
npm run verify:sidebar-layout
```

Expected: still FAIL because `ChatLayout.vue` still renders `ChatSidebar` and lacks `workflow-topbar`.

- [ ] **Step 3: Commit root shell change**

```bash
git add harness-engineering-py/frontend/src/App.vue
git commit -m "feat: replace top nav with app shell" \
  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Simplify Workflow Chat Layout and Add Top Bar

**Files:**
- Modify: `harness-engineering-py/frontend/src/components/workflow/ChatLayout.vue`

- [ ] **Step 1: Replace `ChatLayout.vue`**

Replace `src/components/workflow/ChatLayout.vue` with:

```vue
<template>
  <div class="chat-layout">
    <header class="workflow-topbar">
      <div class="session-meta">
        <h1 class="session-title">{{ currentSessionTitle }}</h1>
        <span class="session-subtitle">OpenCode 工作流</span>
      </div>
      <div class="model-select">
        <span class="model-label">模型</span>
        <el-select v-model="modelValue" size="small" @change="onModelChange" class="model-selector">
          <el-option
            v-for="m in (engineInfo?.models || [])"
            :key="m.id"
            :label="m.name"
            :value="m.id"
          />
        </el-select>
      </div>
    </header>

    <div class="chat-main">
      <ChatStream
        :messages="messages"
        @resolve-permission="(reqId, optId) => $emit('resolvePermission', reqId, optId)"
      />
      <ChatInput
        :is-streaming="isStreaming"
        @send="$emit('sendMessage', $event)"
        @cancel="$emit('cancelStream')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { ChatSession, ChatMessage, EngineAvailability } from '@/types/chat'
import { useEngineStore } from '@/stores/engine'
import ChatStream from './ChatStream.vue'
import ChatInput from './ChatInput.vue'

const props = defineProps<{
  sessions: ChatSession[]
  currentSessionId: string | null
  model: string
  messages: ChatMessage[]
  isStreaming: boolean
}>()

const emit = defineEmits<{
  modelChange: [model: string]
  sendMessage: [content: string]
  resolvePermission: [requestId: string, optionId: string]
  cancelStream: []
}>()

const engineStore = useEngineStore()
const engineInfo = ref<EngineAvailability | null>(null)
const modelValue = ref(props.model)

const currentSessionTitle = computed(() => {
  const session = props.sessions.find(s => s.id === props.currentSessionId)
  return session?.title || '新对话'
})

watch(() => props.model, (val) => { modelValue.value = val })

onMounted(async () => {
  await engineStore.fetchAvailability()
  engineInfo.value = engineStore.engineInfo
  if (engineInfo.value?.defaultModel && !props.model) {
    emit('modelChange', engineInfo.value.defaultModel)
  }
})

function onModelChange(val: string) {
  emit('modelChange', val)
}
</script>

<style scoped>
.chat-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #f7f7f4;
}
.workflow-topbar {
  height: 64px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 24px;
  border-bottom: 1px solid var(--el-border-color-extra-light);
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(10px);
}
.session-meta {
  min-width: 0;
}
.session-title {
  margin: 0;
  font-size: 16px;
  font-weight: 650;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.session-subtitle {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.model-select {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.model-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.model-selector {
  width: 220px;
}
.chat-main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
@media (max-width: 900px) {
  .workflow-topbar {
    padding: 0 14px;
  }
  .model-selector {
    width: 160px;
  }
}
</style>
```

- [ ] **Step 2: Run focused verification**

Run:

```bash
cd harness-engineering-py/frontend
npm run verify:sidebar-layout
```

Expected: PASS with `Sidebar layout source checks passed` if Tasks 1-6 are complete.

- [ ] **Step 3: Run build**

Run:

```bash
cd harness-engineering-py/frontend
npm run build
```

Expected: may FAIL because `WorkflowView.vue` still emits now-removed `selectSession`, `newSession`, and `deleteSession` handlers to `ChatLayout`. Fix in Task 7.

- [ ] **Step 4: Commit layout simplification**

```bash
git add harness-engineering-py/frontend/src/components/workflow/ChatLayout.vue
git commit -m "feat: simplify workflow chat layout" \
  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Update Chat Stream Done Callback

**Files:**
- Modify: `harness-engineering-py/frontend/src/composables/useChatStream.ts`

- [ ] **Step 1: Add optional `onDone` callback to options**

Modify the `UseChatStreamOptions` interface:

```ts
interface UseChatStreamOptions {
  sessionId: string
  model: string
  agentSessionId?: string
  onAgentSessionIdChange?: (id: string) => void
  onDone?: () => void | Promise<void>
}
```

- [ ] **Step 2: Call `onDone` when stream finishes**

In the existing `done` event listener, replace it with this version:

```ts
es.addEventListener('done', async (e) => {
  const data = JSON.parse(e.data)
  if (data.sessionId && options.onAgentSessionIdChange) {
    options.onAgentSessionIdChange(data.sessionId)
  }
  updateAssistant(assistantMsgId, { isStreaming: false })
  isStreaming.value = false
  await options.onDone?.()
  es.close()
  eventSource = null
})
```

Leave the rest of `useChatStream.ts` unchanged.

- [ ] **Step 3: Run build**

Run:

```bash
cd harness-engineering-py/frontend
npm run build
```

Expected: still may FAIL until WorkflowView emits are updated in Task 8. There should be no error from `useChatStream.ts`.

- [ ] **Step 4: Commit stream callback change**

```bash
git add harness-engineering-py/frontend/src/composables/useChatStream.ts
git commit -m "feat: refresh sessions after chat stream completion" \
  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: Refactor WorkflowView to Use Store Actions

**Files:**
- Modify: `harness-engineering-py/frontend/src/views/WorkflowView.vue`

- [ ] **Step 1: Replace `WorkflowView.vue`**

Replace `src/views/WorkflowView.vue` with:

```vue
<template>
  <div class="workflow-page">
    <ChatLayout
      :sessions="chatStore.sessions"
      :current-session-id="chatStore.currentSessionId"
      :model="chatStore.model"
      :messages="chatMessages"
      :is-streaming="isStreaming"
      @model-change="handleModelChange"
      @send-message="handleSendMessage"
      @resolve-permission="handleResolvePermission"
      @cancel-stream="handleCancelStream"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import ChatLayout from '@/components/workflow/ChatLayout.vue'
import { useChatStore } from '@/stores/chat'
import { useChatStream } from '@/composables/useChatStream'
import type { ChatMessage } from '@/types/chat'

const chatStore = useChatStore()

const {
  messages,
  isStreaming,
  sendMessage,
  resolvePermission,
  cancelStream,
} = useChatStream({
  get sessionId() { return chatStore.currentSessionId || '' },
  get model() { return chatStore.model },
  get agentSessionId() { return chatStore.agentSessionId },
  onAgentSessionIdChange(id: string) {
    chatStore.setAgentSessionId(id)
  },
  async onDone() {
    await chatStore.loadSessions()
  },
})

const chatMessages = ref<ChatMessage[]>(messages.value || [])

watch(messages, (val) => {
  chatMessages.value = val
  chatStore.messages = val
}, { deep: true })

watch(() => chatStore.messages, (val) => {
  if (val !== messages.value) {
    messages.value = val
  }
}, { deep: true })

onMounted(async () => {
  await chatStore.loadSessions()
})

function handleModelChange(model: string) {
  chatStore.setModel(model)
}

async function handleSendMessage(content: string) {
  if (!chatStore.currentSessionId) {
    await chatStore.createSession()
  }
  await sendMessage(content)
}

function handleResolvePermission(requestId: string, optionId: string) {
  resolvePermission(requestId, optionId)
}

function handleCancelStream() {
  cancelStream()
}
</script>

<style scoped>
.workflow-page {
  height: 100%;
}
</style>
```

- [ ] **Step 2: Run build**

Run:

```bash
cd harness-engineering-py/frontend
npm run build
```

Expected: PASS or reveal TypeScript issues in direct Pinia ref assignment. If TypeScript complains about assigning `chatStore.messages = val`, update the store with a `setMessages(nextMessages: ChatMessage[])` action and call that instead.

- [ ] **Step 3: If needed, add `setMessages` to store**

Only do this if Step 2 reports assignment/type issues. Add this function inside `src/stores/chat.ts`:

```ts
function setMessages(nextMessages: ChatMessage[]) {
  messages.value = nextMessages
}
```

Return it from the store:

```ts
return {
  sessions,
  currentSessionId,
  messages,
  isStreaming,
  pendingPermission,
  model,
  agentSessionId,
  setSessions,
  loadSessions,
  selectSession,
  createSession,
  deleteSession,
  clearSession,
  setModel,
  setAgentSessionId,
  setMessages,
}
```

Then replace in `WorkflowView.vue`:

```ts
chatStore.messages = val
```

with:

```ts
chatStore.setMessages(val)
```

- [ ] **Step 4: Run focused verification**

Run:

```bash
cd harness-engineering-py/frontend
npm run verify:sidebar-layout
```

Expected: PASS with `Sidebar layout source checks passed`.

- [ ] **Step 5: Commit WorkflowView refactor**

```bash
git add harness-engineering-py/frontend/src/views/WorkflowView.vue harness-engineering-py/frontend/src/stores/chat.ts
git commit -m "feat: wire workflow to shared chat store" \
  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 9: Final Build and Manual Verification

**Files:**
- Verify only; no source changes expected unless checks fail.

- [ ] **Step 1: Run source contract verification**

Run:

```bash
cd harness-engineering-py/frontend
npm run verify:sidebar-layout
```

Expected:

```text
Sidebar layout source checks passed
```

- [ ] **Step 2: Run production build**

Run:

```bash
cd harness-engineering-py/frontend
npm run build
```

Expected: `vue-tsc` and `vite build` complete successfully.

- [ ] **Step 3: Start backend**

Run in one terminal:

```bash
cd harness-engineering-py/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected: FastAPI starts on `http://localhost:8000`.

- [ ] **Step 4: Start frontend**

Run in another terminal:

```bash
cd harness-engineering-py/frontend
npm run dev
```

Expected: Vite starts on `http://localhost:3000`.

- [ ] **Step 5: Manual browser checks**

Open `http://localhost:3000/` and verify:

1. `/` redirects to `/workflow`.
2. The old top navigation is gone.
3. The left sidebar shows Harness, Skills, Agents, history area, theme toggle, collapse control.
4. There is no primary Workflow nav item.
5. Clicking Skills routes to `/skills`.
6. Clicking Agents routes to `/agents`.
7. Clicking the brand area routes to `/workflow`.
8. Collapse button changes the sidebar to icon-only width.
9. History titles are visible only while expanded.
10. The Workflow page does not show the old internal `ChatSidebar`.
11. Workflow top bar shows `新对话` when no session is selected.
12. Model selector is available in the Workflow top bar.
13. Clicking `+` in history creates a new session and routes to Workflow.
14. Sending a first message without a selected session creates a session before streaming.
15. After a response finishes, the history list updates.
16. Deleting the current session clears the chat area.

- [ ] **Step 6: Commit any final fixes**

If Step 5 required small fixes, commit them:

```bash
git add harness-engineering-py/frontend

git commit -m "fix: polish sidebar workflow interactions" \
  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
```

If no fixes were needed, skip this commit.

---

## Self-Review

### Spec Coverage

- Default `/workflow` route: Task 2.
- Left app sidebar: Task 4 and Task 5.
- Skills/Agents only primary nav: Task 4 and verification script.
- Collapsible icon-only behavior: Task 4.
- Bottom history section: Task 4.
- Shared session store: Task 3.
- Workflow without internal `ChatSidebar`: Task 6.
- Model selector in top bar: Task 6.
- First-message auto session creation: Task 8.
- Refresh history after done: Task 7 and Task 8.
- Build/manual verification: Task 9.

### Placeholder Scan

No `TBD`, `TODO`, `implement later`, or unspecified test steps are intentionally left in this plan. Commands and expected outcomes are specified for each task.

### Type Consistency

The plan consistently uses existing types from `src/types/chat.ts`: `ChatSession`, `ChatMessage`, `PermissionRequest`, and `EngineAvailability`. Store action names introduced in Task 3 are reused by `AppSidebar.vue` and `WorkflowView.vue` in later tasks.
