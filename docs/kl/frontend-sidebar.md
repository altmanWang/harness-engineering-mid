# 前端 — 侧边栏 (AppSidebar)

## 文件

`frontend/src/components/layout/AppSidebar.vue`

## 结构

```
┌─────────────────────┐
│ H  Harness (brand)  │  ← 点击回到首页 /
├─────────────────────┤
│ ★ Skills            │  ← 导航: /skills
│ ◆ Agents            │  ← 导航: /agents
├─────────────────────┤
│ 🕐 历史会话    [+]   │  ← 最近 8 条会话
│  ├ 会话标题1    [×] │
│  ├ 会话标题2    [×] │
│  └ ...              │
├─────────────────────┤
│ EngineInfo (模型)   │  ← 引擎/模型选择
├─────────────────────┤
│ ☀ 🌓 (主题/折叠)   │  ← 底部操作栏
└─────────────────────┘
```

## 关键逻辑

### 导航项定义 (硬编码)

```html
<nav class="sidebar-nav">
  <div class="nav-item" @click="go('/skills')"> ... </div>
  <div class="nav-item" @click="go('/agents')"> ... </div>
</nav>
```

**添加新导航项需要**: 在此模板中添加 `<div class="nav-item">`，并在 `activeRoute` computed 中增加路径匹配。

### 路由激活检测

```ts
const activeRoute = computed(() => {
  if (route.path.startsWith('/skills')) return '/skills'
  if (route.path.startsWith('/agents')) return '/agents'
  return ''
})
```

### 历史会话

- 数据源: `chatStore.sessions` (Pinia)
- 显示条数: 最多 8 条 (`slice(0, 8)`)
- 排序: 由 `loadSessions()` 后端返回 (按 updatedAt 降序)
- 操作: 点击选中 → `chatStore.selectSession(id)` + 跳转 `/`；删除 → `chatStore.deleteSession(id)`
- 新建: `chatStore.createSession()` + 跳转 `/`
- 空态: "暂无会话"

### 折叠行为

- `isCollapsed` ref (默认 false)
- 折叠时宽度 64px (仅图标), 展开时 248px
- 移动端 (<900px) 强制折叠
- 折叠时隐藏: 文字标签、历史会话列表、EngineInfo、新建按钮

### 生命周期

```ts
onMounted(async () => {
  chatStore.loadSessions()       // 加载会话列表
  await engineStore.fetchAvailability()  // 加载引擎/模型信息
  availableModels.value = engineStore.engineInfo?.models || []
})
```

## 样式要点

- 背景: `rgba(255, 255, 255, 0.85)` 半透明
- 宽度过渡: `transition: width 0.18s ease`
- 导航项: 40px 高, 12px 圆角, hover 时背景变亮
- 历史列表: max-height 260px, overflow-y auto
- 删除按钮: 默认 opacity 0, hover 时显示
- 底部操作栏: border-top 分割线
