# Hermes Adapter

This adapter is packaged as a Hermes skill.

## Install

Copy the `anime-girl-generator` skill directory into the Hermes skills directory:

```bash
mkdir -p ~/.hermes/skills/creative
cp -R .bootstrap/adapters/hermes/anime-girl-generator/. ~/.hermes/skills/creative/anime-girl-generator/
```

## Entry

Hermes should load:

```text
~/.hermes/skills/creative/anime-girl-generator/SKILL.md
```

Hermes help should read:

```text
~/.hermes/skills/creative/anime-girl-generator/HELP.md
```

The skill delegates to the shared project package:
- `.bootstrap/agent.md`
- `.bootstrap/config/runtime.json`
- `.bootstrap/docs/agent-spec.md`
- `.bootstrap/docs/runbooks/comfyui.md`
- `.bootstrap/docs/runbooks/x-publishing.md`
- `.bootstrap/docs/policies/content.md`
