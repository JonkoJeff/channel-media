"""Zernio route (https://zernio.com/api/v1), run in GitHub Actions with secret ZERNIO_API_KEY. Never commit the key.
  python3 studio/yt/zernio.py accounts                      -> lists connected accounts into studio/yt/zernio.json
  python3 studio/yt/zernio.py playlist "Title" "desc"       -> creates a public YouTube playlist, stores its id in zernio.json
  python3 studio/yt/zernio.py post lfNN 2026-10-13T17:00     -> uploads renders/lfNN video (presign), schedules it (Europe/Amsterdam)
  python3 studio/yt/zernio.py shorts lfNN 2026-10-13         -> schedules all Shorts of lfNN, 3 a day (09:00, 13:00, 21:00) from that date
The YouTube account id and playlist ids live in studio/yt/zernio.json (not secret)."""
import json, os, sys, urllib.request
API = "https://zernio.com/api/v1"; KEY = os.environ["ZERNIO_API_KEY"]; KEY2 = os.environ.get("ZERNIO_API_KEY_2", "")  # KEY2 = second Zernio account (channel "religion")
D = os.path.dirname(os.path.abspath(__file__)); CFG = os.path.join(D, "zernio.json"); R = os.path.join(D, "..", "renders")
cfg = json.load(open(CFG)) if os.path.exists(CFG) else {}


import traceback
def _hook(t, e, tb): print("::error::" + " | ".join("".join(traceback.format_exception(t, e, tb)).splitlines())[-900:]); sys.exit(1)
sys.excepthook = _hook

def call(method, path, body=None, soft=False):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e: sys.exit(f"::error::Zernio {method} {path}: {e.code} {e.read()[:800]}")
    except Exception as e:
        if soft: print(f"::warning::{method} {path} no answer ({type(e).__name__}); checking whether the post exists"); return None, None
        sys.exit(f"::error::Zernio {method} {path}: {type(e).__name__} {str(e)[:300]}")


def save(): json.dump(cfg, open(CFG, "w"), indent=1)


def yt_account(ch="crazyfacts"):  # channel key: crazyfacts (default), moneyatnight or religion (own Zernio account / key)
    global KEY
    if ch == "religion": KEY = KEY2 or sys.exit("::error::ZERNIO_API_KEY_2 missing")
    return cfg.get("youtube", {}).get(ch) or sys.exit(f"::error::no YouTube account for {ch} in zernio.json; run 'accounts' after connecting it in Zernio")


cmd = sys.argv[1]
if cmd == "accounts" and sys.argv[2:3] == ["2"]:   # second Zernio account (Religion Unfolded)
    KEY = KEY2 or sys.exit("::error::ZERNIO_API_KEY_2 missing"); _, a = call("GET", "/accounts"); acc = a.get("accounts", a if isinstance(a, list) else [])
    yt = [x for x in acc if x.get("platform") == "youtube"]
    if yt: cfg.setdefault("youtube", {})["religion"] = yt[0].get("_id") or yt[0].get("id"); save()
    print(f"::notice::Zernio account 2: {len(acc)} accounts, {len(yt)} youtube")
elif cmd == "accounts":
    _, a = call("GET", "/accounts"); acc = a.get("accounts", a if isinstance(a, list) else [])
    cfg["accounts"] = [{k: x.get(k) for k in ("_id", "id", "platform", "username", "displayName", "name")} for x in acc]
    yt = [x for x in cfg["accounts"] if x["platform"] == "youtube"]
    cfg["youtube"] = {("moneyatnight" if "money" in (x.get("username") or "").lower() else "crazyfacts"): x.get("_id") or x.get("id") for x in yt}
    save(); print("::notice::Zernio accounts: " + ", ".join(f"{x['platform']}:{x.get('username') or x.get('displayName') or x.get('name')}" for x in cfg["accounts"]))
elif cmd == "playlist":   # a = "Title|Title2" (prefix "moneyatnight:" for Money at Night), b = shared description
    for t in sys.argv[2].split("|"):
        ch, _, title = t.rpartition(":") if ":" in t else ("crazyfacts", "", t)
        if title in cfg.get("playlists", {}): continue
        yt_account(ch)
        _, p = call("POST", f"/accounts/{yt_account(ch)}/youtube-playlists", {"title": title, "description": sys.argv[3] if len(sys.argv) > 3 else "", "privacy": "public"})
        cfg.setdefault("playlists", {})[title] = p["playlist"]["id"]; save(); print(f"::notice::playlist {title} = {p['playlist']['id']}")
elif cmd == "shorts":
    import datetime as dt
    # b = "YYYY-MM-DD" (3/day at 09/13/21, continuing after earlier posts) or "YYYY-MM-DD@11:00,15:00,19:00" (own slots, from that day)
    day, _, sl = sys.argv[3].partition("@"); vid, day = sys.argv[2], dt.date.fromisoformat(day); res = json.load(open(os.path.join(R, vid, "result.json")))
    v = json.load(open(os.path.join(D, "..", "assetedit", "videos", vid + ".json"))); ch = v.get("channel", "crazyfacts")
    meta = {x["id"]: x for x in json.load(open(os.path.join(D, "..", "assetedit", "videos", "shorts.json")))}
    done = res.setdefault("shorts_posted", {}); slots = sl.split(",") if sl else ["09:00", "13:00", "21:00"]; n = 0 if sl else len(done)
    plid = None if ch == "religion" else cfg.get("playlists", {}).get("Money Shorts" if ch == "moneyatnight" else "Psychology Shorts")
    for sid, url in sorted(res.get("shorts", {}).items()):
        if sid in done: continue
        yt_account(ch); m = meta.get(sid, {}); f = f"/tmp/{sid}.mp4"; urllib.request.urlretrieve(url, f)
        _, ps = call("POST", "/media/presign", {"filename": sid + ".mp4", "contentType": "video/mp4", "size": os.path.getsize(f)})
        urllib.request.urlopen(urllib.request.Request(ps["uploadUrl"], data=open(f, "rb").read(), method="PUT", headers={"Content-Type": "video/mp4"}), timeout=600).read()
        when = f"{day + dt.timedelta(days=n // len(slots))}T{slots[n % len(slots)]}"
        psd = {"title": (m.get("title") or v["title"])[:90] + " #shorts", "visibility": "public", "categoryId": "27", "madeForKids": False, "containsSyntheticMedia": True}
        if plid: psd["playlistId"] = plid
        body = {"content": f"{m.get('title', '')}\n\n{'Full documentary' if ch == 'religion' else 'Full calm 2.5-hour video'} on the channel: {v['title']}\n\n" + " ".join(m.get("tags", ["#shorts"])) + "\n\nNarration is AI-generated (synthetic voice).",
                "tags": [t.lstrip("#") for t in m.get("tags", [])], "mediaItems": [{"type": "video", "url": ps["publicUrl"]}],
                "platforms": [{"platform": "youtube", "accountId": yt_account(ch), "platformSpecificData": psd}], "scheduledFor": when, "timezone": "Europe/Amsterdam"}
        st, p = call("POST", "/posts", body); post = p.get("post", p)
        if st == 207 or post.get("status") == "failed": print(f"::warning::{sid} failed: {json.dumps(post)[:300]}"); continue
        done[sid] = {"zernio_id": post.get("_id"), "when": when}; n += 1
        json.dump(res, open(os.path.join(R, vid, "result.json"), "w"), indent=1); print(f"{sid} -> {when}")
    print(f"::notice::{vid}: {len(done)} Shorts scheduled")
elif cmd == "list":   # a = channel key (religion|crazyfacts|moneyatnight): recent posts of that account, to avoid duplicates after a timeout
    yt_account(sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else "crazyfacts"); st, p = call("GET", "/posts?limit=20"); ps = p.get("posts", p if isinstance(p, list) else [])
    print("::notice::raw " + json.dumps(p)[:1200].replace("\n", " "))
    for x in ps[:20]: print(f"::notice::{x.get('_id')} {x.get('status')} {x.get('scheduledFor')} {str(x.get('content', ''))[:50]!r}")
elif cmd == "delete":   # a = comma-separated Zernio post ids (duplicates created by a timed-out retry)
    yt_account(sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else "crazyfacts")
    for pid in sys.argv[2].split(","): st, _ = call("DELETE", f"/posts/{pid}"); print(f"::notice::deleted {pid}: {st}")
elif cmd == "status":  # a = comma-separated Zernio post ids
    for pid in sys.argv[2].split(","):
        st, p = call("GET", f"/posts/{pid}"); post = p.get("post", p)
        print(f"::notice::{pid} {post.get('status')} {post.get('scheduledFor')} " + json.dumps([{k: v for k, v in x.items() if k not in ("accountId", "_id")} for x in post.get("platforms", [])])[:700])
elif cmd == "reschedule":  # a = post id, b = local time YYYY-MM-DDTHH:MM
    st, p = call("PUT", f"/posts/{sys.argv[2]}", {"scheduledFor": sys.argv[3], "timezone": "Europe/Amsterdam"}); post = p.get("post", p)
    print(f"::notice::{st} {post.get('status')} {post.get('scheduledFor')} {json.dumps(p)[:300]}")
elif cmd == "post":
    vid, when = sys.argv[2], sys.argv[3]
    v = json.load(open(os.path.join(D, "..", "assetedit", "videos", vid + ".json"))); res = json.load(open(os.path.join(R, vid, "result.json")))
    yt_account(v.get("channel", "crazyfacts")); mp4 = sys.argv[4] if len(sys.argv) > 4 else f"/tmp/{vid}.mp4"   # the workflow downloads the release asset here
    _, ps = call("POST", "/media/presign", {"filename": vid + ".mp4", "contentType": "video/mp4", "size": os.path.getsize(mp4)})
    for attempt in (1, 2, 3):   # big files (1.4 GB at 1080p) can drop mid-upload: retry, and say why in the annotation
        try:
            up = urllib.request.Request(ps["uploadUrl"], data=open(mp4, "rb"), method="PUT",
                                        headers={"Content-Type": "video/mp4", "Content-Length": str(os.path.getsize(mp4))})
            urllib.request.urlopen(up, timeout=3600).read(); break
        except Exception as e:
            print(f"::warning::upload attempt {attempt} failed: {type(e).__name__} {str(e)[:300]}")
            if attempt == 3: sys.exit(f"::error::upload failed after 3 attempts: {type(e).__name__} {str(e)[:300]}")
    psd = {"title": v["title"][:100], "visibility": "public", "categoryId": "27", "madeForKids": False, "containsSyntheticMedia": True}
    pl = [cfg.get("playlists", {}).get(t) for t in v.get("playlists", [])]
    if pl and pl[0]: psd["playlistId"] = pl[0]
    body = {"content": open(os.path.join(R, vid, "description.txt")).read(), "tags": [t.lstrip("#") for t in v.get("tags", [])],
            "mediaItems": [{"type": "video", "url": ps["publicUrl"], "thumbnail": res["thumb"]}],
            "platforms": [{"platform": "youtube", "accountId": yt_account(v.get("channel", "crazyfacts")), "platformSpecificData": psd}],
            "scheduledFor": when, "timezone": "Europe/Amsterdam"}
    st, p = call("POST", "/posts", body, soft=True)
    if st is None:   # big video: Zernio creates the post but may not answer in time. NEVER post again: find it.
        import time; time.sleep(20); _, lp = call("GET", "/posts?limit=20"); key = body["content"][:40]
        found = [x for x in lp.get("posts", []) if str(x.get("content", "")).startswith(key) and x.get("status") in ("scheduled", "publishing", "published")]
        if not found: sys.exit("::error::Zernio gave no answer and no scheduled post was found; check manually before retrying")
        post = found[0]
    else:
        post = p.get("post", p)
        if st == 207 or post.get("status") == "failed": sys.exit(f"::error::Zernio post failed: {json.dumps(post)[:800]}")
    res.update(zernio_id=post.get("_id"), scheduled=when + "+02:00", route="zernio"); json.dump(res, open(os.path.join(R, vid, "result.json"), "w"), indent=1)
    print(f"::notice::{vid} scheduled via Zernio for {when}: post {post.get('_id')}")
