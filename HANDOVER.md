# Handover Notes — Dify Agent Skill Plugin

This document is a technical handover for the next maintainer of the
`dify-agent-skill-plugin` repository. It summarizes what the project is,
how the agent strategy works internally, what was recently changed, and
what to keep in mind when extending or packaging it.

## 1. What This Project Is

A Dify **agent strategy plugin**. It provides a custom agent strategy
("Skill-based Agent") that:

1. Loads a set of markdown/YAML skills from `skills/` plus optional
   runtime-provided custom skills.
2. Matches the user query against skill trigger keywords.
3. Injects the matched skill instructions into the system prompt.
4. Runs an LLM loop with external tool support and streams the response.

Inspired by Claude Code Skills and OpenAI Agents Codex Tool concepts.

## 2. Quick Start

- Development / remote-debug instructions: see `DEVELOPMENT.md`.
- Packaging and installation: see `DEVELOPMENT.md` → "Installation".
- The runtime target is **Python 3.12** (see `manifest.yaml` runner
  section). The plugin depends on **`dify_plugin==0.7.1`**
  (`requirements.txt`).

## 3. Architecture Overview

```
main.py                      Plugin entry point (dify_plugin bootstrap)
manifest.yaml                Plugin manifest; declares the agent strategy
provider/agent_skill.yaml    Agent provider definition
strategies/skill_agent.yaml  Strategy parameter schema (model, tools, query,
                             enabled_skills, custom_skills, debug_mode,
                             maximum_iterations)
strategies/skill_agent.py    The agent strategy implementation (core logic)
skills/                      Skill system
  base.py                    BaseSkill / MarkdownSkill / ConfigSkill
  loader.py                  SkillLoader / SkillRegistry (matching, prompts)
  <name>/SKILL.md            Built-in skills
tests/                       Unit tests + SDK test stubs (see §6)
```

### Agent invoke flow (`SkillAgentAgentStrategy._invoke`)

1. `AgentStrategy.invoke()` (SDK) converts parameters, then calls
   `_invoke(parameters)`.
2. `SkillAgentParams(**parameters)` validates the payload (model becomes
   `AgentModelConfig`, tools become `ToolEntity`).
3. Skills are loaded lazily from the filesystem; `custom_skills` YAML is
   registered at runtime; the query is matched and the combined skill
   prompt is appended to the base system prompt.
4. Agent loop (bounded by `maximum_iterations`):
   - Yield an `Iteration N` log message.
   - Call `session.model.llm.invoke(stream=True)`, streaming text chunks
     as `TEXT` messages.
   - If the response contains tool calls → append an
     `AssistantPromptMessage` carrying them, invoke each tool via
     `session.tool.invoke(...)`, append `ToolPromptMessage` results,
     and loop again.
   - If the response has no tool calls → mark `completed`, finish the
     iteration log, and stop.

## 4. Recent Changes (this handover)

Three production errors were reported when using the plugin with external
tools configured, all fixed against the real `dify_plugin` 0.7.1 API:

| # | Error | Root cause | Fix |
|---|-------|------------|-----|
| 1 | `can only concatenate str (not "list") to str` | Streaming `content` may be a `list` of text content blocks (multi-modal), not only `str` | New `_extract_text_content()` helper joins text blocks (`strategies/skill_agent.py`) |
| 2 | `'dict' object has no attribute 'model_dump'` | Tool definitions were built as raw OpenAI-style dicts; the SDK requires `PromptMessageTool` pydantic models (`LLMInvocation.invoke` calls `tool.model_dump()`) | `_build_tool_definitions()` now delegates to the SDK's `_init_prompt_tools()` |
| 3 | Same `model_dump` error (second occurrence) | Same root cause as #2 (error surfaced in the "Thinking" log and the final text) | Same fix as #2 |

Latent bugs found in the same data flow (would have blocked tools from
ever executing):

- Tool calls were read from `chunk.delta.tool_calls`; the real location is
  `chunk.delta.message.tool_calls`.
- `tc.function.arguments` is a **JSON string** in the SDK, but was splatted
  as a dict (`**tool_args`) — now parsed via `_parse_tool_arguments()`.
- `AssistantPromptMessage(tool_calls=...)` was given tuples; the SDK
  requires `AssistantPromptMessage.ToolCall` objects — the chunk's own
  `ToolCall` objects are now passed through untouched.
- Tool results used `str(result.message)` (pydantic repr); now reads
  `.text` when available.

Code-review follow-ups applied before release:

- Spurious "⚠️ Reached maximum iterations" warning when the agent
  completed on the last allowed iteration — fixed with a `completed` flag.
- Hardcoded `ToolProviderType.BUILT_IN` — now uses
  `tool_instance.provider_type` (so MCP/workflow/api tools route
  correctly).
- Malformed tool-call JSON now raises (surfaced as an error log + message)
  instead of silently invoking the tool with empty arguments.
- Missing tool-call ids fall back to unique `call_<index>` ids.
- The iteration log is now marked `ERROR` when the loop aborts on an
  exception (previously it dangled as `START`).

## 5. SDK Contract Notes (dify_plugin == 0.7.1)

These are the SDK behaviors the strategy relies on. They are the ground
truth for any future change:

- `LLMInvocation.invoke()` serializes everything with `model_dump()`:
  `model_config`, each `PromptMessage`, and each tool — so **tools must
  be `PromptMessageTool` instances**, and messages must be real
  `PromptMessage` subclasses (build them with the SDK constructors, never
  raw dicts).
- `PromptMessage.content` is `str | list[PromptMessageContent] | None`.
  Text blocks are `TextPromptMessageContent` (`type == "text"`, `data`
  carries the text).
- `LLMResultChunk.delta.message` is an `AssistantPromptMessage`; its
  `tool_calls` list is the only place tool calls appear in streaming.
- `ToolCallFunction.arguments` is a `str` (JSON), `id` may be empty.
- `ToolEntity` has `provider_type`, `runtime_parameters`, `identity`,
  `description.llm`, and LLM-form `parameters`.
- The SDK provides `AgentStrategy._init_prompt_tools()` /
  `_convert_tool_to_prompt_message_tool()` — prefer these over hand-rolled
  tool schemas.

**If you upgrade the SDK version**, re-verify every item above against the
new SDK source, and update `tests/stubs/` to match (see §6).

## 6. Testing

The repo has no pytest-based SDK installed locally; tests run against a
**faithful stub** of the `dify_plugin` 0.7.1 API surface:

```
tests/
├── test_skill_agent.py          # 5 tests covering the fixed behaviors
└── stubs/dify_plugin/           # Minimal, SDK-faithful modules
```

Run them with (any Python with pydantic >= 2):

```bash
python3 -m unittest tests.test_skill_agent -v
```

Why stubs: the real SDK requires Python >= 3.11, and the plugin normally
runs inside the Dify plugin daemon. The stubs were written by translating
the real SDK 0.7.1 source (line-by-line) to Python 3.9 syntax, so they
reproduce the exact failure modes (e.g. `model_dump` on dict tools,
content as a list, `arguments` as JSON string). Tests were written
test-first: each one reproduced the production error before the fix.

Test coverage:

1. `test_streaming_content_blocks_do_not_crash` — content as text-block
   list does not crash and streams correctly.
2. `test_tools_pass_prompt_message_tool_models` — tools sent to the LLM
   are `PromptMessageTool` instances.
3. `test_tool_calls_are_extracted_and_executed` — full loop: tool call
   extraction, JSON argument parsing, tool invocation (provider_type
   pass-through), final answer.
4. `test_completes_cleanly_on_last_iteration` — no spurious max-iteration
   warning on boundary completion.
5. `test_malformed_tool_arguments_are_surfaced` — broken JSON arguments
   abort loudly, tool is not invoked.

**Stub-fidelity warning:** if the SDK is upgraded, the stubs must be
updated in lockstep, otherwise green tests can mask real breakage.

## 7. Packaging & Release

```bash
# From the PARENT directory of the plugin folder (required):
dify plugin package ./dify-agent-skill-plugin
# Upload the generated .difypkg via Dify → Plugin Management.
```

- `.difyignore` excludes `.venv`, caches, IDE files, `.env`, build
  artifacts, and `tests/` — the shipped package must not contain the test
  stubs (they shadow the real SDK).
- Package size limit: uncompressed < 50 MB.
- `manifest.yaml` declares resource limits (memory, storage, permissions);
  the plugin needs `tool`, `model` (llm), and `storage` permissions.
- Plugin version is managed in `manifest.yaml` (`version:` field) and the
  `meta.version` block; bump both for release.

## 8. Known Limitations & Next Steps

- **Non-text tool results** fall back to `str(pydantic_model)`; formatting
  JSON tool output as `tool response: {...}` (as official plugins do)
  would improve prompt quality.
- **Malformed tool arguments abort the loop** (by design, with a clear
  error). If model self-correction is desired, feed the parse error back
  to the LLM as a tool message instead.
- **Streaming accumulation assumption**: tool calls are overwritten only
  when a chunk carries a non-empty `tool_calls` list (OpenAI-compatible
  accumulation). Providers that split tool calls across chunks *without*
  accumulation are not supported.
- The iteration-limit path stops with a warning when the loop exhausts
  while tool calls remain; no explicit "abort" tool or token-budget guard
  exists.
- `skills/loader.py` logs load errors with `print()` to stdout; these are
  only visible in the plugin daemon logs.

## 9. Key Files Cheat Sheet

| File | What to touch for |
|------|-------------------|
| `strategies/skill_agent.py` | Agent behavior, prompt construction, tool loop |
| `skills/base.py` | Skill model / matching semantics |
| `skills/loader.py` | Skill discovery, YAML frontmatter, registry |
| `strategies/skill_agent.yaml` | Agent strategy parameters (schema for Dify UI) |
| `tests/test_skill_agent.py` | Behavior tests (edit first, then code) |
| `tests/stubs/dify_plugin/` | SDK simulation (update on SDK upgrades) |
| `manifest.yaml` | Plugin metadata, version, permissions |
