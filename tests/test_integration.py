"""
End-to-end integration test for CLOSER AI.
Verifies full pipeline from inbound webhook lead ingestion, voice call session, objection handling,
Google Calendar booking, Follow Up Boss CRM dispatch, and SMS confirmation.
"""

import unittest
from src.closer.agent.schemas import InboundLead
from src.closer.voice.call_session import CallSession
from src.closer.voice.tts import EdgeTTSVoiceEngine
from src.closer.integrations.calendar import CalendarManager
from src.closer.integrations.crm import CRMDispatcher
from src.closer.integrations.telephony import TelephonyManager


class TestEndToEndIntegration(unittest.TestCase):
    """Full lifecycle integration test."""

    def test_full_lead_to_booked_tour_lifecycle(self):
        """Executes a complete real-world qualification call from ad lead to confirmed VIP showing."""
        # 1. Inbound Webhook Ingestion from Instagram Ad
        telephony = TelephonyManager()
        raw_meta_webhook = {
            "lead_id": "meta_lead_78291",
            "name": "David Vance",
            "phone": "+1-310-555-0199",
            "email": "david.vance@techventures.io",
            "campaign_name": "Bel Air High-End Architecture",
            "listing_address": "10484 Bellagio Rd, Bel Air, CA",
            "listing_price": 6850000
        }
        lead = telephony.parse_inbound_lead(raw_meta_webhook, source="instagram_ad")
        self.assertEqual(lead.full_name, "David Vance")
        self.assertEqual(lead.listing_price, 6850000)

        # 2. Outbound Carrier Dispatch (<500ms Speed-to-Lead)
        outbound_res = telephony.initiate_outbound_call(lead)
        self.assertTrue(outbound_res["success"])
        self.assertLess(outbound_res["speed_to_lead_ms"], 500, "Must trigger carrier dispatch under 500ms")

        # 3. Initialize Call Session & Generate Neural Greeting
        call = CallSession(lead=lead)
        greeting_text, greeting_audio = call.start_call()
        self.assertIn("Sophia", greeting_text)
        self.assertTrue(greeting_audio.startswith(b"RIFF"))

        # 4. Turn 1: Objection ("I'm just browsing right now")
        t1_reply_text, t1_audio = call.handle_user_speech(
            audio_chunk=b"",
            simulated_text="Hi Sophia, I was just looking through the Instagram ad. Honestly I am just browsing right now."
        )
        self.assertIn("browsing is the most exciting part", t1_reply_text.lower())
        self.assertIn("just_browsing", call.engine.dossier.objections_raised)

        # 5. Turn 2: Budget & Urgent Timeline Disclosure ($5M, 30 days)
        t2_reply_text, t2_audio = call.handle_user_speech(
            audio_chunk=b"",
            simulated_text="If the right modern view property opened up, our budget is $5 million and we want to move within 30 days."
        )
        self.assertEqual(call.engine.dossier.budget_max, 5000000)
        self.assertEqual(call.engine.dossier.timeframe, "immediate (0-30 days)")

        # 6. Turn 3: Financing (All Cash)
        t3_reply_text, t3_audio = call.handle_user_speech(
            audio_chunk=b"",
            simulated_text="We sold our company last fall so this will be an all cash purchase."
        )
        self.assertEqual(call.engine.dossier.financing_type, "cash")
        self.assertTrue(call.engine.dossier.qualified)

        # 7. Turn 4: Booking Slot Selection ("Thursday at 2 PM")
        t4_reply_text, t4_audio = call.handle_user_speech(
            audio_chunk=b"",
            simulated_text="Thursday at 2:00 PM works perfectly for us to tour."
        )
        self.assertIn("reserved", t4_reply_text.lower())
        self.assertIn("Thursday", call.engine.dossier.appointment_datetime)
        self.assertEqual(call.state.status, "COMPLETED")

        # 8. Finalize Dossier
        dossier = call.end_call()
        self.assertTrue(dossier.qualified)
        self.assertGreaterEqual(dossier.intent_score, 80)

        # 9. Book in Google Calendar
        calendar = CalendarManager(persistence_file=":memory:")
        booking_result = calendar.book_appointment(
            lead_name=dossier.full_name,
            lead_phone=dossier.phone_number,
            slot_datetime=dossier.appointment_datetime,
            property_address=lead.listing_address
        )
        self.assertTrue(booking_result["success"])
        self.assertEqual(booking_result["status"], "CONFIRMED")
        self.assertTrue(booking_result["confirmation_code"].startswith("VIP-"))

        # 10. Dispatch to CRM (Follow Up Boss)
        crm = CRMDispatcher()
        crm_result = crm.dispatch(dossier)
        self.assertTrue(crm_result["success"])
        self.assertIn("#AI-Qualified", crm_result["tags_applied"])
        self.assertIn("#Cash-Buyer", crm_result["tags_applied"])
        self.assertIn("#Tour-Scheduled", crm_result["tags_applied"])
        self.assertEqual(crm_result["stage"], "Tour Scheduled")

        # 11. Send SMS Confirmation to Lead
        sms_result = telephony.send_confirmation_sms(
            to_phone=dossier.phone_number,
            lead_name=dossier.full_name,
            slot_datetime=dossier.appointment_datetime,
            property_address=lead.listing_address
        )
        self.assertTrue(sms_result["success"])
        self.assertIn("David", sms_result["body"])
        self.assertIn("10484 Bellagio Rd", sms_result["body"])


if __name__ == "__main__":
    unittest.main()
