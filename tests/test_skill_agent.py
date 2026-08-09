"""
Integration tests for the skill agent strategy against a faithful stub of
the dify_plugin SDK v0.7.1 API surface.

These tests reproduce the reported production errors:
1. "can only concatenate str (not "list") to str" - streaming content blocks
2. "'dict' object has no attribute 'model_dump'" - tools passed as raw dicts
3. tool calls must be extracted from chunk.delta.message.tool_calls
"""

import os
import sys
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
STUBS_DIR = os.path.join(TESTS_DIR, "stubs")
PLUGIN_ROOT = os.path.dirname(TESTS_DIR)
sys.path.insert(0, STUBS_DIR)
sys.path.insert(0, PLUGIN_ROOT)

from dify_plugin.core.runtime import Session  # noqa: E402
from dify_plugin.entities.agent import AgentRuntime  # noqa: E402
from dify_plugin.entities.invoke_message import InvokeMessage  # noqa: E402
from dify_plugin.entities.model.llm import LLMResultChunk, LLMResultChunkDelta  # noqa: E402
from dify_plugin.entities.model.message import (  # noqa: E402
    AssistantPromptMessage,
    PromptMessageTool,
    TextPromptMessageContent,
)
from dify_plugin.entities.tool import ToolInvokeMessage, ToolProviderType  # noqa: E402
from dify_plugin.interfaces.agent import AgentToolIdentity, ToolEntity  # noqa: E402
from dify_plugin.entities.tool import ToolDescription, ToolParameter  # noqa: E402

from strategies.skill_agent import SkillAgentAgentStrategy  # noqa: E402


MODEL_DICT = {
    "provider": "langgenius/mimo/mimo",
    "model": "mimo-v2-flash",
    "mode": "chat",
    "model_type": "llm",
    "completion_params": {},
}


def build_params(query="时间", tools=None):
    params = {
        "model": dict(MODEL_DICT),
        "query": query,
        "maximum_iterations": 5,
        "enabled_skills": "all",
        "debug_mode": False,
        "custom_skills": "",
    }
    if tools is not None:
        params["tools"] = tools
    return params


def collect_texts(messages):
    return [
        m.message.text
        for m in messages
        if m.type == InvokeMessage.MessageType.TEXT
    ]


def make_time_tool():
    return ToolEntity(
        identity=AgentToolIdentity(provider="time", name="current_time", author="test", label=None),
        description=ToolDescription(human=None, llm="一个用于获取当前时间的工具。"),
        parameters=[
            ToolParameter(
                name="format",
                type=ToolParameter.ToolParameterType.STRING,
                form=ToolParameter.ToolParameterForm.LLM,
                llm_description="时间格式，如 %Y-%m-%d %H:%M:%S",
            )
        ],
        runtime_parameters={},
    )


class SkillAgentStrategyTest(unittest.TestCase):
    def run_strategy(self, session, params):
        strategy = SkillAgentAgentStrategy(
            runtime=AgentRuntime(user_id="test-user"),
            session=session,
        )
        return list(strategy.invoke(params))

    def test_streaming_content_blocks_do_not_crash(self):
        """Bug: can only concatenate str (not "list") to str."""
        session = Session(
            llm_chunks=[
                LLMResultChunk(
                    model="mimo-v2-flash",
                    delta=LLMResultChunkDelta(
                        index=0,
                        message=AssistantPromptMessage(
                            content=[
                                TextPromptMessageContent(data="当前"),
                                TextPromptMessageContent(data="时间"),
                            ]
                        ),
                    ),
                )
            ]
        )
        messages = self.run_strategy(session, build_params())
        texts = collect_texts(messages)

        self.assertTrue(texts, "expected streamed text messages")
        self.assertFalse(
            any("Error" in t for t in texts),
            "strategy must not emit an error: %r" % texts,
        )
        self.assertIn("当前时间", "".join(texts))

    def test_tools_pass_prompt_message_tool_models(self):
        """Bug: 'dict' object has no attribute 'model_dump'."""
        tool = make_time_tool()
        session = Session(
            llm_chunks=[
                LLMResultChunk(
                    model="mimo-v2-flash",
                    delta=LLMResultChunkDelta(
                        index=0,
                        message=AssistantPromptMessage(content="当前时间是 2026-08-09 12:00:00"),
                    ),
                )
            ]
        )
        messages = self.run_strategy(session, build_params(tools=[tool]))
        texts = collect_texts(messages)

        self.assertFalse(
            any("Error" in t for t in texts),
            "strategy must not emit an error: %r" % texts,
        )
        self.assertIn("2026-08-09", "".join(texts))

        self.assertEqual(len(session.llm_calls), 1)
        sent_tools = session.llm_calls[0]["tools"]
        self.assertTrue(sent_tools, "expected tools to be sent to the LLM")
        self.assertTrue(
            all(isinstance(t, PromptMessageTool) for t in sent_tools),
            "tools must be PromptMessageTool instances, got: %r" % sent_tools,
        )
        self.assertIn("current_time", [t.name for t in sent_tools])

    def test_tool_calls_are_extracted_and_executed(self):
        """Tool calls live at chunk.delta.message.tool_calls; arguments are JSON strings."""
        tool = make_time_tool()
        tool_call = AssistantPromptMessage.ToolCall(
            id="call_1",
            type="function",
            function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                name="current_time",
                arguments='{"format": "%Y-%m-%d %H:%M:%S"}',
            ),
        )
        tool.provider_type = ToolProviderType.WORKFLOW
        session = Session()
        session.queue_llm_chunks(
            [
                LLMResultChunk(
                    model="mimo-v2-flash",
                    delta=LLMResultChunkDelta(
                        index=0,
                        message=AssistantPromptMessage(content="", tool_calls=[tool_call]),
                    ),
                )
            ]
        )
        session.queue_llm_chunks(
            [
                LLMResultChunk(
                    model="mimo-v2-flash",
                    delta=LLMResultChunkDelta(
                        index=0,
                        message=AssistantPromptMessage(content="现在时间是 2026-08-09 12:00:00"),
                    ),
                )
            ]
        )
        session._tool_messages = [
            ToolInvokeMessage(
                type=InvokeMessage.MessageType.TEXT,
                message=InvokeMessage.TextMessage(text="2026-08-09 12:00:00"),
            )
        ]

        messages = self.run_strategy(session, build_params(tools=[tool]))
        texts = collect_texts(messages)

        self.assertEqual(
            session.tool_calls,
            [
                {
                    "provider_type": ToolProviderType.WORKFLOW,
                    "provider": "time",
                    "tool_name": "current_time",
                    "parameters": {"format": "%Y-%m-%d %H:%M:%S"},
                }
            ],
            "expected the tool to be invoked with parsed JSON arguments",
        )
        self.assertIn("现在时间是 2026-08-09 12:00:00", "".join(texts))

        second_call = session.llm_calls[1]["prompt_messages"]
        tool_messages = [
            m for m in second_call if isinstance(m, AssistantPromptMessage) and m.tool_calls
        ]
        self.assertEqual(len(tool_messages), 1)
        self.assertEqual(tool_messages[0].tool_calls[0].id, "call_1")

    def test_completes_cleanly_on_last_iteration(self):
        """No spurious 'Reached maximum iterations' warning on boundary completion."""
        session = Session(
            llm_chunks=[
                LLMResultChunk(
                    model="mimo-v2-flash",
                    delta=LLMResultChunkDelta(
                        index=0,
                        message=AssistantPromptMessage(content="完成了"),
                    ),
                )
            ]
        )
        params = build_params()
        params["maximum_iterations"] = 1
        messages = self.run_strategy(session, params)
        texts = collect_texts(messages)

        self.assertIn("完成了", "".join(texts))
        self.assertFalse(
            any("Reached maximum iterations" in t for t in texts),
            "must not warn when the agent completed exactly at the iteration limit: %r" % texts,
        )

    def test_malformed_tool_arguments_are_surfaced(self):
        """Malformed JSON tool arguments must be surfaced, not silently ignored."""
        tool = make_time_tool()
        tool_call = AssistantPromptMessage.ToolCall(
            id="call_1",
            type="function",
            function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                name="current_time",
                arguments="not-valid-json",
            ),
        )
        session = Session()
        session.queue_llm_chunks(
            [
                LLMResultChunk(
                    model="mimo-v2-flash",
                    delta=LLMResultChunkDelta(
                        index=0,
                        message=AssistantPromptMessage(content="", tool_calls=[tool_call]),
                    ),
                )
            ]
        )

        messages = self.run_strategy(session, build_params(tools=[tool]))
        texts = collect_texts(messages)

        self.assertEqual(session.tool_calls, [], "tool must not be invoked with broken arguments")
        self.assertTrue(
            any("not-valid-json" in t for t in texts),
            "expected the malformed arguments to appear in the error output: %r" % texts,
        )


if __name__ == "__main__":
    unittest.main()
