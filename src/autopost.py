"""Clip ko auto-post karta hai — YouTube + Instagram — youtube_bot ko reuse karke.

SAFETY: default dry_run=True -> sirf dikhata hai kya post hoga, actually post NAHI karta.
Live posting tabhi jab dry_run=False (aur tera explicit OK ho).
"""
import os
import sys

import feedback


def _load_ytbot(yt_bot_path):
    """youtube_bot ke uploader + instagram module import karta hai."""
    yt_bot_path = os.path.abspath(yt_bot_path)
    if yt_bot_path not in sys.path:
        sys.path.insert(0, yt_bot_path)
    import config                       # youtube_bot/config.py
    from bot import uploader, instagram
    return config, uploader, instagram


def make_caption(text, hashtags):
    """Clip ke transcript se title + caption banata hai."""
    first = (text or "").strip().replace("\n", " ")
    # pehla vaakya = hook line
    for sep in (".", "?", "!"):
        if sep in first:
            first = first.split(sep)[0].strip() + sep
            break
    title = (first[:90]).strip() or "Watch this 👀"
    tagline = " ".join(hashtags)
    caption = f"{first}\n\n{tagline}"
    return title, caption


def post_clip(clip_path, text, cfg, dry_run=True, title=None, caption=None, source=None):
    hashtags = cfg.get("hashtags", ["#shorts", "#podcast", "#motivation"])
    # LLM ne title/caption diya to wahi use karo, warna auto-generate
    if title and caption:
        pass
    else:
        title, caption = make_caption(text, hashtags)
    tags = [h.lstrip("#") for h in hashtags]

    if dry_run:
        print(f"   [DRY-RUN] {os.path.basename(clip_path)}")
        print(f"             title  : {title}")
        print(f"             caption: {caption[:70]}...")
        return {"dry_run": True, "title": title}

    # --- LIVE (actually posts) ---
    yt_bot = cfg.get("youtube_bot_path", r"c:\xampp\htdocs\pr\youtube_bot")
    _config, uploader, instagram = _load_ytbot(yt_bot)
    # clip_bot apni privacy control kare (.env chhue bina) — test-safe default private
    _config.YT_PRIVACY = cfg.get("yt_privacy", "private")
    result = {}
    try:
        yt_url = uploader.upload(clip_path, title, caption, tags)
        result["youtube"] = yt_url
        vid = yt_url.rstrip("/").split("/")[-1] if yt_url else None
        feedback.record_post(cfg, "youtube", vid, yt_url, title, text, source)
    except Exception as e:
        result["youtube_error"] = str(e)
        print(f"   [youtube] error: {e}")
    try:
        pid = instagram.post_reel(clip_path, caption)
        result["instagram"] = pid
        if pid:
            feedback.record_post(cfg, "instagram", pid, "", title, text, source)
    except Exception as e:
        result["instagram_error"] = str(e)
        print(f"   [instagram] error: {e}")
    return result
