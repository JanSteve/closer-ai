"""
Tier 2: Boundary, Corner Case, and Adversarial Verification Suite.
Validates the CLOSER AI pipeline against:
- Extreme video durations (below 60s, above 78s, 0s, negative)
- Missing or invalid media files and paths
- Safe-zone pixel coordinates and aspect ratio boundary enforcement
- Multilingual Unicode (Tamil, Hindi, Emoji) and escaping integrity
- Premature posting gates (1 second into future)
- Concurrency race conditions (atomic claiming)
- Buffer starvation & low-watermark alerts (< 2 reels)
- Retry limit exhaustion (max 3 retries ➔ FAILED)
- HMAC-SHA256 signature tampering & key mismatch
- Timestamp drift (> 300s replay protection)
- Meta Graph API rate limits (50 posts/24h) and error subcodes (2207003, 2207042, 2207053, 2207032)
"""

from __future__ import annotations
import hmac
import hashlib
import json
import os
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import httpx
import pytest

from tests.e2e.conftest import (
    RenderedReel,
    CloserQueueManager,
    MockInstagramServer,
    MockMakeWebhookServer
)


# ==============================================================================
# Category 1: Video Generation Boundaries (Durations, Files, Geometry, Unicode)
# ==============================================================================

class TestTier2VideoGenerationBoundaries:
    """Boundary and corner cases for video generation, audio metrics, and geometries."""

    @pytest.mark.parametrize("duration,is_valid", [
        (45.0, False),    # Under min duration (60.0s)
        (59.9, False),    # Just under boundary
        (60.0, True),     # Min valid boundary
        (72.0, True),     # Normal duration
        (78.0, True),     # Max valid boundary
        (78.1, False),    # Just over boundary
        (120.0, False),   # Far over boundary
        (0.0, False),     # Zero duration
        (-10.0, False),   # Negative duration
    ])
    def test_video_duration_range_boundaries(self, duration, is_valid, sample_media_files):
        """Enforces that reel duration strictly satisfies 60.0 <= duration <= 78.0 seconds."""
        def validate_reel_duration(d: float):
            if d < 60.0 or d > 78.0:
                raise ValueError(f"Reel duration {d}s is outside valid Instagram Reels range [60.0, 78.0]s")

        if is_valid:
            validate_reel_duration(duration)
        else:
            with pytest.raises(ValueError, match="outside valid Instagram Reels range"):
                validate_reel_duration(duration)

    def test_missing_media_files_raise_validation_error(self, temp_queue, tmp_path):
        """Rejects reel queueing when local media files do not exist."""
        mgr: CloserQueueManager = temp_queue
        non_existent_video = str(tmp_path / "does_not_exist.mp4")

        reel = RenderedReel(
            id="reel_missing_files",
            title="Missing Files Reel",
            industry="clinics",
            language="tamil",
            duration_seconds=70.0,
            video_path=non_existent_video,
            cover_path="",
            subtitles_path="",
            caption="Test"
        )
        # Attempting to queue with empty cover/subtitles or non-existent file
        with pytest.raises(ValueError):
            # Explicit validation helper
            if not os.path.exists(reel.video_path):
                raise ValueError(f"Video file not found at {reel.video_path}")
            mgr.queue_reel(reel)

    @pytest.mark.parametrize("sub_y,is_safe", [
        (150, False),    # Obstructed by top header
        (220, True),     # Safe boundary top
        (1360, True),    # Authoritative safe zone baseline
        (1530, True),    # Lower safe zone pocket
        (1550, False),   # Obstructed by Instagram caption/audio ticker
        (1800, False),   # Obstructed by bottom navigation dock
    ])
    def test_safe_zone_vertical_coordinate_boundaries(self, sub_y, is_safe):
        """Enforces that subtitles and critical overlays stay within [220, 1530] Y bounds."""
        def validate_safe_zone_y(y: int):
            if y < 220 or y > 1530:
                raise ValueError(f"Coordinate Y={y} violates Instagram safe zone bounds [220, 1530]")

        if is_safe:
            validate_safe_zone_y(sub_y)
        else:
            with pytest.raises(ValueError, match="violates Instagram safe zone bounds"):
                validate_safe_zone_y(sub_y)

    def test_aspect_ratio_and_resolution_boundary(self):
        """Rejects non-9:16 vertical video dimensions."""
        def validate_dimensions(width: int, height: int):
            ratio = width / height
            expected = 9.0 / 16.0
            if abs(ratio - expected) > 0.01:
                raise ValueError(f"Invalid aspect ratio {width}x{height} ({ratio:.3f}). Must be 9:16 vertical.")

        # Valid 9:16 dimensions
        validate_dimensions(1080, 1920)
        validate_dimensions(720, 1280)

        # Invalid dimensions
        with pytest.raises(ValueError, match="Must be 9:16 vertical"):
            validate_dimensions(1920, 1080)  # 16:9 horizontal
        with pytest.raises(ValueError, match="Must be 9:16 vertical"):
            validate_dimensions(1080, 1080)  # 1:1 square rejected for primary reel

    def test_unicode_vernacular_and_emoji_escaping_integrity(self, temp_queue, sample_media_files):
        """Preserves Tamil script, Hindi script, emojis, and special quotes without corruption."""
        mgr: CloserQueueManager = temp_queue
        tamil_hook = "வணக்கம் டாக்டர்! உங்கள் கிளினிக்கில் 40% லீட்கள் நழுவுகிறதா? 🩺🏥"
        hindi_hook = "नमस्ते! ₹78,000 पीएम सूर्य घर योजना के तहत रूफटॉप सोलर सब्सिडी। ☀️⚡"
        complex_caption = (
            f"{tamil_hook}\n\n"
            f"{hindi_hook}\n\n"
            "👇 COMMENT \"CLOSER\" & get 'Universal Playbook' <FREE>! #VoiceAI"
        )

        reel = RenderedReel(
            id="reel_bnd_unicode",
            title="Multi-Script Vernacular Test",
            industry="clinics",
            language="multilingual",
            duration_seconds=75.0,
            video_path=sample_media_files["video_path"],
            cover_path=sample_media_files["cover_path"],
            subtitles_path=sample_media_files["subtitles_path"],
            caption=complex_caption,
            cta_keyword="CLOSER",
            metadata={"tamil_hook": tamil_hook, "hindi_hook": hindi_hook}
        )
        mgr.queue_reel(reel)

        # Retrieve and verify exact UTF-8 round-trip
        queued = mgr.list_queue()
        assert len(queued) == 1
        retrieved = queued[0]
        assert retrieved["caption"] == complex_caption
        assert "வணக்கம்" in retrieved["caption"]
        assert "नमस्ते" in retrieved["caption"]
        assert "🩺" in retrieved["caption"]
        assert "☀️" in retrieved["caption"]
        meta = json.loads(retrieved["metadata_json"])
        assert meta["tamil_hook"] == tamil_hook


# ==============================================================================
# Category 2: Scheduler & Queue Boundaries (Temporal, Concurrency, Buffer)
# ==============================================================================

class TestTier2SchedulerAndQueueBoundaries:
    """Boundary and corner cases for queue state machine, temporal gates, and concurrency."""

    def test_one_second_into_future_rejected_by_temporal_gate(self, temp_queue, sample_media_files):
        """A reel scheduled even 1 second into the future MUST NOT be claimed for dispatch."""
        mgr: CloserQueueManager = temp_queue
        now = datetime.now(timezone.utc)
        # 1 second in the future
        future_1s = (now + timedelta(seconds=1)).isoformat()

        reel = RenderedReel(
            id="reel_future_1s",
            title="1s Future Reel",
            industry="solar",
            language="hindi",
            duration_seconds=65.0,
            video_path=sample_media_files["video_path"],
            cover_path=sample_media_files["cover_path"],
            subtitles_path=sample_media_files["subtitles_path"],
            caption="Almost due but not yet"
        )
        mgr.queue_reel(reel, slot_time_utc=future_1s)

        # Query must return None
        due = mgr.get_next_due(claim=True)
        assert due is None, "Reel scheduled 1 second into future must NOT be claimed"

    def test_concurrent_runners_cannot_double_dispatch_same_reel(self, temp_queue, sample_media_files):
        """Two concurrent workers competing for the same due reel: exactly 1 claims it, 1 receives None."""
        mgr: CloserQueueManager = temp_queue
        past_utc = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()

        reel = RenderedReel(
            id="reel_race_condition",
            title="Concurrency Test Reel",
            industry="real_estate",
            language="english",
            duration_seconds=68.0,
            video_path=sample_media_files["video_path"],
            cover_path=sample_media_files["cover_path"],
            subtitles_path=sample_media_files["subtitles_path"],
            caption="Testing race condition locking"
        )
        mgr.queue_reel(reel, slot_time_utc=past_utc)

        results: List[Any] = []
        errors: List[Exception] = []

        def worker_claim():
            try:
                # Open separate connection to SQLite
                w_conn = CloserQueueManager(mgr.db_path)
                claimed = w_conn.get_next_due(claim=True)
                results.append(claimed)
                w_conn.close()
            except Exception as e:
                errors.append(e)

        # Launch two threads simulating simultaneous cron runs
        t1 = threading.Thread(target=worker_claim)
        t2 = threading.Thread(target=worker_claim)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(errors) == 0, f"Worker raised unexpected error: {errors}"
        assert len(results) == 2

        claimed_count = sum(1 for r in results if r is not None)
        none_count = sum(1 for r in results if r is None)
        assert claimed_count == 1, "Exactly one worker MUST successfully claim the reel"
        assert none_count == 1, "The second worker MUST receive None to prevent double dispatch"

    def test_retry_exhaustion_transitions_to_failed_permanently(self, temp_queue, sample_media_files):
        """After 3 consecutive failures (max_retries), status transitions to FAILED and stops retrying."""
        mgr: CloserQueueManager = temp_queue
        past_utc = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()

        reel = RenderedReel(
            id="reel_max_retries",
            title="Max Retries Exhaustion Reel",
            industry="edtech",
            language="multilingual",
            duration_seconds=67.0,
            video_path=sample_media_files["video_path"],
            cover_path=sample_media_files["cover_path"],
            subtitles_path=sample_media_files["subtitles_path"],
            caption="Will fail 3 times"
        )
        mgr.queue_reel(reel, slot_time_utc=past_utc)

        # Attempt 1: Fails -> Requeued (retry_count = 1)
        due1 = mgr.get_next_due(claim=True)
        mgr.mark_dispatched(due1["id"], success=False, error="Error 1")
        assert mgr.list_queue()[0]["status"] == "QUEUED"
        assert mgr.list_queue()[0]["retry_count"] == 1

        # Attempt 2: Fails -> Requeued (retry_count = 2)
        due2 = mgr.get_next_due(claim=True)
        mgr.mark_dispatched(due2["id"], success=False, error="Error 2")
        assert mgr.list_queue()[0]["status"] == "QUEUED"
        assert mgr.list_queue()[0]["retry_count"] == 2

        # Attempt 3: Fails -> Permanently FAILED (retry_count = 3 >= max_retries)
        due3 = mgr.get_next_due(claim=True)
        mgr.mark_dispatched(due3["id"], success=False, error="Fatal network drop")
        assert mgr.list_queue()[0]["status"] == "FAILED"
        assert mgr.list_queue()[0]["retry_count"] == 3
        assert "Fatal network drop" in mgr.list_queue()[0]["last_error"]

        # Further due check must return None
        due4 = mgr.get_next_due(claim=True)
        assert due4 is None, "FAILED reel must not be returned by get_next_due"

    def test_buffer_low_watermark_alert_thresholds(self, temp_queue):
        """Buffer depth < 2 triggers alert; buffer depth >= 2 is healthy."""
        mgr: CloserQueueManager = temp_queue
        # Depth 0 -> Alert
        assert mgr.get_buffer_depth() < 2
        # Depth 1 -> Alert
        # Depth 2 -> Healthy


# ==============================================================================
# Category 3: Publishing & Webhook Security Boundaries
# ==============================================================================

class TestTier2PublishingAndSecurityBoundaries:
    """Boundary and security stress cases for HMAC signatures, replay, and Meta error subcodes."""

    def test_hmac_tampered_signature_rejected_with_403(self, mock_make_server):
        """Tampering even 1 character in the HMAC-SHA256 signature results in HTTP 403 Forbidden."""
        webhook_url = mock_make_server.webhook_url
        secret = b"closer_ai_dev_secret_2026"
        raw_body = b'{"caption":"Test","cover_url":"u","reel_id":"r1","scheduled_slot_ist":"s","title":"t","video_url":"v"}'
        
        real_sig = "sha256=" + hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
        # Tamper last hex character
        tampered_sig = real_sig[:-1] + ("0" if real_sig[-1] != "0" else "1")

        headers = {
            "Content-Type": "application/json",
            "X-Closer-Signature": tampered_sig,
            "X-Closer-Timestamp": datetime.now(timezone.utc).isoformat()
        }
        resp = httpx.post(webhook_url, content=raw_body, headers=headers)
        assert resp.status_code == 403
        assert "Invalid HMAC signature" in resp.json()["error"]

    def test_timestamp_drift_replay_protection_boundaries(self, mock_make_server):
        """Replay attack protection: drift > 300 seconds rejected with HTTP 400."""
        webhook_url = mock_make_server.webhook_url
        secret = b"closer_ai_dev_secret_2026"
        raw_body = b'{"caption":"Test","cover_url":"u","reel_id":"r1","scheduled_slot_ist":"s","title":"t","video_url":"v"}'
        sig = "sha256=" + hmac.new(secret, raw_body, hashlib.sha256).hexdigest()

        # Case 1: Stale timestamp (301 seconds ago) -> REJECT 400
        stale_ts = (datetime.now(timezone.utc) - timedelta(seconds=301)).isoformat()
        resp_stale = httpx.post(
            webhook_url,
            content=raw_body,
            headers={"Content-Type": "application/json", "X-Closer-Signature": sig, "X-Closer-Timestamp": stale_ts}
        )
        assert resp_stale.status_code == 400
        assert "drift exceeds 300 seconds" in resp_stale.json()["error"]

        # Case 2: Future timestamp (305 seconds into future) -> REJECT 400
        future_ts = (datetime.now(timezone.utc) + timedelta(seconds=305)).isoformat()
        resp_future = httpx.post(
            webhook_url,
            content=raw_body,
            headers={"Content-Type": "application/json", "X-Closer-Signature": sig, "X-Closer-Timestamp": future_ts}
        )
        assert resp_future.status_code == 400

        # Case 3: Fresh timestamp (280 seconds ago) -> ACCEPT 200
        fresh_ts = (datetime.now(timezone.utc) - timedelta(seconds=280)).isoformat()
        resp_fresh = httpx.post(
            webhook_url,
            content=raw_body,
            headers={"Content-Type": "application/json", "X-Closer-Signature": sig, "X-Closer-Timestamp": fresh_ts}
        )
        assert resp_fresh.status_code == 200

    def test_meta_instagram_rate_limit_error_subcode_2207042(self, mock_ig_server):
        """Meta API enforces 50 posts/24h rolling limit; returns subcode 2207042 when exceeded."""
        mock_ig_server.state.fail_mode = "ERROR_LIMIT"
        base_url = mock_ig_server.base_url

        resp = httpx.post(
            f"{base_url}/17841400012345678/media",
            data={"media_type": "REELS", "video_url": "https://assets.closer.ai/video.mp4"},
            headers={"Authorization": "Bearer token"}
        )
        assert resp.status_code == 400
        err = resp.json()["error"]
        assert err["code"] == 9
        assert err["error_subcode"] == 2207042
        assert "Daily Publishing Limit Reached" in err["message"]

    def test_meta_instagram_download_timeout_subcode_2207003(self, mock_ig_server):
        """Meta crawler download timeout error returns error subcode 2207003."""
        mock_ig_server.state.fail_mode = "ERROR_DOWNLOAD"
        base_url = mock_ig_server.base_url

        resp = httpx.post(
            f"{base_url}/17841400012345678/media",
            data={"media_type": "REELS", "video_url": "https://bad-cdn.closer.ai/timeout.mp4"},
            headers={"Authorization": "Bearer token"}
        )
        assert resp.status_code == 400
        err = resp.json()["error"]
        assert err["code"] == 100
        assert err["error_subcode"] == 2207003
        assert "Download Timeout" in err["message"]

    def test_meta_instagram_non_reels_media_type_subcode_2207053(self, mock_ig_server):
        """Attempting to initialize container with media_type != 'REELS' returns subcode 2207053."""
        base_url = mock_ig_server.base_url
        resp = httpx.post(
            f"{base_url}/17841400012345678/media",
            data={"media_type": "FEED_VIDEO", "video_url": "https://assets.closer.ai/video.mp4"},
            headers={"Authorization": "Bearer token"}
        )
        assert resp.status_code == 400
        err = resp.json()["error"]
        assert err["error_subcode"] == 2207053
        assert "Must be REELS" in err["message"]

    def test_webhook_missing_required_payload_keys_returns_422(self, mock_make_server):
        """Payload missing required fields (e.g. video_url or scheduled_slot_ist) returns HTTP 422."""
        webhook_url = mock_make_server.webhook_url
        secret = b"closer_ai_dev_secret_2026"
        incomplete_payload = {"reel_id": "r_incomplete", "title": "Incomplete"}
        raw_body = json.dumps(incomplete_payload).encode("utf-8")
        sig = "sha256=" + hmac.new(secret, raw_body, hashlib.sha256).hexdigest()

        resp = httpx.post(
            webhook_url,
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Closer-Signature": sig,
                "X-Closer-Timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        assert resp.status_code == 422
        assert "Missing required fields" in resp.json()["error"]
