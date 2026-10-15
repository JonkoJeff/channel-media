"""Run the Belief Through Time (or any rel/lf) posting on YOUR computer, no GitHub Actions minutes.
Needs: git + gh (logged in) + python3 + ffmpeg, and the Zernio key in the environment (NEVER in the repo):
  PowerShell:  $env:ZERNIO_API_KEY = "<key 1>"
  python studio/local/post_btt.py                     # the default plan below
  python studio/local/post_btt.py rel02=2026-10-16 rel22=2026-10-17   # own plan: episode=day
Per episode: download the release mp4s (free, not Actions) -> zernio.py post (20:00) -> zernio.py shorts (15:00,18:00,21:00,23:30)
-> commit + push result.json after each step. zernio.py has the failsafes (never posts twice, adopts an existing post)."""
import os, subprocess, sys, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PLAN = [("rel02", "2026-10-16"), ("rel22", "2026-10-17"), ("rel03", "2026-10-18"), ("rel23", "2026-10-19"), ("rel04", "2026-10-20"), ("rel24", "2026-10-21")]
if len(sys.argv) > 1: PLAN = [tuple(a.split("=")) for a in sys.argv[1:]]
if not os.environ.get("ZERNIO_API_KEY"): sys.exit("Set ZERNIO_API_KEY first (key 1). Never put it in the repo.")
TMP = tempfile.mkdtemp(prefix="zernio_"); env = {**os.environ, "ZTMP": TMP}
def sh(*a, check=True): return subprocess.run(a, cwd=ROOT, env=env, check=check)
def save(msg):
    sh("git", "add", "studio/yt/zernio.json", check=False); sh("git", "add", "-f", "studio/renders", check=False)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0: return
    sh("git", "commit", "-qm", msg + " [skip ci]")
    for _ in range(5):
        if subprocess.run(["git", "pull", "-q", "--rebase", "--autostash"], cwd=ROOT).returncode == 0 and subprocess.run(["git", "push", "-q"], cwd=ROOT).returncode == 0: return
    sys.exit("result.json not pushed: fix git, do NOT re-run posting before it is pushed")
sh("git", "pull", "-q", "--rebase", "--autostash")
for vid, day in PLAN:
    print(f"== {vid} {day}", flush=True)
    sh("gh", "release", "download", vid, "--pattern", "*.mp4", "--dir", TMP, "--clobber")
    sh(sys.executable, "studio/yt/zernio.py", "post", vid, f"{day}T20:00", os.path.join(TMP, vid + ".mp4")); save(f"zernio post {vid}")
    sh(sys.executable, "studio/yt/zernio.py", "shorts", vid, f"{day}@15:00,18:00,21:00,23:30"); save(f"zernio shorts {vid}")
    for f in os.listdir(TMP): os.remove(os.path.join(TMP, f))
print("ALL DONE")
