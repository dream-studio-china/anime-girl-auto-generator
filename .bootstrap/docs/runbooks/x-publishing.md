# X Semi-Automatic Publishing SOP

## Principle

Publishing is semi-automatic. The agent may prepare a post, but the user must approve the final image, caption, hashtags, alt text, and risk check before anything is posted to X/Twitter.

## Publishing Flow

1. Generate or select an image.
2. Generate caption, hashtags, and alt text.
3. **Auto-generate X intent URL**: concatenate caption + hashtags, URL-encode with `urllib.parse.quote()`, format as `https://twitter.com/intent/tweet?text=...`
4. **Auto-copy image to clipboard**: `osascript -e 'set the clipboard to (read POSIX file "images/xxx.png" as JPEG picture)'` (macOS)
5. Run IP check: `python .bootstrap/scripts/ip_check.py --json`.
6. Check `.bootstrap/state/history.json` for recent posts and duplicates.
7. Apply `.bootstrap/config/runtime.json` `posting_policy`.
8. Show the review card (must include clickable X Intent URL + clipboard confirmation).
9. Wait for explicit user confirmation.
10. Publish with `.bootstrap/scripts/x_poster.py post ... --reviewed`.
11. If adult/edge content is present, include `--adult-content`.
12. Confirm URL and history entry.

## Review Card Policy

Review cards MUST be built from the prompt text and generation parameters. If image content analysis is needed, offload to local Ollama (qwen3.5:9b or qwen2.5vl:7b @ 100.78.52.73:11434) — never consume main model tokens for vision tasks.

## Required Review Card

```text
发布审核
图片: images/xxx.png
Caption: ...
Hashtag: #animegirl #AIart #ComfyUI
Alt text: AI generated anime girl artwork, ...
📋 图片已复制到剪贴板 ✅
🔗 X Intent: https://twitter.com/intent/tweet?text=...
风险检查:
- 频率: OK / BLOCKED
- 重复: OK / BLOCKED
- 成人/擦边: 否 / 是，需要 --adult-content
- IP: residential / mobile / business / hosting / proxy / unknown
- 标签相关性: OK / 需修改
下一步: 回复"确认发布"后我才会发布到 X。
```

## Command Format

Normal reviewed post:

```bash
python .bootstrap/scripts/x_poster.py post \
  -i "images/xxx.png" \
  -c "caption" \
  -t "animegirl,AIart,ComfyUI" \
  -a "AI generated anime girl artwork" \
  --reviewed
```

Adult or edge content:

```bash
python .bootstrap/scripts/x_poster.py post \
  -i "images/xxx.png" \
  -c "caption" \
  -t "animegirl,AIart,ComfyUI" \
  -a "AI generated anime girl artwork" \
  --reviewed \
  --adult-content
```

## Default Guardrails

Read actual values from `.bootstrap/config/runtime.json` `posting_policy`.

Default expectations:
- Mode: `semi_auto_review`
- Daily limit: 5 posts
- Minimum interval: 120 minutes
- Maximum hashtags: 6
- Require `--reviewed`: true
- Require adult content confirmation: true

## Trend Research

Allowed:
- Find topics, styles, seasonal themes, common caption patterns, and broad audience timing.
- Recommend related hashtags only when they match the generated image.

Not allowed:
- Add unrelated trending hashtags to drive traffic.
- Repeatedly post near-identical content into the same trend.
- Coordinate with other accounts to boost content.
- Use automation for aggressive replies, mentions, likes, reposts, follows, or DMs.

## A/B Testing

A/B testing is allowed only as low-frequency creative testing.

Rules:
- Usually test 2-3 variants.
- Review each post separately.
- Space posts out according to `min_interval_minutes` unless using a single thread and user approves the format.
- Do not present early results as conclusive without enough impressions and time.

## Blocking Conditions

Do not publish if:
- User has not confirmed the review card.
- The command would not include `--reviewed`.
- Daily limit or minimum interval would be violated.
- Caption or hashtag combination is duplicated recently.
- Hashtags are unrelated or excessive.
- Content appears to sexualize minors or ambiguous minors.
- Content impersonates a real person or claims to be real.
- X credentials are missing or invalid.
- IP check returns `hosting` or `proxy`, unless user explicitly accepts risk after review.

## Post-Publish Record

记录 timestamp、image path、post ID。其余字段 comfyui_helper.py 和 x_poster.py 自动写入 history.json。

## X Character Limit Auto-Adaptation

| Account Type | Single Post Limit | Action When Over Limit |
|-------------|------------------|----------------------|
| Free | **280 characters** | Auto-shorten caption + reduce hashtags to 2-3 |
| X Basic | **4,000 characters** | Auto-truncate with prompt |
| X Premium | **25,000 characters** | Rarely exceeded |

Before generating X intent URL, count the final post text characters. If over limit, apply auto-shortening strategy (1) shorten caption keeping core message → 2) reduce hashtags → 3) remove redundant whitespace/punctuation). Show character count `(N/M)` in the review card. **Do not generate intent URL** if the text exceeds the limit after shortening.
