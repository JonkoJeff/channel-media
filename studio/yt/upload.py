"""Uploads pending items from studio/yt/queue.json to YouTube (runs in GitHub Actions).
Item: {id, channel (optional slug, e.g. "moneyglitch" -> secret YT_REFRESH_TOKEN_MONEYGLITCH; default YT_REFRESH_TOKEN), file (raw URL), thumb (raw URL|null), title, description, tags[], publish_at (ISO, UTC) | null, short: bool, status: "pending"}
After upload: status "uploaded", video_id. Secrets: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN."""
import json, os, urllib.request, tempfile
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

Q = os.path.join(os.path.dirname(__file__), "queue.json")
S = {k: v for k, v in os.environ.items() if k.startswith("YT_REFRESH_TOKEN_") and v}  # extra channels: add env lines in the workflow
def client(channel=None):
    tok = S.get("YT_REFRESH_TOKEN_" + channel.upper()) if channel else os.environ.get("YT_REFRESH_TOKEN")
    if not tok: raise SystemExit(f"::error::Missing GitHub secret YT_REFRESH_TOKEN_{(channel or '').upper()}")
    return build("youtube", "v3", credentials=Credentials(None, refresh_token=tok, client_id=os.environ["YT_CLIENT_ID"],
                 client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token"))
yt = client()
q = json.load(open(Q)) if os.path.exists(Q) else []
if os.environ.get("CHECK_ONLY"):
    missing = [k for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN") if not os.environ.get(k)]
    if missing: print(f"::error::Missing GitHub secrets: {missing}"); raise SystemExit(1)
    import datetime
    st = {"checked_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"), "channels": []}
    try:
        for ch in [None] + [k[17:].lower() for k in S]:
            items = client(ch).channels().list(part="snippet,statistics", mine=True).execute().get("items", [])
            print(f"::notice::{ch or 'default'} -> {items[0]['snippet']['title'] if items else 'NO CHANNEL (pick the channel at sign-in)'}")
            st["channels"] += [{"key": ch or "default", "id": c["id"], "title": c["snippet"]["title"],
                                **{k: int(v) for k, v in c["statistics"].items() if k in ("subscriberCount", "viewCount", "videoCount")}} for c in items]
        json.dump(st, open(os.path.join(os.path.dirname(__file__), "status.json"), "w"), indent=1)
        print("::notice::status " + json.dumps(st))
    except Exception as e:
        print(f"::error::{type(e).__name__}: {str(e)[:300]}"); raise SystemExit(1)
    raise SystemExit

def fetch(url):
    p = tempfile.mktemp(suffix=os.path.splitext(url)[1]); urllib.request.urlretrieve(url, p); return p

for it in q:
    if it.get("status") != "pending": continue
    status = {"privacyStatus": "private" if it.get("publish_at") else "public", "selfDeclaredMadeForKids": False,
              "containsSyntheticMedia": True}
    if it.get("publish_at"): status["publishAt"] = it["publish_at"]
    body = {"snippet": {"title": it["title"], "description": it["description"], "tags": it.get("tags", []), "categoryId": "27"},
            "status": status}
    yc = client(it.get("channel"))
    r = yc.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(fetch(it["file"]), resumable=True)).execute()
    it["video_id"], it["status"] = r["id"], "uploaded"
    if it.get("thumb"):
        yc.thumbnails().set(videoId=r["id"], media_body=MediaFileUpload(fetch(it["thumb"]))).execute()
    print("uploaded", it["id"], r["id"], r["status"]["privacyStatus"])
    json.dump(q, open(Q, "w"), indent=1)
