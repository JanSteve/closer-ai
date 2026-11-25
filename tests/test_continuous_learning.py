"""
Unit & Integration Tests for Continuous Clinical Learning Memory & Call Recording DB.
Verifies SQLite persistence (temp file & :memory:), autonomous clinical FAQ extraction,
and ConversationEngine Tamil/Tanglish Amura Health integration without touching repo data/.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

import src.closer.memory.learning_db as ldb
from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.schemas import InboundLead
from src.closer.memory.learning_db import LearningMemoryDB


@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "test_learning.db"
    return LearningMemoryDB(db_file)


def test_learning_db_initialization_and_seed(temp_db: LearningMemoryDB):
    stats = temp_db.get_stats()
    assert stats["total_calls_recorded"] == 0
    assert stats["total_learned_topics"] >= 6
    assert stats["total_queries_handled"] >= 6

    topics = {item["topic"] for item in temp_db.get_all_learned_knowledge()}
    assert "metabolic_reversal_approach" in topics
    assert "velachery_clinic_location" in topics
    assert "emergency_108_protocol" in topics


def test_in_memory_db_persistence():
    """Verifies persistent single-connection ':memory:' works across queries without creating files."""
    mem_db = LearningMemoryDB(":memory:")
    try:
        stats = mem_db.get_stats()
        assert stats["total_learned_topics"] >= 6
        ans = mem_db.find_learned_response("Where is the Velachery Chennai clinic?", sector="amura_metabolic")
        assert ans is not None
        assert "Velachery" in ans
    finally:
        mem_db.close()


def test_record_call_and_autonomous_learning(temp_db: LearningMemoryDB):
    call_id = "test_clinical_call_001"
    transcript = [
        {"role": "assistant", "content": "வணக்கம், Amura Health Velachery clinic-ல இருந்து பேசுறோம்."},
        {"role": "user", "content": "Hello, unga clinic-la HbA1c and fasting insulin blood test report review pannuveengala?"},
        {"role": "assistant", "content": "Yes, our doctors review fasting insulin and HbA1c panels carefully."},
        {"role": "user", "content": "Super, MNT and NMT nutrition therapy epdi work aagum?"},
        {"role": "assistant", "content": "MNT and NMT target root-cause insulin resistance with physician supervision."},
        {"role": "user", "content": "Seri, Saturday 11 AM Velachery clinic visit varren."},
    ]
    dossier = {
        "patient_name": "Karthik Subramanian",
        "full_name": "Karthik Subramanian",
        "phone_number": "+91-9840012345",
        "intent_score": 90,
        "qualified": True,
        "appointment_datetime": "Saturday 11:00 AM IST",
    }

    result = temp_db.record_call(
        call_id=call_id,
        customer_name="Karthik Subramanian",
        customer_phone="+91-9840012345",
        market_mode="tamil",
        sector="amura_metabolic",
        business_name="Amura Health",
        transcript=transcript,
        dossier=dossier,
    )

    assert result["status"] == "saved"
    assert result["turn_count"] == 6
    assert result["new_learnings_count"] >= 2

    recent = temp_db.get_recent_calls(1)
    assert len(recent) == 1
    assert recent[0]["customer_name"] == "Karthik Subramanian"
    assert recent[0]["intent_score"] == 90
    assert recent[0]["appointment_slot"] == "Saturday 11:00 AM IST"

    hba1c_ans = temp_db.find_learned_response("hba1c fasting insulin report review", sector="amura_metabolic")
    assert hba1c_ans is not None
    assert "hba1c" in hba1c_ans.lower()

    mnt_ans = temp_db.find_learned_response("MNT and NMT nutrition plan", sector="amura_metabolic")
    assert mnt_ans is not None
    assert "mnt" in mnt_ans.lower()


def test_conversation_engine_continuous_learning_integration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    for key in ("GROQ_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.setenv(key, "")

    db_file = tmp_path / "conv_learning.db"
    custom_db = LearningMemoryDB(db_file)
    monkeypatch.setattr(ldb, "_GLOBAL_LEARNING_DB", custom_db)
    monkeypatch.setattr("src.closer.agent.conversation.get_learning_db", lambda *a, **kw: custom_db)
    monkeypatch.setattr(ldb, "get_learning_db", lambda *a, **kw: custom_db)

    lead = InboundLead(
        lead_id="test_patient_chennai",
        full_name="Venkatesh Iyer",
        phone_number="+91-9884011223",
        market_region="TAMIL",
        ad_campaign="Amura Health Velachery Metabolic Care",
    )

    conv = ConversationEngine(
        lead=lead,
        market_mode="tamil",
        sector="amura_metabolic",
        business_name="Amura Health",
    )

    greeting = conv.get_initial_greeting()
    assert "வணக்கம்" in greeting
    assert "Amura Health" in greeting

    reply_location = conv.process_user_turn("Velachery Chennai clinic address solla mudiyuma?")
    assert "Velachery" in reply_location

    reply_slot = conv.process_user_turn("Ok, Saturday 11 AM consult book pannunga")
    assert "கன்ஃபார்ம்" in reply_slot or "11:00" in reply_slot

    learn_summary = conv.save_and_learn_from_call()
    assert learn_summary["status"] == "saved"

    stats = custom_db.get_stats()
    assert stats["total_calls_recorded"] == 1
