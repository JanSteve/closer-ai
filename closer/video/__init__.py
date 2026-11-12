"""
closer.video
~~~~~~~~~~~~
CLOSER AI Video Batch Generation Engine & Scripting Library.
Provides procedural scenario templates, dual neural voice synthesis (Kokoro ONNX + Edge-TTS),
dynamic Foley audio mixer with EBU R128 loudness normalization, Canvas 2D motion graphics
stage, safe-zone subtitles (subY = 1360), viral CTA hooks (Y = 1530), and multi-format FFmpeg exporter.
"""

from closer.video.config import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    ASPECT_RATIO,
    DEFAULT_FPS,
    SAFE_ZONE_SUBTITLE_Y,
    SAFE_ZONE_SUBTITLE_MAX_W,
    SAFE_ZONE_CTA_Y,
    SAFE_ZONE_CTA_KEYWORD,
    TARGET_LOUDNESS_LUFS,
    TARGET_TRUE_PEAK_DBTP,
    VOICE_DUCKING_DB,
)
try:
    from closer.video.batch_generator import RenderedReel, BatchReelGenerator
except ImportError:
    RenderedReel = None
    BatchReelGenerator = None

__all__ = [
    "CANVAS_WIDTH",
    "CANVAS_HEIGHT",
    "ASPECT_RATIO",
    "DEFAULT_FPS",
    "SAFE_ZONE_SUBTITLE_Y",
    "SAFE_ZONE_SUBTITLE_MAX_W",
    "SAFE_ZONE_CTA_Y",
    "SAFE_ZONE_CTA_KEYWORD",
    "TARGET_LOUDNESS_LUFS",
    "TARGET_TRUE_PEAK_DBTP",
    "VOICE_DUCKING_DB",
    "RenderedReel",
    "BatchReelGenerator",
]
