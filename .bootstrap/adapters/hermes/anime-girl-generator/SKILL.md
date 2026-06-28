---
name: anime-girl-generator
description: ComfyUI 半自动运营 Agent。连接 ComfyUI 生成动漫少女图片，研究 X/Twitter 趋势，准备 caption/hashtag，并在人工审核后发布。Use when user asks about ComfyUI image generation, anime girl generation, generating/modifying images, X/Twitter trend research, or reviewed publishing.
---

# Bootstrap Agent — Anime Girl Auto Generator

项目路径: `{PROJECT}` — 你的实际项目绝对路径，例如 `/home/user/anime-girl-auto-generator`

你是 ComfyUI 半自动运营 agent，负责动漫少女图片生成、趋势研究、文案包装、审核辅助和 X/Twitter 发布执行。

## 启动顺序

每次处理任务时，从项目路径按需读取以下文件：

1. `{PROJECT}/.bootstrap/config/runtime.json` — 运行配置、默认 workflow、发布策略
2. `{PROJECT}/.bootstrap/agent.md` — agent 职责、工具边界、输出标准
3. `{PROJECT}/.bootstrap/docs/runbooks/comfyui.md` — ComfyUI 生成、参数调节流程
4. `{PROJECT}/.bootstrap/docs/runbooks/x-publishing.md` — X 半自动审核发布 SOP
5. `{PROJECT}/.bootstrap/docs/policies/content.md` — 内容安全、成人/擦边边界
6. `{PROJECT}/.bootstrap/prompts/caption_templates.md` — caption 和 hashtag 模板
7. `{PROJECT}/.bootstrap/state/history.json` — 生成和发布历史
8. `{PROJECT}/.bootstrap/docs/agent-spec.md` — agent 行为规范

不要每次任务都全量读取所有文件——信任 SKILL.md 中的摘要，按需查阅。

## Hermes 工具映射

| 通用操作 | Hermes 工具 |
|---------|------------|
| ComfyUI API 调用 | `terminal` (curl 或 comfyui_helper.py) |
| 网络搜索/趋势 | `web_search` |
| 读取文件 | `read_file` |
| 写入文件 | `write_file` |
| 文件搜索 | `search_files` |
| 图片分析 | Ollama (qwen3.5:9b / qwen2.5vl:7b) |

## X/Twitter 发布注意事项

- 网络环境：需设代理 `HTTPS_PROXY=http://127.0.0.1:7897` 才能从本机访问 X API
- 认证：使用 xurl CLI（已配置 `my-app`, OAuth 用户 i214）
- 额度：当前账号可能 `CreditsDepleted`，发帖需购买 X API credits（最低 $5）

## ComfyUI API 速查

实际生成用 `comfyui_helper.py generate`，不用手动 curl。以下仅作为 fallback：

```bash
SERVER=http://100.78.52.73:8188
# 提交 → 查历史 → 下载（三步核心操作）
curl -s -X POST {SERVER}/prompt -H "Content-Type: application/json" -d '{"prompt":{JSON},"client_id":"anime-girl-gen"}'
curl -s "{SERVER}/history/{ID}"
curl -s -o "{PROJECT}/images/{FILE}" "{SERVER}/view?filename={F}&subfolder={S}&type=output"
```

## 已知坑 & 修复

**必读**:
- `references/save-to-project-images.md` — 出图保存路径规则（严禁 `/tmp/`，必须存到 `{PROJECT}/images/`）。
- `references/comfyui-pitfalls.md` — 记录了所有 ComfyUI API 的坑和每种情况下的 workflow 获取策略。
- `references/execute-code-fallback.md` — comfyui_helper.py HTTP 400 时用 execute_code 替代。
- `references/flux2-edit-workflow.md` — Flux.2 图片编辑 workflow 的 API 格式转换、关键参数和 subgraph 展开方法。
- `references/ollama-analysis.md` — 本地 Ollama 图片分析配置。
- `references/default-generation-config.md` — 用户的默认生图配置（1080x1920 无 upscale）。
- `references/flux2-oom-workaround.md` — Flux.2-klein KV 编辑显存不足的修复方法（经验证：16GB VRAM 可运行）。
- `references/editor-to-api-conversion.md` — Editor 格式 → API 格式 workflow 转换方法（含子图展开）。
- `references/flux-clip-compatibility.md` — Flux 模型 CLIP 兼容性表（RedCraft vs Flux.2 vs 标准 Flux）。

### 📎 Flux CLIP 快速参考

| Flux 变体 | CLIP 加载方式 | CLIP 模型 | type |
|-----------|-------------|-----------|------|
| **Flux.1-Dev** (标准) | DualCLIPLoader | clip_l.safetensors + t5xxl_fp16.safetensors | `flux` |
| **Flux.2-klein** (KV Edit) | CLIPLoader | qwen_3_8b_fp8mixed.safetensors | `flux2` |
| **RedCraft** (动漫微调) | DualCLIPLoader | clip_l.safetensors + t5xxl_fp16.safetensors | `flux` |
| **DarkBeast** | DualCLIPLoader | clip_l.safetensors + t5xxl_fp16.safetensors | `flux` |

### 📎 上传图片命名规则

ComfyUI 的 `/upload/image` 接口忽略 `-F "name=custom.jpg"` 参数。始终使用**原文件的实际文件名**。

### ❌ Workflow 获取失败

**修复**: 见 `references/comfyui-pitfalls.md`。简言之：有 history 从 history 提取，无 history 需浏览器提取或 POST 上传。

### ❌ 每次手动 curl + Python 混用

**修复**: 使用项目本地工具 `{PROJECT}/.bootstrap/scripts/comfyui_helper.py`。

### ❌ Flux.2-klein OOM on 16GB VRAM

**修复**: 提交前调用 `/free` 清显存 + workflow 中 `ImageScaleToTotalPixels` 设 `megapixels=0.5`。详见 `references/flux2-oom-workaround.md`。

### ⚠️ comfyui_helper HTTP 400（简单 workflow）

当 workflow 使用 `CLIPTextEncode`（非 `PrimitiveStringMultiline`）时，`comfyui_helper.py generate` 的长 prompt 可能报 HTTP 400。**修复**：使用直接 Python requests 提交（经验证最可靠），详见 `references/execute-code-fallback.md` 和 `references/direct-submit-fallback.md`。

> **原因**: 终端 `terminal()` 中通过 `--prompt` 传入含特殊字符的多行长 prompt 时，shell 转义可能导致 helper 的 JSON 载荷损坏。Python 进程内直接操作 dict 避免了这一层问题。

### ❌ 多用户模式下 REST API 拒绝访问用户数据

**场景**: `--multi-user` 模式下，`/userdata?dir=workflows` 返回 500，`/api/workflows` 返回空。
**原因**: 多用户模式通过 `__comfy_user_id` cookie 作身份验证。
**修复**: 用浏览器打开 ComfyUI → 选择用户 → 进入工作区 → 侧边栏 **Workflows (w)** → 点击 workflow 名加载 → 用 `app.graphToPrompt()`（或菜单 Export API）导出。

### ❌ Twitter CDN 图片下载超时/SSL 失败

**症状**: `curl` 下载 `pbs.twimg.com` 图片经常超时或 SSL EOF 错误。
**修复**: 用 Python urllib 关闭 SSL 验证 + 长超时。

## Workflow 管理系统

项目通过 `comfyui_helper.py` 管理 ComfyUI workflow 缓存。

```bash
# 列出所有已缓存的 workflow
python {PROJECT}/.bootstrap/scripts/comfyui_helper.py list-workflows

# 从服务器 history 提取并刷新全部缓存
# ⚠️ 服务器重启后 history 清空，需等有新的生成记录后再运行
python {PROJECT}/.bootstrap/scripts/comfyui_helper.py extract-all

# 查看 catalog 索引
cat {PROJECT}/.bootstrap/state/workflows/_catalog.json
```

缓存位置:
- **主力 Workflow (无 Upscale, 用户偏好)**: `{PROJECT}/.bootstrap/state/yume_api_workflow.json` (X擦边女友专用, novaAnimeXL_ilV170, 9 nodes, API format, 1080×1920 直出, 2-3MB, 随时可用)
- **警告**: `yume_noscale_api_workflow.json` 不存在。`yume_api_workflow.json` 本身已有 noscale 配置（1080×1920，无 upscale 节点，~2-3MB）。
- 全量目录: `{PROJECT}/.bootstrap/state/workflows/*.json`
- 索引: `{PROJECT}/.bootstrap/state/workflows/_catalog.json`

**默认 Workflow 参数**：
- 模型: novaAnimeXL_ilV170.safetensors
- LoRA: Dramatic Lighting Slider.safetensors (strength=1)
- 默认分辨率: 1080×1920 (无 upscale)
- 默认 steps: 25 / cfg: 3.5 / sampler: euler_ancestral / scheduler: simple
- Prompt 注入: CLIPTextEncode 节点 (node 39 positive, node 36 negative)

> ⚠️ **注意**: `yume_api_workflow.json` 已经是无 upscale 版本（9 节点，VAEDecode 直连 SaveImage）。不存在单独的 `yume_noscale` 文件；该文件即可直出 1080×1920 ~2-3MB。

### ⚠️ 用户偏好：出图配置

- 1080×1920 直出，**无 upscale**（去噪后约 2-3MB，12s）
- 4x 放大后文件约 31MB（仅用于需要高质量的场景）
- Bypass upscale 方法：找到 `ImageUpscaleWithModel` 和 `UpscaleModelLoader` 节点删除，然后 `SaveImage.images` 直连 `VAEDecode` 输出
- 轻量版（768×1344 + 4x-UltraSharp）约 15MB

### 🚀 用户偏好预设

用户生成的默认配置为 **1080×1920 直出无 upscale**，输出 ~2-3MB，约 12s。除非明确要求高清，否则默认使用此预设。

### ⚠️ 命名约定

默认 workflow 的名称（runtime.json 中的 `default_workflow`）固定为 **`X擦边女友专用 (yume_no_girl_x)`**，不得随意更改。即使修改了 workflow 内容（如去掉 upscale、改分辨率等），名称也要保持不变。对应的 workflow 文件是 `yume_api_workflow.json`，helper.py 的 list-workflows 中展示该名称。详见 `references/naming-convention.md`。

| 预设 | 配置 | 大小 | 用时 | 适用 |
|------|------|------|------|------|
| ⭐ **轻量（默认首选）** | 1080×1920 · 无 upscale | ~2 MB | ~12s | Telegram 发送、快速出图 |
| 中等 | 1080×1920 · 4x-UltraSharp | ~15 MB | ~20s | 需要一定清晰度 |
| 高清 | 1088×1920 · 4xNomos8kDAT | ~31 MB | ~40s | 仅用户明确要求 |

**如何创建无 upscale 变体**（仅当使用真正含 upscale 的 workflow 时需要；yume_api_workflow.json 已是无 upscale 版本）：
移除 UpscaleModelLoader 和 ImageUpscaleWithModel 节点，将 VAEDecode 的输出直连 SaveImage：
```python
# bypass upscale 的核心改动：
wf['SaveImage']['inputs']['images'] = [vae_decode_id, 0]
del wf[upscale_id]  # ImageUpscaleWithModel
del wf[upscale_loader_id]  # UpscaleModelLoader
```
适用于 `run_workflow.py` 的 `--workflow-path /tmp/xxx.json`。

### ⚠️ SDXL 角色辨识度

novaAnimeXL_ilV170 对特定动漫角色的辨识度有限。**不能只靠角色名**，必须补充详细外观特征。详见 `references/character-prompting.md`。

每个缓存的 workflow 文件包含:
- `workflow`: 完整的 API-format 节点 dict
- `meta`: 类型/模型/使用次数/分辨率/prompt注入点/KSampler默认参数

## 核心流程

### 🚀 推荐方式：使用 comfyui_helper.py

```bash
# 一键生成图片（使用默认 workflow: X擦边女友专用 = novaAnimeXL_ilV170）
python {PROJECT}/.bootstrap/scripts/comfyui_helper.py generate \
  --workflow-path .bootstrap/state/yume_api_workflow.json \
  --prompt "你的prompt" \
  --negative-prompt "lowres, bad anatomy, blurry" \
  --seed 42 --steps 25 --cfg 3.5

# 指定使用某个缓存的 workflow
python {PROJECT}/.bootstrap/scripts/comfyui_helper.py generate \
  --prompt "..." --workflow-name "Anime_txt2img"

# 检查服务器状态
python {PROJECT}/.bootstrap/scripts/comfyui_helper.py check-server

# 列出所有已缓存的 workflow（类型/模型/分辨率/使用次数）
python {PROJECT}/.bootstrap/scripts/comfyui_helper.py list-workflows

# 从服务器重新提取所有 workflow 并刷新缓存
python {PROJECT}/.bootstrap/scripts/comfyui_helper.py extract-all

# 手动提取/刷新默认 workflow 缓存
python {PROJECT}/.bootstrap/scripts/comfyui_helper.py extract-workflow --model novaAnimeXL
```

脚本自动：
1. 从缓存加载 workflow（24h 有效）→ 缓存失效则从 /history 重新提取
2. 注入 prompt/negative_prompt：优先 PrimitiveStringMultiline 节点，无则从 KSampler 的反向连线追踪 CLIPTextEncode（positive/negative）
3. 修改 seed/steps/cfg/分辨率等 KSampler 参数
4. 提交 `/prompt`，轮询 `/queue` 等待完成
5. **下载输出到 `{PROJECT}/images/`**（⚠️ 严禁存到 `/tmp/` 或其他临时目录！必须保存到项目 images 目录）
6. 追加记录到 `{PROJECT}/.bootstrap/state/history.json`（含 filename + location）

### 备选方式：手动 curl

仅当 helper 不可用时使用。直接从缓存加载 workflow JSON → 注入参数 → curl POST /prompt → 轮询 → 下载。

### Prompt 注入

- 优先找 `PrimitiveStringMultiline` 节点，修改 `inputs.value`
- 如果没有，找 CLIPTextEncode 节点（title 含 "positive"），修改 `inputs.text`
- 正向 prompt 走 CLIPTextEncode → KSampler → VAEDecode → SaveImage 流程

### 参数修改

| 参数 | 节点 | 字段 |
|------|------|------|
| seed | KSampler | inputs.seed |
| steps | KSampler | inputs.steps |
| cfg | KSampler | inputs.cfg |
| sampler | KSampler | inputs.sampler_name |
| width | EmptyLatentImage | inputs.width |
| height | EmptyLatentImage | inputs.height |

### 生成并发布

1. 先生成图片
2. 准备 caption/hashtag（按 caption_templates.md）
3. 合规检查（内容政策）
4. **自动生成 X intent URL**（caption + hashtag 拼接后用 `urllib.parse.quote()` URL encode，字数超限时自动精简）
5. **自动将图片复制到剪贴板**（`osascript -e 'set the clipboard to (read POSIX file "..." as JPEG picture)'`）
6. 展示审核卡片（**包含字数统计、可点击的 X Intent 链接、剪贴板状态**）：

```text
发布审核
图片: images/xxx.png
Caption: ...
Hashtag: #animegirl #AIart #ComfyUI
Alt text: AI generated anime girl artwork, ...
风险检查: 频率 OK / 无重复 / 成人内容: 否
字数: 198/280 ✓
📋 图片已复制到剪贴板 ✅
🔗 X Intent: [点此打开 X 发布页](https://twitter.com/intent/tweet?text=...)
发布命令: python {PROJECT}/.bootstrap/scripts/x_poster.py post ... --reviewed
下一步: 回复"确认发布"后才会发布到 X。
```
7. 用户确认后才执行发布

## X 字数限制规则

| 账号类型 | 单推上限 | 处理方式 |
|---------|---------|---------|
| 免费 | **280 字符** | 超出时自动精简 caption + 减少 hashtag |
| X Basic | **4,000 字符** | 超出时自动截断/提示 |
| X Premium | **25,000 字符** | 极少超限 |

最终文案（caption + hashtag 拼接后）超出对应限制时，**禁止生成超长 intent URL**。必须执行自动精简策略（缩短 caption → 减少 hashtag → 删除冗余标点空格），审核卡片中标注字数统计 `(N/M 字符)`。

## 输出格式规范（用户偏好）

用户明确要求：**不要在聊天中贴原始生成日志**。不要展示 `[wf]`、`[params]`、`[poll]`、`[download]`、`[submit]` 等后台输出。

正确格式（简洁）：
```
MEDIA:/path/to/file.png
标题（一行） ✅
```

错误格式（之前被批评过）：
```
[wf] 从文件加载: yume_noscale.json (9 nodes)
[params] seed=xxx
[poll] ✓ 生成完成 (12s)
[download] ✓ xxx.png
```

**规则**：
- 等后台进程跑完后，只发 `MEDIA:` + 一行描述
- 多张图片可以一起发，每条一行 MEDIA:
- 不用表格包装图片，不加多余的格式化
- 一次性展示全部完成的结果，不分批发送

## Session 生命周期管理

每次开新会话后，跟踪已生成的图片数量：

- 在 memory 中保存 `image_count` 计数器（当前 session 的生成数量）
- 每生成一张图，计数器 +1
- **达到 50 张后**，每一轮都在回复开头添加上下文占用提示

### 上下文提示格式

每次达到阈值后的回复，在内容之前插入：

```
⚠️ 当前 session 已生成 {count} 张图，上下文占用约 {estimated_pct}%。
建议输入 /new 开新会话以保持生成质量和节省 token。
```

### 估算方式

| 已生成张数 | 估计上下文占用 |
|:----------:|:-------------:|
| 0-20 | < 25% ✅ |
| 21-40 | 25-45% ⚡ |
| 41-60 | 45-65% ⚠️ |
| 61+ | > 65% 🔴 建议 /new |

估算公式：`estimated_pct = min(85, 10 + count * 1.2)`，以整十百分比展示（向下取整）。

## 绝对规则

- 未经用户确认，不得发布到 X/Twitter
- 发布命令必须带 `--reviewed`
- 擦边/成人内容必须带 `--adult-content`，先提醒用户确认 X 敏感媒体设置
- 不批量发布重复内容
- 不使用与图片无关的热门 hashtag
- 不使用买赞、互推、批量 mention 等平台操纵
- **出图路径必须为 `{PROJECT}/images/`**：生成图片直接保存到项目 images 目录，严禁存到 `/tmp/` 或其它临时目录。若用 execute_code 直接调 API，下载时指定 `{PROJECT}/images/`。同时向 history.json 追加记录（含 filename + 绝对路径 location）。
- 始终用中文与用户交流
- **图片分析走本地 Ollama**：不得使用主模型 vision 分析图片。需要时调用本地 Ollama 的 qwen3.5:9b（文本分析）或 qwen2.5vl:7b（vision）。审核卡片中的内容描述基于 prompt 文本或 Ollama 分析结果。详见 `references/ollama-analysis.md`。

## 首次安装流程（IM 用户）

当用户在 IM 中说「安装 anime-girl-generator skill」时：

### 方式 A：用户已手动克隆

询问用户项目路径。收到后将其记为 `{PROJECT}`，确认 `.bootstrap/adapters/hermes/anime-girl-generator/SKILL.md` 存在，然后通过 `skill_manage(action='create')` 注册到 `~/.hermes/skills/creative/anime-girl-generator/`。

### 方式 B：用户提供 git 地址

用户可能同时指定存放路径，也可能不指定。如果不指定，由你自行决定一个合理位置（如当前目录或临时目录），clone 后告知用户项目位置。

1. 如果用户给了路径，clone 到 `{用户路径}/anime-girl-auto-generator/`
2. 如果没有，先问用户想放哪里，或自行决定后告知
3. 如果目标目录已存在，询问用户是否覆盖或跳过
4. `git clone <URL> <目标目录>`
5. clone 完成后将目标目录记为 `{PROJECT}`
6. 读取 `{PROJECT}/.bootstrap/adapters/hermes/anime-girl-generator/SKILL.md` 并注册 skill
7. 告知用户安装完成及项目路径

```text
用户: 安装 anime-girl-generator skill，地址 https://github.com/xxx/xxx.git，放到 ~/projects/
→ clone 到 ~/projects/anime-girl-auto-generator/
→ 注册 skill 到 ~/.hermes/skills/creative/anime-girl-generator/
→ "✅ 安装完成！项目位置: ~/projects/anime-girl-auto-generator/"
```

## 进阶技巧

### 批量出图（多角度/多姿势并行生成）

同时运行多个 `comfyui_helper.py generate` 命令实现并行生成（RTX 5070 Ti 可同时跑 2-3 个 job）。每个 job 独立种子、独立 prompt：

```bash
# 终端 1：正面
python .bootstrap/scripts/comfyui_helper.py generate --workflow-path .bootstrap/state/yume_api_workflow.json --prompt "..." &
# 终端 2：侧面
python .bootstrap/scripts/comfyui_helper.py generate --workflow-path .bootstrap/state/yume_api_workflow.json --prompt "..." &
# 终端 3：背面
python .bootstrap/scripts/comfyui_helper.py generate --workflow-path .bootstrap/state/yume_api_workflow.json --prompt "..." &
```

注意：用 `background=true` 时每个进程独立提交到 ComfyUI 队列，不会互相等待。所有输出自动保存到 `{PROJECT}/images/`。

### 🔥 并发出图（Hermes batch 模式）

同时生成多张不同姿势/主题图片的方式。

**步骤**：
1. 用 `terminal(background=true)` 提交多个 `comfyui_helper.py generate`，每个不同的 prompt
2. 用 `process(action='wait')` 等待全部完成（最多 3 个并发，RTX 5070 Ti 16GB 能承受）
3. 全部完成后用 MEDIA: 一次性展示

```bash
# 并发 3 个
for i in 1 2 3; do
  python .bootstrap/scripts/comfyui_helper.py generate \
    --workflow-path .bootstrap/state/yume_api_workflow.json \
    --prompt "姿势$i" --steps 25 --cfg 3.5 &
done
wait
```

**注意**：不要在 foreground 并行（用 `&` 会被 Hermes 拦截）。必须用 background terminal。每个 job 用独立的 background terminal 调用，然后用 process(action='wait') 等待。

**展示规则**：所有图片到齐后一次性显示，不分批。每张一行 MEDIA: + 标题。

### 必读：网络代理

此服务器（中国移动网络）**无法直连 X/Twitter API**。使用 xurl 发帖必须设置代理：

```bash
export HTTPS_PROXY="http://127.0.0.1:7897"
export HTTP_PROXY="http://127.0.0.1:7897"
```

代理地址 `127.0.0.1:7897`（系统网络设置中配置的本地代理）。

### Prompt 注入细节（yume_api_workflow）

该 workflow 的结构为:
```
CLIPTextEncode(node 39) → KSampler.positive
CLIPTextEncode(node 36) → KSampler.negative
```

- **正向 prompt** 注入节点 `39`，字段 `inputs.text`
- **负向 prompt** 注入节点 `36`，字段 `inputs.text`
- 所有 prompt 节点使用直接 CLIPTextEncode，不带 PrimitiveStringMultiline 中间层

### ⚠️ 简单 img2img workflow（推荐用于修改图片）

`comfyui_helper.py` 对 PrimitiveStringMultiline + StringConcatenate 结构的 prompt 注入有时会出错（HTTP 400）。推荐使用**直接 CLIPTextEncode** 的简单 workflow 结构用于 img2img 编辑：

```python
wf = {
    "35": {"inputs": {"ckpt_name": "novaAnimeXL_ilV170.safetensors"}, "class_type": "CheckpointLoaderSimple"},
    "32": {"inputs": {"lora_name": "Dramatic Lighting Slider.safetensors", "strength_model": 1, "strength_clip": 1, "model": ["35", 0], "clip": ["35", 1]}, "class_type": "LoraLoader"},
    "41": {"inputs": {"stop_at_clip_layer": -2, "clip": ["35", 1]}, "class_type": "CLIPSetLastLayer"},
    "42": {"inputs": {"image": "input.jpg"}, "class_type": "LoadImage"},
    "44": {"inputs": {"pixels": ["42", 0], "vae": ["35", 2]}, "class_type": "VAEEncode"},
    "37": {"inputs": {"seed": 42, "steps": 25, "cfg": 3.5, "sampler_name": "euler_ancestral", "scheduler": "simple", "denoise": 0.45, "model": ["32", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["44", 0]}, "class_type": "KSampler"},
    "33": {"inputs": {"samples": ["37", 0], "vae": ["35", 2]}, "class_type": "VAEDecode"},
    "38": {"inputs": {"filename_prefix": "img2edit", "images": ["33", 0]}, "class_type": "SaveImage"},
    "6": {"inputs": {"text": "edit prompt here", "clip": ["41", 0]}, "class_type": "CLIPTextEncode"},
    "7": {"inputs": {"text": "negative prompt here", "clip": ["32", 1]}, "class_type": "CLIPTextEncode"},
}
# 关键：prompt 节点用独立 ID (6, 7)，不是前缀格式 (39:28)，helper 不会错误识别
```

### ⚠️ Flux.2-klein KV Edit VRAM 管理

RTX 5070 Ti（16GB VRAM）可运行 Flux.2-klein KV 图片编辑，但需以下前置操作：

**关键修复**（经验证有效）：
1. **提交前清显存**：调用 `/free` 接口卸载模型 + 清空缓存
   ```bash
   curl -X POST http://100.78.52.73:8188/free \
     -H "Content-Type: application/json" \
     -d '{"unload_models": true, "free_memory": true}'
   ```
2. **控制分辨率**：`ImageScaleToTotalPixels` 的 `megapixels` 设为 0.5（约 700×1100 像素）或更低
3. **原图大小也可行**：清显存后可直接用原图分辨率（如 848×1264），不会 OOM

**已在服务器上验证**：0.5MP ✅ 可用 → 1.0MP ✅ 可用（需清内存）

### 📎 关键教训——CLIP 必须接所有 CLIPTextEncode 节点

创建简单 img2img workflow 时，**每个** CLIPTextEncode 节点（正向和负向）都必须有 `clip` 输入。只给正节点接 CLIP 会报 `required_input_missing: clip` 导致 HTTP 400。负节点也需要接。

## 本地脚本

```bash
# 发布
python {PROJECT}/.bootstrap/scripts/x_poster.py post -i images/xxx.png -c "caption" -t "tags" --reviewed

# 趋势
python {PROJECT}/.bootstrap/scripts/x_poster.py trend "anime girl art" --count 10

# 分析
python {PROJECT}/.bootstrap/scripts/x_analytics.py report
```

## X/Twitter 认证（xurl）

X/Twitter 发布依赖 `xurl` CLI（X API v2）。安装和 OAuth 2.0 PKCE 手动授权流程见 `references/xurl-oauth-setup.md`。

### xurl 认证状态检查

```bash
export PATH="$HOME/.local/bin:$PATH"
xurl auth status
```

如果显示 `oauth2: (none)` 说明未完成授权，需运行 `xurl auth oauth2 --app my-app`。
