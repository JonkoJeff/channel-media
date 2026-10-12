"""Belief Through Time / Religion Unfolded: script file (stories/FORMAT.md) -> 1080p documentary + 4 Shorts. No tokens: runs in GitHub Actions.
python3 build.py <episode file> <id> [--test]   -> out/<id>.mp4, out/<id>_s1..4.mp4, out/result files (see publish step in religion.yml)
Images: ONLY public-domain / CC0 (Wikimedia Commons, The Met Open Access), searched from the VISUAL line; fallback = navy/gold text card.
Voice: Kokoro bm_lewis 0.92 (same for every episode). Ken-Burns stills, dip fades, chapter cards, loudnorm -16 LUFS."""
import json, os, re, subprocess, sys, hashlib, time, urllib.request, urllib.parse, html, wave, glob, textwrap
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(H, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "studio", "voice")); import kokoro_tts as K
src, vid = sys.argv[1], sys.argv[2]; OUT = os.path.join(ROOT, "out"); W = os.path.join(OUT, "work"); os.makedirs(W, exist_ok=True)
UA = {"User-Agent": "ReligionUnfoldedBot/1.0 (https://github.com/JonkoJeff/channel-media)"}; FPS = 25
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"; GOLD = "0xE8C36A"

def sh(*a): subprocess.run(a, check=True)
def get(url):
    for i in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except Exception as e: time.sleep(2 + 3 * i); err = e
    raise err
def secs(t):
    p = [int(x) for x in t.split(":")]; return sum(v * 60 ** i for i, v in enumerate(reversed(p)))

# ---------- parse ----------
txt = open(src, encoding="utf-8").read().replace("\r", ""); head, _, body = txt.partition("\n---")
hd, key = {}, None
for ln in head.splitlines():
    m = re.match(r"(TITLE|DESC|TAGS|SOURCES|SHORTS):\s*(.*)", ln)
    if m: key = m[1]; hd[key] = m[2]
    elif key and ln.strip(): hd[key] += "\n" + ln.strip()
shorts = []
for ln in hd.get("SHORTS", "").splitlines():
    m = re.match(r"\s*([\d:]+)\s*-\s*([\d:]+)\s*\|\s*(.+)", ln)
    if m: shorts.append((secs(m[1]), secs(m[2]), m[3].strip()))
scenes, chap = [], None
parts = re.split(r"(?m)^\s*\[([\d:]+)\]", body)
for i in range(1, len(parts), 2):
    t, b = parts[i], parts[i + 1]; b = re.sub(r"(?m)^\s*CHAPTER:.*$", "", b)
    n = re.search(r"NARRATION:\s*(.*?)(?=^\s*VISUAL:|^\s*SOURCE:|\Z)", b, re.S | re.M); v = re.search(r"VISUAL:\s*(.*?)(?=^\s*SOURCE:|\Z)", b, re.S | re.M); s = re.search(r"SOURCE:\s*(\S+)", b)
    if n and n[1].strip(): scenes.append(dict(t=secs(t), say=" ".join(n[1].split()), vis=" ".join(v[1].split()) if v else "", src=(s[1].lower() if s else "wikimedia"), chap=chap))
# CHAPTER lines trail the previous block: re-attach (chap computed above belongs to the next scene)
pend = (re.findall(r"(?m)^\s*CHAPTER:\s*(.+)$", parts[0]) or [None])[-1]; fixed = []
for i in range(1, len(parts), 2):
    b = parts[i + 1]
    fixed.append(pend); pend = (re.findall(r"(?m)^\s*CHAPTER:\s*(.+)$", b) or [None])[-1]
for sc, c in zip(scenes, fixed): sc["chap"] = c.strip() if c else None
assert scenes, "no scenes parsed"; print(f"{len(scenes)} scenes, {sum(len(s['say'].split()) for s in scenes)} words")

# ---------- images (public domain / CC0 only) ----------
lic_ok = re.compile(r"^(public domain|pd[- ]|cc0|cc-0)", re.I); ATTR = []
def wm(q):
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(dict(action="query", generator="search", gsrsearch=q + " filetype:bitmap", gsrnamespace=6, gsrlimit=15, prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=2400, format="json"))
    r = json.loads(get(u)).get("query", {}).get("pages", {}); out = []
    for p in sorted(r.values(), key=lambda p: p.get("index", 99)):
        ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {}); lic = md.get("LicenseShortName", {}).get("value", "")
        if lic_ok.match(lic) and ii.get("width", 0) >= 1200 and ii.get("thumburl") and not re.search(r"(?i)\.(svg|tif|gif)|logo|flag|coat of arms", p["title"]):
            a = re.sub("<[^>]+>", "", html.unescape(md.get("Artist", {}).get("value", "")))[:80]
            out.append((ii["thumburl"], f"{p['title'][5:]} - {a or 'unknown'} - {lic} - {ii.get('descriptionurl')}"))
    return out
def met(q):
    ids = (json.loads(get("https://collectionapi.metmuseum.org/public/collection/v1/search?hasImages=true&isPublicDomain=true&q=" + urllib.parse.quote(q))).get("objectIDs") or [])[:6]; out = []
    for i in ids:
        o = json.loads(get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{i}"))
        if o.get("isPublicDomain") and o.get("primaryImage"): out.append((o["primaryImage"], f"{o.get('title')} - {o.get('artistDisplayName') or 'unknown'} - The Met Open Access (CC0) - {o.get('objectURL')}"))
    return out
def relevant(q, title):   # the file title must share a meaningful word with the VISUAL line, else the match is random
    ws = [w for w in re.findall(r"[a-z]{4,}", q.lower()) if w not in {"with", "from", "that", "this", "ancient", "painting", "map", "scene", "image", "photo", "artwork", "view"}]
    return not ws or any(w in title.lower() for w in ws)
BLOCK = re.compile(r"(?i)\b(ski|skier|skiing|snowboard|building|skyscraper|office|hospital|airport|airplane|aircraft|biplane|car|truck|football|soccer|tourist|crowd|portrait|selfie|dog|cat|logo|flag|bikini|wedding|concert|stadium|shop|street|city|bridge|graffiti|advert|seedling|mango|tupperware|box|container|jar|bottle|plastic|pot)\b")
def nasa(q):
    r = json.loads(get("https://images-api.nasa.gov/search?media_type=image&q=" + urllib.parse.quote(q))).get("collection", {}).get("items", [])[:8]; out = []
    for it in r:
        d = (it.get("data") or [{}])[0]; nid = d.get("nasa_id", "")
        if nid and not re.search(r"(?i)logo|patch|crew|portrait|astronaut|launch|rocket|technician|facility", d.get("title", "")):
            out.append((f"https://images-assets.nasa.gov/image/{nid}/{urllib.parse.quote(nid)}~large.jpg", f"{d.get('title', nid)} - NASA - Public domain (NASA media usage guidelines) - https://images.nasa.gov/details/{nid}"))
    return out
def wmq(q, cat):
    return wm((q + f' incategory:"{cat}"') if cat else q)
SPACE = re.compile(r"(?i)\b(star|stars|night sky|galaxy|nebula|planet|earth|sun|moon|cosmos|universe|space|milky|orbit|eclipse|smoke|mist cloud)\b")
CACHE = {}; POOL = []
def find(sc):
    v = re.split(r"[;.]", sc["vis"])[0]; v = re.sub(r"(?i)\b(slow|slowly|gentle|gently|quiet|soft|wide|close|forward|drift|pan|zoom|no people|restrained|abstract|illustration|unlabelled|empty|unoccupied|contemporary|text card)\b", " ", v)
    q = " ".join(re.sub(r"[^\w ]", " ", v).split()[:8])
    if sc["src"] in ("text-card", "map") or re.match(r"(?i)(minimal )?text card|three-column|four-window|six |seven |card", sc["vis"]) or not q: return []
    if q in CACHE: return CACHE[q]
    q3 = " ".join(q.split()[:3]); res = []
    attempts = [(nasa, q), (nasa, q3)] if SPACE.search(q) else []
    attempts += [(met, q)] if sc["src"] == "met" else []
    attempts += [(lambda x: wmq(x, "Featured pictures on Wikimedia Commons"), q), (lambda x: wmq(x, "Quality images"), q), (lambda x: wmq(x, "Featured pictures on Wikimedia Commons"), q3), (lambda x: wmq(x, "Quality images"), q3), (wm, q3)]
    for f, qq in attempts:
        try: res += [r for r in f(qq) if relevant(qq, r[1].split(" - ")[0]) or f is nasa and True]
        except Exception as e: print("search fail", qq, str(e)[:80])
        res = [r for r in res if not BLOCK.search(r[1].split(" - ")[0])]
        if len(res) >= 3: break
    got = []
    for url, at in res[:6]:
        fn = os.path.join(W, hashlib.sha1(url.encode()).hexdigest()[:12] + ".jpg")
        try:
            if not os.path.exists(fn): open(fn, "wb").write(get(url)); time.sleep(0.4)
            im = Image.open(fn); im.verify()
            if Image.open(fn).size[0] >= 1300: got.append(fn); ATTR.append(at); POOL.append(fn)
        except Exception as e: print("img fail", str(e)[:80])
        if len(got) >= 3: break
    CACHE[q] = got; return got
def card(text, fn):
    im = Image.new("RGB", (1920, 1080)); d = ImageDraw.Draw(im)
    for y in range(1080): d.line([(0, y), (1920, y)], fill=(6, 11 + y // 40, 28 + y // 14))
    rng = np.random.default_rng(abs(hash(text)) % 2**32)
    for _ in range(140): x, y = int(rng.integers(0, 1920)), int(rng.integers(0, 1080)); r = int(rng.integers(1, 3)); d.ellipse([x, y, x + r, y + r], fill=(200, 190, 150))
    d.rectangle([140, 120, 1780, 960], outline=(168, 140, 70), width=3); d.rectangle([158, 138, 1762, 942], outline=(110, 92, 50), width=1)
    lines = [l for p in re.split(r"\s*/\s*| — ", text or "") for l in textwrap.wrap(p.strip(), 38)][:7]
    f = ImageFont.truetype(FONT, 62 if len(lines) <= 4 else 48); y = 540 - 40 * len(lines)
    for ln in lines: d.text((960, y), ln, font=f, fill=(232, 195, 106), anchor="mm"); y += 82
    im.save(fn, quality=92)

# ---------- voice ----------
def speak(s):
    parts, out = re.split(r"(?<=[.!?])\s+", s), []
    for p in parts:
        if p.strip(): out += [K.speak(p.strip()[:420], "bm_lewis", 0.92), np.zeros(int(24000 * 0.32), np.float32)]
    return np.concatenate(out) if out else np.zeros(2400, np.float32)
audio, jobs, off = [], [], 0.0
for i, sc in enumerate(scenes):
    a = speak(sc["say"]); pad = 0.9 if i + 1 < len(scenes) else 3.5; a = np.concatenate([a, np.zeros(int(24000 * pad), np.float32)])
    nf = int(np.ceil(len(a) / 24000 * FPS)); a = np.concatenate([a, np.zeros(int(nf / FPS * 24000) - len(a) + 1, np.float32)])[:int(nf / FPS * 24000)]
    sc.update(frames=nf, start=off, dur=nf / FPS); off += nf / FPS; audio.append(a)
    if i % 40 == 0: print("voice", i, "/", len(scenes), flush=True)
K.save(np.concatenate(audio), os.path.join(W, "voice.wav")); print(f"voice done: {off / 60:.1f} min")

# ---------- video shots ----------
def shot(args):
    k, img, nf, style, label = args; fn = os.path.join(W, f"s{k:05d}.mp4"); n = max(nf, 2); d = n / FPS
    z = {0: f"z='1+0.14*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'", 1: f"z='1.14-0.14*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'",
         2: f"z=1.16:x='(iw-iw/zoom)*on/{n}':y='ih/2-ih/zoom/2'", 3: f"z=1.16:x='(iw-iw/zoom)*(1-on/{n})':y='ih/2-ih/zoom/2'"}[style % 4]
    vf = f"scale=2400:1350:force_original_aspect_ratio=increase,crop=2400:1350,zoompan={z}:d={n}:s=1920x1080:fps={FPS},eq=gamma=1.2:saturation=1.05,vignette=PI/6,fade=t=in:st=0:d=0.45,fade=t=out:st={d - 0.45:.2f}:d=0.45"
    if label:
        tf = fn[:-4] + ".txt"; open(tf, "w").write(label)
        vf += f",drawtext=fontfile={FONT}:textfile={tf}:fontcolor={GOLD}:fontsize=62:x=(w-text_w)/2:y=h-170:shadowcolor=black:shadowx=3:shadowy=3:enable='lt(t,4)'"
    sh("ffmpeg", "-y", "-loglevel", "error", "-threads", "1", "-i", img, "-vf", vf + ",format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-maxrate", "3500k", "-bufsize", "7000k", "-r", str(FPS), "-frames:v", str(n), fn)
    return fn
tasks, k = [], 0
for i, sc in enumerate(scenes):
    imgs = find(sc)
    iscard = sc["src"] in ("text-card", "map") or re.match(r"(?i)(minimal )?text card|three-column|four-window|six |seven |card", sc["vis"])
    if not imgs and POOL and not iscard: imgs = POOL[-12 - (i % 5):][::3][:3] or POOL[-1:]   # no match: reuse earlier images of this film (different zoom)
    if not imgs: c = os.path.join(W, f"card{i}.jpg"); card(re.split(r"[;]", sc["vis"].split(":", 1)[1] if ":" in sc["vis"] else (sc["chap"] or ""))[0].strip(" ."), c); imgs = [c]
    ns = max(1, round(sc["dur"] / 7)); base = sc["frames"] // ns
    for j in range(ns):
        nf = base if j + 1 < ns else sc["frames"] - base * (ns - 1)
        tasks.append((k, imgs[j % len(imgs)], nf, k, sc["chap"] if j == 0 else None)); k += 1
    if i % 25 == 0: print("images", i, "/", len(scenes), flush=True)
with ThreadPoolExecutor(4) as ex: files = list(ex.map(shot, tasks))
open(os.path.join(W, "list.txt"), "w").write("".join(f"file '{f}'\n" for f in files))
sh("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(W, "list.txt"), "-i", os.path.join(W, "voice.wav"),
   "-af", "acompressor=threshold=-20dB:ratio=2:attack=20:release=250,loudnorm=I=-16:TP=-1.5:LRA=7", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", os.path.join(OUT, vid + ".mp4"))

# ---------- Shorts (vertical, cut on scene boundaries, <=58 s) ----------
meta = {}
for n, (a, b, title) in enumerate(shorts[:4], 1):
    sel = [s for s in scenes if s["t"] >= a and s["t"] < b] or [s for s in scenes if s["t"] >= a][:1]
    st = sel[0]["start"]; en = st
    for s in sel:
        if s["start"] + s["dur"] - st > 58: break
        en = s["start"] + s["dur"]
    en = min(max(en, st + 20), st + 58); sid = f"{vid}_s{n}"; tf = os.path.join(W, sid + ".txt"); open(tf, "w").write("\n".join(textwrap.wrap(title, 22)[:3]))
    fc = ("[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5[bg];[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,"
          f"drawtext=fontfile={FONT}:textfile={tf}:fontcolor={GOLD}:fontsize=60:x=(w-text_w)/2:y=230:line_spacing=12:shadowcolor=black:shadowx=3:shadowy=3:enable='lt(t,5)'")
    sh("ffmpeg", "-y", "-loglevel", "error", "-ss", f"{st:.2f}", "-t", f"{en - st:.2f}", "-i", os.path.join(OUT, vid + ".mp4"), "-filter_complex", fc, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", os.path.join(OUT, sid + ".mp4"))
    meta[sid] = {"title": title, "tags": ["#shorts"] + ["#" + re.sub(r"\W", "", t) for t in hd.get("TAGS", "").split(",")[:3] if t.strip()]}

# ---------- metadata ----------
seen, lines = set(), []
for a in ATTR:
    if a not in seen: seen.add(a); lines.append(a)
desc = hd.get("DESC", "")[:3800] + "\n\nSources: " + hd.get("SOURCES", "").replace("\n", "; ")[:600] + "\n\nNarration is AI-generated (synthetic voice). Images are public-domain / CC0 works from Wikimedia Commons and The Met Open Access; some illustrations are generated text cards. Not made by or affiliated with any religious institution.\n\nImage credits:\n"
for a in lines:
    if len(desc) + len(a) + 1 > 4850: break
    desc += a + "\n"
json.dump({"title": hd.get("TITLE", vid), "tags": [t.strip() for t in hd.get("TAGS", "").split(",") if t.strip()], "desc": desc, "shorts_meta": meta, "minutes": round(off / 60, 1), "images": len(lines)}, open(os.path.join(OUT, "meta.json"), "w"), indent=1)
print(f"DONE {vid}: {off / 60:.1f} min, {len(lines)} credited images, {len(meta)} Shorts")
