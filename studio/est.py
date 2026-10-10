import json,re,sys
for p in sys.argv[1:]:
    v=json.load(open(p)); w=sum(len(s["say"].split()) for s in v["segments"])
    sents=sum(len(re.split(r"(?<=[.!?])\s+",s["say"].strip())) for s in v["segments"])
    gaps=sum({"chapter":0.9,"end":2.0}.get(s["show"]["type"],0.5) for s in v["segments"])
    est=w/213*60+sents*0.4+gaps   # calibrated on lf01 real render
    print(f"{p}: {w} words, {len(v['segments'])} segs, est {est/60:.2f} min {'OK' if est>=490 else 'SHORT'}")
