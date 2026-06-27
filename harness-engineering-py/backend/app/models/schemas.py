from pydantic import BaseModel
from typing import Optional, List


class PermissionOption(BaseModel):
    id: str
    label: str
    style: str = "default"  # "primary" | "danger" | "default"


class PermissionRequest(BaseModel):
    id: str
    type: str
    description: str
    detail: str
    options: List[PermissionOption] = []
    timestamp: str


class ToolCall(BaseModel):
    name: str
    input: str
    output: Optional[str] = None


class ChatMessage(BaseModel):
    id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    thoughtContent: Optional[str] = None
    timestamp: str
    toolCalls: Optional[List[ToolCall]] = None
    permissionRequest: Optional[PermissionRequest] = None
    permissionDecision: Optional[dict] = None
    isStreaming: Optional[bool] = None


class DiagnosisResult(BaseModel):
    code: str
    name: str = ""
    conclusion: Optional[str] = None  # "看多" | "看空" | "观望" | None(失败)
    reason: str = ""
    close: Optional[float] = None
    open: Optional[float] = None
    pct_chg: Optional[float] = None
    ema20: Optional[float] = None
    error: Optional[str] = None
    source: Optional[str] = None
    klinePath: Optional[str] = None  # K 线 CSV 文件路径（相对 session 目录）
    klineDate: Optional[str] = None  # 最近一根 K 线日期


class StockDiagnosis(BaseModel):
    codes: List[str] = []
    sector: Optional[str] = None  # 板块代码（如果是按板块分析）
    days: int = 90
    skills: List[str] = []
    skillNames: List[str] = []  # 已解析的 skill 名称（与 skills 一一对应）
    initialPrompt: str = ""  # 传给 OpenCode 的初始提示词模板（第一条股票的实际 prompt，方便调试）
    results: List[DiagnosisResult] = []
    successCount: int = 0
    failedCount: int = 0


class ChatSession(BaseModel):
    id: str
    type: str = "chat"  # "chat" | "stock_diagnosis"
    title: str
    engine: str
    model: str
    agentSessionId: Optional[str] = None
    messages: List[ChatMessage] = []
    diagnosis: Optional[StockDiagnosis] = None  # 仅 stock_diagnosis 类型
    createdAt: str
    updatedAt: str


class ModelInfo(BaseModel):
    id: str
    name: str


class EngineAvailability(BaseModel):
    available: bool
    name: str
    version: Optional[str] = None
    models: List[ModelInfo] = []
    defaultModel: Optional[str] = None


# Request/Response models

class SendMessageRequest(BaseModel):
    message: str
    model: str
    sessionId: str
    agentSessionId: Optional[str] = None


class CreateSessionRequest(BaseModel):
    engine: Optional[str] = None
    model: Optional[str] = None


class DeleteSessionRequest(BaseModel):
    id: str


class ResolvePermissionRequest(BaseModel):
    requestId: str
    optionId: str


class StockAnalyzeRequest(BaseModel):
    codes: List[str] = []
    sector: Optional[str] = None  # 板块代码，如 BK1036（与 codes 互斥，优先 sector）
    days: int = 90
    skills: List[str] = []
    sessionId: Optional[str] = None
    model: Optional[str] = None  # 不填则使用 opencode 默认模型


class StreamState:
    """内存中的流状态（非 Pydantic 模型）"""
    def __init__(self, chat_id: str, frontend_session_id: str, engine: str):
        self.chat_id = chat_id
        self.frontend_session_id = frontend_session_id
        self.engine = engine
        self.stream_content = ""
        self.status = "running"  # "running" | "completed" | "failed" | "killed"
