"""
tests/unit/test_video_engine.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Comprehensive unit test suite for Milestone 1: Video Batch Generation Engine & Scripting Library.
Verifies Features F1 through F8:
- F1: Sector Scenario Templates & Registry
- F2: Dual Voice Synthesis Engine Specifications
- F3: Dynamic Foley & Audio Mixer (EBU R128 & Ducking)
- F4: Vertical Canvas 2D Stage Configuration
- F5: Safe-Zone Subtitle Renderer (subY = 1360)
- F6: Viral CTA Banner Hook (Y = 1530, 'CLOSER')
- F7: Multi-Format FFmpeg Exporter
- F8: Programmatic Batch Generator & CLI
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Ensure repo root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pytest

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
    FOLEY_DUCKING_DB,
    SECTORS,
)
from closer.video.scenarios.base import (
    Sector,
    Language,
    ScenarioLine,
    CharacterRigConfig,
    WhatsAppAsset,
    FoleyCue,
    ReelScenario,
)
from closer.video.scenarios.registry import (
    get_scenario,
    list_scenarios,
    list_sectors,
    get_round_robin_scenario,
    validate_all_scenarios,
)
from closer.video.audio.sfx import (
    SR,
    SFX_REGISTRY,
    generate_sfx,
    norm,
    compress,
    limit,
    add,
    stereo,
)
from closer.video.audio.synthesizer import (
    VoiceSynthesizer,
    DialogueLine,
    SynthesisResult,
)
from closer.video.audio.mixer import (
    AudioMixer,
    AudioMixResult,
    FoleyCue as MixFoleyCue,
)
from closer.video.exporter import (
    MultiFormatExporter,
    format_timestamp_srt,
    format_timestamp_vtt,
)
from closer.video.batch_generator import (
    BatchReelGenerator,
    RenderedReel,
    normalize_sector_name,
)


# ==============================================================================
# 1. Video Configuration & Safe-Zone Geometry (F4, F5, F6)
# ==============================================================================

class TestVideoConfigAndSafeZones:
    """Verifies vertical stage dimensions, safe-zone anchors, and audio mastering specs."""

    def test_canvas_dimensions_and_aspect_ratio(self):
        """F4: Canvas must be 1080x1920 9:16 vertical."""
        assert CANVAS_WIDTH == 1080
        assert CANVAS_HEIGHT == 1920
        assert ASPECT_RATIO == "9:16"
        assert abs((CANVAS_WIDTH / CANVAS_HEIGHT) - (9.0 / 16.0)) < 1e-4

    def test_safe_zone_subtitle_anchor(self):
        """F5: Subtitles must be anchored strictly at Y = 1360 with max width <= 680px."""
        assert SAFE_ZONE_SUBTITLE_Y == 1360
        assert SAFE_ZONE_SUBTITLE_MAX_W <= 680
        # Horizontal margins
        x_left = (CANVAS_WIDTH - SAFE_ZONE_SUBTITLE_MAX_W) / 2
        x_right = (CANVAS_WIDTH + SAFE_ZONE_SUBTITLE_MAX_W) / 2
        assert x_left == 200
        assert x_right == 880

    def test_safe_zone_cta_anchor_and_keyword(self):
        """F6: Viral CTA banner sits strictly at Y = 1530 and enforces 'CLOSER'."""
        assert SAFE_ZONE_CTA_Y == 1530
        assert SAFE_ZONE_SUBTITLE_Y < SAFE_ZONE_CTA_Y < 1600
        assert SAFE_ZONE_CTA_KEYWORD == "CLOSER"

    def test_audio_normalization_constants(self):
        """F3: EBU R128 loudness target is -14.0 LUFS, -1.2 dBTP ceiling, -8.5 dB ducking."""
        assert TARGET_LOUDNESS_LUFS == -14.0
        assert TARGET_TRUE_PEAK_DBTP == -1.2
        assert VOICE_DUCKING_DB == -8.5
        assert FOLEY_DUCKING_DB == -3.0


# ==============================================================================
# 2. Sector Scenario Templates & Registry (F1)
# ==============================================================================

class TestSectorScenariosAndRegistry:
    """Verifies all 10 presets across 5 Indian SMB business domains."""

    def test_registry_contains_10_presets(self):
        scenarios = list_scenarios()
        assert len(scenarios) >= 10
        sectors = list_sectors()
        assert len(sectors) == 5
        for s in sectors:
            assert len(list_scenarios(sector=s)) >= 2

    def test_all_scenarios_pass_validation(self):
        errors = validate_all_scenarios()
        assert len(errors) == 0, f"Validation errors found: {errors}"

    def test_each_scenario_duration_in_safe_window(self):
        for s in list_scenarios():
            dur = s.estimate_total_duration()
            assert 58.0 <= dur <= 78.0, f"{s.id} duration {dur}s outside [58, 78]"

    def test_subtitles_config_adheres_to_safe_zone_y1360(self):
        for s in list_scenarios():
            subs = s.to_subtitles_config()
            assert len(subs) > 0
            for item in subs:
                assert item["safe_zone_y"] == 1360
                assert item["box_width_max"] <= 680
                assert item["t1"] > item["t0"]

    def test_round_robin_rotation_order(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            served = [get_round_robin_scenario(tmp_path).sector for _ in range(5)]
            expected = [
                Sector.CLINICS,
                Sector.SOLAR,
                Sector.REALESTATE,
                Sector.EDTECH,
                Sector.AGENCY,
            ]
            assert served == expected
            # 6th iteration wraps back to clinics
            s6 = get_round_robin_scenario(tmp_path)
            assert s6.sector == Sector.CLINICS
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_sector_alias_normalization(self):
        assert normalize_sector_name("realestate") == "real_estate"
        assert normalize_sector_name("agency") == "b2b_agency"
        assert normalize_sector_name("clinics") == "clinics"


# ==============================================================================
# 3. Procedural Sound Effects Engine (F3)
# ==============================================================================

class TestProceduralSFXEngine:
    """Verifies all 24+ procedural SFX generators and DSP primitives."""

    def test_registry_contains_24_plus_generators(self):
        assert len(SFX_REGISTRY) >= 24
        # Verify key foley cues exist
        assert "telephone_ring" in SFX_REGISTRY
        assert "hangup_click" in SFX_REGISTRY
        assert "whatsapp_ping" in SFX_REGISTRY
        assert "sub_drop" in SFX_REGISTRY
        assert "comment_chime" in SFX_REGISTRY
        assert "coin_clink" in SFX_REGISTRY

    def test_all_generators_produce_valid_audio(self):
        for name in SFX_REGISTRY:
            audio = generate_sfx(name)
            assert isinstance(audio, np.ndarray)
            assert len(audio) > 0
            assert audio.dtype == np.float32
            assert np.max(np.abs(audio)) > 0.0

    def test_dsp_compress_and_limit(self):
        raw = np.sin(np.linspace(0, 100, 48000)).astype(np.float32) * 1.5
        compressed = compress(raw, thr=0.3, ratio=4.0)
        assert np.max(np.abs(compressed)) < np.max(np.abs(raw))
        limited = limit(compressed, ceiling=0.85)
        assert np.max(np.abs(limited)) <= 0.851

    def test_add_with_panning_and_at_time(self):
        canvas = np.zeros((48000, 2), dtype=np.float32)
        tone = np.ones(24000, dtype=np.float32)
        add(canvas, tone, at_time=0.25, gain=0.5, pan=0.0)
        assert canvas[12000, 0] > 0.0
        assert canvas[12000, 1] > 0.0


# ==============================================================================
# 4. Speech Synthesis & Durations (F2)
# ==============================================================================

class TestVoiceSynthesizer:
    """Verifies VoiceSynthesizer voice routing, silence trimming, and peak normalization."""

    def test_voice_routing_logic(self):
        synth = VoiceSynthesizer()
        assert synth.is_kokoro_voice("af_heart") is True
        assert synth.is_kokoro_voice("af_bella") is True
        assert synth.is_kokoro_voice("signature") is True
        assert synth.is_kokoro_voice("ta-IN-PallaviNeural") is False
        assert synth.is_kokoro_voice("hi-IN-SwaraNeural") is False

    def test_silence_trimming(self):
        synth = VoiceSynthesizer()
        sr = 48000
        # 0.5s silence + 1.0s tone + 0.5s silence
        tone = np.sin(2 * np.pi * 440 * np.arange(sr) / sr).astype(np.float32)
        padded = np.concatenate([np.zeros(sr // 2, dtype=np.float32), tone, np.zeros(sr // 2, dtype=np.float32)])
        trimmed = synth.trim_silence(padded, sr, top_db=30.0, pad_sec=0.05)
        assert len(trimmed) < len(padded)
        assert len(trimmed) >= sr

    def test_peak_normalization(self):
        synth = VoiceSynthesizer()
        tone = np.sin(np.linspace(0, 10, 1000)).astype(np.float32) * 0.4
        normed = synth.normalize_peak(tone, target_db=-1.2)
        expected_linear = 10.0 ** (-1.2 / 20.0)
        assert abs(float(np.max(np.abs(normed))) - expected_linear) < 1e-4


# ==============================================================================
# 5. Audio Mixer & EBU R128 Loudness (F3)
# ==============================================================================

class TestAudioMixer:
    """Verifies AudioMixer timeline sequencing, ducking, and EBU R128 master limiter."""

    def test_timeline_sequencer_conversational_pauses(self):
        mixer = AudioMixer(default_pause_sec=0.35, initial_delay_sec=0.40)
        line_ids = ["line1", "line2", "line3"]
        durations = {"line1": 2.0, "line2": 3.0, "line3": 2.5}
        timeline, cuts, total = mixer.sequence_timeline(line_ids, durations)

        assert timeline["line1"]["start"] == 0.40
        assert timeline["line1"]["end"] == 2.40
        assert timeline["line2"]["start"] == round(2.40 + 0.35, 3)
        assert cuts[0] == 0.0
        assert cuts[1] == 0.40

    def test_dynamic_ducking_curves_drop_during_speech(self):
        mixer = AudioMixer(music_duck_db=-8.5)
        total_samples = 48000 * 10
        speech_intervals = [(1.0, 3.0), (5.0, 7.0)]
        duck_music, duck_foley = mixer.generate_ducking_curves(speech_intervals, total_samples)

        # Before speech: 1.0 (0 dB)
        assert abs(duck_music[int(0.5 * 48000)] - 1.0) < 0.05
        # During speech: ducked to ~0.375 (-8.5 dB)
        expected_duck = 10.0 ** (-8.5 / 20.0)
        assert abs(duck_music[int(2.0 * 48000)] - expected_duck) < 0.05


# ==============================================================================
# 6. Multi-Format Exporter (F7)
# ==============================================================================

class TestMultiFormatExporter:
    """Verifies subtitle generation and timestamp formatters."""

    def test_timestamp_formatters(self):
        assert format_timestamp_srt(65.123) == "00:01:05,123"
        assert format_timestamp_vtt(65.123) == "00:01:05.123"

    def test_subtitles_export_srt_and_vtt(self, tmp_path):
        exporter = MultiFormatExporter()
        subs = [
            {"t0": 0.5, "t1": 3.2, "text": "Doctors: why miss 40% of leads?"},
            {"t0": 3.4, "t1": 6.8, "text": "CLOSER AI dials in 45 seconds."}
        ]
        srt_file = tmp_path / "test.srt"
        vtt_file = tmp_path / "test.vtt"

        exporter.export_subtitles_srt(subs, str(srt_file))
        exporter.export_subtitles_vtt(subs, str(vtt_file))

        assert srt_file.exists()
        assert vtt_file.exists()

        srt_content = srt_file.read_text(encoding="utf-8")
        assert "00:00:00,500 --> 00:00:03,200" in srt_content
        assert "Doctors: why miss 40% of leads?" in srt_content


# ==============================================================================
# 7. Batch Generator & CLI Manifest (F8)
# ==============================================================================

class TestBatchGenerator:
    """Verifies batch generation orchestrator, RenderedReel schema, and daily_reel.json."""

    def test_batch_generator_dry_run(self, tmp_path):
        generator = BatchReelGenerator(output_base_dir=tmp_path, dry_run=True)
        manifest = generator.generate_batch(
            target_date="2026-11-15",
            sector="clinics",
            count=1,
            render_mode="dry-run",
        )

        assert manifest["total_reels"] == 1
        reel = manifest["reels"][0]
        assert reel["industry"] == "clinics"
        assert reel["cta_keyword"] == "CLOSER"
        assert 58.0 <= reel["duration_seconds"] <= 78.0
        assert reel["metadata"]["safe_zone_subtitle_y"] == 1360
        assert reel["metadata"]["safe_zone_cta_y"] == 1530

        # Check files exist
        assert os.path.exists(reel["video_path"])
        assert os.path.exists(reel["cover_path"])
        assert os.path.exists(reel["subtitles_path"])

        # Check daily_reel.json
        daily_json = tmp_path / "2026-11-15" / "daily_reel.json"
        assert daily_json.exists()
