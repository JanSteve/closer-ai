#!/bin/bash
# tools/export_suite.sh — Automated Video Engine Multi-Format Transcoder & Packager
# Converts master closer_reel.mp4 into all social media distribution formats:
# 1. 720p Quick-Share (WhatsApp/Telegram mobile compressed)
# 2. 1080x1080 Square Feed (LinkedIn/Facebook/Meta with blurred background borders)
# 3. 320 kbps Master Audio Extract (MP3)
# 4. SRT / WebVTT Closed Captions
# 5. Full Production Master Assets ZIP
set -e

D="$(cd "$(dirname "$0")/.." && pwd)"
DEMOS="$D/demos"
FFMPEG="${FFMPEG:-/Users/janstevedaniel/.local/bin/ffmpeg}"

echo "=== CLOSER AI Video Engine: Multi-Format Transcoding ==="

if [ ! -f "$DEMOS/closer_reel.mp4" ]; then
  echo "Error: $DEMOS/closer_reel.mp4 not found. Please render the master reel first."
  exit 1
fi

echo "[1/4] Transcoding 720x1280 Mobile / WhatsApp Quick-Share MP4..."
"$FFMPEG" -y -loglevel error -i "$DEMOS/closer_reel.mp4" \
  -vf "scale=720:1280" \
  -c:v libx264 -preset veryfast -crf 23 \
  -c:a aac -b:a 128k -movflags +faststart \
  "$DEMOS/closer_reel_720p.mp4"

echo "[2/4] Transcoding 1080x1080 1:1 Square Feed (Blurred Letterbox) MP4..."
"$FFMPEG" -y -loglevel error -i "$DEMOS/closer_reel.mp4" \
  -filter_complex "[0:v]scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,boxblur=25:5,eq=brightness=-0.15[bg];[0:v]scale=-1:1080[fg];[bg][fg]overlay=(W-w)/2:0" \
  -c:v libx264 -preset veryfast -crf 22 -c:a copy \
  "$DEMOS/closer_reel_square.mp4"

echo "[3/4] Extracting 320 kbps Master Broadcast Audio MP3..."
"$FFMPEG" -y -loglevel error -i "$DEMOS/closer_reel.mp4" \
  -vn -c:a libmp3lame -b:a 320k \
  "$DEMOS/closer_reel_audio.mp3"

echo "[4/4] Syncing metadata & captions to mobile dist..."
mkdir -p "$D/closer_mobile/dist/demos"
cp -f "$DEMOS"/*.srt "$DEMOS"/*.vtt "$DEMOS"/CAPTION.txt "$DEMOS"/daily_reel.json "$DEMOS"/*poster.jpg "$D/closer_mobile/dist/demos/"

echo "✓ Video Engine Export Suite complete! All formats ready in demos/"
