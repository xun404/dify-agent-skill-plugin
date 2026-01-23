# Agent Skill 智能代理技能插件

<p align="center">
  <img src="icon.svg" alt="Agent Skill Plugin" width="120" height="120">
</p>

<p align="center">
  <strong>为 Dify 平台设计的智能代理策略插件，根据用户查询动态激活专业技能</strong>
</p>

<p align="center">
  <a href="#english">English</a> | <a href="#中文">中文</a>
</p>

---

## 中文

### 概述

Agent Skill Plugin 是一个智能代理策略插件，能够根据用户查询自动匹配和激活专业技能。灵感来源于 Claude Code Skills 和 OpenAI Agents Codex Tool 概念。

![Agent Skill](./_assets/agent_skill_main.png)

### ✨ 核心功能

| 功能 | 描述 |
|-----|------|
| 🎯 **多技能架构** | 同时加载和管理多个专业技能 |
| 🔍 **智能匹配** | 基于关键词自动激活相关技能 |
| 🛠️ **工具集成** | 与 Dify 内置工具生态系统无缝集成 |
| 📝 **简易创建** | 支持 SKILL.md 文件和 YAML 配置两种方式 |
| 🔄 **流式响应** | 实时流式输出，支持调试日志 |

### 🧰 内置技能

#### 1. 代码助手 (Code Helper)

协助编程和代码相关任务：

- 📖 **代码解释** - 将复杂逻辑分解为易懂的步骤
- 🔧 **重构** - 应用 SOLID 原则，改进代码结构
- 🐛 **调试** - 分析错误并提供修复方案
- ⚡ **优化** - 识别瓶颈，提升性能

**触发词：** `explain code`, `refactor`, `optimize`, `code review`, `debug`, `fix bug`, `code`

---

#### 2. 文档助手 (Documentation Helper)

为代码和项目创建全面的文档：

- 📄 **README 生成** - 完整的项目文档
- 🌐 **API 文档** - 端点、参数、示例
- 💬 **代码注释** - 多种格式的文档字符串
- ✍️ **技术写作** - 清晰、结构化的内容

**触发词：** `document`, `readme`, `api docs`, `docstring`, `jsdoc`

---

#### 3. 测试助手 (Testing Helper)

生成测试并提高代码覆盖率：

- 🧪 **单元测试** - AAA 模式、边界情况
- 🔗 **集成测试** - 组件交互测试
- 🎭 **模拟与存根** - 依赖隔离
- 📊 **覆盖率分析** - 识别未测试的路径

**触发词：** `test`, `unit test`, `integration test`, `mock`, `coverage`, `pytest`, `jest`

---

### ⚙️ 配置参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|-----|------|-----|-------|------|
| `model` | model-selector | ✅ | - | 使用的 LLM 模型 |
| `tools` | array[tools] | ❌ | - | 可用的外部工具 |
| `query` | string | ✅ | - | 用户查询 |
| `enabled_skills` | string | ❌ | "all" | 逗号分隔的技能名称或 "all" |
| `custom_skills` | string | ❌ | - | YAML 格式的自定义技能 |
| `debug_mode` | boolean | ❌ | false | 启用调试日志 |
| `maximum_iterations` | number | ✅ | 10 | 最大工具调用迭代次数 |

### 📦 自定义技能

在 Dify 界面中使用 YAML 格式定义自定义技能：

```yaml
- name: translation-helper
  description: 帮助在不同语言之间翻译文本
  triggers:
    - translate
    - 翻译
  priority: 5
  category: language
  instructions: |
    # 翻译助手
    
    翻译时：
    1. 识别源语言和目标语言
    2. 提供准确的翻译
    3. 解释细微差别或替代方案
```

### 🚀 快速开始

1. 在 Dify 工作区安装插件
2. 创建新的 Agent 应用
3. 选择 **"Skill-based Agent"** 作为代理策略
4. 配置模型和工具
5. 开始对话 - 技能会自动激活！

### 📚 更多文档

- [开发指南](./DEVELOPMENT.md) - 安装、调试、项目结构
- [隐私政策](./PRIVACY.md) - 数据处理说明

---

## English

### Overview

Agent Skill Plugin is an intelligent agent strategy plugin for the Dify platform that dynamically activates specialized skills based on user queries. Inspired by Claude Code Skills and OpenAI Agents Codex Tool concepts.

![agent_skill_main](./_assets/agent_skill_main.png)

### ✨ Core Features

| Feature | Description |
|---------|-------------|
| 🎯 **Multi-Skill Architecture** | Load and manage multiple specialized skills |
| 🔍 **Smart Matching** | Automatically activate relevant skills based on keywords |
| 🛠️ **Tool Integration** | Seamlessly integrates with Dify's built-in tools |
| 📝 **Easy Creation** | Support SKILL.md files and YAML configuration |
| 🔄 **Streaming Responses** | Real-time streaming output with debug logging |

### 🧰 Built-in Skills

#### 1. Code Helper

Assists with programming and code-related tasks:

- 📖 **Code Explanation** - Break down complex logic
- 🔧 **Refactoring** - Apply SOLID principles
- 🐛 **Debugging** - Analyze errors and provide fixes
- ⚡ **Optimization** - Identify bottlenecks

**Triggers:** `explain code`, `refactor`, `optimize`, `code review`, `debug`, `fix bug`, `code`

---

#### 2. Documentation Helper

Creates comprehensive documentation:

- 📄 **README Generation** - Complete project docs
- 🌐 **API Documentation** - Endpoints, parameters, examples
- 💬 **Code Comments** - Multi-format docstrings
- ✍️ **Technical Writing** - Clear, structured content

**Triggers:** `document`, `readme`, `api docs`, `docstring`, `jsdoc`

---

#### 3. Testing Helper

Generates tests and improves coverage:

- 🧪 **Unit Tests** - AAA pattern, edge cases
- 🔗 **Integration Tests** - Component interaction testing
- 🎭 **Mocking & Stubbing** - Dependency isolation
- 📊 **Coverage Analysis** - Identify untested paths

**Triggers:** `test`, `unit test`, `integration test`, `mock`, `coverage`, `pytest`, `jest`

---

### ⚙️ Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | model-selector | ✅ | - | LLM model to use |
| `tools` | array[tools] | ❌ | - | External tools available |
| `query` | string | ✅ | - | User query to process |
| `enabled_skills` | string | ❌ | "all" | Comma-separated skill names |
| `custom_skills` | string | ❌ | - | YAML-formatted custom skills |
| `debug_mode` | boolean | ❌ | false | Enable debug logging |
| `maximum_iterations` | number | ✅ | 10 | Max tool call iterations |

### 📦 Custom Skills

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

### 🚀 Getting Started

1. Install the plugin in your Dify workspace
2. Create a new Agent application
3. Select **"Skill-based Agent"** as the agent strategy
4. Configure model and tools
5. Start chatting - skills activate automatically!

### 📚 Documentation

- [Development Guide](./DEVELOPMENT.md) - Installation, debugging, project structure
- [Privacy Policy](./PRIVACY.md) - Data handling explanation

---

## License

MIT License

## Contributing

Contributions are welcome! Please see [Development Guide](DEVELOPMENT.md) for details.
