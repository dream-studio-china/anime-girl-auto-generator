# Bootstrap Agent

This is a semi-automatic ComfyUI to X/Twitter publishing agent.

The package uses a layered agent layout: thin entry prompt, runtime config, state, prompts, executable scripts, framework adapters, runbooks, and policies.

## Directory Structure

```text
.bootstrap/
├── agent.md                         # Thin agent entry prompt
├── MANIFEST.md                      # Package metadata and source-of-truth map
├── README.md                        # Human-readable package guide
├── tools.yaml                       # Cross-framework tool mapping
├── config/
│   └── runtime.json                 # Runtime config and posting policy
├── state/
│   └── history.json                 # Generation and publishing history
├── prompts/
│   └── caption_templates.md         # Caption and hashtag templates
├── scripts/
│   ├── x_poster.py                  # X API helper with publishing guardrails
│   ├── x_analytics.py               # Analytics helper
│   └── ip_check.py                  # IP quality helper
├── docs/
│   ├── agent-spec.md                # Agent scope and behavior contract
│   ├── runbooks/
│   │   ├── comfyui.md               # ComfyUI operations runbook
│   │   └── x-publishing.md          # Reviewed publishing SOP
│   └── policies/
│       └── content.md               # Content and platform safety policy
└── adapters/
    ├── codex/
    │   ├── AGENTS.md
    │   ├── README.md
    │   └── codex.yaml
    ├── hermes/
    │   ├── README.md
    │   └── bootstrap/SKILL.md
    └── openclaw/IDENTITY.md
```

## Framework Adapters

Codex standard entry:

```bash
ln -sf .bootstrap/adapters/codex/AGENTS.md AGENTS.md
```

Hermes standard skill package:

```bash
mkdir -p ~/.hermes/skills
cp -R .bootstrap/adapters/hermes/bootstrap ~/.hermes/skills/bootstrap
```

## Operating Model

The agent may automatically:
- generate images with ComfyUI
- prepare captions, hashtags, and alt text
- research trends for topic inspiration
- analyze local publishing history

The agent must not automatically:
- publish to X/Twitter without a user-approved review card
- post without `--reviewed`
- post adult/edge content without `--adult-content`
- use unrelated trending hashtags
- perform engagement manipulation

## Core Workflows

| Workflow | Description | Source |
|----------|-------------|--------|
| Generate image | Submit ComfyUI workflow and download outputs | `docs/runbooks/comfyui.md` |
| Modify parameters | Change seed/steps/cfg/resolution before generation | `docs/runbooks/comfyui.md` |
| Batch generation | Generate bounded variants for review | `docs/runbooks/comfyui.md` |
| Trend research | Produce content ideas and relevant tags | `docs/runbooks/x-publishing.md` |
| Reviewed publishing | Publish only after user approval | `docs/runbooks/x-publishing.md` |
| Content safety | Apply adult/minor/copyright/hashtag rules | `docs/policies/content.md` |

## Quick Start

1. Confirm config:

```bash
python -m json.tool .bootstrap/config/runtime.json
```

2. Install X API dependency if publishing:

```bash
pip install tweepy
```

3. Use from opencode:

```text
@bootstrap 生成图片
@bootstrap 生成并发布
@bootstrap 查趋势
@bootstrap 分析报告
```

4. Publish only after review:

```bash
python .bootstrap/scripts/x_poster.py post \
  -i "images/xxx.png" \
  -c "caption" \
  -t "animegirl,AIart,ComfyUI" \
  -a "AI generated anime girl artwork" \
  --reviewed
```

## Configuration

`config/runtime.json` contains:
- ComfyUI server/user/workflow defaults
- X API credentials
- default caption/tag preferences
- posting policy guardrails

Current default posting policy:
- semi-automatic review mode
- 5 posts per day
- 120 minute minimum interval
- 6 hashtags maximum
- `--reviewed` required
- `--adult-content` required for adult/edge content

## Validation

Run:

```bash
python -m json.tool .bootstrap/config/runtime.json >/dev/null
python -m py_compile .bootstrap/scripts/x_poster.py .bootstrap/scripts/x_analytics.py .bootstrap/scripts/ip_check.py
```
