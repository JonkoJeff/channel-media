"""Trend scan (runs in GitHub Actions every 8 h): finds videos from the last 7 days that blew up in our niches,
measured against the channel's size, and saves title, description, tags, length, stats and thumbnail.
Output: studio/trends/latest.json + studio/trends/thumbs/<id>.jpg (replaced each run), studio/trends/history.jsonl (one line per run).
Quota: ~100 units per search, 6 searches per run = ~600 units (default quota is 10,000/day). Topics: studio/trends/topics.json."""
import json, os, re, shutil, urllib.request, datetime as dt
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

D = os.path.join(os.path.dirname(__file__), "..", "trends")
yt = build("youtube", "v3", credentials=Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"],
           client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token"))
now = dt.datetime.now(dt.timezone.utc)
since = (now - dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

def secs(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    return sum(int(x or 0) * k for x, k in zip(m.groups(), (3600, 60, 1))) if m else 0

out, seen = {"scanned_at": now.strftime("%Y-%m-%dT%H:%MZ"), "groups": []}, set()
for t in json.load(open(os.path.join(D, "topics.json"))):
    try:
        ids = [i["id"]["videoId"] for i in yt.search().list(part="id", q=t["q"], type="video", order="viewCount", publishedAfter=since,
               videoDuration=t["duration"], relevanceLanguage="en", maxResults=25).execute().get("items", [])]
        vids = yt.videos().list(part="snippet,statistics,contentDetails", id=",".join(ids)).execute().get("items", []) if ids else []
        subs = {c["id"]: int(c["statistics"].get("subscriberCount", 0)) for c in yt.channels().list(part="statistics",
                id=",".join({v["snippet"]["channelId"] for v in vids})).execute().get("items", [])} if vids else {}
    except Exception as e:
        print(f"::error::{t['q']}: {type(e).__name__}: {str(e)[:200]}"); continue
    rows = []
    for v in vids:
        sn, st, ln = v["snippet"], v.get("statistics", {}), secs(v["contentDetails"]["duration"])
        if t["format"] == "short" and ln > 180 or t["format"] == "long" and ln < 240: continue
        if sum(c.isascii() for c in sn["title"]) < 0.85 * len(sn["title"]) or "Section 107" in sn.get("description", ""): continue  # non-English titles, fan edits
        if int(st.get("viewCount", 0)) < t.get("min_views", 1000): continue
        views, sub = int(st.get("viewCount", 0)), subs.get(sn["channelId"], 0)
        hours = max(1, (now - dt.datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))).total_seconds() / 3600)
        d = sn.get("description", "")
        rows.append({"id": v["id"], "url": "https://youtu.be/" + v["id"], "title": sn["title"], "channel": sn["channelTitle"], "subs": sub,
                     "views": views, "likes": int(st.get("likeCount", 0)), "comments": int(st.get("commentCount", 0)),
                     "vph": round(views / hours), "outlier": round(views / max(sub, 1000), 1), "seconds": ln,
                     "published": sn["publishedAt"][:16], "tags": sn.get("tags", [])[:15], "chapters": bool(re.search(r"(?m)^\s*0?0:00", d)),
                     "description": d[:1200], "thumb": (sn["thumbnails"].get("maxres") or sn["thumbnails"].get("high") or {}).get("url")})
    rows = sorted(rows, key=lambda r: (r["outlier"], r["vph"]), reverse=True)[:t.get("keep", 6)]
    out["groups"].append({**t, "videos": rows})
    seen |= {r["id"] for r in rows}

th = os.path.join(D, "thumbs"); shutil.rmtree(th, ignore_errors=True); os.makedirs(th)
for g in out["groups"]:
    for r in g["videos"]:
        try: urllib.request.urlretrieve(r["thumb"], os.path.join(th, r["id"] + ".jpg"))
        except Exception: pass
json.dump(out, open(os.path.join(D, "latest.json"), "w"), indent=1)
hp = os.path.join(D, "history.jsonl")  # YouTube API policy: keep other channels' data max 30 days
if os.path.exists(hp):
    keep = [l for l in open(hp) if l.strip() and json.loads(l)["at"] >= (now - dt.timedelta(days=30)).strftime("%Y-%m-%dT%H:%MZ")]
    open(hp, "w").writelines(keep)
with open(hp, "a") as h:
    h.write(json.dumps({"at": out["scanned_at"], "top": [{k: r[k] for k in ("id", "title", "channel", "views", "outlier", "seconds")}
            for g in out["groups"] for r in g["videos"][:3]]}) + "\n")
print(f"::notice::trend scan: {len(seen)} videos in {len(out['groups'])} groups")
