"""
Faithful stub of dify_plugin.interfaces.agent (SDK v0.7.1),
translated to Python 3.9-compatible syntax.

The crucial pieces for the tests:
- ToolEntity / AgentModelConfig models
- _convert_tool_to_prompt_message_tool / _init_prompt_tools (build PromptMessageTool)
- invoke() -> _convert_parameters -> _invoke()
"""

from abc import abstractmethod
from typing import Any, Generator, List, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from dify_plugin.entities.agent import AgentInvokeMessage, AgentRuntime
from dify_plugin.entities.model.llm import LLMModelConfig
from dify_plugin.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageRole,
    PromptMessageTool,
    SystemPromptMessage,
    ToolPromptMessage,
    UserPromptMessage,
)
from dify_plugin.entities.provider_config import CredentialType
from dify_plugin.entities.tool import (
    ToolDescription,
    ToolIdentity,
    ToolParameter,
    ToolProviderType,
)
from dify_plugin.interfaces.tool import ToolLike


class AgentToolIdentity(ToolIdentity):
    provider: str = Field(..., description="The provider of the tool")


class AgentModelConfig(LLMModelConfig):
    entity: Any = None
    history_prompt_messages: List[PromptMessage] = Field(default_factory=list)

    @field_validator("history_prompt_messages", mode="before")
    @classmethod
    def convert_prompt_messages(cls, v):
        if not isinstance(v, list):
            raise ValueError("prompt_messages must be a list")

        for i in range(len(v)):
            if v[i]["role"] == PromptMessageRole.USER.value:
                v[i] = UserPromptMessage(**v[i])
            elif v[i]["role"] == PromptMessageRole.ASSISTANT.value:
                v[i] = AssistantPromptMessage(**v[i])
            elif v[i]["role"] == PromptMessageRole.SYSTEM.value:
                v[i] = SystemPromptMessage(**v[i])
            elif v[i]["role"] == PromptMessageRole.TOOL.value:
                v[i] = ToolPromptMessage(**v[i])
            else:
                v[i] = PromptMessage(**v[i])

        return v


class ToolEntity(BaseModel):
    identity: AgentToolIdentity
    parameters: List[ToolParameter] = Field(default_factory=list)
    description: Optional[ToolDescription] = None
    output_schema: Optional[dict] = None
    credential_id: Optional[str] = None
    credential_type: Optional[CredentialType] = None
    has_runtime_parameters: bool = Field(default=False)
    provider_type: ToolProviderType = ToolProviderType.BUILT_IN

    runtime_parameters: Mapping[str, Any] = {}

    model_config = ConfigDict(protected_namespaces=())

    @field_validator("parameters", mode="before")
    @classmethod
    def set_parameters(cls, v, validation_info: ValidationInfo) -> List[ToolParameter]:
        return v or []


class AgentStrategy(ToolLike[AgentInvokeMessage]):
    def __init__(self, runtime: AgentRuntime, session: Any):
        self.runtime = runtime
        self.session = session
        self.response_type = AgentInvokeMessage

    @abstractmethod
    def _invoke(self, parameters: dict) -> Generator[AgentInvokeMessage, None, None]:
        pass

    def invoke(self, parameters: dict) -> Generator[AgentInvokeMessage, None, None]:
        parameters = self._convert_parameters(parameters)
        return self._invoke(parameters)

    def _init_prompt_tools(self, tools: Optional[List[ToolEntity]]) -> List[PromptMessageTool]:
        prompt_messages_tools = []
        for tool in tools or []:
            try:
                prompt_tool = self._convert_tool_to_prompt_message_tool(tool)
            except Exception:
                continue
            prompt_messages_tools.append(prompt_tool)
        return prompt_messages_tools

    def _convert_tool_to_prompt_message_tool(self, tool: ToolEntity) -> PromptMessageTool:
        message_tool = PromptMessageTool(
            name=tool.identity.name,
            description=tool.description.llm if tool.description else "",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )

        parameters = tool.parameters
        for parameter in parameters:
            if parameter.form != ToolParameter.ToolParameterForm.LLM:
                continue

            parameter_type = parameter.type
            if parameter.type in {
                ToolParameter.ToolParameterType.FILE,
                ToolParameter.ToolParameterType.FILES,
            }:
                continue
            if parameter.type in {
                ToolParameter.ToolParameterType.SELECT,
                ToolParameter.ToolParameterType.SECRET_INPUT,
            }:
                parameter_type = ToolParameter.ToolParameterType.STRING
            enum = []
            if parameter.type == ToolParameter.ToolParameterType.SELECT:
                enum = [option.value for option in parameter.options] if parameter.options else []

            message_tool.parameters["properties"][parameter.name] = (
                {
                    "type": parameter_type,
                    "description": parameter.llm_description or "",
                }
                if parameter.input_schema is None
                else parameter.input_schema
            )

            if len(enum) > 0:
                message_tool.parameters["properties"][parameter.name]["enum"] = enum

            if parameter.required:
                message_tool.parameters["required"].append(parameter.name)

        return message_tool

    @classmethod
    def _convert_parameters(cls, tool_parameters: dict) -> dict:
        return tool_parameters
