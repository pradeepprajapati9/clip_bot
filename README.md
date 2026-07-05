# clip_bot 🎬

An AI-powered bot that turns long-form videos (podcasts / interviews / streams) into
short vertical **captioned clips** and auto-posts them to YouTube and Instagram.
Built for ContentRewards / Whop-style clipping. The core pipeline is niche-agnostic —
it works on any clear-speech content.

## Pipeline

```
YouTube URL
   → download video + auto-captions (yt-dlp, no Whisper needed)
   → Gemini picks the most viral moments + writes scroll-stopping titles/captions
   → ffmpeg: cut + 9:16 blurred-background layout + burned captions
   → auto-post to YouTube + Instagram
   → feedback loop: read back views, rank the winning hooks
```

## Features

- **Smart clip selection** — Gemini reads the transcript and picks the best hooks
  (falls back to a keyword heuristic if the LLM is unavailable).
- **Viral titles & captions** — generated per clip, with hashtags.
- **9:16 vertical** — blurred-background layout (no side-cropping); captions burned in.
- **Auto-post** — YouTube (Data API) + Instagram Reels (Graph API), reusing the
  `youtube_bot` project's uploaders.
- **Feedback loop** — logs every post, reads back view counts, ranks what's working.
- **Resilient** — YouTube 429 handling, download caching (re-runs skip re-download).

## Setup (one time)

### 1. Install ffmpeg
```powershell
winget install --id Gyan.FFmpeg -e
```
If winget fails, download the "release full" build from
https://www.gyan.dev/ffmpeg/builds/ and either add its `bin` to PATH or drop
`ffmpeg.exe` + `ffprobe.exe` into `clip_bot/tools/ffmpeg/` (the path used by `config.json`).

### 2. Python packages
```powershell
cd clip_bot
pip install -r requirements.txt
# for auto-posting to YouTube:
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

### 3. Credentials (for auto-posting)
Auto-post reuses the sibling `youtube_bot` project. Its `.env` (git-ignored) supplies:
- `GEMINI_API_KEY` — clip selection + titles
- `YT_API_KEY` — reading public view counts (feedback loop)
- `IG_USER_ID`, `IG_ACCESS_TOKEN` — Instagram publishing
YouTube upload uses `youtube_bot/credentials/token.json` (run `python src\yt_auth.py`
once to authorize the target channel).

## Usage

```powershell
# make clips only (no posting)
python src\pipeline.py "https://www.youtube.com/watch?v=XXXX"

# preview the titles/captions that would be posted (nothing is published)
python src\pipeline.py "https://www.youtube.com/watch?v=XXXX" --dry-post

# LIVE: generate clips and post to YouTube + Instagram
python src\pipeline.py "https://www.youtube.com/watch?v=XXXX" --post

# read back view counts for everything posted and rank the winners
python src\pipeline.py --feedback
```

Source videos land in `downloads/`, finished clips in `clips/`.
All options live in `config.json` (clip length, number of clips, layout, caption
style, YouTube privacy, hashtags, LLM on/off).

## Files

| File | Purpose |
|------|---------|
| `src/pipeline.py`  | Main entry — orchestrates the whole flow |
| `src/download.py`  | yt-dlp: download video + auto-captions (`.vtt`) |
| `src/subtitles.py` | Parse `.vtt` into timestamped lines |
| `src/moments.py`   | Heuristic clip/hook selection (LLM fallback) |
| `src/llm.py`       | Gemini-powered clip selection + titles/captions |
| `src/clip.py`      | ffmpeg: cut + 9:16 layout + burn captions |
| `src/autopost.py`  | Post clips to YouTube + Instagram |
| `src/feedback.py`  | Log posts, read back views, rank winners |
| `src/yt_auth.py`   | One-time YouTube channel authorization helper |

## Notes

- Never commit secrets. All API keys/tokens live in `youtube_bot/.env` (git-ignored);
  `downloads/`, `clips/`, `tools/`, and `data/` are ignored too.
- Instagram Reels are always public. Instagram access tokens are long-lived (~60 days)
  and need periodic refresh.
- Earnings depend on real views — quality of the hook matters more than volume.
  Do not use fake/botted views (detected and rejected).
