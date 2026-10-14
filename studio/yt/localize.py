"""Adds localized titles/descriptions to existing videos of the channel the YT_REFRESH_TOKEN belongs to (Crazy Facts).
Spec: studio/yt/localize.json {videoId: {"es": {"title": "...", "blurb": "..."}}}. The original (English) description is kept below the blurb.
Needs a token with the youtube (write) scope; says so clearly if it does not."""
import json, os, sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
D = os.path.dirname(__file__)
yt = build("youtube", "v3", credentials=Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"],
           client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token"))
spec = json.load(open(os.path.join(D, "localize.json")))
for vid, langs in spec.items():
    try:
        it = yt.videos().list(part="snippet,localizations", id=vid).execute()["items"][0]
        sn = it["snippet"]; loc = it.get("localizations", {})
        for lg, t in langs.items():
            loc[lg] = {"title": t["title"][:100], "description": (t["blurb"] + "\n\n" + sn.get("description", ""))[:4900]}
        sn["defaultLanguage"] = sn.get("defaultLanguage") or "en"
        yt.videos().update(part="snippet,localizations", body={"id": vid, "snippet": {k: sn[k] for k in ("title", "description", "categoryId", "defaultLanguage") if k in sn} | ({"tags": sn["tags"]} if sn.get("tags") else {}), "localizations": loc}).execute()
        print(f"::notice::{vid}: localized {','.join(langs)}")
    except HttpError as e:
        print(f"::error::{vid}: {e.status_code} {str(e.reason)[:160]} (a 403 here means the stored YouTube token has no write scope: re-authorize with the 'youtube' scope)")
