#!/bin/sh
# Rebuild CLOSER AI Commercial Film from scratch: sh commercial_film/build.sh
set -e
D="$(cd "$(dirname "$0")" && pwd)"
LEMO_ROOT="/Users/janstevedaniel/lemo-opuscar"
PY="$LEMO_ROOT/.venv/bin/python"

echo "=== 1. Synthesizing Voice Lines ==="
$PY "$D/tools/synth_voices.py"

echo "=== 2. Composing Original Minimalist Score ==="
$PY "$D/music/score.py"

echo "=== 3. Mixing Foley, Voice & Score Ducking (-14 LUFS) ==="
$PY "$D/mix.py"

echo "=== 4. Rendering 24 fps Canvas Video Frames ==="
cd "$LEMO_ROOT"
node core/render/video.mjs "$D" --fps 24 --workers 3 --out "$D/out/video24.mp4"

echo "=== 5. Muxing Master Broadcast Video ==="
PATH="/usr/bin:/bin:/usr/sbin:/sbin:$PATH" \
sh core/render/mux.sh "$D/out/video24.mp4" "$D/mix.wav" "$D/closer_ad.mp4" 24 0

echo "=== 6. Generating Poster Image ==="
node core/render/still.mjs "$D" 0 --q scene=poster --out "$D" --prefix po_
mv -f "$D/po_0.jpg" "$D/poster.jpg"

echo "✓ Build complete: $D/closer_ad.mp4"
