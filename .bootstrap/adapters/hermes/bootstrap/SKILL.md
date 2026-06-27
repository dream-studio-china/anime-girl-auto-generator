---
name: bootstrap
description: ComfyUI 半自动运营 Agent。连接 ComfyUI 生成图片，研究 X/Twitter 趋势，准备 caption/hashtag，并在人工审核后发布。Use ONLY when the user asks about ComfyUI image generation, anime girl generation, generating or modifying images, or X/Twitter reviewed publishing.
---

# Bootstrap Agent

你的入口指令在 `.bootstrap/agent.md`。请立即用 `read_file` 工具读取该文件，并按任务需要读取 `.bootstrap/docs/` 下的 runbook 和 policy。

## Hermes 工具映射

| 通用名 | Hermes 工具 |
|--------|------------|
| shell | `bash` |
| search | `web_search` |
| fetch | `fetch_url` |
| read | `read_file` |
| write | `write_file` |

## 核心流程

1. 读取 `.bootstrap/agent.md` — 入口提示和启动顺序
2. 读取 `.bootstrap/config/runtime.json` — 加载配置
3. 读取 `.bootstrap/docs/agent-spec.md` — agent 行为规范
4. 按任务读取 ComfyUI runbook、X 发布 SOP 或内容政策

## ComfyUI API 速查 (通过 bash 执行)

```
列出用户:     curl -s {SERVER}/users
列出 workflows: curl -s "{SERVER}/userdata?user={USER}&dir=workflows"
获取 workflow:  curl -s "{SERVER}/userdata/{FILE}?user={USER}"
提交执行:     curl -s -X POST {SERVER}/prompt -H "Content-Type: application/json" -d '{"prompt":{JSON},"client_id":"bootstrap"}'
查队列:       curl -s {SERVER}/queue
查历史:       curl -s "{SERVER}/history/{ID}"
下载图片:     curl -s -o "images/{FILE}" "{SERVER}/view?filename={F}&subfolder={S}&type=output"
列出模型:     curl -s {SERVER}/models/checkpoints
系统状态:     curl -s {SERVER}/system_stats
```

立即读取 `.bootstrap/agent.md` 开始工作。发布到 X 必须先审核，发布命令必须带 `--reviewed`。
