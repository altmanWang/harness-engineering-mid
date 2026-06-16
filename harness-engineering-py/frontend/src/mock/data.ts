import type { Skill, Agent } from "@/types"

export const skills: Skill[] = [
  { id: "s1", name: "代码生成", description: "根据需求描述自动生成代码片段和函数实现", tags: ["代码生成"], icon: "Code", usageCount: 2340, lastUsedAt: "2026-05-27T10:30:00Z" },
  { id: "s2", name: "单元测试", description: "自动为指定函数生成单元测试用例", tags: ["测试"], icon: "TestTube", usageCount: 1890, lastUsedAt: "2026-05-27T09:15:00Z" },
  { id: "s3", name: "代码审查", description: "AI 驱动的代码审查，发现潜在问题和优化建议", tags: ["代码生成"], icon: "Search", usageCount: 1560, lastUsedAt: "2026-05-26T16:45:00Z" },
  { id: "s4", name: "文档生成", description: "自动生成 API 文档和代码注释", tags: ["文档"], icon: "FileText", usageCount: 1200, lastUsedAt: "2026-05-26T14:20:00Z" },
  { id: "s5", name: "自动部署", description: "一键部署应用到指定环境", tags: ["部署"], icon: "Rocket", usageCount: 980, lastUsedAt: "2026-05-25T11:00:00Z" },
  { id: "s6", name: "数据迁移", description: "数据库 schema 迁移和数据转换工具", tags: ["数据", "部署"], icon: "Database", usageCount: 760, lastUsedAt: "2026-05-24T15:30:00Z" },
  { id: "s7", name: "性能分析", description: "分析代码性能瓶颈并提供优化建议", tags: ["代码生成"], icon: "Gauge", usageCount: 650, lastUsedAt: "2026-05-23T10:00:00Z" },
  { id: "s8", name: "接口测试", description: "自动生成 API 接口测试脚本", tags: ["测试"], icon: "Webhook", usageCount: 580, lastUsedAt: "2026-05-22T09:30:00Z" },
  { id: "s9", name: "安全扫描", description: "扫描代码中的安全漏洞和敏感信息泄露", tags: ["安全"], icon: "Shield", usageCount: 520, lastUsedAt: "2026-05-21T14:00:00Z" },
  { id: "s10", name: "日志分析", description: "智能分析应用日志，定位异常和错误", tags: ["数据"], icon: "ScrollText", usageCount: 450, lastUsedAt: "2026-05-20T16:30:00Z" },
  { id: "s11", name: "依赖管理", description: "检测项目依赖更新和版本冲突", tags: ["部署"], icon: "Package", usageCount: 380, lastUsedAt: "2026-05-19T11:15:00Z" },
  { id: "s12", name: "配置生成", description: "根据项目类型生成配置文件模板", tags: ["文档"], icon: "Settings", usageCount: 310, lastUsedAt: "2026-05-18T08:45:00Z" },
]

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

export const skillTags: string[] = [...new Set(skills.flatMap(s => s.tags))]
export const agentTags: string[] = [...new Set(agents.flatMap(a => a.tags))]
