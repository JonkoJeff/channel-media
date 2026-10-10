"""Kokoro-82M (Apache 2.0) TTS without pip: onnxruntime + espeak-ng (from the Piper bundle) for phonemes.
Usage: python3 kokoro_tts.py "text" out.wav [voice=am_puck] [speed=1.0]"""
import json, os, re, subprocess, sys, wave
import numpy as np, onnxruntime as ort

HERE = os.path.dirname(os.path.abspath(__file__))
VOCAB = json.load(open(os.path.join(HERE, "kokoro_config.json")))["vocab"]
SR = 24000
_sess = _voices = None

def phonemize(text):
    # espeak drops punctuation, so phonemize the words between punctuation and put the marks back (like phonemizer's preserve_punctuation)
    out = []
    for word, punct in re.findall(r"([^.,!?;:…—]+)([.,!?;:…—]*)", text):
        if word.strip():
            ipa = subprocess.run([os.path.join(HERE, "piper", "espeak-ng"), f"--path={os.path.join(HERE, 'piper')}", "-q", "--ipa", "-v", "en-us", word.strip()],
                                 capture_output=True, text=True, env={**os.environ, "LD_LIBRARY_PATH": os.path.join(HERE, "piper")}).stdout
            out.append(" ".join(ipa.split()))
        if punct: out[-1:] = [(out[-1] if out else "") + punct.replace("…", "...")[:3]]
    return "".join(c for c in " ".join(out) if c in VOCAB).strip()

def speak(text, voice="am_puck", speed=1.0):
    global _sess, _voices
    if _sess is None:
        _sess = ort.InferenceSession(os.path.join(HERE, "kokoro.fp32.onnx"))
        _voices = np.load(os.path.join(HERE, "voices.bin"))
    ph = phonemize(text)
    toks = [VOCAB[c] for c in ph][:510]
    style = _voices[voice][len(toks) - 1]
    audio = _sess.run(None, {"tokens": np.array([[0, *toks, 0]], np.int64), "style": style.astype(np.float32),
                             "speed": np.array([speed], np.float32)})[0].ravel()
    return audio

def save(audio, path):
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

if __name__ == "__main__":
    a = sys.argv
    save(speak(a[1], a[3] if len(a) > 3 else "am_puck", float(a[4]) if len(a) > 4 else 1.0), a[2])
