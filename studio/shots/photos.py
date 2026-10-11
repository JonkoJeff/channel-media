"""Fetch free-licensed photos for videos from Openverse (includes Wikimedia Commons, Flickr CC, ...).
Reads studio/channels/<ch>/photos.json: [{"file": "x.jpg", "query": "handmade jewelry shop"}]
Only licenses that allow commercial use AND modification (cc0, pdm, by, by-sa). Writes the image to
studio/channels/<ch>/photos/<file> and its credit to photos/credits.json (title, creator, license, url)."""
import json, os, urllib.parse, urllib.request
UA = {"User-Agent": "CrazyFactsPublisher/1.0 (github.com/JonkoJeff/channel-media)"}
def get(url): return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
for ch in os.listdir("studio/channels"):
    lst = os.path.join("studio/channels", ch, "photos.json")
    if not os.path.exists(lst): continue
    out = os.path.join("studio/channels", ch, "photos"); os.makedirs(out, exist_ok=True)
    cpath = os.path.join(out, "credits.json"); credits = json.load(open(cpath)) if os.path.exists(cpath) else {}
    for p in json.load(open(lst)):
        if os.path.exists(os.path.join(out, p["file"])): continue
        q = urllib.parse.urlencode({"q": p["query"], "license": "cc0,pdm,by,by-sa", "license_type": "commercial,modification",
                                    "page_size": 20, "mature": "false"})
        try:
            res = json.loads(get("https://api.openverse.org/v1/images/?" + q))["results"]
            print(f"::notice::'{p['query']}': {len(res)} results")
            res = sorted(res, key=lambda r: -((r.get("width") or 0) >= 1600))
            for r in res:
                try:
                    data = get(r["url"])
                    if len(data) < 50000: continue
                    open(os.path.join(out, p["file"]), "wb").write(data)
                    credits[p["file"]] = {"title": r.get("title"), "creator": r.get("creator"), "license": f'{r["license"].upper()} {r.get("license_version") or ""}'.strip(),
                                          "license_url": r.get("license_url"), "source": r.get("foreign_landing_url"), "provider": r.get("source")}
                    print("ok", p["file"], r.get("source"), r["license"]); break
                except Exception as e: print(f"::notice::skip {r.get('source')}: {str(e)[:80]}")
            else: print(f"::warning::no usable photo for '{p['query']}'")
        except Exception as e: print(f"::warning::{p['query']}: {e}")
    json.dump(credits, open(cpath, "w"), indent=1)
