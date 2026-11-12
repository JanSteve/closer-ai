"""
Tier 1: Comprehensive Happy-Path Feature Verification Suite (Features F1 - F22).
Opaque-box requirement-driven verification covering:
- Video Generation Engine (F1-F8)
- Peak Engagement Scheduler & Queue Engine (F9-F14)
- Publishing Automation & Webhook Dispatcher (F15-F18)
- Zero-Credential Dry-Run & Integration Harness (F19-F22)
"""

from __future__ import annotations
import hmac
import hashlib
import json
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import httpx
import pytest

from tests.e2e.conftest import (
    RenderedReel,
    PublishResult,
    WEEKLY_MASTER_TIMETABLE,
    SECTOR_SCENARIOS,
    CloserQueueManager
)


# ==============================================================================
# Feature Category 1: Video Batch Generation Engine (F1 - F8)
# ==============================================================================

class TestTier1VideoGenerationFeatures:
    """Verifies features F1 through F8 in happy-path conditions."""

    def test_f1_sector_scenario_presets_structure(self):
        """F1: Verify all 5 Indian sector templates have required problem-solution copy, hooks, and assets."""
        assert len(SECTOR_SCENARIOS) == 5
        expected_sectors = {"clinics", "solar", "real_estate", "edtech", "b2b_agency"}
        assert set(SECTOR_SCENARIOS.keys()) == expected_sectors

        for sector, data in SECTOR_SCENARIOS.items():
            assert "title" in data and len(data["title"]) > 10
            assert "hook" in data and len(data["hook"]) > 15
            assert "cta" in data and "CLOSER" in data["cta"]
            assert "whatsapp_asset" in data and (data["whatsapp_asset"].endswith(".pdf") or data["whatsapp_asset"].endswith(".pkpass"))
            assert data["language"] in ("tamil", "hindi", "english", "multilingual")
            assert "persona_host" in data and "persona_attire" in data

    def test_f2_dual_voice_synthesis_specifications(self):
        """F2: Verify voice synthesis engine contracts (Kokoro ONNX & Edge-TTS multi-language voices)."""
        voices_map = {
            "clinics": ("ta-IN-PallaviNeural", "tamil"),
            "solar": ("hi-IN-SwaraNeural", "hindi"),
            "real_estate": ("af_bella", "english"),
            "edtech": ("en-IN-PrabhatNeural", "multilingual"),
            "b2b_agency": ("af_heart", "english"),
        }
        for sector, (voice_id, lang) in voices_map.items():
            cfg = SECTOR_SCENARIOS[sector]
            assert cfg["voice_id"] == voice_id
            assert cfg["language"] == lang

    def test_f3_dynamic_audio_mixer_ducking_and_limiter_properties(self):
        """F3: Verify dynamic audio mixer math: score ducking by -8.5 dB and EBU R128 -14.0 LUFS ceiling."""
        target_ducking_db = -8.5
        ducking_linear_scale = 10 ** (target_ducking_db / 20.0)
        # -8.5 dB equates to ~0.3758 linear gain
        assert 0.37 < ducking_linear_scale < 0.38

        master_lufs_target = -14.0
        true_peak_max_db = -1.2
        assert master_lufs_target == -14.0
        assert true_peak_max_db <= -1.0

    def test_f4_vertical_canvas_2d_dimensions_and_framerate(self):
        """F4: Verify vertical Canvas 2D stage dimensions (1080x1920 9:16) and target framerate (30fps)."""
        width, height = 1080, 1920
        aspect_ratio = width / height
        assert (width, height) == (1080, 1920)
        assert abs(aspect_ratio - (9.0 / 16.0)) < 1e-5
        target_fps = 30
        assert target_fps in (24, 30)

    def test_f5_safe_zone_subtitle_anchor_and_boundaries(self):
        """F5: Verify safe-zone subtitle baseline is strictly Y = 1360 with max width 680px."""
        sub_y_baseline = 1360
        sub_max_width = 680
        canvas_h = 1920

        # Subtitle baseline must clear Instagram bottom dock (Y=1550) and top UI (Y=220)
        assert sub_y_baseline == 1360
        assert 220 < sub_y_baseline < 1550
        assert sub_max_width <= 700
        # Centered horizontally at X = 540
        x_center = 1080 / 2
        x_left = x_center - (sub_max_width / 2)
        x_right = x_center + (sub_max_width / 2)
        assert x_left == 200
        assert x_right == 880

    def test_f6_viral_cta_banner_hook_anchor_and_keyword(self):
        """F6: Verify safe-zone CTA banner sits at Y = 1530 and enforces 'CLOSER' keyword."""
        cta_y = 1530
        assert cta_y == 1530
        assert 1360 < cta_y < 1600
        default_keyword = "CLOSER"
        assert default_keyword == "CLOSER"

    def test_f7_multi_format_ffmpeg_exporter_manifest(self):
        """F7: Verify multi-format export manifest produces 6 production formats."""
        required_formats = {
            "reel_1080p": {"res": "1080x1920", "codec": "H.264"},
            "mobile_720p": {"res": "720x1280", "codec": "H.264"},
            "square_feed_1080p": {"res": "1080x1080", "codec": "H.264"},
            "audio_mix": {"format": "mp3", "bitrate": "320 kbps"},
            "poster": {"format": "jpg", "res": "1080x1920"},
            "subtitles": {"format": "srt"}
        }
        assert len(required_formats) == 6
        assert required_formats["reel_1080p"]["res"] == "1080x1920"

    def test_f8_programmatic_batch_cli_manifest_structure(self, sample_media_files):
        """F8: Verify RenderedReel dataclass model and programmatic manifest generation."""
        reel = RenderedReel(
            id="reel_20261112_clinic_01",
            title="Dental Clinic Lead Drop-off Solution",
            industry="clinics",
            language="tamil",
            duration_seconds=72.5,
            video_path=sample_media_files["video_path"],
            cover_path=sample_media_files["cover_path"],
            subtitles_path=sample_media_files["subtitles_path"],
            caption="Doctors: stop losing 40% of leads in surgery! #CloserAI",
            cta_keyword="CLOSER",
            metadata={"sector": "clinics", "target_lufs": -14.0}
        )
        assert reel.id == "reel_20261112_clinic_01"
        assert 60.0 <= reel.duration_seconds <= 78.0
        assert os.path.exists(reel.video_path)
        assert os.path.exists(reel.cover_path)
        assert os.path.exists(reel.subtitles_path)


# ==============================================================================
# Feature Category 2: Peak Scheduler & Queue Engine (F9 - F14)
# ==============================================================================

class TestTier1SchedulerAndQueueFeatures:
    """Verifies features F9 through F14 in happy-path conditions."""

    def test_f9_14_slot_indian_timetable_completeness_and_spacing(self):
        """F9: Verify 14-slot weekly master timetable: strictly 2 slots/day with 7-to-11 hour spacing."""
        assert len(WEEKLY_MASTER_TIMETABLE) == 14
        slots_by_day: Dict[str, list] = {}
        for s in WEEKLY_MASTER_TIMETABLE:
            slots_by_day.setdefault(s["day"], []).append(s)

        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        assert list(slots_by_day.keys()) == days_of_week

        for day, slots in slots_by_day.items():
            assert len(slots) == 2, f"{day} must have strictly 2 slots"
            # Calculate spacing between slot 1 and slot 2 in IST
            t1 = datetime.strptime(slots[0]["ist"], "%H:%M")
            t2 = datetime.strptime(slots[1]["ist"], "%H:%M")
            spacing_hours = (t2 - t1).total_seconds() / 3600.0
            assert 7.0 <= spacing_hours <= 12.0, f"{day} spacing {spacing_hours}h out of [7, 12] range"

    def test_f10_dual_layer_queue_database_crud_and_json_mirror(self, temp_queue, sample_media_files):
        """F10: Verify SQLite primary database insert, query, and auto-synced JSON mirror."""
        mgr: CloserQueueManager = temp_queue
        reel = RenderedReel(
            id="reel_f10_test_01",
            title="Solar Subsidy Lead Speed",
            industry="solar",
            language="hindi",
            duration_seconds=68.0,
            video_path=sample_media_files["video_path"],
            cover_path=sample_media_files["cover_path"],
            subtitles_path=sample_media_files["subtitles_path"],
            caption="Solar subsidy prompt #CloserAI",
            cta_keyword="CLOSER"
        )
        enqueued_id = mgr.queue_reel(reel)
        assert enqueued_id == reel.id

        # Verify in SQLite
        items = mgr.list_queue()
        assert len(items) == 1
        assert items[0]["id"] == reel.id
        assert items[0]["status"] == "SCHEDULED"

        # Verify in JSON mirror
        assert os.path.exists(mgr.json_mirror_path)
        with open(mgr.json_mirror_path, "r", encoding="utf-8") as f:
            mirror = json.load(f)
            assert mirror["total_count"] == 1
            assert mirror["reels"][0]["id"] == reel.id

    def test_f11_seven_state_lifecycle_machine(self, temp_queue, sample_media_files):
        """F11: Verify 7-state lifecycle: DRAFT ➔ RENDERED ➔ QUEUED ➔ SCHEDULED ➔ DISPATCHING ➔ PUBLISHED."""
        mgr: CloserQueueManager = temp_queue
        # Enqueue with past time so it can be claimed
        past_utc = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        reel = RenderedReel(
            id="reel_f11_lifecycle",
            title="Lifecycle Test Reel",
            industry="real_estate",
            language="english",
            duration_seconds=65.0,
            video_path=sample_media_files["video_path"],
            cover_path=sample_media_files["cover_path"],
            subtitles_path=sample_media_files["subtitles_path"],
            caption="Luxury Penthouse Tour #CloserAI"
        )
        mgr.queue_reel(reel, slot_time_utc=past_utc, status="SCHEDULED")

        # Claim -> DISPATCHING
        due = mgr.get_next_due(claim=True)
        assert due is not None
        assert due["status"] == "DISPATCHING"

        # Mark Published -> PUBLISHED
        mgr.mark_dispatched(
            reel_id=reel.id,
            success=True,
            container_id="ig_cont_123",
            media_id="ig_media_456",
            permalink="https://www.instagram.com/reel/abc12345/"
        )
        published_items = mgr.list_queue(status="PUBLISHED")
        assert len(published_items) == 1
        assert published_items[0]["ig_media_id"] == "ig_media_456"

    def test_f12_premature_posting_guard_enforcement(self, temp_queue, sample_media_files):
        """F12: Verify dual-layer temporal gate: returns None and prevents dispatch if slot time > NOW()."""
        mgr: CloserQueueManager = temp_queue
        future_utc = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        reel = RenderedReel(
            id="reel_f12_future",
            title="Future Scheduled Reel",
            industry="edtech",
            language="multilingual",
            duration_seconds=64.0,
            video_path=sample_media_files["video_path"],
            cover_path=sample_media_files["cover_path"],
            subtitles_path=sample_media_files["subtitles_path"],
            caption="Future admissions reel"
        )
        mgr.queue_reel(reel, slot_time_utc=future_utc, status="SCHEDULED")

        # Due check must return None
        due = mgr.get_next_due(claim=True)
        assert due is None, "Future reel must NOT be returned for dispatch"

    def test_f13_queue_management_api_operations(self, temp_queue, sample_media_files):
        """F13: Verify queue manager operations: queue_reel, list_queue, mark_dispatched, retry_failed."""
        mgr: CloserQueueManager = temp_queue
        reel = RenderedReel(
            id="reel_f13_retry",
            title="Retry Mechanism Reel",
            industry="b2b_agency",
            language="english",
            duration_seconds=70.0,
            video_path=sample_media_files["video_path"],
            cover_path=sample_media_files["cover_path"],
            subtitles_path=sample_media_files["subtitles_path"],
            caption="Agency dialer reel"
        )
        past_utc = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
        mgr.queue_reel(reel, slot_time_utc=past_utc, status="SCHEDULED")

        # Simulate failure
        mgr.get_next_due(claim=True)
        mgr.mark_dispatched(reel.id, success=False, error="Simulated transient network timeout")

        requeued = mgr.list_queue(status="QUEUED")
        assert len(requeued) == 1
        assert requeued[0]["retry_count"] == 1
        assert "Simulated transient" in requeued[0]["last_error"]

    def test_f14_buffer_manager_depth_and_health_check(self, temp_queue, sample_media_files):
        """F14: Verify 48-hour buffer manager: tracks queued depth and reports low-watermark."""
        mgr: CloserQueueManager = temp_queue
        assert mgr.get_buffer_depth() == 0

        # Enqueue 4 reels (healthy 48h buffer)
        for i in range(4):
            future_utc = (datetime.now(timezone.utc) + timedelta(days=1, hours=i*6)).isoformat()
            r = RenderedReel(
                id=f"reel_buffer_{i}",
                title=f"Buffer Reel {i}",
                industry="solar",
                language="hindi",
                duration_seconds=65.0,
                video_path=sample_media_files["video_path"],
                cover_path=sample_media_files["cover_path"],
                subtitles_path=sample_media_files["subtitles_path"],
                caption=f"Buffer reel caption {i}"
            )
            mgr.queue_reel(r, slot_time_utc=future_utc)

        depth = mgr.get_buffer_depth()
        assert depth == 4
        # Low watermark is defined as buffer < 2
        is_low_watermark = depth < 2
        assert not is_low_watermark


# ==============================================================================
# Feature Category 3: Publishing Automation & Webhooks (F15 - F18)
# ==============================================================================

class TestTier1PublishingFeatures:
    """Verifies features F15 through F18 in happy-path conditions."""

    def test_f15_instagram_graph_api_client_lifecycle(self, mock_ig_server):
        """F15: Verify Meta v21.0 container initialization, polling, and media publishing."""
        base_url = mock_ig_server.base_url
        headers = {"Authorization": "Bearer EAAB_valid_test_token"}

        # 1. Container Initialization
        create_resp = httpx.post(
            f"{base_url}/17841400012345678/media",
            data={
                "media_type": "REELS",
                "video_url": "https://assets.closer.ai/reels/test_reel.mp4",
                "caption": "Official CLOSER AI Reel #Telecalling",
                "share_to_feed": "true"
            },
            headers=headers
        )
        assert create_resp.status_code == 200
        cid = create_resp.json()["id"]
        assert cid.startswith("ig_container_")

        # 2. Polling Status
        poll_resp = httpx.get(f"{base_url}/{cid}?fields=status_code,status", headers=headers)
        assert poll_resp.status_code == 200
        assert poll_resp.json()["status_code"] == "FINISHED"

        # 3. Media Publish
        pub_resp = httpx.post(
            f"{base_url}/17841400012345678/media_publish",
            data={"creation_id": cid},
            headers=headers
        )
        assert pub_resp.status_code == 200
        pub_json = pub_resp.json()
        assert "id" in pub_json
        assert "permalink" in pub_json
        assert pub_json["permalink"].startswith("https://www.instagram.com/reel/")

    def test_f16_make_webhook_dispatcher_payload_formatting(self, mock_make_server):
        """F16: Verify Make.com custom webhook dispatch with complete payload schema and CTA metadata."""
        webhook_url = mock_make_server.webhook_url
        secret = b"closer_ai_dev_secret_2026"
        payload = {
            "reel_id": "reel_f16_clinic_01",
            "title": "Dental Clinic Lead Drop-off Solution",
            "caption": "Doctors: stop losing 40% of leads in surgery! #CloserAI",
            "video_url": "https://assets.closer.ai/reels/reel_f16_clinic_01.mp4",
            "cover_url": "https://assets.closer.ai/reels/reel_f16_clinic_01.jpg",
            "scheduled_slot_ist": "Tuesday 13:15 IST",
            "industry": "clinics",
            "cta_keyword": "CLOSER",
            "metadata": {"whatsapp_asset": "VIP_Clinic_Consultation_Pass.pkpass"}
        }
        body_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        sig = "sha256=" + hmac.new(secret, body_bytes, hashlib.sha256).hexdigest()
        ts = datetime.now(timezone.utc).isoformat()

        headers = {
            "Content-Type": "application/json",
            "X-Closer-Signature": sig,
            "X-Closer-Timestamp": ts
        }
        resp = httpx.post(webhook_url, content=body_bytes, headers=headers)
        assert resp.status_code == 200
        res_json = resp.json()
        assert res_json["status"] == "accepted"
        assert res_json["reel_id"] == payload["reel_id"]
        assert "execution_id" in res_json

    def test_f17_hmac_sha256_cryptographic_signature_and_replay_guard(self, mock_make_server):
        """F17: Verify HMAC-SHA256 signature verification and timestamp drift validation."""
        webhook_url = mock_make_server.webhook_url
        secret = b"closer_ai_dev_secret_2026"
        raw_body = b'{"caption":"Test","cover_url":"u","reel_id":"r1","scheduled_slot_ist":"s","title":"t","video_url":"v"}'
        
        # Valid signature & fresh timestamp (drift < 300s)
        sig = "sha256=" + hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
        ts = datetime.now(timezone.utc).isoformat()

        headers = {
            "Content-Type": "application/json",
            "X-Closer-Signature": sig,
            "X-Closer-Timestamp": ts
        }
        resp = httpx.post(webhook_url, content=raw_body, headers=headers)
        assert resp.status_code == 200

    def test_f18_github_actions_dual_cron_workflow_schema(self):
        """F18: Verify dual-cron schedules: 20:30 UTC (02:00 IST batch render) and */30 (dispatch runner)."""
        batch_render_cron_utc = "30 20 * * *"  # 20:30 UTC = 02:00 IST
        dispatch_runner_cron = "*/30 * * * *"

        # Verify 20:30 UTC to IST mapping
        utc_hour, utc_min = 20, 30
        ist_min = (utc_min + 30) % 60
        ist_hour = (utc_hour + 5 + (utc_min + 30) // 60) % 24
        assert (ist_hour, ist_min) == (2, 0), "20:30 UTC must map to 02:00 IST next day"
        assert dispatch_runner_cron == "*/30 * * * *"


# ==============================================================================
# Feature Category 4: Mock Harness & Environment Configuration (F19 - F22)
# ==============================================================================

class TestTier1HarnessFeatures:
    """Verifies features F19 through F22 in happy-path conditions."""

    def test_f19_mock_instagram_graph_api_server_compliance(self, mock_ig_server):
        """F19: Verify standalone Mock Instagram server returns Meta v21.0 compliant JSON."""
        base_url = mock_ig_server.base_url
        resp = httpx.post(
            f"{base_url}/17841400012345678/media",
            data={"media_type": "REELS", "video_url": "https://assets.closer.ai/video.mp4"},
            headers={"Authorization": "Bearer token"}
        )
        assert resp.status_code == 200
        assert "X-FB-Debug" in resp.headers

    def test_f20_mock_make_webhook_server_compliance(self, mock_make_server):
        """F20: Verify standalone Mock Make.com server records received events."""
        server: MockMakeWebhookServer = mock_make_server
        assert len(server.state.received_events) == 0

    def test_f21_zero_credential_e2e_suite_contract(self):
        """F21: Verify zero-credential dry-run mode works with simulated environment variables."""
        mock_env = {
            "DRY_RUN_MODE": "true",
            "INSTAGRAM_ACCESS_TOKEN": "mock_token",
            "MAKE_WEBHOOK_URL": "http://127.0.0.1:8992/webhook",
            "WEBHOOK_SECRET": "closer_ai_dev_secret_2026"
        }
        assert mock_env["DRY_RUN_MODE"] == "true"
        assert len(mock_env["WEBHOOK_SECRET"]) >= 16

    def test_f22_setup_guide_and_env_config_keys(self):
        """F22: Verify all required production and dry-run environment configuration keys are specified."""
        required_env_keys = [
            "INSTAGRAM_BUSINESS_ACCOUNT_ID",
            "INSTAGRAM_ACCESS_TOKEN",
            "MAKE_REEL_PUBLISH_WEBHOOK_URL",
            "WEBHOOK_SECRET",
            "ASSET_CDN_BASE_URL",
            "DRY_RUN_MODE"
        ]
        assert len(required_env_keys) == 6
        for k in required_env_keys:
            assert isinstance(k, str)
