"""
Test double for dify_plugin.core.runtime.Session.

Replicates the SDK v0.7.1 behavior that matters for the strategy:
- LLMInvocation.invoke() does `[tool.model_dump() for tool in tools]`,
  i.e. it requires PromptMessageTool pydantic models (crashes on dicts).
- Streaming chunks expose tool_calls at chunk.delta.message.tool_calls.
"""

from typing import Any, Generator, List, Optional

from dify_plugin.entities.model.llm import LLMResultChunk
from dify_plugin.entities.tool import ToolInvokeMessage, ToolProviderType


class LLMInvocation:
    def __init__(self, session: "Session"):
        self.session = session

    def invoke(
        self,
        model_config,
        prompt_messages,
        tools: Optional[List] = None,
        stop: Optional[list] = None,
        stream: bool = True,
    ) -> Generator[LLMResultChunk, None, None]:
        # Faithful copy of dify_plugin/invocations/model/llm.py behavior
        data = {
            **model_config.model_dump(),
            "prompt_messages": [message.model_dump() for message in prompt_messages],
            "tools": [tool.model_dump() for tool in tools] if tools else None,
            "stop": stop,
            "stream": stream,
        }
        self.session.llm_calls.append(
            {
                "model_config": model_config,
                "prompt_messages": prompt_messages,
                "tools": tools,
                "data": data,
            }
        )
        return iter(self.session._next_llm_chunks())


class ToolInvocation:
    def __init__(self, session: "Session"):
        self.session = session

    def invoke(
        self,
        provider_type: ToolProviderType,
        provider: str,
        tool_name: str,
        parameters: dict,
        credential_id: Optional[str] = None,
    ) -> Generator[ToolInvokeMessage, None, None]:
        self.session.tool_calls.append(
            {
                "provider_type": provider_type,
                "provider": provider,
                "tool_name": tool_name,
                "parameters": parameters,
            }
        )
        return iter(self.session._tool_messages)


class Session:
    def __init__(self, llm_chunks: Optional[List[LLMResultChunk]] = None):
        # Each LLM invocation consumes one group of chunks; if only one
        # flat list is given, it is reused for every invocation.
        if llm_chunks is None:
            self._llm_chunk_groups: List[List[LLMResultChunk]] = []
        else:
            self._llm_chunk_groups: List[List[LLMResultChunk]] = [list(llm_chunks)]
        self._tool_messages: List[ToolInvokeMessage] = []
        self.llm_calls: List[dict] = []
        self.tool_calls: List[dict] = []
        self.model = type("ModelHolder", (), {"llm": LLMInvocation(self)})()
        self.tool = ToolInvocation(self)
        self.app_id: Optional[str] = None
        self.context = type("Context", (), {"credentials": type("C", (), {"get_credential_id": lambda self, p: None})()})()
        self.session_id = "test-session"

    def _next_llm_chunks(self) -> List[LLMResultChunk]:
        if len(self._llm_chunk_groups) > 1:
            return self._llm_chunk_groups.pop(0)
        return list(self._llm_chunk_groups[0])

    def queue_llm_chunks(self, chunks: List[LLMResultChunk]) -> None:
        self._llm_chunk_groups.append(chunks)
