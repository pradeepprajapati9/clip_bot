"""Secrets loader — CLOUD (GitHub env vars) ya LOCAL (youtube_bot/.env) dono se.

GitHub Actions me secrets env vars ban jaate hain -> yahan se milte hain.
Local pe env nahi hote -> youtube_bot/.env + credentials/token.json se fallback.
Isse clip_bot ab youtube_bot pe depend nahi karta (cloud pe chal sakta hai).
"""
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_YTBOT = os.path.abspath(os.path.join(_ROOT, "..", "youtube_bot"))
_LOCAL = None


def _local_env():
    d = {}
    envf = os.path.join(_YTBOT, ".env")
    if os.path.exists(envf):
        for line in open(envf, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def get(name, default=""):
    global _LOCAL
    v = os.getenv(name, "")
    if v:
        return v
    if _LOCAL is None:
        _LOCAL = _local_env()
    return _LOCAL.get(name, default)


GEMINI_API_KEY = get("GEMINI_API_KEY")
YT_API_KEY = get("YT_API_KEY")
IG_USER_ID = get("IG_USER_ID")
IG_ACCESS_TOKEN = get("IG_ACCESS_TOKEN")
IG_API_BASE = get("IG_API_BASE", "https://graph.instagram.com")


def yt_token_json():
    """token.json ka content — env secret (YT_TOKEN) ya local credentials file se."""
    v = os.getenv("YT_TOKEN", "")
    if v:
        return v
    p = os.path.join(_YTBOT, "credentials", "token.json")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read()
    return ""
