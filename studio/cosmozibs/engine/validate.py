"""Validates a Cosmozibs episode JSON against FORMAT.md. Usage: python3 validate.py ../episodes/czNN.json  (exit 1 on errors)"""
import json, sys, re
SCENES = {"title", "lineup", "crew", "map", "planet", "versus", "thermo", "pressure", "daybar", "quiz", "sunrise", "dive", "fill", "bignum", "wind",
          "sunlight", "glassrain", "blanket", "poof", "tides", "tilt", "car", "nomoon", "acid", "nightsky", "math", "voyager", "daynight", "speed", "pick", "signal", "lightcurve", "visitor", "blackhole"}
KINDS = {"mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune", "exo", "moon", "ganymede", "sun", "star", "blackhole", "oumuamua"}
WHO = {"cosmo", "zib", "bolt", "rocky", "tik"}; FX = {"flames", "shards", "streaks", "rocket"}
ep = json.load(open(sys.argv[1])); err = []; warn = []
def thumb(t, where):
    if not t: err.append(f"{where}: missing"); return
    if len(t.get("text", "").split()) > 3: err.append(f"{where}: text > 3 words")
    if t.get("planet") not in KINDS: err.append(f"{where}: planet {t.get('planet')}")
    if t.get("char") not in WHO: err.append(f"{where}: char {t.get('char')}")
    if not set(t.get("fx", [])) <= FX: err.append(f"{where}: fx {t.get('fx')}")
for k in ("id", "title", "sources", "segments"):
    if k not in ep: err.append(f"missing {k}")
thumb(ep.get("thumb"), "thumb")
if len(ep.get("title", "")) > 60: err.append("title > 60 chars")
words = 0; shorts = 0
for s in ep["segments"]:
    for i, l in enumerate(s["lines"]):
        words += len(l["say"].split())
        if l["who"] not in WHO: err.append(f"{s['id']}[{i}] who {l['who']}")
        if len(l["say"].split()) > 30: warn.append(f"{s['id']}[{i}] {len(l['say'].split())} words")
        if re.search(r"\d", l["say"]): err.append(f"{s['id']}[{i}] digits in say (write numbers as words)")
        sh = l.get("show")
        if sh:
            if sh.get("type") not in SCENES: err.append(f"{s['id']}[{i}] scene {sh.get('type')}")
            if sh.get("type") == "planet" and sh.get("kind") not in KINDS: err.append(f"{s['id']}[{i}] planet kind {sh.get('kind')}")
            if sh.get("type") == "quiz" and (len(sh.get("options", [])) != 3 or not l.get("pause")): err.append(f"{s['id']}[{i}] quiz needs 3 options + pause")
    if "short" in s:
        shorts += 1; sh = s["short"]; e = sh.get("end", -1)
        if not 0 < e < len(s["lines"]): err.append(f"{s['id']}: short.end {e}")
        if not s["lines"][0].get("show"): err.append(f"{s['id']}: line 0 needs a show")
        w = sum(len(l["say"].split()) for l in s["lines"][:e + 1])
        if not 60 <= w <= 150: warn.append(f"{s['id']}: Short has {w} words (aim 70-130)")
        if len(sh.get("title", "")) > 50: err.append(f"{s['id']}: short title > 50")
        thumb(sh.get("cover"), f"{s['id']}.cover")
if shorts != 4: err.append(f"{shorts} shorts (need 4)")
if not 1080 <= words <= 1250: warn.append(f"{words} words (aim ~1,150 for 8:05-8:20)")
for w in warn: print("WARN", w)
for e in err: print("ERROR", e)
print(f"{len(err)} errors, {len(warn)} warnings, {words} words"); sys.exit(1 if err else 0)
