"""
Unit tests for CLOSER AI Amura Health Clinical Intake Qualification & Pydantic Schema Extraction.
Verifies clinical entity extraction, concern handling, intent scoring, and dossier serialization.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.closer.memory.learning_db as ldb
from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.schemas import BuyerDossier, InboundLead, PatientDossier

_API_KEYS = (
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "SARVAM_API_KEY",
    "APILAYER_API_KEY",
)


class TestAgentQualification(unittest.TestCase):
    """Test suite for clinical patient intake extraction and qualification logic."""

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._env_patch = patch.dict(os.environ, {k: "" for k in _API_KEYS})
        self._env_patch.start()
        ldb._GLOBAL_LEARNING_DB = None
        self._db_patch = patch(
            "src.closer.agent.conversation.get_learning_db",
            side_effect=lambda *a, **kw: ldb.LearningMemoryDB(Path(self._tmp_dir.name) / "qual.db"),
        )
        self._db_patch.start()

    def tearDown(self):
        self._db_patch.stop()
        self._env_patch.stop()
        ldb._GLOBAL_LEARNING_DB = None
        self._tmp_dir.cleanup()

    def test_high_urgency_metabolic_patient_persona(self):
        """Verifies metabolic patient sharing HbA1c/diabetes + immediate timeline is scored qualified (>= 80)."""
        lead = InboundLead(
            lead_id="test_patient_metabolic",
            full_name="Priya Raman",
            phone_number="+91-98400-11223",
            market_region="INDIA",
            primary_concern="Type-2 Diabetes & Fasting Insulin",
        )
        engine = ConversationEngine(lead=lead, market_mode="english", business_name="Amura Health")

        engine.process_user_turn(
            "I have Type-2 diabetes and my HbA1c is 8.4 with elevated fasting insulin. I want online care in Velachery Chennai."
        )
        engine.process_user_turn("I want to start physician-led care immediately within the next 30 days.")

        dossier = engine.export_dossier()
        self.assertEqual(dossier.full_name, "Priya Raman")
        self.assertEqual(dossier.patient_name, "Priya Raman")
        self.assertEqual(dossier.condition_category, "metabolic_diabetes")
        self.assertIn("HbA1c", dossier.biomarkers_mentioned)
        self.assertIn("Fasting Insulin", dossier.biomarkers_mentioned)
        self.assertEqual(dossier.timeframe, "immediate (0-30 days)")
        self.assertIn("Chennai", dossier.target_locations)
        self.assertTrue(dossier.qualified)
        self.assertGreaterEqual(dossier.intent_score, 80)
        self.assertTrue(bool(dossier.follow_up_note))

    def test_hesitant_patient_with_concern_persona(self):
        """Verifies hesitation handling, empathetic guidance, and subsequent qualification."""
        lead = InboundLead(
            lead_id="test_patient_hesitant",
            full_name="Meera Krishnan",
            phone_number="+91-98400-44556",
            market_region="INDIA",
        )
        engine = ConversationEngine(lead=lead, market_mode="english", business_name="Amura Health")

        reply_1 = engine.process_user_turn("Hi, I am just looking into what Amura Health offers right now.")
        self.assertIn("amura health", reply_1.lower())
        self.assertIn("just_browsing", engine.dossier.objections_raised)
        self.assertGreater(len(engine.dossier.objections_handled), 0)

        engine.process_user_turn("I have PCOS and thyroid issues with TSH 6.2 and want to begin within 1 to 3 months.")
        dossier = engine.export_dossier()
        self.assertEqual(dossier.condition_category, "pcod_hormonal")
        self.assertIn("TSH", dossier.biomarkers_mentioned)
        self.assertEqual(dossier.timeframe, "1-3 months")
        self.assertTrue(dossier.qualified)

    def test_low_intent_general_inquiry_persona(self):
        """Verifies casual non-urgent browsing without clinical urgency stays qualified=False."""
        lead = InboundLead(
            lead_id="test_patient_low",
            full_name="Sam Casual",
            phone_number="+91-98400-01010",
            market_region="INDIA",
        )
        engine = ConversationEngine(lead=lead, market_mode="english", business_name="Amura Health")

        engine.process_user_turn("I am not in a rush, just browsing for a year or two from now.")
        dossier = engine.export_dossier()
        self.assertEqual(dossier.timeframe, "browsing (6+ months)")
        self.assertFalse(dossier.qualified)
        self.assertLess(dossier.intent_score, 50)

    def test_pydantic_clinical_schema_serialization(self):
        """Verifies PatientDossier / BuyerDossier model_dump excludes real-estate keys and includes clinical fields."""
        dossier = PatientDossier(
            patient_name="Elena Nair",
            full_name="Elena Nair",
            phone_number="+91-98400-99112",
            chief_concern="Fatty Liver & Insulin Resistance",
            condition_category="fatty_liver",
            triage_urgency="Priority",
            care_pathway="Amura MNT + NMT Reversal",
            detected_emotion="anxious",
            safety_flag="safe",
            consent_status="granted",
            qualified=True,
            intent_score=90,
        )
        self.assertIs(BuyerDossier, PatientDossier)
        data = dossier.model_dump()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["patient_name"], "Elena Nair")
        self.assertEqual(data["detected_emotion"], "anxious")
        self.assertEqual(data["safety_flag"], "safe")
        self.assertEqual(data["consent_status"], "granted")
        self.assertTrue(bool(data["follow_up_note"]))
        for forbidden in ("tax_exchange_1031", "bhk_preference", "property_type", "lender_name"):
            self.assertNotIn(forbidden, data)

        json_str = dossier.model_dump_json()
        self.assertIn("Elena Nair", json_str)
        self.assertIn("Amura MNT + NMT Reversal", json_str)


if __name__ == "__main__":
    unittest.main()
