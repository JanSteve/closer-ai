#!/usr/bin/env python3
"""
Interactive Terminal Walkthrough for CLOSER AI.
Simulates a live inbound luxury real estate lead and autonomous voice qualification call.
"""

import sys
import time
from pathlib import Path

# Add project root and src to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "src"))

from src.closer.config import settings
from src.closer.agent.schemas import InboundLead
from src.closer.voice.call_session import CallSession
from src.closer.voice.tts import EdgeTTSVoiceEngine
from src.closer.integrations.calendar import CalendarManager
from src.closer.integrations.crm import CRMDispatcher
from src.closer.integrations.telephony import TelephonyManager


def c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def print_banner():
    print(c("\n" + "=" * 75, "36"))
    print(c("  CLOSER AI: AUTONOMOUS VOICE LEAD QUALIFICATION ENGINE", "36;1"))
    print(c("  Production Startup Architecture for Luxury Real Estate Brokerages", "2"))
    print(c(f"  Architect & Founder: {settings.FOUNDER_NAME} | {settings.BROKERAGE_NAME}", "2"))
    print(c("=" * 75 + "\n", "36"))


def main():
    print_banner()
    time.sleep(0.5)

    # Step 1: Inbound Lead Arrival
    print(c("[STAGE 1: INBOUND LEAD CAPTURE]", "33;1"))
    raw_lead = {
        "id": "ig_ad_88320",
        "name": "Harrison Sterling",
        "phone": "+1-310-555-0144",
        "email": "harrison@sterlingcap.com",
        "campaign": "Bel Air Private Architectural Showcase",
        "listing_address": "10484 Bellagio Rd, Bel Air, CA",
        "listing_price": 6850000
    }
    telephony = TelephonyManager()
    lead = telephony.parse_inbound_lead(raw_lead, source="instagram_ad")
    print(f" -> Lead Ingested from Instagram Lead Ad in {c('342ms', '32;1')}")
    print(f" -> Property: {lead.listing_address} (${lead.listing_price:,} USD)")
    print(f" -> Contact:  {lead.full_name} ({lead.phone_number})\n")
    time.sleep(0.8)

    # Step 2: Instant Outbound Call Trigger
    print(c("[STAGE 2: SPEED-TO-LEAD CARRIER DISPATCH]", "33;1"))
    outbound = telephony.initiate_outbound_call(lead)
    speed_ms = outbound['speed_to_lead_ms']
    print(f" -> Twilio Voice Call SID: {outbound['call_sid']}")
    print(f" -> Speed-to-lead response time: {c(str(speed_ms) + 'ms', '32;1')} (Industry average: 47 mins)")
    print(f" -> Connecting live carrier audio stream...\n")
    time.sleep(0.8)

    # Step 3: Conversational Loop
    print(c("[STAGE 3: VOICE-NATIVE QUALIFICATION CALL]", "33;1"))
    session = CallSession(lead=lead)
    greeting_text, greeting_audio = session.start_call()
    
    print(c("Agent (Sophia - ISA): ", "36;1") + greeting_text)
    print(c(f"   [Neural Speech: {len(greeting_audio)} bytes WAV | Sample Rate: 24kHz]", "2"))
    time.sleep(1.0)

    dialogue = [
        ("Harrison Sterling", "Hi Sophia, thanks for following up so fast. We saw the Bel Air video walkthrough. We love the views, but honestly we're just browsing online right now."),
        ("Harrison Sterling", "Well, we want at least 5 bedrooms, privacy, and panoramic skyline views. Our budget ceiling is around $6.5 million, and we're looking to purchase in the next 30 to 60 days."),
        ("Harrison Sterling", "We're actually paying all cash from our fund distribution, so financing is fully liquid."),
        ("Harrison Sterling", "This Thursday at 2:00 PM PST works perfectly for our schedule. Please confirm.")
    ]

    for speaker, utterance in dialogue:
        print()
        print(c(f"Buyer ({speaker}): ", "32;1") + utterance)
        time.sleep(0.8)
        
        reply_text, reply_audio = session.handle_user_speech(
            audio_chunk=b"",
            simulated_text=utterance
        )
        print(c("Agent (Sophia - ISA): ", "36;1") + reply_text)
        print(c(f"   [Neural Speech: {len(reply_audio)} bytes WAV | Interruption Buffer Ready]", "2"))
        time.sleep(0.8)

    # Step 4: Final Dossier Extraction
    print("\n" + c("[STAGE 4: EXTRACTED BUYER DOSSIER]", "33;1"))
    dossier = session.end_call()
    print(f" -> Full Name:         {dossier.full_name}")
    print(f" -> Budget:            ${dossier.budget_min:,} - ${dossier.budget_max:,} USD")
    print(f" -> Financing:         {dossier.financing_type.upper()} (Pre-Approved: {dossier.pre_approved})")
    print(f" -> Purchase Window:   {dossier.timeframe}")
    print(f" -> Intent Score:      {c(f'{dossier.intent_score}/100', '32;1')} [QUALIFIED: {dossier.qualified}]")
    print(f" -> Objections Solved: {len(dossier.objections_handled)} handled with luxury script")
    print(f" -> Reserved Tour:     {c(dossier.appointment_datetime, '36;1')}\n")
    time.sleep(0.8)

    # Step 5: Calendar Booking
    print(c("[STAGE 5: GOOGLE CALENDAR LOCK]", "33;1"))
    cal = CalendarManager(persistence_file=":memory:")
    booking = cal.book_appointment(
        lead_name=dossier.full_name,
        lead_phone=dossier.phone_number,
        slot_datetime=dossier.appointment_datetime,
        property_address=lead.listing_address
    )
    print(f" -> Appointment Confirmed: {booking['confirmation_code']}")
    print(f" -> Realtor Reserved:     {settings.REALTOR_NAME}")
    print(f" -> Tour Duration:        {settings.TOUR_DURATION_MINUTES} minutes (+15 min buffer)\n")
    time.sleep(0.8)

    # Step 6: CRM Dispatch & SMS
    print(c("[STAGE 6: CRM DOSSIER & SMS CONFIRMATION]", "33;1"))
    crm = CRMDispatcher()
    crm_res = crm.dispatch(dossier)
    print(f" -> Follow Up Boss Tags:  {', '.join(crm_res['tags_applied'])}")
    print(f" -> CRM Pipeline Stage:   {crm_res['stage']}")
    print(f" -> HMAC Webhook Signed:  {crm_res['record']['signature'][:32]}...")

    sms = telephony.send_confirmation_sms(dossier.phone_number, dossier.full_name, dossier.appointment_datetime)
    print(f" -> Carrier SMS Sent:     \"{sms['body'][:70]}...\"\n")

    print(c("=" * 75, "32"))
    print(c("  DEMO WALKTHROUGH COMPLETED SUCCESSFULLY (100% AUTONOMOUS)", "32;1"))
    print(c("=" * 75 + "\n", "32"))


if __name__ == "__main__":
    main()
