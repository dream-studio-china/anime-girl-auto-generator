# Bootstrap Manifest

## Agent Name

bootstrap

## Version

0.3.0

## Architecture

Thin prompt + runbooks + policies. Hermes native skill at `~/.hermes/skills/creative/bootstrap/`.

## Entry Points

| Runtime | Entry |
|---------|-------|
| Hermes | `~/.hermes/skills/creative/bootstrap/SKILL.md` (primary) |
| Shared prompt | `.bootstrap/agent.md` |
| Codex | `.bootstrap/adapters/codex/AGENTS.md` |
| OpenClaw | `.bootstrap/adapters/openclaw/IDENTITY.md` |

## Source Of Truth

| Concern | File |
|---------|------|
| Behavior contract | `~/.hermes/skills/creative/bootstrap/SKILL.md` |
| Runtime config | `.bootstrap/config/runtime.json` |
| ComfyUI operations | `.bootstrap/docs/runbooks/comfyui.md` |
| X reviewed publishing | `.bootstrap/docs/runbooks/x-publishing.md` |
| Content policy | `.bootstrap/docs/policies/content.md` |
| Caption templates | `.bootstrap/prompts/caption_templates.md` |
| Image analysis | Ollama qwen3.5:9b / qwen2.5vl:7b @ 100.78.52.73:11434 |

## Safety Model

Publishing is semi-automatic. Generation and analysis may be automated, but posting to X/Twitter requires a user-approved review card and `--reviewed` at the script layer. Image analysis offloaded to local Ollama — main model tokens are never consumed for vision tasks.
