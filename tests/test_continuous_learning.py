"""
Unit & Integration Tests for Continuous Learning Memory & Call Recording DB in CLOSER AI.
Verifies that every customer call is persisted in SQLite, analyzed for new domain inquiries,
and dynamically used to answer future customer calls.
"""

import pytest
from pathlib import Path
from src.closer.memory.learning_db import LearningMemoryDB
from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.schemas import InboundLead


@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "test_learning.db"
    return LearningMemoryDB(db_file)


def test_learning_db_initialization_and_seed(temp_db: LearningMemoryDB):
    stats = temp_db.get_stats()
    assert stats["total_calls_recorded"] == 0
    assert stats["total_learned_topics"] >= 6
    assert stats["total_queries_handled"] >= 6


def test_record_call_and_autonomous_learning(temp_db: LearningMemoryDB):
    call_id = "test_call_001"
    transcript = [
        {"role": "assistant", "content": "Vanakkam Sir, Green Valley project-la irundhu pesurom."},
        {"role": "user", "content": "Hello, unga project-ku nearest metro station evvalavu thooram irukku?"},
        {"role": "assistant", "content": "Sir, upcoming metro station 1.2 km thooram thaan."},
        {"role": "user", "content": "Super, car parking and EV charging irukka?"},
        {"role": "assistant", "content": "Aama Sir, covered car parking and EV charging spot irukku."},
        {"role": "user", "content": "Seri, Saturday 11 AM site visit varren."}
    ]
    dossier = {
        "full_name": "Karthik Subramanian",
        "phone_number": "+91-9840012345",
        "intent_score": 90,
        "qualified": True,
        "appointment_datetime": "Saturday 11:00 AM"
    }

    result = temp_db.record_call(
        call_id=call_id,
        customer_name="Karthik Subramanian",
        customer_phone="+91-9840012345",
        market_mode="tamil",
        sector="real_estate",
        business_name="Green Valley Residences",
        transcript=transcript,
        dossier=dossier
    )

    assert result["status"] == "saved"
    assert result["turn_count"] == 6
    assert result["new_learnings_count"] >= 2

    # Verify call is in database
    recent = temp_db.get_recent_calls(1)
    assert len(recent) == 1
    assert recent[0]["customer_name"] == "Karthik Subramanian"
    assert recent[0]["intent_score"] == 90
    assert recent[0]["appointment_slot"] == "Saturday 11:00 AM"

    # Verify newly learned knowledge can be queried by future calls
    metro_ans = temp_db.find_learned_response("metro station enga irukku?", sector="real_estate")
    assert metro_ans is not None
    assert "metro" in metro_ans.lower()

    parking_ans = temp_db.find_learned_response("covered car parking kidaikkuma?", sector="real_estate")
    assert parking_ans is not None
    assert "parking" in parking_ans.lower()


def test_conversation_engine_continuous_learning_integration(tmp_path: Path):
    db_file = tmp_path / "conv_learning.db"
    custom_db = LearningMemoryDB(db_file)

    lead = InboundLead(
        lead_id="test_lead_chennai",
        full_name="Venkatesh Iyer",
        phone_number="+91-9884011223",
        ad_campaign="Porur Luxury Towers"
    )

    conv = ConversationEngine(lead=lead, market_mode="tamil", sector="real_estate", business_name="Porur Luxury Towers")
    conv.learning_db = custom_db  # Inject test DB

    # Turn 1: Greeting
    greeting = conv.get_initial_greeting()
    assert "வணக்கம்" in greeting

    # Turn 2: Customer asks about CMDA approval (learned seed knowledge)
    reply_approval = conv.process_user_turn("Indha project CMDA and RERA approval irukka?")
    assert "CMDA" in reply_approval or "TNRERA" in reply_approval

    # Turn 3: Customer asks about UDS percentage (learned seed knowledge)
    reply_uds = conv.process_user_turn("UDS percentage evvalavu thareenga?")
    assert "UDS" in reply_uds

    # Turn 4: Customer confirms slot
    reply_slot = conv.process_user_turn("Ok, Saturday 11 AM vandhu paakuren")
    assert "கன்ஃபார்ம்" in reply_slot or "Saturday" in reply_slot

    # Save and learn from the completed call
    learn_summary = conv.save_and_learn_from_call()
    assert learn_summary["status"] == "saved"

    # Verify DB stats updated
    stats = custom_db.get_stats()
    assert stats["total_calls_recorded"] == 1
