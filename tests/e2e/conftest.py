"""
Pytest fixtures and mock server infrastructure for CLOSER AI E2E tests.
Provides isolated SQLite databases, ephemeral mock Meta v21.0 Graph API server,
mock Make.com Webhook receiver with HMAC-SHA256, and reference test data.
"""

from __future__ import annotations
import hmac
import hashlib
import json
import os
import socket
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List, Optional, Tuple
import urllib.parse
import pytest


# ==============================================================================
# 1. Interface Contracts (as defined in PROJECT.md)
# ==============================================================================

@dataclass
class RenderedReel:
    id: str
    title: str
    industry: str
    language: str
    duration_seconds: float
    video_path: str
    cover_path: str
    subtitles_path: str
    caption: str
    cta_keyword: str = "CLOSER"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PublishResult:
    success: bool
    container_id: Optional[str] = None
    media_id: Optional[str] = None
    permalink: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[int] = None
    error_subcode: Optional[int] = None


# Master 14-Slot Indian Engagement Timetable (IST & UTC)
WEEKLY_MASTER_TIMETABLE = [
    {"day": "Monday", "slot": "Slot 1 (Morning Urgency)", "ist": "08:30", "utc": "03:00", "industry": "b2b_agency"},
    {"day": "Monday", "slot": "Slot 2 (Night Debrief)", "ist": "20:15", "utc": "14:45", "industry": "real_estate"},
    {"day": "Tuesday", "slot": "Slot 1 (Lunch OPD Lull)", "ist": "13:15", "utc": "07:45", "industry": "clinics"},
    {"day": "Tuesday", "slot": "Slot 2 (Night Finance)", "ist": "20:45", "utc": "15:15", "industry": "b2b_agency"},
    {"day": "Wednesday", "slot": "Slot 1 (Morning Field Push)", "ist": "09:00", "utc": "03:30", "industry": "solar"},
    {"day": "Wednesday", "slot": "Slot 2 (Night High-Ticket)", "ist": "20:30", "utc": "15:00", "industry": "real_estate"},
    {"day": "Thursday", "slot": "Slot 1 (Lunch Speed Teardown)", "ist": "13:30", "utc": "08:00", "industry": "edtech"},
    {"day": "Thursday", "slot": "Slot 2 (Night Vernacular)", "ist": "21:00", "utc": "15:30", "industry": "clinics"},
    {"day": "Friday", "slot": "Slot 1 (Morning Agency Push)", "ist": "09:15", "utc": "03:45", "industry": "b2b_agency"},
    {"day": "Friday", "slot": "Slot 2 (Weekend Autopilot)", "ist": "19:45", "utc": "14:15", "industry": "solar"},
    {"day": "Saturday", "slot": "Slot 1 (Brunch Strategy)", "ist": "11:30", "utc": "06:00", "industry": "edtech"},
    {"day": "Saturday", "slot": "Slot 2 (Evening Mobile HUD)", "ist": "18:45", "utc": "13:15", "industry": "real_estate"},
    {"day": "Sunday", "slot": "Slot 1 (Morning Family Leisure)", "ist": "10:30", "utc": "05:00", "industry": "clinics"},
    {"day": "Sunday", "slot": "Slot 2 (Sunday Scaries / Launch)", "ist": "20:45", "utc": "15:15", "industry": "b2b_agency"},
]

# 5 Core Indian Business Sector Presets
SECTOR_SCENARIOS = {
    "clinics": {
        "title": "Dental & Hair Clinic Lead Drop-off Solution",
        "industry": "clinics",
        "language": "tamil",
        "persona_host": "Dr. Pallavi",
        "persona_attire": "labcoat",
        "voice_id": "ta-IN-PallaviNeural",
        "hook": "Doctor: why does your front desk miss 40% of leads while in surgery?",
        "whatsapp_asset": "VIP_Clinic_Consultation_Pass.pkpass",
        "cta": "👇 COMMENT 'CLOSER' BELOW 👇 for the Dental & Hair Clinic Automated Lead Qualification Protocol"
    },
    "solar": {
        "title": "Rooftop Solar PM Surya Ghar Subsidy Closer",
        "industry": "solar",
        "language": "hindi",
        "persona_host": "Swati",
        "persona_attire": "high_vis_vest",
        "voice_id": "hi-IN-SwaraNeural",
        "hook": "₹78,000 PM Surya Ghar rooftop solar subsidy inquiries are freezing in your CRM.",
        "whatsapp_asset": "5kW_Solar_PM_Surya_Ghar_Quotation.pdf",
        "cta": "👇 COMMENT 'CLOSER' BELOW 👇 for the PM Surya Ghar 5kW Subsidy Prompt & Calculator"
    },
    "real_estate": {
        "title": "Luxury Real Estate & Villa NRI Buyer Closer",
        "industry": "real_estate",
        "language": "english",
        "persona_host": "Maya",
        "persona_attire": "blazer",
        "voice_id": "af_bella",
        "hook": "Losing a ₹2.85 Cr penthouse sale to a competing builder due to a 4-hour delay.",
        "whatsapp_asset": "ECR_Sea_Facing_Penthouse_Brochure.pdf",
        "cta": "👇 COMMENT 'CLOSER' BELOW 👇 to get the ECR Villa Brochure & Sunday Site Visit Booking Agent"
    },
    "edtech": {
        "title": "EdTech & Bootcamp Admissions Speed-to-Lead",
        "industry": "edtech",
        "language": "multilingual",
        "persona_host": "Arjun",
        "persona_attire": "turtleneck",
        "voice_id": "en-IN-PrabhatNeural",
        "hook": "Students apply to 4 bootcamps simultaneously. First caller within 45s wins.",
        "whatsapp_asset": "Data_Science_Syllabus_Scholarship_Pass.pdf",
        "cta": "👇 COMMENT 'CLOSER' BELOW 👇 for the Sub-45s Admissions Speed-to-Lead Make.com Blueprint"
    },
    "b2b_agency": {
        "title": "Performance Agency Media Buyer Client Defense",
        "industry": "b2b_agency",
        "language": "english",
        "persona_host": "Rohan",
        "persona_attire": "turtleneck",
        "voice_id": "af_heart",
        "hook": "Media buyers: your client blames your Meta ads for bad leads. The truth? Their sales team takes 14 hours to dial.",
        "whatsapp_asset": "Agency_Instant_AutoDialer_Workflow.pdf",
        "cta": "👇 COMMENT 'CLOSER' BELOW 👇 for the Agency Instant Auto-Dialer Setup Blueprint"
    }
}


# ==============================================================================
# 2. SQLite Database Schema & Helper Class
# ==============================================================================

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS reels (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    industry_sector TEXT NOT NULL CHECK(industry_sector IN ('clinics', 'solar', 'real_estate', 'edtech', 'b2b_agency', 'universal')),
    language TEXT NOT NULL CHECK(language IN ('english', 'tamil', 'hindi', 'multilingual')),
    status TEXT NOT NULL CHECK(status IN ('DRAFT', 'RENDERED', 'QUEUED', 'SCHEDULED', 'DISPATCHING', 'PUBLISHED', 'FAILED')),
    scheduled_time_utc TEXT NOT NULL,
    scheduled_time_ist TEXT NOT NULL,
    slot_day TEXT NOT NULL,
    slot_name TEXT NOT NULL,
    video_path TEXT NOT NULL,
    video_url TEXT,
    cover_path TEXT,
    cover_url TEXT,
    subtitles_path TEXT,
    caption TEXT NOT NULL,
    cta_keyword TEXT NOT NULL DEFAULT 'CLOSER',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    dispatched_at TEXT,
    published_at TEXT,
    ig_container_id TEXT,
    ig_media_id TEXT,
    ig_permalink TEXT,
    make_webhook_status TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    last_error TEXT,
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_reels_status_sched ON reels(status, scheduled_time_utc);
CREATE INDEX IF NOT EXISTS idx_reels_slot ON reels(slot_day, slot_name);

CREATE TABLE IF NOT EXISTS queue_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reel_id TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    actor TEXT NOT NULL,
    details TEXT,
    FOREIGN KEY(reel_id) REFERENCES reels(id) ON DELETE CASCADE
);
"""


class CloserQueueManager:
    """Manages SQLite and JSON mirror for E2E testing."""

    def __init__(self, db_path: str, json_mirror_path: Optional[str] = None):
        self.db_path = db_path
        self.json_mirror_path = json_mirror_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self.conn:
            self.conn.executescript(SCHEMA_SQL)
        self.sync_json_mirror()

    def sync_json_mirror(self):
        if not self.json_mirror_path:
            return
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM reels ORDER BY scheduled_time_utc ASC")
        rows = [dict(row) for row in cursor.fetchall()]
        summary = {
            "last_synced": datetime.now(timezone.utc).isoformat(),
            "total_count": len(rows),
            "by_status": {},
            "reels": rows
        }
        for r in rows:
            summary["by_status"][r["status"]] = summary["by_status"].get(r["status"], 0) + 1
        with open(self.json_mirror_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

    def queue_reel(
        self,
        rendered_reel: RenderedReel,
        slot_time_utc: Optional[str] = None,
        slot_time_ist: Optional[str] = None,
        slot_day: Optional[str] = None,
        slot_name: Optional[str] = None,
        status: str = "SCHEDULED"
    ) -> str:
        # Validate media files exist or paths provided
        if not rendered_reel.video_path:
            raise ValueError("video_path is required")

        now_utc = datetime.now(timezone.utc).isoformat()
        if not slot_time_utc:
            # Default to tomorrow 13:15 IST / 07:45 UTC
            tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
            slot_time_utc = tomorrow.replace(hour=7, minute=45, second=0, microsecond=0).isoformat()
            slot_time_ist = (tomorrow + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d 13:15 IST")
            slot_day = tomorrow.strftime("%A")
            slot_name = "Slot 1 (Standard Peak)"

        with self.conn:
            self.conn.execute("""
                INSERT INTO reels (
                    id, title, industry_sector, language, status,
                    scheduled_time_utc, scheduled_time_ist, slot_day, slot_name,
                    video_path, video_url, cover_path, cover_url, subtitles_path,
                    caption, cta_keyword, created_at, updated_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rendered_reel.id,
                rendered_reel.title,
                rendered_reel.industry,
                rendered_reel.language,
                status,
                slot_time_utc,
                slot_time_ist or "TBD IST",
                slot_day or "Monday",
                slot_name or "Slot 1",
                rendered_reel.video_path,
                f"https://assets.closer.ai/reels/{rendered_reel.id}.mp4",
                rendered_reel.cover_path,
                f"https://assets.closer.ai/reels/{rendered_reel.id}.jpg",
                rendered_reel.subtitles_path,
                rendered_reel.caption,
                rendered_reel.cta_keyword,
                now_utc,
                now_utc,
                json.dumps(rendered_reel.metadata)
            ))
            self.conn.execute("""
                INSERT INTO queue_audit_log (reel_id, from_status, to_status, timestamp, actor, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (rendered_reel.id, "RENDERED", status, now_utc, "TestQueueManager", "Reel enqueued"))
        self.sync_json_mirror()
        return rendered_reel.id

    def get_next_due(self, claim: bool = True) -> Optional[Dict[str, Any]]:
        """
        Dual-layer premature posting prevention:
        1. SQL gate: scheduled_time_utc <= NOW()
        2. Python temporal assertion
        """
        cursor = self.conn.cursor()
        now_str = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            SELECT * FROM reels
            WHERE status IN ('QUEUED', 'SCHEDULED')
              AND datetime(scheduled_time_utc) <= datetime(?)
            ORDER BY scheduled_time_utc ASC
            LIMIT 1
        """, (now_str,))
        row = cursor.fetchone()
        if not row:
            return None

        reel = dict(row)
        # Python temporal gate
        sched_dt = datetime.fromisoformat(reel["scheduled_time_utc"].replace("Z", "+00:00"))
        now_dt = datetime.now(timezone.utc)
        if sched_dt > now_dt:
            raise RuntimeError(f"Premature posting prevented: scheduled {sched_dt} is in future vs {now_dt}")

        if claim:
            with self.conn:
                cur_upd = self.conn.execute("""
                    UPDATE reels
                    SET status = 'DISPATCHING', dispatched_at = ?, updated_at = ?
                    WHERE id = ? AND status IN ('QUEUED', 'SCHEDULED')
                """, (now_str, now_str, reel["id"]))
                if cur_upd.rowcount == 0:
                    # Race condition lost: Another concurrent worker claimed this reel
                    return None
                self.conn.execute("""
                    INSERT INTO queue_audit_log (reel_id, from_status, to_status, timestamp, actor, details)
                    VALUES (?, ?, 'DISPATCHING', ?, 'TestQueueManager', 'Atomic claim for dispatch')
                """, (reel["id"], reel["status"], now_str))
            self.sync_json_mirror()
            reel["status"] = "DISPATCHING"
            reel["dispatched_at"] = now_str
        return reel

    def mark_dispatched(
        self,
        reel_id: str,
        success: bool,
        container_id: Optional[str] = None,
        media_id: Optional[str] = None,
        permalink: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        now_str = datetime.now(timezone.utc).isoformat()
        cursor = self.conn.cursor()
        cursor.execute("SELECT status, retry_count, max_retries FROM reels WHERE id = ?", (reel_id,))
        row = cursor.fetchone()
        if not row:
            raise KeyError(f"Reel {reel_id} not found")
        
        curr_status = row["status"]
        retries = row["retry_count"]
        max_retries = row["max_retries"]

        with self.conn:
            if success:
                self.conn.execute("""
                    UPDATE reels
                    SET status = 'PUBLISHED', published_at = ?, ig_container_id = ?,
                        ig_media_id = ?, ig_permalink = ?, updated_at = ?, last_error = NULL
                    WHERE id = ?
                """, (now_str, container_id, media_id, permalink, now_str, reel_id))
                self.conn.execute("""
                    INSERT INTO queue_audit_log (reel_id, from_status, to_status, timestamp, actor, details)
                    VALUES (?, ?, 'PUBLISHED', ?, 'TestQueueManager', ?)
                """, (reel_id, curr_status, now_str, f"Published successfully. media_id={media_id}"))
            else:
                new_retries = retries + 1
                if new_retries < max_retries:
                    new_status = "QUEUED"
                    detail = f"Failed attempt {new_retries}/{max_retries}: {error}. Requeued."
                else:
                    new_status = "FAILED"
                    detail = f"Permanently failed after {new_retries} attempts: {error}"

                self.conn.execute("""
                    UPDATE reels
                    SET status = ?, retry_count = ?, last_error = ?, updated_at = ?
                    WHERE id = ?
                """, (new_status, new_retries, error, now_str, reel_id))
                self.conn.execute("""
                    INSERT INTO queue_audit_log (reel_id, from_status, to_status, timestamp, actor, details)
                    VALUES (?, ?, ?, ?, 'TestQueueManager', ?)
                """, (reel_id, curr_status, new_status, now_str, detail))
        self.sync_json_mirror()

    def list_queue(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        if status:
            cursor.execute("SELECT * FROM reels WHERE status = ? ORDER BY scheduled_time_utc ASC", (status,))
        else:
            cursor.execute("SELECT * FROM reels ORDER BY scheduled_time_utc ASC")
        return [dict(r) for r in cursor.fetchall()]

    def get_buffer_depth(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM reels WHERE status IN ('QUEUED', 'SCHEDULED')")
        return cursor.fetchone()["cnt"]

    def close(self):
        self.conn.close()


# ==============================================================================
# 3. Mock Instagram Graph API v21.0 Server
# ==============================================================================

class MockInstagramState:
    def __init__(self):
        self.containers: Dict[str, Dict[str, Any]] = {}
        self.published_media: Dict[str, Dict[str, Any]] = {}
        self.poll_counts: Dict[str, int] = {}
        self.fail_mode: Optional[str] = None
        self.rolling_published_count: int = 0
        self.rate_limit_max: int = 50

    def reset(self):
        self.containers.clear()
        self.published_media.clear()
        self.poll_counts.clear()
        self.fail_mode = None
        self.rolling_published_count = 0


class MockInstagramHandler(BaseHTTPRequestHandler):
    state: MockInstagramState = MockInstagramState()

    def _send_json(self, status_code: int, data: Dict[str, Any]):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-FB-Debug", f"mock_debug_{uuid.uuid4().hex[:10]}")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _read_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        content_type = self.headers.get("Content-Type", "")
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
        parsed = {}
        if "application/json" in content_type and body:
            parsed = json.loads(body)
        elif body:
            query_dict = urllib.parse.parse_qs(body)
            parsed = {k: v[0] if len(v) == 1 else v for k, v in query_dict.items()}
        if "?" in self.path:
            _, query_str = self.path.split("?", 1)
            q_params = urllib.parse.parse_qs(query_str)
            for k, v in q_params.items():
                if k not in parsed:
                    parsed[k] = v[0] if len(v) == 1 else v
        return parsed

    def do_POST(self):
        auth_header = self.headers.get("Authorization", "")
        if not auth_header and "access_token" not in self.path:
            self._send_json(401, {
                "error": {
                    "message": "An active access token must be used to query information about the current user.",
                    "type": "OAuthException",
                    "code": 190
                }
            })
            return

        params = self._read_body()
        path = self.path.split("?")[0].strip("/")
        parts = path.split("/")

        # Rate Limit check
        if self.state.rolling_published_count >= self.state.rate_limit_max or self.state.fail_mode == "ERROR_LIMIT":
            self._send_json(400, {
                "error": {
                    "message": "Daily Publishing Limit Reached: Maximum 50 reels allowed per 24 hours.",
                    "type": "OAuthException",
                    "code": 9,
                    "error_subcode": 2207042
                }
            })
            return

        # 1. POST /{ig-user-id}/media (Container Init)
        if len(parts) >= 2 and parts[-1] == "media":
            media_type = params.get("media_type")
            video_url = params.get("video_url")
            caption = params.get("caption", "")

            if media_type != "REELS":
                self._send_json(400, {
                    "error": {
                        "message": f"Invalid media_type '{media_type}'. Must be REELS for vertical 9:16 video.",
                        "type": "OAuthException",
                        "code": 100,
                        "error_subcode": 2207053
                    }
                })
                return

            if not video_url:
                self._send_json(400, {
                    "error": {
                        "message": "Missing required parameter 'video_url'.",
                        "type": "OAuthException",
                        "code": 100,
                        "error_subcode": 2207032
                    }
                })
                return

            if self.state.fail_mode == "ERROR_DOWNLOAD":
                self._send_json(400, {
                    "error": {
                        "message": "Download Timeout: Meta crawler could not fetch video_url within timeout.",
                        "type": "OAuthException",
                        "code": 100,
                        "error_subcode": 2207003
                    }
                })
                return

            cid = f"ig_container_{uuid.uuid4().hex[:10]}"
            self.state.containers[cid] = {
                "id": cid,
                "video_url": video_url,
                "caption": caption,
                "status_code": "IN_PROGRESS",
                "created_at": time.time()
            }
            self.state.poll_counts[cid] = 0
            self._send_json(200, {"id": cid})
            return

        # 2. POST /{ig-user-id}/media_publish
        if len(parts) >= 2 and parts[-1] == "media_publish":
            cid = params.get("creation_id")
            if not cid or cid not in self.state.containers:
                self._send_json(400, {
                    "error": {
                        "message": f"Container '{cid}' does not exist or has expired.",
                        "type": "OAuthException",
                        "code": 100,
                        "error_subcode": 2207006
                    }
                })
                return

            container = self.state.containers[cid]
            if container.get("status_code") != "FINISHED":
                self._send_json(400, {
                    "error": {
                        "message": f"Container '{cid}' is not in FINISHED status (current: {container.get('status_code')}).",
                        "type": "OAuthException",
                        "code": 100,
                        "error_subcode": 2207032
                    }
                })
                return

            media_id = f"179{uuid.uuid4().int % 1000000000000000}"
            permalink = f"https://www.instagram.com/reel/{uuid.uuid4().hex[:11]}/"
            self.state.published_media[media_id] = {
                "id": media_id,
                "container_id": cid,
                "permalink": permalink,
                "published_at": time.time()
            }
            self.state.rolling_published_count += 1
            container["status_code"] = "PUBLISHED"
            self._send_json(200, {"id": media_id, "permalink": permalink})
            return

        self._send_json(404, {"error": "Endpoint not found"})

    def do_GET(self):
        auth_header = self.headers.get("Authorization", "")
        if not auth_header and "access_token" not in self.path:
            self._send_json(401, {"error": "Unauthorized"})
            return

        path = self.path.split("?")[0].strip("/")
        parts = path.split("/")
        cid = parts[-1]

        if cid in self.state.containers:
            self.state.poll_counts[cid] = self.state.poll_counts.get(cid, 0) + 1
            # Transition to FINISHED on first poll
            if self.state.poll_counts[cid] >= 1:
                self.state.containers[cid]["status_code"] = "FINISHED"

            self._send_json(200, {
                "id": cid,
                "status_code": self.state.containers[cid]["status_code"],
                "status": "Ready to publish" if self.state.containers[cid]["status_code"] == "FINISHED" else "Processing"
            })
            return

        self._send_json(404, {"error": f"Container {cid} not found"})

    def log_message(self, format, *args):
        pass


class MockInstagramServer:
    def __init__(self, port: int):
        self.port = port
        self.state = MockInstagramState()
        MockInstagramHandler.state = self.state
        self.server = HTTPServer(("127.0.0.1", self.port), MockInstagramHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self):
        self.state.reset()
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1.0)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"


# ==============================================================================
# 4. Mock Make.com Custom Webhook Server
# ==============================================================================

class MockMakeWebhookState:
    def __init__(self):
        self.received_events: List[Dict[str, Any]] = []
        self.webhook_secret: bytes = b"closer_ai_dev_secret_2026"
        self.require_hmac: bool = True

    def reset(self):
        self.received_events.clear()
        self.require_hmac = True


class MockMakeWebhookHandler(BaseHTTPRequestHandler):
    state: MockMakeWebhookState = MockMakeWebhookState()

    def _send_json(self, status_code: int, data: Dict[str, Any]):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b""

        sig_header = self.headers.get("X-Closer-Signature", "")
        ts_header = self.headers.get("X-Closer-Timestamp", "")

        # 1. HMAC Signature Verification
        if self.state.require_hmac:
            if not sig_header:
                self._send_json(401, {"error": "Missing X-Closer-Signature header"})
                return

            expected_sig = "sha256=" + hmac.new(self.state.webhook_secret, raw_body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig_header, expected_sig):
                self._send_json(403, {"error": "Invalid HMAC signature"})
                return

            # 2. Timestamp Drift Replay Protection (300 seconds)
            if ts_header:
                try:
                    ts = datetime.fromisoformat(ts_header.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)
                    if abs((now - ts).total_seconds()) > 300:
                        self._send_json(400, {"error": "Timestamp drift exceeds 300 seconds"})
                        return
                except Exception:
                    self._send_json(400, {"error": "Malformed X-Closer-Timestamp ISO-8601 string"})
                    return

        # 3. Payload Validation
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON payload: {e}"})
            return

        required_keys = ["reel_id", "title", "caption", "video_url", "cover_url", "scheduled_slot_ist"]
        missing = [k for k in required_keys if k not in payload]
        if missing:
            self._send_json(422, {"error": f"Missing required fields: {missing}"})
            return

        exec_id = f"make_exec_{uuid.uuid4().hex[:10]}"
        self.state.received_events.append({
            "execution_id": exec_id,
            "received_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload
        })

        self._send_json(200, {
            "status": "accepted",
            "execution_id": exec_id,
            "reel_id": payload["reel_id"]
        })

    def log_message(self, format, *args):
        pass


class MockMakeWebhookServer:
    def __init__(self, port: int):
        self.port = port
        self.state = MockMakeWebhookState()
        MockMakeWebhookHandler.state = self.state
        self.server = HTTPServer(("127.0.0.1", self.port), MockMakeWebhookHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self):
        self.state.reset()
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1.0)

    @property
    def webhook_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/webhook/closer-reels"


# ==============================================================================
# 5. Pytest Fixtures
# ==============================================================================

def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def mock_ig_server():
    port = find_free_port()
    server = MockInstagramServer(port)
    server.start()
    yield server
    server.stop()


@pytest.fixture
def mock_make_server():
    port = find_free_port()
    server = MockMakeWebhookServer(port)
    server.start()
    yield server
    server.stop()


@pytest.fixture
def temp_queue(tmp_path):
    db_path = str(tmp_path / "test_reels_queue.db")
    json_path = str(tmp_path / "test_queue_state.json")
    mgr = CloserQueueManager(db_path, json_path)
    yield mgr
    mgr.close()


@pytest.fixture
def sample_media_files(tmp_path):
    media_dir = tmp_path / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    video_path = str(media_dir / "sample_reel_1080p.mp4")
    cover_path = str(media_dir / "sample_poster.jpg")
    subtitles_path = str(media_dir / "sample_subtitles.srt")

    # Create dummy media files
    with open(video_path, "wb") as f:
        f.write(b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41" + b"\x00" * 1024)
    with open(cover_path, "wb") as f:
        f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 512)
    with open(subtitles_path, "w", encoding="utf-8") as f:
        f.write("1\n00:00:00,000 --> 00:00:03,000\nDoctors: why miss leads in surgery?\n\n")

    return {
        "video_path": video_path,
        "cover_path": cover_path,
        "subtitles_path": subtitles_path
    }
