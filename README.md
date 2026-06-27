# Anime Girl Auto Generator

一个面向 ComfyUI 的半自动动漫少女图片生成与 X/Twitter 发布 agent 项目。

项目目标不是做无人值守刷帖机器人，而是提供一套“生成图片 → 准备文案 → 合规检查 → 人工审核 → 发布记录 → 数据复盘”的安全工作流。生成和分析可以自动化，发布必须经过人工确认。

## 功能特性

- 使用 ComfyUI workflow 生成图片
- 支持 prompt 注入、seed/steps/cfg/分辨率等参数调节
- 支持批量生成候选图，但不自动批量发布
- 生成 X/Twitter caption、hashtag 和 alt text 建议
- 支持 X/Twitter 趋势研究，用于选题参考
- 发布前强制人工审核，脚本层要求 `--reviewed`
- 对成人/擦边内容要求额外 `--adult-content` 确认
- 内置日发布上限、最小发布时间间隔、重复文案和重复标签组合检查
- 记录生成与发布历史，支持基础数据分析
- 提供 opencode、Codex、Hermes、OpenClaw 适配入口

## 项目结构

```text
.
├── opencode.json                    # opencode 项目配置
├── .opencode/
│   └── agents/anime-girl-generator.md    # opencode project subagent 入口
└── .bootstrap/
    ├── agent.md                     # 共享 agent 入口提示词
    ├── HELP.md                      # 通用快速帮助
    ├── MANIFEST.md                  # agent 包元信息
    ├── README.md                    # bootstrap 包内部说明
    ├── tools.yaml                   # 跨框架工具映射
    ├── backups/                     # 关键文件备份
    ├── config/runtime.json          # ComfyUI、X API、发布策略配置
    ├── state/history.json           # 生成和发布历史
    ├── prompts/caption_templates.md # caption 和 hashtag 模板
    ├── scripts/                     # 本地执行脚本
    ├── docs/                        # agent 规范、runbook、policy
    └── adapters/                    # Codex / Hermes / OpenClaw 适配
        └── hermes/anime-girl-generator/ # Hermes skill 包
```

## 快速开始

### 1. 配置 ComfyUI

编辑 `.bootstrap/config/runtime.json`：

```json
{
  "comfyui_server": "http://你的-comfyui:8188/",
  "default_user": "你的用户",
  "default_workflow": "你的 workflow 名称"
}
```

当前配置文件也包含 X API 凭据字段。未发布到 X 时可以保持为空。

### 默认 Workflow 预设

默认使用 **X擦边女友专用 (yume_no_girl_x)**，对应 `.bootstrap/state/yume_api_workflow.json`。当前该文件是 9 节点 API workflow，1080×1920 直出无 upscale，输出约 2-3MB。

| 预设 | 配置 | 大小 | 用时 | 适用 |
|------|------|------|------|------|
| ⭐ **轻量（默认）** | 1080×1920 · 无 upscale | ~2 MB | ~12s | Telegram 发送、快速出图 |
| 高清 | 1080×1920 · 4xNomos8kDAT upscale | ~31 MB | ~40s | 需要高清晰度时 |

生成示例：

```bash
# 默认（noscale，输出前缀 anime-txt2img）
python .bootstrap/scripts/comfyui_helper.py generate \
  --workflow-path .bootstrap/state/yume_api_workflow.json \
  --prompt "1girl, anime style"
```

### 2. 安装发布依赖

只有需要发布到 X/Twitter 时才需要安装：

```bash
pip install tweepy
```

### 3. 在 opencode 中使用

项目已通过 `.opencode/agents/anime-girl-generator.md` 注册为 opencode project subagent。

常用命令：

```text
@anime-girl-generator 生成图片
@anime-girl-generator steps 40 cfg 5 生成
@anime-girl-generator 查趋势
@anime-girl-generator 生成并发布
@anime-girl-generator 分析报告
```

## 半自动审核发布流程

当你要求“生成并发布”或“发 X”时，agent 会先生成候选图和发布审核卡片，例如：

```text
发布审核
图片: images/xxx.png
Caption: ...
Hashtag: #animegirl #AIart #ComfyUI
Alt text: AI generated anime girl artwork, ...
风险检查: 频率 OK / 无重复 / 成人内容: 否 / IP: residential
下一步: 回复“确认发布”后我才会发布到 X。
```

只有你明确确认后，agent 才允许执行发布命令：

```bash
python .bootstrap/scripts/x_poster.py post \
  -i "images/xxx.png" \
  -c "caption" \
  -t "animegirl,AIart,ComfyUI" \
  -a "AI generated anime girl artwork" \
  --reviewed
```

如果内容包含成人、擦边、hentai、裸露或明显性暗示，发布命令必须额外包含：

```bash
--adult-content
```

## 发布策略

默认发布策略位于 `.bootstrap/config/runtime.json`：

- 模式：半自动审核发布
- 每日最多 5 帖
- 最小发布间隔 120 分钟
- 单帖最多 6 个 hashtag
- 发布必须带 `--reviewed`
- 成人/擦边内容必须带 `--adult-content`

脚本层会阻止未审核发布、过于频繁发布、重复 caption、重复 hashtag 组合和未确认的成人/擦边内容。

## Codex 使用方式

Codex 推荐使用标准 `AGENTS.md` 入口：

```bash
ln -sf .bootstrap/adapters/codex/AGENTS.md AGENTS.md
```

如果你的 Codex 运行时支持 named agent，也可以参考：

```bash
.bootstrap/adapters/codex/codex.yaml
```

## Hermes 使用方式

### 方式一：IM 安装（提供 git 地址，推荐）

让 Hermes 从 git 仓库安装：

```text
从 https://github.com/dream-studio-china/anime-girl-auto-generator.git 安装 anime-girl-generator skill
```

Hermes 会 clone 仓库并安装 skill。**建议同时指定存放路径**，避免 agent 自行决定位置：

```text
安装 anime-girl-generator skill。地址 https://github.com/dream-studio-china/anime-girl-auto-generator.git，放到 ~/hermes-projects/
```

> ⚠️ **注意**：Hermes 没有内置的 git clone → skill 注册流程。这一步依赖 agent 的通用推理能力，不同 agent 的实现可能不同。建议用户主动指定项目路径，或采用方式三手动安装。

### 方式二：IM 安装（手动告知路径）

在聊天中告诉 Hermes：

```text
安装 anime-girl-generator skill
```

Hermes 会询问项目路径。将克隆下来的项目绝对路径告知即可，例如：

```text
我的项目在 /home/user/anime-girl-auto-generator
```

Hermes 应从 `{项目路径}/.bootstrap/adapters/hermes/anime-girl-generator/SKILL.md` 读取 skill 配置并完成安装。

> ⚠️ **注意**：SKILL.md 中的 `{PROJECT}` 变量需要替换为你的实际项目路径。安装时 Hermes 会自动提示你设置。

### 方式三：CLI 安装（推荐服务器/远程环境）

```bash
mkdir -p ~/.hermes/skills/creative
mkdir -p ~/.hermes/skills/creative/anime-girl-generator
cp -R .bootstrap/adapters/hermes/anime-girl-generator/. ~/.hermes/skills/creative/anime-girl-generator/
```

Hermes 入口文件：

```text
~/.hermes/skills/creative/anime-girl-generator/SKILL.md
```

Hermes 帮助文件：

```text
~/.hermes/skills/creative/anime-girl-generator/HELP.md
```

## OpenClaw 使用方式

OpenClaw 适配文件位于：

```text
.bootstrap/adapters/openclaw/IDENTITY.md
```

## 本地脚本

### 发布到 X/Twitter

```bash
python .bootstrap/scripts/x_poster.py post \
  -i images/xxx.png \
  -c "caption" \
  -t "animegirl,AIart,ComfyUI" \
  --reviewed
```

### 查看趋势

```bash
python .bootstrap/scripts/x_poster.py trend "anime girl art" --count 10
```

### 查看分析报告

```bash
python .bootstrap/scripts/x_analytics.py report
```

### 检查 IP 质量

```bash
python .bootstrap/scripts/ip_check.py --json
```

## 安全边界

本项目不会帮助执行以下行为：

- 未经审核自动发布到 X/Twitter
- 高频重复发帖或刷屏
- 使用无关热门 hashtag 引流
- 买赞、互推、批量 mention、批量 DM、批量回复等平台操纵行为
- 发布未成年性化、非自愿亲密内容、真实人物冒充或明显版权侵权内容
- 将 AI 图片伪装成真实人物、真实照片或真实事件

## 校验

```bash
python -m json.tool .bootstrap/config/runtime.json >/dev/null
python -m json.tool opencode.json >/dev/null
python -m py_compile \
  .bootstrap/scripts/x_poster.py \
  .bootstrap/scripts/x_analytics.py \
  .bootstrap/scripts/ip_check.py
```

## 许可证

未指定。使用前请根据你的实际发布需求补充许可证和平台合规说明。
