"""
Unit tests for CLOSER AI Calendar Booking & Collision Prevention Engine.
Verifies slot discovery, collision rejection, and duplicate booking prevention.
"""

import os
import unittest
import tempfile
from src.closer.integrations.calendar import CalendarManager


class TestCalendarBooking(unittest.TestCase):
    """Test suite for Google Calendar / Calendly appointment manager."""

    def setUp(self):
        # Use a temporary file for isolated persistence tests
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
        """Verifies initial slots are open and formatted correctly."""
        slots = self.cal.get_available_slots("2026-10-24")
        self.assertGreaterEqual(len(slots), 4)
        self.assertIn("2026-10-24 02:00 PM PST", slots)

    def test_successful_booking(self):
        """Verifies booking a showing reserves the slot and returns a confirmation code."""
        slot = "2026-10-24 02:00 PM PST"
        res = self.cal.book_appointment(
            lead_name="Harrison Sterling",
            lead_phone="+1-310-555-0144",
            slot_datetime=slot,
            property_address="10484 Bellagio Rd, Bel Air, CA"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "CONFIRMED")
        self.assertTrue(res["confirmation_code"].startswith("VIP-"))
        self.assertFalse(self.cal.is_slot_available(slot))

    def test_collision_detection(self):
        """Verifies attempting to double-book the same slot raises a collision error."""
        slot = "2026-10-24 03:30 PM PST"
        # First booking succeeds
        self.cal.book_appointment(
            lead_name="Buyer Alpha",
            lead_phone="+1-310-555-0111",
            slot_datetime=slot
        )
        
        # Second buyer attempts the exact same slot -> must fail with ValueError
        with self.assertRaises(ValueError) as ctx:
            self.cal.book_appointment(
                lead_name="Buyer Beta",
                lead_phone="+1-310-555-0222",
                slot_datetime=slot
            )
        self.assertIn("Calendar collision", str(ctx.exception))

    def test_duplicate_booking_idempotency(self):
        """Verifies same lead re-submitting same slot returns ALREADY_BOOKED idempotently without error."""
        slot = "2026-10-24 11:30 AM PST"
        res1 = self.cal.book_appointment(
            lead_name="David Vance",
            lead_phone="+1-310-555-0199",
            slot_datetime=slot
        )
        self.assertEqual(res1["status"], "CONFIRMED")

        # Second submission by same client
        res2 = self.cal.book_appointment(
            lead_name="David Vance",
            lead_phone="+1-310-555-0199",
            slot_datetime=slot
        )
        self.assertEqual(res2["status"], "ALREADY_BOOKED")
        self.assertEqual(res1["confirmation_code"], res2["confirmation_code"])

    def test_cancel_appointment(self):
        """Verifies cancellation frees the slot for other buyers."""
        slot = "2026-10-24 05:00 PM PST"
        res = self.cal.book_appointment(
            lead_name="Elena Rostova",
            lead_phone="+1-415-555-0199",
            slot_datetime=slot
        )
        booking_id = res["booking_id"]
        self.assertFalse(self.cal.is_slot_available(slot))

        cancelled = self.cal.cancel_appointment(booking_id)
        self.assertTrue(cancelled)
        self.assertTrue(self.cal.is_slot_available(slot))


if __name__ == "__main__":
    unittest.main()
