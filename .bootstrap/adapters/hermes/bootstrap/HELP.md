# Bootstrap Agent

快速生成动漫图片，可半自动发布到 X/Twitter。

---

## 快速上手

### 1. 让 Hermes 安装此 skill

在对话中发送：

```text
skill_manage action=create
```

然后把 `.bootstrap/adapters/hermes/bootstrap/` 的内容复制到系统剪贴板，告诉 Hermes 粘贴即可。

或直接说：

```text
安装 bootstrap skill
```

### 2. 让 Hermes 出图

在对话中直接说：

```text
创建一张xxx图
生成一张xxx的r15图
```

Hermes 会自动加载 bootstrap skill 并调用 ComfyUI 出图。图片会自动存到 `images/`。

### 3. 默认出图参数

- **模型**: novaAnimeXL_ilV170
- **分辨率**: 1080x1920 直出（约 2-3MB）
- **步数/CFG**: 25 / 3.5
- **采样器**: euler_ancestral + simple

### 4. 修改出图参数

```text
改一下种子 / 步数改成40 / CFG改成7
```

### 5. 批量出图

```text
生成3张不同姿势的xxx图
```

### 6. 生成 X 草稿

出图后告诉 Hermes：

```text
准备X推文
写caption和hashtag
```

Hermes 会生成推文草稿供你预览。

### 7. 发布到 X

确认草稿没问题后：

```text
发布到X
```

必须经过人工审核确认后才发送。

---

## 项目结构

| 路径 | 用途 |
|------|------|
| `images/` | 出图存放处 |
| `.bootstrap/config/runtime.json` | 服务器、workflow 配置 |
| `.bootstrap/state/history.json` | 生成记录（已加 .gitignore） |
| `.bootstrap/scripts/comfyui_helper.py` | 后台出图脚本 |
| `.bootstrap/scripts/x_poster.py` | 发布脚本 |
| `.bootstrap/docs/runbooks/comfyui.md` | ComfyUI 详细操作 |
| `.bootstrap/docs/runbooks/x-publishing.md` | 发布审核流程 |

## 记住

- **出图存到 `images/`，不放 `/tmp/`**
- **发布到 X 必须人工确认**
- 图片分析走本地 Ollama，不浪费主模型 token
