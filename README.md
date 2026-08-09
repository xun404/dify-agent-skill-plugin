# Agent Skill Plugin

## Overview

Agent Skill Plugin is an intelligent agent strategy plugin for the Dify platform that dynamically activates specialized skills based on user queries. Inspired by Claude Code Skills and OpenAI Agents Codex Tool concepts.

## ✨ Core Features

| Feature | Description |
|---------|-------------|
| 🎯 **Multi-Skill Architecture** | Load and manage multiple specialized skills |
| 🔍 **Smart Matching** | Automatically activate relevant skills based on keywords |
| 🛠️ **Tool Integration** | Seamlessly integrates with Dify's built-in tools |
| 📝 **Easy Creation** | Support SKILL.md files and YAML configuration |
| 🔄 **Streaming Responses** | Real-time streaming output with debug logging |

## 🧰 Built-in Skills

### 1. Code Helper

Assists with programming and code-related tasks:

- 📖 **Code Explanation** - Break down complex logic
- 🔧 **Refactoring** - Apply SOLID principles
- 🐛 **Debugging** - Analyze errors and provide fixes
- ⚡ **Optimization** - Identify bottlenecks

**Triggers:** `explain code`, `refactor`, `optimize`, `code review`, `debug`, `fix bug`, `code`

---

### 2. Documentation Helper

Creates comprehensive documentation:

- 📄 **README Generation** - Complete project docs
- 🌐 **API Documentation** - Endpoints, parameters, examples
- 💬 **Code Comments** - Multi-format docstrings
- ✍️ **Technical Writing** - Clear, structured content

**Triggers:** `document`, `readme`, `api docs`, `docstring`, `jsdoc`

---

### 3. Testing Helper

Generates tests and improves coverage:

- 🧪 **Unit Tests** - AAA pattern, edge cases
- 🔗 **Integration Tests** - Component interaction testing
- 🎭 **Mocking & Stubbing** - Dependency isolation
- 📊 **Coverage Analysis** - Identify untested paths

**Triggers:** `test`, `unit test`, `integration test`, `mock`, `coverage`, `pytest`, `jest`

---

## ⚙️ Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | model-selector | ✅ | - | LLM model to use |
| `tools` | array[tools] | ❌ | - | External tools available |
| `query` | string | ✅ | - | User query to process |
| `enabled_skills` | string | ❌ | "all" | Comma-separated skill names |
| `custom_skills` | string | ❌ | - | YAML-formatted custom skills |
| `debug_mode` | boolean | ❌ | false | Enable debug logging |
| `maximum_iterations` | number | ✅ | 10 | Max tool call iterations |

## 📦 Custom Skills

Define custom skills using YAML format in Dify interface:

```yaml
- name: translation-helper
  description: Helps translate text between languages
  triggers:
    - translate
    - translation
  priority: 5
  category: language
  instructions: |
    # Translation Helper
    
    When translating:
    1. Identify source and target languages
    2. Provide accurate translations
    3. Explain nuances or alternatives
```

## 🚀 Getting Started

1. Install the plugin in your Dify workspace
2. Create a new Agent application
3. Select **"Skill-based Agent"** as the agent strategy
4. Configure model and tools
5. Start chatting - skills activate automatically!

## 🔑 Requirements

- **Model**: An LLM model configured in the Agent application (required, no built-in credentials)
- **Tools** (optional): Any Dify tools you want the agent to call (e.g. built-in tools, API tools)
- **Network**: The plugin only communicates with your configured LLM provider and the tools you enable; it makes no other external calls
- **No API keys required**: The plugin itself has no credentials to configure

## 📦 Source Repository

https://github.com/xun404/dify-agent-skill-plugin

## 📚 Documentation

- [Privacy Policy](./PRIVACY.md) - Data handling explanation

---

# License

MIT License

# Contributing

Contributions are welcome! Please see [Development Guide](DEVELOPMENT.md) for details.
