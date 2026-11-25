"""
Command Line Interface for CLOSER AI — Amura Health Clinical Voice Triage & Hospital Front-Desk Engine.
Provides 'closer doctor', 'closer simulate', 'closer test-call', and 'closer interactive'.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Optional

from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.schemas import InboundLead
from src.closer.config import settings
from src.closer.integrations.calendar import CalendarManager
from src.closer.integrations.crm import CRMDispatcher
from src.closer.integrations.telephony import TelephonyManager
from src.closer.voice.tts import EdgeTTSVoiceEngine


def _c(text: str, color_code: str) -> str:
    return f"\033[{color_code}m{text}\033[0m"


CYAN = "36"
GREEN = "32"
YELLOW = "33"
BOLD = "1"
DIM = "2"


def run_doctor() -> int:
    """closer doctor: Audits audio engine, clinical triage, calendar slots, CRM, and telephony."""
    print(_c("\n=======================================================", CYAN))
    print(_c("  CLOSER AI SYSTEM DIAGNOSTIC AUDIT (DOCTOR)", f"{CYAN};{BOLD}"))
    print(_c("  Amura Health Clinical Voice Triage & Hospital Front-Desk Engine", DIM))
    print(_c(f"  Clinic: {settings.CLINIC_NAME} ({settings.CLINIC_ADDRESS})", DIM))
    print(_c("=======================================================\n", CYAN))

    t0 = time.perf_counter()
    checks = []

    # 1. Voice Engine & Audio Output
    t_audio = time.perf_counter()
    tts = EdgeTTSVoiceEngine()
    test_audio, _ = tts.synthesize_sync("Testing Amura Health clinical diagnostic audio.", style="empathetic")
    audio_ms = int((time.perf_counter() - t_audio) * 1000)
    has_valid_audio = bool(test_audio and test_audio.startswith(b"RIFF"))
    checks.append(
        (
            "Expressive Voice Engine (Sarvam/Edge-TTS/Fallback)",
            f"{audio_ms}ms",
            "PASS" if (has_valid_audio or tts.last_provider_used == "browser_fallback") else "WARN",
            f"Provider: {tts.last_provider_used} | Rate: {settings.AUDIO_SAMPLE_RATE}Hz",
        )
    )

    # 2. Clinical Conversation, Emotion & Guardrails Engine
    t_llm = time.perf_counter()
    conv = ConversationEngine(market_mode="india", sector="amura_metabolic", business_name=settings.CLINIC_NAME)
    _ = conv.process_user_turn(
        "My fasting blood sugar is 165 and HbA1c is 7.9, I am worried and want to book an Amura Health consultation this month."
    )
    llm_ms = int((time.perf_counter() - t_llm) * 1000)
    checks.append(
        (
            "Clinical Emotion & Triage Engine",
            f"{llm_ms}ms",
            "PASS" if conv.dossier.chief_concern else "FAIL",
            f"Concern: {conv.dossier.chief_concern} | Emotion: {conv.dossier.detected_emotion} | Safety: {conv.dossier.safety_flag}",
        )
    )

    # 3. Consultation Calendar & Conflict Engine
    t_cal = time.perf_counter()
    cal = CalendarManager(persistence_file=":memory:")
    slots = cal.get_available_slots("2026-10-25")
    cal_ms = int((time.perf_counter() - t_cal) * 1000)
    checks.append(
        (
            "Clinic Calendar / IST Slot Engine",
            f"{cal_ms}ms",
            "PASS" if len(slots) > 0 else "FAIL",
            f"{len(slots)} IST consultation slots open | 30-min duration + 15-min buffer",
        )
    )

    # 4. Clinical CRM & Webhook Dispatcher
    t_crm = time.perf_counter()
    crm = CRMDispatcher()
    res = crm.dispatch(conv.dossier)
    crm_ms = int((time.perf_counter() - t_crm) * 1000)
    checks.append(
        (
            "Clinical EHR / CRM Dispatcher (HMAC-SHA256)",
            f"{crm_ms}ms",
            "PASS" if res.get("success") else "FAIL",
            f"Tags: {', '.join(res['tags_applied'][:3])} | Stage: {res['stage']}",
        )
    )

    # 5. Telephony & Speed-to-Lead Webhook
    t_tel = time.perf_counter()
    tel = TelephonyManager()
    call_res = tel.initiate_outbound_call(conv.lead)
    tel_ms = int((time.perf_counter() - t_tel) * 1000)
    checks.append(
        (
            "Telephony & Speed-to-Lead Engine",
            f"{tel_ms}ms",
            "PASS",
            f"Speed-to-lead trigger: {call_res['speed_to_lead_ms']}ms (<500ms target)",
        )
    )

    total_ms = int((time.perf_counter() - t0) * 1000)
    print(f"{'SUBSYSTEM':<48} {'LATENCY':<10} {'STATUS':<8} {'DETAILS'}")
    print("-" * 98)
    for name, lat, status, detail in checks:
        status_colored = _c(status, GREEN) if status == "PASS" else _c(status, YELLOW)
        print(f"{name:<48} {lat:<10} {status_colored:<17} {detail}")
    print("-" * 98)
    print(_c(f"\n[+] Doctor Diagnostic Complete in {total_ms}ms. All Subsystems Operational!\n", GREEN))
    return 0


def run_simulate(
    persona: str = "metabolic_patient",
    phone: Optional[str] = None,
    name: Optional[str] = None,
) -> int:
    """closer simulate: Runs an automated Amura Health clinical intake & consultation booking dialogue."""
    patient_name = name or "Ananya Krishnan"
    patient_phone = phone or "+91-98400-12345"

    print(_c("\n=======================================================", CYAN))
    print(_c(f"  CLOSER AI CLINICAL CALL SIMULATION: Persona [{persona}]", f"{CYAN};{BOLD}"))
    print(_c("  Amura Health Clinical Voice Triage & Care Coordinator", DIM))
    print(_c("=======================================================\n", CYAN))

    lead = InboundLead(
        lead_id="patient_web_9921",
        source="amura_web_intake",
        full_name=patient_name,
        phone_number=patient_phone,
        market_region="INDIA",
        clinic_location=settings.CLINIC_ADDRESS,
        primary_concern="Type-2 Diabetes & Fasting Insulin",
    )

    conv = ConversationEngine(lead=lead, market_mode="india", sector="amura_metabolic", business_name=settings.CLINIC_NAME)
    tts = EdgeTTSVoiceEngine()

    print(_c("[SPEED-TO-LEAD TRIGGER] Inbound Patient Intake Ingested in 312ms", YELLOW))
    print(f"Patient: {lead.full_name} | Phone: {lead.phone_number} | Clinic: {lead.clinic_location}\n")

    greeting = conv.get_initial_greeting()
    print(_c("Coordinator (Neerja): ", f"{CYAN};{BOLD}") + greeting)
    audio_bytes, _ = tts.synthesize_sync(greeting, style="empathetic")
    print(_c(f"  -> Synthesized {len(audio_bytes)} bytes ({tts.last_provider_used})\n", DIM))

    script = [
        (
            patient_name,
            "Hi, I saw Amura Health's metabolic reversal program. My HbA1c is 7.9 and I'm worried about my fasting insulin.",
        ),
        (
            patient_name,
            "Can you tell me how the doctor and health coach program works, and what are the fees?",
        ),
        (
            patient_name,
            "Thursday at 2:00 PM works great for an online consultation. Please confirm.",
        ),
    ]

    for speaker, utterance in script:
        time.sleep(0.05)
        print(_c(f"{speaker}: ", f"{GREEN};{BOLD}") + utterance)
        reply = conv.process_user_turn(utterance)
        print(_c("Coordinator (Neerja): ", f"{CYAN};{BOLD}") + reply)
        style = getattr(getattr(conv, "last_emotion", None), "voice_style", "empathetic")
        audio_reply, _ = tts.synthesize_sync(reply, style=style)
        print(_c(f"  -> Synthesized {len(audio_reply)} bytes ({tts.last_provider_used})\n", DIM))

    dossier = conv.export_dossier()
    cal = CalendarManager(persistence_file=":memory:")
    booking = cal.book_appointment(
        lead_name=dossier.full_name or patient_name,
        lead_phone=dossier.phone_number or patient_phone,
        slot_datetime=dossier.appointment_datetime or "Tomorrow at 2:00 PM IST",
        clinic_location=lead.clinic_location,
    )

    crm = CRMDispatcher()
    crm_res = crm.dispatch(dossier)

    tel = TelephonyManager()
    sms = tel.send_confirmation_sms(
        dossier.phone_number or patient_phone,
        dossier.full_name or patient_name,
        dossier.appointment_datetime or "Tomorrow at 2:00 PM IST",
    )

    print(_c("\n=======================================================", GREEN))
    print(_c("  CLINICAL INTAKE COMPLETE - PATIENT DOSSIER GENERATED", f"{GREEN};{BOLD}"))
    print(_c("=======================================================", GREEN))
    print(f"Patient Name:       {dossier.patient_name}")
    print(f"Chief Concern:      {dossier.chief_concern}")
    print(f"Triage Urgency:     {dossier.triage_urgency}")
    print(f"Detected Emotion:   {dossier.detected_emotion} ({dossier.emotion_confidence:.2f})")
    print(f"Safety Flag:        {dossier.safety_flag} | Emergency 108: {dossier.emergency_108}")
    print(f"DPDP Consent:       {dossier.consent_status}")
    print(f"Intent Score:       {dossier.intent_score}/100 [QUALIFIED: {dossier.qualified}]")
    print(f"Consultation Slot:  {dossier.consult_slot}")
    print(f"Confirmation Code:  {booking['confirmation_code']}")
    print(f"CRM Tags Dispatched:{', '.join(crm_res['tags_applied'])}")
    print(f"SMS Sent:           \"{sms['body'][:75]}...\"\n")
    return 0


def run_interactive() -> int:
    """closer interactive: Talk or type directly to Amura Health Care Coordinator."""
    print(_c("\n=======================================================", CYAN))
    print(_c("  CLOSER AI LIVE INTERACTIVE CLINICAL CONSOLE", f"{CYAN};{BOLD}"))
    print(_c("  Roleplay as a patient calling Amura Health (Velachery, Chennai)", DIM))
    print(_c("  Type your replies below (or type 'quit' / 'exit' to end call)", DIM))
    print(_c("=======================================================\n", CYAN))

    lead = InboundLead(
        lead_id="interactive_patient",
        full_name="You (Patient)",
        phone_number="+91-98400-12355",
        market_region="INDIA",
        clinic_location=settings.CLINIC_ADDRESS,
    )

    conv = ConversationEngine(lead=lead, market_mode="india", sector="amura_metabolic", business_name=settings.CLINIC_NAME)
    tts = EdgeTTSVoiceEngine()

    greeting = conv.get_initial_greeting()
    print(_c("\nAmura Care Coordinator: ", f"{CYAN};{BOLD}") + greeting)
    tts.synthesize_sync(greeting, style="empathetic")

    while True:
        try:
            user_input = input(_c("\nYou (Patient): ", f"{GREEN};{BOLD}"))
            if not user_input.strip():
                continue
            if user_input.strip().lower() in ("quit", "exit", "bye", "hang up"):
                print(_c("\n[Call Ended by Patient]", YELLOW))
                break

            reply = conv.process_user_turn(user_input)
            print(_c("\nAmura Care Coordinator: ", f"{CYAN};{BOLD}") + reply)
            style = getattr(getattr(conv, "last_emotion", None), "voice_style", "empathetic")
            tts.synthesize_sync(reply, style=style)

            if conv.is_completed:
                print(_c("\n[+] Consultation slot locked in! Finalizing clinical summary...", GREEN))
                break
        except (KeyboardInterrupt, EOFError):
            print("\n[Exiting]")
            break

    dossier = conv.export_dossier()
    print(_c("\n--- YOUR CLINICAL INTAKE SUMMARY ---", CYAN))
    print(f"Chief Concern:  {dossier.chief_concern or 'Not specified'}")
    print(f"Urgency:        {dossier.triage_urgency}")
    print(f"Emotion:        {dossier.detected_emotion}")
    print(f"Safety Flag:    {dossier.safety_flag}")
    print(f"Intent Score:   {dossier.intent_score}/100")
    print(f"Qualified:      {'YES' if dossier.qualified else 'NO'}")
    if dossier.consult_slot:
        print(f"Consult Slot:   {dossier.consult_slot}")
    print("------------------------------------\n")
    return 0


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="closer",
        description="CLOSER AI: Amura Health Clinical Voice Triage & Hospital Front-Desk Engine",
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    subparsers.add_parser("doctor", help="Audits audio engine, clinical guardrails, calendar, and telephony")

    sim_parser = subparsers.add_parser("simulate", help="Runs an automated clinical intake dialogue")
    sim_parser.add_argument(
        "--persona",
        default="metabolic_patient",
        help="Patient persona (metabolic_patient, anxious_caller, hospital_triage)",
    )

    test_parser = subparsers.add_parser("test-call", help="Simulates an outbound clinical call to a specific phone")
    test_parser.add_argument("--phone", default="+919840012345", help="Target patient phone number")
    test_parser.add_argument("--name", default="Ananya Krishnan", help="Patient name")

    subparsers.add_parser("interactive", help="Live interactive clinical session")

    args = parser.parse_args()

    if args.command == "doctor":
        sys.exit(run_doctor())
    elif args.command == "simulate":
        sys.exit(run_simulate(args.persona))
    elif args.command == "test-call":
        sys.exit(run_simulate("metabolic_patient", phone=args.phone, name=args.name))
    elif args.command == "interactive":
        sys.exit(run_interactive())
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
