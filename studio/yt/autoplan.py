"""Auto-plan: schedule every rendered-but-unscheduled video (lf = Brain After Dark, rel = Belief Through Time) on Zernio. No chat needed.
Long video: 20:00 on the first free day after the last scheduled long video (at most 14 days ahead). Shorts 15:00/18:00/21:00/23:30:
BTT on the same days as the long video, BAD after the last scheduled Short (at most 35 days ahead). Posting itself stays in zernio.py (failsafes: no double upload).
python3 studio/yt/autoplan.py          -> print the plan
python3 studio/yt/autoplan.py --run    -> execute it (needs ZERNIO_API_KEY)"""
import datetime as dt, glob, json, os, re, subprocess, sys
D = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(D, "..", "renders"); TMP = os.environ.get("ZTMP", "/tmp"); SLOTS = "15:00,18:00,21:00,23:30"
today = dt.datetime.now(dt.timezone(dt.timedelta(hours=2 if dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) < dt.datetime(2026, 10, 25, 1) else 1))).date()
res = {}
for f in glob.glob(os.path.join(R, "*", "result.json")):
    r = json.load(open(f)); m = re.fullmatch(r"(lf|rel)(\d+)", r.get("id", ""))
    if m: res[r["id"]] = (m.group(1), int(m.group(2)), r)
num = lambda i: res[i][1]
plan = []
for pre in ("lf", "rel"):
    mine = {i: x for i, x in res.items() if x[0] == pre}
    longs = [dt.date.fromisoformat(r["scheduled"][:10]) for _, _, r in mine.values() if r.get("scheduled")]
    shorts = [dt.date.fromisoformat(s["when"][:10]) for _, _, r in mine.values() for s in r.get("shorts_posted", {}).values()]
    nxt_long = max(longs + [today]) + dt.timedelta(days=1); nxt_short = max(shorts + [today]) + dt.timedelta(days=1)
    for i in sorted(mine, key=num):
        r = mine[i][2]
        if not r.get("video"): continue
        todo_long = not r.get("zernio_id") and not r.get("scheduled"); todo_sh = bool(r.get("shorts")) and len(r.get("shorts_posted", {})) < len(r["shorts"]) and (r.get("zernio_id") or r.get("scheduled") or todo_long)
        if not (todo_long or todo_sh): continue
        if todo_long:
            if nxt_long > today + dt.timedelta(days=14): print(f"{i}: long video buffer full (next free {nxt_long})"); continue
            lday = nxt_long; nxt_long += dt.timedelta(days=1)
        else: lday = dt.date.fromisoformat(r["scheduled"][:10])
        if todo_sh:
            sday = lday if pre == "rel" else nxt_short
            if sday > today + dt.timedelta(days=35): print(f"{i}: Shorts buffer full (next free {sday})"); todo_sh = False
            elif pre == "lf": nxt_short = sday + dt.timedelta(days=-(-len(r["shorts"]) // 4))
        plan.append((i, f"{lday}T20:00" if todo_long else None, f"{sday}@{SLOTS}" if todo_sh else None))
for i, l, s in plan: print(f"{i}: long {l or 'already'}  shorts {s or 'already/none'}")
if not plan: print("nothing to plan")
if "--run" in sys.argv:
    fail = 0
    for i, l, s in plan:
        if l:
            subprocess.run(["gh", "release", "download", i, "--repo", os.environ.get("GITHUB_REPOSITORY", "JonkoJeff/channel-media"), "--pattern", "*.mp4", "--dir", TMP, "--clobber"], check=False)
            fail += subprocess.run([sys.executable, os.path.join(D, "zernio.py"), "post", i, l, os.path.join(TMP, i + ".mp4")]).returncode != 0
        if s: fail += subprocess.run([sys.executable, os.path.join(D, "zernio.py"), "shorts", i, s]).returncode != 0
    sys.exit(1 if fail else 0)
