"""
Dify Agent Skill Plugin - Main Entry Point

This plugin provides an agent strategy that supports multiple skills
for intelligent task execution, inspired by Claude Code Skills and
OpenAI Agents Codex Tool concepts.
"""

from dify_plugin import DifyPluginEnv, Plugin

# Initialize plugin environment
plugin = Plugin(DifyPluginEnv())

if __name__ == "__main__":
    plugin.run()
