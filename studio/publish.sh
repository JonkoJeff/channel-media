#!/usr/bin/env bash
# Put video files online for Metricool: commits them to branch "media" (folder files/) and prints the public raw URLs.
# Usage: studio/publish.sh <file>...        |  studio/publish.sh --rm <name>...  (remove files once Metricool has copied them)
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel); W=/tmp/media-wt; RAW=https://raw.githubusercontent.com/JonkoJeff/channel-media/media/files
git -C "$ROOT" fetch -q --depth 1 origin media
rm -rf "$W"; git -C "$ROOT" worktree prune; git -C "$ROOT" worktree add -q -B media "$W" FETCH_HEAD
G() { git -C "$W" -c user.name=channel-bot -c user.email=jeffrey.vastenhout@gmail.com "$@"; }
if [ "${1:-}" = "--rm" ]; then shift; for n in "$@"; do G rm -q --ignore-unmatch "files/$n"; done; G commit -qm "Remove published files" || true; G push -q origin media; exit; fi
mkdir -p "$W/files"
for f in "$@"; do  # one push per file keeps each request small
  n=$(basename "$f"); cp "$f" "$W/files/$n"; G add "files/$n"; G commit -qm "Add $n"; G push -q origin media; echo "$RAW/$n"
done
