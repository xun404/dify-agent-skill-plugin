"""
Skill-based Agent Strategy

This module implements the core agent strategy that leverages the skill
system to provide intelligent, context-aware responses. The agent:

1. Loads and matches skills based on user queries
2. Constructs enhanced prompts with skill instructions
3. Executes LLM calls with tool support
4. Manages the conversation loop with iteration limits
"""

import json
import os
import time
from typing import Any, Dict, Generator, List, Optional

from pydantic import BaseModel

from dify_plugin.entities.agent import AgentInvokeMessage
from dify_plugin.entities.model.message import (
    PromptMessage,
    PromptMessageRole,
    PromptMessageTool,
    SystemPromptMessage,
    UserPromptMessage,
    AssistantPromptMessage,
    ToolPromptMessage,
)
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.interfaces.agent import AgentModelConfig, AgentStrategy, ToolEntity

from skills import SkillRegistry


class SkillAgentParams(BaseModel):
    """Parameters for the skill-based agent strategy."""
    model: AgentModelConfig
    tools: Optional[List[ToolEntity]] = None
    query: str
    enabled_skills: str = "all"
    custom_skills: str = ""
    debug_mode: bool = False
    maximum_iterations: int = 10


class SkillAgentAgentStrategy(AgentStrategy):
    """
    Agent strategy that uses skills to enhance LLM responses.

    This strategy:
    1. Loads skills from the skills directory
    2. Matches relevant skills based on the user query
    3. Constructs prompts with skill instructions
    4. Executes tool calls as needed
    5. Returns streaming responses
    """

    # Base system prompt for the agent
    BASE_SYSTEM_PROMPT = """You are an intelligent assistant with specialized skills.

Based on the user's query, relevant skills have been activated to help you provide the best response.
Follow the instructions from the active skills while maintaining a helpful and professional tone.

When using tools:
1. Analyze the task and determine which tools are needed
2. Call tools with appropriate parameters
3. Process tool results and incorporate them into your response
4. If a tool fails, explain the issue and try alternatives

Always explain your reasoning and provide clear, actionable responses."""


    def _ensure_skills_loaded(self) -> SkillRegistry:
        """
        Ensure skills are loaded and return the registry.

        Returns:
            Initialized SkillRegistry with loaded skills
        """
        # Lazy initialization since we cannot override __init__
        if not hasattr(self, '_skill_registry') or self._skill_registry is None:
            self._skill_registry = SkillRegistry()

            # Determine skills directory path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            plugin_dir = os.path.dirname(current_dir)
            skills_dir = os.path.join(plugin_dir, 'skills')

            # Load skills
            count = self._skill_registry.load_from_directory(skills_dir)

        return self._skill_registry

    def _parse_enabled_skills(self, enabled_skills: str) -> Optional[List[str]]:
        """
        Parse the enabled skills parameter.

        Args:
            enabled_skills: Comma-separated skill names or 'all'

        Returns:
            List of skill names, or None to enable all
        """
        if not enabled_skills or enabled_skills.lower().strip() == 'all':
            return None

        return [s.strip() for s in enabled_skills.split(',') if s.strip()]

    def _build_tool_definitions(
        self,
        tools: Optional[List[ToolEntity]]
    ) -> List[PromptMessageTool]:
        """
        Build tool definitions for the LLM.

        Args:
            tools: List of tool entities

        Returns:
            List of PromptMessageTool definitions for the LLM
        """
        if not tools:
            return []

        return self._init_prompt_tools(tools)

    def _extract_text_content(self, content: Any) -> str:
        """
        Extract plain text from a message content field.

        Args:
            content: str, list of content blocks, or None

        Returns:
            Concatenated text content
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif getattr(block, 'type', None) == 'text':
                    parts.append(getattr(block, 'data', "") or "")
            return "".join(parts)
        return ""

    def _parse_tool_arguments(self, arguments: Any) -> Dict[str, Any]:
        """
        Parse tool call arguments into a dict.

        Args:
            arguments: JSON string or dict

        Returns:
            Arguments dict
        """
        if isinstance(arguments, dict):
            return arguments
        if isinstance(arguments, str) and arguments.strip():
            try:
                parsed = json.loads(arguments)
            except ValueError:
                raise ValueError(f"Invalid tool call arguments JSON: {arguments}")
            if isinstance(parsed, dict):
                return parsed
        return {}

    def _extract_tool_calls(
        self,
        message: Any
    ) -> List[Any]:
        """
        Extract tool calls from an LLM response message.

        Args:
            message: Assistant message from the LLM response chunk

        Returns:
            List of tool call objects
        """
        if not message:
            return []

        tool_calls = getattr(message, 'tool_calls', None)
        if not tool_calls:
            return []

        return list(tool_calls)

    def _invoke(
        self,
        parameters: Dict[str, Any]
    ) -> Generator[AgentInvokeMessage, None, None]:
        """
        Main invocation method for the agent strategy.

        Args:
            parameters: Strategy parameters from Dify

        Yields:
            AgentInvokeMessage objects for streaming response
        """
        # Parse parameters
        params = SkillAgentParams(**parameters)

        # Load skills
        registry = self._ensure_skills_loaded()

        # Debug: show loaded skills count (only if debug_mode enabled)
        if params.debug_mode:
            all_skill_names = registry.list_skill_names()
            yield self.create_text_message(
                f"📚 Loaded {len(all_skill_names)} built-in skill(s): {', '.join(all_skill_names) if all_skill_names else 'none'}\n"
            )

        # Load custom skills from parameter
        custom_count = 0
        if params.custom_skills:
            if params.debug_mode:
                yield self.create_text_message(
                    f"🔧 Custom skills parameter received ({len(params.custom_skills)} chars)\n"
                )
            result = registry.register_from_yaml(params.custom_skills)
            # Handle both old (int) and new (tuple) return types
            if isinstance(result, tuple):
                custom_count, error_msg = result
                if error_msg:
                    # Always show errors
                    yield self.create_text_message(
                        f"⚠️ Custom skills error: {error_msg}\n"
                    )
            else:
                custom_count = result

            if custom_count > 0 and params.debug_mode:
                # Show newly loaded skill names
                all_names_after = registry.list_skill_names()
                yield self.create_text_message(
                    f"📦 Loaded {custom_count} custom skill(s). All skills now: {', '.join(all_names_after)}\n"
                )
        elif params.debug_mode:
            yield self.create_text_message(
                f"ℹ️ No custom skills parameter provided\n"
            )

        # Parse enabled skills filter
        skill_filter = self._parse_enabled_skills(params.enabled_skills)

        # Match skills to query
        skill_prompt, activated_skills = registry.get_combined_prompt(
            query=params.query,
            skill_filter=skill_filter,
            max_skills=3
        )

        # Build system prompt
        system_parts = [self.BASE_SYSTEM_PROMPT]
        if skill_prompt:
            system_parts.append("\n\n" + skill_prompt)
        if activated_skills:
            # Log activated skills (only if debug_mode)
            if params.debug_mode:
                yield self.create_text_message(
                    f"🎯 Activated skills: {', '.join(activated_skills)}\n\n"
                )
        elif params.debug_mode:
            yield self.create_text_message(
                f"ℹ️ No skills matched query: '{params.query[:100]}...'\n\n"
            )

        system_prompt = "".join(system_parts)

        # Initialize conversation
        messages: List[PromptMessage] = [
            SystemPromptMessage(content=system_prompt),
            UserPromptMessage(content=params.query)
        ]

        # Build tool instances map
        tool_instances = {}
        if params.tools:
            tool_instances = {
                tool.identity.name: tool
                for tool in params.tools
            }

        # Build tool definitions for LLM
        tool_defs = self._build_tool_definitions(params.tools)

        # Main agent loop
        iteration = 0
        completed = False
        while iteration < params.maximum_iterations:
            iteration += 1

            # Create log for this iteration
            iteration_started = time.perf_counter()
            iteration_log = self.create_log_message(
                label=f"Iteration {iteration}",
                data={"iteration": iteration},
                metadata={"started_at": iteration_started},
                status=ToolInvokeMessage.LogMessage.LogStatus.START
            )
            yield iteration_log

            # Invoke LLM
            model_log = self.create_log_message(
                label=f"{params.model.model} Thinking",
                data={},
                metadata={
                    "provider": params.model.provider,
                    "started_at": time.perf_counter()
                },
                status=ToolInvokeMessage.LogMessage.LogStatus.START,
                parent=iteration_log
            )
            yield model_log

            # `params.model` was validated into an `AgentModelConfig` by
            # `SkillAgentParams`, so it can be passed to the LLM invoke
            # method as-is (the SDK accepts either a model config or dict).

            # Call the LLM and stream the response
            try:
                response_text = ""
                tool_calls = []

                # Handle streaming response chunks
                for chunk in self.session.model.llm.invoke(
                    model_config=params.model,
                    prompt_messages=messages,
                    tools=tool_defs if tool_defs else None,
                    stream=True
                ):
                    if hasattr(chunk, 'delta') and chunk.delta:
                        delta_message = getattr(chunk.delta, 'message', None)
                        if delta_message:
                            # Content may be a str or a list of content
                            # blocks (e.g. TextPromptMessageContent)
                            delta_content = getattr(delta_message, 'content', None)
                            delta_text = self._extract_text_content(delta_content)
                            if delta_text:
                                response_text += delta_text
                                yield self.create_text_message(delta_text)

                        # Tool calls live on the delta message. In
                        # OpenAI-compatible streaming they accumulate across
                        # chunks, so only replace the set when a chunk
                        # actually carries tool calls.
                        extracted_calls = self._extract_tool_calls(delta_message)
                        if extracted_calls:
                            tool_calls = extracted_calls

                # Finish model log
                yield self.finish_log_message(
                    log=model_log,
                    data={
                        "response_length": len(response_text),
                        "has_tool_calls": len(tool_calls) > 0
                    },
                    metadata={
                        "finished_at": time.perf_counter(),
                        "elapsed_time": time.perf_counter() - iteration_started
                    }
                )

                # If no tool calls, we're done
                if not tool_calls:
                    completed = True
                    yield self.finish_log_message(
                        log=iteration_log,
                        data={"status": "completed", "response": response_text[:200]},
                        metadata={
                            "finished_at": time.perf_counter(),
                            "elapsed_time": time.perf_counter() - iteration_started
                        }
                    )
                    break

                # Add assistant message with tool calls
                messages.append(AssistantPromptMessage(
                    content=response_text,
                    tool_calls=tool_calls
                ))

                # Execute tool calls
                for tool_call_index, tool_call in enumerate(tool_calls):
                    tool_call_id = getattr(tool_call, 'id', None) or f"call_{tool_call_index}"
                    tool_name = tool_call.function.name
                    tool_args = self._parse_tool_arguments(tool_call.function.arguments)

                    tool_log = self.create_log_message(
                        label=f"Tool: {tool_name}",
                        data={"arguments": tool_args},
                        metadata={"started_at": time.perf_counter()},
                        status=ToolInvokeMessage.LogMessage.LogStatus.START,
                        parent=iteration_log
                    )
                    yield tool_log

                    try:
                        if tool_name not in tool_instances:
                            raise ValueError(f"Unknown tool: {tool_name}")

                        tool_instance = tool_instances[tool_name]

                        # Invoke the tool with the parsed arguments merged
                        # over any runtime parameters. The provider type
                        # comes from the tool entity itself so non-builtin
                        # tools (MCP, workflow, api) route correctly.
                        tool_result_parts = []
                        for result in self.session.tool.invoke(
                            provider_type=tool_instance.provider_type,
                            provider=tool_instance.identity.provider,
                            tool_name=tool_instance.identity.name,
                            parameters={
                                **tool_instance.runtime_parameters,
                                **tool_args
                            }
                        ):
                            if hasattr(result, 'message') and result.message:
                                result_message = result.message
                                if hasattr(result_message, 'text'):
                                    tool_result_parts.append(str(result_message.text))
                                else:
                                    tool_result_parts.append(str(result_message))

                        tool_result = "\n".join(tool_result_parts) or "Tool executed successfully"

                        yield self.finish_log_message(
                            log=tool_log,
                            data={"result": tool_result[:500]},
                            metadata={"finished_at": time.perf_counter()}
                        )

                        # Add tool result to messages
                        messages.append(ToolPromptMessage(
                            content=tool_result,
                            tool_call_id=tool_call_id
                        ))

                    except Exception as e:
                        error_msg = f"Tool error: {str(e)}"
                        yield self.finish_log_message(
                            log=tool_log,
                            data={"error": error_msg},
                            metadata={"finished_at": time.perf_counter()},
                            status=ToolInvokeMessage.LogMessage.LogStatus.ERROR
                        )

                        messages.append(ToolPromptMessage(
                            content=error_msg,
                            tool_call_id=tool_call_id
                        ))

                # Finish iteration log
                yield self.finish_log_message(
                    log=iteration_log,
                    data={
                        "status": "tool_calls_completed",
                        "tools_called": [tc.function.name for tc in tool_calls]
                    },
                    metadata={
                        "finished_at": time.perf_counter(),
                        "elapsed_time": time.perf_counter() - iteration_started
                    }
                )

            except Exception as e:
                yield self.finish_log_message(
                    log=model_log,
                    data={"error": str(e)},
                    metadata={"finished_at": time.perf_counter()},
                    status=ToolInvokeMessage.LogMessage.LogStatus.ERROR
                )
                yield self.finish_log_message(
                    log=iteration_log,
                    data={"status": "error", "error": str(e)},
                    metadata={"finished_at": time.perf_counter()},
                    status=ToolInvokeMessage.LogMessage.LogStatus.ERROR
                )
                yield self.create_text_message(f"\n\nError: {str(e)}")
                break

        # Check if we hit the iteration limit without a final answer.
        # `completed` distinguishes a clean break on the last allowed
        # iteration from an exhausted loop that still had tool calls.
        if not completed and iteration >= params.maximum_iterations:
            yield self.create_text_message(
                f"\n\n⚠️ Reached maximum iterations ({params.maximum_iterations})"
            )
