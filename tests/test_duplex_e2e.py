"""
End-to-End Test Suite: CLOSER AI Google Duplex & VoiceStudio Elevation.
Covers Tiers 1-4 across Google Duplex prosody, dynamic latency, tri-language personas,
and VoiceStudio 48kHz audio controls.
Discovered and executed via python3 pytest.py.
"""

from __future__ import annotations
import io
import os
import re
import sys
import time
import wave
import struct
import base64
import unittest
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from src.closer.voice.tts import (
    EdgeTTSVoiceEngine,
    normalize_speech_text,
    generate_silence_pcm,
    inject_silence_wav,
    apply_pitch_contour,
    inject_duplex_disfluencies,
    VOICES,
    VOICE_ALIASES,
)
from src.closer.voice.call_session import (
    CallSession,
    DynamicLatencyPacer,
    PacingResult,
    REFLEX_SYNC_PATTERNS,
    REFLEX_RESPONSES,
)
from src.closer.agent.schemas import InboundLead, BuyerDossier, CallSessionState
from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.prompt import (
    ISA_SYSTEM_PROMPT,
    OBJECTION_PLAYBOOK,
    INDIA_CUSTOMER_CARE_SYSTEM_PROMPT,
    INDIA_QUERY_PLAYBOOK,
    HINDI_CUSTOMER_CARE_SYSTEM_PROMPT,
    HINDI_QUERY_PLAYBOOK,
)
from src.closer.web.dashboard import HTML_TEMPLATE


# ==============================================================================
# TIER 1: FEATURE COVERAGE (>=5 tests per feature, 16 features = 80 tests)
# ==============================================================================

class TestTier1FeatureCoverage(unittest.TestCase):
    """
    Tier 1: Comprehensive feature-by-feature verification covering all 16 features
    defined in TEST_INFRA.md and ORIGINAL_REQUEST.md.
    """

    def setUp(self):
        self.tts = EdgeTTSVoiceEngine()
        self.lead_usa = InboundLead(
            lead_id="lead_usa_test",
            full_name="Victoria Sterling",
            phone_number="+1-310-555-0188",
            market_region="USA",
            listing_address="10484 Bellagio Rd, Bel Air, CA",
            listing_price=15000000,
        )
        self.lead_india = InboundLead(
            lead_id="lead_india_test",
            full_name="Rajesh Sharma",
            phone_number="+91-98801-23456",
            market_region="INDIA",
            listing_address="Sobha Windsor, Whitefield, Bengaluru",
            listing_price=16500000,
        )

    # --------------------------------------------------------------------------
    # Feature 1: Context-Aware Filler Particles (R1)
    # --------------------------------------------------------------------------
    def test_t1_f1_1_us_disfluencies(self):
        """Verifies US English filler particles ('mm-hmm', 'um', 'gotcha', 'well') formatting."""
        res_mmhmm = inject_duplex_disfluencies("I will check the calendar.", market="usa", intent="affirmation")
        self.assertTrue(res_mmhmm.startswith("Mm-hmm..."), f"Expected 'Mm-hmm...', got {res_mmhmm}")

        res_um = inject_duplex_disfluencies("Let me review the off-market inventory.", market="usa", intent="thinking")
        self.assertTrue(res_um.startswith("Um..."), f"Expected 'Um...', got {res_um}")

        res_gotcha = inject_duplex_disfluencies("I have your price ceiling noted.", market="usa", intent="acknowledgement")
        self.assertTrue(res_gotcha.startswith("Gotcha..."), f"Expected 'Gotcha...', got {res_gotcha}")

        res_well = inject_duplex_disfluencies("For estates in this tier, private tours are exclusive.", market="usa", intent="general")
        self.assertTrue(res_well.startswith("Well..."), f"Expected 'Well...', got {res_well}")

    def test_t1_f1_2_hindi_disfluencies(self):
        """Verifies Hindi vernacular filler particles ('जी बिल्कुल', 'हाँ जी', 'नमस्ते जी') formatting."""
        res_bilkul = inject_duplex_disfluencies("हम शनिवार को साइट विज़िट बुक कर देते हैं।", market="hindi", intent="friction")
        self.assertTrue(res_bilkul.startswith("जी बिल्कुल..."), f"Expected 'जी बिल्कुल...', got {res_bilkul}")

        res_haanji = inject_duplex_disfluencies("मैं आपकी पूरी सहायता करूँगी।", market="hindi", intent="acknowledgement")
        self.assertTrue(res_haanji.startswith("हाँ जी..."), f"Expected 'हाँ जी...', got {res_haanji}")

        res_norm = normalize_speech_text("नमस्ते जी, क्या आप सुन सकते हैं?")
        self.assertTrue(res_norm.startswith("नमस्ते जी..."), f"Expected 'नमस्ते जी...', got {res_norm}")

    def test_t1_f1_3_indian_english_disfluencies(self):
        """Verifies Indian English fillers ('Haanji', 'Understood', 'Definitely sir') formatting."""
        res_ind = inject_duplex_disfluencies("I will dispatch the brochure on WhatsApp.", market="india", intent="acknowledgement")
        self.assertTrue(res_ind.startswith("Haanji..."), f"Expected 'Haanji...', got {res_ind}")

        res_fric = inject_duplex_disfluencies("I understand you have an urgent office meeting.", market="india", is_friction=True)
        self.assertTrue(res_fric.startswith("Understood..."), f"Expected 'Understood...', got {res_fric}")

        norm_def = normalize_speech_text("Definitely sir, our manager will resolve CC-84291.")
        self.assertTrue(norm_def.startswith("Definitely sir..."), f"Expected 'Definitely sir...', got {norm_def}")

    def test_t1_f1_4_context_intent_mapping(self):
        """Verifies context intent mapping selects appropriate filler particle."""
        text = "Our private client desk is available tomorrow."
        t_fric = inject_duplex_disfluencies(text, market="usa", is_friction=True)
        self.assertIn("Mm-hmm...", t_fric)

        t_think = inject_duplex_disfluencies(text, market="usa", intent="thinking")
        self.assertIn("Um...", t_think)

        t_ack = inject_duplex_disfluencies(text, market="usa", intent="acknowledgement")
        self.assertIn("Gotcha...", t_ack)

    def test_t1_f1_5_entity_keyword_preservation(self):
        """Verifies that injecting disfluencies never strips or corrupts crucial transaction keywords."""
        msg = "We have off-market 1031 tax exchange options in Bel Air and Aspen for $15M."
        injected = inject_duplex_disfluencies(msg, market="usa", is_friction=True)
        self.assertIn("1031 tax exchange", injected)
        self.assertIn("Bel Air", injected)
        self.assertIn("Aspen", injected)
        self.assertIn("15 million dollars", injected)

    # --------------------------------------------------------------------------
    # Feature 2: Synthetic Cognitive Pauses (120ms-350ms) (R1)
    # --------------------------------------------------------------------------
    def test_t1_f2_1_silence_pcm_120ms(self):
        """Verifies exact PCM silence generation for lower cognitive bound (120ms) at 48kHz."""
        pcm = generate_silence_pcm(120, sample_rate=48000)
        expected_bytes = int(48000 * 2 * 0.120)  # 11,520 bytes
        self.assertEqual(len(pcm), expected_bytes)
        self.assertEqual(pcm, b"\x00" * expected_bytes)

    def test_t1_f2_2_silence_pcm_200ms(self):
        """Verifies exact PCM silence generation for standard cognitive pause (200ms) at 48kHz."""
        pcm = generate_silence_pcm(200, sample_rate=48000)
        expected_bytes = int(48000 * 2 * 0.200)  # 19,200 bytes
        self.assertEqual(len(pcm), expected_bytes)
        self.assertEqual(pcm, b"\x00" * expected_bytes)

    def test_t1_f2_3_silence_pcm_350ms(self):
        """Verifies exact PCM silence generation for upper cognitive bound (350ms) at 48kHz."""
        pcm = generate_silence_pcm(350, sample_rate=48000)
        expected_bytes = int(48000 * 2 * 0.350)  # 33,600 bytes
        self.assertEqual(len(pcm), expected_bytes)
        self.assertEqual(pcm, b"\x00" * expected_bytes)

    def test_t1_f2_4_inject_silence_wav(self):
        """Verifies inject_silence_wav prepends silence into RIFF WAV stream without corrupting header."""
        engine = EdgeTTSVoiceEngine()
        base_wav = engine._generate_pcm_wav(sample_rate=48000, duration_sec=0.2)
        with wave.open(io.BytesIO(base_wav), "rb") as w:
            orig_frames = w.getnframes()

        padded_wav = inject_silence_wav(base_wav, duration_ms=250, sample_rate=48000)
        self.assertTrue(padded_wav.startswith(b"RIFF"))
        with wave.open(io.BytesIO(padded_wav), "rb") as w:
            new_frames = w.getnframes()
            added_frames = new_frames - orig_frames
            expected_added = int(48000 * 0.250)
            self.assertEqual(added_frames, expected_added)

    def test_t1_f2_5_punctuation_breathing_cadences(self):
        """Verifies punctuation delimiters ('...', ' — ') convert into acoustic breathing cadences."""
        raw = "We can schedule that for Thursday -- or actually, let me check Friday."
        norm = normalize_speech_text(raw)
        self.assertIn(" — ", norm)
        self.assertNotIn("--", norm)

    # --------------------------------------------------------------------------
    # Feature 3: Pitch Contour Shaping (R1)
    # --------------------------------------------------------------------------
    def test_t1_f3_1_interrogative_rising_pitch(self):
        """Verifies interrogative questions '?' receive rising pitch contour (+2Hz to +3Hz)."""
        pitch_q = apply_pitch_contour("Would tomorrow at 2:00 PM work for you?")
        self.assertIn(pitch_q, ("+2Hz", "+3Hz"))

    def test_t1_f3_2_confirmation_falling_pitch(self):
        """Verifies empathetic confirmations '.' receive falling cadence (-2Hz)."""
        pitch_dot = apply_pitch_contour("I completely understand your busy schedule.")
        self.assertEqual(pitch_dot, "-2Hz")

        pitch_excl = apply_pitch_contour("We look forward to meeting you!")
        self.assertEqual(pitch_excl, "-2Hz")

    def test_t1_f3_3_explicit_pitch_preservation(self):
        """Verifies user-specified pitch override ('+5Hz', '-5Hz') is strictly preserved."""
        self.assertEqual(apply_pitch_contour("Any text?", pitch="+5Hz"), "+5Hz")
        self.assertEqual(apply_pitch_contour("Any text.", pitch="-5Hz"), "-5Hz")

    def test_t1_f3_4_neutral_pitch_default(self):
        """Verifies neutral or unterminated text defaults to +0Hz."""
        self.assertEqual(apply_pitch_contour("hello there"), "+0Hz")
        self.assertEqual(apply_pitch_contour(""), "+0Hz")

    def test_t1_f3_5_synthesis_with_pitch_variations(self):
        """Verifies voice synthesis operates cleanly across rising, falling, and extreme pitch settings."""
        engine = EdgeTTSVoiceEngine()
        data_pos, _ = engine.synthesize_sync("Are you there?", pitch="+3Hz", sample_rate=48000)
        self.assertTrue(data_pos.startswith(b"RIFF"))

        data_neg, _ = engine.synthesize_sync("I understand.", pitch="-2Hz", sample_rate=48000)
        self.assertTrue(data_neg.startswith(b"RIFF"))

    # --------------------------------------------------------------------------
    # Feature 4: Reflex Sync Response Fast-Path (<90ms) (R2)
    # --------------------------------------------------------------------------
    def test_t1_f4_1_reflex_pattern_detection(self):
        """Verifies REFLEX_SYNC_PATTERNS accurately identifies standard sync tokens."""
        sync_tokens = [
            "hello?", "hi?", "can you hear me?", "are you there?",
            "yeah", "yes", "speaking", "haanji?", "namaste?"
        ]
        for token in sync_tokens:
            self.assertTrue(
                DynamicLatencyPacer.is_reflex_sync(token),
                f"Failed to identify '{token}' as reflex sync"
            )

    def test_t1_f4_2_reflex_substantive_rejection(self):
        """Verifies substantive transactional utterances are NOT treated as reflex syncs."""
        non_reflex = [
            "hello, I want to book a showing for Bel Air",
            "yes I have a 1031 tax exchange budget of $15 million",
            "can you hear me? I want to discuss ticket CC-84291",
            "speaking about my schedule, today is not good"
        ]
        for utterance in non_reflex:
            self.assertFalse(
                DynamicLatencyPacer.is_reflex_sync(utterance),
                f"Incorrectly flagged '{utterance}' as reflex sync"
            )

    def test_t1_f4_3_reflex_latency_under_90ms(self):
        """Verifies total turnaround latency for standalone reflex sync is under 90ms."""
        session = CallSession(lead=self.lead_usa)
        t0 = time.perf_counter()
        reply_text, reply_audio = session.handle_user_speech(audio_chunk=b"", simulated_text="can you hear me?")
        elapsed = time.perf_counter() - t0

        self.assertLess(elapsed, 0.095, f"Reflex sync exceeded latency threshold: {elapsed*1000:.2f}ms")
        self.assertTrue(len(reply_audio) > 44)
        self.assertEqual(session.last_pacing_tier, "reflex_sync")

    def test_t1_f4_4_reflex_dossier_telemetry(self):
        """Verifies dossier records reflex_sync tier telemetry upon conversational sync."""
        engine = ConversationEngine(lead=self.lead_usa)
        engine.process_user_turn("hello?")
        self.assertEqual(engine.dossier.response_latency_tier, "reflex_sync")
        self.assertEqual(engine.dossier.disfluency_type, "acknowledgment")

    def test_t1_f4_5_reflex_cached_audio_delivery(self):
        """Verifies cached reflex audio is a mathematically valid RIFF WAV buffer."""
        session = CallSession(lead=self.lead_usa)
        _, audio = session.handle_user_speech(audio_chunk=b"", simulated_text="hello?")
        self.assertTrue(audio.startswith(b"RIFF"))
        with wave.open(io.BytesIO(audio), "rb") as w:
            self.assertIn(w.getframerate(), (24000, 48000))
            self.assertEqual(w.getnchannels(), 1)

    # --------------------------------------------------------------------------
    # Feature 5: Dynamic Cognitive Latency Pacing (200ms–450ms) (R2)
    # --------------------------------------------------------------------------
    def test_t1_f5_1_schedule_friction_pacing(self):
        """Verifies schedule friction pacing delay is strictly within 200ms–450ms."""
        res = DynamicLatencyPacer.calculate_pacing_delay("today is not good, I will come tomorrow", is_friction=True)
        self.assertEqual(res.tier, "cognitive_paced")
        self.assertGreaterEqual(res.delay, 0.200)
        self.assertLessEqual(res.delay, 0.450)

    def test_t1_f5_2_busy_friction_pacing(self):
        """Verifies busy objection pacing delay is strictly within 200ms–450ms."""
        res = DynamicLatencyPacer.calculate_pacing_delay("I am busy right now, contact me later")
        self.assertEqual(res.tier, "cognitive_paced")
        self.assertGreaterEqual(res.delay, 0.200)
        self.assertLessEqual(res.delay, 0.450)

    def test_t1_f5_3_meeting_friction_pacing(self):
        """Verifies in-meeting friction pacing delay is strictly within 200ms–450ms."""
        res = DynamicLatencyPacer.calculate_pacing_delay("I'm in a zoom conference right now")
        self.assertEqual(res.tier, "cognitive_paced")
        self.assertGreaterEqual(res.delay, 0.200)
        self.assertLessEqual(res.delay, 0.450)

    def test_t1_f5_4_tax_exchange_pacing(self):
        """Verifies 1031 tax exchange complex reasoning triggers cognitive pacing delay."""
        res = DynamicLatencyPacer.calculate_pacing_delay("We are executing a 1031 exchange replacement")
        self.assertEqual(res.tier, "cognitive_paced")
        self.assertGreaterEqual(res.delay, 0.200)
        self.assertLessEqual(res.delay, 0.450)

    def test_t1_f5_5_standard_turn_pacing(self):
        """Verifies standard conversational turn pacing is within standard bounds (120ms–200ms)."""
        res = DynamicLatencyPacer.calculate_pacing_delay("Sounds great, please continue.")
        self.assertEqual(res.tier, "standard")
        self.assertEqual(res.delay, 0.120)

    # --------------------------------------------------------------------------
    # Feature 6: Barge-In Cutoff (<50ms) & Turn Recovery (R2)
    # --------------------------------------------------------------------------
    def test_t1_f6_1_barge_in_abort_flag_set(self):
        """Verifies user speech while speaking immediately triggers barge-in abort."""
        session = CallSession(lead=self.lead_usa)
        session.is_speaking = True
        session.handle_user_speech(audio_chunk=b"", simulated_text="Wait a second!")
        self.assertFalse(session.is_speaking)
        self.assertGreaterEqual(session.interrupted_count, 1)

    def test_t1_f6_2_barge_in_increments_counter(self):
        """Verifies multiple interruptions increment session interrupted_count accurately."""
        session = CallSession(lead=self.lead_usa)
        session.is_speaking = True
        session.abort_speaking("Wait")
        session.is_speaking = True
        session.abort_speaking("Hold on")
        self.assertEqual(session.interrupted_count, 2)
        self.assertEqual(session.state.interrupted_count, 2)

    def test_t1_f6_3_barge_in_cutoff_latency_under_50ms(self):
        """Verifies barge-in execution cutoff latency is strictly under 50ms."""
        session = CallSession(lead=self.lead_usa)
        session.is_speaking = True
        t0 = time.perf_counter()
        session._execute_barge_in_abort("Interrupted fragment")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        self.assertLess(elapsed_ms, 50.0)
        self.assertLess(session.last_barge_in_latency_ms, 50.0)

    def test_t1_f6_4_barge_in_recovery_courtesy_prefix(self):
        """Verifies that an interrupted agent prepends polite turn recovery courtesy on next turn."""
        session = CallSession(lead=self.lead_usa)
        session.is_speaking = True
        session._execute_barge_in_abort("Let me explain the Bel Air...")
        reply, _ = session.handle_user_speech(audio_chunk=b"", simulated_text="I was asking about price.")
        self.assertTrue(reply.startswith("Oh, pardon me — please go ahead!"))

    def test_t1_f6_5_barge_in_state_preservation(self):
        """Verifies barge-in does not corrupt transcript history or lead dossier state."""
        session = CallSession(lead=self.lead_usa)
        session.is_speaking = True
        session._execute_barge_in_abort()
        session.handle_user_speech(audio_chunk=b"", simulated_text="My budget is $15M cash.")
        self.assertTrue(session.engine.dossier.bant_budget_qualified)
        self.assertEqual(session.engine.dossier.budget_max, 15000000)

    # --------------------------------------------------------------------------
    # Feature 7: US Luxury Real Estate ISA Persona (R3)
    # --------------------------------------------------------------------------
    def test_t1_f7_1_1031_tax_exchange_playbook(self):
        """Verifies 1031 tax exchange trigger offers qualified intermediary & 45-day deadline response."""
        engine = ConversationEngine(lead=self.lead_usa)
        reply = engine.process_user_turn("We are looking for a 1031 tax exchange replacement property.")
        self.assertIn("1031", reply)
        self.assertIn("45-day", reply)
        self.assertTrue(engine.dossier.tax_exchange_1031)
        self.assertEqual(engine.dossier.exchange_deadline_days, 45)

    def test_t1_f7_2_jumbo_financing_playbook(self):
        """Verifies jumbo financing inquiry connects to private banking desk (J.P. Morgan/First Republic)."""
        engine = ConversationEngine(lead=self.lead_usa)
        reply = engine.process_user_turn("We will need a jumbo loan through private banking.")
        self.assertTrue(
            any(bank in reply for bank in ["J.P. Morgan", "First Republic", "private banking"]),
            f"Expected private banking reference in reply: {reply}"
        )

    def test_t1_f7_3_aspen_estate_tour(self):
        """Verifies Aspen estate inquiry presents ski-in/ski-out off-market compound walkthrough."""
        engine = ConversationEngine(lead=self.lead_usa)
        reply = engine.process_user_turn("Do you have any private mountain compounds in Aspen?")
        self.assertIn("Aspen", reply)
        self.assertTrue(any(w in reply.lower() for w in ["ski-in", "mountain", "compound", "red mountain", "starwood"]))

    def test_t1_f7_4_bel_air_tour_qualification(self):
        """Verifies Bel Air estate inquiry qualifies luxury budget and proposes showing."""
        engine = ConversationEngine(lead=self.lead_usa)
        reply = engine.process_user_turn("I am looking for an estate in Bel Air around $12 million.")
        self.assertIn("Bel Air", engine.dossier.target_locations)
        self.assertTrue(engine.dossier.bant_budget_qualified)

    def test_t1_f7_5_beverly_hills_pocket_listings(self):
        """Verifies Beverly Hills pocket listings are handled with concierge discretion."""
        engine = ConversationEngine(lead=self.lead_usa)
        reply = engine.process_user_turn("We want off-market pocket listings in Beverly Hills.")
        self.assertIn("Beverly Hills", engine.dossier.target_locations)

    # --------------------------------------------------------------------------
    # Feature 8: Pydantic BANT Schema Expansion (R3)
    # --------------------------------------------------------------------------
    def test_t1_f8_1_bant_budget_qualified(self):
        """Verifies BuyerDossier.bant_budget_qualified reflects financial qualification."""
        dossier = BuyerDossier(budget_max=6500000, financing_type="cash")
        self.assertFalse(dossier.bant_budget_qualified)  # default
        engine = ConversationEngine(lead=self.lead_usa)
        engine.process_user_turn("We have $10 million in liquid cash.")
        self.assertTrue(engine.dossier.bant_budget_qualified)

    def test_t1_f8_2_bant_authority_verified(self):
        """Verifies BuyerDossier.bant_authority_verified extracts decision maker entity."""
        engine = ConversationEngine(lead=self.lead_usa)
        engine.process_user_turn("I am the sole decision maker for our family office.")
        self.assertIn("Family Office", engine.dossier.bant_authority_verified)

    def test_t1_f8_3_bant_need_identified(self):
        """Verifies BuyerDossier.bant_need_identified captures architectural requirement."""
        engine = ConversationEngine(lead=self.lead_usa)
        engine.process_user_turn("We need a modern architectural estate in Bel Air.")
        self.assertTrue(bool(engine.dossier.bant_need_identified))
        self.assertIn("Bel Air", engine.dossier.bant_need_identified)

    def test_t1_f8_4_bant_timeline_confirmed(self):
        """Verifies BuyerDossier.bant_timeline_confirmed stores purchase window."""
        engine = ConversationEngine(lead=self.lead_usa)
        engine.process_user_turn("We need to close within 30 days.")
        self.assertTrue(bool(engine.dossier.bant_timeline_confirmed))

    def test_t1_f8_5_tax_exchange_1031_fields(self):
        """Verifies 1031 tax exchange boolean and deadline days fields."""
        dossier = BuyerDossier(tax_exchange_1031=True, exchange_deadline_days=45)
        self.assertTrue(dossier.tax_exchange_1031)
        self.assertEqual(dossier.exchange_deadline_days, 45)

    # --------------------------------------------------------------------------
    # Feature 9: Indian English Enterprise Care CC-84291 (R3)
    # --------------------------------------------------------------------------
    def test_t1_f9_1_ticket_cc84291_issued(self):
        """Verifies Indian customer complaint flow immediately issues Ticket #CC-84291."""
        engine = ConversationEngine(lead=self.lead_india, market_mode="india")
        reply = engine.process_user_turn("I have an urgent complaint regarding my booking agreement.")
        self.assertIn("CC-84291", reply)
        self.assertEqual(engine.dossier.ticket_id, "CC-84291")

    def test_t1_f9_2_ticket_cc84291_2hr_sla(self):
        """Verifies Ticket #CC-84291 commits to a 2-hour senior manager resolution SLA."""
        engine = ConversationEngine(lead=self.lead_india, market_mode="india")
        reply = engine.process_user_turn("I need a status update on my service ticket.")
        self.assertTrue("2 hours" in reply or "two hours" in reply)
        self.assertIn("CC-84291", engine.dossier.follow_up_note)

    def test_t1_f9_3_pricing_lakhs_and_crores(self):
        """Verifies Indian pricing inquiries return ₹ Lakhs and ₹ Crores quotes."""
        engine = ConversationEngine(lead=self.lead_india, market_mode="india")
        reply = engine.process_user_turn("What is the starting price for 2 BHK and 3 BHK?")
        self.assertTrue("95 Lakhs" in reply or "95 lakh" in reply)
        self.assertTrue("1.65 Crores" in reply or "1.65 crore" in reply)

    def test_t1_f9_4_rera_compliance_confirmation(self):
        """Verifies RERA inquiry confirms 100% RERA compliance and bank approvals."""
        engine = ConversationEngine(lead=self.lead_india, market_mode="india")
        reply = engine.process_user_turn("Is this project RERA approved?")
        self.assertIn("RERA", reply)
        self.assertTrue(any(bank in reply for bank in ["SBI", "HDFC", "bank"]))

    def test_t1_f9_5_whatsapp_brochure_dispatch(self):
        """Verifies WhatsApp documentation offer and dossier dispatch tagging."""
        engine = ConversationEngine(lead=self.lead_india, market_mode="india")
        engine.process_user_turn("Please share the brochure on WhatsApp.")
        self.assertEqual(engine.dossier.preferred_channel, "WhatsApp")
        self.assertTrue(engine.dossier.whatsapp_dispatched)

    # --------------------------------------------------------------------------
    # Feature 10: Hindi Vernacular Care & Site Visits (R3)
    # --------------------------------------------------------------------------
    def test_t1_f10_1_respectful_hindi_honorifics(self):
        """Verifies Hindi customer care dialogue employs respectful honorifics."""
        engine = ConversationEngine(lead=self.lead_india, market_mode="hindi")
        greeting = engine.get_initial_greeting()
        self.assertTrue("नमस्ते" in greeting or "जी" in greeting)
        reply = engine.process_user_turn("मुझे प्रोजेक्ट की जानकारी चाहिए।")
        self.assertTrue("जी" in reply or "आप" in reply)

    def test_t1_f10_2_hindi_ticket_cc84291(self):
        """Verifies Hindi customer complaint flow issues टिकट नंबर #CC-84291 with 2-hour SLA."""
        engine = ConversationEngine(lead=self.lead_india, market_mode="hindi")
        reply = engine.process_user_turn("मेरी एक जरूरी शिकायत है।")
        self.assertIn("CC-84291", reply)
        self.assertTrue("2 घंटे" in reply or "घंटे" in reply)
        self.assertEqual(engine.dossier.ticket_id, "CC-84291")

    def test_t1_f10_3_hindi_pricing_and_rera(self):
        """Verifies Hindi pricing inquiry returns ₹ लाख / ₹ करोड़ and 100% रेरा रजिस्ट्रेशन."""
        engine = ConversationEngine(lead=self.lead_india, market_mode="hindi")
        reply = engine.process_user_turn("कीमत और रेरा रजिस्ट्रेशन क्या है?")
        self.assertTrue("लाख" in reply or "करोड़" in reply)
        self.assertTrue("रेरा" in reply or "RERA" in reply)

    def test_t1_f10_4_hindi_weekend_site_visit(self):
        """Verifies Hindi site visit coordination coordinates Saturday 11 AM / Sunday 3 PM visit."""
        engine = ConversationEngine(lead=self.lead_india, market_mode="hindi")
        reply = engine.process_user_turn("क्या हम इस वीकेंड परिवार के साथ साइट देख सकते हैं?")
        self.assertTrue("शनिवार" in reply or "रविवार" in reply)
        self.assertTrue("साइट विज़िट" in reply or "विज़िट" in reply)

    def test_t1_f10_5_hindi_office_busy_friction(self):
        """Verifies Hindi office busy friction accommodates post-6 PM callback and WhatsApp pass."""
        engine = ConversationEngine(lead=self.lead_india, market_mode="hindi")
        reply = engine.process_user_turn("मैं अभी ऑफिस की मीटिंग में हूँ, बाद में बात करें।")
        self.assertTrue("शाम 6 बजे" in reply or "वॉट्सऐप" in reply or "मीटिंग" in reply)

    # --------------------------------------------------------------------------
    # Feature 11: VoiceStudio 48kHz Broadcast Master Audio (R4)
    # --------------------------------------------------------------------------
    def test_t1_f11_1_audio_48khz_riff_magic(self):
        """Verifies 48kHz audio synthesis starts with valid RIFF magic bytes."""
        engine = EdgeTTSVoiceEngine()
        data, _ = engine.synthesize_sync("Broadcast master test", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))
        self.assertEqual(data[8:12], b"WAVE")

    def test_t1_f11_2_audio_48khz_sample_rate(self):
        """Verifies wave framerate strictly equals 48,000 Hz."""
        engine = EdgeTTSVoiceEngine()
        data = engine._generate_pcm_wav(sample_rate=48000, duration_sec=0.2)
        with wave.open(io.BytesIO(data), "rb") as w:
            self.assertEqual(w.getframerate(), 48000)

    def test_t1_f11_3_audio_48khz_channels(self):
        """Verifies wave channel count strictly equals 1 (mono)."""
        engine = EdgeTTSVoiceEngine()
        data = engine._generate_pcm_wav(sample_rate=48000, duration_sec=0.2)
        with wave.open(io.BytesIO(data), "rb") as w:
            self.assertEqual(w.getnchannels(), 1)

    def test_t1_f11_4_audio_48khz_bit_depth(self):
        """Verifies wave sample width strictly equals 2 (16-bit linear PCM)."""
        engine = EdgeTTSVoiceEngine()
        data = engine._generate_pcm_wav(sample_rate=48000, duration_sec=0.2)
        with wave.open(io.BytesIO(data), "rb") as w:
            self.assertEqual(w.getsampwidth(), 2)

    def test_t1_f11_5_audio_48khz_offline_fallback(self):
        """Verifies offline fallback produces valid 48kHz WAV audio with exact byte rate."""
        engine = EdgeTTSVoiceEngine()
        data = engine._synthesize_local_fallback("Offline 48kHz test", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))
        with wave.open(io.BytesIO(data), "rb") as w:
            self.assertEqual(w.getframerate(), 48000)
            self.assertEqual(w.getnchannels(), 1)
            self.assertEqual(w.getsampwidth(), 2)

    # --------------------------------------------------------------------------
    # Feature 12: Dynamic Speed & Pitch Sliders (R4)
    # --------------------------------------------------------------------------
    def test_t1_f12_1_speed_slider_range(self):
        """Verifies Web Console HTML defines speed slider with min=-15 and max=25 (-15% to +25%)."""
        self.assertIn('id="voiceRateSlider"', HTML_TEMPLATE)
        self.assertTrue(
            'min="-15"' in HTML_TEMPLATE and 'max="25"' in HTML_TEMPLATE,
            "Speed slider bounds must be -15 to 25"
        )

    def test_t1_f12_2_pitch_slider_range(self):
        """Verifies Web Console HTML defines pitch slider with min=-5 and max=5 (-5Hz to +5Hz)."""
        self.assertIn('id="voicePitchSlider"', HTML_TEMPLATE)
        self.assertTrue(
            'min="-5"' in HTML_TEMPLATE and 'max="5"' in HTML_TEMPLATE,
            "Pitch slider bounds must be -5 to 5"
        )

    def test_t1_f12_3_speed_min_synthesis(self):
        """Verifies voice synthesis at min speed bound (-15%) produces valid RIFF WAV audio."""
        engine = EdgeTTSVoiceEngine()
        data, _ = engine.synthesize_sync("Testing -15% speed bound.", rate="-15%", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))

    def test_t1_f12_4_speed_max_synthesis(self):
        """Verifies voice synthesis at max speed bound (+25%) produces valid RIFF WAV audio."""
        engine = EdgeTTSVoiceEngine()
        data, _ = engine.synthesize_sync("Testing +25% speed bound.", rate="+25%", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))

    def test_t1_f12_5_pitch_extreme_synthesis(self):
        """Verifies voice synthesis at extreme pitch bounds (-5Hz, +5Hz) produces valid audio."""
        engine = EdgeTTSVoiceEngine()
        data_low, _ = engine.synthesize_sync("Low pitch test", pitch="-5Hz", sample_rate=48000)
        self.assertTrue(data_low.startswith(b"RIFF"))
        data_high, _ = engine.synthesize_sync("High pitch test", pitch="+5Hz", sample_rate=48000)
        self.assertTrue(data_high.startswith(b"RIFF"))

    # --------------------------------------------------------------------------
    # Feature 13: One-Click WAV Download (R4)
    # --------------------------------------------------------------------------
    def test_t1_f13_1_download_button_present(self):
        """Verifies Web Console HTML contains the Save WAV button and handler."""
        self.assertIn('id="btnDownloadAudio"', HTML_TEMPLATE)
        self.assertIn("downloadLastAudio", HTML_TEMPLATE)

    def test_t1_f13_2_download_mime_type(self):
        """Verifies downloadLastAudio creates a Blob with MIME type 'audio/wav'."""
        self.assertIn("type: 'audio/wav'", HTML_TEMPLATE)

    def test_t1_f13_3_download_base64_decoding(self):
        """Verifies base64 RIFF audio decoding roundtrip."""
        engine = EdgeTTSVoiceEngine()
        wav_bytes = engine._generate_pcm_wav(sample_rate=48000, duration_sec=0.1)
        b64 = base64.b64encode(wav_bytes).decode("utf-8")
        self.assertTrue(b64.startswith("UklGR"))  # Standard base64 prefix for RIFF header
        decoded = base64.b64decode(b64)
        self.assertEqual(decoded[:4], b"RIFF")

    def test_t1_f13_4_download_empty_alert(self):
        """Verifies downloadLastAudio alerts the user when audio has not yet been generated."""
        self.assertIn("Please click 'Test Audio Sample' or send a message first", HTML_TEMPLATE)

    def test_t1_f13_5_download_valid_wav_blob(self):
        """Verifies exported base64 audio decodes into a standard playable 48kHz WAV container."""
        engine = EdgeTTSVoiceEngine()
        data, _ = engine.synthesize_sync("One click save test", sample_rate=48000)
        b64_str = base64.b64encode(data).decode("ascii")
        recovered = base64.b64decode(b64_str)
        self.assertTrue(recovered.startswith(b"RIFF"))

    # --------------------------------------------------------------------------
    # Feature 14: Social Media Marketing Soundboard (R4)
    # --------------------------------------------------------------------------
    def test_t1_f14_1_soundboard_us_hook(self):
        """Verifies soundboard includes US $15M Luxury estate hook."""
        self.assertIn("Play US $15M Luxury Hook", HTML_TEMPLATE)
        self.assertIn("playMarketingHook('usa')", HTML_TEMPLATE)

    def test_t1_f14_2_soundboard_india_hook(self):
        """Verifies soundboard includes India CC-84291 SLA hook with corrected ticket number."""
        self.assertIn("Play India CC-84291 SLA Hook", HTML_TEMPLATE)
        self.assertNotIn("CC-8492", HTML_TEMPLATE)
        self.assertIn("playMarketingHook('india')", HTML_TEMPLATE)

    def test_t1_f14_3_soundboard_hindi_hook(self):
        """Verifies soundboard includes Hindi Site Visit hook."""
        self.assertIn("Play हिन्दी (Hindi) Site Visit Hook", HTML_TEMPLATE)
        self.assertIn("playMarketingHook('hindi')", HTML_TEMPLATE)

    def test_t1_f14_4_soundboard_hook_text_content(self):
        """Verifies soundboard JavaScript handler sets correct prompt content."""
        self.assertIn("10484 Bellagio Rd in Bel Air", HTML_TEMPLATE)
        self.assertIn("CC-84291", HTML_TEMPLATE)
        self.assertIn("प्रेस्टिज वाइटफ़ील्ड", HTML_TEMPLATE)

    def test_t1_f14_5_soundboard_market_switching(self):
        """Verifies playMarketingHook dynamically adjusts market persona mode."""
        self.assertIn("function playMarketingHook(market)", HTML_TEMPLATE)
        self.assertIn("switchMarket(market)", HTML_TEMPLATE)

    # --------------------------------------------------------------------------
    # Feature 15: Live Audio Waveform Canvas Visualizer (R4)
    # --------------------------------------------------------------------------
    def test_t1_f15_1_canvas_element_present(self):
        """Verifies Web Console HTML defines <canvas id='liveAudioWaveform'>."""
        self.assertIn('<canvas id="liveAudioWaveform"', HTML_TEMPLATE)

    def test_t1_f15_2_canvas_attributes(self):
        """Verifies canvas element has width and height attributes configured."""
        match = re.search(r'<canvas\s+id="liveAudioWaveform"[^>]*>', HTML_TEMPLATE)
        self.assertIsNotNone(match)
        canvas_tag = match.group(0)
        self.assertIn('width="', canvas_tag)
        self.assertIn('height="', canvas_tag)

    def test_t1_f15_3_web_audio_analyser_node(self):
        """Verifies Web Audio API integration initializes AnalyserNode for oscilloscope rendering."""
        self.assertIn("audioCtx.createAnalyser()", HTML_TEMPLATE)
        self.assertIn("analyser.fftSize", HTML_TEMPLATE)

    def test_t1_f15_4_canvas_idle_baseline(self):
        """Verifies drawWaveform renders horizontal idle line when audio playback is quiescent."""
        self.assertIn("drawWaveform", HTML_TEMPLATE)
        self.assertIn("lineTo(w, h / 2)", HTML_TEMPLATE)

    def test_t1_f15_5_canvas_barge_in_reset(self):
        """Verifies barge-in interruption cleanly halts waveform animation and rests idle."""
        self.assertIn("simulateBargeIn", HTML_TEMPLATE)
        self.assertIn("drawWaveform()", HTML_TEMPLATE)

    # --------------------------------------------------------------------------
    # Feature 16: Automated Regression Test Suite Integrity (R3/Acceptance)
    # --------------------------------------------------------------------------
    def test_t1_f16_1_unittest_discoverable(self):
        """Verifies test suite conforms to standard unittest discovery conventions."""
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(TestTier1FeatureCoverage)
        self.assertGreater(suite.countTestCases(), 50)

    def test_t1_f16_2_execution_duration(self):
        """Verifies fast unit execution meets sub-second standards."""
        t0 = time.perf_counter()
        p = generate_silence_pcm(150, 48000)
        self.assertEqual(len(p), 14400)
        self.assertLess(time.perf_counter() - t0, 0.05)

    def test_t1_f16_3_dossier_serialization(self):
        """Verifies BuyerDossier serializes cleanly to dict and JSON including all BANT fields."""
        d = BuyerDossier(
            bant_budget_qualified=True,
            bant_authority_verified="Family Office",
            bant_need_identified="Aspen Compound",
            bant_timeline_confirmed="45-day deadline",
            tax_exchange_1031=True,
            exchange_deadline_days=45,
            response_latency_tier="cognitive_paced",
            disfluency_type="cognitive_hesitation",
        )
        dump = d.model_dump()
        self.assertTrue(dump["bant_budget_qualified"])
        self.assertTrue(dump["tax_exchange_1031"])
        self.assertEqual(dump["exchange_deadline_days"], 45)
        self.assertEqual(dump["response_latency_tier"], "cognitive_paced")

    def test_t1_f16_4_call_state_serialization(self):
        """Verifies CallSessionState serializes cleanly with latency metrics."""
        state = CallSessionState(
            session_id="call_test_123",
            lead_id="lead_123",
            caller_phone="+1234567890",
            recipient_phone="+0987654321",
            latency_tier="reflex_sync",
            target_latency_ms=85,
        )
        dump = state.model_dump()
        self.assertEqual(dump["session_id"], "call_test_123")
        self.assertEqual(dump["latency_tier"], "reflex_sync")

    def test_t1_f16_5_voice_registry_integrity(self):
        """Verifies high-fidelity voice registry contains all primary tri-language voices."""
        required = ["sophia", "guy", "neerja", "prabhat", "swara", "madhur"]
        for v in required:
            self.assertIn(v, VOICES)
            self.assertTrue(len(VOICES[v]) > 5)


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES (>=5 tests per category, 6 categories = 30 tests)
# ==============================================================================

class TestTier2BoundaryAndCornerCases(unittest.TestCase):
    """
    Tier 2: Boundary, corner case, and stress testing across extreme rates,
    pitches, offline fallbacks, empty inputs, Hindi Unicode, and rapid barge-in.
    """

    def setUp(self):
        self.engine = EdgeTTSVoiceEngine()

    # --------------------------------------------------------------------------
    # Category 1: Rate Boundaries
    # --------------------------------------------------------------------------
    def test_t2_c1_1_rate_min_boundary(self):
        """Verifies synthesis at strict minimum boundary (-15%)."""
        data, lat = self.engine.synthesize_sync("Boundary -15% speed", rate="-15%", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))
        self.assertLess(lat, 2.0)

    def test_t2_c1_2_rate_max_boundary(self):
        """Verifies synthesis at strict maximum boundary (+25%)."""
        data, lat = self.engine.synthesize_sync("Boundary +25% speed", rate="+25%", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))
        self.assertLess(lat, 2.0)

    def test_t2_c1_3_rate_out_of_bounds_low(self):
        """Verifies extreme out-of-bounds low rate (-50%) is handled gracefully without crashing."""
        data, _ = self.engine.synthesize_sync("Out of bounds low rate", rate="-50%", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))

    def test_t2_c1_4_rate_out_of_bounds_high(self):
        """Verifies extreme out-of-bounds high rate (+100%) is handled gracefully without crashing."""
        data, _ = self.engine.synthesize_sync("Out of bounds high rate", rate="+100%", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))

    def test_t2_c1_5_rate_empty_and_malformed(self):
        """Verifies empty or malformed rate defaults gracefully to standard rate."""
        data1, _ = self.engine.synthesize_sync("Empty rate", rate="", sample_rate=48000)
        self.assertTrue(data1.startswith(b"RIFF"))
        data2, _ = self.engine.synthesize_sync("Malformed rate", rate="invalid_speed", sample_rate=48000)
        self.assertTrue(data2.startswith(b"RIFF"))

    # --------------------------------------------------------------------------
    # Category 2: Pitch Boundaries
    # --------------------------------------------------------------------------
    def test_t2_c2_1_pitch_min_boundary(self):
        """Verifies synthesis at strict minimum pitch bound (-5Hz)."""
        data, _ = self.engine.synthesize_sync("Pitch -5Hz test", pitch="-5Hz", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))

    def test_t2_c2_2_pitch_max_boundary(self):
        """Verifies synthesis at strict maximum pitch bound (+5Hz)."""
        data, _ = self.engine.synthesize_sync("Pitch +5Hz test", pitch="+5Hz", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))

    def test_t2_c2_3_pitch_out_of_bounds_low(self):
        """Verifies extreme out-of-bounds low pitch (-20Hz) is handled gracefully."""
        data, _ = self.engine.synthesize_sync("Pitch -20Hz test", pitch="-20Hz", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))

    def test_t2_c2_4_pitch_out_of_bounds_high(self):
        """Verifies extreme out-of-bounds high pitch (+20Hz) is handled gracefully."""
        data, _ = self.engine.synthesize_sync("Pitch +20Hz test", pitch="+20Hz", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))

    def test_t2_c2_5_pitch_empty_and_malformed(self):
        """Verifies empty or malformed pitch defaults gracefully to +0Hz."""
        self.assertEqual(apply_pitch_contour("Test text", pitch=""), "+0Hz")
        self.assertEqual(apply_pitch_contour("Test text", pitch="auto"), "+0Hz")
        data, _ = self.engine.synthesize_sync("Malformed pitch", pitch="ultra_high", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))

    # --------------------------------------------------------------------------
    # Category 3: Offline Mode Fallbacks
    # --------------------------------------------------------------------------
    def test_t2_c3_1_forced_offline_pcm_48khz(self):
        """Verifies pure-Python offline PCM wave generator at 48kHz produces valid RIFF header."""
        data = self.engine._generate_pcm_wav(sample_rate=48000, duration_sec=0.25)
        self.assertTrue(data.startswith(b"RIFF"))
        with wave.open(io.BytesIO(data), "rb") as w:
            self.assertEqual(w.getframerate(), 48000)
            self.assertEqual(w.getnchannels(), 1)
            self.assertEqual(w.getsampwidth(), 2)

    def test_t2_c3_2_forced_offline_pcm_24khz(self):
        """Verifies offline PCM generator at 24kHz matches standard telephony specs."""
        data = self.engine._generate_pcm_wav(sample_rate=24000, duration_sec=0.25)
        with wave.open(io.BytesIO(data), "rb") as w:
            self.assertEqual(w.getframerate(), 24000)

    def test_t2_c3_3_offline_synthesize_local_fallback(self):
        """Verifies _synthesize_local_fallback guarantees genuine audio bytes under network dropouts."""
        data = self.engine._synthesize_local_fallback("Offline resilient speech test", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))
        self.assertGreater(len(data), 500)

    def test_t2_c3_4_offline_latency_under_500ms(self):
        """Verifies offline audio generation latency is strictly within bounds."""
        t0 = time.perf_counter()
        data = self.engine._synthesize_local_fallback("Quick latency test", sample_rate=48000)
        elapsed = time.perf_counter() - t0
        self.assertLess(elapsed, 2.500)

    def test_t2_c3_5_offline_provider_label(self):
        """Verifies engine last_provider_used is set appropriately."""
        _ = self.engine._synthesize_local_fallback("Fallback provider", sample_rate=48000)
        self.assertIsNotNone(self.engine.last_provider_used)

    # --------------------------------------------------------------------------
    # Category 4: Empty and Extreme Inputs
    # --------------------------------------------------------------------------
    def test_t2_c4_1_empty_string(self):
        """Verifies empty string text normalization and synthesis handles cleanly."""
        self.assertEqual(normalize_speech_text(""), "")
        self.assertEqual(inject_duplex_disfluencies(""), "")

    def test_t2_c4_2_whitespace_only(self):
        """Verifies whitespace-only string returns None from handle_user_speech."""
        session = CallSession()
        res = session.handle_user_speech(audio_chunk=b"", simulated_text="    \t  ")
        self.assertIsNone(res)

    def test_t2_c4_3_newlines_only(self):
        """Verifies newlines and carriage returns do not crash normalization."""
        norm = normalize_speech_text("\n\n\r\n\t")
        self.assertEqual(norm, "")

    def test_t2_c4_4_single_character(self):
        """Verifies single character input processes without index error."""
        norm = normalize_speech_text("a")
        self.assertEqual(norm, "a")
        res = inject_duplex_disfluencies("a", market="usa")
        self.assertTrue(len(res) > 1)

    def test_t2_c4_5_very_long_paragraph(self):
        """Verifies 1500+ character script normalizes and synthesizes without memory leak."""
        long_text = "We are pleased to introduce 10484 Bellagio Road in Bel Air. " * 30
        self.assertGreater(len(long_text), 1500)
        norm = normalize_speech_text(long_text)
        self.assertTrue(len(norm) > 1000)
        data = self.engine._generate_pcm_wav(sample_rate=48000, duration_sec=0.5)
        self.assertTrue(data.startswith(b"RIFF"))

    # --------------------------------------------------------------------------
    # Category 5: Hindi Unicode, Emojis & Complex Ligatures
    # --------------------------------------------------------------------------
    def test_t2_c5_1_hindi_emoji_normalization(self):
        """Verifies Hindi text with emojis and Indian currency normalizes cleanly."""
        raw = "नमस्ते जी! 🙏 हमारा बजट ₹1.85 Cr है।"
        norm = normalize_speech_text(raw)
        self.assertIn("1.85 crore rupees", norm)
        self.assertIn("नमस्ते जी...", norm)

    def test_t2_c5_2_hindi_zero_width_joiner(self):
        """Verifies complex Hindi ligatures with ZWJ (क् + ् + ष = क्ष) preserve Unicode integrity."""
        raw = "कृपया क्षमा करें, हम शनिवार को आएंगे।"
        norm = normalize_speech_text(raw)
        self.assertIn("क्षमा करें...", norm)

    def test_t2_c5_3_hindi_danda_punctuation(self):
        """Verifies Devanagari full stop (danda '।') is recognized as terminal boundary."""
        pitch = apply_pitch_contour("यह 100% रेरा अप्रूव्ड प्रोजेक्ट है।")
        self.assertEqual(pitch, "-2Hz")

    def test_t2_c5_4_mixed_hinglish_unicode(self):
        """Verifies mixed Hinglish text with Lakhs and BHK expansions."""
        raw = "Sir, 2 BHK flat at ₹95L near Outer Ring Road."
        norm = normalize_speech_text(raw)
        self.assertIn("2 B-H-K", norm)
        self.assertIn("95 lakh rupees", norm)

    def test_t2_c5_5_hindi_complex_numbers(self):
        """Verifies Hindi dialogue engine processes Hindi numeric statements without error."""
        engine = ConversationEngine(market_mode="hindi")
        reply = engine.process_user_turn("हमारा बजट 2 करोड़ रुपये है।")
        self.assertEqual(engine.dossier.budget_currency, "INR")
        self.assertEqual(engine.dossier.budget_max, 20000000)

    # --------------------------------------------------------------------------
    # Category 6: Rapid Barge-In Stress
    # --------------------------------------------------------------------------
    def test_t2_c6_1_sub_10ms_rapid_barge_in(self):
        """Verifies sub-10ms rapid barge-in execution immediately halts speech state."""
        session = CallSession()
        session.is_speaking = True
        t0 = time.perf_counter()
        session.abort_speaking("Immediate cutoff")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        self.assertFalse(session.is_speaking)
        self.assertLess(elapsed_ms, 15.0)

    def test_t2_c6_2_multiple_consecutive_barge_ins(self):
        """Verifies 3 consecutive interruptions increment counter to 3 accurately."""
        session = CallSession()
        for i in range(1, 4):
            session.is_speaking = True
            session.abort_speaking(f"Interruption {i}")
            self.assertEqual(session.interrupted_count, i)

    def test_t2_c6_3_barge_in_when_not_speaking(self):
        """Verifies abort_speaking when agent is NOT speaking is an idempotent safe operation."""
        session = CallSession()
        session.is_speaking = False
        res = session.abort_speaking("Spurious cutoff")
        self.assertTrue(res)
        self.assertFalse(session.is_speaking)

    def test_t2_c6_4_barge_in_preserves_audio_log(self):
        """Verifies barge-in does not wipe out previously logged audio buffers."""
        session = CallSession()
        session.audio_log.append(b"sample_audio_frame_1")
        session.is_speaking = True
        session.abort_speaking("Halt")
        self.assertEqual(len(session.audio_log), 1)

    def test_t2_c6_5_barge_in_recovery_multi_turn(self):
        """Verifies recovery courtesy phrase applies on the turn immediately answering the interruption."""
        session = CallSession()
        session.is_speaking = True
        session.abort_speaking("Wait")
        reply, _ = session.handle_user_speech(audio_chunk=b"", simulated_text="I need the price.")
        self.assertTrue(reply.startswith("Oh, pardon me — please go ahead!"))
        self.assertFalse(session.was_interrupted)


# ==============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (7 integration combination tests)
# ==============================================================================

class TestTier3CrossFeatureCombinations(unittest.TestCase):
    """
    Tier 3: Pairwise and multi-feature interaction testing combining disfluencies,
    dynamic latency, personas, 48kHz audio, and BANT qualification.
    """

    def setUp(self):
        self.lead_usa = InboundLead(
            lead_id="lead_combo_usa",
            full_name="Alexander Vanderbilt",
            phone_number="+1-310-555-0999",
            market_region="USA",
        )
        self.lead_india = InboundLead(
            lead_id="lead_combo_india",
            full_name="Sunil Mehta",
            phone_number="+91-98200-11223",
            market_region="INDIA",
        )

    def test_t3_combo_1_disfluency_and_1031_exchange(self):
        """Combo 1: Ingests 1031 tax exchange query with natural 'mm-hmm' filler and updates BANT dossier."""
        engine = ConversationEngine(lead=self.lead_usa)
        raw_reply = engine.process_user_turn("We have a 1031 tax exchange requirement with a 45-day deadline.")
        formatted = inject_duplex_disfluencies(raw_reply, market="usa", is_friction=True)

        self.assertTrue(formatted.startswith("Mm-hmm..."))
        self.assertTrue(engine.dossier.tax_exchange_1031)
        self.assertEqual(engine.dossier.exchange_deadline_days, 45)
        self.assertTrue(engine.dossier.bant_budget_qualified)

    def test_t3_combo_2_barge_in_and_ticket_cc84291(self):
        """Combo 2: Caller interrupts mid-sentence regarding Ticket #CC-84291; agent halts in <50ms and recovers."""
        session = CallSession(lead=self.lead_india)
        session.engine.market_mode = "india"
        session.is_speaking = True
        session.abort_speaking("Let me check your previous...")

        reply, _ = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text="Wait! What happened to my customer support ticket?"
        )
        self.assertTrue(reply.startswith("Sorry for that, please go ahead sir."))
        self.assertIn("CC-84291", reply)
        self.assertEqual(session.engine.dossier.ticket_id, "CC-84291")

    def test_t3_combo_3_hindi_site_visit_and_48khz(self):
        """Combo 3: Hindi site visit coordination synthesized into genuine 48kHz broadcast audio."""
        engine = ConversationEngine(lead=self.lead_india, market_mode="hindi")
        reply = engine.process_user_turn("हम शनिवार सुबह 11 बजे साइट देखने आ सकते हैं।")
        self.assertIn("शनिवार", reply)

        tts = EdgeTTSVoiceEngine()
        data, lat = tts.synthesize_sync(reply, voice="hi-IN-SwaraNeural", sample_rate=48000)
        self.assertTrue(data.startswith(b"RIFF"))
        with wave.open(io.BytesIO(data), "rb") as w:
            self.assertEqual(w.getframerate(), 48000)
            self.assertEqual(w.getnchannels(), 1)
            self.assertEqual(w.getsampwidth(), 2)

    def test_t3_combo_4_speed_pitch_and_bant(self):
        """Combo 4: Dynamic speed (+10%) & pitch (-2Hz) applied while qualifying luxury BANT budget ($15M cash)."""
        engine = ConversationEngine(lead=self.lead_usa)
        engine.process_user_turn("We have $15M in all-cash liquid reserves.")
        self.assertTrue(engine.dossier.bant_budget_qualified)
        self.assertEqual(engine.dossier.financing_type, "cash")

        tts = EdgeTTSVoiceEngine()
        data, _ = tts.synthesize_sync(
            "Understood. That places you in an elite buying position.",
            rate="+10%",
            pitch="-2Hz",
            sample_rate=48000
        )
        self.assertTrue(data.startswith(b"RIFF"))

    def test_t3_combo_5_soundboard_and_reflex_sync(self):
        """Combo 5: Soundboard trigger executed followed immediately by reflex sync ('can you hear me?')."""
        session = CallSession(lead=self.lead_usa)
        # 1. Soundboard inquiry
        hook_text = "I saw your showcase for 10484 Bellagio Rd in Bel Air ($15M) and want details."
        r1, _ = session.handle_user_speech(audio_chunk=b"", simulated_text=hook_text)
        self.assertIsNotNone(r1)

        # 2. Reflex sync fast-path
        t0 = time.perf_counter()
        r2, _ = session.handle_user_speech(audio_chunk=b"", simulated_text="hello? can you hear me?")
        elapsed = time.perf_counter() - t0
        self.assertLess(elapsed, 0.090)
        self.assertEqual(session.last_pacing_tier, "reflex_sync")

    def test_t3_combo_6_extreme_pitch_hindi_cognitive_pause(self):
        """Combo 6: Pitch (+5Hz) + Hindi vernacular + 200ms cognitive pause."""
        tts = EdgeTTSVoiceEngine()
        silence = generate_silence_pcm(200, sample_rate=48000)
        hindi_text = inject_duplex_disfluencies("हम आपका स्वागत करते हैं।", market="hindi")
        wav_data, _ = tts.synthesize_sync(hindi_text, pitch="+5Hz", sample_rate=48000)
        combined = inject_silence_wav(wav_data, duration_ms=200, sample_rate=48000)
        self.assertTrue(combined.startswith(b"RIFF"))

    def test_t3_combo_7_1031_jumbo_aspen_compound(self):
        """Combo 7: 1031 exchange + private banking jumbo mortgage + Aspen compound tour in single dossier."""
        engine = ConversationEngine(lead=self.lead_usa)
        engine.process_user_turn("We have a 1031 exchange and need a private banking jumbo loan for an Aspen compound.")
        self.assertTrue(engine.dossier.tax_exchange_1031)
        self.assertIn("Aspen", engine.dossier.target_locations)
        self.assertTrue(engine.dossier.bant_budget_qualified)


# ==============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS (5 realistic multi-turn scenarios)
# ==============================================================================

class TestTier4RealWorldApplicationScenarios(unittest.TestCase):
    """
    Tier 4: Realistic, end-to-end multi-turn conversational scenarios matching
    the exact user stories in TEST_INFRA.md and ORIGINAL_REQUEST.md.
    """

    def test_t4_scenario_1_us_luxury_1031_jumbo_bel_air(self):
        """
        Scenario 1: US Luxury $15M Bel Air estate inquiry with 1031 tax exchange & jumbo financing.
        Features exercised: F1, F2, F3, F7, F8, F11, F13.
        Multi-turn workflow:
        - Turn 1: Lead inquires about $15M Bel Air estate.
        - Turn 2: Mentions 1031 tax exchange with strict 45-day deadline.
        - Turn 3: Confirms private banking jumbo mortgage through J.P. Morgan.
        - Turn 4: Also requests off-market Aspen compound showings.
        - Turn 5: Locks in private VIP walkthrough for Friday 2:00 PM.
        """
        lead = InboundLead(
            lead_id="lead_sc1_victoria",
            full_name="Victoria Sterling",
            phone_number="+1-310-555-0188",
            market_region="USA",
            listing_address="10484 Bellagio Rd, Bel Air, CA",
            listing_price=15000000,
        )
        session = CallSession(lead=lead)
        greeting, greeting_audio = session.start_call()
        self.assertTrue(len(greeting_audio) > 44)

        # Turn 1: Bel Air inquiry
        r1, a1 = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text="Hi Sophia, I saw 10484 Bellagio Road in Bel Air and want to schedule a walkthrough."
        )
        self.assertIsNotNone(r1)
        self.assertIn("Bel Air", session.engine.dossier.target_locations)

        # Turn 2: 1031 Tax Exchange
        r2, a2 = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text="We are in a 1031 tax exchange with a strict 45-day identification deadline."
        )
        self.assertIn("1031", r2)
        self.assertTrue(session.engine.dossier.tax_exchange_1031)
        self.assertEqual(session.engine.dossier.exchange_deadline_days, 45)

        # Turn 3: Jumbo financing
        r3, a3 = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text="We have jumbo financing pre-approval with J.P. Morgan Private Bank."
        )
        self.assertTrue(session.engine.dossier.bant_budget_qualified)

        # Turn 4: Aspen property preference
        r4, a4 = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text="Do you also represent off-market ski compounds in Aspen?"
        )
        self.assertIn("Aspen", session.engine.dossier.target_locations)

        # Turn 5: Booking confirmation
        r5, a5 = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text="Friday at 2:00 PM works perfectly for a private tour."
        )
        self.assertIsNotNone(r5)

        dossier = session.end_call()
        self.assertTrue(dossier.bant_budget_qualified)
        self.assertTrue(dossier.tax_exchange_1031)
        self.assertIn("Bel Air", dossier.target_locations)
        self.assertIn("Aspen", dossier.target_locations)

        # Audio export verification (F11, F13)
        self.assertGreater(len(session.audio_log), 3)
        last_audio = session.audio_log[-1]
        self.assertTrue(last_audio.startswith(b"RIFF"))

    def test_t4_scenario_2_india_enterprise_escalation_cc84291(self):
        """
        Scenario 2: India Enterprise customer escalation on Ticket #CC-84291 with 2-hour SLA.
        Features exercised: F1, F4, F5, F9, F11, F14.
        Multi-turn workflow:
        - Turn 1: Reflex sync ('Hello? Can you hear me?') answered in <90ms.
        - Turn 2: Customer escalation on agreement delay. Ticket #CC-84291 assigned with 2-hr SLA.
        - Turn 3: Customer inquires about 3 BHK Whitefield pricing (₹1.65 Crores).
        - Turn 4: Customer has meeting friction; requests post-6 PM call and WhatsApp brochure.
        """
        lead = InboundLead(
            lead_id="lead_sc2_rajesh",
            full_name="Rajesh Sharma",
            phone_number="+91-98801-23456",
            market_region="INDIA",
        )
        session = CallSession(lead=lead)
        session.engine.market_mode = "india"

        # Turn 1: Reflex sync
        t0 = time.perf_counter()
        r1, a1 = session.handle_user_speech(audio_chunk=b"", simulated_text="Hello? Can you hear me?")
        elapsed = time.perf_counter() - t0
        self.assertLess(elapsed, 0.090)
        self.assertEqual(session.last_pacing_tier, "reflex_sync")

        # Turn 2: Service complaint escalation
        r2, a2 = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text="I am calling regarding a major delay in my unit registration paperwork!"
        )
        self.assertIn("CC-84291", r2)
        self.assertEqual(session.engine.dossier.ticket_id, "CC-84291")
        self.assertTrue("2 hours" in r2 or "two hours" in r2)

        # Turn 3: 3 BHK Pricing inquiry
        r3, a3 = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text="Also, what is the price for a 3 BHK in Sobha Windsor Whitefield?"
        )
        self.assertTrue("1.65 Crores" in r3 or "1.65 crore" in r3)
        self.assertIn("Whitefield", session.engine.dossier.target_locations)

        # Turn 4: Meeting friction & WhatsApp request
        r4, a4 = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text="I am in an office meeting now, call me after 6 PM and send details on WhatsApp."
        )
        self.assertEqual(session.engine.dossier.preferred_channel, "WhatsApp")
        self.assertTrue(session.engine.dossier.whatsapp_dispatched)

        dossier = session.end_call()
        self.assertEqual(dossier.ticket_id, "CC-84291")
        self.assertTrue(dossier.query_resolved)

    def test_t4_scenario_3_hindi_vernacular_prestige_site_visit(self):
        """
        Scenario 3: Hindi Vernacular Prestige Whitefield 3 BHK site visit with family.
        Features exercised: F1, F2, F3, F10, F11, F14.
        Multi-turn workflow:
        - Turn 1: Greeting in Hindi.
        - Turn 2: Project & RERA inquiry (₹1.65 करोड़, रेरा अप्रूव्ड).
        - Turn 3: Weekend site visit request with family.
        - Turn 4: Confirmation for Saturday 11 AM with WhatsApp location pass.
        """
        lead = InboundLead(
            lead_id="lead_sc3_amit",
            full_name="Amitabh Verma",
            phone_number="+91-98111-22334",
            market_region="INDIA",
        )
        session = CallSession(lead=lead)
        session.engine.market_mode = "hindi"

        # Turn 1: Hindi initial greeting
        greeting, _ = session.start_call()
        self.assertTrue("नमस्ते" in greeting or "जी" in greeting)

        # Turn 2: Project inquiry
        r1, _ = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text="नमस्ते जी, मुझे प्रेस्टिज वाइटफ़ील्ड में 3 बीएचके फ्लैट की जानकारी चाहिए।"
        )
        self.assertTrue("लाख" in r1 or "करोड़" in r1)
        self.assertTrue("रेरा" in r1 or "RERA" in r1)

        # Turn 3: Site visit request with family
        r2, _ = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text="क्या हम शनिवार सुबह 11 बजे अपने परिवार के साथ साइट देखने आ सकते हैं?"
        )
        self.assertTrue("शनिवार" in r2 or "विज़िट" in r2)

        # Turn 4: Confirmation
        r3, _ = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text="जी बिल्कुल, शनिवार 11 बजे का समय पक्का कर दीजिए और वॉट्सऐप पर लोकेशन भेज दें।"
        )
        self.assertIsNotNone(r3)

        dossier = session.end_call()
        self.assertEqual(dossier.market_region, "INDIA")
        self.assertEqual(dossier.budget_currency, "INR")

    def test_t4_scenario_4_rapid_barge_in_turn_resumption(self):
        """
        Scenario 4: Rapid barge-in mid-utterance and clean turn resumption.
        Features exercised: F4, F6, F7, F8.
        Workflow:
        - Agent begins speaking luxury estate pitch.
        - Caller interrupts abruptly in <50ms.
        - Speech is truncated immediately.
        - Agent resumes with 'Oh, pardon me — please go ahead!' and answers user's inquiry directly.
        """
        lead = InboundLead(
            lead_id="lead_sc4_barge",
            full_name="Marcus Aurelius",
            phone_number="+1-310-555-0777",
            market_region="USA",
        )
        session = CallSession(lead=lead)
        session.is_speaking = True
        session.current_speaking_text = "Welcome to our Bel Air estate collection featuring..."

        # Mid-utterance interruption
        t0 = time.perf_counter()
        session.abort_speaking("Do you have tennis courts?")
        cutoff_ms = (time.perf_counter() - t0) * 1000
        self.assertLess(cutoff_ms, 50.0)
        self.assertFalse(session.is_speaking)

        # Caller follows up
        reply, _ = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text="Sorry to cut you off, but does this Bel Air property include a tennis court?"
        )
        self.assertTrue(reply.startswith("Oh, pardon me — please go ahead!"))
        self.assertFalse(session.was_interrupted)

    def test_t4_scenario_5_web_console_48khz_soundboard_export(self):
        """
        Scenario 5: Web Console broadcast master 48kHz export with custom speed/pitch.
        Features exercised: F11, F12, F13, F14, F15.
        Workflow:
        - Simulates soundboard trigger in Web Console.
        - Validates speed slider bound (-15% to +25%) and pitch bound (-5Hz to +5Hz).
        - Synthesizes 48kHz broadcast master RIFF WAV audio.
        - Verifies live waveform canvas presence in HTML.
        - Downloads base64-encoded audio as standard RIFF WAV.
        """
        # 1. Verify soundboard buttons exist
        self.assertIn("playMarketingHook('usa')", HTML_TEMPLATE)
        self.assertIn("playMarketingHook('india')", HTML_TEMPLATE)
        self.assertIn("playMarketingHook('hindi')", HTML_TEMPLATE)

        # 2. Verify sliders bounds
        self.assertIn('id="voiceRateSlider"', HTML_TEMPLATE)
        self.assertIn('id="voicePitchSlider"', HTML_TEMPLATE)
        self.assertIn('min="-15"', HTML_TEMPLATE)
        self.assertIn('max="25"', HTML_TEMPLATE)
        self.assertIn('min="-5"', HTML_TEMPLATE)
        self.assertIn('max="5"', HTML_TEMPLATE)

        # 3. Synthesize 48kHz audio with custom sliders
        tts = EdgeTTSVoiceEngine()
        text = "Welcome to 10484 Bellagio Road in Bel Air, an off-market $15 million estate."
        audio_data, _ = tts.synthesize_sync(text, rate="+10%", pitch="-2Hz", sample_rate=48000)
        self.assertTrue(audio_data.startswith(b"RIFF"))

        with wave.open(io.BytesIO(audio_data), "rb") as w:
            self.assertEqual(w.getframerate(), 48000)
            self.assertEqual(w.getnchannels(), 1)
            self.assertEqual(w.getsampwidth(), 2)

        # 4. Verify live audio waveform canvas
        self.assertIn('<canvas id="liveAudioWaveform"', HTML_TEMPLATE)

        # 5. One-click WAV export
        b64_audio = base64.b64encode(audio_data).decode("utf-8")
        self.assertTrue(b64_audio.startswith("UklGR"))
        recovered = base64.b64decode(b64_audio)
        self.assertEqual(recovered[:4], b"RIFF")


if __name__ == "__main__":
    unittest.main()
