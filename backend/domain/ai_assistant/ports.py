from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class LlmResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    latency_ms: int
    attempts: int


class LlmGateway(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> LlmResult:
        """Llama al modelo. Lanza las subclases de domain.ai_assistant.errors.LlmError."""


class AiCallLog(ABC):
    """Bitacora de llamadas al LLM (exitosas o fallidas)."""

    @abstractmethod
    def record(self, **fields) -> int:
        """Guarda la llamada (y la confirma de inmediato) y devuelve su id."""

    @abstractmethod
    def api_calls_since(self, user_id: int, since: datetime) -> tuple[int, Optional[datetime]]:
        """(cantidad de llamadas del usuario desde `since`, fecha de la mas antigua)."""
