# 前端 — 视图层 (Views)

## HomeView (`views/HomeView.vue`)

聊天首页，根据是否有活跃会话切换两种视图:

```
isLanding (无会话 或 无消息)
  → <LandingHero>  欢迎页 + 输入框 + 提示卡片

!isLanding (有会话 且有消息)
  → <ChatLayout>   聊天界面
```

### Props 传递

**LandingHero 接收**: isStreaming, model, models, skills, selectedSkillId
**ChatLayout 接收**: sessions, currentSessionId, model, models, messages, isStreaming, skills, selectedSkillId

### 事件处理

| 事件 | 处理函数 | 说明 |
|------|---------|------|
| `@send` (LandingHero) | `handleFirstSend` | 创建会话 → 发送消息 |
| `@send-message` (ChatLayout) | `handleSendMessage` | 确保会话存在 → 发送 |
| `@model-change` | `handleModelChange` | chatStore.setModel() |
| `@skill-change` | `handleSkillChange` | POST /api/skills/{id}/load |
| `@resolve-permission` | `handleResolvePermission` | 转发到 useChatStream |
| `@cancel-stream` | `handleCancelStream` | 转发到 useChatStream |

### Skill 加载流程

1. `onMounted` → `loadSkills()` → GET /api/skills
2. 用户在 LandingHero/ChatLayout 选择 skill → `handleSkillChange(skillId)`
3. 如果有活跃会话 → POST `/api/skills/{skillId}/load?sessionId=...`

---

## SkillsView (`views/SkillsView.vue`)

Skill 管理页面，结构:

```
┌─────────────────────────────────────┐
│ Skills 管理            [上传 Skill] │
├─────────────────────────────────────┤
│ [标签筛选] [搜索框]                 │
├─────────────────────────────────────┤
│ ┌────────┐ ┌────────┐ ┌────────┐   │
│ │ Skill  │ │ Skill  │ │ Skill  │   │
│ │ Card   │ │ Card   │ │ Card   │   │
│ └────────┘ └────────┘ └────────┘   │
└─────────────────────────────────────┘
```

- 数据源: `GET /api/skills`
- 筛选: 标签多选 + 搜索关键词 (名称/描述)
- 上传: `SkillUploadDialog` 组件 (multipart form: name, description, tags, file.zip)
- 删除: SkillCard 内部 `@deleted` → 从列表移除

---

## AgentsView (`views/AgentsView.vue`)

Agent 市场页面，结构类似 SkillsView:

```
┌─────────────────────────────────────┐
│ Agents 市场                         │
├─────────────────────────────────────┤
│ [标签筛选] [搜索框]                 │
├─────────────────────────────────────┤
│ ┌────────┐ ┌────────┐ ┌────────┐   │
│ │ Agent  │ │ Agent  │ │ Agent  │   │
│ │ Card   │ │ Card   │ │ Card   │   │
│ └────────┘ └────────┘ └────────┘   │
└─────────────────────────────────────┘
```

- 数据源: `@/mock/data.ts` (静态 mock 数据, **非 API**)
- 筛选: 使用 `useMarketFilter` composable
- 无 CRUD 操作 (只读展示)
