"""Clip ko auto-post karta hai — YouTube + Instagram — self-contained (secrets se).

SAFETY: default dry_run=True -> sirf dikhata hai kya post hoga, actually post NAHI karta.
Live posting tabhi jab dry_run=False.
"""
import os

import feedback


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

    # --- LIVE (actually posts) — self-contained, secrets se ---
    from _vendor import yt_upload, ig_post_reel
    privacy = cfg.get("yt_privacy", "public")
    post_to = cfg.get("post_to", ["youtube", "instagram"])
    result = {}
    if "youtube" in post_to:
        try:
            yt_url = yt_upload(clip_path, title, caption, tags, privacy)
            result["youtube"] = yt_url
            vid = yt_url.rstrip("/").split("/")[-1] if yt_url else None
            feedback.record_post(cfg, "youtube", vid, yt_url, title, text, source)
        except Exception as e:
            result["youtube_error"] = str(e)
            print(f"   [youtube] error: {e}")
    if "instagram" in post_to:
        try:
            pid = ig_post_reel(clip_path, caption)
            result["instagram"] = pid
            if pid:
                feedback.record_post(cfg, "instagram", pid, "", title, text, source)
        except Exception as e:
            result["instagram_error"] = str(e)
            print(f"   [instagram] error: {e}")
    return result
