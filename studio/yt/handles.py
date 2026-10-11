"""Check which YouTube handles are taken (channels.list forHandle, 1 quota unit each). Input env HANDLES (comma-separated)."""
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
yt = build("youtube", "v3", credentials=Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"],
           client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token"))
res = []
for h in [x.strip().lstrip("@") for x in os.environ["HANDLES"].split(",") if x.strip()]:
    it = yt.channels().list(part="snippet,statistics", forHandle="@" + h).execute().get("items", [])
    res.append(f"@{h}: " + (f"TAKEN ({it[0]['snippet']['title']}, {it[0]['statistics'].get('subscriberCount', '?')} subs)" if it else "free"))
print("::notice::" + " | ".join(res))
