"""
Unit tests for Milestone 3: Tri-Language Dialect, Personas & Pydantic BANT Schema.
Verifies US 1031 tax-deferred exchanges, Aspen compound tours, jumbo financing desks,
Indian customer care ticket #CC-84291 SLA, Hindi honorifics & site visits, and BANT schema extraction.
"""

import unittest
from src.closer.agent.schemas import InboundLead, BuyerDossier, CallSessionState
from src.closer.agent.conversation import ConversationEngine


class TestTriLanguageAndBantSchema(unittest.TestCase):
    """Test suite for Milestone 3 tri-language specialization and BANT schema."""

    def test_bant_schema_attributes_and_aliases(self):
        """Verifies Pydantic v2 BANT fields, property aliases, and JSON serialization."""
        dossier = BuyerDossier(
            full_name="Eleanor Vance",
            phone_number="+1-310-555-0188",
            bant_budget_qualified=True,
            bant_authority_verified="Sole Decision Maker",
            bant_need_identified="Modern Architectural View Estate in Bel Air",
            bant_timeline_confirmed="45-day identification deadline",
            tax_exchange_1031=True,
            exchange_deadline_days=45,
            response_latency_tier="cognitive_paced",
            disfluency_type="cognitive_hesitation"
        )

        # Direct field assertions
        self.assertTrue(dossier.bant_budget_qualified)
        self.assertEqual(dossier.bant_authority_verified, "Sole Decision Maker")
        self.assertEqual(dossier.bant_need_identified, "Modern Architectural View Estate in Bel Air")
        self.assertEqual(dossier.bant_timeline_confirmed, "45-day identification deadline")
        self.assertTrue(dossier.tax_exchange_1031)
        self.assertEqual(dossier.exchange_deadline_days, 45)
        self.assertEqual(dossier.response_latency_tier, "cognitive_paced")
        self.assertEqual(dossier.disfluency_type, "cognitive_hesitation")

        # Property alias accessors
        self.assertTrue(dossier.bant_budget)
        self.assertEqual(dossier.bant_authority, "Sole Decision Maker")
        self.assertEqual(dossier.bant_need, "Modern Architectural View Estate in Bel Air")
        self.assertEqual(dossier.bant_timeline, "45-day identification deadline")

        # Property setter verification
        dossier.bant_authority = "Family Office / Trust"
        self.assertEqual(dossier.bant_authority_verified, "Family Office / Trust")
        dossier.bant_need = "Penthouse in Aspen"
        self.assertEqual(dossier.bant_need_identified, "Penthouse in Aspen")
        dossier.bant_timeline = "Immediate 30 days"
        self.assertEqual(dossier.bant_timeline_confirmed, "Immediate 30 days")
        dossier.bant_budget = False
        self.assertFalse(dossier.bant_budget_qualified)

        # Serialization test
        dump = dossier.model_dump()
        self.assertIn("bant_budget_qualified", dump)
        self.assertIn("tax_exchange_1031", dump)
        self.assertIn("exchange_deadline_days", dump)
        self.assertIn("response_latency_tier", dump)

        json_str = dossier.model_dump_json()
        self.assertIn("tax_exchange_1031", json_str)

        # CallSessionState verification
        session_state = CallSessionState(
            session_id="sess_test_01",
            lead_id="lead_test_01",
            caller_phone="+1-310-555-0100",
            recipient_phone="+1-310-555-0101",
            latency_tier="cognitive_paced",
            target_latency_ms=280
        )
        self.assertEqual(session_state.latency_tier, "cognitive_paced")
        self.assertEqual(session_state.target_latency_ms, 280)

    def test_us_1031_tax_exchange_and_aspen_tours(self):
        """Verifies 1031 tax exchange playbook, 45-day timeline, QI authority, and Aspen compound tours."""
        lead = InboundLead(
            lead_id="lead_1031_aspen",
            full_name="Harrison Ford",
            phone_number="+1-310-555-0199",
            listing_address="10484 Bellagio Rd, Bel Air, CA"
        )
        engine = ConversationEngine(lead=lead, market_mode="usa")

        reply = engine.process_user_turn(
            "We are executing a 1031 tax exchange for a private mountain compound in Aspen and have 45 days to identify a replacement property."
        )

        # Response asserts
        self.assertIn("1031 tax-deferred exchange", reply.lower())
        self.assertIn("qualified intermediaries", reply.lower())
        self.assertIn("aspen", reply.lower())
        self.assertIn("45-day", reply.lower())

        # Dossier asserts
        dossier = engine.export_dossier()
        self.assertTrue(dossier.tax_exchange_1031)
        self.assertEqual(dossier.exchange_deadline_days, 45)
        self.assertIn("Aspen", dossier.target_locations)
        self.assertEqual(dossier.bant_timeline_confirmed, "45-day identification deadline")
        self.assertEqual(dossier.bant_authority_verified, "Qualified Intermediary / 1031 Entity")
        self.assertIn("1031 Exchange Replacement Estate", dossier.bant_need_identified)
        self.assertIn("Aspen", dossier.bant_need_identified)
        self.assertTrue(dossier.bant_budget_qualified)
        self.assertTrue(dossier.qualified)
        self.assertEqual(dossier.response_latency_tier, "cognitive_paced")

    def test_us_jumbo_financing_desk_jp_morgan_and_first_republic(self):
        """Verifies jumbo mortgage financing desk and private banking partnership extraction."""
        lead = InboundLead(
            lead_id="lead_jumbo",
            full_name="Marcus Vance",
            phone_number="+1-310-555-0144"
        )
        engine = ConversationEngine(lead=lead, market_mode="usa")

        reply = engine.process_user_turn(
            "We are looking in Beverly Hills and will be arranging a bespoke jumbo mortgage through J.P. Morgan Private Bank."
        )

        # Response asserts
        self.assertIn("private banking desks", reply.lower())
        self.assertIn("j.p. morgan", reply.lower())
        self.assertIn("jumbo financing", reply.lower())

        # Dossier asserts
        dossier = engine.export_dossier()
        self.assertEqual(dossier.financing_type, "private_banking")
        self.assertEqual(dossier.lender_name, "J.P. Morgan Private Bank")
        self.assertTrue(dossier.pre_approved)
        self.assertTrue(dossier.bant_budget_qualified)
        self.assertIn("Beverly Hills", dossier.target_locations)

    def test_us_bant_authority_variations(self):
        """Verifies authority verification across sole buyer, spouse co-buyer, family office, and trust."""
        # 1. Sole Decision Maker
        e1 = ConversationEngine(market_mode="usa")
        e1.process_user_turn("I am the sole decision maker and purchasing on my own.")
        self.assertEqual(e1.dossier.bant_authority_verified, "Sole Decision Maker")

        # 2. Co-Buyer with Spouse
        e2 = ConversationEngine(market_mode="usa")
        e2.process_user_turn("My wife and I will be touring properties together.")
        self.assertEqual(e2.dossier.bant_authority_verified, "Co-Buyer with Spouse/Partner")

        # 3. Family Office / Trust
        e3 = ConversationEngine(market_mode="usa")
        e3.process_user_turn("The estate will be acquired through our family office trust.")
        self.assertEqual(e3.dossier.bant_authority_verified, "Family Office / Trust")

        # 4. Corporate Entity / LLC
        e4 = ConversationEngine(market_mode="usa")
        e4.process_user_turn("We will hold the deed in our real estate holding LLC.")
        self.assertEqual(e4.dossier.bant_authority_verified, "Corporate Entity / LLC")

    def test_india_customer_care_cc84291_sla(self):
        """Verifies customer complaint resolution, priority ticket #CC-84291, and 2-hour manager SLA."""
        lead = InboundLead(
            lead_id="lead_ind_sla",
            full_name="Rajesh Khanna",
            phone_number="+91-98765-88888",
            market_region="INDIA"
        )
        engine = ConversationEngine(lead=lead, market_mode="india")

        reply = engine.process_user_turn(
            "I have a major service issue with delayed documentation, please log a complaint and escalate."
        )

        # Response asserts
        self.assertIn("apologize for the inconvenience", reply.lower())
        self.assertIn("CC-84291", reply)
        self.assertIn("two hours", reply.lower())
        self.assertIn("whatsapp", reply.lower())

        # Dossier asserts
        dossier = engine.export_dossier()
        self.assertEqual(dossier.ticket_id, "CC-84291")
        self.assertEqual(dossier.customer_type, "support_query")
        self.assertEqual(dossier.query_type, "customer_complaint")
        self.assertTrue(dossier.query_resolved)
        self.assertTrue(dossier.whatsapp_dispatched)
        self.assertEqual(dossier.bant_timeline_confirmed, "2-hour senior manager resolution SLA")
        self.assertEqual(dossier.bant_authority_verified, "Authorized Account Holder")
        self.assertEqual(dossier.response_latency_tier, "cognitive_paced")

    def test_india_pricing_and_weekend_vip_site_visit(self):
        """Verifies Indian Lakhs/Crores pricing, RERA bank approvals, and weekend site visit confirmation."""
        lead = InboundLead(
            lead_id="lead_ind_visit",
            full_name="Deepak Chopra",
            phone_number="+91-98765-99999",
            market_region="INDIA"
        )
        engine = ConversationEngine(lead=lead, market_mode="india")

        # Turn 1: 3 BHK in Whitefield with Lakhs/Crores pricing
        r1 = engine.process_user_turn("What is the price for a 3 BHK in Whitefield?")
        self.assertIn("95 lakhs", r1.lower())
        self.assertIn("1.65 crores", r1.lower())
        self.assertEqual(engine.dossier.bhk_preference, "3 BHK")
        self.assertEqual(engine.dossier.budget_max, 16500000)
        self.assertTrue(engine.dossier.bant_budget_qualified)
        self.assertIn("Whitefield", engine.dossier.target_locations)
        self.assertIn("3 BHK Luxury Apartment in Whitefield", engine.dossier.bant_need_identified)

        # Turn 2: Confirm Saturday 11 AM VIP site visit
        r2 = engine.process_user_turn("Can we confirm a site visit for Saturday 11 AM?")
        self.assertIn("confirmed", r2.lower())
        self.assertIn("Saturday 11:00 AM", r2)
        self.assertIn("whatsapp", r2.lower())

        dossier = engine.export_dossier()
        self.assertEqual(dossier.appointment_datetime, "Saturday 11:00 AM")
        self.assertEqual(dossier.appointment_type, "weekend_site_visit")
        self.assertEqual(dossier.bant_timeline_confirmed, "Weekend VIP Site Visit: Saturday 11:00 AM")
        self.assertEqual(dossier.bant_authority_verified, "Family Decision Maker")
        self.assertTrue(dossier.whatsapp_dispatched)
        self.assertTrue(engine.is_completed)

    def test_hindi_vernacular_honorifics_rera_and_site_visit(self):
        """Verifies native Hindi honorifics ("आप", "जी बिल्कुल"), RERA, ₹ लाख / ₹ करोड़, and site visit booking."""
        lead = InboundLead(
            lead_id="lead_hi_01",
            full_name="सुनील वर्मा",
            phone_number="+91-98765-11111",
            market_region="INDIA_HINDI"
        )
        engine = ConversationEngine(lead=lead, market_mode="hindi")

        # Initial greeting
        greeting = engine.get_initial_greeting()
        self.assertIn("नमस्ते जी", greeting)
        self.assertIn("स्वाति", greeting)

        # Turn 1: RERA and 3 BHK inquiries
        r1 = engine.process_user_turn("नमस्ते जी, क्या आपका 3 बीएचके प्रोजेक्ट 100% रेरा अप्रूवड है?")
        self.assertIn("जी बिल्कुल", r1)
        self.assertIn("रेरा (RERA) रजिस्टर्ड", r1)
        self.assertIn("एसबीआई व एचडीएफसी बैंक", r1)
        self.assertEqual(engine.dossier.bhk_preference, "3 BHK")
        self.assertEqual(engine.dossier.budget_max, 16500000)
        self.assertTrue(engine.dossier.bant_budget_qualified)
        self.assertIn("3 BHK Luxury Apartment", engine.dossier.bant_need_identified)

        # Turn 2: Saturday 11 AM site visit
        r2 = engine.process_user_turn("हाँ जी, क्या शनिवार सुबह 11 बजे की साइट विज़िट बुक कर सकते हैं?")
        self.assertIn("शनिवार सुबह 11:00 बजे", r2)
        self.assertIn("वॉट्सऐप", r2)

        dossier = engine.export_dossier()
        self.assertEqual(dossier.appointment_datetime, "शनिवार सुबह 11:00 बजे")
        self.assertEqual(dossier.appointment_type, "weekend_site_visit")
        self.assertEqual(dossier.bant_timeline_confirmed, "साइट विज़िट: शनिवार सुबह 11:00 बजे")
        self.assertEqual(dossier.bant_authority_verified, "पारिवारिक निर्णय / मुख्य खरीदार")
        self.assertTrue(dossier.whatsapp_dispatched)
        self.assertTrue(engine.is_completed)

    def test_hindi_customer_complaint_and_sla_ticket(self):
        """Verifies native Hindi complaint handling, #CC-84291 ticket assignment, and manager SLA."""
        lead = InboundLead(
            lead_id="lead_hi_complaint",
            full_name="कविता शर्मा",
            phone_number="+91-98765-22222",
            market_region="INDIA_HINDI"
        )
        engine = ConversationEngine(lead=lead, market_mode="hindi")

        reply = engine.process_user_turn("मेरी बुकिंग में समस्या आ रही है, मुझे कंप्लेंट दर्ज करवानी है।")
        self.assertIn("असुविधा के लिए मैं दिल से माफ़ी चाहती हूँ", reply)
        self.assertIn("#CC-84291", reply)
        self.assertIn("2 घंटे", reply)

        dossier = engine.export_dossier()
        self.assertEqual(dossier.ticket_id, "CC-84291")
        self.assertEqual(dossier.customer_type, "support_query")
        self.assertEqual(dossier.query_type, "customer_complaint")
        self.assertTrue(dossier.query_resolved)
        self.assertTrue(dossier.whatsapp_dispatched)
        self.assertEqual(dossier.bant_timeline_confirmed, "2 घंटे में सीनियर मैनेजर रिज़ॉल्यूशन एसएलए")

    def test_reflex_sync_and_cognitive_paced_latency_tiers(self):
        """Verifies reflex sync (<90ms) and cognitive paced (200-450ms) classification."""
        engine = ConversationEngine(market_mode="usa")

        # Reflex sync 1: "can you hear me?"
        engine.process_user_turn("Can you hear me?")
        self.assertEqual(engine.dossier.response_latency_tier, "reflex_sync")
        self.assertEqual(engine.dossier.disfluency_type, "acknowledgment")

        # Reflex sync 2: "hello?"
        engine.process_user_turn("Hello?")
        self.assertEqual(engine.dossier.response_latency_tier, "reflex_sync")

        # Cognitive paced: Friction / schedule negotiation
        engine.process_user_turn("Today is not good, I will come tomorrow")
        self.assertEqual(engine.dossier.response_latency_tier, "cognitive_paced")
        self.assertEqual(engine.dossier.disfluency_type, "cognitive_hesitation")


if __name__ == "__main__":
    unittest.main()
