"""Natural narration flow, shared by Brain After Dark (assetedit/longform.py) and Belief Through Time (religion/build.py).
RUNBOOK "VOICE FLOW": 1-2 sentences per Kokoro take (<170 chars, never across a question), speed with +-3% repeatable
variation per take, pause scaled by take length / question and jittered, silence trimmed, 12 ms fades."""
import re
import numpy as np


def takes(text):
    out = []
    for s in re.split(r"(?<=[.!?])\s+", text.strip()):
        if not s: continue
        if out and len(out[-1]) + len(s) < 170 and not out[-1].endswith("?"): out[-1] += " " + s
        else: out.append(s)
    return out


def say(k, text, voice, speed, seed, pause=0.6):
    """k = kokoro_tts module; seed makes the variation repeatable (same text -> same audio)."""
    out = []
    for ci, sent in enumerate(takes(text)):
        rng = np.random.default_rng(seed + ci)
        a = k.speak(sent[:420], voice, speed * float(rng.uniform(0.97, 1.03)))
        nz = np.nonzero(np.abs(a) > 0.01)[0]
        if len(nz): a = a[max(0, nz[0] - 400):nz[-1] + 900].copy()
        f = int(0.012 * k.SR)
        if len(a) > 2 * f: a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
        ps = pause * (1.25 if sent.rstrip().endswith("?") else 1.0) * (1.15 if len(sent) > 110 else 0.9) * float(rng.uniform(0.85, 1.2))
        out += [a.astype(np.float32), np.zeros(int(ps * k.SR), np.float32)]
    return np.concatenate(out) if out else np.zeros(2400, np.float32)


WARM = "equalizer=f=160:t=q:w=0.9:g=3.5,equalizer=f=320:t=q:w=1:g=1.5,equalizer=f=3800:t=q:w=1:g=-2.5,lowpass=f=7800"


def warm(path):
    """Warmer voice (owner 15 Oct, Brain After Dark): body +3.5 dB around 160 Hz, a little less 3-4 kHz edge, soft top. No timing change."""
    import os, subprocess
    tmp = path + ".w.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-af", WARM + ",alimiter=limit=0.89", tmp], check=True)
    os.replace(tmp, path)
