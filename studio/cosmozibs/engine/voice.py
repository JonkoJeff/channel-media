"""Builds all audio for an episode: one wav per line (cached), a long mix and one mix per Short, plus timeline JSON with
per-line timing, mouth openness per frame, captions. Usage: python3 voice.py ../episodes/cz01.json"""
import sys, os, json, subprocess, hashlib, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'voice')); import kokoro_tts as k
SR, FPS = 24000, 12
VOICES = {"cosmo": ("am_puck", 1.06, 1.14), "zib": ("am_liam", 1.08, 1.24), "bolt": ("am_echo", 1.06, 1.15),
          "rocky": ("am_fenrir", 1.0, 1.05), "tik": ("am_michael", 1.06, 1.14)}
GAP, SCENE_GAP = 0.42, 0.8
ep = json.load(open(sys.argv[1])); OUT = os.path.join(HERE, "build", ep["id"]); os.makedirs(OUT + "/lines", exist_ok=True)

def load(p):
    with wave.open(p) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767

def line_wav(who, text):
    v, sp, pitch = VOICES[who]
    h = hashlib.md5(f"{who}|{v}|{sp}|{pitch}|{text}".encode()).hexdigest()[:12]; p = f"{OUT}/lines/{h}.wav"
    if not os.path.exists(p):
        raw = p + ".raw.wav"; k.save(k.speak(text, v, sp), raw)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", f"asetrate={SR}*{pitch},aresample={SR},atempo={1/pitch:.4f},equalizer=f=3000:t=q:w=1:g=2.5", p], check=True); os.remove(raw)
    a = load(p); return a / (np.abs(a).max() + 1e-6) * .9

# ---------- procedural music + sfx (royalty-free) ----------
def music(total):
    tt = np.arange(int(total * SR)) / SR; m = np.zeros_like(tt)
    chords = [(261.6, 329.6, 392.0), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7)]; bar = 2.2
    for i in range(int(total / bar) + 1):
        ch = chords[i % 4]; a0 = int(i * bar * SR); a1 = min(len(tt), int((i + 1) * bar * SR))
        if a0 >= len(tt): break
        seg = tt[a0:a1] - tt[a0]; env = np.minimum(1, seg / .5) * np.minimum(1, (bar - seg) / .5)
        m[a0:a1] += .22 * env * sum(np.sin(2 * np.pi * f / 2 * seg) for f in ch)
        for j in range(8):
            s0 = a0 + int(j * bar / 8 * SR); n = int(.25 * SR)
            if s0 + n > len(tt): break
            f = ch[[0, 1, 2, 1, 0, 2, 1, 2][j]] * (2 if j in (3, 7) else 1); x = np.arange(n) / SR
            m[s0:s0 + n] += .16 * np.exp(-x * 10) * np.sin(2 * np.pi * f * x)
    m = np.convolve(m, np.ones(8) / 8, "same"); return m / (np.abs(m).max() + 1e-6) * .13

def sfx(kind):
    R = np.random.RandomState(7)
    if kind == "whoosh":
        n = int(.5 * SR); x = np.arange(n) / SR; z = np.convolve(R.randn(n), np.ones(25) / 25, "same"); return z * np.sin(np.pi * x / .5) ** 2 * .9
    if kind == "pop":
        n = int(.09 * SR); x = np.arange(n) / SR; return np.sin(2 * np.pi * (500 + 2500 * x) * x) * np.exp(-x * 40) * .5
    if kind == "ding":
        n = int(1.0 * SR); x = np.arange(n) / SR; return (np.sin(2 * np.pi * 1318 * x) + .5 * np.sin(2 * np.pi * 1976 * x)) * np.exp(-x * 4) * .35
    if kind == "boing":
        n = int(.45 * SR); x = np.arange(n) / SR; return np.sin(2 * np.pi * (180 + 120 * np.sin(2 * np.pi * 9 * x)) * x) * np.exp(-x * 6) * .5
    if kind == "scratch":
        n = int(.35 * SR); x = np.arange(n) / SR; z = np.convolve(R.randn(n), np.ones(6) / 6, "same"); return z * np.sin(2 * np.pi * 14 * x) ** 2 * np.exp(-x * 5) * .7
    if kind == "tick":
        n = int(.05 * SR); x = np.arange(n) / SR; return np.sin(2 * np.pi * 1800 * x) * np.exp(-x * 90) * .45
    if kind == "riser":
        n = int(1.0 * SR); x = np.arange(n) / SR; return np.sin(2 * np.pi * (300 + 600 * x * x) * x) * (x / 1.0) * .18
    return np.zeros(1)

def build(lines, name):
    t = 0.5; tl = []; voice_parts = []; fx = []
    prev_show = None
    for i, ln in enumerate(lines):
        a = line_wav(ln["who"], ln["say"])
        if ln.get("show") and i: t += SCENE_GAP - GAP
        if ln.get("show"): fx.append((t - .3, "whoosh"))
        st = t; t += len(a) / SR
        tl.append({"i": i, "who": ln["who"], "say": ln["say"], "start": round(st, 3), "end": round(t, 3), "show": ln.get("show"), "seg": ln.get("seg")})
        voice_parts.append((st, a))
        if ln.get("sfx"): fx.append((st - (.35 if ln["sfx"] == "scratch" else 0), ln["sfx"]))
        if ln.get("pause"):
            for q in range(int(ln["pause"])): fx.append((t + .3 + q, "tick"))
            fx.append((t + ln["pause"] - .7, "riser")); t += ln["pause"]
        t += GAP
    total = t + 1.2
    voice = np.zeros(int(total * SR))
    for st, a in voice_parts: voice[int(st * SR):int(st * SR) + len(a)] += a
    env = np.convolve(np.abs(voice), np.ones(4800) / 4800, "same"); duck = 1 - .6 * np.clip(env * 12, 0, 1)
    mix = voice + music(total) * duck
    for at, kd in fx:
        s = sfx(kd); i0 = int(max(0, at) * SR); mix[i0:i0 + len(s)] += s[:max(0, len(mix) - i0)]
    mix = mix / (np.abs(mix).max() + 1e-6) * .95
    k.save(mix.astype(np.float32), f"{OUT}/{name}.wav")
    nfr = int(total * FPS); talk = []
    for f in range(nfr):
        a0, a1 = int(f / FPS * SR), int((f + 1) / FPS * SR); talk.append(round(float(min(1, np.sqrt((voice[a0:a1] ** 2).mean() + 1e-9) * 6)), 2))
    json.dump({"fps": FPS, "total": total, "lines": tl, "talk": talk, "title": ep["title"]}, open(f"{OUT}/{name}.json", "w"))
    return total

# long: all segments in order; mark segment ids
allines = []
for s in ep["segments"]:
    for j, ln in enumerate(s["lines"]): allines.append({**ln, "seg": s["id"]})
T = build(allines, "long"); print("long", round(T, 1), "s")
for s in ep["segments"]:
    if "short" in s:
        ls = [{**ln, "seg": s["id"]} for ln in s["lines"][:s["short"]["end"] + 1]]
        if not ls[0].get("show"): ls[0]["show"] = {"type": "crew"}
        Ts = build(ls, "short_" + s["id"]); print("short", s["id"], round(Ts, 1), "s")
