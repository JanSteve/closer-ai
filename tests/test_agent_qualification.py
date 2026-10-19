"""
Unit tests for CLOSER AI Agent Lead Qualification & Pydantic Schema Extraction.
Verifies entity extraction, objection handling, intent scoring, and persona differentiation.
"""

import unittest
from src.closer.agent.schemas import InboundLead, BuyerDossier
from src.closer.agent.conversation import ConversationEngine


class TestAgentQualification(unittest.TestCase):
    """Test suite for Pydantic lead extraction and qualification logic."""

    def test_ultra_luxury_cash_buyer_persona(self):
        """Verifies ultra-luxury all-cash buyer is scored as highly qualified (score >= 80)."""
        lead = InboundLead(
            lead_id="test_lead_ultra",
            full_name="Victoria Sterling",
            phone_number="+1-310-555-0188",
            listing_address="10484 Bellagio Rd, Bel Air, CA",
            listing_price=8500000
        )
        engine = ConversationEngine(lead=lead)
        
        # Turn 1: Buyer states high budget and liquid cash
        engine.process_user_turn("We are looking in Bel Air and Beverly Hills with an $8 million budget. We will be paying all cash.")
        # Turn 2: Buyer states urgent timeline
        engine.process_user_turn("We want to close immediately within the next 30 days.")
        
        dossier = engine.export_dossier()

        self.assertEqual(dossier.full_name, "Victoria Sterling")
        self.assertEqual(dossier.budget_max, 8000000)
        self.assertEqual(dossier.financing_type, "cash")
        self.assertTrue(dossier.pre_approved)
        self.assertEqual(dossier.timeframe, "immediate (0-30 days)")
        self.assertIn("Bel Air", dossier.target_locations)
        self.assertIn("Beverly Hills", dossier.target_locations)
        self.assertTrue(dossier.qualified, "Lead with $8M cash within 30 days must be marked qualified")
        self.assertGreaterEqual(dossier.intent_score, 80)

    def test_hesitant_buyer_with_objection_persona(self):
        """Verifies objection detection, resolution tagging, and consultative qualification."""
        lead = InboundLead(
            lead_id="test_lead_hesitant",
            full_name="Jonathan Mercer",
            phone_number="+1-310-555-0142"
        )
        engine = ConversationEngine(lead=lead)
        
        # Turn 1: Objection 'just browsing'
        reply_1 = engine.process_user_turn("Hi, I was looking at the photo gallery, but I am just browsing online right now.")
        self.assertIn("browsing is the most exciting part", reply_1.lower())
        self.assertIn("just_browsing", engine.dossier.objections_raised)
        self.assertGreater(len(engine.dossier.objections_handled), 0)

        # Turn 2: Discloses budget & financing
        engine.process_user_turn("Well, our price ceiling is around $3.5 million and we are pre-approved with First Republic.")
        engine.process_user_turn("We are looking to purchase within 1 to 3 months.")

        dossier = engine.export_dossier()
        self.assertEqual(dossier.budget_max, 3500000)
        self.assertTrue(dossier.pre_approved)
        self.assertTrue(dossier.qualified)
        self.assertEqual(dossier.timeframe, "1-3 months")

    def test_unqualified_lead_persona(self):
        """Verifies leads with sub-market budgets or no qualification are flagged as qualified=False."""
        lead = InboundLead(
            lead_id="test_lead_low",
            full_name="Sam Casual",
            phone_number="+1-310-555-0101"
        )
        engine = ConversationEngine(lead=lead)

        engine.process_user_turn("My budget is only $250k and I haven't talked to any bank yet.")
        engine.process_user_turn("I might buy in a year or two, just window shopping.")

        dossier = engine.export_dossier()
        self.assertEqual(dossier.budget_max, 250000)
        self.assertFalse(dossier.pre_approved)
        self.assertFalse(dossier.qualified, "Sub-$1M lead in Bel Air must be flagged unqualified")
        self.assertLess(dossier.intent_score, 50)

    def test_pydantic_schema_serialization(self):
        """Verifies Pydantic v2 model_dump, dict, and json methods."""
        dossier = BuyerDossier(
            full_name="Elena Rostova",
            phone_number="+1-415-555-0199",
            budget_max=6500000,
            pre_approved=True,
            qualified=True,
            intent_score=90
        )
        data = dossier.model_dump()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["full_name"], "Elena Rostova")
        self.assertEqual(data["budget_max"], 6500000)

        json_str = dossier.model_dump_json()
        self.assertIsInstance(json_str, str)
        self.assertIn("Elena Rostova", json_str)
        self.assertIn("6500000", json_str)


if __name__ == "__main__":
    unittest.main()
