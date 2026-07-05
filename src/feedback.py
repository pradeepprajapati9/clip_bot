"""Feedback loop — bot ka 'seekhne wala' dimaag.

- record_post(): har posted clip ko data/posts.json me log karta hai (title, hook, id)
- refresh():     YouTube + Instagram se latest views/likes waapas padhta hai
- report():      score ke hisaab se ranked list — kaunsa hook/format jeeta

YouTube stats: youtube_bot ka YT_API_KEY (public Data API). Instagram: graph.instagram.com.
"""
import os
import sys
import json
from datetime import datetime


def _posts_file(cfg):
    root = cfg.get("_root", ".")
    d = os.path.join(root, "data")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "posts.json")


def _load(cfg):
    p = _posts_file(cfg)
    if os.path.exists(p):
        try:
            return json.loads(open(p, encoding="utf-8").read())
        except Exception:
            pass
    return {"posts": []}


def _save(cfg, data):
    open(_posts_file(cfg), "w", encoding="utf-8").write(
        json.dumps(data, ensure_ascii=False, indent=2))


def _ytbot_config(cfg):
    yt_bot = cfg.get("youtube_bot_path", "../youtube_bot")
    root = cfg.get("_root", "")
    yt_bot = yt_bot if os.path.isabs(yt_bot) else os.path.join(root, yt_bot)
    yt_bot = os.path.abspath(yt_bot)
    if yt_bot not in sys.path:
        sys.path.insert(0, yt_bot)
    import config as ytcfg
    return ytcfg


def record_post(cfg, platform, post_id, url, title, hook, source):
    """Ek successful post ko log karta hai."""
    if not post_id:
        return
    data = _load(cfg)
    data["posts"].append({
        "platform": platform,
        "post_id": str(post_id),
        "url": url,
        "title": title or "",
        "hook": (hook or "")[:200],
        "source": source or "",
        "posted_at": datetime.now().isoformat(timespec="seconds"),
        "views": 0, "likes": 0, "comments": 0, "score": 0,
    })
    data["posts"] = data["posts"][-500:]
    _save(cfg, data)


def _refresh_youtube(ytcfg, posts):
    ids = [p["post_id"] for p in posts if p["platform"] == "youtube"]
    if not ids or not getattr(ytcfg, "YT_API_KEY", ""):
        if ids:
            print("[feedback] YT_API_KEY missing -> YouTube views skip")
        return
    from googleapiclient.discovery import build
    yt = build("youtube", "v3", developerKey=ytcfg.YT_API_KEY)
    stats = {}
    for i in range(0, len(ids), 50):
        resp = yt.videos().list(part="statistics", id=",".join(ids[i:i + 50])).execute()
        for it in resp.get("items", []):
            stats[it["id"]] = it.get("statistics", {})
    for p in posts:
        s = stats.get(p["post_id"])
        if s:
            p["views"] = int(s.get("viewCount", 0) or 0)
            p["likes"] = int(s.get("likeCount", 0) or 0)
            p["comments"] = int(s.get("commentCount", 0) or 0)
    print(f"[feedback] YouTube: {len(stats)} clips refreshed")


def _refresh_instagram(ytcfg, posts):
    import requests
    token = getattr(ytcfg, "IG_ACCESS_TOKEN", "")
    base = getattr(ytcfg, "IG_API_BASE", "https://graph.instagram.com")
    ig_posts = [p for p in posts if p["platform"] == "instagram"]
    if not ig_posts or not token:
        return
    ok = 0
    for p in ig_posts:
        try:
            m = requests.get(f"{base}/{p['post_id']}", timeout=30, params={
                "fields": "like_count,comments_count", "access_token": token}).json()
            p["likes"] = int(m.get("like_count", 0) or 0)
            p["comments"] = int(m.get("comments_count", 0) or 0)
            ins = requests.get(f"{base}/{p['post_id']}/insights", timeout=30, params={
                "metric": "reach", "access_token": token}).json()
            for d in ins.get("data", []):
                if d.get("name") == "reach":
                    p["views"] = int(d["values"][0]["value"])
            ok += 1
        except Exception as ex:
            print(f"[feedback] IG {p['post_id']} skip: {ex}")
    print(f"[feedback] Instagram: {ok} clips refreshed")


def refresh(cfg):
    """YouTube + Instagram se latest stats + rescore."""
    data = _load(cfg)
    posts = data["posts"]
    if not posts:
        print("[feedback] abhi koi post log nahi hua")
        return
    ytcfg = _ytbot_config(cfg)
    try:
        _refresh_youtube(ytcfg, posts)
    except Exception as ex:
        print(f"[feedback] YouTube refresh skip: {ex}")
    try:
        _refresh_instagram(ytcfg, posts)
    except Exception as ex:
        print(f"[feedback] IG refresh skip: {ex}")
    for p in posts:
        p["score"] = p["views"] + 20 * p["likes"] + 50 * p["comments"]
    _save(cfg, data)


def report(cfg, k=10):
    data = _load(cfg)
    posts = sorted(data["posts"], key=lambda p: p.get("score", 0), reverse=True)
    if not posts:
        print("Koi post nahi. Pehle --post se clips daalo, phir feedback aayega.")
        return
    print(f"\n=== TOP CLIPS (views ke hisaab se) ===")
    for i, p in enumerate(posts[:k], 1):
        print(f"{i}. [{p['platform']:9}] {p['views']:>7} views | {p['likes']} likes  "
              f"| {p['title'][:55]}")
    print("\n>> Upar wale HOOKS jeet rahe hain — aage aise clips zyada banao.")


if __name__ == "__main__":
    # standalone: refresh + report
    import json as _j
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = _j.loads(open(os.path.join(root, "config.json"), encoding="utf-8").read())
    cfg["_root"] = root
    refresh(cfg)
    report(cfg)
