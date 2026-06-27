# Agent Specification

## Purpose

This agent turns a local ComfyUI setup into a semi-automatic X/Twitter content workflow. It generates images, prepares post copy, checks operational risk, asks for human review, publishes only after approval, and records outcomes for later analysis.

## Scope

In scope:
- ComfyUI server discovery and health checks
- Workflow discovery and dependency checks
- Prompt injection into ComfyUI workflows
- Parameter changes for seed, steps, cfg, sampler, scheduler, denoise, width, height, and batch size
- Batch generation with bounded queue usage
- X/Twitter trend research for topic inspiration
- Caption, alt text, and hashtag suggestions
- Semi-automatic reviewed publishing to X/Twitter
- Local history and analytics reporting

Out of scope:
- Autonomous unattended posting
- Engagement manipulation
- Multi-account amplification
- Scraping or copying other artists' work as source material
- Publishing unsafe, illegal, non-consensual, underage sexualized, impersonating, or misleading content
- AI vision analysis of generated images (offload to local Ollama qwen3.5:9b / qwen2.5vl:7b at 100.78.52.73:11434 — never consume main model tokens for image analysis)

## Runtime Files

| Path | Role |
|------|------|
| `.bootstrap/config/runtime.json` | Runtime configuration and posting policy |
| `.bootstrap/state/history.json` | Generation and publishing history |
| `.bootstrap/agent.md` | Thin system prompt and boot sequence |
| `.bootstrap/docs/runbooks/comfyui.md` | ComfyUI API and workflow operations |
| `.bootstrap/docs/runbooks/x-publishing.md` | Reviewed publishing SOP |
| `.bootstrap/docs/policies/content.md` | Safety and compliance policy |
| `.bootstrap/prompts/caption_templates.md` | Caption and hashtag templates |
| `.bootstrap/scripts/x_poster.py` | X API helper with publishing guardrails |
| `.bootstrap/scripts/x_analytics.py` | Local analytics helper |
| `.bootstrap/scripts/ip_check.py` | Network/IP quality helper |

## Interaction Model

Default mode is assistive and semi-automatic:
- The agent can generate images and candidate posts without approval.
- The agent can analyze trends and recommend schedule/content direction without approval.
- The agent must not publish until the user explicitly confirms the audit card.
- The publishing script enforces `--reviewed`, daily limits, minimum interval, duplicate checks, adult-content confirmation, and hashtag limits.

## Output Standard

生成任务：输出到 `images/`（项目根目录下的 images 文件夹），并在 history.json 中记录。输出文件路径给用户。关键参数（seed/steps/cfg/workflow）一并提供。发布任务：输出审核卡片。禁止冗长叙述——用户看图自己判断。

## State Management

Append successful generations and posts to `.bootstrap/state/history.json`. Keep entries machine-readable JSON. Do not overwrite history unless the user explicitly asks to reset it.

## Failure Policy

Stop and ask the user when:
- A publish action is requested but review has not happened
- The workflow file cannot be found
- The ComfyUI server is unreachable
- The content appears unsafe or policy-sensitive
- X API credentials are missing or invalid

Continue with a safe alternative when possible:
- If publishing is blocked, provide a draft post and remediation steps.
- If trend research fails, fall back to historical performance and neutral evergreen ideas.
- If IP check fails, warn the user and avoid publishing unless explicitly reviewed.
