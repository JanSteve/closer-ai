#!/usr/bin/env python3
"""
Interactive Customer Testing Console for CLOSER AI.
Allows the founder or team to test CLOSER AI as a live customer.
Records every turn, extracts lead intelligence, and saves new learnings to SQLite.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.schemas import InboundLead
from src.closer.memory.learning_db import get_learning_db


def run_interactive_customer_test(
    sector: str = "real_estate",
    market_mode: str = "tamil",
    business_name: str = "Green Valley Residences (Porur)",
    customer_name: str = "Jan Steve Daniel",
    customer_phone: str = "+91-98400-55555"
):
    print("=" * 70)
    print("🎙️ CLOSER AI — INTERACTIVE CUSTOMER TEST CONSOLE")
    print(f"📍 Business: {business_name}")
    print(f"🌐 Sector: {sector.upper()} | Language Mode: {market_mode.upper()}")
    print(f"👤 Customer: {customer_name} ({customer_phone})")
    print("💡 Instructions: Type your questions or objections as a real customer.")
    print("   Type 'exit', 'quit', or 'bye' to hang up the call and see what AI learned.")
    print("=" * 70)

    lead = InboundLead(
        lead_id="test_sim_user",
        full_name=customer_name,
        phone_number=customer_phone,
        ad_campaign="OMR & Porur Hoarding Campaign"
    )

    conv = ConversationEngine(
        lead=lead,
        market_mode=market_mode,
        sector=sector,
        business_name=business_name
    )

    # 1. AI Initial Greeting
    greeting = conv.get_initial_greeting()
    print(f"\n🤖 CLOSER AI: {greeting}\n")

    # 2. Interactive Loop
    while True:
        try:
            user_input = input("🗣️ You (Customer): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[Call Ended]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "bye", "hangup", "முடிந்தது"):
            print("\n[Hanging up phone call...]")
            break

        # Process Turn
        ai_reply = conv.process_user_turn(user_input)
        print(f"\n🤖 CLOSER AI: {ai_reply}\n")

        # Live Dossier Peek
        dossier = conv.dossier
        print(f"   📊 [Live Status] Intent: {dossier.intent_score}/100 | "
              f"Budget: {dossier.budget_inr_text or 'Under discussion'} | "
              f"Slot: {dossier.appointment_datetime or 'Pending'}")
        print("-" * 70)

    # 3. Call Wrap-Up & Self-Learning Extraction
    print("\n" + "=" * 70)
    print("💾 PERSISTING CALL RECORDING & EXTRACTING AUTONOMOUS LEARNING...")
    summary = conv.save_and_learn_from_call()

    print(f"✅ Call ID: {summary.get('call_id')}")
    print(f"✅ Turn Count: {summary.get('turn_count')} turns recorded into SQLite")
    print(f"✅ New Domain Inquiries Learned: {summary.get('new_learnings_count')}")

    learnings = summary.get("learnings", [])
    if learnings:
        print("\n🧠 AUTONOMOUS KNOWLEDGE ACQUIRED FROM THIS CALL:")
        for idx, l in enumerate(learnings, 1):
            status = l.get("status")
            topic = l.get("topic")
            query = l.get("customer_query")
            freq = l.get("frequency")
            print(f"   [{idx}] {topic} ({status}) | Frequency: {freq}x")
            print(f"       Customer Question: \"{query}\"")
            if "learned_response" in l:
                print(f"       AI Learned Answer: \"{l.get('learned_response')}\"")
    else:
        print("ℹ️ Standard conversational queries handled (no new unmapped topics detected).")

    db = get_learning_db()
    stats = db.get_stats()
    print("\n📚 OVERALL KNOWLEDGE BASE STATS:")
    print(f"   Total Calls In DB: {stats['total_calls_recorded']}")
    print(f"   Total Learned Topics: {stats['total_learned_topics']}")
    print(f"   Total Queries Processed: {stats['total_queries_handled']}")
    print(f"   Database File: {stats['db_path']}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_interactive_customer_test()
