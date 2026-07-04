"""Main entry: URL do -> ready vertical captioned clips milte hain.

    python src\\pipeline.py "https://youtube.com/watch?v=XXXX"
"""
import os
import re
import sys
import json

# src/ ko import path me daal do
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from download import download, _find_sub
from subtitles import parse_vtt
from moments import make_candidates
from clip import make_clip


def _youtube_id(url):
    m = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def load_config():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["_root"] = root
    return cfg


def run(url):
    cfg = load_config()
    root = cfg["_root"]
    dl_dir = os.path.join(root, cfg.get("download_dir", "downloads"))
    clips_dir = os.path.join(root, cfg.get("clips_dir", "clips"))

    # ffmpeg ka folder (yt-dlp ko merge ke liye chahiye)
    ff = cfg.get("ffmpeg_path")
    ffmpeg_dir = None
    if ff:
        ff_abs = ff if os.path.isabs(ff) else os.path.join(root, ff)
        if os.path.exists(ff_abs):
            ffmpeg_dir = os.path.dirname(ff_abs)

    # agar ye video pehle download ho chuki hai -> dobara download mat karo (data + 429 bachao)
    vid_guess = _youtube_id(url)
    cached = os.path.join(dl_dir, f"{vid_guess}.mp4") if vid_guess else None
    if cached and os.path.exists(cached):
        print(f"\n[1/4] Cached video mil gaya, download skip: {cached}")
        video_path = cached
        sub_path = _find_sub(dl_dir, vid_guess, cfg.get("subtitle_lang", "en"))
        info = {"id": vid_guess, "title": vid_guess}
    else:
        print(f"\n[1/4] Download ho raha hai: {url}")
        video_path, sub_path, info = download(url, dl_dir, cfg.get("subtitle_lang", "en"), ffmpeg_dir)
    print(f"      video: {video_path}")
    print(f"      subs : {sub_path}")

    if not sub_path or not os.path.exists(sub_path):
        print("\n[!] Is video pe captions nahi mile. v1 captions pe chalta hai.")
        print("    Aisा video try karo jispe CC ho, ya baad me Whisper add karenge.")
        return

    print("\n[2/4] Captions parse ho rahe hain...")
    cues = parse_vtt(sub_path)
    print(f"      {len(cues)} caption lines mile")

    print("\n[3/4] Candidate clips chune ja rahe hain...")
    cands = make_candidates(
        cues,
        cfg.get("clip_min_seconds", 21),
        cfg.get("clip_max_seconds", 34),
        cfg.get("max_clips_per_video", 10),
        cfg.get("skip_intro_seconds", 8),
    )
    for k, c in enumerate(cands, 1):
        print(f"      #{k} [{c['start']:.0f}-{c['end']:.0f}s] hook={c['hook']:.2f}  {c['text'][:70]}...")

    print(f"\n[4/4] {len(cands)} clips ban rahe hain...")
    vid = info["id"]
    made = []
    for k, c in enumerate(cands, 1):
        out = os.path.join(clips_dir, f"{vid}_{k:02d}.mp4")
        try:
            make_clip(video_path, cues, c["start"], c["end"], out, cfg)
            made.append(out)
            print(f"      OK  {out}")
        except Exception as e:
            print(f"      FAIL #{k}: {e}")

    print(f"\nDone! {len(made)} clips '{clips_dir}' me ready hain.")
    print("Ab inme se best manually dekho -> post karo -> views note karo (recipe test).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python src\\pipeline.py "<youtube-url>"')
        sys.exit(1)
    run(sys.argv[1])
