"""Video + auto-captions download karta hai (yt-dlp se). AI ki zarurat nahi.

YouTube aksar 429 (Too Many Requests) deta hai automated download pe, isliye:
- video aur subtitles alag-alag download karte hain
- subtitles best-effort hain (fail ho to crash nahi, warning deke aage)
- retries + thoda sleep taaki rate-limit kam lage
"""
import os
import time
import yt_dlp


def _base_opts(out_dir, ffmpeg_location=None):
    opts = {
        "outtmpl": os.path.join(out_dir, "%(id)s.%(ext)s"),
        "quiet": False,
        "noprogress": False,
        "retries": 10,
        "fragment_retries": 10,
        "sleep_interval_requests": 1,   # requests ke beech thoda gap
    }
    if ffmpeg_location:
        opts["ffmpeg_location"] = ffmpeg_location   # merge ke liye ffmpeg kahan hai
    # cookies.txt ho to use karo (cloud pe YouTube "not a bot" ke liye)
    cookies = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies.txt")
    if os.path.exists(cookies) and os.path.getsize(cookies) > 0:
        opts["cookiefile"] = cookies
    return opts


def _find_sub(out_dir, vid, sub_lang):
    for cand in (f"{vid}.{sub_lang}.vtt", f"{vid}.{sub_lang}-orig.vtt"):
        p = os.path.join(out_dir, cand)
        if os.path.exists(p):
            return p
    for f in os.listdir(out_dir):
        if f.startswith(vid) and f.endswith(".vtt"):
            return os.path.join(out_dir, f)
    return None


def _try_subs(url, out_dir, sub_lang, attempts=3, ffmpeg_location=None):
    opts = _base_opts(out_dir, ffmpeg_location)
    opts.update({
        "skip_download": True,
        "writeautomaticsub": True,
        "writesubtitles": True,
        "subtitleslangs": [sub_lang],
        "subtitlesformat": "vtt",
    })
    for a in range(attempts):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
            return _find_sub(out_dir, info["id"], sub_lang)
        except Exception as e:
            wait = 8 * (a + 1)
            print(f"      [subs] attempt {a + 1}/{attempts} fail ({e}). {wait}s ruk ke retry...")
            time.sleep(wait)
    print("      [subs] captions nahi mile (rate-limit ya video pe CC nahi).")
    return None


def download(url, out_dir="downloads", sub_lang="en", ffmpeg_location=None):
    """Returns: (video_path, subtitle_path or None, info_dict)"""
    os.makedirs(out_dir, exist_ok=True)

    # 1) Video download (info ke saath)
    vopts = _base_opts(out_dir, ffmpeg_location)
    vopts.update({
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "merge_output_format": "mp4",
    })
    with yt_dlp.YoutubeDL(vopts) as ydl:
        info = ydl.extract_info(url, download=True)
    vid = info["id"]
    video_path = os.path.join(out_dir, vid + ".mp4")

    # 2) Subtitles alag se (best-effort)
    sub_path = _try_subs(url, out_dir, sub_lang, ffmpeg_location=ffmpeg_location)

    return video_path, sub_path, info


if __name__ == "__main__":
    import sys
    v, s, info = download(sys.argv[1])
    print("VIDEO:", v)
    print("SUBS :", s)
    print("TITLE:", info.get("title"))
