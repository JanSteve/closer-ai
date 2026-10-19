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
    print("   CLOSER AI: LIVE VOICE PHONE CALL SIMULATOR")
    print(f"   Brokerage: {settings.BROKERAGE_NAME}")
    print(f"   Founder: {settings.FOUNDER_NAME}")
    print("=" * 70)
    print("\nSelect your AI Inside Sales Agent voice:")
    print("  1. 👩 Sophia (Aria - Female, Warm & Consultative Luxury Assistant) [DEFAULT]")
    print("  2. 👨 Guy    (Guy - Male, Confident Luxury Broker Tone)")
    print("  3. 👩 Jenny  (Jenny - Female, Crisp & Upbeat)")
    print("  4. 👨 Christopher (Christopher - Male, Authoritative Executive)")
    print("  5. 👩 Neerja (Neerja - Indian English Luxury Consultant)")
    
    choice = input("\nEnter choice [1-5, or press Enter for Sophia]: ").strip()
    voice_map = {
        "1": "en-US-AriaNeural",
        "2": "en-US-GuyNeural",
        "3": "en-US-JennyNeural",
        "4": "en-US-ChristopherNeural",
        "5": "en-IN-NeerjaNeural"
    }
    voice_name = voice_map.get(choice, "en-US-AriaNeural")
    agent_name = "Guy" if "Guy" in voice_name or "Christopher" in voice_name else "Sophia"

    print(f"\n[+] Connecting outbound call with {agent_name} ({voice_name})...")
    print("[*] TIP: Turn up your Mac volume! Audio will play through your speakers.")
    print("[*] Type 'quit' or 'q' to hang up.\n")

    engine = ConversationEngine()
    tts = EdgeTTSVoiceEngine(default_voice=voice_name)

    # Initial Agent Greeting
    greeting = engine.history[0].content
    print(f"{agent_name} > {greeting}")
    print("  [🔊 Speaking through speakers...]")
    audio, latency = tts.synthesize_sync(greeting, voice=voice_name)
    play_audio(audio)

    while True:
        try:
            print("\n" + "-" * 70)
            user_input = input("You (Buyer) > ").strip()
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
            print("\n  [📊 Live Lead Dossier]")
            if dossier.budget_max:
                print(f"    • Budget: ${dossier.budget_max:,.0f} USD")
            if dossier.financing_type:
                print(f"    • Financing: {dossier.financing_type.upper()}")
            if dossier.timeframe:
                print(f"    • Timeframe: {dossier.timeframe}")
            print(f"    • Intent Score: {dossier.intent_score} / 100")
            if dossier.appointment_datetime:
                print(f"    • 📅 Google Calendar Tour: {dossier.appointment_datetime} (LOCKED)")

        except (KeyboardInterrupt, EOFError):
            print("\n\n[+] Call disconnected.")
            break


if __name__ == "__main__":
    main()
