"""Transcript se BEST candidate clips chunta hai.

v2 recipe:
- junk cues (Translator/credits/[Music]/[Applause]) hata deta hai
- har cue ko "kitna strong HOOK hai" score karta hai
- clips ko sabse strong-hook wale pal se START karta hai (rule #1: pehle 2 sec)
- overlap nahi hone deta, intro ke pehle X sec skip karta hai

Yahi jagah baad me LLM/data-driven recipe lagega. Abhi smart heuristic.
"""
import re

# Ye lines clip me nahi chahiye
JUNK_PATTERNS = [
    r"translator\s*:", r"reviewer\s*:", r"transcriber\s*:",
    r"\[music\]", r"\[applause\]", r"\[laughter\]", r"\[.*?\]",
    r"like and subscribe", r"subscribe to", r"link in (the )?(bio|description)",
]

# Strong opener — inse shuru hone wali line achha hook hoti hai
HOOK_OPENERS = [
    "how ", "why ", "what ", "who ", "when ", "the reason", "here's", "here is",
    "the secret", "the truth", "the biggest", "the one thing", "the problem",
    "the mistake", "nobody", "everybody", "everyone", "most people", "you need",
    "you should", "you have to", "never ", "always ", "stop ", "listen",
    "imagine", "let me tell", "i'll tell you", "the key", "the thing is",
]

# Emotion/curiosity words — hook strong karte hain
EMOTION = [
    "crazy", "shocking", "insane", "amazing", "incredible", "worst", "best",
    "biggest", "secret", "truth", "mistake", "wrong", "unbelievable", "powerful",
    "dangerous", "surprising", "hate", "love", "fail", "success", "money", "rich",
]


def _is_junk(text):
    low = text.lower().strip()
    if len(low) < 3:
        return True
    return any(re.search(p, low) for p in JUNK_PATTERNS)


def clean_cues(cues):
    return [(s, e, t) for (s, e, t) in cues if not _is_junk(t)]


def score_hook(text):
    """0-1: ye line ek clip ke START ke liye kitni achhi hai."""
    t = text.lower().strip()
    score = 0.0

    for op in HOOK_OPENERS:
        if t.startswith(op):
            score += 0.5
            break

    if "?" in t[:120]:            # sawaal = curiosity
        score += 0.3
    if re.search(r"\b\d", t):     # number/stat
        score += 0.2

    hits = sum(1 for w in EMOTION if w in t)
    score += min(0.3, hits * 0.15)

    if re.search(r"\byou\b|\byour\b", t[:80]):   # direct address
        score += 0.15

    return min(1.0, round(score, 2))


def _build_segment(cues, i, min_sec, max_sec):
    """cue i se shuru karke ek clip banata hai jo vaakya ke end pe rukta hai."""
    n = len(cues)
    seg_start = cues[i][0]
    texts, seg_end, j = [], None, i
    while j < n:
        texts.append(cues[j][2])
        dur = cues[j][1] - seg_start
        ends_sentence = cues[j][2].rstrip().endswith((".", "?", "!"))
        if dur >= min_sec and (ends_sentence or dur >= max_sec):
            seg_end = cues[j][1]
            break
        if dur >= max_sec:
            seg_end = cues[j][1]
            break
        j += 1
    if seg_end is None:
        seg_end = cues[min(j, n) - 1][1]
    return seg_start, seg_end, " ".join(texts).strip()


def make_candidates(cues, min_sec=21, max_sec=34, max_clips=10, skip_intro_sec=8):
    cues = clean_cues(cues)
    if not cues:
        return []

    # har cue ko START-hook score do (intro skip karke)
    ranked = [
        (score_hook(cues[i][2]), i)
        for i in range(len(cues))
        if cues[i][0] >= skip_intro_sec
    ]
    ranked.sort(reverse=True)   # sabse strong hook pehle

    used, candidates = [], []
    for sc, i in ranked:
        if len(candidates) >= max_clips:
            break
        seg_start, seg_end, text = _build_segment(cues, i, min_sec, max_sec)
        if seg_end - seg_start < min_sec * 0.6:
            continue
        # overlap check — do clips same footage na cover karein
        if any(not (seg_end <= us or seg_start >= ue) for us, ue in used):
            continue
        used.append((seg_start, seg_end))
        candidates.append({
            "start": round(seg_start, 2),
            "end": round(seg_end, 2),
            "text": text,
            "hook": sc,
        })

    candidates.sort(key=lambda c: c["hook"], reverse=True)
    return candidates


if __name__ == "__main__":
    import sys
    from subtitles import parse_vtt
    cues = parse_vtt(sys.argv[1])
    for c in make_candidates(cues):
        print(f"[{c['start']:.0f}-{c['end']:.0f}] hook={c['hook']:.2f}  {c['text'][:75]}...")
