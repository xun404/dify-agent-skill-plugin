"""
Faithful stub of dify_plugin.entities.tool (SDK v0.7.1), trimmed to the
surface used by agent strategies and the LLM tool conversion helpers.
"""

from enum import Enum
from typing import Any, Mapping, Optional, Union

from pydantic import BaseModel, Field

from dify_plugin.entities.invoke_message import InvokeMessage


class ToolInvokeMessage(InvokeMessage):
    pass


class ToolProviderType(Enum):
    BUILT_IN = "builtin"
    WORKFLOW = "workflow"
    API = "api"
    APP = "app"
    DATASET_RETRIEVAL = "dataset-retrieval"
    MCP = "mcp"


class ToolIdentity(BaseModel):
    author: str = Field(..., description="The author of the tool")
    name: str = Field(..., description="The name of the tool")
    label: Any = Field(default=None, description="The label of the tool")


class ParameterOption(BaseModel):
    value: Any = Field(default=None, description="The value of the option")
    label: Any = Field(default=None, description="The label of the option")


class ToolParameter(BaseModel):
    class ToolParameterType(str, Enum):
        STRING = "string"
        NUMBER = "number"
        BOOLEAN = "boolean"
        SELECT = "select"
        SECRET_INPUT = "secret-input"
        FILE = "file"
        FILES = "files"
        MODEL_SELECTOR = "model-selector"
        APP_SELECTOR = "app-selector"
        CHECKBOX = "checkbox"
        ANY = "any"
        OBJECT = "object"
        ARRAY = "array"
        DYNAMIC_SELECT = "dynamic-select"

    class ToolParameterForm(Enum):
        SCHEMA = "schema"
        FORM = "form"
        LLM = "llm"

    name: str = Field(..., description="The name of the parameter")
    label: Any = Field(default=None, description="The label presented to the user")
    type: ToolParameterType = Field(..., description="The type of the parameter")
    form: ToolParameterForm = Field(..., description="The form of the parameter, schema/form/llm")
    llm_description: Optional[str] = None
    required: Optional[bool] = False
    options: Optional[list] = None
    input_schema: Optional[Mapping[str, Any]] = None


class ToolDescription(BaseModel):
    human: Any = Field(default=None, description="The description presented to the user")
    llm: str = Field(..., description="The description presented to the LLM")
