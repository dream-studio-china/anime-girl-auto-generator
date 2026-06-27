"""
X/Twitter Reviewed Posting Helper
=================================
供 Bootstrap Agent 通过 shell 调用，处理 X/Twitter API v2 发帖和媒体上传。
默认执行半自动审核发布护栏：未带 --reviewed 会阻止发布。

用法:
    python .bootstrap/scripts/x_poster.py post -i images/xxx.png -c "caption text" -t tag1,tag2 --reviewed
    python .bootstrap/scripts/x_poster.py post -i xx.png -c "txt" -t tags --reviewed --adult-content
    python .bootstrap/scripts/x_poster.py trend "anime girl 2026" --count 10
    python .bootstrap/scripts/x_poster.py engagement --post-id 12345

依赖: pip install tweepy
配置: 从 .bootstrap/config/runtime.json 读取 x_credentials
"""

import json
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

AGENT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = AGENT_ROOT / "config" / "runtime.json"
HISTORY_PATH = AGENT_ROOT / "state" / "history.json"
DEFAULT_DAILY_LIMIT = 5
DEFAULT_MIN_INTERVAL_MINUTES = 120
DEFAULT_DUPLICATE_WINDOW_HOURS = 48


ADULT_KEYWORDS = {
    "adult", "nsfw", "hentai", "nude", "nudity", "sex", "sexual",
    "sexy", "bikini", "swimsuit", "lingerie", "underwear", "cleavage",
    "擦边", "成人", "裸", "裸体", "性爱", "性暗示", "泳装", "比基尼", "内衣",
}


def load_credentials() -> dict:
    cfg = load_config()
    return cfg.get("x_credentials", {})


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_posting_policy() -> dict:
    cfg = load_config()
    policy = cfg.get("posting_policy", {})
    return policy if isinstance(policy, dict) else {}


def load_history() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    try:
        with open(HISTORY_PATH) as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_history(history: list[dict]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def parse_time(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def has_adult_signal(text: str, tags: list[str]) -> bool:
    combined = normalize_text(" ".join([text, *tags]))
    return any(keyword in combined for keyword in ADULT_KEYWORDS)


def validate_post_policy(caption: str, tags: list[str], reviewed: bool,
                         adult_content: bool, daily_limit: int,
                         min_interval_minutes: int) -> dict:
    """Enforce semi-automatic publishing safeguards before hitting X."""
    if not reviewed:
        return {
            "error": "发布被阻止: 缺少人工审核确认",
            "hint": "先展示图片、caption、hashtag、风险检查，用户确认后再加 --reviewed。",
        }

    if has_adult_signal(caption, tags) and not adult_content:
        return {
            "error": "发布被阻止: 检测到可能的成人/擦边内容",
            "hint": "确认 X 账号媒体敏感/成人内容设置后，使用 --adult-content。",
        }

    if len(tags) > 6:
        return {
            "error": "发布被阻止: hashtag 过多",
            "hint": "单帖建议 3-6 个相关 hashtag，删除无关热门标签后重试。",
        }

    now = datetime.now(timezone.utc)
    history = load_history()
    published = [entry for entry in history if entry.get("post_id") or entry.get("url")]

    today_count = 0
    last_post_time = None
    duplicate_cutoff = now - timedelta(hours=DEFAULT_DUPLICATE_WINDOW_HOURS)
    normalized_caption = normalize_text(caption)
    normalized_tags = sorted(t.strip("#").lower() for t in tags if t.strip())

    for entry in published:
        entry_time = parse_time(entry.get("time", "") or entry.get("created_at", ""))
        if entry_time and entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=timezone.utc)

        if entry_time and entry_time.date() == now.date():
            today_count += 1

        if entry_time and (last_post_time is None or entry_time > last_post_time):
            last_post_time = entry_time

        if entry_time and entry_time >= duplicate_cutoff:
            old_caption = normalize_text(entry.get("text", "") or entry.get("caption", ""))
            old_tags = sorted(t.strip("#").lower() for t in entry.get("tags", []) if str(t).strip())
            if old_caption and old_caption == normalized_caption:
                return {
                    "error": "发布被阻止: 48 小时内存在重复 caption",
                    "hint": "请重写文案或更换图片后再发布。",
                }
            if old_tags and old_tags == normalized_tags:
                return {
                    "error": "发布被阻止: 48 小时内存在重复 hashtag 组合",
                    "hint": "请调整标签组合，确保标签与图片内容相关。",
                }

    if today_count >= daily_limit:
        return {
            "error": f"发布被阻止: 今日已达到 {daily_limit} 帖上限",
            "hint": "明天再发，或明确降低自动化频率。",
        }

    if last_post_time:
        elapsed_minutes = (now - last_post_time).total_seconds() / 60
        if elapsed_minutes < min_interval_minutes:
            remaining = int(min_interval_minutes - elapsed_minutes)
            return {
                "error": "发布被阻止: 距离上次发布时间过短",
                "hint": f"默认最小间隔 {min_interval_minutes} 分钟，请至少再等 {remaining} 分钟。",
            }

    return {"ok": True}


def append_post_history(result: dict, caption: str, tags: list[str],
                        adult_content: bool, reviewed: bool) -> None:
    history = load_history()
    history.append({
        "time": datetime.now(timezone.utc).isoformat(),
        "post_id": result.get("id"),
        "url": result.get("url"),
        "image": result.get("image"),
        "text": result.get("text") or caption,
        "caption": caption,
        "tags": tags,
        "ip_grade": result.get("ip_grade"),
        "adult_content": adult_content,
        "reviewed": reviewed,
    })
    save_history(history)


def get_client():
    try:
        import tweepy
    except ImportError:
        print("ERROR: tweepy not installed. Run: pip install tweepy")
        sys.exit(1)

    creds = load_credentials()
    client = tweepy.Client(
        consumer_key=creds.get("api_key", ""),
        consumer_secret=creds.get("api_secret", ""),
        access_token=creds.get("access_token", ""),
        access_token_secret=creds.get("access_secret", ""),
        bearer_token=creds.get("bearer_token", ""),
    )
    return client, creds


def get_v1_api():
    """v1.1 API for media upload."""
    try:
        import tweepy
    except ImportError:
        print("ERROR: tweepy not installed. Run: pip install tweepy")
        sys.exit(1)

    creds = load_credentials()
    auth = tweepy.OAuth1UserHandler(
        creds.get("api_key", ""),
        creds.get("api_secret", ""),
        creds.get("access_token", ""),
        creds.get("access_secret", ""),
    )
    return tweepy.API(auth)


# ============================================================
# Post: 发布图片到 X/Twitter
# ============================================================

def post_image(image_path: str, caption: str, tags: Optional[list[str]] = None,
               alt_text: str = "", reply_to: Optional[str] = None,
               skip_ip_check: bool = False, reviewed: bool = False,
               adult_content: bool = False, daily_limit: int = DEFAULT_DAILY_LIMIT,
               min_interval_minutes: int = DEFAULT_MIN_INTERVAL_MINUTES) -> dict:
    """上传图片并发布 tweet。"""
    tags = tags or []

    policy = validate_post_policy(
        caption=caption,
        tags=tags,
        reviewed=reviewed,
        adult_content=adult_content,
        daily_limit=daily_limit,
        min_interval_minutes=min_interval_minutes,
    )
    if "error" in policy:
        return policy

    if not os.path.exists(image_path):
        return {"error": f"图片不存在: {image_path}"}

    # IP 质量预检
    ip_result = None
    if not skip_ip_check:
        try:
            from ip_check import run_check
            ip_result = run_check()
        except ImportError:
            pass

    if ip_result and ip_result["grade"] in ("hosting", "proxy"):
        return {
            "error": f"IP 风险过高 ({ip_result['grade']})，已阻止发布",
            "ip_check": ip_result,
            "hint": "加上 --skip-ip-check 跳过检测，或切换网络后重试",
        }

    # 构建完整推文文本
    tag_str = " " + " ".join(f"#{t.strip('#')}" for t in tags) if tags else ""
    full_text = f"{caption}{tag_str}"

    if len(full_text) > 280:
        full_text = full_text[:277] + "..."

    client, _ = get_client()
    v1 = get_v1_api()

    # Step 1: 上传媒体
    media = v1.media_upload(filename=image_path)
    alt = alt_text or f"AI generated anime girl artwork"
    # Tweepy v1 media metadata support varies by auth/app settings. Keep alt
    # text in history even if the API call is unavailable.
    try:
        v1.create_media_metadata(media.media_id, alt)
    except Exception:
        pass

    # Step 2: 发布推文
    if reply_to:
        tweet = client.create_tweet(
            text=full_text,
            media_ids=[media.media_id],
            in_reply_to_tweet_id=reply_to,
        )
    else:
        tweet = client.create_tweet(
            text=full_text,
            media_ids=[media.media_id],
        )

    result = {
        "id": str(tweet.data["id"]),
        "text": full_text,
        "url": f"https://x.com/i/status/{tweet.data['id']}",
        "image": image_path,
        "ip_grade": ip_result["grade"] if ip_result else "unchecked",
        "adult_content": adult_content,
        "reviewed": reviewed,
    }
    append_post_history(result, caption, tags, adult_content, reviewed)
    return result


# ============================================================
# Trend: 搜索 X 趋势
# ============================================================

def search_trends(query: str, count: int = 10) -> list[dict]:
    """搜索 X/Twitter 上的趋势帖文。"""
    client, _ = get_client()

    # 搜索近期热门推文
    tweets = client.search_recent_tweets(
        query=query,
        max_results=min(count, 100),
        tweet_fields=["public_metrics", "created_at", "author_id", "entities"],
        expansions=["author_id", "attachments.media_keys"],
        media_fields=["url", "preview_image_url"],
    )

    results = []
    if tweets.data:
        for t in tweets.data:
            results.append({
                "id": t.id,
                "text": t.text,
                "likes": t.public_metrics.get("like_count", 0) if t.public_metrics else 0,
                "retweets": t.public_metrics.get("retweet_count", 0) if t.public_metrics else 0,
                "replies": t.public_metrics.get("reply_count", 0) if t.public_metrics else 0,
                "created_at": str(t.created_at),
            })

    return sorted(results, key=lambda x: x["likes"], reverse=True)


# ============================================================
# Engagement: 查看指定帖子的互动数据
# ============================================================

def get_engagement(post_id: str) -> dict:
    """获取指定推文的互动数据。"""
    client, _ = get_client()
    tweet = client.get_tweet(
        post_id,
        tweet_fields=["public_metrics", "created_at"],
    )
    if tweet.data:
        return {
            "id": post_id,
            "likes": tweet.data.public_metrics.get("like_count", 0),
            "retweets": tweet.data.public_metrics.get("retweet_count", 0),
            "replies": tweet.data.public_metrics.get("reply_count", 0),
            "impressions": tweet.data.public_metrics.get("impression_count", 0),
            "created_at": str(tweet.data.created_at),
        }
    return {"error": f"未找到推文: {post_id}"}


# ============================================================
# My Tweets: 查看自己的最近推文
# ============================================================

def get_my_tweets(count: int = 10) -> list[dict]:
    """获取自己最近的推文及互动数据。"""
    client, _ = get_client()
    me = client.get_me()
    tweets = client.get_users_tweets(
        id=me.data.id,
        max_results=min(count, 100),
        tweet_fields=["public_metrics", "created_at"],
    )
    results = []
    if tweets.data:
        for t in tweets.data:
            results.append({
                "id": t.id,
                "text": t.text[:100],
                "likes": t.public_metrics.get("like_count", 0) if t.public_metrics else 0,
                "retweets": t.public_metrics.get("retweet_count", 0) if t.public_metrics else 0,
                "replies": t.public_metrics.get("reply_count", 0) if t.public_metrics else 0,
                "impressions": t.public_metrics.get("impression_count", 0) if t.public_metrics else 0,
                "created_at": str(t.created_at),
            })
    return results


# ============================================================
# CLI
# ============================================================

def main():
    policy = load_posting_policy()
    daily_limit_default = int(policy.get("daily_limit", DEFAULT_DAILY_LIMIT))
    min_interval_default = int(policy.get("min_interval_minutes", DEFAULT_MIN_INTERVAL_MINUTES))

    parser = argparse.ArgumentParser(description="X/Twitter Posting Helper")
    sub = parser.add_subparsers(dest="command")

    # post
    p = sub.add_parser("post", help="发布图片到 X")
    p.add_argument("-i", "--image", required=True, help="图片路径")
    p.add_argument("-c", "--caption", required=True, help="推文正文")
    p.add_argument("-t", "--tags", help="逗号分隔的 hashtag")
    p.add_argument("-a", "--alt", default="", help="图片 alt text")
    p.add_argument("-r", "--reply", help="回复到指定推文 ID")
    p.add_argument("--skip-ip-check", action="store_true", help="跳过 IP 质量检测")
    p.add_argument("--reviewed", action="store_true", help="确认图片、文案、标签和风险已人工审核")
    p.add_argument("--adult-content", action="store_true", help="确认该内容已按 X 成人/敏感媒体要求处理")
    p.add_argument("--daily-limit", type=int, default=daily_limit_default, help="每日发布上限")
    p.add_argument("--min-interval", type=int, default=min_interval_default, help="最小发布间隔，单位分钟")

    # trend
    t = sub.add_parser("trend", help="搜索 X 趋势")
    t.add_argument("query", help="搜索关键词")
    t.add_argument("--count", type=int, default=10, help="返回数量")

    # engagement
    e = sub.add_parser("engagement", help="查看推文互动")
    e.add_argument("--post-id", required=True, help="推文 ID")

    # my
    m = sub.add_parser("my", help="查看自己最近推文")
    m.add_argument("--count", type=int, default=10, help="返回数量")

    args = parser.parse_args()

    if args.command == "post":
        tags = args.tags.split(",") if args.tags else []
        result = post_image(args.image, args.caption, tags, args.alt, args.reply,
                            skip_ip_check=args.skip_ip_check,
                            reviewed=args.reviewed,
                            adult_content=args.adult_content,
                            daily_limit=args.daily_limit,
                            min_interval_minutes=args.min_interval)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "trend":
        results = search_trends(args.query, args.count)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif args.command == "engagement":
        result = get_engagement(args.post_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.command == "my":
        results = get_my_tweets(args.count)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
