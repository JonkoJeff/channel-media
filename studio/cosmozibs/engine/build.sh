#!/usr/bin/env bash
# Render an episode: long (16:9) + all Shorts (9:16). Usage: bash build.sh cz01 [workers]
set -euo pipefail
ID=$1; N=${2:-4}; MODE=${3:-full}; D=build/$ID; HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
EP=../episodes/$ID.json; [ -f ../../channels/faith/episodes/$ID.json ] && EP=../../channels/faith/episodes/$ID.json   # Faith Doodles (TikTok only)
cat core.part cast.part scenes.part > engine.js; cat core.part cast.part scenes.part thumbs.part > thumbs.js
if [ "$MODE" = tiktok ]; then :; elif [ "$MODE" = clips ]; then python3 voice.py "$EP" clips; else python3 voice.py "$EP"; node thumbs.mjs "$D/thumbs" "$EP"; fi
render() { # timeline layout outname title
  local TL=$1 LAY=$2 OUT=$3 TITLE=${4:-}; local FR=$(python3 -c "import json;print(len(json.load(open('$TL'))['talk']))")
  rm -rf "$D/frames_$OUT"; local Q=$(( (FR + N - 1) / N )); local pids=()
  for ((w=0; w<N; w++)); do node render.mjs "$TL" "$LAY" "$D/frames_$OUT" $((w*Q)) $(((w+1)*Q)) "$TITLE" & pids+=($!); done
  for p in "${pids[@]}"; do wait $p; done
  ffmpeg -y -loglevel error -framerate 12 -pattern_type glob -i "$D/frames_$OUT/*.jpg" -i "${TL%.json}.wav" -vf fps=24,format=yuv420p \
    -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 160k -shortest -movflags +faststart "$D/$OUT.mp4"
  rm -rf "$D/frames_$OUT"; echo "done $OUT $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$D/$OUT.mp4")"
}
if [ "$MODE" = tiktok ]; then python3 voice.py "$EP"; T=$(python3 -c "import json;t=json.load(open('$EP'))['tiktok'];print(t['title']+'|'+t['hook'])"); render "$D/long.json" tiktok "${ID}_tiktok" "$T"; exit 0; fi
if [ "$MODE" != clips ]; then
render "$D/long.json" long "${ID}_long"
for s in $(python3 -c "import json;ep=json.load(open('$EP'));print(' '.join(x['id'] for x in ep['segments'] if 'short' in x))"); do
  T=$(python3 -c "import json;ep=json.load(open('$EP'));print([x for x in ep['segments'] if x['id']=='$s'][0]['short']['title'])")
  render "$D/short_$s.json" short "${ID}_short_$s" "$T"
done
fi
# TikTok-only clips (owner 20 Oct): part 2 of every story + the speed round
for c in $(python3 -c "import json;print(' '.join(x['id'] for x in json.load(open('$D/clips.json'))))"); do
  T=$(python3 -c "import json;x=[x for x in json.load(open('$D/clips.json')) if x['id']=='$c'][0];print(x['title']+'|'+x.get('hook',''))")
  render "$D/clip_$c.json" tiktok "${ID}_clip_$c" "$T"
done
