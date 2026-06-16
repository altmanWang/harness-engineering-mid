from abc import ABC, abstractmethod
from typing import Any, Callable, Dict
from dataclasses import dataclass


@dataclass
class EngineStreamEvent:
    type: str  # "text" | "thought" | "tool" | "permission_request" | "error"
    content: str
    metadata: Any = None


class Engine(ABC):
    @abstractmethod
    def get_name(self) -> str: ...

    @abstractmethod
    async def execute(self, options: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    def cancel(self) -> None: ...

    @abstractmethod
    async def is_available(self) -> bool: ...

    @abstractmethod
    def resolve_permission(self, option_id: str) -> None: ...

    @abstractmethod
    def on(self, event: str, listener: Callable[..., Any]) -> None: ...

    @abstractmethod
    def off(self, event: str, listener: Callable[..., Any]) -> None: ...
