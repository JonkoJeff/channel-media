"""Free AI images with Flux on Cloudflare Workers AI (runs in GitHub Actions; secret CF_API_TOKEN).
studio/ai/jobs.json: [{"out": "name.png", "prompt": "...", "model": "flux-2-klein-9b" | "flux-2-klein-4b" | "flux-1-schnell",
                       "refs": ["studio/ai/refs/x.png", ...] (max 4, each < 512 px), "width": 1024, "height": 1024, "seed": 1}]
Writes studio/ai/out/<out>; skips files that already exist."""
import base64, json, os, urllib.request, uuid
tok, acc = os.environ["CF_API_TOKEN"], os.environ["CF_ACCOUNT_ID"]
D = os.path.dirname(__file__); os.makedirs(os.path.join(D, "out"), exist_ok=True)
def multipart(fields, files):
    b = uuid.uuid4().hex; body = b""
    for k, v in fields.items(): body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for k, path in files.items():
        body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{os.path.basename(path)}"\r\nContent-Type: image/png\r\n\r\n'.encode() + open(path, "rb").read() + b"\r\n"
    return body + f"--{b}--\r\n".encode(), f"multipart/form-data; boundary={b}"
for j in json.load(open(os.path.join(D, "jobs.json"))):
    dst = os.path.join(D, "out", j["out"])
    if os.path.exists(dst): continue
    m = j.get("model", "flux-2-klein-9b"); url = f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/@cf/black-forest-labs/{m}"
    try:
        if m == "flux-1-schnell":
            data, ct = json.dumps({"prompt": j["prompt"], "steps": j.get("steps", 4)}).encode(), "application/json"
        else:
            f = {"prompt": j["prompt"], "width": j.get("width", 1024), "height": j.get("height", 1024)}
            if "seed" in j: f["seed"] = j["seed"]
            data, ct = multipart(f, {f"input_image_{i}": r for i, r in enumerate(j.get("refs", []))})
        res = json.loads(urllib.request.urlopen(urllib.request.Request(url, data=data, headers={"Authorization": "Bearer " + tok, "Content-Type": ct}), timeout=180).read())
        open(dst, "wb").write(base64.b64decode(res["result"]["image"])); print("ok", j["out"])
    except Exception as e:
        print(f"::error::{j['out']}: {type(e).__name__}: {str(e)[:150]} {getattr(e, 'read', lambda: b'')()[:400]}")
