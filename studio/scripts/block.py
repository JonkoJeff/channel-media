"""Compact script format -> video block JSON (+ photos.json entries). Usage: python3 studio/scripts/block.py <id> <file.txt> [first_chapter_n]
Segments are separated by blank lines. First line of a segment is a header, the rest is the voice line:
  @char SPRITE BG | cap | sub            @chapter SPRITE BG | title           @end SPRITE BG | next title
  @list SPRITE BG | title | a ;; b ;; c  @study SPRITE BG | who | where | what @stat SPRITE BG | title | big | label
  @bars SPRITE BG | title | unit | lab:val ;; lab:val                     @quote SPRITE BG | text | by
  @curve SPRITE BG | title | x | y | peak | label                         @photo FILE | cap
Lines '#ai FILE | prompt' or '#ov FILE | openverse query' add photos to studio/assetedit/photos.json."""
import json, os, sys
D = os.path.join(os.path.dirname(__file__), "..", "assetedit")
bid, src = sys.argv[1], open(sys.argv[2]).read(); n = int(sys.argv[3]) if len(sys.argv) > 3 else 1
segs, photos = [], []
for blk in [b.strip() for b in src.split("\n\n") if b.strip()]:
    lines = [l for l in blk.splitlines() if l.strip()]
    if lines[0].startswith("#"):
        for l in lines:
            k, rest = l.split(" ", 1); f, val = [x.strip() for x in rest.split("|", 1)]
            photos.append({"file": f, "ai": val} if k == "#ai" else {"file": f, "query": val})
        continue
    head, say = lines[0], " ".join(l.strip() for l in lines[1:])
    parts = [p.strip() for p in head[1:].split("|")]; t, *a = parts[0].split(); f = parts[1:]
    if t == "photo": sh = {"type": "photo", "file": a[0]}; sh.update({"cap": f[0]} if f and f[0] else {})
    else:
        sh = {"type": t, "sprite": a[0], "bg": a[1]}
        if t == "char": sh.update({"cap": f[0]} if f and f[0] else {}); sh.update({"sub": f[1]} if len(f) > 1 and f[1] else {})
        elif t == "chapter": sh.update(n=n, title=f[0]); n += 1
        elif t == "end": sh.update(next=f[0])
        elif t == "list": sh.update(title=f[0], items=[x.strip() for x in f[1].split(";;")])
        elif t == "study": sh.update(who=f[0], where=f[1], what=f[2])
        elif t == "stat": sh.update(title=f[0], big=f[1], label=f[2])
        elif t == "bars": sh.update(title=f[0], unit=f[1], bars=[[x.rsplit(":", 1)[0].strip(), float(x.rsplit(":", 1)[1])] for x in f[2].split(";;")])
        elif t == "quote": sh.update(text=f[0], by=f[1])
        elif t == "curve": sh.update(title=f[0], x=f[1], y=f[2], peak=float(f[3]), label=f[4])
    assert say, f"empty voice line: {head}"
    segs.append({"say": say, "show": sh})
v = {"id": bid, "part": True, "vibe": "calm", "voice": "am_michael", "segments": segs}
sys.path.insert(0, D); os.chdir(D); import longform as L; L.validate(v)
json.dump(v, open(os.path.join(os.path.dirname(__file__), "..", "assetedit", "videos", bid + ".json"), "w"), indent=1, ensure_ascii=False)
if photos:
    pj = os.path.join(os.environ.get("CHANNEL_DIR") or D, "photos.json"); cur = json.load(open(pj)) if os.path.exists(pj) else []
    have = {p["file"] for p in cur}; cur += [p for p in photos if p["file"] not in have]; json.dump(cur, open(pj, "w"), indent=1, ensure_ascii=False)
w = sum(len(s["say"].split()) for s in segs); print(f"{bid}: {len(segs)} segments, {w} words, ~{w / 160:.1f} min, photos +{len(photos)}")
