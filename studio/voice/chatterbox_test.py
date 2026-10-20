"""Voice test (owner 20 Oct): Chatterbox (MIT, Resemble AI) for the religion TikTok account. Runs in GitHub Actions (cosmozibs.yml mode=voicetest).
Energetic young creator delivery; reference voices are our own Kokoro voices (never a real person). Output: studio/channels/faith/voice_tests/*.mp3"""
import os, subprocess, sys
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); import kokoro_tts as k
OUT = os.path.join(HERE, "..", "channels", "faith", "voice_tests"); os.makedirs(OUT, exist_ok=True)
TEXT = ("Wait. Five different religions tell almost the same flood story? And nobody talks about it! "
        "Okay, so in ancient Mesopotamia, a man builds a giant boat to survive a flood. Sound familiar? Let's break it down.")
m = ChatterboxTTS.from_pretrained(device="cpu")
refs = {}
for v in ("am_puck", "am_echo", "am_michael"):
    refs[v] = f"/tmp/ref_{v}.wav"; k.save(k.speak("Hey guys, today I'm going to show you something that honestly blew my mind. Stay with me, because this one is wild.", v, 1.1), refs[v])
tests = [("1_default_calm", None, .5, .5), ("2_default_hype", None, .8, .3), ("3_young_hype", "am_puck", .75, .3), ("4_bright_hype", "am_echo", .75, .3), ("5_warm_hype", "am_michael", .7, .35)]
for name, ref, ex, cfg in tests:
    wav = m.generate(TEXT, audio_prompt_path=refs.get(ref), exaggeration=ex, cfg_weight=cfg)
    w = f"/tmp/{name}.wav"; ta.save(w, wav, m.sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", w, "-af", "loudnorm=I=-14", "-c:a", "libmp3lame", "-q:a", "3", f"{OUT}/{name}.mp3"], check=True); print("done", name)
