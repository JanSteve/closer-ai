"""
Unit tests for CLOSER AI Autonomous Clinical Concierge & Dynamic Script Deviation Engine.
Verifies empathetic schedule friction handling, busy/meeting constraints, async WhatsApp care guides,
and PatientDossier continuity without rigid intake looping or real-estate terminology.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.closer.memory.learning_db as ldb
from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.schemas import InboundLead

_API_KEYS = (
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "SARVAM_API_KEY",
)


class TestScriptDeviationEngine(unittest.TestCase):
    """Test suite for empathetic clinical triage schedule friction handling."""

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._env_patch = patch.dict(os.environ, {k: "" for k in _API_KEYS})
        self._env_patch.start()
        ldb._GLOBAL_LEARNING_DB = None
        self._db_patch = patch(
            "src.closer.agent.conversation.get_learning_db",
            side_effect=lambda *a, **kw: ldb.LearningMemoryDB(Path(self._tmp_dir.name) / "dev.db"),
        )
        self._db_patch.start()

        self.lead = InboundLead(
            lead_id="test_friction_patient",
            full_name="Arjun Nair",
            phone_number="+91-98400-55667",
            market_region="INDIA",
            clinic_location="11th Floor, One National Park, 142 Velachery Main Road, Chennai - 600042",
        )
        self.engine = ConversationEngine(
            lead=self.lead,
            market_mode="english",
            sector="amura_metabolic",
            business_name="Amura Health",
        )

    def tearDown(self):
        self._db_patch.stop()
        self._env_patch.stop()
        ldb._GLOBAL_LEARNING_DB = None
        self._tmp_dir.cleanup()

    def test_schedule_friction_today_not_good_come_tomorrow(self):
        reply_1 = self.engine.process_user_turn("Today is not good, I will come tomorrow")
        self.assertNotIn("what primary health concern", reply_1.lower())
        self.assertIn("respect your schedule", reply_1.lower())
        self.assertIn("tomorrow", reply_1.lower())
        self.assertTrue("11:00 am" in reply_1.lower() or "2:00 pm" in reply_1.lower())

        dossier = self.engine.export_dossier()
        self.assertEqual(dossier.timeframe, "tomorrow (immediate)")
        self.assertIn("tomorrow", dossier.follow_up_note.lower())
        self.assertIn("Accommodated schedule friction", dossier.objections_handled[0])

        reply_2 = self.engine.process_user_turn("Tomorrow afternoon works great for an online consultation.")
        self.assertIn("reserved", reply_2.lower())
        self.assertIn("Tomorrow at 2:00 PM IST", self.engine.dossier.consult_slot)
        self.assertEqual(self.engine.dossier.appointment_type, "tele_consultation")
        self.assertTrue(self.engine.is_completed)

    def test_busy_right_now_contact_me_later(self):
        reply_1 = self.engine.process_user_turn("I am busy right now, contact me later")
        self.assertNotIn("what primary health concern", reply_1.lower())
        self.assertIn("respect your time", reply_1.lower())
        self.assertTrue("callback" in reply_1.lower() or "whatsapp" in reply_1.lower())

        dossier = self.engine.export_dossier()
        self.assertIn("busy", dossier.follow_up_note.lower())
        self.assertEqual(dossier.sentiment_rating, "Polite / Busy")

        reply_2 = self.engine.process_user_turn("Please send the care guide via WhatsApp.")
        self.assertIn(self.lead.phone_number, reply_2)
        self.assertEqual(self.engine.dossier.preferred_channel, "SMS/WhatsApp")

    def test_in_a_meeting_friction(self):
        reply = self.engine.process_user_turn("I'm in a meeting right now, please call me later.")
        self.assertIn("respect your time", reply.lower())
        self.assertIn("callback", reply.lower())
        self.assertIn("meeting", self.engine.export_dossier().follow_up_note.lower())

    def test_schedule_friction_with_exact_tomorrow_hour(self):
        reply = self.engine.process_user_turn("Today is not good, I will come to the clinic tomorrow at 3 PM.")
        self.assertIn("reserved", reply.lower())
        self.assertIn("Tomorrow at 3:00 PM IST", reply)
        self.assertEqual(self.engine.dossier.consult_slot, "Tomorrow at 3:00 PM IST")
        self.assertEqual(self.engine.dossier.appointment_type, "clinic_consultation")
        self.assertTrue(self.engine.is_completed)

    def test_call_tomorrow_friction(self):
        reply_1 = self.engine.process_user_turn("Today is not good, can you call me tomorrow?")
        self.assertIn("respect your schedule", reply_1.lower())
        self.assertIn("tomorrow", reply_1.lower())

        dossier = self.engine.export_dossier()
        self.assertEqual(dossier.timeframe, "tomorrow (immediate)")
        self.assertEqual(dossier.appointment_type, "phone_consultation")
        self.assertIn("callback requested for tomorrow", dossier.follow_up_note.lower())

        reply_2 = self.engine.process_user_turn("Tomorrow afternoon works")
        self.assertIn("scheduled", reply_2.lower())
        self.assertIn("Tomorrow at 2:00 PM IST", self.engine.dossier.consult_slot)
        self.assertTrue(self.engine.is_completed)

    def test_colloquial_brush_off_today_a_wash(self):
        reply = self.engine.process_user_turn("Today's a wash, catch you on the flip side.")
        self.assertIn("care guide", reply.lower())
        self.assertTrue("sms" in reply.lower() or "whatsapp" in reply.lower())
        self.assertIn("rain check", self.engine.export_dossier().follow_up_note.lower())

    def test_compound_friction_busy_morning_evening_viable(self):
        reply = self.engine.process_user_turn(
            "I'm busy today and tomorrow morning, but tomorrow evening might work if I'm not traveling."
        )
        self.assertNotIn("11:00 AM", reply)
        self.assertIn("5:00 PM IST", reply)
        dossier = self.engine.export_dossier()
        self.assertIn("tomorrow (tentative)", dossier.timeframe)
        self.assertIn("5:00 PM IST", dossier.follow_up_note)

    def test_busy_with_direct_whatsapp_request(self):
        reply = self.engine.process_user_turn("I'm busy right now, text me the details via WhatsApp.")
        self.assertIn(self.lead.phone_number, reply)
        self.assertEqual(self.engine.dossier.preferred_channel, "SMS/WhatsApp")
        self.assertEqual(self.engine.dossier.timeframe, "async_guide_sent")

    def test_callback_relative_window_minutes(self):
        e1 = ConversationEngine(lead=self.lead, market_mode="english", business_name="Amura Health")
        e1.process_user_turn("Can you call back in 10 minutes?")
        self.assertIn("Today in 10 minutes", e1.dossier.consult_slot)
        self.assertEqual(e1.dossier.appointment_type, "phone_consultation")
        self.assertTrue(e1.is_completed)

        e2 = ConversationEngine(lead=self.lead, market_mode="english", business_name="Amura Health")
        e2.process_user_turn("Call me back in 30 minutes.")
        self.assertIn("Today in 30 minutes", e2.dossier.consult_slot)
        self.assertNotIn("30:00", e2.dossier.consult_slot)
        self.assertTrue(e2.is_completed)

    def test_meeting_variations_prevent_false_booking(self):
        for phrase in (
            "I am in a zoom meeting right now",
            "I'm in a conference right now",
            "I'm with a client right now",
            "I am in an urgent meeting",
        ):
            e = ConversationEngine(lead=self.lead, market_mode="english", business_name="Amura Health")
            reply = e.process_user_turn(phrase)
            self.assertNotIn("reserved Tomorrow", reply)
            self.assertIn("respect your time", reply.lower())
            self.assertEqual(e.dossier.sentiment_rating, "Polite / Busy")

    def test_busy_follow_up_turn_2_callback_selection(self):
        self.engine.process_user_turn("I am busy right now, contact me later")
        reply_2 = self.engine.process_user_turn("A callback would be great")
        self.assertIn("callback", reply_2.lower())
        self.assertEqual(self.engine.dossier.timeframe, "callback_scheduled")


if __name__ == "__main__":
    unittest.main()
