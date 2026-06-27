# Hermes Adapter

This adapter is packaged as a Hermes skill.

## Install

Copy the `bootstrap` skill directory into the Hermes skills directory:

```bash
mkdir -p ~/.hermes/skills
mkdir -p ~/.hermes/skills/bootstrap
cp -R .bootstrap/adapters/hermes/bootstrap/. ~/.hermes/skills/bootstrap/
```

## Entry

Hermes should load:

```text
~/.hermes/skills/bootstrap/SKILL.md
```

Hermes help should read:

```text
~/.hermes/skills/bootstrap/HELP.md
```

The skill delegates to the shared project package:
- `.bootstrap/agent.md`
- `.bootstrap/config/runtime.json`
- `.bootstrap/docs/agent-spec.md`
- `.bootstrap/docs/runbooks/comfyui.md`
- `.bootstrap/docs/runbooks/x-publishing.md`
- `.bootstrap/docs/policies/content.md`
