"""
Faithful stub of dify_plugin.entities.model (SDK v0.7.1), trimmed to what
LLMModelConfig / AgentModelConfig need.
"""

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ModelType(Enum):
    LLM = "llm"
    TEXT_EMBEDDING = "text-embedding"
    RERANK = "rerank"
    MODERATION = "moderation"
    TTS = "tts"
    SPEECH2TEXT = "speech2text"


class PriceInfo(BaseModel):
    total_price: Decimal = Field(default=Decimal("0.0"))
    currency: str = Field(default="USD")
    latency: float = Field(default=0.0)


class ModelUsage(PriceInfo):
    pass


class BaseModelConfig(BaseModel):
    provider: str
    model: str
    model_type: ModelType

    model_config = ConfigDict(protected_namespaces=())


class AIModelEntity(BaseModel):
    pass
