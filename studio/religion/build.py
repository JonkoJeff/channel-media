"""Belief Through Time / Religion Unfolded: script file (stories/FORMAT.md) -> 1080p documentary + 4 Shorts. No tokens: runs in GitHub Actions.
python3 build.py <episode file> <id> [--test]   -> out/<id>.mp4, out/<id>_s1..4.mp4, out/result files (see publish step in religion.yml)
Images: ONLY public-domain / CC0 (Wikimedia Commons, The Met Open Access), searched from the VISUAL line; fallback = navy/gold text card.
Voice: Kokoro bm_lewis 0.92 with the shared natural flow (studio/voice/flow.py, same as Brain After Dark). Ken-Burns stills, chapter cards,
quiet music bed that drops before each chapter reveal, own thumbnail (out/thumb.jpg), loudnorm -16 LUFS."""
import json, os, re, subprocess, sys, hashlib, time, urllib.request, urllib.parse, html, wave, glob, textwrap
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(H, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "studio", "voice")); import kokoro_tts as K, flow, zlib
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
    m = re.match(r"(TITLE|DESC|TAGS|SOURCES|SHORTS|THUMB):\s*(.*)", ln)
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
CITY = re.compile(r"(?i)building|architecture|city|cities|street|people|person|portrait|bridge|office|urban|vehicle|car |cars|transport|ship|boat|train|airport|economy|industry|agricultur|farm|workers|military|war |sport|ski|tourism|monument|church|castle|house|road|village|town|night photography of cities|london|moscow|russia")
NATURE = re.compile(r"(?i)landscape|sky|sea|ocean|water|mountain|desert|cloud|rain|forest|lake|river|beach|sunrise|sunset|dawn|dusk|star|moon|nature|coast|valley|waterfall|grass|geolog|rock|earth|space|astronomy|horizon|mist|fog|stone|hill|meadow|painting|art|manuscript|calligraph|mosque|bible|jesus|temple|ruins|archaeolog|egypt|mesopotamia|ancient")
def wm(q):
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(dict(action="query", generator="search", gsrsearch=q + " filetype:bitmap", gsrnamespace=6, gsrlimit=15, prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=2400, format="json"))
    r = json.loads(get(u)).get("query", {}).get("pages", {}); out = []
    for p in sorted(r.values(), key=lambda p: p.get("index", 99)):
        ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {}); lic = md.get("LicenseShortName", {}).get("value", "")
        cats = md.get("Categories", {}).get("value", "")
        if CITY.search(cats) or not NATURE.search(cats + " " + p["title"]): continue   # Wikimedia categories are far more reliable than file titles
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
            im2 = Image.open(fn); hsv = np.asarray(im2.convert("RGB").resize((64, 36)).convert("HSV")).astype(float)
            ok = im2.size[0] >= 1300 and (hsv[..., 1].mean() > 28 or "Met Open" in at) and hsv[..., 2].mean() > 45   # not black-and-white, not nearly black
            if ok: got.append(fn); ATTR.append(at); POOL.append(fn)
        except Exception as e: print("img fail", str(e)[:80])
        if len(got) >= 3: break
    CACHE[q] = got; return got
def card(text, fn, quote=None):
    """Designed card: gold reference/title + (optional) the narration's own line as a pull-quote. Never an empty frame."""
    im = Image.new("RGB", (1920, 1080)); d = ImageDraw.Draw(im)
    for y in range(1080): d.line([(0, y), (1920, y)], fill=(6, 11 + y // 40, 28 + y // 14))
    rng = np.random.default_rng(zlib.crc32((text or quote or "x").encode()))
    for _ in range(140): x, y = int(rng.integers(0, 1920)), int(rng.integers(0, 1080)); r = int(rng.integers(1, 3)); d.ellipse([x, y, x + r, y + r], fill=(200, 190, 150))
    d.rectangle([140, 120, 1780, 960], outline=(168, 140, 70), width=3); d.rectangle([158, 138, 1762, 942], outline=(110, 92, 50), width=1)
    head = [l for p in re.split(r"\s*/\s*| — ", text or "") for l in textwrap.wrap(p.strip(), 34)][:3]
    qt = textwrap.wrap(f"\u201c{quote}\u201d", 46)[:5] if quote else []
    fh, fq = ImageFont.truetype(FONT, 70), ImageFont.truetype(FONT, 46)
    total = len(head) * 90 + (60 + len(qt) * 66 if qt else 0); y = 540 - total // 2
    for ln in head: d.text((960, y), ln, font=fh, fill=(232, 195, 106), anchor="mm"); y += 90
    if qt:
        d.line([(760, y + 10), (1160, y + 10)], fill=(168, 140, 70), width=2); y += 60
        for ln in qt: d.text((960, y), ln, font=fq, fill=(240, 232, 214), anchor="mm"); y += 66
    im.save(fn, quality=92)


# ---------- voice ----------
def speak(s, i):   # same natural flow as Brain After Dark (RUNBOOK VOICE FLOW); voice identity unchanged: bm_lewis 0.92
    return flow.say(K, s, "bm_lewis", 0.92, zlib.crc32(vid.encode()) + i * 97, pause=0.6)
audio, jobs, off = [], [], 0.0
for i, sc in enumerate(scenes):
    a = speak(sc["say"], i); pad = 0.9 if i + 1 < len(scenes) else 3.5; a = np.concatenate([a, np.zeros(int(24000 * pad), np.float32)])
    nf = int(np.ceil(len(a) / 24000 * FPS)); a = np.concatenate([a, np.zeros(int(nf / FPS * 24000) - len(a) + 1, np.float32)])[:int(nf / FPS * 24000)]
    sc.update(frames=nf, start=off, dur=nf / FPS); off += nf / FPS; audio.append(a)
    if i % 40 == 0: print("voice", i, "/", len(scenes), flush=True)
vo = np.concatenate(audio); sr = 24000; tt = np.arange(len(vo)) / sr; bed = np.zeros_like(tt)
for ci, ch in enumerate([(261.6, 329.6, 392.0), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7)] * int(len(vo) / sr / 27.4 + 2)):
    a0, b0 = int(ci * 6.86 * sr), int((ci + 1) * 6.86 * sr)
    if a0 >= len(tt): break
    seg = tt[a0:b0] - tt[a0]; env = np.minimum(1, seg / 1.5) * np.minimum(1, (6.86 - seg) / 1.5)
    bed[a0:b0] += env * sum(np.sin(2 * np.pi * f / 2 * seg) + 0.3 * np.sin(2 * np.pi * f * seg) for f in ch)
for i, sc in enumerate(scenes):   # "silence before the reveal": the bed drops out around each new chapter card
    if i and sc["chap"] and sc["chap"] != scenes[i - 1]["chap"]: bed[max(0, int((sc["start"] - 0.8) * sr)):int((sc["start"] + 0.6) * sr)] = 0.0
bed = np.convolve(bed, np.ones(60) / 60, "same"); vr = np.sqrt((vo[np.abs(vo) > 0.01] ** 2).mean()) if (np.abs(vo) > 0.01).any() else 0.1
bed = bed / np.sqrt((bed ** 2).mean() + 1e-9) * vr * 10 ** (-26 / 20)   # ~26 dB under the voice, like Brain After Dark
K.save((vo + bed).astype(np.float32), os.path.join(W, "voice.wav")); print(f"voice done: {off / 60:.1f} min")

# ---------- video shots ----------
def shot(args):
    k, img, nf, style, label = args; fn = os.path.join(W, f"s{k:05d}.mp4"); n = max(nf, 2); d = n / FPS
    z = {0: f"z='1+0.14*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'", 1: f"z='1.14-0.14*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'",
         2: f"z=1.16:x='(iw-iw/zoom)*on/{n}':y='ih/2-ih/zoom/2'", 3: f"z=1.16:x='(iw-iw/zoom)*(1-on/{n})':y='ih/2-ih/zoom/2'",
         4: f"z='1+0.13*on/{n}':x='(iw-iw/zoom)*on/{n}':y='(ih-ih/zoom)*on/{n}'", 5: f"z='1.13-0.13*on/{n}':x='(iw-iw/zoom)*(1-on/{n})':y='(ih-ih/zoom)*(1-on/{n})'",
         6: f"z='1+0.13*on/{n}':x='(iw-iw/zoom)*(1-on/{n})':y='(ih-ih/zoom)*on/{n}'", 7: f"z='1.13-0.11*on/{n}':x='(iw-iw/zoom)*on/{n}':y='(ih-ih/zoom)*(1-on/{n})'"}[style % 8]   # 8 camera moves, never the same twice in a row
    vf = f"scale=2400:1350:force_original_aspect_ratio=increase,crop=2400:1350,zoompan={z}:d={n}:s=1920x1080:fps={FPS},eq=gamma=1.2:saturation=1.05,vignette=PI/6,fade=t=in:st=0:d=0.2,fade=t=out:st={d - 0.2:.2f}:d=0.2"
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
    if not imgs:
        c = os.path.join(W, f"card{i}.jpg")
        ref = re.sub(r"(?i)\s*(english )?(paraphrase|verse reference).*$", "", re.split(r"[;]", sc["vis"] or (sc["chap"] or ""))[0]).strip(" .")
        ref = re.sub(r"(?i)^(minimal )?text[- ]card\s*[:\-]?\s*", "", ref).strip()
        first = re.split(r"(?<=[.!?])\s", sc["say"])[0]; q = first if 30 <= len(first) <= 190 else None   # the narration's own first sentence as the pull-quote
        card(ref or (sc["chap"] or ""), c, q); imgs = [c]
    ns = max(1, round(sc["dur"] / 5.5)); base = sc["frames"] // ns   # a new shot every ~5.5 s (was 7): more rhythm
    for j in range(ns):
        nf = base if j + 1 < ns else sc["frames"] - base * (ns - 1)
        tasks.append((k, imgs[j % len(imgs)], nf, k, sc["chap"] if j == 0 else None)); k += 1
    if i % 25 == 0: print("images", i, "/", len(scenes), flush=True)
with ThreadPoolExecutor(4) as ex: files = list(ex.map(shot, tasks))
open(os.path.join(W, "list.txt"), "w").write("".join(f"file '{f}'\n" for f in files))
sh("ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(W, "list.txt"), "-i", os.path.join(W, "voice.wav"),
   "-af", "acompressor=threshold=-20dB:ratio=2:attack=20:release=250,loudnorm=I=-16:TP=-1.5:LRA=7", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", os.path.join(OUT, vid + ".mp4"))

# ---------- thumbnail: own headline per episode (GAP 2): base image + max 4 big words, high contrast, accent/side rotate per episode ----------
def thumb(base, words, n, path):
    im = Image.open(base).convert("RGB"); r = 1280 / 720
    w, h = im.size; im = im.crop(((w - h * r) / 2, 0, (w + h * r) / 2, h) if w / h > r else (0, (h - w / r) / 2, w, (h + w / r) / 2)).resize((1280, 720))
    left = n % 2 == 0; acc = [(232, 195, 106), (255, 179, 71), (127, 227, 216), (244, 167, 185), (242, 230, 201)][n % 5]
    ov = Image.new("L", (1280, 720)); d = ImageDraw.Draw(ov)
    for x in range(1280): d.line([(x, 0), (x, 720)], fill=int(235 * max(0, 1 - (x if left else 1279 - x) / 760) ** 1.3))
    im = Image.composite(Image.new("RGB", (1280, 720), (8, 10, 22)), im, ov); d = ImageDraw.Draw(im)
    ws = [x for x in re.sub(r"[^\w' -]", " ", words).upper().split() if x and (hd.get("THUMB") or x not in ("THE", "OF", "AND", "A", "AN", "IN", "TO", "WHEN", "WERE", "IS", "AS"))][:4]; lines = [" ".join(ws[:2]), " ".join(ws[2:])] if len(ws) > 2 else ws
    size = 150
    while size > 70 and max(ImageFont.truetype(FONT, size).getlength(l) for l in lines) > 640: size -= 6
    f = ImageFont.truetype(FONT, size); x0 = 60 if left else 1220; y = 360 - (len(lines) * (size + 18)) // 2
    for k2, ln in enumerate(lines):
        col = acc if k2 == len(lines) - 1 else (250, 246, 236)
        d.text((x0, y), ln, font=f, fill=col, anchor="la" if left else "ra", stroke_width=6, stroke_fill=(0, 0, 0)); y += size + 18
    im.save(path, quality=92)
words = hd.get("THUMB") or re.split(r"[:—-]", hd.get("TITLE", vid))[-1]
# approved owner art already carries its own title: keep it unchanged; generate only for episodes without art (e.g. Christianity 11-20)
owner_art = os.environ.get("THUMB") and os.path.exists(os.environ.get("THUMB", ""))
base = None if owner_art else (POOL[len(POOL) // 3] if POOL else None)
if base: thumb(base, words, int(re.sub(r"\D", "", vid) or 0), os.path.join(OUT, "thumb.jpg")); print("thumbnail:", " ".join(words.split()[:4]))

# ---------- Shorts (vertical, cut on scene boundaries, <=58 s) ----------
meta = {}
for n, (a, b, title) in enumerate(shorts[:4], 1):
    sel = [s for s in scenes if s["t"] >= a and s["t"] < b] or [s for s in scenes if s["t"] >= a][:1]
    st = sel[0]["start"]; en = st
    for s in sel:
        if s["start"] + s["dur"] - st > 58: break
        en = s["start"] + s["dur"]
    en = min(max(en, st + 20), st + 58); sid = f"{vid}_s{n}"; tf = os.path.join(W, sid + ".txt"); open(tf, "w").write("\n".join(textwrap.wrap(title, 22)[:3]))
    cf, cv = os.path.join(W, sid + "_f.jpg"), os.path.join(W, sid + "_cover.jpg")   # cover = thumbnail frame for the first 1.7 s (Zernio takes the frame at 1.5 s)
    sh("ffmpeg", "-y", "-loglevel", "error", "-ss", f"{st + 1:.2f}", "-i", os.path.join(OUT, vid + ".mp4"), "-frames:v", "1", "-q:v", "2", cf)
    cx = os.path.join(ROOT, "studio", "covers", sid + ".jpg")   # cover painted by Codex (factory rel_cover), else the drawn one
    if os.path.exists(cx): cv = cx
    else: import cover as _cv; _cv.cover(cf, title, n, cv, int(re.sub(r"\D", "", vid) or 0))
    fc = ("[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5[bg];[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2[v0];[v0][1:v]overlay=0:0:enable='lt(t,1.7)',"
          f"drawtext=fontfile={FONT}:textfile={tf}:fontcolor={GOLD}:fontsize=60:x=(w-text_w)/2:y=230:line_spacing=12:shadowcolor=black:shadowx=3:shadowy=3:enable='between(t,1.7,5)'")
    sh("ffmpeg", "-y", "-loglevel", "error", "-ss", f"{st:.2f}", "-t", f"{en - st:.2f}", "-i", os.path.join(OUT, vid + ".mp4"), "-loop", "1", "-t", f"{en - st:.2f}", "-i", cv, "-filter_complex", fc, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", os.path.join(OUT, sid + ".mp4"))
    meta[sid] = {"title": title, "tags": ["#shorts"] + ["#" + re.sub(r"\W", "", t) for t in hd.get("TAGS", "").split(",")[:3] if t.strip()]}

# ---------- metadata ----------
seen, lines = set(), []
for a in ATTR:
    if a not in seen: seen.add(a); lines.append(a)
# estimated chapter timestamps are internal notes, never public (rel21)
desc = re.split(r"\s*Estimated chapter", hd.get("DESC", ""), flags=re.I)[0][:3800] + "\n\nSources: " + hd.get("SOURCES", "").replace("\n", "; ")[:600] + "\n\nNarration is AI-generated (synthetic voice). Images are public-domain / CC0 works from Wikimedia Commons and The Met Open Access; some illustrations are generated text cards. Not made by or affiliated with any religious institution.\n\nImage credits:\n"
for a in lines:
    if len(desc) + len(a) + 1 > 4850: break
    desc += a + "\n"
json.dump({"title": hd.get("TITLE", vid), "tags": [t.strip() for t in hd.get("TAGS", "").split(",") if t.strip()], "desc": desc, "shorts_meta": meta, "minutes": round(off / 60, 1), "images": len(lines)}, open(os.path.join(OUT, "meta.json"), "w"), indent=1)
print(f"DONE {vid}: {off / 60:.1f} min, {len(lines)} credited images, {len(meta)} Shorts")
