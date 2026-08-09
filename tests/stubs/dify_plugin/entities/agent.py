"""
Faithful stub of dify_plugin.entities.agent (SDK v0.7.1).
"""

from typing import Optional

from pydantic import BaseModel

from dify_plugin.entities.invoke_message import InvokeMessage


class AgentRuntime(BaseModel):
    user_id: Optional[str] = None


class AgentInvokeMessage(InvokeMessage):
    pass
