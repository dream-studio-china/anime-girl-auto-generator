# Codex Adapter

This adapter provides Codex-friendly entry points for the Bootstrap agent package.

## Standard Entry

Use `AGENTS.md` as the Codex instruction file. Copy or symlink it into the Codex working directory when you want Codex to operate as this agent:

```bash
ln -sf .bootstrap/adapters/codex/AGENTS.md AGENTS.md
```

## Optional Agent Config

`codex.yaml` preserves the older explicit `agents.bootstrap` style configuration. Merge it into a project-level `codex.yaml` only if your Codex runtime supports named agents:

```bash
cat .bootstrap/adapters/codex/codex.yaml >> codex.yaml
```

## Source Of Truth

The adapter should defer to:
- `.bootstrap/agent.md`
- `.bootstrap/docs/agent-spec.md`
- `.bootstrap/docs/runbooks/comfyui.md`
- `.bootstrap/docs/runbooks/x-publishing.md`
- `.bootstrap/docs/policies/content.md`
