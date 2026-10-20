"""
Tests for India Market: Customer Care & Lead Support Executive Agent.
Verifies Indian customer support query handling, complaint ticket logging,
RERA verification, WhatsApp dispatch, BHK qualification, and market mode switching.
"""

import io
import json
import unittest
from unittest.mock import MagicMock

from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.schemas import InboundLead
from src.closer.voice.tts import normalize_speech_text, EdgeTTSVoiceEngine
from src.closer.web.dashboard import DashboardHTTPHandler


class TestIndiaCustomerCareAgent(unittest.TestCase):
    """Test suite for Indian Customer Care and Lead Qualification engine."""

    def setUp(self):
        self.lead = InboundLead(
            lead_id="ind_lead_501",
            full_name="Vikram Malhotra",
            phone_number="+91-98765-43210",
            market_region="INDIA",
            ad_campaign="Whitefield Heights Luxury Residences",
            listing_address="Prestige Whitefield, Bengaluru",
            listing_price=16500000
        )
        self.engine = ConversationEngine(lead=self.lead, market_mode="india")

    def test_indian_customer_care_initial_greeting(self):
        """Verifies polite, warm Indian customer care greeting with Namaste."""
        greeting = self.engine.get_initial_greeting()
        self.assertIn("Namaste", greeting)
        self.assertIn("Priya", greeting)
        self.assertIn("Customer Care", greeting)
        self.assertEqual(self.engine.dossier.market_region, "INDIA")
        self.assertEqual(self.engine.dossier.budget_currency, "INR")

    def test_customer_complaint_and_ticket_generation(self):
        """Verifies empathetic complaint resolution, ticket logging, and WhatsApp link."""
        reply = self.engine.process_user_turn("I have an issue with my booking payment, please register a complaint")
        self.assertIn("apologize for the inconvenience", reply.lower())
        self.assertIn("CC-84291", reply)
        self.assertEqual(self.engine.dossier.ticket_id, "CC-84291")
        self.assertEqual(self.engine.dossier.customer_type, "support_query")
        self.assertTrue(self.engine.dossier.query_resolved)
        self.assertEqual(self.engine.dossier.whatsapp_status, "sent")

    def test_rera_and_legal_clearance_inquiry(self):
        """Verifies confirmation of 100% RERA compliance and bank loan tie-ups."""
        reply = self.engine.process_user_turn("Is this property RERA registered and approved by banks?")
        self.assertIn("rera registered", reply.lower())
        self.assertIn("sbi", reply.lower())
        self.assertIn("hdfc", reply.lower())
        self.assertIn("whatsapp", reply.lower())

    def test_bhk_and_crore_pricing_qualification(self):
        """Verifies parsing of 3 BHK in Whitefield with budget in Crores."""
        reply = self.engine.process_user_turn("What is the price for a 3 BHK in Whitefield? My budget is 1.8 to 2.5 Crores.")
        self.assertEqual(self.engine.dossier.bhk_preference, "3 BHK")
        self.assertIn("Whitefield", self.engine.dossier.target_locations)
        self.assertEqual(self.engine.dossier.budget_currency, "INR")
        self.assertGreaterEqual(self.engine.dossier.budget_max, 18000000)
        self.assertTrue(self.engine.dossier.qualified)

    def test_indian_office_schedule_friction(self):
        """Verifies handling of 'in office/meeting right now, call after 6 PM'."""
        reply = self.engine.process_user_turn("I am in an office meeting right now, please call me after 6 PM")
        self.assertIn("respect your busy work hours", reply.lower())
        self.assertIn("6:00 pm", reply.lower())
        self.assertEqual(self.engine.dossier.timeframe, "callback_after_6pm")
        self.assertTrue(self.engine.dossier.whatsapp_dispatched)
        self.assertEqual(self.engine.dossier.whatsapp_status, "sent")

    def test_whatsapp_only_communication_preference(self):
        """Verifies respect for customer preference to communicate strictly on WhatsApp."""
        reply = self.engine.process_user_turn("Please don't call during work, message me on WhatsApp only")
        self.assertIn("whatsapp", reply.lower())
        self.assertEqual(self.engine.dossier.preferred_channel, "WhatsApp")
        self.assertTrue(self.engine.dossier.whatsapp_dispatched)

    def test_weekend_site_visit_booking(self):
        """Verifies booking a weekend site visit for Saturday or Sunday."""
        reply = self.engine.process_user_turn("Can I come for a site visit this weekend with my family?")
        self.assertIn("saturday", reply.lower())
        self.assertIn("sunday", reply.lower())
        self.assertEqual(self.engine.dossier.appointment_type, "weekend_site_visit")

        # Confirm Saturday slot
        confirm_reply = self.engine.process_user_turn("Saturday 11 AM works fine")
        self.assertIn("confirmed", confirm_reply.lower())
        self.assertIn("Saturday 11:00 AM", self.engine.dossier.appointment_datetime)
        self.assertTrue(self.engine.is_completed)

    def test_speech_text_normalization(self):
        """Verifies phonetic speech normalization for Indian and US currency/acronyms."""
        raw_text = "The 3 BHK in Whitefield costs ₹1.65 Cr with RERA approval. Ticket #CC-84291 sent via WhatsApp."
        clean = normalize_speech_text(raw_text)
        self.assertIn("3 B-H-K", clean)
        self.assertIn("1.65 crore rupees", clean)
        self.assertIn("R-E-R-A", clean)
        self.assertIn("Whats App", clean)
        self.assertIn("Ticket C-C 84291", clean)

    def test_market_mode_switching(self):
        """Verifies dynamic switching between USA and India modes on the engine."""
        engine = ConversationEngine(market_mode="usa")
        self.assertEqual(engine.dossier.market_region, "USA")
        self.assertEqual(engine.dossier.budget_currency, "USD")

        # Switch to India mode
        engine.set_market_mode("india")
        self.assertEqual(engine.dossier.market_region, "INDIA")
        self.assertEqual(engine.dossier.budget_currency, "INR")

        greeting = engine.get_initial_greeting()
        self.assertIn("Namaste", greeting)

    def test_post_market_mode_api(self):
        """Verifies POST /api/market_mode endpoint on DashboardHTTPHandler."""
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


if __name__ == "__main__":
    unittest.main()
