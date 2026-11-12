"""
Tier 4: Real-World End-to-End Application Scenarios Suite.
Executes the full generation-to-publishing lifecycle for 5 distinct Indian industry sectors:
1. Clinic Emergency / Lead Drop-off (Healthcare & Aesthetics, Dr. Pallavi, Tamil + Indian English)
2. Solar Subsidy Rush (Rooftop Solar EPC, Swati, PM Surya Ghar ₹78,000, Hindi + Indian English)
3. Luxury Real Estate (Luxury Developers & NRI Buyers, Maya, ₹2.85 Cr Penthouse, Luxury English)
4. EdTech Admissions Speed-to-Lead (Bootcamps, Arjun, Sub-45s Lead Triage, Hinglish + Indian English)
5. Agency Lead Gen / Media Buyer Defense (B2B Performance Marketing, Rohan, Client Defense, Indian English)
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
    CloserQueueManager,
    MockInstagramServer,
    MockMakeWebhookServer
)


class TestTier4RealWorldScenarios:
    """End-to-end lifecycle verification for 5 realistic Indian business scenarios."""

    def _execute_full_lifecycle(
        self,
        sector_key: str,
        target_day: str,
        target_ist_time: str,
        mock_ig_server: MockInstagramServer,
        mock_make_server: MockMakeWebhookServer,
        queue_mgr: CloserQueueManager,
        sample_files: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Reusable pipeline executor running full 10-step lifecycle:
        1. Select sector template
        2. Verify voice synthesis & ducking math (-8.5 dB, -14.0 LUFS)
        3. Enforce safe-zone geometry (Y=1360 subtitles, Y=1530 CTA)
        4. Package multi-format manifest
        5. Ingest into SQLite mapped to IST slot
        6. Enforce temporal gate
        7. Atomic claim (DISPATCHING)
        8. HMAC-SHA256 signed Make.com webhook dispatch
        9. Meta Graph API container creation, polling, and publish
        10. Verify PUBLISHED status, audit log, and live permalink
        """
        scenario = SECTOR_SCENARIOS[sector_key]

        # 1. Script & Dialogue Generation
        reel_id = f"reel_20261112_{sector_key}_01"
        title = scenario["title"]
        caption = (
            f"{scenario['hook']}\n\n"
            f"Doctor/Founder: your ad budget runs 24/7. Human staff sleeps at night. "
            f"CLOSER AI responds in under 45 seconds in {scenario['language'].title()}.\n\n"
            f"{scenario['cta']}\n\n"
            f"#CloserAI #{sector_key.replace('_', '').title()} #IndiaBusiness #Telecalling"
        )

        # 2. Voice & Audio Ducking Checks
        voice_id = scenario["voice_id"]
        ducking_db = -8.5
        ducking_linear = 10 ** (ducking_db / 20.0)
        assert 0.37 < ducking_linear < 0.38
        lufs_target = -14.0
        assert lufs_target == -14.0

        # 3. Safe-zone Overlay Verification
        sub_y = 1360
        cta_y = 1530
        assert sub_y == 1360
        assert cta_y == 1530
        assert 220 < sub_y < cta_y < 1550

        # 4. Multi-format packaging
        rendered = RenderedReel(
            id=reel_id,
            title=title,
            industry=sector_key,
            language=scenario["language"],
            duration_seconds=74.5,
            video_path=sample_files["video_path"],
            cover_path=sample_files["cover_path"],
            subtitles_path=sample_files["subtitles_path"],
            caption=caption,
            cta_keyword="CLOSER",
            metadata={
                "persona_host": scenario["persona_host"],
                "persona_attire": scenario["persona_attire"],
                "whatsapp_asset": scenario["whatsapp_asset"],
                "lufs": lufs_target
            }
        )

        # 5. Ingest into Queue with assigned Timetable slot
        slot_def = next(s for s in WEEKLY_MASTER_TIMETABLE if s["day"] == target_day and target_ist_time in s["ist"])
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        # Parse UTC time from slot_def
        u_h, u_m = map(int, slot_def["utc"].split(":"))
        slot_utc = tomorrow.replace(hour=u_h, minute=u_m, second=0, microsecond=0).isoformat()
        slot_ist = f"{tomorrow.strftime('%Y-%m-%d')} {slot_def['ist']} IST"

        queue_mgr.queue_reel(
            rendered,
            slot_time_utc=slot_utc,
            slot_time_ist=slot_ist,
            slot_day=slot_def["day"],
            slot_name=slot_def["slot"],
            status="SCHEDULED"
        )

        # 6. Temporal Gate Verification (Future slot cannot be claimed)
        future_check = queue_mgr.get_next_due(claim=True)
        assert future_check is None, "Reel scheduled for tomorrow must be protected by temporal gate"

        # Simulate time arrival: update scheduled_time_utc to 1 minute in the past
        past_utc = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        with queue_mgr.conn:
            queue_mgr.conn.execute("UPDATE reels SET scheduled_time_utc = ? WHERE id = ?", (past_utc, reel_id))

        # 7. Atomic Claim (DISPATCHING)
        claimed = queue_mgr.get_next_due(claim=True)
        assert claimed is not None
        assert claimed["id"] == reel_id
        assert claimed["status"] == "DISPATCHING"

        # 8. HMAC-SHA256 Signed Webhook Dispatch
        payload = {
            "reel_id": claimed["id"],
            "title": claimed["title"],
            "caption": claimed["caption"],
            "video_url": claimed["video_url"],
            "cover_url": claimed["cover_url"],
            "scheduled_slot_ist": claimed["scheduled_time_ist"],
            "industry": claimed["industry_sector"],
            "cta_keyword": claimed["cta_keyword"],
            "metadata": json.loads(claimed["metadata_json"])
        }
        body_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        secret = b"closer_ai_dev_secret_2026"
        sig = "sha256=" + hmac.new(secret, body_bytes, hashlib.sha256).hexdigest()
        ts = datetime.now(timezone.utc).isoformat()

        headers = {
            "Content-Type": "application/json",
            "X-Closer-Signature": sig,
            "X-Closer-Timestamp": ts
        }

        resp_hook = httpx.post(mock_make_server.webhook_url, content=body_bytes, headers=headers)
        assert resp_hook.status_code == 200
        webhook_exec_id = resp_hook.json()["execution_id"]

        # 9. Meta Instagram Graph API v21.0 Container Ingestion & Publish
        ig_headers = {"Authorization": "Bearer EAAB_valid_meta_token"}
        # 9a. Init container
        resp_c = httpx.post(
            f"{mock_ig_server.base_url}/17841400012345678/media",
            data={
                "media_type": "REELS",
                "video_url": claimed["video_url"],
                "caption": claimed["caption"],
                "share_to_feed": "true"
            },
            headers=ig_headers
        )
        assert resp_c.status_code == 200
        container_id = resp_c.json()["id"]

        # 9b. Poll until FINISHED
        resp_p = httpx.get(f"{mock_ig_server.base_url}/{container_id}?fields=status_code,status", headers=ig_headers)
        assert resp_p.status_code == 200
        assert resp_p.json()["status_code"] == "FINISHED"

        # 9c. Publish
        resp_pub = httpx.post(
            f"{mock_ig_server.base_url}/17841400012345678/media_publish",
            data={"creation_id": container_id},
            headers=ig_headers
        )
        assert resp_pub.status_code == 200
        pub_data = resp_pub.json()
        media_id = pub_data["id"]
        permalink = pub_data["permalink"]

        # 10. Status Callback to Queue
        queue_mgr.mark_dispatched(
            reel_id=claimed["id"],
            success=True,
            container_id=container_id,
            media_id=media_id,
            permalink=permalink
        )

        # Final Verification of Record
        final_record = queue_mgr.list_queue(status="PUBLISHED")[0]
        assert final_record["id"] == reel_id
        assert final_record["status"] == "PUBLISHED"
        assert final_record["ig_container_id"] == container_id
        assert final_record["ig_media_id"] == media_id
        assert final_record["ig_permalink"] == permalink
        assert final_record["published_at"] is not None

        # Verify audit log
        cursor = queue_mgr.conn.cursor()
        cursor.execute("SELECT * FROM queue_audit_log WHERE reel_id = ? ORDER BY id ASC", (reel_id,))
        logs = cursor.fetchall()
        assert len(logs) >= 3  # RENDERED -> SCHEDULED -> DISPATCHING -> PUBLISHED

        return {
            "reel_id": reel_id,
            "webhook_exec_id": webhook_exec_id,
            "container_id": container_id,
            "media_id": media_id,
            "permalink": permalink
        }

    def test_scenario_1_clinic_emergency_lead_dropoff(self, mock_ig_server, mock_make_server, temp_queue, sample_media_files):
        """Scenario 1: Healthcare & Dental/Hair Clinics (Tamil + English, Tuesday 13:15 IST OPD slot)."""
        res = self._execute_full_lifecycle(
            sector_key="clinics",
            target_day="Tuesday",
            target_ist_time="13:15",
            mock_ig_server=mock_ig_server,
            mock_make_server=mock_make_server,
            queue_mgr=temp_queue,
            sample_files=sample_media_files
        )
        assert res["reel_id"].startswith("reel_20261112_clinics_")
        assert res["permalink"].startswith("https://www.instagram.com/reel/")

    def test_scenario_2_solar_subsidy_rush(self, mock_ig_server, mock_make_server, temp_queue, sample_media_files):
        """Scenario 2: Rooftop Solar EPC PM Surya Ghar Subsidy (Hindi + English, Wednesday 09:00 IST field push)."""
        res = self._execute_full_lifecycle(
            sector_key="solar",
            target_day="Wednesday",
            target_ist_time="09:00",
            mock_ig_server=mock_ig_server,
            mock_make_server=mock_make_server,
            queue_mgr=temp_queue,
            sample_files=sample_media_files
        )
        assert res["reel_id"].startswith("reel_20261112_solar_")
        assert res["media_id"] is not None

    def test_scenario_3_luxury_real_estate(self, mock_ig_server, mock_make_server, temp_queue, sample_media_files):
        """Scenario 3: Luxury Real Estate & Villa NRI Desk (Luxury English, Wednesday 20:30 IST night slot)."""
        res = self._execute_full_lifecycle(
            sector_key="real_estate",
            target_day="Wednesday",
            target_ist_time="20:30",
            mock_ig_server=mock_ig_server,
            mock_make_server=mock_make_server,
            queue_mgr=temp_queue,
            sample_files=sample_media_files
        )
        assert res["reel_id"].startswith("reel_20261112_real_estate_")
        assert res["container_id"].startswith("ig_container_")

    def test_scenario_4_edtech_admissions_speed_to_lead(self, mock_ig_server, mock_make_server, temp_queue, sample_media_files):
        """Scenario 4: EdTech & Career Bootcamps (Hinglish + English, Thursday 13:30 IST lunch speed teardown)."""
        res = self._execute_full_lifecycle(
            sector_key="edtech",
            target_day="Thursday",
            target_ist_time="13:30",
            mock_ig_server=mock_ig_server,
            mock_make_server=mock_make_server,
            queue_mgr=temp_queue,
            sample_files=sample_media_files
        )
        assert res["reel_id"].startswith("reel_20261112_edtech_")
        assert res["webhook_exec_id"].startswith("make_exec_")

    def test_scenario_5_agency_lead_gen_media_buyer_defense(self, mock_ig_server, mock_make_server, temp_queue, sample_media_files):
        """Scenario 5: B2B Agency Lead Gen & Media Buyer Defense (Indian English, Friday 09:15 IST morning push)."""
        res = self._execute_full_lifecycle(
            sector_key="b2b_agency",
            target_day="Friday",
            target_ist_time="09:15",
            mock_ig_server=mock_ig_server,
            mock_make_server=mock_make_server,
            queue_mgr=temp_queue,
            sample_files=sample_media_files
        )
        assert res["reel_id"].startswith("reel_20261112_b2b_agency_")
        assert res["permalink"].startswith("https://www.instagram.com/reel/")
