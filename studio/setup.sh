#!/usr/bin/env bash
# Downloads the voice model + phonemizer into studio/voice (not committed). Safe to re-run.
set -euo pipefail
V="$(cd "$(dirname "$0")" && pwd)/voice"; cd "$V"
R=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
get() { for i in 1 2 3; do curl -sL -C - -m 900 -o "$1" "$2" && [ "$(stat -c %s "$1")" = "$3" ] && return 0; sleep 3; done; echo "download failed: $1"; exit 1; }
[ -f kokoro.fp32.onnx ] || get kokoro.fp32.onnx $R/kokoro-v1.0.onnx 325532387
[ -f voices.bin ] || get voices.bin $R/voices-v1.0.bin 28214398
if [ ! -x piper/espeak-ng ]; then
  curl -sL -m 300 -o piper.tgz https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz && tar xzf piper.tgz && rm piper.tgz && chmod +x piper/espeak-ng
fi
python3 -c "import onnxruntime, numpy, scipy, PIL" && which ffmpeg ffprobe >/dev/null
python3 -c "import sys; sys.path.insert(0,'$V'); import kokoro_tts as k; a=k.speak('Setup check.','am_puck'); assert len(a)>1000; print('voice OK')"
