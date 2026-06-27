# Bootstrap Manifest

## Agent Name

bootstrap

## Version

0.2.0

## Architecture

Thin prompt plus runbooks and policies.

## Entry Points

| Runtime | Entry |
|---------|-------|
| opencode | `.opencode/agents/bootstrap.md` |
| shared prompt | `.bootstrap/agent.md` |
| Codex | `.bootstrap/adapters/codex/AGENTS.md` |
| Codex named agent config | `.bootstrap/adapters/codex/codex.yaml` |
| Hermes | `.bootstrap/adapters/hermes/bootstrap/SKILL.md` |
| OpenClaw | `.bootstrap/adapters/openclaw/IDENTITY.md` |

## Source Of Truth

| Concern | File |
|---------|------|
| Behavior contract | `.bootstrap/docs/agent-spec.md` |
| ComfyUI operations | `.bootstrap/docs/runbooks/comfyui.md` |
| X reviewed publishing | `.bootstrap/docs/runbooks/x-publishing.md` |
| Content policy | `.bootstrap/docs/policies/content.md` |
| Runtime policy values | `.bootstrap/config/runtime.json` |

## Safety Model

Publishing is semi-automatic. Generation and analysis may be automated, but posting to X/Twitter requires a user-approved review card and `--reviewed` at the script layer.
