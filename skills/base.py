"""
Base Skill Classes

Defines the core interfaces and data structures for the skill system.
Each skill provides specialized instructions that enhance the agent's
capabilities for specific types of tasks.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import re


@dataclass
class SkillConfig:
    """
    Skill configuration parsed from SKILL.md frontmatter.
    
    Attributes:
        name: Unique identifier for the skill
        description: Human-readable description of what the skill does
        triggers: Keywords or patterns that activate this skill
        allowed_tools: List of tools this skill is allowed to use (None = all)
        priority: Higher priority skills are selected first when multiple match
        category: Optional category for organizing skills
    """
    name: str
    description: str
    triggers: List[str] = field(default_factory=list)
    allowed_tools: Optional[List[str]] = None
    priority: int = 0
    category: Optional[str] = None
    
    def __post_init__(self):
        # Normalize trigger keywords to lowercase
        self.triggers = [t.lower().strip() for t in self.triggers]


@dataclass
class SkillContext:
    """
    Context passed to skills during execution.
    
    Attributes:
        query: The user's original query
        matched_triggers: Which triggers activated this skill
        previous_output: Output from previously executed skills (for chaining)
        metadata: Additional context information
    """
    query: str
    matched_triggers: List[str] = field(default_factory=list)
    previous_output: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseSkill(ABC):
    """
    Abstract base class for all skills.
    
    Skills are modular instruction sets that enhance the agent's
    capabilities for specific types of tasks. Each skill:
    
    1. Has configuration (name, description, triggers)
    2. Provides a system prompt with specialized instructions
    3. Can determine when it should be activated based on queries
    4. May provide additional context for the LLM
    
    Example:
        class CodeHelperSkill(BaseSkill):
            def get_system_prompt(self) -> str:
                return "When helping with code..."
            
            def should_activate(self, query: str) -> float:
                code_keywords = ['code', 'function', 'debug']
                return self._keyword_match_score(query, code_keywords)
    """
    
    def __init__(self, config: SkillConfig, content: str = ""):
        """
        Initialize a skill with its configuration.
        
        Args:
            config: Skill configuration from SKILL.md frontmatter
            content: The main content/instructions from SKILL.md
        """
        self.config = config
        self.content = content
        self._compiled_triggers: List[re.Pattern] = []
        self._compile_triggers()
    
    def _compile_triggers(self) -> None:
        """Compile trigger patterns for efficient matching."""
        for trigger in self.config.triggers:
            # Escape special regex characters except *
            pattern = re.escape(trigger).replace(r'\*', '.*')
            self._compiled_triggers.append(
                re.compile(pattern, re.IGNORECASE)
            )
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Return the skill's system prompt/instructions.
        
        This prompt is injected into the LLM context when this skill
        is activated, providing specialized instructions for the task.
        
        Returns:
            String containing the skill's instructions
        """
        pass
    
    def should_activate(self, query: str) -> float:
        """
        Calculate an activation score based on query relevance.
        
        The score indicates how relevant this skill is to the given query.
        Higher scores mean greater relevance.
        
        Args:
            query: The user's query to evaluate
            
        Returns:
            Float between 0.0 (not relevant) and 1.0 (highly relevant)
        """
        query_lower = query.lower()
        matched = 0
        
        for pattern in self._compiled_triggers:
            if pattern.search(query_lower):
                matched += 1
        
        if not self._compiled_triggers:
            return 0.0
        
        # Base score from trigger matches
        base_score = matched / len(self._compiled_triggers)
        
        # Boost score if multiple triggers match
        if matched > 1:
            base_score = min(1.0, base_score * 1.2)
        
        return base_score
    
    def get_matched_triggers(self, query: str) -> List[str]:
        """
        Get list of triggers that matched the query.
        
        Args:
            query: The user's query
            
        Returns:
            List of trigger strings that matched
        """
        query_lower = query.lower()
        matched = []
        
        for i, pattern in enumerate(self._compiled_triggers):
            if pattern.search(query_lower):
                matched.append(self.config.triggers[i])
        
        return matched
    
    def get_context(self, ctx: SkillContext) -> Optional[str]:
        """
        Generate additional context based on the execution context.
        
        Override this method to provide dynamic context based on
        the query, previous outputs, or other factors.
        
        Args:
            ctx: Current skill execution context
            
        Returns:
            Optional additional context string, or None
        """
        return None
    
    def format_for_llm(self, ctx: SkillContext) -> str:
        """
        Format the skill's instructions for LLM consumption.
        
        Combines the system prompt, any additional context, and
        metadata about which triggers activated this skill.
        
        Args:
            ctx: Current skill execution context
            
        Returns:
            Formatted instruction string for the LLM
        """
        parts = [f"## Skill: {self.config.name}"]
        parts.append(f"**Description**: {self.config.description}")
        
        if ctx.matched_triggers:
            parts.append(f"**Activated by**: {', '.join(ctx.matched_triggers)}")
        
        parts.append("")
        parts.append(self.get_system_prompt())
        
        additional_ctx = self.get_context(ctx)
        if additional_ctx:
            parts.append("")
            parts.append("### Additional Context")
            parts.append(additional_ctx)
        
        return "\n".join(parts)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.config.name}'>"


class MarkdownSkill(BaseSkill):
    """
    A skill loaded from a SKILL.md file.
    
    The skill's instructions come directly from the markdown content,
    which is parsed and used as the system prompt.
    """
    
    def get_system_prompt(self) -> str:
        """Return the markdown content as the system prompt."""
        return self.content
