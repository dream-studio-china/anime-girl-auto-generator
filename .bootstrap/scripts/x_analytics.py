"""
X/Twitter Analytics Helper
==========================
分析自己的推文数据，输出优化建议。

用法:
    python .bootstrap/scripts/x_analytics.py report           # 完整分析报告
    python .bootstrap/scripts/x_analytics.py hashtags         # Hashtag 效果排行
    python .bootstrap/scripts/x_analytics.py best-time        # 最佳发布时间分析
    python .bootstrap/scripts/x_analytics.py top-posts        # 表现最好的帖子
    python .bootstrap/scripts/x_analytics.py calendar         # 生成内容日历建议
    python .bootstrap/scripts/x_analytics.py refresh          # 刷新所有帖子的最新互动数据

依赖: pip install tweepy
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict

AGENT_ROOT = Path(__file__).resolve().parent.parent
HISTORY_PATH = AGENT_ROOT / "state" / "history.json"


def load_history() -> list[dict]:
    """读取本地发布历史。"""
    if HISTORY_PATH.exists():
        with open(HISTORY_PATH) as f:
            return json.load(f)
    return []


def save_history(history: list[dict]):
    """保存历史到文件。"""
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def refresh_engagement(history: list[dict]) -> list[dict]:
    """用 X API 刷新所有帖子的最新互动数据。"""
    try:
        from x_poster import get_engagement
    except ImportError:
        print("ERROR: 无法导入 x_poster")
        return history

    updated = []
    for i, entry in enumerate(history):
        post_id = entry.get("post_id") or entry.get("id")
        if not post_id:
            updated.append(entry)
            continue

        data = get_engagement(post_id)
        if "error" not in data:
            entry["live_metrics"] = {
                "likes": data.get("likes", 0),
                "retweets": data.get("retweets", 0),
                "replies": data.get("replies", 0),
                "impressions": data.get("impressions", 0),
                "fetched_at": datetime.now().isoformat(),
            }
            print(f"  ✓ {post_id}: {data['likes']}♥ {data['impressions']}👁")
        else:
            print(f"  ✗ {post_id}: {data.get('error', 'unknown')}")
        updated.append(entry)

    # 保存刷新结果
    save_history(updated)
    return updated


def has_recent_metrics(entry: dict, max_hours: int = 24) -> bool:
    """检查是否有最近的 metrics 数据。"""
    live = entry.get("live_metrics", {})
    if not live:
        return False
    fetched = live.get("fetched_at", "")
    if not fetched:
        return False
    try:
        dt = datetime.fromisoformat(fetched)
        age = (datetime.now() - dt).total_seconds() / 3600
        return age < max_hours
    except ValueError:
        return False


def analyze_hashtags(history: list[dict]) -> list[dict]:
    """分析 hashtag 效果。"""
    tag_metrics = defaultdict(lambda: {"count": 0, "total_likes": 0, "total_impressions": 0})

    for entry in history:
        text = entry.get("text", "")
        tags_in_post = [w.strip("#") for w in text.split() if w.startswith("#")]
        likes = entry.get("live_metrics", {}).get("likes", 0)
        impressions = entry.get("live_metrics", {}).get("impressions", 0)

        for tag in tags_in_post:
            tag_metrics[tag]["count"] += 1
            tag_metrics[tag]["total_likes"] += likes
            tag_metrics[tag]["total_impressions"] += impressions

    results = []
    for tag, m in tag_metrics.items():
        results.append({
            "hashtag": tag,
            "used": m["count"],
            "total_likes": m["total_likes"],
            "avg_likes": round(m["total_likes"] / m["count"], 1) if m["count"] else 0,
        })

    return sorted(results, key=lambda x: x["avg_likes"], reverse=True)


def analyze_best_time(history: list[dict]) -> list[dict]:
    """分析最佳发布时间。"""
    hour_metrics = defaultdict(lambda: {"count": 0, "total_likes": 0, "total_impressions": 0})

    for entry in history:
        t = entry.get("time", "")
        if not t:
            t = entry.get("created_at", "")
        if not t:
            continue
        try:
            dt = datetime.fromisoformat(t)
        except ValueError:
            continue
        hour = dt.hour
        likes = entry.get("live_metrics", {}).get("likes", 0)
        impressions = entry.get("live_metrics", {}).get("impressions", 0)

        hour_metrics[hour]["count"] += 1
        hour_metrics[hour]["total_likes"] += likes
        hour_metrics[hour]["total_impressions"] += impressions

    results = []
    for hour, m in hour_metrics.items():
        results.append({
            "hour_utc": hour,
            "posts": m["count"],
            "total_likes": m["total_likes"],
            "avg_likes": round(m["total_likes"] / m["count"], 1) if m["count"] else 0,
        })

    return sorted(results, key=lambda x: x["avg_likes"], reverse=True)


def analyze_workflow_performance(history: list[dict]) -> list[dict]:
    """分析不同 workflow 的表现。"""
    wf_metrics = defaultdict(lambda: {"count": 0, "total_likes": 0})

    for entry in history:
        wf = entry.get("workflow", "unknown")
        likes = entry.get("live_metrics", {}).get("likes", 0)
        wf_metrics[wf]["count"] += 1
        wf_metrics[wf]["total_likes"] += likes

    results = []
    for wf, m in wf_metrics.items():
        results.append({
            "workflow": wf,
            "posts": m["count"],
            "total_likes": m["total_likes"],
            "avg_likes": round(m["total_likes"] / m["count"], 1) if m["count"] else 0,
        })

    return sorted(results, key=lambda x: x["avg_likes"], reverse=True)


def analyze_param_correlation(history: list[dict]) -> list[dict]:
    """分析 seed/cfg/steps 等参数与互动的相关性。"""
    records = []
    for entry in history:
        params = entry.get("params", {})
        if not params:
            continue
        likes = entry.get("live_metrics", {}).get("likes", 0)
        records.append({
            "seed": params.get("seed"),
            "cfg": params.get("cfg"),
            "steps": params.get("steps"),
            "likes": likes,
            "workflow": entry.get("workflow", ""),
            "note": entry.get("note", ""),
        })

    if not records:
        return []

    # 按 likes 排序
    return sorted(records, key=lambda x: x["likes"], reverse=True)


def generate_calendar(history: list[dict]) -> list[dict]:
    """基于历史数据生成一周内容日历建议。"""
    # 找出每日最佳发布时间和最佳 workflow
    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    # 最佳时间
    best_times = analyze_best_time(history)
    top_hour = best_times[0]["hour_utc"] if best_times else 11

    # 最佳 workflow
    best_wf = analyze_workflow_performance(history)
    top_wf = best_wf[0]["workflow"] if best_wf else "default"

    # 最佳 hashtags
    top_tags = analyze_hashtags(history)
    top_tag_list = [t["hashtag"] for t in top_tags[:5]]

    # 风格轮换建议 (如果没有足够数据，用默认方案)
    style_themes = [
        {"day": 0, "theme": "轻松日常", "style": "casual, slice-of-life, cute"},
        {"day": 1, "theme": "高质量主图", "style": "detailed, high quality, showcase"},
        {"day": 2, "theme": "风格变化", "style": "alternative outfit, different mood"},
        {"day": 3, "theme": "互动帖", "style": "AB test, question, engagement"},
        {"day": 4, "theme": "周末预热", "style": "sexy, bold, weekend vibe"},
        {"day": 5, "theme": "周末主图", "style": "elaborate, special, premium"},
        {"day": 6, "theme": "收尾/回顾", "style": "soft, relaxing, week recap"},
    ]

    calendar = []
    for theme in style_themes:
        calendar.append({
            "day": day_names[theme["day"]],
            "theme": theme["theme"],
            "style": theme["style"],
            "suggested_hour": f"{top_hour}:00 UTC" if top_hour else "11:00 UTC",
            "suggested_workflow": top_wf,
            "suggested_tags": top_tag_list,
        })

    return calendar


def print_report(history: list[dict]):
    """打印完整分析报告。"""
    # 基础统计
    total = len(history)
    total_likes = sum(e.get("live_metrics", {}).get("likes", 0) for e in history)
    total_impressions = sum(e.get("live_metrics", {}).get("impressions", 0) for e in history)

    print(f"""
╔══════════════════════════════════════════════╗
║         X/Twitter Analytics Report          ║
╠══════════════════════════════════════════════╣
║  总帖数: {total:<34} ║
║  总点赞: {total_likes:<34} ║
║  总曝光: {total_impressions:<34} ║
║  均点赞: {round(total_likes/total, 1) if total else 0:<34} ║
╚══════════════════════════════════════════════╝
""")

    # Top 5 帖子
    top = sorted(history,
                 key=lambda e: e.get("live_metrics", {}).get("likes", 0),
                 reverse=True)[:5]
    if top:
        print("🏆 Top 5 帖子:")
        for i, e in enumerate(top, 1):
            metrics = e.get("live_metrics", {})
            print(f"  {i}. [{metrics.get('likes', 0)}♥] {e.get('text', '')[:60]}...")
            print(f"     {e.get('url', '')}")
        print()

    # Hashtag 排名
    hashtags = analyze_hashtags(history)
    if hashtags:
        print("📊 Hashtag 效果排行 (均点赞):")
        for h in hashtags[:10]:
            print(f"  #{h['hashtag']:<25}  x{h['used']}  均{h['avg_likes']}♥")
        print()

    # 最佳时间
    times = analyze_best_time(history)
    if times:
        print("⏰ 最佳发布时间 (UTC):")
        for t in times[:5]:
            jst = (t["hour_utc"] + 9) % 24
            print(f"  {t['hour_utc']:02d}:00 UTC ({jst:02d}:00 JST)  x{t['posts']}帖  均{t['avg_likes']}♥")
        print()

    # Workflow 表现
    wf = analyze_workflow_performance(history)
    if wf:
        print("🎨 Workflow 表现排行:")
        for w in wf:
            print(f"  {w['workflow']:<35}  x{w['posts']}帖  均{w['avg_likes']}♥")
        print()

    # Content Calendar
    calendar = generate_calendar(history)
    if calendar:
        print("📅 推荐下周内容日历:")
        for c in calendar:
            print(f"  {c['day']} - {c['theme']} ({c['style']}) @ {c['suggested_hour']}")
        print()

    # 建议
    print("💡 优化建议:")
    top_wf_list = [w["workflow"] for w in wf[:1]] if wf else []
    top_tag_list = [h["hashtag"] for h in hashtags[:3]] if hashtags else []
    top_hour_list = [t["hour_utc"] for t in times[:1]] if times else []

    if top_wf_list:
        print(f"  → 多用 workflow: {top_wf_list[0]}")
    if top_tag_list:
        print(f"  → 必加 hashtag: {' #'.join(top_tag_list)}")
    if top_hour_list:
        jst = (top_hour_list[0] + 9) % 24
        print(f"  → 黄金时段: {top_hour_list[0]:02d}:00 UTC / {jst:02d}:00 JST")
    print()


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="X/Twitter Analytics")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("report", help="完整分析报告")
    sub.add_parser("hashtags", help="Hashtag 效果排行")
    sub.add_parser("best-time", help="最佳发布时间")
    sub.add_parser("top-posts", help="表现最好的帖子")
    sub.add_parser("calendar", help="内容日历建议")
    r = sub.add_parser("refresh", help="刷新所有帖子的互动数据")
    r.add_argument("--force", action="store_true", help="强制刷新 (忽略缓存)")

    args = parser.parse_args()
    cmd = args.command or "report"

    history = load_history()

    if not history:
        print("暂无发布记录。先用 @anime-girl-generator 生成并发布 积累数据。")
        return

    # 需要最新 metrics 的命令先刷新
    needs_metrics = cmd in ("report", "hashtags", "best-time", "top-posts")
    if needs_metrics:
        stale = any(not has_recent_metrics(e) for e in history if e.get("post_id") or e.get("id"))
        if stale or getattr(args, "force", False):
            print("🔄 刷新帖子的最新互动数据...")
            history = refresh_engagement(history)

    if cmd == "report":
        print_report(history)

    elif cmd == "hashtags":
        for h in analyze_hashtags(history):
            print(f"#{h['hashtag']:<25}  x{h['used']}帖  均{h['avg_likes']}♥  {h['total_likes']}♥累计")

    elif cmd == "best-time":
        for t in analyze_best_time(history):
            jst = (t["hour_utc"] + 9) % 24
            print(f"{t['hour_utc']:02d}:00 UTC / {jst:02d}:00 JST  x{t['posts']}帖  均{t['avg_likes']}♥")

    elif cmd == "top-posts":
        top = sorted(history,
                     key=lambda e: e.get("live_metrics", {}).get("likes", 0),
                     reverse=True)[:10]
        for i, e in enumerate(top, 1):
            m = e.get("live_metrics", {})
            print(f"{i:2}. [{m.get('likes', 0)}♥ {m.get('impressions', 0)}👁] {e.get('text', '')[:70]}")
            print(f"    {e.get('time', '')}  {e.get('url', '')}")

    elif cmd == "calendar":
        for c in generate_calendar(history):
            print(f"{c['day']}: {c['theme']} ({c['style']}) @ {c['suggested_hour']} [{c['suggested_workflow']}]")

    elif cmd == "refresh":
        force = getattr(args, "force", False)
        print("🔄 刷新中...")
        refresh_engagement(history)


if __name__ == "__main__":
    main()
