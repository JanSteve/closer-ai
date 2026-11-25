"""
Unit tests for CLOSER AI Amura Health Consultation Calendar & Collision Prevention Engine.
Verifies IST slot discovery, clinic booking, collision rejection, and duplicate booking idempotency.
"""

import os
import tempfile
import unittest

from src.closer.integrations.calendar import CalendarManager


class TestCalendarBooking(unittest.TestCase):
    """Test suite for Amura Health consultation calendar manager."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_file.close()
        self.cal = CalendarManager(persistence_file=self.temp_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
            except OSError:
                pass

    def test_get_available_slots(self):
        """Verifies initial IST consultation slots are open and formatted correctly."""
        slots = self.cal.get_available_slots("2026-10-24")
        self.assertGreaterEqual(len(slots), 4)
        self.assertIn("2026-10-24 02:00 PM IST", slots)

    def test_successful_booking(self):
        """Verifies booking an Amura consultation reserves the slot and returns an AMR- confirmation code."""
        slot = "2026-10-24 02:00 PM IST"
        res = self.cal.book_appointment(
            lead_name="Priya Raman",
            lead_phone="+91-98400-11223",
            slot_datetime=slot,
            clinic_location="11th Floor, One National Park, 142 Velachery Main Road, Chennai - 600042",
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "CONFIRMED")
        self.assertTrue(res["confirmation_code"].startswith("AMR-"))
        self.assertIn("Amura", res["event"]["notes"])
        self.assertFalse(self.cal.is_slot_available(slot))

    def test_collision_detection(self):
        """Verifies attempting to double-book the same IST slot raises a collision error."""
        slot = "2026-10-24 04:00 PM IST"
        self.cal.book_appointment(
            lead_name="Patient Alpha",
            lead_phone="+91-98400-11111",
            slot_datetime=slot,
        )

        with self.assertRaises(ValueError) as ctx:
            self.cal.book_appointment(
                lead_name="Patient Beta",
                lead_phone="+91-98400-22222",
                slot_datetime=slot,
            )
        self.assertIn("Calendar collision", str(ctx.exception))

    def test_duplicate_booking_idempotency(self):
        """Verifies same patient re-submitting same slot returns ALREADY_BOOKED idempotently."""
        slot = "2026-10-24 11:30 AM IST"
        res1 = self.cal.book_appointment(
            lead_name="Karthik Subramanian",
            lead_phone="+91-98400-12345",
            slot_datetime=slot,
        )
        self.assertEqual(res1["status"], "CONFIRMED")

        res2 = self.cal.book_appointment(
            lead_name="Karthik Subramanian",
            lead_phone="+91-98400-12345",
            slot_datetime=slot,
        )
        self.assertEqual(res2["status"], "ALREADY_BOOKED")
        self.assertEqual(res1["confirmation_code"], res2["confirmation_code"])

    def test_cancel_appointment(self):
        """Verifies cancellation frees the IST slot for other patients."""
        slot = "2026-10-24 05:30 PM IST"
        res = self.cal.book_appointment(
            lead_name="Meera Nair",
            lead_phone="+91-98400-33445",
            slot_datetime=slot,
        )
        booking_id = res["booking_id"]
        self.assertFalse(self.cal.is_slot_available(slot))

        cancelled = self.cal.cancel_appointment(booking_id)
        self.assertTrue(cancelled)
        self.assertTrue(self.cal.is_slot_available(slot))


if __name__ == "__main__":
    unittest.main()
