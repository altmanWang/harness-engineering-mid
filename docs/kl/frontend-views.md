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

---

## StockView (`views/StockView.vue`)

智能诊股页面，结构:

```
┌──────────────────────────────────────────────────┐
│ 智能诊股                                         │
├──────────────────────────────────────────────────┤
│ [StockInput: 搜索 + 手动代码输入 + 天数 + Skills] │
├──────────────────────────────────────────────────┤
│ [进度条: 成功/失败/待分析统计]                    │
├──────────────────────────────────────────────────┤
│ [StockResultTable: 诊股结果表格]                  │
│   - 代码/名称/结论(看多/看空/观望)/理由           │
│   - 收盘价/开盘价/涨跌幅/EMA20                    │
│   - K线日期/详情按钮                              │
├──────────────────────────────────────────────────┤
│ [追问 AI] 按钮                                   │
└──────────────────────────────────────────────────┘
```

### 核心流程

1. 用户通过 `StockInput` 搜索股票或手动输入代码
2. 选择分析天数 (30/60/90/180) 和 Skills
3. 点击"开始诊股" → `useStockAnalysis.startAnalysis()`
4. POST `/api/stock/analyze` → 获取 `analysisId`
5. EventSource GET `/api/stock/stream?analysisId=...` → 逐只推送 SSE 结果
6. `StockResultTable` 实时更新每只股票的状态 (pending → analyzing → done/error)
7. 点击详情 → `KLineChart` 弹窗显示 ECharts K 线图
8. 对比模式: URL 参数 `?compare=id1,id2` → `StockCompare` 并排对比

### 数据流

```
StockInput → useStockAnalysis.startAnalysis(codes, days, skills, sessionId)
  → POST /api/stock/analyze → { analysisId, sessionId }
  → EventSource GET /api/stock/stream?analysisId=...
    → SSE events: start → stock_result → stock_error → done
      → stockItems ref 实时更新 → StockResultTable 渲染
```

### 关键 Composable: `useStockAnalysis`

- `stockItems`: `Ref<StockItem[]>` — 每只股票的分析状态
- `startAnalysis(codes, days, skills, sessionId)` — 发起诊股
- `suppress(sessionId)` — 暂停实时 SSE（切换到历史 session）
- `resume(sessionId)` — 恢复实时 SSE（切换回活跃 session）
- 用于 StockView 和 AppSidebar 对比模式的 session 切换
