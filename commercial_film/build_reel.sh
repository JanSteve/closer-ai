#!/bin/sh
# Rebuild CLOSER AI Official Instagram Reel (9:16 Vertical 1080x1920)
set -e
D="$(cd "$(dirname "$0")" && pwd)"
LEMO_ROOT="/Users/janstevedaniel/lemo-opuscar"
PY="$LEMO_ROOT/.venv/bin/python"

echo "=== 1. Synthesizing Reel Voice Lines ==="
$PY "$D/tools/synth_reel_voices.py"

echo "=== 2. Composing Kinetic Reel Score ==="
$PY "$D/music/score_reel.py"

echo "=== 3. Mixing Audio (-14 LUFS) ==="
$PY "$D/mix_reel.py"

echo "=== 4. Rendering 1080x1920 Vertical Canvas Video Frames ==="
cd "$LEMO_ROOT"
node core/render/video.mjs "$D" --size 1080x1920 --fps 24 --workers 4 --q "format=reel" --out "$D/out/video_reel.mp4"

echo "=== 5. Muxing Master Broadcast Instagram Reel ==="
PATH="/usr/bin:/bin:/usr/sbin:/sbin:$PATH" \
sh core/render/mux.sh "$D/out/video_reel.mp4" "$D/mix_reel.wav" "$D/closer_reel.mp4" 24 0

echo "=== 6. Generating Vertical Poster Image ==="
node core/render/still.mjs "$D" 2.0 --size 1080x1920 --q "format=reel" --out "$D" --prefix po_reel_
mv -f "$D/po_reel_2.0.jpg" "$D/closer_reel_poster.jpg"

echo "✓ Instagram Reel build complete: $D/closer_reel.mp4"
