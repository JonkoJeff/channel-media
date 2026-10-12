"""Register curated sprites cut by cutsheet.py: python3 register.py <cutdir> <prefix> <channel_dir> "n:EMO,n:EMO,..." <character name>
Copies <cutdir>/<prefix>NN.png -> <channel_dir>/assets/<prefix>NN.png and adds approved manifest entries (emotion tag by owner review)."""
import sys, json, shutil, os
cut, pre, ch, spec, who = sys.argv[1:6]
mp = os.path.join(ch, "manifest.json"); m = json.load(open(mp)); have = {a["asset_id"] for a in m["assets"]}
for it in spec.split(","):
    n, emo = it.split(":"); n = int(n); aid = f"{pre}{n:02d}"
    if aid in have: continue
    shutil.copy(f"{cut}/{aid}.png", f"{ch}/assets/{aid}.png")
    m["assets"].append({"asset_id": aid, "file_path": f"assets/{aid}.png", "approved": True, "emotion": emo, "gesture": "sheet_pose", "character": who, "anchor_point": "bottom_center"})
json.dump(m, open(mp, "w"), indent=1, ensure_ascii=False); print(pre, len(m["assets"]), "assets")
