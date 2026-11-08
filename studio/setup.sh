#!/usr/bin/env bash
# Downloads the voice model + phonemizer into studio/voice (not committed). Safe to re-run.
set -euo pipefail
V="$(cd "$(dirname "$0")" && pwd)/voice"; cd "$V"
R=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
get() { for i in 1 2 3; do curl -sL -C - -m 900 -o "$1" "$2" && [ "$(stat -c %s "$1")" = "$3" ] && return 0; sleep 3; done; echo "download failed: $1"; exit 1; }
[ -f kokoro.fp32.onnx ] || get kokoro.fp32.onnx $R/kokoro-v1.0.onnx 325532387
[ -f voices.bin ] || get voices.bin $R/voices-v1.0.bin 28214398
if [ ! -x piper/espeak-ng ]; then
  for i in 1 2 3 4 5; do  # retry: parallel render jobs sometimes get an error page instead of the tarball (lf35, 8 Nov)
    curl -sfL -m 300 -o piper.tgz https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz && tar xzf piper.tgz && chmod +x piper/espeak-ng && break
    sleep $((i * 10))
  done
  rm -f piper.tgz
  if [ ! -f piper/espeak-ng ]; then  # release download keeps failing on some runners (lf35, 8 Nov): use the distro espeak-ng
    sudo apt-get install -y -q espeak-ng >/dev/null; mkdir -p piper; ln -sf "$(command -v espeak-ng)" piper/espeak-ng
    ln -sfn "$(dirname "$(dpkg -L espeak-ng-data | grep '/espeak-ng-data/phontab$')")" piper/espeak-ng-data
  fi
fi
python3 -c "import onnxruntime, numpy, scipy, PIL" && which ffmpeg ffprobe >/dev/null
python3 -c "import sys; sys.path.insert(0,'$V'); import kokoro_tts as k; a=k.speak('Setup check.','am_puck'); assert len(a)>1000; print('voice OK')"
