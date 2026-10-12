"""Zernio route (https://zernio.com/api/v1), run in GitHub Actions with secret ZERNIO_API_KEY. Never commit the key.
  python3 studio/yt/zernio.py accounts                      -> lists connected accounts into studio/yt/zernio.json
  python3 studio/yt/zernio.py playlist "Title" "desc"       -> creates a public YouTube playlist, stores its id in zernio.json
  python3 studio/yt/zernio.py post lfNN 2026-10-13T17:00     -> uploads renders/lfNN video (presign), schedules it (Europe/Amsterdam)
The YouTube account id and playlist ids live in studio/yt/zernio.json (not secret)."""
import json, os, sys, urllib.request
API = "https://zernio.com/api/v1"; KEY = os.environ["ZERNIO_API_KEY"]
D = os.path.dirname(os.path.abspath(__file__)); CFG = os.path.join(D, "zernio.json"); R = os.path.join(D, "..", "renders")
cfg = json.load(open(CFG)) if os.path.exists(CFG) else {}


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e: sys.exit(f"::error::Zernio {method} {path}: {e.code} {e.read()[:800]}")


def save(): json.dump(cfg, open(CFG, "w"), indent=1)


def yt_account():
    return cfg.get("youtube") or sys.exit("::error::no YouTube account in zernio.json; run 'accounts' first and connect YouTube in the Zernio dashboard")


cmd = sys.argv[1]
if cmd == "accounts":
    _, a = call("GET", "/accounts"); acc = a.get("accounts", a if isinstance(a, list) else [])
    cfg["accounts"] = [{k: x.get(k) for k in ("_id", "id", "platform", "username", "displayName", "name")} for x in acc]
    yt = [x for x in cfg["accounts"] if x["platform"] == "youtube"]
    if yt: cfg["youtube"] = yt[0].get("_id") or yt[0].get("id")
    save(); print("::notice::Zernio accounts: " + ", ".join(f"{x['platform']}:{x.get('username') or x.get('displayName') or x.get('name')}" for x in cfg["accounts"]))
elif cmd == "playlist":
    title, desc = sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "")
    _, p = call("POST", f"/accounts/{yt_account()}/youtube-playlists", {"title": title, "description": desc, "privacy": "public"})
    cfg.setdefault("playlists", {})[title] = p["playlist"]["id"]; save(); print(f"::notice::playlist {title} = {p['playlist']['id']}")
elif cmd == "post":
    vid, when = sys.argv[2], sys.argv[3]
    v = json.load(open(os.path.join(D, "..", "assetedit", "videos", vid + ".json"))); res = json.load(open(os.path.join(R, vid, "result.json")))
    mp4 = sys.argv[4] if len(sys.argv) > 4 else f"/tmp/{vid}.mp4"   # the workflow downloads the release asset here
    _, ps = call("POST", "/media/presign", {"filename": vid + ".mp4", "contentType": "video/mp4", "size": os.path.getsize(mp4)})
    up = urllib.request.Request(ps["uploadUrl"], data=open(mp4, "rb"), method="PUT",
                                headers={"Content-Type": "video/mp4", "Content-Length": str(os.path.getsize(mp4))})
    urllib.request.urlopen(up, timeout=1800).read()
    psd = {"title": v["title"][:100], "visibility": "public", "categoryId": "27", "madeForKids": False, "containsSyntheticMedia": True}
    pl = [cfg.get("playlists", {}).get(t) for t in v.get("playlists", [])]
    if pl and pl[0]: psd["playlistId"] = pl[0]
    body = {"content": open(os.path.join(R, vid, "description.txt")).read(), "tags": [t.lstrip("#") for t in v.get("tags", [])],
            "mediaItems": [{"type": "video", "url": ps["publicUrl"], "thumbnail": res["thumb"]}],
            "platforms": [{"platform": "youtube", "accountId": yt_account(), "platformSpecificData": psd}],
            "scheduledFor": when, "timezone": "Europe/Amsterdam"}
    st, p = call("POST", "/posts", body); post = p.get("post", p)
    if st == 207 or post.get("status") == "failed": sys.exit(f"::error::Zernio post failed: {json.dumps(post)[:800]}")
    res.update(zernio_id=post.get("_id"), scheduled=when + "+02:00", route="zernio"); json.dump(res, open(os.path.join(R, vid, "result.json"), "w"), indent=1)
    print(f"::notice::{vid} scheduled via Zernio for {when}: post {post.get('_id')}")
