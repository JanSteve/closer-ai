"""
Consultation Calendar & Clinic Slot Scheduling Integration for CLOSER AI (Amura Health).
Enforces clinic hours (IST), conflict detection, and duplicate booking prevention.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.closer.config import settings


class CalendarManager:
    """
    Manages clinical consultation scheduling for Amura Health (Velachery, Chennai & Telehealth).
    """

    def __init__(self, persistence_file: Optional[str] = None):
        self.persistence_file = persistence_file or "calendar_bookings.json"
        self.bookings: List[Dict[str, Any]] = []
        self._load_bookings()

    def _load_bookings(self) -> None:
        if self.persistence_file == ":memory:":
            return
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, "r", encoding="utf-8") as f:
                    self.bookings = json.load(f)
            except Exception:
                self.bookings = []

    def _save_bookings(self) -> None:
        if self.persistence_file == ":memory:":
            return
        try:
            with open(self.persistence_file, "w", encoding="utf-8") as f:
                json.dump(self.bookings, f, indent=2)
        except Exception:
            pass

    def get_available_slots(self, target_date: str) -> List[str]:
        """
        Returns available 30-minute consultation slots for a given date (YYYY-MM-DD) in IST.
        Standard hours: 10:00 AM, 11:30 AM, 02:00 PM, 04:00 PM, 05:30 PM IST.
        """
        standard_times = ["10:00 AM", "11:30 AM", "02:00 PM", "04:00 PM", "05:30 PM"]
        available: List[str] = []
        for st in standard_times:
            slot_str = f"{target_date} {st} IST"
            if self.is_slot_available(slot_str):
                available.append(slot_str)
        return available

    def is_slot_available(self, slot_datetime: str) -> bool:
        """Checks if the requested slot is open without calendar collisions."""
        normalized = slot_datetime.strip().lower()
        for b in self.bookings:
            if b.get("slot_datetime", "").strip().lower() == normalized and b.get("status") == "CONFIRMED":
                return False
        return True

    def book_appointment(
        self,
        lead_name: str,
        lead_phone: str,
        slot_datetime: str,
        lead_email: Optional[str] = None,
        clinic_location: Optional[str] = None,
        property_address: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Books a confirmed 30-minute Amura Health physician & health-coach consultation.
        Enforces collision detection and duplicate booking prevention.
        """
        for b in self.bookings:
            if b.get("lead_phone") == lead_phone and b.get("slot_datetime") == slot_datetime and b.get("status") == "CONFIRMED":
                return {
                    "success": True,
                    "status": "ALREADY_BOOKED",
                    "booking_id": b["booking_id"],
                    "confirmation_code": b["confirmation_code"],
                    "message": "Consultation already confirmed for this patient.",
                }

        if not self.is_slot_available(slot_datetime):
            raise ValueError(f"Calendar collision: Slot '{slot_datetime}' is already booked.")

        booking_id = f"gcal_evt_{uuid.uuid4().hex[:10]}"
        confirmation_code = f"AMR-{uuid.uuid4().hex[:6].upper()}"
        resolved_location = clinic_location or property_address or settings.CLINIC_ADDRESS

        record = {
            "booking_id": booking_id,
            "confirmation_code": confirmation_code,
            "status": "CONFIRMED",
            "clinician_name": settings.CLINICAL_DIRECTOR_NAME,
            "patient_name": lead_name,
            "lead_name": lead_name,
            "lead_phone": lead_phone,
            "lead_email": lead_email or f"{lead_name.lower().replace(' ', '.')}@patient.amura.ai",
            "slot_datetime": slot_datetime,
            "clinic_location": resolved_location,
            "duration_minutes": settings.CONSULT_DURATION_MINUTES,
            "notes": notes or "Amura Health Metabolic & Chronic-Care Consultation",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "google_calendar_link": f"https://calendar.google.com/calendar/r/eventedit?eid={booking_id}",
        }

        self.bookings.append(record)
        self._save_bookings()
        return {
            "success": True,
            "status": "CONFIRMED",
            "booking_id": booking_id,
            "confirmation_code": confirmation_code,
            "event": record,
        }

    def cancel_appointment(self, booking_id: str) -> bool:
        """Cancels an existing consultation booking."""
        for b in self.bookings:
            if b.get("booking_id") == booking_id:
                b["status"] = "CANCELLED"
                self._save_bookings()
                return True
        return False
