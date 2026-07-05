"""Clean YouTube authorization — naye channel ke liye token.json banata hai.

- URL saaf print karta hai (flush) taaki browser na khule to manually khol sakein
- emoji nahi (Windows console crash se bachne)
- youtube_bot ka client_secret + token path use karta hai
"""
import os
import sys

YT_BOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "youtube_bot"))
sys.path.insert(0, YT_BOT)

import config  # youtube_bot/config.py
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

if __name__ == "__main__":
    print("Starting YouTube authorization for NEW channel...", flush=True)
    flow = InstalledAppFlow.from_client_secrets_file(str(config.CLIENT_SECRET_FILE), SCOPES)
    creds = flow.run_local_server(port=0, open_browser=True,
                                  authorization_prompt_message="VISIT THIS URL: {url}")
    config.TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    print("TOKEN SAVED OK ->", config.TOKEN_FILE, flush=True)
