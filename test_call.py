#!/usr/bin/env python3
"""
Interactive Phone Call Tester for CLOSER AI.
Plays audio out loud through your Mac speakers using native macOS 'afplay'.
Allows you to roleplay as a luxury real estate buyer speaking to Sophia or Guy.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# Ensure src is in sys.path
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "src"))

from src.closer.config import settings
from src.closer.agent.conversation import ConversationEngine
from src.closer.voice.tts import EdgeTTSVoiceEngine


def play_audio(audio_bytes: bytes):
    """Plays audio bytes out loud on Mac speakers using afplay."""
    if not audio_bytes:
        return
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        tf.write(audio_bytes)
        temp_wav = tf.name

    try:
        subprocess.run(["afplay", temp_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    finally:
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except OSError:
                pass


def main():
    print("=" * 70)
    print("   CLOSER AI: DUAL-MARKET LIVE VOICE SIMULATOR (USA & INDIA)")
    print(f"   Brokerage / Org: {settings.BROKERAGE_NAME}")
    print(f"   Founder: {settings.FOUNDER_NAME}")
    print("=" * 70)
    print("\nSelect your Market & Agent Mode:")
    print("  1. 🇺🇸 USA: Luxury Real Estate ISA (Sophia / Guy) [DEFAULT]")
    print("  2. 🇮🇳 INDIA: Customer Care & Lead Support Executive (Priya / Neerja)")
    
    market_choice = input("\nEnter Market [1 or 2, default 1]: ").strip()
    is_india = (market_choice == "2")
    market_mode = "india" if is_india else "usa"

    if is_india:
        print("\nSelect Indian Customer Care Voice Persona:")
        print("  1. 👩 Priya / Neerja (Warm, Polite Customer Care & Client Relations) [DEFAULT]")
        print("  2. 👨 Prabhat / Aarav (Professional Corporate Support & Technical Lead)")
        vc = input("Choice [1 or 2, default 1]: ").strip()
        voice_name = "en-IN-PrabhatNeural" if vc == "2" else "en-IN-NeerjaNeural"
        agent_name = "Prabhat" if vc == "2" else "Priya"
    else:
        print("\nSelect US Luxury Real Estate Voice Persona:")
        print("  1. 👩 Sophia (Aria - Warm & Consultative Luxury Concierge) [DEFAULT]")
        print("  2. 👨 Guy    (Guy - Confident Elite Luxury Broker Tone)")
        print("  3. 👩 Jenny  (Jenny - Crisp & Upbeat Advisor)")
        print("  4. 👨 Christopher (Christopher - Authoritative Executive)")
        vc = input("Choice [1-4, default 1]: ").strip()
        voice_map = {
            "1": "en-US-AriaNeural",
            "2": "en-US-GuyNeural",
            "3": "en-US-JennyNeural",
            "4": "en-US-ChristopherNeural"
        }
        voice_name = voice_map.get(vc, "en-US-AriaNeural")
        agent_name = "Guy" if "Guy" in voice_name or "Christopher" in voice_name else "Sophia"

    print(f"\n[+] Connecting outbound call with {agent_name} ({voice_name})...")
    print(f"[+] Active Market Mode: {market_mode.upper()}")
    print("[*] TIP: Turn up your Mac volume! Audio will play through your speakers.")
    print("[*] Type 'quit' or 'q' to hang up.\n")

    engine = ConversationEngine(market_mode=market_mode)
    tts = EdgeTTSVoiceEngine(default_voice=voice_name)

    # Initial Agent Greeting
    greeting = engine.get_initial_greeting()
    print(f"{agent_name} > {greeting}")
    print("  [🔊 Speaking through speakers...]")
    audio, latency = tts.synthesize_sync(greeting, voice=voice_name)
    play_audio(audio)

    while True:
        try:
            print("\n" + "-" * 70)
            user_input = input("You (Buyer / Customer) > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q", "bye"):
                print(f"\n[+] Call ended. Thank you for testing CLOSER AI!")
                break

            # Process turn through stateful conversation engine
            reply = engine.process_user_turn(user_input)
            dossier = engine.export_dossier()

            print(f"\n{agent_name} > {reply}")
            print(f"  [🔊 Synthesizing & Speaking ({latency:.2f}s latency)...]")
            audio, latency = tts.synthesize_sync(reply, voice=voice_name)
            play_audio(audio)

            # Display real-time Pydantic qualification metrics
            print("\n  [📊 Live Client Dossier]")
            if dossier.market_region == "INDIA":
                if dossier.budget_inr_text:
                    print(f"    • Budget: {dossier.budget_inr_text}")
                elif dossier.budget_max:
                    print(f"    • Budget: ₹{dossier.budget_max:,.0f} INR")
                if dossier.bhk_preference:
                    print(f"    • Configuration: {dossier.bhk_preference}")
                if dossier.ticket_id:
                    print(f"    • 🎟️ Support Ticket: #{dossier.ticket_id} (LOGGED)")
                if dossier.whatsapp_status or dossier.whatsapp_dispatched:
                    print(f"    • 📲 WhatsApp Dispatch: CONFIRMED")
            else:
                if dossier.budget_max:
                    print(f"    • Budget: ${dossier.budget_max:,.0f} USD")
                if dossier.financing_type:
                    print(f"    • Financing: {dossier.financing_type.upper()}")

            if dossier.timeframe:
                print(f"    • Timeframe: {dossier.timeframe}")
            print(f"    • Intent / Resolution Score: {dossier.intent_score} / 100")
            if dossier.appointment_datetime:
                visit_label = "Site Visit" if is_india else "VIP Tour"
                print(f"    • 📅 {visit_label}: {dossier.appointment_datetime} (CONFIRMED)")

        except (KeyboardInterrupt, EOFError):
            print("\n\n[+] Call disconnected.")
            break


if __name__ == "__main__":
    main()
