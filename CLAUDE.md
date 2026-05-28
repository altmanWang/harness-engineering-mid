# Harness Engineering

Skills & Agents 市场 + 使用 Dashboard 的前端应用。

## 技术栈

- **框架**: Next.js 16 (App Router)
- **语言**: TypeScript 6
- **UI**: React 19 + Tailwind CSS 3 + lucide-react 图标
- **图表**: Recharts 3
- **AI 集成**: @anthropic-ai/claude-agent-sdk、@agentclientprotocol/sdk
- **CSS 工具**: clsx + tailwind-merge + tailwindcss-animate

## 构建 & 启动

```bash
cd harness-engineering
npm install        # node_modules ~700MB
npm run dev        # next dev，默认端口 3000，首页自动跳转 /dashboard
npm run build      # next build，生产构建
npm run start      # next start，运行生产服务
```

- `npm run dev` 首次启动会编译，按路由按需编译（首次访问某页面时才构建该路由）
- `.next` 缓存目录约 470MB，Windows 上文件 I/O 较慢，卡顿时可 `rm -rf .next` 清理后重启
- tsconfig target 当前为 es5，可考虑改为 ES2017+ 提升编译速度

## 项目结构

```
harness-engineering/src/
├── app/                    # Next.js App Router
│   ├── api/
│   │   ├── chat/stream/    # SSE 流式聊天（核心路由）
│   │   ├── chat/sessions/  # 会话管理
│   │   ├── chat/permission/# 权限请求
│   │   └── engines/        # 引擎可用性检测
│   ├── agents/             # Agents 页面
│   ├── dashboard/          # Dashboard 页面
│   ├── skills/             # Skills 页面
│   └── workflow/           # Workflow 页面
├── components/             # React 组件（14 个）
├── hooks/                  # use-chat-stream
├── lib/
│   ├── chat/               # 流状态、会话存储、权限队列
│   ├── engines/            # 引擎抽象层（opencode-wrapper、acp-engine、engine-factory）
│   ├── mock-data.ts
│   └── utils.ts
└── types/                  # TypeScript 类型定义
```

## 引擎架构

- `Engine` 接口定义在 `src/lib/engines/engine-interface.ts`
- `engine-factory.ts` 管理引擎池（Map + TTL 10分钟自动回收）
- 当前唯一实现：`OpenCodeEngineWrapper`，通过本地 OpenCode CLI 驱动
- `api/chat/stream` 通过 EventEmitter 实现 SSE 推送（text/thought/permission_request/error）

## 注意事项

- 路径别名：`@/*` 映射到 `./src/*`
- API 路由均为 `force-dynamic`
- SSE 连接使用 Map 内存存储，重启服务后会话丢失
- Windows 开发环境文件 I/O 是性能瓶颈，生产部署建议 Linux
