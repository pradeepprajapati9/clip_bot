# clip_bot 🎬

Long-form video (podcast/interview/stream) ko chhote vertical **captioned clips** me kaat-ne wala bot.
ContentRewards / Whop clipping ke liye. Core pipeline **niche-agnostic** hai — kisi bhi content pe chalega.

## Kaam kaise karta hai (flow)
```
YouTube URL  →  download (video + auto-captions)  →  candidate clips chuno
             →  ffmpeg se kaato + 9:16 vertical + captions burn  →  ready clips/  folder
```

Abhi v1 me **AI Whisper nahi** — YouTube ke ready auto-captions use karte hain (free, fast).
Baad me add karenge: LLM se best-hook selection + auto-post (YouTube uploader + Instagram Graph API) + feedback loop.

---

## Setup (ek baar)

### 1. ffmpeg install karo (zaroori)
PowerShell me:
```powershell
winget install --id Gyan.FFmpeg -e
```
Install ke baad terminal **band karke naya kholo**, phir check:
```powershell
ffmpeg -version
```
(Agar `winget` na chale to https://www.gyan.dev/ffmpeg/builds/ se "release full" zip download karke `bin` folder ko PATH me daal do.)

### 2. Python packages
```powershell
cd c:\xampp\htdocs\pr\clip_bot
pip install -r requirements.txt
```

---

## Chalाना (test)
```powershell
python src\pipeline.py "https://www.youtube.com/watch?v=XXXX"
```
- Source video `downloads/` me aayega
- Ready clips `clips/` me aayenge (9:16, captions ke saath)

Options `config.json` me — clip length, kitne clips, caption style, etc.

## Files
| File | Kaam |
|------|------|
| `src/download.py` | yt-dlp se video + auto-caption (.vtt) download |
| `src/subtitles.py` | .vtt ko parse karke timestamped lines banata hai |
| `src/moments.py`   | transcript ko ~30s ke candidate clips me todta hai (recipe yahan tune hoga) |
| `src/clip.py`      | ffmpeg: kaato + 9:16 crop + captions burn |
| `src/pipeline.py`  | sab ko jodta hai (main entry) |

## TODO (aage)
- [ ] LLM se "best hook" wale moments auto-chunna (abhi simple heuristic)
- [ ] Auto-post: `youtube_bot` uploader + Instagram Graph API
- [ ] Feedback loop: posted clips ke views waapas padho → winners double karo
- [ ] Blurred-background 9:16 (abhi center-crop hai)
