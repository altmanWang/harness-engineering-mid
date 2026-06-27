# Harness Engineering

代码入口harness-engineering-py

## 构建 & 启动

### 后端（先启动）

```bash
cd harness-engineering-py/backend
pip install -r requirements.txt    # 安装 Python 依赖
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

- 默认端口 **8000**，API 文档自动生成在 http://localhost:8080/docs
- 依赖系统已安装 `opencode` CLI，后端通过 ACP 协议与 OpenCode 子进程通信
- 会话数据存储在 `./data/chat-sessions/`（相对于后端启动目录）
- 无 `.env` 文件，无需环境变量配置

### 前端

```bash
cd harness-engineering-py/frontend
npm install        # node_modules ~700MB
npm run dev        # next dev，默认端口 3000，首页自动跳转 /dashboard
npm run build      # next build，生产构建
npm run start      # next start，运行生产服务
```
