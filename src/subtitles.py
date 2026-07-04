"""WebVTT caption file ko parse karke [(start, end, text)] list banata hai."""
import re
import html

_TS = re.compile(r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})")


def _to_seconds(ts):
    h, m, s, ms = ts
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_vtt(path):
    """Return list of cues: [(start_sec, end_sec, text), ...] time ke order me."""
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    cues = []
    for block in re.split(r"\n\s*\n", raw):
        m = _TS.findall(block)
        if len(m) < 2:
            continue
        start = _to_seconds(m[0])
        end = _to_seconds(m[1])

        # text lines = timestamp line ke baad wali lines
        lines = block.splitlines()
        text_lines = []
        for ln in lines:
            if "-->" in ln or ln.strip().upper() == "WEBVTT" or ln.strip().isdigit():
                continue
            # inline timing tags <00:00:01.000> aur <c> tags hata do
            ln = re.sub(r"<[^>]+>", "", ln)
            if ln.strip():
                text_lines.append(html.unescape(ln.strip()))
        text = " ".join(text_lines).strip()
        if text:
            cues.append((start, end, text))

    # YouTube auto-captions me aksar duplicate/rolling lines hote hain — dedupe
    cleaned = []
    for start, end, text in cues:
        if cleaned and cleaned[-1][2] == text:
            # same text repeat -> end time extend kar do
            ps, pe, pt = cleaned[-1]
            cleaned[-1] = (ps, max(pe, end), pt)
            continue
        cleaned.append((start, end, text))
    return cleaned


if __name__ == "__main__":
    import sys
    for c in parse_vtt(sys.argv[1])[:20]:
        print(f"{c[0]:7.1f} - {c[1]:7.1f}  {c[2]}")
