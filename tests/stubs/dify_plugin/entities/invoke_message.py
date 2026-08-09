"""
Faithful stub of dify_plugin.entities.invoke_message (SDK v0.7.1),
translated to Python 3.9-compatible syntax.
"""

import uuid
from enum import Enum
from typing import Any, Mapping, Optional, Union

from pydantic import BaseModel, Field, field_serializer, field_validator

from dify_plugin.entities.provider_config import LogMetadata


class InvokeMessage(BaseModel):
    class TextMessage(BaseModel):
        text: str

        def to_dict(self):
            return {"text": self.text}

    class JsonMessage(BaseModel):
        json_object: Union[Mapping, list]

        def to_dict(self):
            return {"json_object": self.json_object}

    class BlobMessage(BaseModel):
        blob: bytes

    class VariableMessage(BaseModel):
        variable_name: str = Field(..., description="The name of the variable")
        variable_value: Any = Field(..., description="The value of the variable")
        stream: bool = Field(default=False, description="Whether the variable is streamed")

    class LogMessage(BaseModel):
        class LogStatus(Enum):
            START = "start"
            ERROR = "error"
            SUCCESS = "success"

        id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="The id of the log")
        label: str = Field(..., description="The label of the log")
        parent_id: Optional[str] = Field(default=None, description="Leave empty for root log")
        error: Optional[str] = Field(default=None, description="The error message")
        status: "InvokeMessage.LogMessage.LogStatus" = Field(..., description="The status of the log")
        data: Mapping[str, Any] = Field(..., description="Detailed log data")
        metadata: Optional[Mapping[LogMetadata, Any]] = Field(
            default=None, description="The metadata of the log"
        )

    class RetrieverResourceMessage(BaseModel):
        pass

    class MessageType(Enum):
        TEXT = "text"
        FILE = "file"
        BLOB = "blob"
        JSON = "json"
        LINK = "link"
        IMAGE = "image"
        IMAGE_LINK = "image_link"
        VARIABLE = "variable"
        BLOB_CHUNK = "blob_chunk"
        LOG = "log"
        RETRIEVER_RESOURCES = "retriever_resources"

    type: MessageType
    message: Union[
        TextMessage,
        JsonMessage,
        VariableMessage,
        BlobMessage,
        LogMessage,
        RetrieverResourceMessage,
        None,
    ]
    meta: Optional[dict] = None

    @field_serializer("message")
    def serialize_message(self, v):
        return v
