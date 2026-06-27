# X Semi-Automatic Publishing SOP

## Principle

Publishing is semi-automatic. The agent may prepare a post, but the user must approve the final image, caption, hashtags, alt text, and risk check before anything is posted to X/Twitter.

## Publishing Flow

1. Generate or select an image.
2. Generate caption, hashtags, and alt text.
3. Run IP check: `python .bootstrap/scripts/ip_check.py --json`.
4. Check `.bootstrap/state/history.json` for recent posts and duplicates.
5. Apply `.bootstrap/config/runtime.json` `posting_policy`.
6. Show the review card.
7. Wait for explicit user confirmation.
8. Publish with `.bootstrap/scripts/x_poster.py post ... --reviewed`.
9. If adult/edge content is present, include `--adult-content`.
10. Confirm URL and history entry.

## Required Review Card

```text
发布审核
图片: images/xxx.png
Caption: ...
Hashtag: #animegirl #AIart #ComfyUI
Alt text: AI generated anime girl artwork, ...
风险检查:
- 频率: OK / BLOCKED
- 重复: OK / BLOCKED
- 成人/擦边: 否 / 是，需要 --adult-content
- IP: residential / mobile / business / hosting / proxy / unknown
- 标签相关性: OK / 需修改
下一步: 回复“确认发布”后我才会发布到 X。
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

Record:
- timestamp
- image path
- caption and full text
- tags
- post ID and URL
- IP grade
- adult content flag
- reviewed flag
- workflow and generation parameters when available
