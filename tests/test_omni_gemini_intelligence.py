"""
Tests for CLOSER AI Omni-Domain General Intelligence (Gemini-grade reasoning).
Verifies that CLOSER AI can answer ANY question (science, history, cooking, casual talk)
without forcing business/sales pitches, while still answering business inquiries accurately.
"""

import unittest
from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.prompt import get_omni_gemini_prompt
from src.closer.agent.sector_playbooks import process_tamil_turn, process_non_realestate_sector_turn
from src.closer.agent.schemas import BuyerDossier


class TestOmniGeminiIntelligence(unittest.TestCase):
    """Test suite for Gemini-grade boundless knowledge and dual-mode conversational handling."""

    def test_omni_gemini_prompt_generation(self):
        """Verifies system prompts generate properly for all supported languages."""
        prompt_hi = get_omni_gemini_prompt("hindi", "CLOSER AI")
        prompt_ta = get_omni_gemini_prompt("tamil", "CLOSER AI")
        prompt_en = get_omni_gemini_prompt("english", "CLOSER AI")

        self.assertIn("Ritu", prompt_hi)
        self.assertIn("Gemini-grade", prompt_hi)
        self.assertIn("DO NOT force a sales pitch", prompt_hi)

        self.assertIn("Priya", prompt_ta)
        self.assertIn("Gemini-grade", prompt_ta)
        self.assertIn("DO NOT force a sales pitch", prompt_ta)

        self.assertIn("Sophia", prompt_en)
        self.assertIn("Gemini-grade", prompt_en)
        self.assertIn("DO NOT force a sales pitch", prompt_en)

    def test_hindi_general_knowledge_turn(self):
        """Verifies Hindi engine answers general questions directly without sales pitching."""
        engine = ConversationEngine()
        engine.set_market_mode("hindi")
        reply = engine.process_user_turn("चाँद पर पहला कदम किसने रखा था?")
        self.assertTrue(len(reply) > 5)
        # Should not force real estate brochure or booking
        self.assertNotIn("3 बीएचके", reply)
        self.assertNotIn("करोड़", reply)

    def test_tamil_general_knowledge_turn(self):
        """Verifies Tamil engine answers general questions without spamming real estate."""
        dossier = BuyerDossier()
        reply = process_tamil_turn(
            "சூரியன்ல இருந்து பூமிக்கு வர வெளிச்சம் எவ்வளவு நேரம் எடுக்கும்?",
            dossier,
            sector="real_estate",
            business_name="CLOSER AI",
        )
        self.assertTrue(len(reply) > 5)
        # Should answer question
        self.assertNotIn("floor plan", reply.lower())

    def test_english_general_knowledge_turn(self):
        """Verifies English engine answers general questions without forcing Bel Air $3M-$10M qualification."""
        engine = ConversationEngine()
        engine.set_market_mode("usa")
        reply = engine.process_user_turn("Why is the sky blue?")
        self.assertTrue(len(reply) > 5)
        self.assertNotIn("Bel Air", reply)
        self.assertNotIn("Beverly Hills", reply)


if __name__ == "__main__":
    unittest.main()
