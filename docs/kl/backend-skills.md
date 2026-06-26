# 后端 — Skill 管理

## 文件

- Router: `backend/app/routers/skills.py`
- Service: `backend/app/services/skill_store.py`

## API 端点

| Method | Path | 说明 |
|--------|------|------|
| `GET` | `/api/skills` | 列出所有 Skill 元数据 |
| `POST` | `/api/skills` | 上传 Skill (multipart form) |
| `GET` | `/api/skills/{id}/download` | 下载 Skill ZIP |
| `DELETE` | `/api/skills/{id}` | 删除 Skill |
| `POST` | `/api/skills/{id}/load` | 加载 Skill 到 worktree |

## 上传 (POST /api/skills)

### 请求 (multipart/form-data)

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | Skill 名称 |
| `description` | string | 描述 |
| `tags` | string | 逗号分隔的标签 |
| `file` | file | .zip 文件 |

### 校验规则

- name/description 非空
- tags 至少一个, 必须在 `ALLOWED_TAGS` 内: `{"代码开发", "DSL", "悍马平台", "数据"}`
- 文件扩展名必须为 `.zip`
- 文件内容非空

### 响应

```json
{
  "skill": {
    "id": "skill-1782304193865-1uuqfm",
    "name": "westock-data",
    "description": "获取A股数据",
    "tags": ["数据"],
    "fileName": "westock-data.zip",
    "fileSize": 12345,
    "createdAt": "2025-06-24T..."
  }
}
```

## 存储结构

```
data/
├── skills/
│   ├── metadata.json              # Skill 元数据数组
│   ├── skill-{id}.zip             # Skill ZIP 文件
│   └── skill-{id}.zip.loaded      # 加载标记 (防重复)
```

## 加载到 Worktree (POST /api/skills/{id}/load?sessionId=...)

1. 获取 Skill 元数据 → 读取 ZIP
2. 解压到 `data/worktrees/{sessionId}/.opencode/skills/{skill_name}/`
3. 创建 `.loaded` 标记文件 (防重复加载)
4. ZIP 扁平化处理: 如果 ZIP 内只有一个顶层目录, 内容上移一级

### 参数

| Query | 说明 |
|-------|------|
| `sessionId` | 目标会话 ID, 决定 worktree 路径 |

## Skill 元数据格式

```json
[
  {
    "id": "skill-1782304193865-1uuqfm",
    "name": "westock-data",
    "description": "获取A股数据",
    "tags": ["数据"],
    "fileName": "westock-data.zip",
    "fileSize": 12345,
    "createdAt": "2025-06-24T10:00:00+00:00"
  }
]
```
