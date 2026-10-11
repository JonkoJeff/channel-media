"""Look up any YouTube videos by id (GitHub Actions, input VIDEO_IDS comma-separated) -> studio/yt/lookup.json + thumbnails in studio/yt/lookup/."""
import json, os, urllib.request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
yt = build("youtube", "v3", credentials=Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"],
           client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token"))
D = os.path.dirname(__file__); os.makedirs(os.path.join(D, "lookup"), exist_ok=True)
out = yt.videos().list(part="snippet,statistics,contentDetails,status", id=os.environ["VIDEO_IDS"]).execute().get("items", [])
for v in out:
    t = v["snippet"]["thumbnails"]; u = (t.get("maxres") or t.get("high") or {}).get("url")
    if u: urllib.request.urlretrieve(u, os.path.join(D, "lookup", v["id"] + ".jpg"))
json.dump(out, open(os.path.join(D, "lookup.json"), "w"), indent=1)
print(f"::notice::lookup {len(out)} videos: " + "; ".join(v["snippet"]["title"] for v in out))
