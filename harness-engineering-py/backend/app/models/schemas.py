from pydantic import BaseModel, Field
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


class ChatSession(BaseModel):
    id: str
    title: str
    engine: str
    model: str
    agentSessionId: Optional[str] = None
    messages: List[ChatMessage] = []
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


class StreamState:
    """内存中的流状态（非 Pydantic 模型）"""
    def __init__(self, chat_id: str, frontend_session_id: str, engine: str):
        self.chat_id = chat_id
        self.frontend_session_id = frontend_session_id
        self.engine = engine
        self.stream_content = ""
        self.status = "running"  # "running" | "completed" | "failed" | "killed"
