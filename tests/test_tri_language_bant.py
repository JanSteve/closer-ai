"""
Unit tests for Tri-Language Clinical Intake, Personas & Pydantic PatientDossier Schema.
Verifies English Amura Health triage, caregiver/self decision-maker authority,
Indian patient support ticket #CC-84291 SLA, Hindi honorifics & consultation booking,
and duplex latency pacing tiers.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.closer.memory.learning_db as ldb
from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.schemas import BuyerDossier, CallSessionState, InboundLead, PatientDossier

_API_KEYS = (
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "SARVAM_API_KEY",
    "APILAYER_API_KEY",
)


class TestTriLanguageAndClinicalSchema(unittest.TestCase):
    """Test suite for tri-language clinical workflows and PatientDossier schema."""

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._env_patch = patch.dict(os.environ, {k: "" for k in _API_KEYS})
        self._env_patch.start()
        ldb._GLOBAL_LEARNING_DB = None
        self._db_patch = patch(
            "src.closer.agent.conversation.get_learning_db",
            side_effect=lambda *a, **kw: ldb.LearningMemoryDB(Path(self._tmp_dir.name) / "trilang.db"),
        )
        self._db_patch.start()

    def tearDown(self):
        self._db_patch.stop()
        self._env_patch.stop()
        ldb._GLOBAL_LEARNING_DB = None
        self._tmp_dir.cleanup()

    def test_clinical_intake_schema_attributes_and_aliases(self):
        """Verifies Pydantic v2 clinical fields, transitional aliases, and clean JSON serialization."""
        dossier = PatientDossier(
            patient_name="Eleanor Vance",
            full_name="Eleanor Vance",
            phone_number="+91-98400-01881",
            chief_concern="Type-2 Diabetes & Elevated Fasting Insulin",
            condition_category="metabolic_diabetes",
            triage_urgency="Priority",
            care_pathway="Amura MNT + NMT Reversal",
            consent_status="granted",
            detected_emotion="anxious",
            safety_flag="safe",
            bant_budget_qualified=True,
            bant_authority_verified="Self / Patient",
            timeframe="immediate (0-30 days)",
            response_latency_tier="cognitive_paced",
            disfluency_type="cognitive_hesitation",
        )

        self.assertIs(BuyerDossier, PatientDossier)
        self.assertEqual(dossier.patient_name, "Eleanor Vance")
        self.assertEqual(dossier.chief_concern, "Type-2 Diabetes & Elevated Fasting Insulin")
        self.assertEqual(dossier.bant_authority_verified, "Self / Patient")
        self.assertEqual(dossier.bant_need, "Type-2 Diabetes & Elevated Fasting Insulin")
        self.assertEqual(dossier.bant_timeline, "immediate (0-30 days)")
        self.assertTrue(dossier.bant_budget)

        dossier.bant_authority = "Family Caregiver"
        self.assertEqual(dossier.bant_authority_verified, "Family Caregiver")
        dossier.bant_need = "PCOD Hormonal Care"
        self.assertEqual(dossier.chief_concern, "PCOD Hormonal Care")

        dump = dossier.model_dump()
        self.assertIn("chief_concern", dump)
        self.assertIn("triage_urgency", dump)
        self.assertIn("care_pathway", dump)
        self.assertIn("consent_status", dump)
        self.assertIn("detected_emotion", dump)
        self.assertIn("safety_flag", dump)
        self.assertIn("response_latency_tier", dump)
        for legacy in ("tax_exchange_1031", "bhk_preference", "property_type"):
            self.assertNotIn(legacy, dump)

        session_state = CallSessionState(
            session_id="sess_test_01",
            lead_id="patient_test_01",
            caller_phone="+91-62-622-62222",
            recipient_phone="+91-98400-01881",
            latency_tier="cognitive_paced",
            target_latency_ms=280,
        )
        self.assertEqual(session_state.latency_tier, "cognitive_paced")
        self.assertEqual(session_state.target_latency_ms, 280)

    def test_english_metabolic_intake_and_biomarkers(self):
        """Verifies English Amura Health intake captures metabolic concern, biomarkers, and care pathway."""
        lead = InboundLead(
            lead_id="patient_metabolic_01",
            full_name="Arjun Nair",
            phone_number="+91-98400-55667",
            market_region="INDIA",
        )
        engine = ConversationEngine(lead=lead, market_mode="english", business_name="Amura Health")

        reply = engine.process_user_turn(
            "I have insulin resistance and high HbA1c and fasting insulin, looking for an online telehealth consult within 30 days."
        )
        self.assertTrue(len(reply) > 10)
        dossier = engine.export_dossier()
        self.assertEqual(dossier.condition_category, "metabolic_diabetes")
        self.assertIn("HbA1c", dossier.biomarkers_mentioned)
        self.assertIn("Fasting Insulin", dossier.biomarkers_mentioned)
        self.assertIn("Online Telehealth", dossier.target_locations)
        self.assertEqual(dossier.care_pathway, "Amura MNT + NMT Reversal")
        self.assertTrue(dossier.qualified)
        self.assertEqual(dossier.response_latency_tier, "cognitive_paced")

    def test_caregiver_and_payment_readiness_variations(self):
        """Verifies authority & payment coverage detection across self, caregiver, and corporate wellness."""
        e1 = ConversationEngine(market_mode="english", business_name="Amura Health")
        e1.process_user_turn("I am calling for myself and ready to pay via UPI.")
        self.assertEqual(e1.dossier.bant_authority_verified, "Self / Patient")
        self.assertEqual(e1.dossier.financing_type, "self_pay")
        self.assertTrue(e1.dossier.pre_approved)

        e2 = ConversationEngine(market_mode="english", business_name="Amura Health")
        e2.process_user_turn("I am booking for my mother using health insurance coverage.")
        self.assertEqual(e2.dossier.bant_authority_verified, "Family Caregiver")
        self.assertEqual(e2.dossier.financing_type, "insurance")

        e3 = ConversationEngine(market_mode="english", business_name="Amura Health")
        e3.process_user_turn("This is through our corporate wellness employer program.")
        self.assertEqual(e3.dossier.bant_authority_verified, "Corporate Wellness / Employer")

    def test_india_customer_care_cc84291_sla(self):
        """Verifies patient portal support issue resolution, ticket #CC-84291, and 2-hour SLA."""
        lead = InboundLead(
            lead_id="patient_ind_sla",
            full_name="Rajesh Khanna",
            phone_number="+91-98765-88888",
            market_region="INDIA",
        )
        engine = ConversationEngine(lead=lead, market_mode="india", business_name="Amura Health")

        reply = engine.process_user_turn(
            "I have a problem with my lab report upload on the portal, please log a ticket and escalate."
        )
        self.assertIn("apologize for the inconvenience", reply.lower())
        self.assertIn("CC-84291", reply)
        self.assertIn("two hours", reply.lower())
        self.assertIn("whatsapp", reply.lower())

        dossier = engine.export_dossier()
        self.assertEqual(dossier.ticket_id, "CC-84291")
        self.assertEqual(dossier.customer_type, "support_query")
        self.assertEqual(dossier.query_type, "patient_support")
        self.assertTrue(dossier.query_resolved)
        self.assertTrue(dossier.whatsapp_dispatched)
        self.assertEqual(dossier.response_latency_tier, "cognitive_paced")

    def test_india_metabolic_protocol_and_weekend_consult(self):
        """Verifies Indian English MNT/NMT protocol explanation and Saturday 11:00 AM IST consultation."""
        lead = InboundLead(
            lead_id="patient_ind_consult",
            full_name="Deepak Subramanian",
            phone_number="+91-98765-99999",
            market_region="INDIA",
        )
        engine = ConversationEngine(lead=lead, market_mode="india", business_name="Amura Health")

        r1 = engine.process_user_turn("Can you explain the MNT and NMT metabolic reversal program at Velachery?")
        self.assertIn("medical nutrition therapy", r1.lower())
        self.assertIn("natural molecule therapy", r1.lower())
        self.assertIn("Velachery", engine.dossier.target_locations)

        r2 = engine.process_user_turn("Can we confirm a consultation for Saturday 11 AM at Velachery clinic?")
        self.assertIn("confirmed", r2.lower())
        self.assertIn("Saturday 11:00 AM IST", r2)
        self.assertIn("whatsapp", r2.lower())

        dossier = engine.export_dossier()
        self.assertEqual(dossier.consult_slot, "Saturday 11:00 AM IST")
        self.assertEqual(dossier.appointment_type, "clinic_consultation")
        self.assertTrue(dossier.whatsapp_dispatched)
        self.assertTrue(engine.is_completed)

    def test_hindi_vernacular_honorifics_and_consultation_booking(self):
        """Verifies native Hindi honorifics, Amura metabolic explanation, and Saturday 11 AM IST booking."""
        lead = InboundLead(
            lead_id="patient_hi_01",
            full_name="सुनील वर्मा",
            phone_number="+91-98765-11111",
            market_region="INDIA_HINDI",
        )
        engine = ConversationEngine(lead=lead, market_mode="hindi", business_name="Amura Health")

        greeting = engine.get_initial_greeting()
        self.assertIn("नमस्ते जी", greeting)
        self.assertIn("स्वाति", greeting)
        self.assertIn("Amura Health", greeting)

        r1 = engine.process_user_turn("नमस्ते जी, मुझे डायबिटीज और मेटाबोलिक प्रोग्राम के बारे में बताइए।")
        self.assertIn("जी बिल्कुल", r1)
        self.assertIn("Amura Health", r1)
        self.assertEqual(engine.dossier.condition_category, "metabolic_diabetes")

        r2 = engine.process_user_turn("हाँ जी, इस शनिवार सुबह 11 बजे का डॉक्टर कंसल्टेशन बुक कर दीजिए।")
        self.assertIn("शनिवार सुबह 11:00 बजे", r2)
        self.assertIn("वॉट्सऐप", r2)

        dossier = engine.export_dossier()
        self.assertEqual(dossier.consult_slot, "शनिवार सुबह 11:00 बजे IST")
        self.assertEqual(dossier.appointment_type, "tele_consultation")
        self.assertTrue(dossier.whatsapp_dispatched)
        self.assertTrue(engine.is_completed)

    def test_hindi_patient_complaint_and_sla_ticket(self):
        """Verifies native Hindi support complaint handling and #CC-84291 ticket assignment."""
        lead = InboundLead(
            lead_id="patient_hi_complaint",
            full_name="कविता शर्मा",
            phone_number="+91-98765-22222",
            market_region="INDIA_HINDI",
        )
        engine = ConversationEngine(lead=lead, market_mode="hindi", business_name="Amura Health")

        reply = engine.process_user_turn("मेरी रिपोर्ट अपलोड करने में समस्या आ रही है, मुझे शिकायत दर्ज करवानी है।")
        self.assertIn("असुविधा के लिए मैं दिल से माफ़ी चाहती हूँ", reply)
        self.assertIn("#CC-84291", reply)
        self.assertIn("2 घंटे", reply)

        dossier = engine.export_dossier()
        self.assertEqual(dossier.ticket_id, "CC-84291")
        self.assertEqual(dossier.customer_type, "support_query")
        self.assertTrue(dossier.query_resolved)

    def test_reflex_sync_and_cognitive_paced_latency_tiers(self):
        """Verifies reflex sync (<90ms) and cognitive paced (200-450ms) classification."""
        engine = ConversationEngine(market_mode="english", business_name="Amura Health")

        engine.process_user_turn("Can you hear me?")
        self.assertEqual(engine.dossier.response_latency_tier, "reflex_sync")
        self.assertEqual(engine.dossier.disfluency_type, "acknowledgment")

        engine.process_user_turn("Vanakkam?")
        self.assertEqual(engine.dossier.response_latency_tier, "reflex_sync")

        engine.process_user_turn("Today is not good, I will come tomorrow")
        self.assertEqual(engine.dossier.response_latency_tier, "cognitive_paced")
        self.assertEqual(engine.dossier.disfluency_type, "cognitive_hesitation")


if __name__ == "__main__":
    unittest.main()
