"""ffmpeg se: segment kaato + 9:16 vertical crop + captions burn."""
import os
import subprocess


def _fmt_srt_time(t):
    if t < 0:
        t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(cues, start, end, srt_path):
    """[start,end] window ke andar wale cues ka clip-local .srt banata hai."""
    idx = 1
    with open(srt_path, "w", encoding="utf-8") as f:
        for cs, ce, text in cues:
            if ce <= start or cs >= end:
                continue
            a = max(cs, start) - start
            b = min(ce, end) - start
            if b - a < 0.2:
                continue
            f.write(f"{idx}\n{_fmt_srt_time(a)} --> {_fmt_srt_time(b)}\n{text}\n\n")
            idx += 1
    return idx > 1  # True agar kuch likha


def _ffmpeg_exe(cfg):
    """config me diya local ffmpeg use karo, warna system PATH wala."""
    p = cfg.get("ffmpeg_path")
    root = cfg.get("_root", "")
    if p:
        cand = p if os.path.isabs(p) else os.path.join(root, p)
        if os.path.exists(cand):
            return os.path.abspath(cand)
    return "ffmpeg"


def _force_style(style):
    parts = [
        f"FontName={style.get('font', 'Arial')}",
        f"FontSize={style.get('fontsize', 16)}",
        f"PrimaryColour={style.get('primary_colour', '&H00FFFFFF')}",
        f"OutlineColour={style.get('outline_colour', '&H00000000')}",
        f"Outline={style.get('outline', 3)}",
        f"Bold={style.get('bold', 1)}",
        f"Alignment={style.get('alignment', 2)}",
        f"MarginV={style.get('margin_v', 60)}",
    ]
    return ",".join(parts)


def make_clip(video_path, cues, start, end, out_path, cfg):
    """Ek clip banata hai. Windows subtitle-path jhanjhat se bachne ke liye
    ffmpeg ko clips_dir me chalाते hain aur srt ko basename se reference karte hain."""
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(out_path))[0]
    srt_name = base + ".srt"
    srt_path = os.path.join(out_dir, srt_name)

    has_caps = write_srt(cues, start, end, srt_path)

    W = cfg.get("video_width", 1080)
    H = cfg.get("video_height", 1920)
    vf = f"crop=ih*9/16:ih,scale={W}:{H}"
    if has_caps:
        style = _force_style(cfg.get("caption_style", {}))
        # srt_name safe hai (alnum + _), isliye seedha reference
        vf += f",subtitles={srt_name}:force_style='{style}'"

    cmd = [
        _ffmpeg_exe(cfg), "-y",
        "-ss", str(start), "-to", str(end),
        "-i", os.path.abspath(video_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        os.path.basename(out_path),
    ]
    subprocess.run(cmd, cwd=out_dir, check=True)
    return out_path
