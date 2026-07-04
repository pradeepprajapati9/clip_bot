"""Gemini se BEST clips chunna + scroll-stopping title/caption likhna.

youtube_bot ka gemini_call reuse karta hai (GEMINI_API_KEY .env me).
Key na ho / fail ho -> None return -> pipeline heuristic pe fallback ho jata hai.
"""
import os
import sys
import json
import re

from moments import clean_cues, _build_segment


def _gemini_fn(cfg):
    """youtube_bot se gemini_call laata hai, agar key set ho."""
    yt_bot = cfg.get("youtube_bot_path", "../youtube_bot")
    root = cfg.get("_root", "")
    yt_bot = yt_bot if os.path.isabs(yt_bot) else os.path.join(root, yt_bot)
    yt_bot = os.path.abspath(yt_bot)
    if not os.path.isdir(yt_bot):
        return None
    if yt_bot not in sys.path:
        sys.path.insert(0, yt_bot)
    try:
        import config as ytcfg
        if not getattr(ytcfg, "GEMINI_API_KEY", ""):
            print("[llm] GEMINI_API_KEY nahi mila -> heuristic use hoga")
            return None
        from bot.thinker import gemini_call
        return gemini_call
    except Exception as e:
        print(f"[llm] gemini load fail: {e} -> heuristic")
        return None


def _extract_json(text):
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def pick_clips(cues, cfg, n=10, min_sec=21, max_sec=34):
    """Gemini se top-N viral clips. Returns candidates ya None (fallback)."""
    gem = _gemini_fn(cfg)
    if not gem:
        return None
    cues = clean_cues(cues)
    if not cues:
        return None

    transcript = "\n".join(f"{int(s)}: {t}" for (s, e, t) in cues)
    prompt = (
        "You are an expert viral short-form video editor. Below is a timestamped "
        "transcript (each line = 'SECONDS: text').\n"
        f"Pick the {n} MOST viral, scroll-stopping {min_sec}-{max_sec} second moments "
        "to clip for TikTok / Instagram Reels / YouTube Shorts. Each clip MUST start on "
        "a strong hook (a bold claim, a question, a surprising line).\n"
        "For each pick return:\n"
        "- start: the exact SECONDS value (from a line's start) where the hook begins\n"
        "- title: a punchy title under 80 chars, no hashtags\n"
        "- caption: one short line + 3-5 relevant hashtags\n"
        'Return ONLY a JSON array, nothing else:\n'
        '[{"start": 123, "title": "...", "caption": "..."}]\n\n'
        f"TRANSCRIPT:\n{transcript}"
    )

    raw = gem(prompt, timeout=60)
    picks = _extract_json(raw)
    if not picks:
        print("[llm] Gemini se valid JSON nahi mila -> heuristic fallback")
        return None

    out, used = [], []
    for p in picks[:n]:
        try:
            st = float(p.get("start"))
        except (TypeError, ValueError):
            continue
        i = min(range(len(cues)), key=lambda k: abs(cues[k][0] - st))
        seg_start, seg_end, text = _build_segment(cues, i, min_sec, max_sec)
        if seg_end - seg_start < min_sec * 0.6:
            continue
        if any(not (seg_end <= us or seg_start >= ue) for us, ue in used):
            continue
        used.append((seg_start, seg_end))
        out.append({
            "start": round(seg_start, 2),
            "end": round(seg_end, 2),
            "text": text,
            "hook": 1.0,
            "title": str(p.get("title", "")).strip()[:90],
            "caption": str(p.get("caption", "")).strip()[:300],
        })
    return out or None
