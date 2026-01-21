# Agent Skill Plugin for Dify

A Dify plugin that provides an intelligent agent strategy with support for multiple specialized skills. Inspired by Claude Code Skills and OpenAI Agents Codex Tool concepts.

## Features

- 🎯 **Multi-Skill Support** - Load and use multiple specialized skills
- 🔍 **Smart Skill Matching** - Automatically activates relevant skills based on user queries
- 🛠️ **Tool Integration** - Seamlessly works with Dify's built-in tools
- 📝 **Easy Skill Creation** - Simple SKILL.md format for creating new skills
- 🔄 **Streaming Responses** - Real-time streaming output with progress logging

## Installation

### From Local Package

1. Package the plugin (run from the **parent directory** of the plugin folder):
   ```bash
   # Navigate to the parent directory first
   cd /path/to/parent
   
   # Package the plugin
   dify plugin package ./dify-agent-skill-plugin
   ```

   > **Note**: The `dify plugin package` command must be run from outside the plugin directory. Running it inside the plugin directory will result in an error.

2. The generated `dify-agent-skill-plugin.difypkg` file will be created in the current directory.

3. Upload the `.difypkg` file to your Dify workspace via the plugin management page.

### Build Notes

- A `.difyignore` file is included to exclude unnecessary files (like `.venv/`, `__pycache__/`, etc.) from the package
- The uncompressed package size must be less than 50MB
- Ensure `manifest.yaml` has proper `storage.size` configured if storage is enabled

### Remote Debug (For Development)

This section explains how to use Dify's remote debugging feature to test the plugin during development. For more details, see the [official documentation](https://docs.dify.ai/zh/develop-plugin/features-and-specs/plugin-types/remote-debug-a-plugin).

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Get Debug Key from Dify

1. Open your Dify instance and navigate to **"Plugin Management"** page
2. Click **"Debug Plugin"** button
3. Copy the debug connection information:
   - `REMOTE_INSTALL_URL` - The debug server address (e.g., `debug.dify.ai:5003` or your local server)
   - `REMOTE_INSTALL_KEY` - Your unique debug key (UUID format)

#### 3. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env
```

Edit `.env` and fill in your debug information:

```bash
INSTALL_METHOD=remote
REMOTE_INSTALL_URL=debug.dify.ai:5003  # or your server address like 192.168.x.x:5003
REMOTE_INSTALL_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  # Your debug key
```

#### 4. Run the Plugin

```bash
python -m main
```

If successful, you should see output like:

```
INFO:dify_plugin.plugin:Installed agent: agent_skill_provider
```

#### 5. Verify Installation

Go back to Dify's Plugin Management page. You should see the plugin listed with a **"debugging"** status. The plugin will now work in your Dify environment while running locally.

#### Troubleshooting

| Error | Solution |
|-------|----------|
| `ValidationError: 'description'` | Ensure `description` is a top-level field in strategy YAML, not inside `identity` |
| Connection refused | Check `REMOTE_INSTALL_URL` matches your Dify server's debug port |
| Invalid key | Regenerate the debug key from Dify's Plugin Management page |

## Usage

1. Create a new Agent application in Dify
2. Select "Skill-based Agent" as the agent strategy
3. Configure the model and tools
4. Start chatting!

The agent will automatically match your queries to relevant skills and use them to provide enhanced responses.

## Built-in Skills

### Code Helper
Helps with code explanation, refactoring, debugging, and optimization.

**Triggers**: explain code, refactor, optimize, code review, debug, fix bug

### Documentation Helper
Generates documentation for code, APIs, and projects.

**Triggers**: document, readme, api docs, docstring, jsdoc

### Testing Helper
Generates unit tests, integration tests, and test strategies.

**Triggers**: test, unit test, integration test, mock, coverage

## Creating Custom Skills

Skills are defined using markdown files with YAML frontmatter. Each skill lives in its own directory under `skills/`.

### Directory Structure

```
skills/
├── my_skill/
│   ├── SKILL.md      # Required: Skill definition
│   └── config.yaml   # Optional: Additional configuration
```

### SKILL.md Format

```markdown
---
name: my-skill
description: A brief description of what this skill does
triggers:
  - keyword1
  - keyword2
  - phrase to match
priority: 5
category: general
---

# My Skill

Instructions for the LLM when this skill is activated.

## When to Use
- Scenario 1
- Scenario 2

## Best Practices
1. Practice 1
2. Practice 2
```

### Configuration Options

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique skill identifier |
| `description` | string | Yes | Brief description shown in skill list |
| `triggers` | list | Yes | Keywords/phrases that activate this skill |
| `priority` | int | No | Higher priority skills are selected first (default: 0) |
| `category` | string | No | Optional category for organization |
| `allowed_tools` | list | No | Restrict which tools this skill can use |

## Agent Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | model-selector | Yes | - | LLM model to use |
| `tools` | array[tools] | No | - | External tools available to the agent |
| `query` | string | Yes | - | User query to process |
| `enabled_skills` | string | No | "all" | Comma-separated skill names or "all" |
| `custom_skills` | string | No | - | YAML-formatted custom skill definitions |
| `maximum_iterations` | number | No | 10 | Max tool call iterations |

## Custom Skills Configuration

You can define custom skills directly in the Dify interface using YAML format. This allows you to add new skills without modifying the plugin package.

### Custom Skill Format

```yaml
- name: translation-helper
  description: Helps translate text between languages
  triggers:
    - translate
    - 翻译
    - translation
  priority: 5
  category: language
  instructions: |
    # Translation Helper
    
    When the user asks for translation:
    1. Identify the source and target languages
    2. Provide accurate translations
    3. Explain any nuances or alternative translations

- name: sql-helper
  description: Helps write and optimize SQL queries
  triggers:
    - sql
    - database
    - query
  priority: 5
  instructions: |
    # SQL Helper
    
    Assist users with SQL-related tasks:
    - Write efficient queries
    - Optimize existing queries
    - Explain query execution plans
```

### Custom Skill Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique identifier for the skill |
| `description` | string | Yes | Brief description of the skill |
| `triggers` | list | Yes | Keywords that activate this skill |
| `priority` | int | No | Higher priority skills are selected first (default: 0) |
| `category` | string | No | Optional category for organization |
| `instructions` | string | Yes | Detailed instructions for the LLM |

## Development

### Project Structure

```
dify-agent-skill-plugin/
├── manifest.yaml           # Plugin manifest
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── provider/
│   └── agent_skill.yaml    # Agent provider config
├── strategies/
│   ├── skill_agent.yaml    # Strategy definition
│   └── skill_agent.py      # Strategy implementation
└── skills/
    ├── __init__.py
    ├── base.py             # Skill base classes
    ├── loader.py           # Skill loader
    ├── code_helper/        # Example skill
    ├── docs_helper/        # Example skill
    └── testing_helper/     # Example skill
```

### Running Tests

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=skills tests/
```

## Requirements

- Python 3.12+
- Dify Plugin SDK
- PyYAML
- Pydantic

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

### Adding New Skills

1. Create a new directory under `skills/`
2. Add a `SKILL.md` file with proper frontmatter
3. Optionally add a `config.yaml` for additional settings
4. Test your skill by running the plugin locally
5. Submit a pull request
