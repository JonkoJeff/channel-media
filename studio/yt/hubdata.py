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
json.dump({"updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "checked_at": st.get("checked_at"), "channels": st.get("channels", []),
           "videos": vids, "planned": planned, "in_progress": inprog,
           "approved": os.path.exists("studio/yt/APPROVED")}, open("hub/data.json", "w"), indent=1)
print("hub data:", len(vids), "videos,", len(planned), "planned")
