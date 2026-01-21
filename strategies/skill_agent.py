"""
Skill-based Agent Strategy

This module implements the core agent strategy that leverages the skill
system to provide intelligent, context-aware responses. The agent:

1. Loads and matches skills based on user queries
2. Constructs enhanced prompts with skill instructions
3. Executes LLM calls with tool support
4. Manages the conversation loop with iteration limits
"""

import os
import time
from typing import Any, Dict, Generator, List, Optional, Tuple

from pydantic import BaseModel

from dify_plugin.entities.agent import AgentInvokeMessage
from dify_plugin.entities.model.llm import LLMModelConfig
from dify_plugin.entities.model.message import (
    PromptMessage,
    PromptMessageRole,
    SystemPromptMessage,
    UserPromptMessage,
    AssistantPromptMessage,
    ToolPromptMessage,
)
from dify_plugin.entities.tool import ToolInvokeMessage, ToolProviderType
from dify_plugin.interfaces.agent import AgentModelConfig, AgentStrategy, ToolEntity

from skills import SkillRegistry


class SkillAgentParams(BaseModel):
    """Parameters for the skill-based agent strategy."""
    model: AgentModelConfig
    tools: Optional[List[ToolEntity]] = None
    query: str
    enabled_skills: str = "all"
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

    def __init__(self):
        """Initialize the agent strategy."""
        super().__init__()
        self._skill_registry: Optional[SkillRegistry] = None
        self._skills_loaded = False
    
    def _ensure_skills_loaded(self) -> SkillRegistry:
        """
        Ensure skills are loaded and return the registry.
        
        Returns:
            Initialized SkillRegistry with loaded skills
        """
        if self._skill_registry is None or not self._skills_loaded:
            self._skill_registry = SkillRegistry()
            
            # Determine skills directory path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            plugin_dir = os.path.dirname(current_dir)
            skills_dir = os.path.join(plugin_dir, 'skills')
            
            # Load skills
            count = self._skill_registry.load_from_directory(skills_dir)
            self._skills_loaded = True
            
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
    ) -> List[Dict[str, Any]]:
        """
        Build tool definitions for the LLM.
        
        Args:
            tools: List of tool entities
            
        Returns:
            List of tool definition dicts for the LLM
        """
        if not tools:
            return []
        
        definitions = []
        for tool in tools:
            definition = {
                "type": "function",
                "function": {
                    "name": tool.identity.name,
                    "description": tool.description.llm if tool.description else "",
                    "parameters": tool.parameters or {}
                }
            }
            definitions.append(definition)
        
        return definitions
    
    def _extract_tool_calls(
        self,
        response: Any
    ) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Extract tool calls from LLM response.
        
        Args:
            response: LLM response object
            
        Returns:
            List of (tool_call_id, tool_name, arguments) tuples
        """
        tool_calls = []
        
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tc in response.tool_calls:
                tool_calls.append((
                    tc.id or f"call_{len(tool_calls)}",
                    tc.function.name,
                    tc.function.arguments or {}
                ))
        
        return tool_calls
    
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
            # Log activated skills
            yield self.create_text_message(
                f"🎯 Activated skills: {', '.join(activated_skills)}\n\n"
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
            
            # Prepare model config
            model_config = LLMModelConfig(
                provider=params.model.provider,
                model=params.model.model,
                model_parameters=params.model.model_parameters or {},
                credentials=params.model.credentials or {}
            )
            
            # Call LLM
            try:
                response_text = ""
                tool_calls = []
                
                for chunk in self.session.model.llm.invoke(
                    model_config=model_config,
                    prompt_messages=messages,
                    tools=tool_defs if tool_defs else None,
                    stream=True
                ):
                    # Handle streaming response
                    if hasattr(chunk, 'delta') and chunk.delta:
                        if hasattr(chunk.delta, 'message') and chunk.delta.message:
                            delta_content = chunk.delta.message.content
                            if delta_content:
                                response_text += delta_content
                                yield self.create_text_message(delta_content)
                        
                        # Check for tool calls
                        if hasattr(chunk.delta, 'tool_calls'):
                            tool_calls = self._extract_tool_calls(chunk.delta)
                
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
                    yield self.finish_log_message(
                        log=iteration_log,
                        data={"status": "completed", "response": response_text[:200]},
                        metadata={
                            "finished_at": time.perf_counter(),
                            "total_time": time.perf_counter() - iteration_started
                        }
                    )
                    break
                
                # Add assistant message with tool calls
                messages.append(AssistantPromptMessage(
                    content=response_text,
                    tool_calls=tool_calls
                ))
                
                # Execute tool calls
                for tool_call_id, tool_name, tool_args in tool_calls:
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
                        
                        # Invoke the tool
                        tool_result_parts = []
                        for result in self.session.tool.invoke(
                            provider_type=ToolProviderType.BUILT_IN,
                            provider=tool_instance.identity.provider,
                            tool_name=tool_instance.identity.name,
                            parameters={
                                **tool_instance.runtime_parameters,
                                **tool_args
                            }
                        ):
                            if hasattr(result, 'message') and result.message:
                                tool_result_parts.append(str(result.message))
                        
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
                        "tools_called": [tc[1] for tc in tool_calls]
                    },
                    metadata={
                        "finished_at": time.perf_counter(),
                        "iteration_time": time.perf_counter() - iteration_started
                    }
                )
                
            except Exception as e:
                yield self.finish_log_message(
                    log=model_log,
                    data={"error": str(e)},
                    metadata={"finished_at": time.perf_counter()},
                    status=ToolInvokeMessage.LogMessage.LogStatus.ERROR
                )
                yield self.create_text_message(f"\n\nError: {str(e)}")
                break
        
        # Check if we hit iteration limit
        if iteration >= params.maximum_iterations:
            yield self.create_text_message(
                f"\n\n⚠️ Reached maximum iterations ({params.maximum_iterations})"
            )
