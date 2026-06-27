# ComfyUI Runbook

## Configuration

Read `.bootstrap/config/runtime.json` for:
- `comfyui_server`
- `default_user`
- `default_workflow`

Normalize `comfyui_server` by removing a trailing slash before building API URLs.

## API Reference (仅直接用法，完整 API 见表末)

```bash
SERVER=http://100.78.52.73:8188
# 提交生成
curl -s -X POST {SERVER}/prompt -H "Content-Type: application/json" -d '{"prompt":{JSON},"client_id":"bootstrap"}'
# 查历史
curl -s "{SERVER}/history/{ID}"
# 下载
curl -s -o "images/{FILE}" "{SERVER}/view?filename={F}&subfolder={S}&type=output"
```

## First-Time Setup

已配置完毕，无需操作。若 server/user/workflow 缺失，问用户即可。

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
10. 图片分析走 Ollama 本地模型 (qwen3.5:9b / qwen2.5vl:7b @ 100.78.52.73:11434)，禁止用主模型。

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

用到时再查：对比 loader 节点中的模型名 vs `/models/{type}` 端点。

## Error Handling

Server 不可达 → 问用户检查。生成超时 5 分钟 → 问是否继续等。其余错误直接报原文。
