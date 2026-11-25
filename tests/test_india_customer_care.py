"""
Tests for India Market: Amura Health Patient Care & Hospital Front-Desk Coordinator.
Verifies Indian patient support ticket logging, MNT/NMT protocol inquiry, WhatsApp dispatch,
INR care-plan qualification, clinical speech normalization, and market mode switching.
"""

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import src.closer.memory.learning_db as ldb
from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.schemas import InboundLead
from src.closer.voice.tts import normalize_speech_text
from src.closer.web.dashboard import DashboardHTTPHandler

_API_KEYS = (
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "SARVAM_API_KEY",
    "APILAYER_API_KEY",
)


class TestIndiaCustomerCareAgent(unittest.TestCase):
    """Test suite for Indian Amura Health Patient Care & Hospital Front-Desk engine."""

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._env_patch = patch.dict(os.environ, {k: "" for k in _API_KEYS})
        self._env_patch.start()
        ldb._GLOBAL_LEARNING_DB = None
        self._db_patch = patch(
            "src.closer.agent.conversation.get_learning_db",
            side_effect=lambda *a, **kw: ldb.LearningMemoryDB(Path(self._tmp_dir.name) / "india.db"),
        )
        self._db_patch.start()

        self.lead = InboundLead(
            lead_id="ind_patient_501",
            full_name="Vikram Malhotra",
            phone_number="+91-98765-43210",
            market_region="INDIA",
            ad_campaign="Amura Health Metabolic Reversal - Velachery",
            clinic_location="11th Floor, One National Park, 142 Velachery Main Road, Chennai - 600042",
        )
        self.engine = ConversationEngine(
            lead=self.lead,
            market_mode="india",
            sector="amura_metabolic",
            business_name="Amura Health",
        )

    def tearDown(self):
        self._db_patch.stop()
        self._env_patch.stop()
        ldb._GLOBAL_LEARNING_DB = None
        self._tmp_dir.cleanup()

    def test_indian_customer_care_initial_greeting(self):
        """Verifies polite Indian patient care greeting with Namaste and Amura Health."""
        greeting = self.engine.get_initial_greeting()
        self.assertIn("Namaste", greeting)
        self.assertIn("Amura Health", greeting)
        self.assertIn("Neerja", greeting)
        self.assertEqual(self.engine.dossier.market_region, "INDIA")
        self.assertEqual(self.engine.dossier.budget_currency, "INR")

    def test_customer_complaint_and_ticket_generation(self):
        """Verifies empathetic patient portal/billing complaint resolution and WhatsApp link."""
        reply = self.engine.process_user_turn(
            "I have an issue with my lab report upload on the portal, please register a complaint"
        )
        self.assertIn("apologize for the inconvenience", reply.lower())
        self.assertIn("CC-84291", reply)
        self.assertEqual(self.engine.dossier.ticket_id, "CC-84291")
        self.assertEqual(self.engine.dossier.customer_type, "support_query")
        self.assertTrue(self.engine.dossier.query_resolved)
        self.assertEqual(self.engine.dossier.whatsapp_status, "sent")

    def test_clinical_program_and_accreditation_inquiry(self):
        """Verifies explanation of physician-led MNT/NMT metabolic reversal protocol and EMI support."""
        reply = self.engine.process_user_turn(
            "Is the Amura metabolic reversal program supervised by a doctor with MNT, NMT, and EMI?"
        )
        self.assertIn("physician", reply.lower())
        self.assertIn("medical nutrition therapy", reply.lower())
        self.assertIn("whatsapp", reply.lower())

    def test_metabolic_package_and_inr_qualification(self):
        """Verifies parsing of diabetes/PCOD care & Velachery Chennai location with INR package."""
        reply = self.engine.process_user_turn(
            "I want diabetes reversal in Velachery Chennai and my budget is ₹1.25 Lakhs for a comprehensive plan."
        )
        self.assertEqual(self.engine.dossier.condition_category, "metabolic_diabetes")
        self.assertIn("Velachery", self.engine.dossier.target_locations)
        self.assertIn("Chennai", self.engine.dossier.target_locations)
        self.assertEqual(self.engine.dossier.budget_currency, "INR")
        self.assertGreaterEqual(self.engine.dossier.budget_max, 100000)
        self.assertTrue(self.engine.dossier.qualified)
        self.assertTrue(len(reply) > 10)

    def test_indian_office_schedule_friction(self):
        """Verifies handling of 'in office/meeting right now, call after 6 PM'."""
        reply = self.engine.process_user_turn("I am in an office meeting right now, please call me after 6 PM")
        self.assertIn("respect your workday schedule", reply.lower())
        self.assertIn("6:00 pm", reply.lower())
        self.assertEqual(self.engine.dossier.timeframe, "callback_after_6pm")
        self.assertTrue(self.engine.dossier.whatsapp_dispatched)
        self.assertEqual(self.engine.dossier.whatsapp_status, "sent")

    def test_whatsapp_only_communication_preference(self):
        """Verifies respect for patient preference to communicate strictly on WhatsApp."""
        reply = self.engine.process_user_turn("Please don't call during work, message me on WhatsApp only")
        self.assertIn("whatsapp", reply.lower())
        self.assertEqual(self.engine.dossier.preferred_channel, "WhatsApp")
        self.assertTrue(self.engine.dossier.whatsapp_dispatched)
        self.assertIn("whatsapp", self.engine.dossier.follow_up_note.lower())

    def test_weekend_clinic_visit_booking(self):
        """Verifies booking a weekend Velachery clinic consultation for Saturday 11:00 AM IST."""
        reply = self.engine.process_user_turn("Can I book a Velachery clinic consultation this weekend?")
        self.assertIn("saturday", reply.lower())
        self.assertIn("sunday", reply.lower())
        self.assertEqual(self.engine.dossier.appointment_type, "clinic_consultation")

        confirm_reply = self.engine.process_user_turn("Saturday 11 AM works fine")
        self.assertIn("confirmed", confirm_reply.lower())
        self.assertIn("Saturday 11:00 AM IST", self.engine.dossier.appointment_datetime)
        self.assertTrue(self.engine.is_completed)

    def test_speech_text_normalization(self):
        """Verifies phonetic speech normalization for Indian clinical text, INR currency, and acronyms."""
        raw_text = (
            "Amura Health consultation in Velachery costs ₹12,500 or ₹1.25 Lakhs with HbA1c and MNT review. "
            "Ticket #CC-84291 sent via WhatsApp."
        )
        clean = normalize_speech_text(raw_text)
        self.assertIn("12500 rupees", clean)
        self.assertIn("1.25 lakh rupees", clean)
        self.assertIn("H-b-A-1-c", clean)
        self.assertIn("Medical Nutrition Therapy", clean)
        self.assertIn("Whats App", clean)
        self.assertIn("Ticket C-C 84291", clean)

    def test_market_mode_switching(self):
        """Verifies dynamic switching between USA/English and India clinical modes."""
        engine = ConversationEngine(market_mode="usa", business_name="Amura Health")
        self.assertEqual(engine.dossier.market_region, "USA")
        self.assertEqual(engine.dossier.budget_currency, "USD")

        engine.set_market_mode("india")
        self.assertEqual(engine.dossier.market_region, "INDIA")
        self.assertEqual(engine.dossier.budget_currency, "INR")

        greeting = engine.get_initial_greeting()
        self.assertIn("Namaste", greeting)
        self.assertIn("Amura Health", greeting)

    def test_post_market_mode_api(self):
        """Verifies POST /api/market_mode endpoint on DashboardHTTPHandler with isolated DB."""
        orig_engine = DashboardHTTPHandler.conversation_engine
        try:
            DashboardHTTPHandler.conversation_engine = ConversationEngine(
                market_mode="english",
                sector="amura_metabolic",
                business_name="Amura Health",
            )
            handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
            handler.path = "/api/market_mode"
            payload = json.dumps({"mode": "india"}).encode("utf-8")
            handler.headers = {"Content-Length": str(len(payload))}
            handler.rfile = io.BytesIO(payload)
            handler.wfile = io.BytesIO()
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()

            handler.do_POST()

            handler.send_response.assert_called_with(200)
            resp = json.loads(handler.wfile.getvalue().decode("utf-8"))
            self.assertTrue(resp["success"])
            self.assertEqual(resp["mode"], "india")
            self.assertIn("Namaste", resp["greeting"])
            self.assertEqual(resp["dossier"]["market_region"], "INDIA")
        finally:
            DashboardHTTPHandler.conversation_engine = orig_engine


if __name__ == "__main__":
    unittest.main()
