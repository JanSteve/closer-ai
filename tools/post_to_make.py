#!/usr/bin/env python3
"""tools/post_to_make.py — One-Click & Scheduled Webhook Dispatcher to Make.com

Dispatches the production CLOSER AI Reel and viral caption to a Make.com Custom Webhook,
which automatically publishes it to Instagram for Business (Reels).

Usage:
  # Test with Make.com webhook URL:
  python tools/post_to_make.py --webhook https://hook.eu1.make.com/your-webhook-token

  # Or set via environment variable:
  export MAKE_WEBHOOK_URL="https://hook.eu1.make.com/your-webhook-token"
  python tools/post_to_make.py
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
from datetime import datetime

DEFAULT_VIDEO_URL = "https://closer-ai-tawny.vercel.app/demos/closer_reel.mp4"
DEFAULT_COVER_URL = "https://closer-ai-tawny.vercel.app/demos/closer_reel_poster.jpg"

VIRAL_CAPTION = """Are you paying a performance marketing agency ₹2,50,000 every month just to get an Excel sheet of dead leads? 📊📉

Watch what actually happens in India:
1️⃣ Your agency runs Meta ads promising "500 High-Intent Inquiries".
2️⃣ Your telecaller calls 4 hours later.
3️⃣ The customer yells: "WHO ARE YOU?! I NEVER FILLED ANY FORM!" and slams the phone. 📞💥

Harvard Business Review proved this:
Wait just 5 minutes, and lead qualification collapses by -391%. In 4 hours, your ad budget is literally up in smoke. 🔥

Enter CLOSER AI — the autonomous voice sales agent operating across all high-ticket sectors:

🏖️ REAL ESTATE: Maya closes ₹15.5 Cr ECR beach villas in fluent English with instant RERA floor plans.
🩺 HEALTHCARE & CLINICS: Dr. Pallavi books hair transplants & dental VIP consultations in Chennai in conversational Tamil.
☀️ SOLAR & HOME RENO: Swati calculates 40% government rooftop subsidies in Hindi for Delhi NCR homeowners.

⚡ 0.08s Speed-To-Lead: Dials while the lead is still looking at your ad.
📲 Multi-Sector WhatsApp Engine: Drops floor plans, clinic passes & quotes directly on WhatsApp mid-call.
💰 ₹1.55 Economics: Replaces ₹220/call human agency overhead.

Want to see how CLOSER AI works for your exact industry?

👇 COMMENT "AUDIT" BELOW 👇
and our system will automatically DM you:
1. The Multi-Sector Autonomous Lead-Capture Blueprint
2. Live Tamil, Hindi & English Voice Agent Demo Numbers
3. Free Unit Economics Calculator for Real Estate, Clinics & Solar

Save this reel and comment "AUDIT" right now! 🚀

#MetaAds #PerformanceMarketing #LeadGeneration #AIAgents #RealEstateIndia #DentalClinic #HairTransplantIndia #SolarEnergy #EdTech #VoiceAI #Automation #CloserAI"""

def dispatch_to_make(webhook_url: str):
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "title": "CLOSER AI — The Performance Agency Trap",
        "video_url": DEFAULT_VIDEO_URL,
        "cover_url": DEFAULT_COVER_URL,
        "caption": VIRAL_CAPTION,
        "call_to_action": "AUDIT",
        "source": "Antigravity Automated Dispatch"
    }

    print(f"[*] Packaging Instagram Reel payload...")
    print(f"    Video URL: {payload['video_url']}")
    print(f"    Cover URL: {payload['cover_url']}")
    print(f"    Caption Length: {len(payload['caption'])} characters")
    print(f"    Target Webhook: {webhook_url}")

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data_bytes,
        headers={"Content-Type": "application/json", "User-Agent": "CLOSER-AI-Dispatcher/1.0"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
            print(f"\n[✓] Successfully dispatched to Make.com!")
            print(f"    HTTP Status: {status}")
            print(f"    Make.com Response: {body}")
            print(f"\nMake.com will now trigger 'Instagram for Business -> Create a Reel' and publish to your profile.")
            return True
    except urllib.error.HTTPError as e:
        print(f"\n[!] Make.com Webhook error: HTTP {e.code} — {e.read().decode('utf-8', errors='ignore')}")
        return False
    except Exception as e:
        print(f"\n[!] Failed to connect to Make.com Webhook: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Dispatch CLOSER AI Instagram Reel to Make.com")
    parser.add_argument("--webhook", default=os.getenv("MAKE_WEBHOOK_URL"), help="Make.com Custom Webhook URL")
    args = parser.parse_args()

    if not args.webhook:
        print("Usage: python tools/post_to_make.py --webhook <YOUR_MAKE_WEBHOOK_URL>")
        print("Or set: export MAKE_WEBHOOK_URL='https://hook.eu1.make.com/...'")
        sys.exit(1)

    dispatch_to_make(args.webhook)

if __name__ == "__main__":
    main()
