"""Chhota LOCAL form — URL daalo, seedha queue.txt me chala jayega.

Chalाने ke liye: add.bat double-click karo (ya: python src\\serve.py)
Phir browser me khulega http://localhost:8000 — URL paste karo, Add dabao. Bas.
"""
import os
import json
import webbrowser
import urllib.parse
import http.server

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "queue.txt")
CONFIG = os.path.join(ROOT, "config.json")
PORT = 8000


def read_queue():
    if not os.path.exists(QUEUE):
        return []
    out = []
    for line in open(QUEUE, encoding="utf-8"):
        s = line.strip()
        if s and not s.startswith("#"):
            out.append(s)
    return out


def add_urls(text):
    urls = [u.strip() for u in text.replace(",", "\n").split("\n") if u.strip()]
    existing = set(read_queue())
    added = 0
    with open(QUEUE, "a", encoding="utf-8") as f:
        for u in urls:
            if u not in existing:
                f.write(u + "\n")
                existing.add(u)
                added += 1
    return added


def set_platforms(plats):
    try:
        cfg = json.loads(open(CONFIG, encoding="utf-8").read())
        cfg["post_to"] = plats or ["instagram"]
        open(CONFIG, "w", encoding="utf-8").write(json.dumps(cfg, indent=2))
    except Exception as e:
        print("config update fail:", e)


def page(msg=""):
    q = read_queue()
    qlist = "".join(f"<li>{u}</li>" for u in q) or "<li style='color:#98a2b3'>(queue khaali)</li>"
    banner = f"<div class='ok'>{msg}</div>" if msg else ""
    return f"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>clip_bot · Add</title><style>
*{{box-sizing:border-box}}body{{font-family:system-ui,Segoe UI,Roboto,sans-serif;
background:#0f1117;color:#eef1f7;margin:0;padding:26px 16px}}
.w{{max-width:520px;margin:0 auto}}h1{{text-align:center}}h1 span{{color:#8b7bff}}
.card{{background:#191c26;border:1px solid #2b3040;border-radius:16px;padding:22px;margin-bottom:16px}}
label{{display:block;font-weight:600;margin:16px 0 8px}}label:first-child{{margin-top:0}}
textarea{{width:100%;background:#10141d;color:#eef1f7;border:1px solid #2b3040;border-radius:12px;
padding:14px;font-size:1rem;min-height:120px;font-family:inherit}}
.chk{{display:flex;gap:12px}}.chk span{{flex:1}}.chk input{{display:none}}
.chk label{{margin:0;text-align:center;padding:13px;border:2px solid #2b3040;border-radius:12px;
cursor:pointer;color:#98a2b3;font-weight:600}}
.chk input:checked+label{{border-color:#6d5efc;color:#fff;background:rgba(109,94,252,.12)}}
button{{width:100%;background:#6d5efc;color:#fff;border:0;border-radius:14px;padding:16px;
font-size:1.1rem;font-weight:700;cursor:pointer;margin-top:22px}}
.ok{{background:#123b28;border:1px solid #28c76f;color:#7ff0b0;padding:12px 14px;
border-radius:12px;margin-bottom:16px}}
ul{{padding-left:20px;line-height:1.9;word-break:break-all}}small{{color:#98a2b3}}
details{{background:#191c26;border:1px solid #2b3040;border-radius:14px;padding:4px 18px;margin-bottom:16px}}
summary{{cursor:pointer;font-weight:700;padding:14px 0;list-style:none}}
summary::-webkit-details-marker{{display:none}}summary::before{{content:"📋 "}}
.flags{{font-size:.92rem;margin:0 0 12px;padding-left:2px}}.flags li{{list-style:none;margin:6px 0}}
.g::before{{content:"✅ "}}.r::before{{content:"❌ "}}
.order{{background:#10141d;border-radius:10px;padding:11px 13px;font-size:.86rem;color:#cfe3ff;margin:0 0 10px}}
</style></head><body><div class=w>
<h1>🎬 clip_<span>bot</span></h1>
{banner}
<details><summary>Best campaign kaise chunein?</summary>
<ul class=flags>
<li class=g>Instagram ya YouTube allowed ho (sirf TikTok = India ban)</li>
<li class=g>Budget bacha ho (jaise $500/$5000)</li>
<li class=g>CPM $1/1K se upar</li>
<li class=g>Podcast / interview / streamer content (clear speech)</li>
<li class=g>Source video/link diya ho</li>
</ul>
<ul class=flags>
<li class=r>"30%+ Tier 1 audience required" — Indian views count nahi honge</li>
<li class=r>Budget full ($5000/$5000) = dead campaign</li>
<li class=r>CPM $0.12/1K type = bekaar</li>
<li class=r>Gambling / casino = India me risk</li>
<li class=r>"Use our AI tool" ya heavy editing = bot fit nahi</li>
</ul>
<p class=order><b>5-second check:</b> Platform → Tier → Budget → CPM → Content</p>
</details>
<form method=post class=card>
  <label>Kahan post hogi?</label>
  <div class=chk>
    <span><input type=checkbox name=ig id=ig checked><label for=ig>📷 Instagram</label></span>
    <span><input type=checkbox name=yt id=yt checked><label for=yt>▶️ YouTube</label></span>
  </div>
  <label>Video URL(s) <small>(ek line me ek)</small></label>
  <textarea name=urls placeholder="https://www.youtube.com/watch?v=..."></textarea>
  <button>Add to queue ✅</button>
</form>
<div class=card>
  <b>Queue me abhi ({len(q)}):</b>
  <ul>{qlist}</ul>
  <small>Cron roz 10 AM inhe post karega. Ek baar post hone ke baad apne aap hat jate hain.</small>
</div>
</div></body></html>"""


class H(http.server.BaseHTTPRequestHandler):
    def _send(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(page())

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        data = urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8"))
        plats = []
        if "ig" in data:
            plats.append("instagram")
        if "yt" in data:
            plats.append("youtube")
        set_platforms(plats)
        added = add_urls(data.get("urls", [""])[0])
        where = " + ".join(p.title() for p in plats) or "kahin nahi"
        self._send(page(f"✅ {added} URL add ho gaye. Post to: {where}"))

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"Form yahan khulega: http://localhost:{PORT}")
    print("Band karne ke liye ye window band kar do (ya Ctrl+C).")
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except Exception:
        pass
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
