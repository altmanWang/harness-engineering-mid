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
    conclusion: Optional[str] = None  # "买入" | "观望" | None(失败)
    reason: str = ""
    close: Optional[float] = None
    open: Optional[float] = None
    pct_chg: Optional[float] = None
    ema20: Optional[float] = None
    error: Optional[str] = None
    source: Optional[str] = None
    klinePath: Optional[str] = None  # K 线 CSV 文件路径（相对 session 目录）
    klineDate: Optional[str] = None  # 最近一根 K 线日期
    backtestBarsPath: Optional[str] = None     # 回测 bars CSV 相对路径
    backtestSummaryPath: Optional[str] = None  # 回测 summary JSON 相对路径


class BacktestSummary(BaseModel):
    stock_code: str
    stock_name: str
    initial_capital: float = 20000.0
    final_capital: float = 0.0
    total_return: float = 0.0       # 总收益率 (%)
    max_drawdown: float = 0.0       # 最大回撤 (%)
    win_rate: float = 0.0           # 胜率 (%)
    trade_count: int = 0            # 交易次数


class BacktestBar(BaseModel):
    date: str
    stock_name: str = ""
    open: float = 0.0
    close: float = 0.0
    signal: Optional[str] = None    # "买入" | "卖出" | "持有" | "观望"
    cost: Optional[float] = None
    profit: Optional[float] = None
    capital: float = 0.0
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None


class StockDiagnosis(BaseModel):
    codes: List[str] = []
    sector: Optional[str] = None  # 板块代码（如果是按板块分析）
    days: int = 90
    strategy: str = ""  # 策略 ID，如 "ema_pullback"
    strategyConfig: dict = {}  # 用户覆盖的策略配置
    skills: List[str] = []  # 保留兼容，不再使用
    skillNames: List[str] = []  # 保留兼容，不再使用
    initialPrompt: str = ""  # 保留兼容，不再使用
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
    strategy: Optional[str] = None  # 策略 ID
    strategyConfig: Optional[dict] = None  # 策略配置覆盖
    skills: List[str] = []  # 保留兼容，不再使用
    sessionId: Optional[str] = None
    model: Optional[str] = None  # 保留兼容，不再使用


class StreamState:
    """内存中的流状态（非 Pydantic 模型）"""
    def __init__(self, chat_id: str, frontend_session_id: str, engine: str):
        self.chat_id = chat_id
        self.frontend_session_id = frontend_session_id
        self.engine = engine
        self.stream_content = ""
        self.status = "running"  # "running" | "completed" | "failed" | "killed"
