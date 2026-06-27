# ComfyUI Runbook

## Configuration

Read `.bootstrap/config/runtime.json` for:
- `comfyui_server`
- `default_user`
- `default_workflow`

Normalize `comfyui_server` by removing a trailing slash before building API URLs.

## API Reference

| Operation | Command |
|-----------|---------|
| List users | `curl -s {SERVER}/users` |
| System stats | `curl -s {SERVER}/system_stats` |
| List model types | `curl -s {SERVER}/models` |
| List checkpoints | `curl -s {SERVER}/models/checkpoints` |
| List LoRAs | `curl -s {SERVER}/models/loras` |
| List VAEs | `curl -s {SERVER}/models/vae` |
| Node info | `curl -s {SERVER}/object_info/{NODE_CLASS}` |
| List workflows | `curl -s "{SERVER}/userdata?user={USER}&dir=workflows"` |
| Fetch workflow | `curl -s "{SERVER}/userdata/{WORKFLOW}?user={USER}"` |
| Submit prompt | `curl -s -X POST {SERVER}/prompt -H "Content-Type: application/json" -d '{"prompt":{WORKFLOW_JSON},"client_id":"bootstrap-agent"}'` |
| Queue status | `curl -s {SERVER}/queue` |
| Prompt history | `curl -s "{SERVER}/history/{PROMPT_ID}"` |
| Download output | `curl -s -o "images/{FILENAME}" "{SERVER}/view?filename={F}&subfolder={S}&type=output"` |

## First-Time Setup

If `comfyui_server`, `default_user`, or `default_workflow` is missing:

1. Ask for ComfyUI server URL.
2. Call `/users` and ask user to choose a user.
3. Call `/userdata?user={USER}&dir=workflows` and ask user to choose a workflow.
4. Update `.bootstrap/config/runtime.json` while preserving existing keys.

## Default Generation

1. Read config.
2. Fetch default workflow JSON.
3. Submit workflow to `/prompt`.
4. Parse `prompt_id`.
5. Poll `/queue` every 2 seconds until the prompt is no longer running or pending.
6. Fetch `/history/{prompt_id}`.
7. Download all image outputs into `images/`.
8. Append a generation record to `.bootstrap/state/history.json`.
9. Report output paths.

## Prompt Injection

When user provides a prompt:

1. Locate nodes with `class_type` containing `CLIPTextEncode`.
2. Prefer nodes whose title or metadata includes `positive`, `prompt`, or similar positive-prompt labels.
3. Replace `inputs.text` for the positive prompt.
4. If a negative prompt is provided, replace the negative prompt node.
5. If there are multiple ambiguous text nodes, show a short summary and ask which to modify.

## Parameter Changes

| User Parameter | Node Type | Field |
|----------------|-----------|-------|
| seed | `KSampler` | `inputs.seed` |
| steps | `KSampler` | `inputs.steps` |
| cfg | `KSampler` | `inputs.cfg` |
| sampler | `KSampler` | `inputs.sampler_name` |
| scheduler | `KSampler` | `inputs.scheduler` |
| denoise | `KSampler` | `inputs.denoise` |
| width | `EmptyLatentImage` | `inputs.width` |
| height | `EmptyLatentImage` | `inputs.height` |
| batch_size | `EmptyLatentImage` | `inputs.batch_size` |

Before submitting, summarize changed parameters.

## Batch Generation

Batch generation is allowed for image generation, not for unattended publishing.

Rules:
- Keep batches bounded by the user's requested range.
- Warn if many jobs will queue.
- Record prompt IDs and parameter variants.
- Download outputs with prefixes such as `seed_42_` or `cfg_7_`.
- Publishing batch outputs must still go through one review card per post.

## Workflow Dependency Check

For dependency checks:

1. Parse loader nodes such as `CheckpointLoader`, `LoraLoader`, `VAELoader`, and ControlNet loaders.
2. Compare model names against `/models/{type}` endpoints.
3. Report installed, missing, and uncertain dependencies.

## Error Handling

| Error | Action |
|-------|--------|
| Server unavailable | Ask user to check URL and ComfyUI process |
| User missing | List users and ask again |
| Workflow missing | List workflows and ask again |
| Prompt submit error | Show ComfyUI `node_errors` or API error |
| Long generation | Ask whether to keep waiting or interrupt after 5 minutes |
| Download failure | Retry once, then report failed filename/subfolder |
| Missing model | Report missing model and do not submit unless user confirms |
