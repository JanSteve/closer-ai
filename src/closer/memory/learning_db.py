"""
Continuous Learning & Call Recording Database for CLOSER AI (Amura Health).
Stores patient call recordings, transcripts, and extracts reusable clinical FAQs
without mutating repository data/ files during tests.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _resolve_default_db_path() -> Path:
    """
    Returns an isolated temp DB path by default so automated tests never mutate repo data/.
    Set CLOSER_MEMORY_DB_PATH for an explicit path, or CLOSER_PERSIST_LOCAL_DB=1 to use data/.
    """
    explicit = os.environ.get("CLOSER_MEMORY_DB_PATH")
    if explicit:
        return Path(explicit)
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return Path(tempfile.gettempdir()) / "closer_learning.db"
    if os.environ.get("CLOSER_PERSIST_LOCAL_DB") == "1":
        try:
            data_dir = Path("data")
            data_dir.mkdir(parents=True, exist_ok=True)
            return data_dir / "closer_learning.db"
        except (OSError, PermissionError):
            pass
    return Path(tempfile.gettempdir()) / "closer_learning.db"


DEFAULT_DB_PATH = _resolve_default_db_path()


class LearningMemoryDB:
    """
    SQLite-backed memory and autonomous clinical knowledge base for CLOSER AI (Amura Health).
    Supports temp-file SQLite and persistent single-connection ':memory:'.
    """

    def __init__(self, db_path: Optional[Path | str] = None):
        self._is_memory = False
        self._mem_conn: Optional[sqlite3.Connection] = None

        if db_path is not None and str(db_path) == ":memory:":
            self._is_memory = True
            self.db_path = Path(":memory:")
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
        else:
            self.db_path = Path(db_path) if db_path is not None else _resolve_default_db_path()
            try:
                if self.db_path.parent:
                    self.db_path.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError):
                self.db_path = Path(tempfile.gettempdir()) / "closer_learning.db"

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._is_memory and self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def close(self) -> None:
        if self._mem_conn is not None:
            try:
                self._mem_conn.close()
            except Exception:
                pass
            self._mem_conn = None

    def _init_db(self) -> None:
        """Initializes tables for call records and learned clinical knowledge."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS call_records (
                    call_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    customer_name TEXT,
                    customer_phone TEXT,
                    market_mode TEXT,
                    sector TEXT,
                    business_name TEXT,
                    transcript_json TEXT,
                    dossier_json TEXT,
                    intent_score INTEGER,
                    qualified INTEGER,
                    appointment_slot TEXT,
                    turn_count INTEGER
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS learned_knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    category TEXT NOT NULL,
                    sector TEXT NOT NULL,
                    customer_query TEXT NOT NULL,
                    learned_response TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    confidence_score REAL DEFAULT 0.85,
                    last_observed TEXT NOT NULL,
                    source_call_id TEXT,
                    UNIQUE(topic, sector)
                )
                """
            )
            cursor.execute("SELECT COUNT(*) FROM learned_knowledge")
            if cursor.fetchone()[0] == 0:
                self._seed_baseline_knowledge(cursor)
            conn.commit()

    def _seed_baseline_knowledge(self, cursor: sqlite3.Cursor) -> None:
        """Seeds initial verified clinical FAQ knowledge for Amura Health & Hospital Front-Desk."""
        now = datetime.now(timezone.utc).isoformat()
        seeds = [
            (
                "metabolic_reversal_approach",
                "clinical_program",
                "amura_metabolic",
                "Amura Health metabolic reversal approach MNT NMT",
                "Amura Health uses deep biomarker tracking, Medical Nutrition Therapy (MNT), and Natural Molecule Therapy (NMT) for root-cause chronic-care reversal.",
                now,
            ),
            (
                "care_team_structure",
                "care_team",
                "amura_metabolic",
                "Doctor physician and health coach care team",
                "Every patient at Amura Health is guided by a licensed physician alongside a dedicated life-science health coach with regular check-ins.",
                now,
            ),
            (
                "velachery_clinic_location",
                "location",
                "amura_metabolic",
                "Velachery Chennai clinic address and online telehealth",
                "Amura Health's Chennai clinic is at 11th Floor, One National Park, 142 Velachery Main Road, Chennai - 600042, with full online telehealth consultations.",
                now,
            ),
            (
                "lab_reports_whatsapp",
                "onboarding",
                "amura_metabolic",
                "Fasting insulin HbA1c lab report upload via WhatsApp",
                "You can share recent fasting glucose, fasting insulin, HbA1c, or lipid reports on WhatsApp (+91-62-622-62222) prior to your physician consultation.",
                now,
            ),
            (
                "medication_safety_policy",
                "safety",
                "amura_metabolic",
                "Medication dosage insulin adjustment safety policy",
                "Only a licensed Amura Health physician can evaluate lab reports or adjust medications after a clinical consultation; never alter doses without medical supervision.",
                now,
            ),
            (
                "emergency_108_protocol",
                "emergency",
                "amura_metabolic",
                "Emergency chest pain breathing red-flag 108 protocol",
                "For chest pain, severe shortness of breath, stroke signs, or acute distress, call 108 emergency services immediately or go to the nearest ER.",
                now,
            ),
        ]
        cursor.executemany(
            """
            INSERT OR IGNORE INTO learned_knowledge
            (topic, category, sector, customer_query, learned_response, frequency, confidence_score, last_observed)
            VALUES (?, ?, ?, ?, ?, 1, 0.95, ?)
            """,
            seeds,
        )

    def record_call(
        self,
        call_id: str,
        customer_name: str,
        customer_phone: str,
        market_mode: str,
        sector: str,
        business_name: str,
        transcript: List[Dict[str, str]],
        dossier: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Stores complete call record and runs autonomous clinical knowledge extraction."""
        now = datetime.now(timezone.utc).isoformat()
        transcript_json = json.dumps(transcript, ensure_ascii=False)
        dossier_json = json.dumps(dossier, ensure_ascii=False)
        intent_score = dossier.get("intent_score", 50)
        qualified = 1 if dossier.get("qualified") else 0
        slot = dossier.get("appointment_datetime") or ""
        turn_count = len(transcript)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO call_records (
                    call_id, timestamp, customer_name, customer_phone, market_mode,
                    sector, business_name, transcript_json, dossier_json,
                    intent_score, qualified, appointment_slot, turn_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id,
                    now,
                    customer_name,
                    customer_phone,
                    market_mode,
                    sector,
                    business_name,
                    transcript_json,
                    dossier_json,
                    intent_score,
                    qualified,
                    slot,
                    turn_count,
                ),
            )
            conn.commit()

        new_learnings = self.extract_and_learn_from_call(
            call_id=call_id,
            transcript=transcript,
            sector=sector,
            business_name=business_name,
        )

        return {
            "call_id": call_id,
            "status": "saved",
            "turn_count": turn_count,
            "new_learnings_count": len(new_learnings),
            "learnings": new_learnings,
        }

    def extract_and_learn_from_call(
        self,
        call_id: str,
        transcript: List[Dict[str, str]],
        sector: str = "amura_metabolic",
        business_name: str = "Amura Health",
    ) -> List[Dict[str, Any]]:
        """Scans patient queries in the transcript to capture clinical FAQ themes & frequencies."""
        learnings: List[Dict[str, Any]] = []
        user_turns = [t["content"] for t in transcript if t.get("role") == "user" and t.get("content")]
        now = datetime.now(timezone.utc).isoformat()

        detectors = [
            {
                "topic": "hba1c_biomarkers",
                "category": "diagnostics",
                "keywords": ["hba1c", "fasting insulin", "fasting sugar", "blood test", "lab report", "biomarker", "ரிப்போர்ட்", "लैब रिपोर्ट"],
                "query": "HbA1c, fasting insulin, and biomarker lab review",
                "response": f"{business_name} physicians review fasting insulin, HbA1c, lipid, and metabolic panels before designing your personalized care plan.",
            },
            {
                "topic": "mnt_nmt_therapy",
                "category": "clinical_program",
                "keywords": ["mnt", "nmt", "medical nutrition", "natural molecule", "diet plan", "nutrition", "டயட்", "डाइट"],
                "query": "Medical Nutrition Therapy (MNT) and Natural Molecule Therapy (NMT)",
                "response": f"At {business_name}, MNT and NMT target root-cause insulin resistance alongside physician supervision and health coaching.",
            },
            {
                "topic": "pcod_thyroid_care",
                "category": "conditions",
                "keywords": ["pcod", "pcos", "thyroid", "tsh", "hormonal", "irregular periods", "थायरॉइड"],
                "query": "PCOD/PCOS and thyroid metabolic care",
                "response": f"{business_name} provides structured physician + coach programs for PCOD/PCOS and thyroid balance.",
            },
            {
                "topic": "fatty_liver_gut",
                "category": "conditions",
                "keywords": ["fatty liver", "nafld", "gut", "gerd", "acidity", "bloating", "sgpt"],
                "query": "Fatty liver and gut inflammation reversal",
                "response": f"Our clinical team addresses fatty liver and gut inflammation via targeted nutrition, micronutrient support, and regular follow-ups.",
            },
            {
                "topic": "hypertension_cardiac",
                "category": "conditions",
                "keywords": ["hypertension", "blood pressure", "bp", "cholesterol", "triglycerides", "dyslipidemia"],
                "query": "Hypertension and dyslipidemia metabolic management",
                "response": f"{business_name} tracks blood pressure and lipid markers closely under licensed medical supervision.",
            },
            {
                "topic": "telehealth_velachery_visit",
                "category": "appointments",
                "keywords": ["velachery", "chennai", "telehealth", "online consult", "video call", "clinic visit", "வேளச்சேரி", "ऑनलाइन"],
                "query": "Online video consultation vs Velachery Chennai clinic visit",
                "response": f"You can consult {business_name} online via video from anywhere or visit our Velachery Main Road, Chennai clinic.",
            },
        ]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for user_text in user_turns:
                text_low = user_text.lower()
                for d in detectors:
                    if any(k in text_low for k in d["keywords"]):
                        topic = d["topic"]
                        cursor.execute(
                            "SELECT id, frequency FROM learned_knowledge WHERE topic = ? AND sector = ?",
                            (topic, sector),
                        )
                        existing = cursor.fetchone()
                        if existing:
                            new_freq = existing["frequency"] + 1
                            cursor.execute(
                                """
                                UPDATE learned_knowledge
                                SET frequency = ?, last_observed = ?, source_call_id = ?
                                WHERE id = ?
                                """,
                                (new_freq, now, call_id, existing["id"]),
                            )
                            learnings.append(
                                {
                                    "topic": topic,
                                    "status": "updated_frequency",
                                    "frequency": new_freq,
                                    "customer_query": d["query"],
                                }
                            )
                        else:
                            cursor.execute(
                                """
                                INSERT INTO learned_knowledge (
                                    topic, category, sector, customer_query,
                                    learned_response, frequency, confidence_score,
                                    last_observed, source_call_id
                                ) VALUES (?, ?, ?, ?, ?, 1, 0.90, ?, ?)
                                """,
                                (
                                    topic,
                                    d["category"],
                                    sector,
                                    d["query"],
                                    d["response"],
                                    now,
                                    call_id,
                                ),
                            )
                            learnings.append(
                                {
                                    "topic": topic,
                                    "status": "newly_learned",
                                    "frequency": 1,
                                    "customer_query": d["query"],
                                    "learned_response": d["response"],
                                }
                            )
            conn.commit()

        return learnings

    def find_learned_response(self, user_utterance: str, sector: str = "amura_metabolic") -> Optional[str]:
        """Matches a live user query against the continuously updated clinical knowledge base."""
        text_low = (user_utterance or "").lower().strip()
        if not text_low:
            return None
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT topic, customer_query, learned_response, frequency
                FROM learned_knowledge
                WHERE sector = ?
                ORDER BY frequency DESC
                """,
                (sector,),
            )
            rows = cursor.fetchall()
            if not rows and sector != "amura_metabolic":
                cursor.execute(
                    """
                    SELECT topic, customer_query, learned_response, frequency
                    FROM learned_knowledge
                    WHERE sector = 'amura_metabolic'
                    ORDER BY frequency DESC
                    """
                )
                rows = cursor.fetchall()

            for r in rows:
                topic_words = [w for w in r["topic"].split("_") if len(w) > 2]
                query_words = [w.strip(",.()") for w in r["customer_query"].lower().split() if len(w.strip(",.()")) > 3]
                if any(w in text_low for w in topic_words) or any(w in text_low for w in query_words):
                    return r["learned_response"]
        return None

    def get_all_learned_knowledge(self, sector: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all knowledge items acquired from patient calls."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if sector:
                cursor.execute(
                    """
                    SELECT id, topic, category, sector, customer_query, learned_response, frequency, last_observed
                    FROM learned_knowledge WHERE sector = ? ORDER BY frequency DESC
                    """,
                    (sector,),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, topic, category, sector, customer_query, learned_response, frequency, last_observed
                    FROM learned_knowledge ORDER BY frequency DESC
                    """
                )
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_calls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns the most recent recorded patient calls."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT call_id, timestamp, customer_name, customer_phone, market_mode,
                       sector, business_name, intent_score, qualified, appointment_slot, turn_count
                FROM call_records ORDER BY timestamp DESC LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """Returns database operational statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM call_records")
            total_calls = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM learned_knowledge")
            total_topics = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(frequency) FROM learned_knowledge")
            total_queries_handled = cursor.fetchone()[0] or 0

            return {
                "total_calls_recorded": total_calls,
                "total_learned_topics": total_topics,
                "total_queries_handled": total_queries_handled,
                "db_path": str(self.db_path),
            }


_GLOBAL_LEARNING_DB: Optional[LearningMemoryDB] = None


def get_learning_db(db_path: Optional[Path | str] = None) -> LearningMemoryDB:
    global _GLOBAL_LEARNING_DB
    if _GLOBAL_LEARNING_DB is None or db_path is not None:
        _GLOBAL_LEARNING_DB = LearningMemoryDB(db_path)
    return _GLOBAL_LEARNING_DB
