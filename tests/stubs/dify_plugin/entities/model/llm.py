"""
Faithful stub of dify_plugin.entities.model.llm (SDK v0.7.1),
translated to Python 3.9-compatible syntax.
"""

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dify_plugin.entities.model import BaseModelConfig, ModelType, ModelUsage, PriceInfo
from dify_plugin.entities.model.message import AssistantPromptMessage, PromptMessage


class LLMMode(Enum):
    COMPLETION = "completion"
    CHAT = "chat"


class LLMUsage(ModelUsage):
    prompt_tokens: int
    prompt_unit_price: Decimal
    prompt_price_unit: Decimal
    prompt_price: Decimal
    completion_tokens: int
    completion_unit_price: Decimal
    completion_price_unit: Decimal
    completion_price: Decimal
    total_tokens: int
    total_price: Decimal
    currency: str
    latency: float

    @classmethod
    def empty_usage(cls):
        return cls(
            prompt_tokens=0,
            prompt_unit_price=Decimal("0.0"),
            prompt_price_unit=Decimal("0.0"),
            prompt_price=Decimal("0.0"),
            completion_tokens=0,
            completion_unit_price=Decimal("0.0"),
            completion_price_unit=Decimal("0.0"),
            completion_price=Decimal("0.0"),
            total_tokens=0,
            total_price=Decimal("0.0"),
            currency="USD",
            latency=0.0,
        )


class LLMResultChunkDelta(BaseModel):
    index: int
    message: AssistantPromptMessage
    usage: Optional[LLMUsage] = None
    finish_reason: Optional[str] = None


class LLMResultChunk(BaseModel):
    model: str
    prompt_messages: List[PromptMessage] = Field(default_factory=list)
    system_fingerprint: Optional[str] = None
    delta: LLMResultChunkDelta

    @field_validator("prompt_messages", mode="before")
    @classmethod
    def transform_prompt_messages(cls, value):
        return []


class LLMResult(BaseModel):
    model: str
    prompt_messages: List[PromptMessage] = Field(default_factory=list)
    message: AssistantPromptMessage
    usage: LLMUsage
    system_fingerprint: Optional[str] = None

    @field_validator("prompt_messages", mode="before")
    @classmethod
    def transform_prompt_messages(cls, value):
        return []


class LLMModelConfig(BaseModelConfig):
    model_type: ModelType = ModelType.LLM
    mode: str
    completion_params: dict = Field(default_factory=dict)

    model_config = ConfigDict(protected_namespaces=())


class NumTokensResult(PriceInfo):
    tokens: int
