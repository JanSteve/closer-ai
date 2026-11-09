"""Test Bland AI Phone Calling for CLOSER AI.

Dispatches an outbound phone call to your mobile number:
    python3 test_bland_call.py --to +919876543210 --agent tamil
    python3 test_bland_call.py --to +919876543210 --agent hindi
    python3 test_bland_call.py --to +15551234567 --agent english
"""

import argparse
import asyncio
import os
import sys

from closer.telephony.bland_engine import BlandTelephonyEngine


async def main():
    parser = argparse.ArgumentParser(description="Dispatch Bland AI phone call")
    parser.add_argument("--to", required=True, help="Destination phone number in E.164 format (+91... / +1...)")
    parser.add_argument("--agent", choices=["tamil", "hindi", "english"], default="tamil", help="Closer language")
    parser.add_argument("--duration", type=int, default=3, help="Max duration in minutes (default: 3)")
    args = parser.parse_args()

    engine = BlandTelephonyEngine()

    print("\n=======================================================")
    print("  📞  CLOSER AI: BLAND AI REAL-WORLD CALL DISPATCHER")
    print(f"  Target Number : {args.to}")
    print(f"  Agent Voice   : {args.agent.upper()}")
    print(f"  Max Duration  : {args.duration} minutes")
    print("=======================================================\n")

    if not engine.is_configured:
        print("❌ BLAND_API_KEY is not configured in .env!\n")
        print("💡 HOW TO GET IT 100% FREE (NO CREDIT CARD NEEDED):")
        print("1. Go to https://bland.ai and sign up (takes 30 seconds).")
        print("2. Copy your API Key from the Bland AI Dashboard.")
        print("3. Add it to your .env file:")
        print("   echo 'BLAND_API_KEY=your_key_here' >> .env\n")
        print("4. Re-run this command: python3 test_bland_call.py --to " + args.to)
        return

    print("🚀 Initiating call via Bland AI network...")
    result = await engine.dispatch_phone_call(
        phone_number=args.to,
        language=args.agent,
        max_duration_minutes=args.duration
    )

    if result.get("success"):
        print(f"✅ CALL PLACED SUCCESSFULLY!")
        print(f"   Call ID: {result.get('call_id')}")
        print(f"   Your phone should ring in ~5-15 seconds.")
        print(f"   Answer it and test negotiation/discounts or barge-in!\n")
    else:
        print(f"❌ Failed to dispatch call: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
