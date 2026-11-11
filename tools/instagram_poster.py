#!/usr/bin/env python3
"""tools/instagram_poster.py — Automated Instagram Reel Publisher for CLOSER AI

Supports two publishing engines:
1. Meta Official Graph API (Recommended for 100% ban-free, zero-checkpoint automation on Creator/Business accounts)
2. Instagrapi (Direct private API client with session reuse)

Usage:
  python tools/instagram_poster.py --preview           # Print full viral caption, tags & DM automation instructions
  python tools/instagram_poster.py --post --api graph   # Post via Meta Graph API
  python tools/instagram_poster.py --post --api private # Post via Instagrapi
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VIDEO = BASE_DIR / "demos" / "closer_reel.mp4"
DEFAULT_COVER = BASE_DIR / "demos" / "closer_reel_poster.jpg"

# ==============================================================================
# HIGH-CONVERTING INSTAGRAM VIRAL CAPTION & COMMENT HOOK
# Designed for maximum comment velocity to trigger the Instagram Reel algorithm
# ==============================================================================
VIRAL_CAPTION = """Why do 70% of luxury real estate leads vanish into thin air? 📉

At JSM Integrated Services in Chennai, we looked at the real data:
Builders spend ₹50,000 to ₹5,00,000 every single month on Meta & Google ads.

Then this happens:
A high-intent buyer inquires at 11:42 PM about a ₹15.5 Crore beach villa.
Your human sales team is asleep.
By the time someone calls back 4 to 6 hours later… the buyer has already moved on.

Harvard & MIT studies prove it:
Lead qualification drops by 391% after just 5 MINUTES of delay.

Meet CLOSER AI — the autonomous voice gatekeeper built for high-ticket developers:
⚡ Sub-45s Inbound Callback (dials before intent decays)
🗣️ Fluent Tri-Lingual Closers (English NRI desk, Tamil Chennai ECR villas, Hindi NCR penthouses)
📱 Live WhatsApp Co-Browsing (drops verified RERA floor plans & Apple Wallet passes WHILE on call)
💰 Unit Economics: ₹1.55 per call vs ₹220 for traditional call centers.

Want the complete real estate AI playbook?

💬 COMMENT "CLOSER" BELOW 👇
and our system will automatically DM you:
1. The Full Luxury Real Estate AI Blueprint & Architecture
2. Proven High-Ticket Objection-Handling Script Breakdown
3. The Private Live Developer Test Phone Number

Save this reel and comment "CLOSER" right now. 🚀

---
#RealEstate #PropTech #AIAgents #ArtificialIntelligence #RealEstateMarketing #LuxuryRealEstate #ChennaiRealEstate #ECRVillas #GurugramRealEstate #VoiceAI #SaaS #StartupLife #LeadGeneration #Automation #BuildInPublic
"""

def check_video(video_path: Path):
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found at {video_path}")
    size_mb = video_path.stat().st_size / (1024 * 1024)
    print(f"✓ Video verified: {video_path.name} ({size_mb:.2f} MB)")
    return True

def post_via_meta_graph(video_path: Path, caption: str):
    """Post using Meta's Official Instagram Content Publishing Graph API.
    Requirements:
      - INSTAGRAM_ACCOUNT_ID (Your Instagram Business/Creator Account ID)
      - INSTAGRAM_ACCESS_TOKEN (Page access token with instagram_content_publish permission)
      - PUBLIC_VIDEO_URL (Direct HTTPS URL to video, e.g. https://closer-ai-tawny.vercel.app/demos/closer_reel.mp4)
    """
    account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    public_url = os.getenv("PUBLIC_VIDEO_URL", "https://closer-ai-tawny.vercel.app/demos/closer_reel.mp4")

    if not account_id or not access_token:
        print("\n[!] Meta Graph API credentials not detected in environment.")
        print("To publish via Meta Graph API without checkpoints:")
        print("  export INSTAGRAM_ACCOUNT_ID='your_ig_user_id'")
        print("  export INSTAGRAM_ACCESS_TOKEN='your_meta_page_access_token'")
        print(f"  export PUBLIC_VIDEO_URL='{public_url}'")
        return False

    import urllib.request
    import urllib.parse
    import time

    print(f"\n[1/3] Creating Instagram Reel Container for video: {public_url}...")
    create_url = f"https://graph.facebook.com/v19.0/{account_id}/media"
    data = urllib.parse.urlencode({
        "media_type": "REELS",
        "video_url": public_url,
        "caption": caption,
        "access_token": access_token
    }).encode("utf-8")

    req = urllib.request.Request(create_url, data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        container_id = res.get("id")
        print(f"  -> Container created successfully: {container_id}")

    print("\n[2/3] Waiting for Instagram video processing...")
    status_url = f"https://graph.facebook.com/v19.0/{container_id}?fields=status_code&access_token={access_token}"
    for _ in range(30):
        time.sleep(5)
        with urllib.request.urlopen(status_url) as s_resp:
            s_data = json.loads(s_resp.read().decode("utf-8"))
            status = s_data.get("status_code")
            print(f"  -> Current processing status: {status}")
            if status == "FINISHED":
                break
            elif status == "ERROR":
                print("  [!] Video processing failed on Meta servers.")
                return False

    print("\n[3/3] Publishing Reel to Instagram feed...")
    publish_url = f"https://graph.facebook.com/v19.0/{account_id}/media_publish"
    pub_data = urllib.parse.urlencode({
        "creation_id": container_id,
        "access_token": access_token
    }).encode("utf-8")
    p_req = urllib.request.Request(publish_url, data=pub_data, method="POST")
    with urllib.request.urlopen(p_req) as p_resp:
        p_res = json.loads(p_resp.read().decode("utf-8"))
        media_id = p_res.get("id")
        print(f"\n🎉 REEL PUBLISHED SUCCESSFULLY! Media ID: {media_id}")
        return True

def post_via_instagrapi(video_path: Path, caption: str):
    """Post using the open-source instagrapi library with session dumping."""
    try:
        from instagrapi import Client
    except ImportError:
        print("[!] instagrapi is not installed. Run: pip install instagrapi")
        return False

    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    session_file = BASE_DIR / ".instagram_session.json"

    if not username or not password:
        print("\n[!] Instagram credentials not detected in environment.")
        print("To publish via instagrapi:")
        print("  export INSTAGRAM_USERNAME='your_handle'")
        print("  export INSTAGRAM_PASSWORD='your_password'")
        return False

    cl = Client()
    if session_file.exists():
        print(f"Loading cached Instagram session from {session_file}...")
        try:
            cl.load_settings(session_file)
            cl.login(username, password)
        except Exception:
            print("Session expired, re-authenticating...")
            cl.login(username, password)
            cl.dump_settings(session_file)
    else:
        print(f"Logging in as {username}...")
        cl.login(username, password)
        cl.dump_settings(session_file)

    print(f"Uploading Reel ({video_path.name})...")
    media = cl.clip_upload(
        path=str(video_path),
        caption=caption
    )
    print(f"\n🎉 REEL UPLOADED! Media ID: {media.id}, Code: {media.code}")
    print(f"View live at: https://www.instagram.com/reel/{media.code}/")
    return True

def main():
    parser = argparse.ArgumentParser(description="CLOSER AI Automated Instagram Publisher")
    parser.add_argument("--preview", action="store_true", help="Preview viral caption, hooks, and tags")
    parser.add_argument("--post", action="store_true", help="Publish the reel to Instagram")
    parser.add_argument("--api", choices=["graph", "private"], default="graph", help="Publishing API engine")
    parser.add_argument("--video", type=str, default=str(DEFAULT_VIDEO), help="Path to reel MP4")
    args = parser.parse_args()

    video_path = Path(args.video)

    if args.preview or not args.post:
        print("=" * 70)
        print("CLOSER AI — INSTAGRAM VIRAL PUBLISHING ENGINE")
        print("=" * 70)
        print("\n[1] VIDEO ASSET CHECK:")
        check_video(video_path)
        print(f"\n[2] VIRAL CAPTION & COMMENT MAGNET HOOK:")
        print("-" * 50)
        print(VIRAL_CAPTION)
        print("-" * 50)
        print("\n[3] COMMENT-TO-DM VIRAL STRATEGY:")
        print("  • When users comment 'CLOSER', Instagram's algorithm treats comment velocity as 5x more valuable than likes.")
        print("  • Connect ManyChat or an Instagram Webhook to auto-DM anyone who comments 'CLOSER' with:")
        print("    'Hey! Here is your free Luxury Real Estate AI Blueprint: https://closer-ai-tawny.vercel.app/commercial'")
        print("\n[4] TO AUTOMATE POSTING:")
        print("  Option A (Recommended, Official Meta Graph API):")
        print("    python tools/instagram_poster.py --post --api graph")
        print("  Option B (Instagrapi wrapper):")
        print("    python tools/instagram_poster.py --post --api private")
        return

    if args.post:
        check_video(video_path)
        if args.api == "graph":
            post_via_meta_graph(video_path, VIRAL_CAPTION)
        else:
            post_via_instagrapi(video_path, VIRAL_CAPTION)

if __name__ == "__main__":
    main()
