"""
Faithful stub of dify_plugin.interfaces.tool.ToolLike (SDK v0.7.1),
translated to Python 3.9-compatible syntax.
"""

from abc import ABC
from typing import Any, Generic, List, Mapping, Optional, TypeVar, Union

from pydantic import BaseModel

from dify_plugin.entities.invoke_message import InvokeMessage
from dify_plugin.entities.provider_config import LogMetadata

T = TypeVar("T", bound=InvokeMessage)


class ToolLike(ABC, Generic[T]):
    response_type: type

    def create_text_message(self, text: str) -> T:
        return self.response_type(
            type=InvokeMessage.MessageType.TEXT,
            message=InvokeMessage.TextMessage(text=text),
        )

    def create_json_message(self, json: Union[Mapping, list]) -> T:
        return self.response_type(
            type=InvokeMessage.MessageType.JSON,
            message=InvokeMessage.JsonMessage(json_object=json),
        )

    def create_variable_message(self, variable_name: str, variable_value: Any) -> T:
        return self.response_type(
            type=InvokeMessage.MessageType.VARIABLE,
            message=InvokeMessage.VariableMessage(
                variable_name=variable_name,
                variable_value=variable_value,
            ),
        )

    def create_stream_variable_message(self, variable_name: str, variable_value: str) -> T:
        return self.response_type(
            type=InvokeMessage.MessageType.VARIABLE,
            message=InvokeMessage.VariableMessage(
                variable_name=variable_name,
                variable_value=variable_value,
                stream=True,
            ),
        )

    def create_log_message(
        self,
        label: str,
        data: Mapping[str, Any],
        status: Any = InvokeMessage.LogMessage.LogStatus.SUCCESS,
        parent: Optional[T] = None,
        metadata: Optional[Mapping[LogMetadata, Any]] = None,
    ) -> T:
        return self.response_type(
            type=InvokeMessage.MessageType.LOG,
            message=InvokeMessage.LogMessage(
                label=label,
                data=data,
                status=status,
                parent_id=parent.message.id
                if parent and isinstance(parent.message, InvokeMessage.LogMessage)
                else None,
                metadata=metadata,
            ),
        )

    def finish_log_message(
        self,
        log: T,
        status: Any = InvokeMessage.LogMessage.LogStatus.SUCCESS,
        error: Optional[str] = None,
        data: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[LogMetadata, Any]] = None,
    ) -> T:
        assert isinstance(log.message, InvokeMessage.LogMessage)
        return self.response_type(
            type=InvokeMessage.MessageType.LOG,
            message=InvokeMessage.LogMessage(
                id=log.message.id,
                label=log.message.label,
                data=data or log.message.data,
                status=status,
                parent_id=log.message.parent_id,
                error=error,
                metadata=metadata or log.message.metadata,
            ),
        )
