"""
Skill Loader and Registry

Provides functionality for discovering, loading, and managing skills
from the skills directory. Skills are loaded from SKILL.md files with
YAML frontmatter configuration.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from skills.base import BaseSkill, MarkdownSkill, ConfigSkill, SkillConfig, SkillContext


@dataclass
class SkillMatch:
    """
    Represents a matched skill with its activation score.
    """
    skill: BaseSkill
    score: float
    matched_triggers: List[str]
    
    def __lt__(self, other: "SkillMatch") -> bool:
        # Sort by score descending, then priority descending
        if self.score != other.score:
            return self.score > other.score
        return self.skill.config.priority > other.skill.config.priority


class SkillLoader:
    """
    Loads skills from SKILL.md files in a directory.
    
    Each skill is expected to be in its own subdirectory with a SKILL.md file.
    The SKILL.md file should have YAML frontmatter with configuration.
    
    Example structure:
        skills/
        ├── code_helper/
        │   └── SKILL.md
        ├── docs_helper/
        │   └── SKILL.md
        └── testing_helper/
            └── SKILL.md
    """
    
    SKILL_FILENAME = "SKILL.md"
    CONFIG_FILENAME = "config.yaml"
    
    def __init__(self, skills_dir: Optional[str] = None):
        """
        Initialize the skill loader.
        
        Args:
            skills_dir: Path to the skills directory. If None, uses
                       the 'skills' directory relative to this file.
        """
        if skills_dir is None:
            skills_dir = os.path.dirname(os.path.abspath(__file__))
        self.skills_dir = Path(skills_dir)
    
    def discover_skills(self) -> List[Path]:
        """
        Discover all skill directories.
        
        Returns:
            List of paths to directories containing SKILL.md files
        """
        skill_dirs = []
        
        if not self.skills_dir.exists():
            return skill_dirs
        
        for item in self.skills_dir.iterdir():
            if item.is_dir() and not item.name.startswith(('_', '.')):
                skill_file = item / self.SKILL_FILENAME
                if skill_file.exists():
                    skill_dirs.append(item)
        
        return skill_dirs
    
    def parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """
        Parse YAML frontmatter from markdown content.
        
        Args:
            content: Full markdown content with frontmatter
            
        Returns:
            Tuple of (frontmatter dict, remaining content)
        """
        frontmatter = {}
        body = content
        
        # Match frontmatter between --- delimiters
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)
        
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                frontmatter = {}
            body = match.group(2)
        
        return frontmatter, body.strip()
    
    def load_skill(self, skill_dir: Path) -> Optional[BaseSkill]:
        """
        Load a skill from a directory.
        
        Args:
            skill_dir: Path to the skill directory
            
        Returns:
            Loaded skill instance, or None if loading failed
        """
        skill_file = skill_dir / self.SKILL_FILENAME
        
        if not skill_file.exists():
            return None
        
        try:
            content = skill_file.read_text(encoding='utf-8')
            frontmatter, body = self.parse_frontmatter(content)
            
            # Load additional config if exists
            config_file = skill_dir / self.CONFIG_FILENAME
            if config_file.exists():
                try:
                    additional_config = yaml.safe_load(
                        config_file.read_text(encoding='utf-8')
                    ) or {}
                    frontmatter = {**frontmatter, **additional_config}
                except yaml.YAMLError:
                    pass
            
            # Create skill config
            config = SkillConfig(
                name=frontmatter.get('name', skill_dir.name),
                description=frontmatter.get('description', ''),
                triggers=frontmatter.get('triggers', []),
                allowed_tools=frontmatter.get('allowed_tools'),
                priority=frontmatter.get('priority', 0),
                category=frontmatter.get('category'),
            )
            
            return MarkdownSkill(config=config, content=body)
            
        except Exception as e:
            print(f"Error loading skill from {skill_dir}: {e}")
            return None
    
    def load_all_skills(self) -> List[BaseSkill]:
        """
        Load all skills from the skills directory.
        
        Returns:
            List of loaded skill instances
        """
        skills = []
        
        for skill_dir in self.discover_skills():
            skill = self.load_skill(skill_dir)
            if skill:
                skills.append(skill)
        
        return skills


class SkillRegistry:
    """
    Registry for managing loaded skills.
    
    Provides functionality for:
    - Registering and storing skills
    - Matching queries to relevant skills
    - Filtering skills by name or category
    """
    
    def __init__(self):
        """Initialize an empty skill registry."""
        self._skills: Dict[str, BaseSkill] = {}
        self._loader: Optional[SkillLoader] = None
    
    def register(self, skill: BaseSkill) -> None:
        """
        Register a skill in the registry.
        
        Args:
            skill: Skill instance to register
        """
        self._skills[skill.config.name] = skill
    
    def unregister(self, name: str) -> Optional[BaseSkill]:
        """
        Remove a skill from the registry.
        
        Args:
            name: Name of the skill to remove
            
        Returns:
            The removed skill, or None if not found
        """
        return self._skills.pop(name, None)
    
    def get(self, name: str) -> Optional[BaseSkill]:
        """
        Get a skill by name.
        
        Args:
            name: Name of the skill
            
        Returns:
            Skill instance if found, None otherwise
        """
        return self._skills.get(name)
    
    def list_skills(self) -> List[BaseSkill]:
        """
        Get all registered skills.
        
        Returns:
            List of all skill instances
        """
        return list(self._skills.values())
    
    def list_skill_names(self) -> List[str]:
        """
        Get names of all registered skills.
        
        Returns:
            List of skill names
        """
        return list(self._skills.keys())
    
    def filter_by_names(self, names: List[str]) -> List[BaseSkill]:
        """
        Get skills matching the given names.
        
        Args:
            names: List of skill names to match
            
        Returns:
            List of matching skills
        """
        return [
            skill for name, skill in self._skills.items()
            if name in names
        ]
    
    def filter_by_category(self, category: str) -> List[BaseSkill]:
        """
        Get skills in a given category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of skills in the category
        """
        return [
            skill for skill in self._skills.values()
            if skill.config.category == category
        ]
    
    def match_query(
        self,
        query: str,
        threshold: float = 0.1,
        max_skills: int = 3,
        skill_filter: Optional[List[str]] = None
    ) -> List[SkillMatch]:
        """
        Find skills that match a query.
        
        Args:
            query: User query to match against
            threshold: Minimum activation score (0-1)
            max_skills: Maximum number of skills to return
            skill_filter: Optional list of skill names to consider
            
        Returns:
            List of SkillMatch objects, sorted by relevance
        """
        matches = []
        
        skills_to_check = self._skills.values()
        if skill_filter:
            skills_to_check = [
                s for s in skills_to_check
                if s.config.name in skill_filter
            ]
        
        for skill in skills_to_check:
            score = skill.should_activate(query)
            if score >= threshold:
                matched_triggers = skill.get_matched_triggers(query)
                matches.append(SkillMatch(
                    skill=skill,
                    score=score,
                    matched_triggers=matched_triggers
                ))
        
        # Sort by score and priority
        matches.sort()
        
        return matches[:max_skills]
    
    def load_from_directory(self, skills_dir: Optional[str] = None) -> int:
        """
        Load all skills from a directory.
        
        Args:
            skills_dir: Path to skills directory
            
        Returns:
            Number of skills loaded
        """
        self._loader = SkillLoader(skills_dir)
        skills = self._loader.load_all_skills()
        
        for skill in skills:
            self.register(skill)
        
        return len(skills)
    
    def get_combined_prompt(
        self,
        query: str,
        skill_filter: Optional[List[str]] = None,
        max_skills: int = 3
    ) -> Tuple[str, List[str]]:
        """
        Generate a combined prompt from matching skills.
        
        Args:
            query: User query to match
            skill_filter: Optional skill name filter
            max_skills: Maximum skills to combine
            
        Returns:
            Tuple of (combined prompt, list of activated skill names)
        """
        matches = self.match_query(
            query,
            skill_filter=skill_filter,
            max_skills=max_skills
        )
        
        if not matches:
            return "", []
        
        prompts = []
        skill_names = []
        
        for match in matches:
            ctx = SkillContext(
                query=query,
                matched_triggers=match.matched_triggers
            )
            prompts.append(match.skill.format_for_llm(ctx))
            skill_names.append(match.skill.config.name)
        
        combined = "\n\n---\n\n".join(prompts)
        
        header = f"# Active Skills ({len(matches)})\n\n"
        header += "The following skills are relevant to this query:\n"
        for name in skill_names:
            header += f"- {name}\n"
        header += "\n---\n\n"
        
        return header + combined, skill_names
    
    def __len__(self) -> int:
        return len(self._skills)
    
    def __contains__(self, name: str) -> bool:
        return name in self._skills
    
    def register_from_config(self, config_dict: Dict) -> Optional[BaseSkill]:
        """
        Register a skill from a configuration dictionary.
        
        Args:
            config_dict: Dictionary with skill configuration
            
        Returns:
            Registered skill instance, or None if registration failed
        """
        skill = ConfigSkill.from_dict(config_dict)
        if skill:
            self.register(skill)
        return skill
    
    def register_from_yaml(self, yaml_string: str) -> tuple:
        """
        Register skills from a YAML string.
        
        The YAML should be a list of skill configurations:
        
        - name: skill-name
          description: Skill description
          triggers:
            - keyword1
            - keyword2
          priority: 5
          instructions: |
            Skill instructions...
        
        Args:
            yaml_string: YAML string containing skill configurations
            
        Returns:
            Tuple of (count, error_message) where count is number of skills 
            registered and error_message is None on success or a string on failure
        """
        if not yaml_string or not yaml_string.strip():
            return (0, "Empty YAML string")
        
        try:
            configs = yaml.safe_load(yaml_string)
            if configs is None:
                return (0, "YAML parsed to None")
            
            if not isinstance(configs, list):
                # Single skill config
                configs = [configs]
            
            count = 0
            errors = []
            for i, config in enumerate(configs):
                if isinstance(config, dict):
                    skill = self.register_from_config(config)
                    if skill:
                        count += 1
                    else:
                        errors.append(f"Config {i}: Failed to create skill from {config.get('name', 'unknown')}")
                else:
                    errors.append(f"Config {i}: Not a dict, got {type(config)}")
            
            if count == 0 and errors:
                return (0, "; ".join(errors))
            return (count, None)
        except yaml.YAMLError as e:
            return (0, f"YAML parse error: {str(e)}")
        except Exception as e:
            return (0, f"Unexpected error: {str(e)}")
