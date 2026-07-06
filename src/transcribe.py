"""Video ko transcribe karke cues [(start, end, text)] deta hai (faster-whisper).

YouTube pe free captions hote hain, par Drive/Instagram videos pe nahi —
tab ye audio se transcript banata hai (subtitles.parse_vtt jaisा hi output).
"""
_model = None


def _get_model(size="base"):
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        print(f"      [whisper] model '{size}' load (pehli baar ~150MB download)...")
        _model = WhisperModel(size, device="cpu", compute_type="int8")
    return _model


def transcribe(video_path, size="base"):
    """Returns cues: [(start_sec, end_sec, text), ...]"""
    model = _get_model(size)
    segments, info = model.transcribe(video_path, beam_size=1, vad_filter=True)
    cues = []
    for seg in segments:
        t = (seg.text or "").strip()
        if t:
            cues.append((float(seg.start), float(seg.end), t))
    print(f"      [whisper] {len(cues)} segments transcribe hue")
    return cues


if __name__ == "__main__":
    import sys
    for c in transcribe(sys.argv[1])[:15]:
        print(f"{c[0]:7.1f}-{c[1]:7.1f}  {c[2]}")
