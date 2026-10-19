"""Zernio route (https://zernio.com/api/v1), run in GitHub Actions with secret ZERNIO_API_KEY. Never commit the key.
  python3 studio/yt/zernio.py accounts                      -> lists connected accounts into studio/yt/zernio.json
  python3 studio/yt/zernio.py playlist "Title" "desc"       -> creates a public YouTube playlist, stores its id in zernio.json
  python3 studio/yt/zernio.py post lfNN 2026-10-13T17:00     -> uploads renders/lfNN video (presign), schedules it (Europe/Amsterdam)
  python3 studio/yt/zernio.py shorts lfNN 2026-10-13         -> schedules all Shorts of lfNN, 3 a day (09:00, 13:00, 21:00) from that date
The YouTube account id and playlist ids live in studio/yt/zernio.json (not secret)."""
import json, os, sys, urllib.request
TMP = os.environ.get("ZTMP", "/tmp")   # local runs (Windows): set ZTMP to a temp folder
API = "https://zernio.com/api/v1"; KEY = os.environ["ZERNIO_API_KEY"]; KEY2 = os.environ.get("ZERNIO_API_KEY_2", ""); KEY3 = os.environ.get("ZERNIO_API_KEY_3", "")  # KEY2 = second Zernio account (channel "religion")
D = os.path.dirname(os.path.abspath(__file__)); CFG = os.path.join(D, "zernio.json"); R = os.path.join(D, "..", "renders")
cfg = json.load(open(CFG)) if os.path.exists(CFG) else {}


import traceback
def _hook(t, e, tb): print("::error::" + " | ".join("".join(traceback.format_exception(t, e, tb)).splitlines())[-900:]); sys.exit(1)
sys.excepthook = _hook

_retry = [0]
def call(method, path, body=None, soft=False):
    body_ = body
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read()[:800]
        if e.code == 429 and _retry[0] < 40:   # rate limit 60/min: wait the advised time and retry (bulk rethumb)
            import re as _re, time as _t; _retry[0] += 1; _t.sleep(int((_re.search(rb"retryAfterSeconds\\?\"?:\s*(\d+)", body) or [0, b"30"])[1]) + 2); return call(method, path, body_, soft)
        sys.exit(f"::error::Zernio {method} {path}: {e.code} {body}")
    except Exception as e:
        if soft: print(f"::warning::{method} {path} no answer ({type(e).__name__}); checking whether the post exists"); return None, None
        sys.exit(f"::error::Zernio {method} {path}: {type(e).__name__} {str(e)[:300]}")


def save(): json.dump(cfg, open(CFG, "w"), indent=1)


def tz(ch):   # Cosmozibs is planned in US Eastern time (owner 19 Oct: American audience); the other channels in Amsterdam time
    return "America/New_York" if ch == "cosmozibs" else "Europe/Amsterdam"


def yt_account(ch="crazyfacts"):  # channel key: crazyfacts (default), moneyatnight or religion (own Zernio account / key)
    global KEY
    if ch == "religion2": KEY = KEY2; return "-"
    if ch == "cosmozibs" and KEY3: KEY = KEY3   # Cosmozibs (YouTube + TikTok) lives on its own Zernio account (owner 19 Oct)   # old key-2 account: only for delete/status of leftovers
    if ch == "religion" and cfg.get("religion_key") == 2: KEY = KEY2 or sys.exit("::error::ZERNIO_API_KEY_2 missing")   # default: religion = 2nd YouTube account of key 1 (owner, 13 Oct)
    return cfg.get("youtube", {}).get(ch) or sys.exit(f"::error::no YouTube account for {ch} in zernio.json; run 'accounts' after connecting it in Zernio")



def existing(prefix):   # FAILSAFE: a live (scheduled/publishing/published) post whose content starts with prefix, else None
    seen = set()
    for pg in range(1, 12):   # all pages: a post created during a timed-out request is not always on page 1 (rel22, 15 Oct)
        try: _, lp = call("GET", f"/posts?limit=100&page={pg}")
        except SystemExit: return None
        ps = [x for x in lp.get("posts", lp if isinstance(lp, list) else []) if x.get("_id") not in seen]
        if not ps: return None
        for x in ps:
            seen.add(x.get("_id"))
            if str(x.get("content", "")).startswith(prefix) and x.get("status") in ("scheduled", "publishing", "published", "processing", "pending"): return x
    return None



def host_thumb(url):   # repo is PRIVATE: Zernio/YouTube cannot fetch raw.githubusercontent.com. Upload the checked-out file to Zernio media instead and return its public URL.
    rel = url.split("/main/", 1)[-1] if "raw.githubusercontent.com" in url else None
    f = os.path.join(D, "..", "..", rel) if rel else None
    if not f or not os.path.exists(f): sys.exit(f"::error::thumbnail file not found for {url}")
    return host_file(f)


def cover(sid):   # Short cover painted by Codex (factory cf_cover / rel_cover), if there is one
    f = os.path.join(D, "..", "covers", sid + ".jpg"); return f if os.path.exists(f) else None


def host_file(f):
    ct = "image/png" if f.lower().endswith(".png") else "image/jpeg"
    _, ps = call("POST", "/media/presign", {"filename": os.path.basename(f), "contentType": ct, "size": os.path.getsize(f)})
    urllib.request.urlopen(urllib.request.Request(ps["uploadUrl"], data=open(f, "rb").read(), method="PUT", headers={"Content-Type": ct}), timeout=300).read()
    return ps["publicUrl"]


cmd = sys.argv[1]
if cmd == "accounts" and sys.argv[2:3] == ["3"]: KEY = KEY3 or sys.exit("::error::ZERNIO_API_KEY_3 missing")   # Cosmozibs account: then fall through to the normal listing
if cmd == "accounts" and sys.argv[2:3] == ["2"]:   # second Zernio account (Religion Unfolded)
    KEY = KEY2 or sys.exit("::error::ZERNIO_API_KEY_2 missing"); _, a = call("GET", "/accounts"); acc = a.get("accounts", a if isinstance(a, list) else [])
    yt = [x for x in acc if x.get("platform") == "youtube"]
    if yt: cfg.setdefault("youtube", {})["religion"] = yt[0].get("_id") or yt[0].get("id"); save()
    print(f"::notice::Zernio account 2: {len(acc)} accounts, {len(yt)} youtube")
elif cmd == "accounts":
    old_acc = cfg.get("accounts", []); _, a = call("GET", "/accounts"); acc = a.get("accounts", a if isinstance(a, list) else [])
    cfg["accounts"] = [{k: x.get(k) for k in ("_id", "id", "platform", "username", "displayName", "name")} for x in acc]
    yt = [x for x in cfg["accounts"] if x["platform"] == "youtube"]
    def chan(x):   # map an account to our channel key by its name (BAD was renamed from Crazy Facts, 19 Oct)
        n = f"{x.get('username') or ''} {x.get('displayName') or ''}".lower()
        return "crazyfacts" if ("crazy" in n or "brain" in n) else "cosmozibs" if "cosmo" in n else "religion" if ("belief" in n or "religion" in n) else None
    merge = sys.argv[2:3] == ["3"]   # key 3 (Cosmozibs): add its accounts, never drop the channels of key 1
    ytm = {chan(x): x.get("_id") or x.get("id") for x in yt if chan(x)}
    cfg["youtube"] = {**cfg.get("youtube", {}), **ytm} if merge else ytm
    tt = [x for x in cfg["accounts"] if x["platform"] == "tiktok" and chan(x)]
    if tt: cfg["tiktok"] = {**cfg.get("tiktok", {}), **{chan(x): x.get("_id") or x.get("id") for x in tt}}
    if merge: cfg["accounts_3"] = cfg["accounts"]; cfg["accounts"] = old_acc
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
    step = None
    offs = None
    if "T" in sys.argv[3] and "@" in sys.argv[3]:   # b = "YYYY-MM-DDTHH:MM@270,420,660,1020": Shorts at these minutes after the long video (Cosmozibs rhythm)
        st0, _, ol = sys.argv[3].partition("@"); start, offs = dt.datetime.fromisoformat(st0), [int(x) for x in ol.split(",")]; sys.argv[3] = st0[:10]
    elif "T" in sys.argv[3]:   # b = "YYYY-MM-DDTHH:MM+60": first Short at that time, then one every 60 minutes
        st0, _, mins = sys.argv[3].partition("+"); start, step = dt.datetime.fromisoformat(st0), int(mins or 60); sys.argv[3] = st0[:10]
    day, _, sl = sys.argv[3].partition("@"); vid, day = sys.argv[2], dt.date.fromisoformat(day); res = json.load(open(os.path.join(R, vid, "result.json")))
    v = json.load(open(os.path.join(D, "..", "assetedit", "videos", vid + ".json"))); ch = v.get("channel", "crazyfacts")
    meta = {x["id"]: x for x in json.load(open(os.path.join(D, "..", "assetedit", "videos", "shorts.json")))}
    done = res.setdefault("shorts_posted", {}); slots = sl.split(",") if sl else ["09:00", "12:00", "15:00", "20:00"]; n = 0 if sl else len(done)
    plid = None if ch == "religion" else cfg.get("playlists", {}).get("Cosmozibs Shorts") if ch == "cosmozibs" else cfg.get("playlists", {}).get("Money Shorts" if ch == "moneyatnight" else "Psychology Shorts")   # never another channel's playlist
    k = -1
    for sid, url in sorted(res.get("shorts", {}).items()):
        if sid in done: continue
        k += 1
        yt_account(ch); m = meta.get(sid, {}); f = os.path.join(TMP, f"{sid}.mp4")
        pre = f"{m.get('title', '')}\n\n"[:40]
        ex = existing(pre) if m.get("title") else None   # FAILSAFE: this Short already exists on Zernio -> adopt, never post twice
        if ex:
            done[sid] = {"zernio_id": ex.get("_id"), "when": str(ex.get("scheduledFor"))}; json.dump(res, open(os.path.join(R, vid, "result.json"), "w"), indent=1); print(f"{sid} already on Zernio, adopted"); continue; os.path.exists(f) or urllib.request.urlretrieve(url, f)
        th = None   # Short thumbnail = the Codex cover, else a frame ~1.5 s in (hook text is on screen), hosted on Zernio media; failure here must never block the post
        try:
            if ch == "religion": raise RuntimeError("BTT: no thumbnails (owner 19 Oct)")
            jf = cover(sid)
            if not jf:
                import subprocess; jf = os.path.join(TMP, f"{sid}.jpg")
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "1.5", "-i", f, "-frames:v", "1", "-q:v", "2", jf], check=True, timeout=60)
            _, tp = call("POST", "/media/presign", {"filename": sid + ".jpg", "contentType": "image/jpeg", "size": os.path.getsize(jf)})
            urllib.request.urlopen(urllib.request.Request(tp["uploadUrl"], data=open(jf, "rb").read(), method="PUT", headers={"Content-Type": "image/jpeg"}), timeout=120).read(); th = tp["publicUrl"]
        except BaseException as e: print(f"::notice::{sid}: no thumbnail ({type(e).__name__})")
        _, ps = call("POST", "/media/presign", {"filename": sid + ".mp4", "contentType": "video/mp4", "size": os.path.getsize(f)})
        urllib.request.urlopen(urllib.request.Request(ps["uploadUrl"], data=open(f, "rb").read(), method="PUT", headers={"Content-Type": "video/mp4"}), timeout=600).read()
        if offs and k >= len(offs): print(f"::notice::{sid}: no slot left in this run"); continue
        when = (start + dt.timedelta(minutes=offs[k])).strftime("%Y-%m-%dT%H:%M") if offs else (start + dt.timedelta(minutes=step * k)).strftime("%Y-%m-%dT%H:%M") if step else f"{day + dt.timedelta(days=n // len(slots))}T{slots[n % len(slots)]}"
        psd = {"title": (m.get("title") or v["title"])[:90] + " #shorts", "visibility": "public", "categoryId": "27", "madeForKids": False, "containsSyntheticMedia": True}
        if plid: psd["playlistId"] = plid
        body = {"content": f"{m.get('title', '')}\n\n{'Full documentary' if ch == 'religion' else 'Full episode' if ch == 'cosmozibs' else 'Full calm 2.5-hour video'} on the channel: {v['title']}\n\n" + " ".join(m.get("tags", ["#shorts"])) + "\n\nNarration is AI-generated (synthetic voice).",
                "tags": [t.lstrip("#") for t in m.get("tags", [])], "mediaItems": [{"type": "video", "url": ps["publicUrl"], **({"thumbnail": th} if th else {})}],
                "platforms": [{"platform": "youtube", "accountId": yt_account(ch), "platformSpecificData": psd}], "scheduledFor": when, "timezone": tz(ch)}
        tt = cfg.get("tiktok", {}).get(ch)   # same Short also to TikTok (owner 19 Oct, Cosmozibs): only for channels with a TikTok account in zernio.json
        if tt:
            body["platforms"].append({"platform": "tiktok", "accountId": tt})
            body["tiktokSettings"] = {"privacy_level": "PUBLIC_TO_EVERYONE", "allow_comment": True, "allow_duet": True, "allow_stitch": True, "commercial_content_type": "none",
                                      "content_preview_confirmed": True, "express_consent_given": True, "media_type": "video", "auto_add_music": False, "video_made_with_ai": True}
        st, p = call("POST", "/posts", body, soft=True)
        if st is None:   # no answer: the post may exist. Look, never re-post
            import time; time.sleep(20); ex = existing(body["content"][:40])
            if not ex: sys.exit(f"::error::{sid}: no answer and no post found; check Zernio before retrying")
            p = ex
        post = p.get("post", p)
        if st == 207 or post.get("status") == "failed": print(f"::warning::{sid} failed: {json.dumps(post)[:300]}"); continue
        done[sid] = {"zernio_id": post.get("_id"), "when": when}; n += 1
        json.dump(res, open(os.path.join(R, vid, "result.json"), "w"), indent=1); print(f"{sid} -> {when}")
    print(f"::notice::{vid}: {len(done)} Shorts scheduled")
elif cmd == "list":   # a = channel key (religion|crazyfacts|moneyatnight): recent posts of that account, to avoid duplicates after a timeout
    yt_account(sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else "crazyfacts"); st, p = call("GET", "/posts?limit=100"); ps = p.get("posts", p if isinstance(p, list) else [])
    seen_ = {x.get("_id") for x in ps}
    for pg in range(2, 12):   # all pages: the account may have more than 100 posts
        _, lp = call("GET", f"/posts?limit=100&page={pg}"); more = [x for x in lp.get("posts", []) if x.get("_id") not in seen_]
        if not more: break
        ps += more; seen_ |= {x.get("_id") for x in more}
    print("::notice::raw " + json.dumps(p)[:1200].replace("\n", " "))
    for x in ps[:100]: print(f"::notice::{x.get('_id')} acc={str([q.get('accountId') for q in x.get('platforms', [])])[-9:]} {x.get('status')} {x.get('scheduledFor')} {str(x.get('content', ''))[:50]!r}")
    json.dump([{"id": x.get("_id"), "account": str([q.get("accountId") for q in x.get("platforms", [])]), "status": x.get("status"), "when": x.get("scheduledFor"), "text": str(x.get("content", ""))[:80]} for x in ps],
              open(os.path.join(D, f"list_{sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else 'crazyfacts'}.json"), "w"), indent=1)
elif cmd == "delete":   # a = comma-separated Zernio post ids (duplicates created by a timed-out retry)
    yt_account(sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else "crazyfacts")
    for pid in sys.argv[2].split(","):
        try: st, _ = call("DELETE", f"/posts/{pid}"); print(f"::notice::deleted {pid}: {st}")
        except SystemExit as e: print(f"::notice::skip {pid}: {str(e)[:90]}")
elif cmd == "status":  # a = comma-separated Zernio post ids, b = channel key (religion uses account 2)
    yt_account(sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else "crazyfacts")
    for pid in sys.argv[2].split(","):
        st, p = call("GET", f"/posts/{pid}"); post = p.get("post", p)
        print(f"::notice::{pid} {post.get('status')} {post.get('scheduledFor')} " + json.dumps([{k: v for k, v in x.items() if k not in ("accountId", "_id")} for x in post.get("platforms", [])])[:700])
elif cmd == "reslot":   # a = first day YYYY-MM-DD, b = slots "15:00,18:00,21:00,23:30", c = channel prefix: lf (Brain After Dark, default) | rel (Belief Through Time). Re-times every still-pending Short of that channel so exactly len(slots) go out per day, in the existing order
    import datetime as dt, glob, re
    day0 = dt.date.fromisoformat(sys.argv[2]); slots = (sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else "15:00,18:00,21:00,23:30").split(",")
    pre = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else "lf"; ch = "religion" if pre.startswith("rel") else "crazyfacts"
    items = []
    lost = [(f, sid) for f in glob.glob(os.path.join(R, pre + "*", "result.json")) for sid, d in json.load(open(f)).get("shorts_posted", {}).items() if not d.get("zernio_id")]
    if lost:   # earlier runs lost some ids to a push race: recover them from Zernio by title (page through /posts)
        yt_account(ch); meta = {x["id"]: x for x in json.load(open(os.path.join(D, "..", "assetedit", "videos", "shorts.json")))}; seen = {}; first = None
        for f, _ in lost: meta.update({k: v for k, v in json.load(open(f)).get("shorts_meta", {}).items()})   # BTT Short titles live in result.json
        for pg in range(1, 8):
            _, lp = call("GET", f"/posts?limit=100&page={pg}"); ps_ = lp.get("posts", [])
            if not ps_ or ps_[0].get("_id") == first: break
            first = ps_[0].get("_id")
            for x in ps_:
                if x.get("status") == "scheduled": seen.setdefault(str(x.get("content", "")).split("\n\n")[0], x.get("_id"))
        for f, sid in lost:
            t = meta.get(sid, {}).get("title"); r = json.load(open(f))
            if t and t in seen: r["shorts_posted"][sid]["zernio_id"] = seen[t]; r["shorts_posted"][sid].pop("note", None); json.dump(r, open(f, "w"), indent=1); print(f"::notice::recovered id of {sid}")
    for f in sorted(glob.glob(os.path.join(R, pre + "*", "result.json"))):
        r = json.load(open(f))
        for sid, d in r.get("shorts_posted", {}).items():
            if d.get("zernio_id") and d["when"][:10] >= str(day0): items.append((d["when"], f, sid))
    NEW_VOICE_FROM = 13   # Brain After Dark: lf13+ carry the new warm voice (15 Oct 10:59); lf07-lf12 still have the old one -> new-voice Shorts go out first (owner 18 Oct)
    items.sort(key=lambda t: (0 if pre == "lf" and int((re.search(r"lf(\d+)", t[1]) or [0, 0])[1]) >= NEW_VOICE_FROM else 1, t[0])); yt_account(ch); n = 0; moved = 0
    for _, f, sid in items:
        when = f"{day0 + dt.timedelta(days=n // len(slots))}T{slots[n % len(slots)]}"; n += 1
        r = json.load(open(f)); d = r["shorts_posted"][sid]
        if d["when"] == when: continue
        import time; ok = False
        for tr in (1, 2, 3, 4):   # Zernio rate limit (429): wait and retry; other errors: skip this one
            try: call("PUT", f"/posts/{d['zernio_id']}", {"scheduledFor": when, "timezone": "Europe/Amsterdam"}); ok = True; time.sleep(2); break
            except SystemExit as e:
                if "429" in str(e) and tr < 4: time.sleep(45); continue
                print(f"::notice::skip {sid}: {str(e)[:80]}"); break
        if not ok: continue
        d["when"] = when; json.dump(r, open(f, "w"), indent=1); moved += 1
    print(f"::notice::reslot {pre}: {len(items)} pending Shorts, {moved} moved, {len(slots)}/day from {day0} until {day0 + dt.timedelta(days=(n - 1) // len(slots))}")
elif cmd == "rethumb":   # a = comma-separated video ids (lf09,rel01): re-attach the thumbnail (hosted on Zernio) to the existing scheduled post. Published posts cannot be changed: set the thumbnail in YouTube Studio.
    for vid in sys.argv[2].split(","):
        v = json.load(open(os.path.join(D, "..", "assetedit", "videos", vid + ".json"))); res = json.load(open(os.path.join(R, vid, "result.json"))); yt_account(v.get("channel", "crazyfacts"))
        if v.get("channel") == "religion": print(f"::notice::{vid}: BTT has no thumbnails (owner 19 Oct), skipped"); continue
        # the long video's thumbnail, then the Codex cover of every Short that has one (studio/covers/<short id>.jpg)
        # Belief Through Time only: a Short whose Codex cover failed the image gate (file removed) gets its drawn cover back = the frame at 1.5 s of the rendered Short (cover.py)
        def drawn(s):
            import subprocess; mp, jf = os.path.join(TMP, s + ".mp4"), os.path.join(TMP, s + "_drawn.jpg")
            os.path.exists(mp) or urllib.request.urlretrieve(res["shorts"][s], mp)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "1.5", "-i", mp, "-frames:v", "1", "-q:v", "2", jf], check=True, timeout=120); return host_file(jf)
        rel = v.get("channel") == "religion"
        for key, pid, th in [(vid, res.get("zernio_id"), lambda: host_thumb(res["thumb"]))] + [(s, x.get("zernio_id"), (lambda s=s: host_file(cover(s))) if cover(s) else (lambda s=s: drawn(s))) for s, x in sorted(res.get("shorts_posted", {}).items()) if cover(s) or (rel and s in res.get("shorts", {}))]:
            if not pid: continue
            _, p = call("GET", f"/posts/{pid}"); post = p.get("post", p)
            if post.get("status") != "scheduled": print(f"::notice::{key}: status {post.get('status')}, not changeable: set the thumbnail in YouTube Studio"); continue
            try: url = th()
            except BaseException as e: print(f"::warning::{key}: no thumbnail file ({type(e).__name__}), post unchanged"); continue
            mi = [dict(x) for x in post.get("mediaItems", [])]
            for x in mi: x.pop("_id", None); x["thumbnail"] = url if x.get("type") == "video" else x.get("thumbnail")
            try: call("PUT", f"/posts/{pid}", {"mediaItems": mi}); print(f"::notice::{key}: thumbnail re-attached")
            except SystemExit as e: print(f"::notice::{key}: {str(e)[:200]}")
elif cmd == "reschedule":  # a = post id, b = local time YYYY-MM-DDTHH:MM, c = channel (cosmozibs: its own key + US Eastern time)
    ch = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else "crazyfacts"; yt_account(ch)
    st, p = call("PUT", f"/posts/{sys.argv[2]}", {"scheduledFor": sys.argv[3], "timezone": tz(ch)}); post = p.get("post", p)
    print(f"::notice::{st} {post.get('status')} {post.get('scheduledFor')} {json.dumps(p)[:300]}")
elif cmd == "post":
    vid, when = sys.argv[2], sys.argv[3]
    v = json.load(open(os.path.join(D, "..", "assetedit", "videos", vid + ".json"))); res = json.load(open(os.path.join(R, vid, "result.json")))
    if res.get("zernio_id"):   # FAILSAFE 1: result.json says it is already posted -> never post again (delete the post and clear zernio_id on purpose to re-post)
        print(f"::notice::{vid} already posted ({res['zernio_id']}), nothing to do"); sys.exit(0)
    yt_account(v.get("channel", "crazyfacts")); mp4 = (sys.argv[4] if len(sys.argv) > 4 else "") or os.path.join(TMP, f"{vid}.mp4")   # the workflow downloads the release asset here
    ex = existing(open(os.path.join(R, vid, "description.txt")).read()[:40])   # FAILSAFE 2: Zernio already has it (earlier run died after posting) -> adopt it
    if ex:
        res.update(zernio_id=ex.get("_id"), scheduled=str(ex.get("scheduledFor")), route="zernio"); json.dump(res, open(os.path.join(R, vid, "result.json"), "w"), indent=1)
        print(f"::notice::{vid} already exists on Zernio ({ex.get('_id')}), adopted, not posted again"); sys.exit(0)
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
            "mediaItems": [{"type": "video", "url": ps["publicUrl"], **({} if v.get("channel") == "religion" else {"thumbnail": host_thumb(res["thumb"])})}],   # BTT: no thumbnail (owner 19 Oct)
            "platforms": [{"platform": "youtube", "accountId": yt_account(v.get("channel", "crazyfacts")), "platformSpecificData": psd}],
            "scheduledFor": when, "timezone": tz(v.get("channel", "crazyfacts"))}
    st, p = call("POST", "/posts", body, soft=True)
    if st is None:   # big video: Zernio creates the post but may not answer in time. NEVER post again: find it.
        import time; time.sleep(20); _, lp = call("GET", "/posts?limit=100"); key = body["content"][:40]
        found = [x for x in lp.get("posts", []) if str(x.get("content", "")).startswith(key) and x.get("status") in ("scheduled", "publishing", "published")]
        if not found: sys.exit("::error::Zernio gave no answer and no scheduled post was found; check manually before retrying")
        post = found[0]
    else:
        post = p.get("post", p)
        if st == 207 or post.get("status") == "failed": sys.exit(f"::error::Zernio post failed: {json.dumps(post)[:800]}")
    res.update(zernio_id=post.get("_id"), scheduled=f"{when} {tz(v.get('channel', 'crazyfacts'))}", route="zernio"); json.dump(res, open(os.path.join(R, vid, "result.json"), "w"), indent=1)
    print(f"::notice::{vid} scheduled via Zernio for {when}: post {post.get('_id')}")
