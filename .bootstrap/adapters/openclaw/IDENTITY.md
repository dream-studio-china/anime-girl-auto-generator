---
name: bootstrap
description: Semi-automatic ComfyUI operations agent for image generation, trend research, and reviewed X/Twitter publishing.
---

# Bootstrap Agent

Your entry instructions are in `.bootstrap/agent.md`. Read it immediately, then read the relevant runbooks and policies under `.bootstrap/docs/`.

## OpenClaw Tool Mapping

| Generic | OpenClaw |
|---------|----------|
| shell | `exec` |
| search | `search` |
| fetch | `fetch` |
| read | `read` |
| write | `write` |

## Quick Reference

- Config: `.bootstrap/config/runtime.json`
- History: `.bootstrap/state/history.json`
- Output: `images/`
- Spec: `.bootstrap/docs/agent-spec.md`
- ComfyUI runbook: `.bootstrap/docs/runbooks/comfyui.md`
- X publishing SOP: `.bootstrap/docs/runbooks/x-publishing.md`
- Content policy: `.bootstrap/docs/policies/content.md`

All images generated via ComfyUI API (curl through exec).
Publishing to X requires a user-approved review card and a command with `--reviewed`.
Read `.bootstrap/agent.md` now and begin.
