#!/usr/bin/env bash
# Lays the soundtrack under the demo video that demo.tape records (VHS records no
# sound). Run it from the repository root after `vhs scripts/video/demo.tape`:
#
#     scripts/video/add_music.sh [video]
#
# The picture is copied untouched; any earlier soundtrack is replaced, so running it
# twice is harmless. The music fades out over its last few seconds, or at the end of
# the video if that comes first.
#
# Music: "110611-005_chora_harp_from_gambia.wav" by reinsamba, CC0,
# https://freesound.org/people/reinsamba/sounds/135811/

set -euo pipefail

VIDEO="${1:-docs/video/reason-commons-demo.mp4}"
MUSIC="$(dirname "$0")/chora-harp-from-gambia.m4a"
FADE=6

duration() {
  ffprobe -v error -show_entries format=duration -of csv=p=0 "$1"
}

END="$(python3 -c "print(min($(duration "$VIDEO"), $(duration "$MUSIC")))")"
FADE_START="$(python3 -c "print(max(0, $END - $FADE))")"

OUT="$(mktemp "${TMPDIR:-/tmp}/reason-commons-demo.XXXXXX").mp4"
ffmpeg -hide_banner -loglevel error -y -i "$VIDEO" -i "$MUSIC" \
  -map 0:v:0 -map 1:a:0 -c:v copy \
  -af "afade=t=out:st=$FADE_START:d=$FADE" -c:a aac -b:a 160k \
  -t "$(duration "$VIDEO")" -movflags +faststart "$OUT"
mv "$OUT" "$VIDEO"
echo "Added music to $VIDEO"
