"""
Faithful stub of dify_plugin.entities.model.message (SDK v0.7.1),
translated to Python 3.9-compatible syntax.
"""

from enum import Enum
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, BeforeValidator, Field, field_validator

try:
    from enum import StrEnum
except ImportError:  # Python < 3.11
    class StrEnum(str, Enum):
        pass


class PromptMessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    DEVELOPER = "developer"


class PromptMessageTool(BaseModel):
    name: str
    description: str
    parameters: dict


class PromptMessageFunction(BaseModel):
    type: str = "function"
    function: PromptMessageTool


class PromptMessageContentType(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"


class PromptMessageContent(BaseModel):
    pass


class TextPromptMessageContent(PromptMessageContent):
    type: Literal[PromptMessageContentType.TEXT] = PromptMessageContentType.TEXT
    data: str


class MultiModalPromptMessageContent(PromptMessageContent):
    format: str = Field(default=..., description="the format of multi-modal file")
    base64_data: str = Field(default="", description="the base64 data of multi-modal file")
    url: str = Field(default="", description="the url of multi-modal file")
    mime_type: str = Field(default=..., description="the mime type of multi-modal file")
    filename: str = Field(default="", description="the filename of multi-modal file")

    @property
    def data(self):
        return self.url or "data:{};base64,{}".format(self.mime_type, self.base64_data)


class ImagePromptMessageContent(MultiModalPromptMessageContent):
    class DETAIL(Enum):
        LOW = "low"
        HIGH = "high"

    type: Literal[PromptMessageContentType.IMAGE] = PromptMessageContentType.IMAGE
    detail: "ImagePromptMessageContent.DETAIL" = "low"


def _make_content_type(type_: PromptMessageContentType):
    class _Content(MultiModalPromptMessageContent):
        type: Literal[type_] = type_

    return _Content


VideoPromptMessageContent = _make_content_type(PromptMessageContentType.VIDEO)
AudioPromptMessageContent = _make_content_type(PromptMessageContentType.AUDIO)
DocumentPromptMessageContent = _make_content_type(PromptMessageContentType.DOCUMENT)


PromptMessageContentUnionTypes = Annotated[
    Union[
        TextPromptMessageContent,
        ImagePromptMessageContent,
        DocumentPromptMessageContent,
        AudioPromptMessageContent,
        VideoPromptMessageContent,
    ],
    Field(discriminator="type"),
]


class PromptMessage(BaseModel):
    role: PromptMessageRole
    content: Optional[Union[str, List[PromptMessageContent]]] = None
    name: Optional[str] = None

    def is_empty(self) -> bool:
        return not self.content

    @field_validator("content", mode="before")
    @classmethod
    def transform_content(cls, value):
        if isinstance(value, str):
            return value
        elif isinstance(value, (list, tuple)):
            result = []
            for content in value:
                if isinstance(content, PromptMessageContent):
                    result.append(content)
                    continue
                if not isinstance(content, dict):
                    raise ValueError("invalid prompt message content")
                value_type = content.get("type")
                if value_type == PromptMessageContentType.TEXT:
                    result.append(TextPromptMessageContent.model_validate(content))
                elif value_type == PromptMessageContentType.IMAGE:
                    result.append(ImagePromptMessageContent.model_validate(content))
                elif value_type == PromptMessageContentType.AUDIO:
                    result.append(AudioPromptMessageContent.model_validate(content))
                elif value_type == PromptMessageContentType.VIDEO:
                    result.append(VideoPromptMessageContent.model_validate(content))
                elif value_type == PromptMessageContentType.DOCUMENT:
                    result.append(DocumentPromptMessageContent.model_validate(content))
                else:
                    raise ValueError("invalid prompt message content type")
            return result
        return value


class UserPromptMessage(PromptMessage):
    role: PromptMessageRole = PromptMessageRole.USER


def _ensure_field_empty_str(value: Optional[str]) -> str:
    if value is None:
        return ""
    return value


class AssistantPromptMessage(PromptMessage):
    class ToolCall(BaseModel):
        class ToolCallFunction(BaseModel):
            name: Annotated[str, BeforeValidator(_ensure_field_empty_str)]
            arguments: Annotated[str, BeforeValidator(_ensure_field_empty_str)]

        id: str
        type: Annotated[str, BeforeValidator(_ensure_field_empty_str)]
        function: ToolCallFunction

        @field_validator("id", mode="before")
        @classmethod
        def transform_id_to_str(cls, value) -> str:
            if value is None:
                return ""
            elif not isinstance(value, str):
                return str(value)
            else:
                return value

    role: PromptMessageRole = PromptMessageRole.ASSISTANT
    tool_calls: List[ToolCall] = []

    def is_empty(self) -> bool:
        return not (not super().is_empty() and not self.tool_calls)


class SystemPromptMessage(PromptMessage):
    role: PromptMessageRole = PromptMessageRole.SYSTEM


class DeveloperPromptMessage(PromptMessage):
    role: PromptMessageRole = PromptMessageRole.DEVELOPER


class ToolPromptMessage(PromptMessage):
    role: PromptMessageRole = PromptMessageRole.TOOL
    tool_call_id: str

    def is_empty(self) -> bool:
        return not (not super().is_empty() and not self.tool_call_id)
