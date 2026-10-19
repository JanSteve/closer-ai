"""
Unit tests for CLOSER AI Autonomous Rational Reasoning & Dynamic Script Deviation Engine.
Verifies empathetic objection resolution, schedule friction handling, busy/meeting constraints,
and Pydantic buyer dossier continuity without rigid script looping.
"""

import unittest
from src.closer.agent.schemas import InboundLead, BuyerDossier
from src.closer.agent.conversation import ConversationEngine


class TestScriptDeviationEngine(unittest.TestCase):
    """Test suite for autonomous concierge problem-solving and schedule friction handling."""

    def setUp(self):
        self.lead = InboundLead(
            lead_id="test_friction_lead",
            full_name="Alexander Wright",
            phone_number="+1-310-555-0177",
            listing_address="10484 Bellagio Rd, Bel Air, CA",
            listing_price=6850000
        )
        self.engine = ConversationEngine(lead=self.lead)

    def test_schedule_friction_today_not_good_come_tomorrow(self):
        """
        Verifies that 'Today is not good, I will come tomorrow' triggers an empathetic,
        rational response offering tomorrow's time window, rather than repeating the initial sales pitch.
        """
        # Buyer presents schedule friction
        reply_1 = self.engine.process_user_turn("Today is not good, I will come tomorrow")
        
        # Must NOT force rigid canned script questions
        self.assertNotIn("When acquiring in prime areas", reply_1)
        self.assertNotIn("What price comfort range", reply_1)
        
        # Must reason empathetically & offer tomorrow's window
        self.assertIn("respect your schedule", reply_1.lower())
        self.assertIn("tomorrow", reply_1.lower())
        self.assertTrue(
            "11:00 am" in reply_1.lower() or "afternoon at 2:00 pm" in reply_1.lower(),
            f"Expected morning vs afternoon offering in: {reply_1}"
        )
        
        # Pydantic dossier must reflect requested timeframe and follow-up notes
        dossier = self.engine.export_dossier()
        self.assertEqual(dossier.timeframe, "tomorrow (immediate)")
        self.assertIsNotNone(dossier.follow_up_note)
        self.assertIn("tomorrow", dossier.follow_up_note.lower())
        self.assertIn("Accommodated schedule friction", dossier.objections_handled[0])

        # Turn 2: Buyer accepts tomorrow afternoon
        reply_2 = self.engine.process_user_turn("Tomorrow afternoon works great for me.")
        self.assertIn("reserved", reply_2.lower())
        self.assertIn("Tomorrow at 2:00 PM PST", self.engine.dossier.appointment_datetime)
        self.assertEqual(self.engine.dossier.appointment_type, "private_vip_tour")
        self.assertTrue(self.engine.is_completed)

    def test_busy_right_now_contact_me_later(self):
        """
        Verifies that 'I am busy right now, contact me later' is met with polite respect
        for their time and an offer for a callback window or async SMS/WhatsApp brochure.
        """
        reply_1 = self.engine.process_user_turn("I am busy right now, contact me later")
        
        # Must NOT repeat canned qualification questions
        self.assertNotIn("When acquiring in prime areas", reply_1)
        
        # Must show high EQ respect for their busy schedule
        self.assertIn("respect your time", reply_1.lower())
        self.assertTrue(
            "callback" in reply_1.lower() or "sms" in reply_1.lower() or "whatsapp" in reply_1.lower(),
            f"Expected callback or SMS/WhatsApp offer in: {reply_1}"
        )
        
        # Verify dossier updates seamlessly
        dossier = self.engine.export_dossier()
        self.assertIsNotNone(dossier.follow_up_note)
        self.assertIn("busy", dossier.follow_up_note.lower())
        self.assertEqual(dossier.sentiment_rating, "Polite / Busy")

        # Turn 2: Buyer requests async digital brochure
        reply_2 = self.engine.process_user_turn("Please text it to me via WhatsApp.")
        self.assertIn("text", reply_2.lower())
        self.assertIn(self.lead.phone_number, reply_2)
        self.assertEqual(self.engine.dossier.preferred_channel, "SMS/WhatsApp")

    def test_in_a_meeting_friction(self):
        """Verifies utterance 'I'm in a meeting right now' triggers courteous, frictionless handling."""
        reply = self.engine.process_user_turn("I'm in a meeting right now, please call me later.")
        self.assertIn("respect your time", reply.lower())
        self.assertIn("callback", reply.lower())
        
        dossier = self.engine.export_dossier()
        self.assertIn("meeting", dossier.follow_up_note.lower())

    def test_schedule_friction_with_exact_tomorrow_hour(self):
        """Verifies buyer directly providing tomorrow hour locks in booking without friction."""
        reply = self.engine.process_user_turn("Today is not good, I will come tomorrow at 3 PM.")
        self.assertIn("reserved", reply.lower())
        self.assertIn("Tomorrow at 3:00 PM PST", reply)
        self.assertEqual(self.engine.dossier.appointment_datetime, "Tomorrow at 3:00 PM PST")
        self.assertTrue(self.engine.is_completed)

    def test_call_tomorrow_friction(self):
        """
        Verifies that 'call tomorrow' / 'can you call tomorrow' triggers an empathetic
        callback deferral response offering tomorrow's window, rather than a tour walkthrough
        or rigid budget script loop.
        """
        reply_1 = self.engine.process_user_turn("Today is not good, can you call me tomorrow?")
        
        # Must NOT force rigid canned script questions
        self.assertNotIn("When acquiring in prime areas", reply_1)
        self.assertNotIn("What price comfort range", reply_1)
        
        # Must reason empathetically & offer tomorrow's callback window
        self.assertIn("respect your schedule", reply_1.lower())
        self.assertIn("tomorrow", reply_1.lower())
        self.assertIn("call", reply_1.lower())
        
        # Dossier must record callback request
        dossier = self.engine.export_dossier()
        self.assertEqual(dossier.timeframe, "tomorrow (immediate)")
        self.assertEqual(dossier.appointment_type, "phone_consultation")
        self.assertIn("callback requested for tomorrow", dossier.follow_up_note.lower())

        # Turn 2: Buyer accepts tomorrow afternoon
        reply_2 = self.engine.process_user_turn("Tomorrow afternoon works")
        self.assertIn("scheduled", reply_2.lower())
        self.assertIn("Tomorrow at 2:00 PM PST", self.engine.dossier.appointment_datetime)
        self.assertEqual(self.engine.dossier.appointment_type, "phone_consultation")
        self.assertTrue(self.engine.is_completed)

    def test_colloquial_brush_off_today_a_wash(self):
        """
        Verifies colloquial friction phrasing ('today is a wash, catch you on the flip side')
        is met with high EQ rain check acknowledgment and async brochure offer.
        """
        reply = self.engine.process_user_turn("Today's a wash, catch you on the flip side.")
        
        self.assertNotIn("When acquiring in prime areas", reply)
        self.assertIn("rain check", reply.lower())
        self.assertTrue("sms" in reply.lower() or "whatsapp" in reply.lower())
        
        dossier = self.engine.export_dossier()
        self.assertIsNotNone(dossier.follow_up_note)
        self.assertIn("rain check", dossier.follow_up_note.lower())

    def test_compound_friction_busy_morning_evening_viable(self):
        """
        Verifies compound friction with conflicting time constraints:
        'I'm busy today and tomorrow morning, but tomorrow evening might work if I'm not traveling'
        correctly avoids booking the morning slot and addresses tomorrow evening.
        """
        reply = self.engine.process_user_turn(
            "I'm busy today and tomorrow morning, but tomorrow evening might work if I'm not traveling."
        )
        
        # Must NOT book 11:00 AM morning
        self.assertNotIn("11:00 AM", reply)
        self.assertIn("5:00 PM", reply)
        self.assertTrue("tentative" in reply.lower() or "brochure" in reply.lower())
        
        dossier = self.engine.export_dossier()
        self.assertIn("tomorrow (tentative)", dossier.timeframe)
        self.assertIn("5:00 PM", dossier.follow_up_note)

    def test_busy_with_direct_whatsapp_request(self):
        """
        Verifies that when a busy buyer directly requests WhatsApp/SMS text,
        the AI immediately confirms sending the brochure rather than asking if they want a call.
        """
        reply = self.engine.process_user_turn("I'm busy right now, text me the details via WhatsApp.")
        
        self.assertIn("text", reply.lower())
        self.assertIn(self.lead.phone_number, reply)
        self.assertEqual(self.engine.dossier.preferred_channel, "SMS/WhatsApp")
        self.assertEqual(self.engine.dossier.timeframe, "async_brochure_sent")

    def test_callback_relative_window_minutes(self):
        """
        Verifies relative callback time expressions like 'in 10 minutes' and 'in 30 minutes'
        are correctly parsed and not mangled into nonsensical hours like 30:00 PM.
        """
        e1 = ConversationEngine(lead=self.lead)
        r1 = e1.process_user_turn("Can you call back in 10 minutes?")
        self.assertIn("Today in 10 minutes", e1.dossier.appointment_datetime)
        self.assertEqual(e1.dossier.appointment_type, "phone_consultation")
        self.assertTrue(e1.is_completed)

        e2 = ConversationEngine(lead=self.lead)
        r2 = e2.process_user_turn("Call me back in 30 minutes.")
        self.assertIn("Today in 30 minutes", e2.dossier.appointment_datetime)
        self.assertNotIn("30:00", e2.dossier.appointment_datetime)
        self.assertTrue(e2.is_completed)

    def test_meeting_variations_prevent_false_booking(self):
        """
        Verifies that saying 'in a zoom meeting', 'in a conference', or 'with a client'
        never false-books a VIP tour walkthrough.
        """
        for phrase in [
            "I am in a zoom meeting right now",
            "I'm in a conference right now",
            "I'm with a client right now",
            "I am in an urgent meeting"
        ]:
            e = ConversationEngine(lead=self.lead)
            reply = e.process_user_turn(phrase)
            self.assertNotIn("reserved Tomorrow", reply, f"False booking occurred for phrase: {phrase}")
            self.assertIn("respect your time", reply.lower())
            self.assertEqual(e.dossier.sentiment_rating, "Polite / Busy")

    def test_busy_follow_up_turn_2_callback_selection(self):
        """
        Verifies that when a busy buyer replies 'A callback would be great' on Turn 2,
        the AI accommodates the callback rather than reverting to the rigid budget qualification.
        """
        # Turn 1: busy friction
        self.engine.process_user_turn("I am busy right now, contact me later")
        
        # Turn 2: buyer chooses callback
        reply_2 = self.engine.process_user_turn("A callback would be great")
        self.assertNotIn("When acquiring in prime areas", reply_2)
        self.assertNotIn("What price comfort range", reply_2)
        self.assertIn("callback", reply_2.lower())
        self.assertEqual(self.engine.dossier.timeframe, "callback_scheduled")


if __name__ == "__main__":
    unittest.main()
