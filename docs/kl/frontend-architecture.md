# 前端架构总览

## 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | Vue 3 (Composition API + `<script setup>`) |
| 构建 | Vite |
| 路由 | Vue Router 4 (createWebHistory) |
| 状态管理 | Pinia |
| UI 组件库 | Element Plus |
| 图标 | @element-plus/icons-vue |
| CSS | Scoped CSS (无 Tailwind/预处理器) |

## 目录结构

```
frontend/src/
├── App.vue                    # 根布局: AppSidebar + <router-view>
├── main.ts                    # createApp + router + pinia
├── router/index.ts            # 路由定义 (3 条)
├── stores/
│   ├── chat.ts                # 会话 & 消息状态
│   └── engine.ts              # 引擎可用性状态
├── composables/
│   ├── useChatStream.ts       # SSE 流式聊天逻辑
│   └── useMarketFilter.ts     # 搜索/标签过滤
├── types/
│   ├── index.ts               # Skill, Agent, MarketItem
│   └── chat.ts                # ChatMessage, ChatSession, EngineAvailability
├── mock/data.ts               # Agents 静态 mock 数据
├── views/
│   ├── HomeView.vue           # 首页 (LandingHero ↔ ChatLayout)
│   ├── SkillsView.vue         # Skills 管理页
│   └── AgentsView.vue         # Agents 市场页
└── components/
    ├── layout/
    │   ├── AppSidebar.vue     # 左侧边栏
    │   └── Navbar.vue         # (未使用) 旧版顶部导航
    ├── workflow/
    │   ├── LandingHero.vue    # 欢迎页 (会话未开始)
    │   ├── ChatLayout.vue     # 聊天主布局
    │   ├── ChatInput.vue      # 输入框
    │   ├── ChatMessage.vue    # 单条消息渲染
    │   ├── ChatStream.vue     # 消息列表
    │   ├── ChatSidebar.vue    # (未使用) 完整会话侧栏
    │   ├── EngineInfo.vue     # 引擎/模型选择器
    │   ├── PermissionCard.vue # 权限请求卡片
    │   ├── PromptCards.vue    # 提示卡片
    │   ├── ThoughtBlock.vue   # 思考内容块
    │   └── ToolCallCard.vue   # 工具调用卡片
    ├── skills/
    │   ├── SkillCard.vue      # Skill 卡片
    │   ├── SkillFilter.vue    # Skill 筛选栏
    │   └── SkillUploadDialog.vue # 上传对话框
    └── agents/
        ├── AgentCard.vue      # Agent 卡片
        └── AgentFilter.vue    # Agent 筛选栏
```

## 路由表

| Path | Name | Component | 说明 |
|------|------|-----------|------|
| `/` | Home | HomeView.vue (lazy) | 聊天首页 |
| `/skills` | Skills | SkillsView.vue (lazy) | Skill 管理 |
| `/agents` | Agents | AgentsView.vue (lazy) | Agent 市场 |

## 布局 (App.vue)

```
┌──────────────────────────────────────┐
│ ┌──────────┐ ┌─────────────────────┐ │
│ │          │ │                     │ │
│ │ Sidebar  │ │   <router-view>     │ │
│ │ (248px)  │ │   (flex: 1)        │ │
│ │          │ │                     │ │
│ └──────────┘ └─────────────────────┘ │
└──────────────────────────────────────┘
```

- `.app-shell`: flex row, 100% height, `#f5f5f1` 背景
- `.app-main`: flex 1, 100vh, overflow auto
- 侧边栏: 248px 默认, 64px 折叠, 移动端 (<900px) 自动折叠

## 数据流概览

```
User Input → ChatInput.vue
  → HomeView.handleSendMessage()
    → useChatStream.sendMessage()
      → POST /api/chat/stream
      → EventSource GET /api/chat/stream?id=<chatId>
        → SSE events → messages ref 更新
          → ChatStream.vue → ChatMessage.vue 渲染
```

## 开发命令

```bash
cd frontend
npm install        # node_modules ~700MB
npm run dev        # 默认 :3000, 代理 /api → :8000
npm run build      # 生产构建
```
