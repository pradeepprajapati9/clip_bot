"""Self-contained Gemini + YouTube-upload + Instagram-post (secrets se, youtube_bot ke bina).
Cloud (GitHub Actions) aur local dono pe chalta hai via settings.py."""
import json
import time
import requests

import settings

GEMINI_MODELS = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]


def gemini_call(prompt, timeout=60):
    key = settings.GEMINI_API_KEY
    if not key:
        return ""
    for attempt in range(2):
        for model in GEMINI_MODELS:
            url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{model}:generateContent?key={key}")
            try:
                r = requests.post(url, timeout=timeout,
                                  json={"contents": [{"parts": [{"text": prompt}]}]})
                if r.status_code == 200:
                    return r.json()["candidates"][0]["content"]["parts"][0]["text"]
                if r.status_code in (429, 503):
                    continue
                print(f"[gemini] {model} http {r.status_code}: {r.text[:140]}")
            except Exception as ex:
                print(f"[gemini] {model} error: {ex}")
        if attempt == 0:
            time.sleep(3)
    return ""


def yt_upload(video_path, title, description, tags, privacy="public"):
    """token.json (embedded client_id/secret/refresh) se seedha upload — client_secret.json ki zarurat nahi."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    info = json.loads(settings.yt_token_json())
    creds = Credentials.from_authorized_user_info(info, SCOPES)
    yt = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {"title": title[:100], "description": description[:4900],
                    "tags": tags[:15], "categoryId": "27"},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    url = f"https://youtu.be/{resp['id']}"
    print(f"[upload] done -> {url}")
    return url


def _host_video(path):
    try:
        with open(path, "rb") as f:
            r = requests.post("https://catbox.moe/user/api.php",
                              data={"reqtype": "fileupload"},
                              files={"fileToUpload": f}, timeout=180)
        if r.status_code == 200 and r.text.startswith("http"):
            return r.text.strip()
        print(f"[instagram] host failed: {r.status_code} {r.text[:100]}")
    except Exception as ex:
        print(f"[instagram] host error: {ex}")
    return None


def ig_post_reel(video_path, caption):
    uid, token, base = settings.IG_USER_ID, settings.IG_ACCESS_TOKEN, settings.IG_API_BASE
    if not (uid and token):
        return None
    video_url = _host_video(video_path)
    if not video_url:
        return None
    try:
        r = requests.post(f"{base}/{uid}/media", timeout=60, data={
            "media_type": "REELS", "video_url": video_url,
            "caption": caption[:2200], "access_token": token})
        cid = r.json().get("id")
        if not cid:
            print(f"[instagram] container failed: {r.text[:200]}")
            return None
        for _ in range(25):
            time.sleep(6)
            s = requests.get(f"{base}/{cid}", timeout=30, params={
                "fields": "status_code", "access_token": token})
            code = s.json().get("status_code")
            if code == "FINISHED":
                break
            if code == "ERROR":
                print("[instagram] processing ERROR")
                return None
        else:
            print("[instagram] processing timed out")
            return None
        p = requests.post(f"{base}/{uid}/media_publish", timeout=60, data={
            "creation_id": cid, "access_token": token})
        pid = p.json().get("id")
        if pid:
            print(f"[instagram] reel published: {pid}")
            return pid
        print(f"[instagram] publish failed: {p.text[:200]}")
    except Exception as ex:
        print(f"[instagram] post error: {ex}")
    return None
