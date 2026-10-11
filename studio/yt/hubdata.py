"""Builds hub/data.json for the screen hub (GitHub Pages) from studio/yt/status.json + rendered/scheduled videos."""
import json, glob, os, re, datetime as dt
st = json.load(open("studio/yt/status.json"))
def secs(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or ""); return sum(int(x or 0) * k for x, k in zip(m.groups(), (3600, 60, 1))) if m else 0
vids = [dict(v, seconds=secs(v["duration"]), type="Short" if secs(v["duration"]) <= 180 or "#shorts" in v["title"].lower() else "Long") for v in st.get("videos", [])]
planned = []
for p in sorted(glob.glob("studio/renders/*/result.json")):
    r = json.load(open(p)); meta = f"studio/assetedit/videos/{r['id']}.json"
    t = json.load(open(meta))["title"] if os.path.exists(meta) else r["id"]
    planned.append({"id": r["id"], "title": t, "scheduled": r.get("scheduled"), "length": r.get("length"), "thumb": r.get("thumb")})
inprog = []
for m in sorted(glob.glob("studio/assetedit/videos/lf*.json")):
    if "_b" in m or "_p" in m: continue
    v = json.load(open(m))
    if "parts" in v and not os.path.exists(f"studio/renders/{v['id']}/result.json"):
        done = sum(os.path.exists(f"studio/assetedit/videos/{b}.json") for b in v["parts"]); inprog.append({"id": v["id"], "title": v["title"], "blocks": f"{done}/{len(v['parts'])}"})
# views history (every run; full detail for 48 h, hourly after that, max 60 days)
now = dt.datetime.now(dt.timezone.utc); hp = "hub/history.json"
hist = json.load(open(hp)) if os.path.exists(hp) else []
tot = sum(v["views"] for v in vids); tl = sum(v["views"] for v in vids if v["type"] == "Long")
ch0 = (st.get("channels") or [{}])[0]
hist.append({"t": now.strftime("%Y-%m-%dT%H:%MZ"), "views": tot, "long": tl, "short": tot - tl, "subs": ch0.get("subscriberCount", 0)})
keep, seen_h = [], set()
for h in hist:
    age = (now - dt.datetime.fromisoformat(h["t"].replace("Z", "+00:00"))).total_seconds() / 3600
    if age > 24 * 60: continue
    if age > 48:
        k = h["t"][:13]
        if k in seen_h: continue
        seen_h.add(k)
    keep.append(h)
json.dump(keep, open(hp, "w"))
day_ago = [h for h in keep if (now - dt.datetime.fromisoformat(h["t"].replace("Z", "+00:00"))).total_seconds() >= 24 * 3600]
views24 = tot - (day_ago[-1]["views"] if day_ago else keep[0]["views"])
subs24 = ch0.get("subscriberCount", 0) - (day_ago[-1]["subs"] if day_ago else keep[0]["subs"])
# schedule: next 7 days (Amsterdam), one long video per day
try:
    from zoneinfo import ZoneInfo; AMS = ZoneInfo("Europe/Amsterdam")
except Exception: AMS = dt.timezone(dt.timedelta(hours=2))
today = now.astimezone(AMS).date(); sched = []
by_day = {}
for p_ in planned:
    if p_.get("scheduled"): by_day.setdefault(p_["scheduled"][:10], p_)
pub_day = {}
for v in vids:
    if v["type"] == "Long": pub_day.setdefault(v["published"][:10], v)
nxt = inprog[0] if inprog else None
for i in range(7):
    d = today + dt.timedelta(days=i); k = d.isoformat()
    if k in by_day: e = {"status": "gepland", "title": by_day[k]["title"], "time": by_day[k]["scheduled"][11:16], "length": by_day[k].get("length")}
    elif k in pub_day: e = {"status": "online", "title": pub_day[k]["title"], "time": pub_day[k]["published"][11:16]}
    elif nxt and not any(x["status"] == "in de maak" for x in sched): e = {"status": "in de maak", "title": nxt["title"], "time": "17:00", "blocks": nxt["blocks"]}
    else: e = {"status": "open", "title": "nog leeg · de machine vult dit automatisch", "time": "17:00"}
    sched.append(dict(e, date=k))
month = today.strftime("%Y-%m"); used = len({p_["id"] for p_ in planned if (p_.get("scheduled") or "")[:7] == month}) + len([v for v in vids if v["published"][:7] == month])
# last result of every GitHub Actions workflow (status of the machine's parts)
wf = {}
tok = os.environ.get("GH_TOKEN")
if tok:
    import urllib.request
    for name in ("render-long.yml", "stats.yml", "trends.yml", "screenshots.yml", "youtube.yml", "upscale.yml", "ai.yml"):
        try:
            r = json.loads(urllib.request.urlopen(urllib.request.Request(f"https://api.github.com/repos/JonkoJeff/channel-media/actions/workflows/{name}/runs?per_page=1",
                headers={"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json"}), timeout=20).read())["workflow_runs"]
            if r: wf[name] = {"status": r[0]["status"], "conclusion": r[0]["conclusion"], "at": r[0]["created_at"][:16] + "Z"}
        except Exception as e: wf[name] = {"status": "unknown", "conclusion": None, "error": str(e)[:80]}
json.dump({"updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "checked_at": st.get("checked_at"), "channels": st.get("channels", []),
           "videos": vids, "planned": planned, "in_progress": inprog,
           "approved": os.path.exists("studio/yt/APPROVED"),
           "views24": views24, "subs24": subs24, "schedule": sched, "metricool_used": used, "workflows": wf}, open("hub/data.json", "w"), indent=1)
print("hub data:", len(vids), "videos,", len(planned), "planned")
