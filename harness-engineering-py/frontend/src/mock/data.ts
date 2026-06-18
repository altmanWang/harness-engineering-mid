import type { Skill, Agent } from "@/types"

export const agents: Agent[] = [
  { id: "a1", name: "编码助手", description: "全栈编码助手，支持代码生成、重构和调试", tags: ["编码"], icon: "Bot", usageCount: 3210, lastUsedAt: "2026-05-27T11:00:00Z" },
  { id: "a2", name: "测试助手", description: "自动化测试编排，覆盖单元、集成和 E2E 测试", tags: ["测试"], icon: "FlaskConical", usageCount: 2100, lastUsedAt: "2026-05-27T10:00:00Z" },
  { id: "a3", name: "运维助手", description: "监控、告警和自动化运维操作", tags: ["运维"], icon: "Server", usageCount: 1680, lastUsedAt: "2026-05-26T15:30:00Z" },
  { id: "a4", name: "文档助手", description: "自动生成和维护项目文档", tags: ["文档"], icon: "BookOpen", usageCount: 1200, lastUsedAt: "2026-05-25T09:00:00Z" },
  { id: "a5", name: "安全助手", description: "安全审计、合规检查和漏洞修复建议", tags: ["安全"], icon: "ShieldCheck", usageCount: 890, lastUsedAt: "2026-05-24T14:00:00Z" },
  { id: "a6", name: "数据助手", description: "数据分析、可视化和报告生成", tags: ["数据"], icon: "BarChart3", usageCount: 750, lastUsedAt: "2026-05-23T10:30:00Z" },
  { id: "a7", name: "架构助手", description: "系统架构设计和代码结构优化", tags: ["编码"], icon: "Blocks", usageCount: 620, lastUsedAt: "2026-05-22T16:00:00Z" },
  { id: "a8", name: "DevOps 助手", description: "CI/CD 流水线编排和部署管理", tags: ["运维"], icon: "GitBranch", usageCount: 540, lastUsedAt: "2026-05-21T11:30:00Z" },
]

export const agentTags: string[] = [...new Set(agents.flatMap(a => a.tags))]
