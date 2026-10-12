"""Look up any YouTube videos by id (GitHub Actions, input VIDEO_IDS comma-separated) -> studio/yt/lookup.json + thumbnails in studio/yt/lookup/."""
import json, os, urllib.request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
yt = build("youtube", "v3", credentials=Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"],
           client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token"))
D = os.path.dirname(__file__); os.makedirs(os.path.join(D, "lookup"), exist_ok=True)
ids = [i for i in os.environ.get("VIDEO_IDS", "").split(",") if i]
for q in [q for q in os.environ.get("SEARCH", "").split(";") if q.strip()]:   # extra: top videos per search query (by views, last 2 years)
    r = yt.search().list(part="id", q=q.strip(), type="video", order="viewCount", maxResults=15, relevanceLanguage="en",
                         publishedAfter="2024-10-01T00:00:00Z").execute()
    ids += [x["id"]["videoId"] for x in r.get("items", []) if x["id"]["videoId"] not in ids]
out = []
for i in range(0, len(ids), 50):
    out += yt.videos().list(part="snippet,statistics,contentDetails,status", id=",".join(ids[i:i + 50])).execute().get("items", [])
chs = list({v["snippet"]["channelId"] for v in out}); cs = {}
for i in range(0, len(chs), 50):
    cs.update({c["id"]: c["statistics"] for c in yt.channels().list(part="statistics", id=",".join(chs[i:i + 50])).execute().get("items", [])})
for v in out: v["channelStats"] = cs.get(v["snippet"]["channelId"], {})
for v in out:
    t = v["snippet"]["thumbnails"]; u = (t.get("medium") or t.get("high") or {}).get("url")
    if u: urllib.request.urlretrieve(u, os.path.join(D, "lookup", v["id"] + ".jpg"))
json.dump(out, open(os.path.join(D, "lookup.json"), "w"), indent=1)
print(f"::notice::lookup {len(out)} videos: " + "; ".join(v["snippet"]["title"] for v in out))
