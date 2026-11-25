"""
Tests for CLOSER AI Omni-Domain General Intelligence with Clinical Safety Guardrails.
Verifies general-knowledge questions are answered naturally without forcing clinic pitches
or leaking real-estate copy, while embedding strict clinical safety boundaries.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.closer.memory.learning_db as ldb
from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.prompt import get_omni_gemini_prompt
from src.closer.agent.schemas import PatientDossier
from src.closer.agent.sector_playbooks import process_tamil_turn

_API_KEYS = (
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "SARVAM_API_KEY",
)


class TestOmniGeminiIntelligence(unittest.TestCase):
    """Test suite for dual-mode general knowledge & safe clinical concierge handling."""

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._env_patch = patch.dict(os.environ, {k: "" for k in _API_KEYS})
        self._env_patch.start()
        ldb._GLOBAL_LEARNING_DB = None
        self._db_patch = patch(
            "src.closer.agent.conversation.get_learning_db",
            side_effect=lambda *a, **kw: ldb.LearningMemoryDB(Path(self._tmp_dir.name) / "omni.db"),
        )
        self._db_patch.start()

    def tearDown(self):
        self._db_patch.stop()
        self._env_patch.stop()
        ldb._GLOBAL_LEARNING_DB = None
        self._tmp_dir.cleanup()

    def test_omni_gemini_prompt_generation(self):
        """Verifies clinical concierge system prompts across Hindi, Tamil, and English."""
        prompt_hi = get_omni_gemini_prompt("hindi", "Amura Health", "amura_metabolic")
        prompt_ta = get_omni_gemini_prompt("tamil", "Amura Health", "amura_metabolic")
        prompt_en = get_omni_gemini_prompt("english", "Amura Health", "amura_metabolic")

        for p, persona in ((prompt_hi, "Swati"), (prompt_ta, "Pallavi"), (prompt_en, "Maya")):
            self.assertIn(persona, p)
            self.assertIn("Amura Health", p)
            self.assertIn("NEVER diagnose", p)
            self.assertIn("NEVER prescribe", p)
            self.assertIn("108", p)
            self.assertIn("GENERAL KNOWLEDGE & CASUAL TALK", p)

    def test_hindi_general_knowledge_turn(self):
        """Verifies Hindi engine answers general questions without forcing clinic pitches or real estate."""
        engine = ConversationEngine(business_name="Amura Health")
        engine.set_market_mode("hindi")
        reply = engine.process_user_turn("चाँद पर पहला कदम किसने रखा था?")
        self.assertTrue(len(reply) > 5)
        for forbidden in ("3 बीएचके", "करोड़", "रेरा", "साइट विज़िट"):
            self.assertNotIn(forbidden, reply)

    def test_tamil_general_knowledge_turn(self):
        """Verifies Tamil engine answers general questions cleanly without pushing appointments."""
        dossier = PatientDossier()
        reply = process_tamil_turn(
            "சூரியன்ல இருந்து பூமிக்கு வர வெளிச்சம் எவ்வளவு நேரம் எடுக்கும்?",
            dossier,
            sector="healthcare",
            business_name="Amura Health",
        )
        self.assertTrue(len(reply) > 5)
        for forbidden in ("floor plan", "rera", "bhk", "vip pass"):
            self.assertNotIn(forbidden, reply.lower())

    def test_english_general_knowledge_turn(self):
        """Verifies English engine answers general questions without forcing clinic or real-estate pitch."""
        engine = ConversationEngine(business_name="Amura Health")
        engine.set_market_mode("english")
        reply = engine.process_user_turn("Why is the sky blue?")
        self.assertTrue(len(reply) > 5)
        for forbidden in ("Bel Air", "Beverly Hills", "3 million"):
            self.assertNotIn(forbidden, reply)


if __name__ == "__main__":
    unittest.main()
