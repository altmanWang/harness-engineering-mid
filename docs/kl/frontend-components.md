# 前端 — 组件清单

共 22 个 Vue 组件，按目录分类:

## layout/ (布局)

| 组件 | 文件 | 使用状态 | 职责 |
|------|------|---------|------|
| `AppSidebar` | `AppSidebar.vue` | **使用中** (App.vue) | 左侧导航栏、历史会话、引擎信息 |
| `Navbar` | `Navbar.vue` | **未使用** | 旧版顶部导航 (el-menu 水平布局) |

## workflow/ (聊天工作流)

| 组件 | 文件 | 使用状态 | 职责 |
|------|------|---------|------|
| `LandingHero` | `LandingHero.vue` | HomeView | 欢迎页: 输入框 + 模型选择 + 技能选择 + 提示卡片 |
| `ChatLayout` | `ChatLayout.vue` | HomeView | 聊天主布局: 消息列表 + 输入框 |
| `ChatInput` | `ChatInput.vue` | LandingHero, ChatLayout | 消息输入框 + 发送/取消按钮 |
| `ChatMessage` | `ChatMessage.vue` | ChatStream | 单条消息渲染: 用户/助手/系统角色 |
| `ChatStream` | `ChatStream.vue` | ChatLayout | 消息列表容器 + 自动滚动 |
| `ChatSidebar` | `ChatSidebar.vue` | **未使用** | 完整会话侧栏 (独立组件, 未在任何 view 中渲染) |
| `EngineInfo` | `EngineInfo.vue` | AppSidebar | 引擎名称 + 模型下拉选择器 |
| `PermissionCard` | `PermissionCard.vue` | ChatMessage | 权限请求卡片: 选项按钮 (允许/拒绝) |
| `PromptCards` | `PromptCards.vue` | LandingHero | 预设提示词卡片 |
| `ThoughtBlock` | `ThoughtBlock.vue` | ChatMessage | 可折叠的 AI 思考内容块 |
| `ToolCallCard` | `ToolCallCard.vue` | ChatMessage | 工具调用展示: 名称/输入/输出 |

## skills/ (技能管理)

| 组件 | 文件 | 使用状态 | 职责 |
|------|------|---------|------|
| `SkillCard` | `SkillCard.vue` | SkillsView | Skill 卡片: 名称/描述/标签/删除 |
| `SkillFilter` | `SkillFilter.vue` | SkillsView | 标签多选 + 搜索框 |
| `SkillUploadDialog` | `SkillUploadDialog.vue` | SkillsView | 上传对话框: name/description/tags/file |

## agents/ (Agent 市场)

| 组件 | 文件 | 使用状态 | 职责 |
|------|------|---------|------|
| `AgentCard` | `AgentCard.vue` | AgentsView | Agent 卡片: 名称/描述/标签/使用次数 |
| `AgentFilter` | `AgentFilter.vue` | AgentsView | 标签多选 + 搜索框 |

## stock/ (智能诊股)

| 组件 | 文件 | 使用状态 | 职责 |
|------|------|---------|------|
| `StockInput` | `StockInput.vue` | StockView | 股票搜索、手动输入代码、天数选择、Skills 多选 |
| `StockResultTable` | `StockResultTable.vue` | StockView | 诊股结果表格: 结论/价格/涨跌幅/详情，底部统计 |
| `KLineChart` | `KLineChart.vue` | StockResultTable | ECharts K 线图弹窗: 蜡烛图 + EMA20 + 成交量 |
| `StockCompare` | `StockCompare.vue` | StockView | 多会话诊股结果并排对比，高亮结论变化 |

## 组件依赖关系

```
App.vue
└── AppSidebar
    └── EngineInfo

HomeView
├── LandingHero
│   ├── ChatInput
│   ├── PromptCards
│   └── (model/skill selectors inline)
└── ChatLayout
    ├── ChatStream
    │   └── ChatMessage
    │       ├── ThoughtBlock
    │       ├── ToolCallCard
    │       └── PermissionCard
    └── ChatInput

SkillsView
├── SkillFilter
├── SkillCard
└── SkillUploadDialog

AgentsView
├── AgentFilter
└── AgentCard

StockView
├── StockInput
├── StockResultTable
│   └── KLineChart
└── StockCompare
```
