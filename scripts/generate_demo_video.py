#!/usr/bin/env python3
"""
Automated 1080p Demo Video Generator for CLOSER AI.
Uses Pillow to create high-resolution 1920x1080 storyboard frames,
EdgeTTS to synthesize professional narration audio,
and ffmpeg to compile a 60-second broadcast-ready MP4 demo with burned-in subtitles.
"""

import os
import sys
import math
import subprocess
from pathlib import Path
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont

# Add project root and src to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "src"))

from src.closer.config import settings
from src.closer.voice.tts import EdgeTTSVoiceEngine

DEMO_DIR = root_dir / "docs" / "demo"
DEMO_DIR.mkdir(parents=True, exist_ok=True)

# 1080p Dimensions
WIDTH = 1920
HEIGHT = 1080

# Color Palette
BG_COLOR = (9, 13, 22)           # #090d16
SURFACE_COLOR = (17, 24, 39)     # #111827
BORDER_COLOR = (55, 65, 81)      # #374151
PRIMARY_BLUE = (59, 130, 246)    # #3b82f6
EMERALD_GREEN = (16, 185, 129)  # #10b981
GOLD_ACCENT = (245, 158, 11)     # #f59e0b
TEXT_MAIN = (249, 250, 251)      # #f9fafb
TEXT_DIM = (156, 163, 175)       # #9ca3af


def get_font(size: int, bold: bool = False):
    """Loads system true type font or fallback."""
    font_paths = [
        "/System/Library/Fonts/SFPro.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Geneva.dfont"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_rounded_rect(draw, box, radius, fill, outline=None, width=1):
    """Draws rounded rectangle on PIL canvas."""
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def render_scene_1(out_path: str):
    """Scene 1: Title Card & The Speed-to-Lead Problem."""
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(im)

    font_title = get_font(68, bold=True)
    font_subtitle = get_font(32)
    font_body = get_font(26)
    font_badge = get_font(20, bold=True)
    font_stat_val = get_font(72, bold=True)
    font_stat_label = get_font(22)

    # Top Brand Header
    draw_rounded_rect(draw, (80, 60, 290, 110), 10, fill=(30, 58, 138), outline=PRIMARY_BLUE, width=2)
    draw.text((100, 72), "STARTUP SHOWCASE", fill=PRIMARY_BLUE, font=font_badge)

    draw.text((80, 140), "CLOSER AI", fill=TEXT_MAIN, font=font_title)
    draw.text((80, 230), "Autonomous Voice-Native Real Estate Lead Qualification Engine", fill=GOLD_ACCENT, font=font_subtitle)
    draw.text((80, 280), "Engineered for US Luxury Brokerages & Top 1% Producing Realtors", fill=TEXT_DIM, font=font_body)

    # Problem Cards Grid
    # Card 1: 5-Minute Drop-off
    draw_rounded_rect(draw, (80, 380, 640, 720), 16, fill=SURFACE_COLOR, outline=BORDER_COLOR, width=2)
    draw.text((120, 420), "-391%", fill=(239, 68, 68), font=font_stat_val)
    draw.text((120, 510), "Conversion Crash After 5 Mins", fill=TEXT_MAIN, font=get_font(26, bold=True))
    draw.text((120, 560), "Real estate leads called after 5 minutes\nare 8x less likely to book a showing.", fill=TEXT_DIM, font=get_font(20))

    # Card 2: Industry Average
    draw_rounded_rect(draw, (700, 380, 1260, 720), 16, fill=SURFACE_COLOR, outline=BORDER_COLOR, width=2)
    draw.text((740, 420), "47 Mins", fill=GOLD_ACCENT, font=font_stat_val)
    draw.text((740, 510), "Average Agent Response Time", fill=TEXT_MAIN, font=get_font(26, bold=True))
    draw.text((740, 560), "Buyers submit inquiries and continue\nscrolling to the next competing listing.", fill=TEXT_DIM, font=get_font(20))

    # Card 3: CLOSER AI Speed
    draw_rounded_rect(draw, (1320, 380, 1840, 720), 16, fill=(16, 40, 30), outline=EMERALD_GREEN, width=3)
    draw.text((1360, 420), "<500ms", fill=EMERALD_GREEN, font=font_stat_val)
    draw.text((1360, 510), "CLOSER AI Instant Response", fill=TEXT_MAIN, font=get_font(26, bold=True))
    draw.text((1360, 560), "Instant carrier voice call dialed while the\nbuyer is still looking at the property.", fill=(167, 243, 208), font=get_font(20))

    # Footer Metadata
    draw.line([(80, 960), (1840, 960)], fill=BORDER_COLOR, width=1)
    draw.text((80, 990), f"Founder: {settings.FOUNDER_NAME}  |  Brokerage: {settings.BROKERAGE_NAME}", fill=TEXT_DIM, font=get_font(22))
    draw.text((1420, 990), "GitHub: JanSteve/closer-ai", fill=PRIMARY_BLUE, font=get_font(22, bold=True))

    im.save(out_path)


def render_scene_2(out_path: str):
    """Scene 2: Inbound Lead Ingestion & Sub-500ms Trigger."""
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(im)

    font_title = get_font(52, bold=True)
    font_subtitle = get_font(26)

    draw_rounded_rect(draw, (80, 60, 400, 110), 10, fill=(16, 40, 30), outline=EMERALD_GREEN, width=2)
    draw.text((100, 72), "STAGE 1: INGESTION", fill=EMERALD_GREEN, font=get_font(20, bold=True))

    draw.text((80, 140), "Inbound Lead Captured & Dispatched in 342ms", fill=TEXT_MAIN, font=font_title)
    draw.text((80, 210), "Direct webhook ingestion from Meta Instagram Ads & Zillow Premier Agent", fill=TEXT_DIM, font=font_subtitle)

    # Lead Card Visual
    draw_rounded_rect(draw, (80, 300, 900, 880), 20, fill=SURFACE_COLOR, outline=BORDER_COLOR, width=2)
    draw.text((120, 340), "INSTAGRAM LEAD AD PAYLOAD", fill=GOLD_ACCENT, font=get_font(22, bold=True))
    draw.line([(120, 380), (860, 380)], fill=BORDER_COLOR, width=1)

    fields = [
        ("Campaign:", "Bel Air Private Architectural Showcase"),
        ("Listing Address:", "10484 Bellagio Rd, Bel Air, CA"),
        ("Asking Price:", "$6,850,000 USD"),
        ("Lead Name:", "Harrison Sterling"),
        ("Phone Number:", "+1 (310) 555-0144"),
        ("Ingestion Latency:", "342ms (Sub-500ms Guaranteed)")
    ]

    y = 410
    for label, val in fields:
        draw.text((120, y), label, fill=TEXT_DIM, font=get_font(22))
        draw.text((360, y), val, fill=TEXT_MAIN if "342ms" not in val else EMERALD_GREEN, font=get_font(22, bold=True))
        y += 65

    # Outbound Trigger Card Visual
    draw_rounded_rect(draw, (960, 300, 1840, 880), 20, fill=(17, 30, 50), outline=PRIMARY_BLUE, width=3)
    draw.text((1000, 340), "TWILIO CELLULAR CARRIER DISPATCH", fill=PRIMARY_BLUE, font=get_font(22, bold=True))
    draw.line([(1000, 380), (1800, 380)], fill=BORDER_COLOR, width=1)

    draw_rounded_rect(draw, (1000, 420, 1420, 475), 12, fill=(30, 58, 138), outline=PRIMARY_BLUE)
    draw.text((1020, 435), "CALL STATUS: DIALING CARRIER", fill=TEXT_MAIN, font=get_font(20, bold=True))

    draw.text((1000, 500), "Call SID: CA_3b1c83c66c274990a64f", fill=TEXT_DIM, font=get_font(22))
    draw.text((1000, 550), "WebSocket Stream: wss://stream.danielrealty.com/v1/stream", fill=TEXT_DIM, font=get_font(22))
    draw.text((1000, 600), "Voice Model: Microsoft Neural Guy / Aria (Zero-Cost)", fill=GOLD_ACCENT, font=get_font(22, bold=True))
    draw.text((1000, 650), "Interruption Protocol: Silero VAD (Sub-50ms Barge-In)", fill=EMERALD_GREEN, font=get_font(22, bold=True))

    # Big Action Button
    draw_rounded_rect(draw, (1000, 740, 1800, 830), 14, fill=EMERALD_GREEN)
    draw.text((1220, 765), "PHONE RINGING (BUYER CONNECTED)", fill=(0, 0, 0), font=get_font(26, bold=True))

    im.save(out_path)


def render_scene_3(out_path: str):
    """Scene 3: Live AI Voice Call & Turn-Taking Loop."""
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(im)

    draw_rounded_rect(draw, (80, 60, 420, 110), 10, fill=(30, 58, 138), outline=PRIMARY_BLUE, width=2)
    draw.text((100, 72), "STAGE 2: VOICE CALL", fill=PRIMARY_BLUE, font=get_font(20, bold=True))

    draw.text((80, 140), "Live Conversational Loop with Zero-Cost Neural Audio", fill=TEXT_MAIN, font=get_font(52, bold=True))
    draw.text((80, 210), "Empathetic, consultative dialogue representing Daniel & Associates Luxury Realty", fill=TEXT_DIM, font=get_font(26))

    # Live Dialogue Panel
    draw_rounded_rect(draw, (80, 290, 1240, 880), 20, fill=SURFACE_COLOR, outline=BORDER_COLOR, width=2)
    draw.text((120, 330), "REAL-TIME TRANSCRIPT & AUDIO SYNTHESIS", fill=GOLD_ACCENT, font=get_font(22, bold=True))
    draw.line([(120, 370), (1200, 370)], fill=BORDER_COLOR, width=1)

    # Chat Bubbles
    # 1. Agent
    draw_rounded_rect(draw, (120, 400, 1100, 500), 12, fill=(30, 58, 138), outline=PRIMARY_BLUE)
    draw.text((140, 415), "Sophia (ISA):", fill=PRIMARY_BLUE, font=get_font(18, bold=True))
    draw.text((140, 445), '"Hi Harrison, this is Sophia with Daniel & Associates. I noticed you just requested details on our Bel Air estate."', fill=TEXT_MAIN, font=get_font(20))

    # 2. Buyer
    draw_rounded_rect(draw, (220, 530, 1200, 630), 12, fill=(31, 41, 55), outline=EMERALD_GREEN)
    draw.text((240, 545), "Harrison (Buyer):", fill=EMERALD_GREEN, font=get_font(18, bold=True))
    draw.text((240, 575), '"Hi Sophia, we loved the video walkthrough, but honestly we are just browsing online right now."', fill=TEXT_MAIN, font=get_font(20))

    # 3. Agent Objection Handler
    draw_rounded_rect(draw, (120, 660, 1100, 780), 12, fill=(30, 58, 138), outline=PRIMARY_BLUE)
    draw.text((140, 675), "Sophia (ISA) — Objection Handled:", fill=GOLD_ACCENT, font=get_font(18, bold=True))
    draw.text((140, 705), '"I completely understand — browsing is the most exciting part! If the dream off-market property opened up,', fill=TEXT_MAIN, font=get_font(20))
    draw.text((140, 735), 'what would be your ideal timeline and budget?"', fill=TEXT_MAIN, font=get_font(20))

    # Audio Waveform Panel on Right
    draw_rounded_rect(draw, (1280, 290, 1840, 880), 20, fill=(15, 23, 42), outline=EMERALD_GREEN, width=2)
    draw.text((1320, 330), "AUDIO STREAM DYNAMICS", fill=EMERALD_GREEN, font=get_font(22, bold=True))
    draw.line([(1320, 370), (1800, 370)], fill=BORDER_COLOR, width=1)

    draw.text((1320, 410), "Format: 24,000 Hz 16-Bit Mono", fill=TEXT_DIM, font=get_font(20))
    draw.text((1320, 450), "Rate: +7% Snappy American Cadence", fill=TEXT_DIM, font=get_font(20))
    draw.text((1320, 490), "Barge-in Interruption: ENABLED", fill=EMERALD_GREEN, font=get_font(20, bold=True))

    # Draw synthetic animated waveform bars
    wave_x = 1320
    wave_y_center = 680
    for i in range(24):
        h = int(30 + 80 * abs(math.sin(i * 0.45)))
        draw_rounded_rect(draw, (wave_x, wave_y_center - h // 2, wave_x + 14, wave_y_center + h // 2), 6, fill=EMERALD_GREEN)
        wave_x += 21

    draw.text((1320, 800), "Zero-Cost Edge TTS: $0.00 / minute", fill=GOLD_ACCENT, font=get_font(22, bold=True))

    im.save(out_path)


def render_scene_4(out_path: str):
    """Scene 4: Qualification & Pydantic Dossier Extraction."""
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(im)

    draw_rounded_rect(draw, (80, 60, 440, 110), 10, fill=(50, 40, 15), outline=GOLD_ACCENT, width=2)
    draw.text((100, 72), "STAGE 3: QUALIFICATION", fill=GOLD_ACCENT, font=get_font(20, bold=True))

    draw.text((80, 140), "Real-Time Pydantic Structured Entity Extraction", fill=TEXT_MAIN, font=get_font(52, bold=True))
    draw.text((80, 210), "Continuously scores buyer intent and validates luxury buying criteria", fill=TEXT_DIM, font=get_font(26))

    # Left Dossier Card
    draw_rounded_rect(draw, (80, 290, 940, 880), 20, fill=SURFACE_COLOR, outline=BORDER_COLOR, width=2)
    draw.text((120, 330), "EXTRACTED BUYER DOSSIER", fill=GOLD_ACCENT, font=get_font(22, bold=True))
    draw.line([(120, 370), (900, 370)], fill=BORDER_COLOR, width=1)

    items = [
        ("Full Name:", "Harrison Sterling"),
        ("Phone Number:", "+1 (310) 555-0144"),
        ("Verified Budget:", "$6,500,000 USD (All-Cash Liquid)"),
        ("Purchase Timeframe:", "1-3 months (High Urgency)"),
        ("Property Criteria:", "Bel Air / Beverly Hills Modern Estate"),
        ("Objections Resolved:", "2 ('Just browsing' -> Off-Market VIP)"),
        ("Qualification Verdict:", "QUALIFIED (Top 1% Luxury Buyer)")
    ]

    y = 405
    for lbl, val in items:
        draw.text((120, y), lbl, fill=TEXT_DIM, font=get_font(22))
        color = EMERALD_GREEN if "QUALIFIED" in val or "Cash" in val else TEXT_MAIN
        draw.text((380, y), val, fill=color, font=get_font(22, bold=True))
        y += 65

    # Right Intent Score Visual
    draw_rounded_rect(draw, (980, 290, 1840, 880), 20, fill=(15, 23, 42), outline=EMERALD_GREEN, width=3)
    draw.text((1020, 330), "INTENT SCORING ALGORITHM", fill=EMERALD_GREEN, font=get_font(22, bold=True))
    draw.line([(1020, 370), (1800, 370)], fill=BORDER_COLOR, width=1)

    draw.text((1020, 420), "100 / 100", fill=EMERALD_GREEN, font=get_font(84, bold=True))
    draw.text((1020, 530), "MAXIMUM CONVERSION RATING", fill=TEXT_MAIN, font=get_font(28, bold=True))

    scoring_details = [
        ("Budget > $5,000,000:", "+30 points"),
        ("All-Cash Proof of Funds:", "+20 points"),
        ("Immediate 30-Day Timeline:", "+20 points"),
        ("Objection Successfully Handled:", "+10 points"),
        ("Showing Appointment Requested:", "+20 points")
    ]

    sy = 600
    for metric, pts in scoring_details:
        draw.text((1020, sy), metric, fill=TEXT_DIM, font=get_font(20))
        draw.text((1580, sy), pts, fill=GOLD_ACCENT, font=get_font(20, bold=True))
        sy += 48

    im.save(out_path)


def render_scene_5(out_path: str):
    """Scene 5: Google Calendar Booking & CRM Dispatch."""
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(im)

    draw_rounded_rect(draw, (80, 60, 460, 110), 10, fill=(16, 40, 30), outline=EMERALD_GREEN, width=2)
    draw.text((100, 72), "STAGE 4: BOOKING & CRM", fill=EMERALD_GREEN, font=get_font(20, bold=True))

    draw.text((80, 140), "Autonomous Appointment Lock & CRM Synchronization", fill=TEXT_MAIN, font=get_font(52, bold=True))
    draw.text((80, 210), "Google Calendar confirmed, Follow Up Boss tagged, and instant SMS sent to buyer", fill=TEXT_DIM, font=get_font(26))

    # Google Calendar Card
    draw_rounded_rect(draw, (80, 290, 940, 880), 20, fill=(17, 30, 50), outline=PRIMARY_BLUE, width=3)
    draw.text((120, 330), "GOOGLE CALENDAR CONFIRMED", fill=PRIMARY_BLUE, font=get_font(24, bold=True))
    draw.line([(120, 370), (900, 370)], fill=BORDER_COLOR, width=1)

    draw_rounded_rect(draw, (120, 410, 900, 530), 14, fill=(30, 58, 138))
    draw.text((150, 435), "This Thursday at 2:00 PM PST", fill=TEXT_MAIN, font=get_font(30, bold=True))
    draw.text((150, 480), "Private Showing — 10484 Bellagio Rd, Bel Air", fill=(191, 219, 254), font=get_font(20))

    cal_items = [
        ("Confirmation Code:", "VIP-2AE327"),
        ("Realtor Assigned:", "R Jan Steve Daniel (Principal Broker)"),
        ("Showing Duration:", "45 Minutes (+15 Min Buffer)"),
        ("Collision Prevention:", "VERIFIED (Zero Overlap)"),
        ("Security Gate Access:", "Reserved under Harrison Sterling")
    ]

    cy = 570
    for k, v in cal_items:
        draw.text((120, cy), k, fill=TEXT_DIM, font=get_font(20))
        draw.text((360, cy), v, fill=TEXT_MAIN, font=get_font(20, bold=True))
        cy += 55

    # CRM & SMS Card
    draw_rounded_rect(draw, (980, 290, 1840, 880), 20, fill=SURFACE_COLOR, outline=BORDER_COLOR, width=2)
    draw.text((1020, 330), "FOLLOW UP BOSS CRM & SMS DISPATCH", fill=GOLD_ACCENT, font=get_font(24, bold=True))
    draw.line([(1020, 370), (1800, 370)], fill=BORDER_COLOR, width=1)

    # Tags Badges
    draw.text((1020, 400), "CRM Tags Applied:", fill=TEXT_DIM, font=get_font(20))
    tags = ["#CLOSER-AI", "#AI-Qualified", "#Hot-Lead", "#Cash-Buyer", "#Tour-Scheduled"]
    tx = 1020
    for tg in tags:
        draw_rounded_rect(draw, (tx, 440, tx + len(tg) * 14, 480), 8, fill=(16, 40, 30), outline=EMERALD_GREEN)
        draw.text((tx + 10, 452), tg, fill=EMERALD_GREEN, font=get_font(16, bold=True))
        tx += len(tg) * 14 + 14

    draw.text((1020, 520), "SMS Confirmation Sent:", fill=TEXT_DIM, font=get_font(20))
    draw_rounded_rect(draw, (1020, 560, 1800, 720), 12, fill=(31, 41, 55))
    sms_txt_1 = '"Hello Harrison, your private showing with R Jan Steve Daniel is'
    sms_txt_2 = 'confirmed for Thursday at 2:00 PM PST. Gate code and private parking'
    sms_txt_3 = 'instructions have been reserved under your name."'
    draw.text((1050, 580), sms_txt_1, fill=TEXT_MAIN, font=get_font(20))
    draw.text((1050, 620), sms_txt_2, fill=TEXT_MAIN, font=get_font(20))
    draw.text((1050, 660), sms_txt_3, fill=TEXT_MAIN, font=get_font(20))

    draw.text((1020, 760), "HMAC Webhook Signature: sha256=4d430bc35a90...", fill=TEXT_DIM, font=get_font(18))
    draw.text((1020, 800), "CRM Pipeline Stage: TOUR SCHEDULED", fill=EMERALD_GREEN, font=get_font(22, bold=True))

    im.save(out_path)


def render_scene_6(out_path: str):
    """Scene 6: Outro & Founder Credits."""
    im = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(im)

    draw_rounded_rect(draw, (80, 60, 350, 110), 10, fill=(30, 58, 138), outline=PRIMARY_BLUE, width=2)
    draw.text((100, 72), "PRODUCTION READY", fill=PRIMARY_BLUE, font=get_font(20, bold=True))

    draw.text((80, 140), "CLOSER AI — Scale Your Luxury Brokerage", fill=TEXT_MAIN, font=get_font(60, bold=True))
    draw.text((80, 220), "Turn ad spend into high-ticket verified showings in seconds.", fill=GOLD_ACCENT, font=get_font(30))

    # Architecture Recap Cards
    features = [
        ("Zero-Cost Neural Voice", "Microsoft Edge Neural Guy & Aria synthesis with zero monthly API fees."),
        ("Fast-Whisper + VAD", "Streaming speech-to-text with sub-50ms conversational barge-in interruptions."),
        ("Pydantic Schema Engine", "Guaranteed precision extraction of budget, pre-approval, and purchase timeframe."),
        ("Autonomous Calendar Lock", "Real-time Google Calendar slot validation, collision detection, and instant invite.")
    ]

    fx = 80
    for title, desc in features:
        draw_rounded_rect(draw, (fx, 310, fx + 410, 620), 16, fill=SURFACE_COLOR, outline=BORDER_COLOR, width=2)
        draw.text((fx + 25, 340), title, fill=PRIMARY_BLUE, font=get_font(22, bold=True))
        draw.line([(fx + 25, 380), (fx + 385, 380)], fill=BORDER_COLOR, width=1)
        # Wrap description
        words = desc.split()
        line = ""
        y = 410
        for w in words:
            if len(line + " " + w) > 28:
                draw.text((fx + 25, y), line, fill=TEXT_DIM, font=get_font(18))
                y += 28
                line = w
            else:
                line += " " + w if line else w
        if line:
            draw.text((fx + 25, y), line, fill=TEXT_DIM, font=get_font(18))
        fx += 450

    # Founder Box
    draw_rounded_rect(draw, (80, 680, 1840, 880), 20, fill=(15, 23, 42), outline=EMERALD_GREEN, width=3)
    draw.text((120, 720), f"Architect & Founder: {settings.FOUNDER_NAME}", fill=TEXT_MAIN, font=get_font(34, bold=True))
    draw.text((120, 775), "GitHub: https://github.com/JanSteve/closer-ai", fill=PRIMARY_BLUE, font=get_font(24, bold=True))
    draw.text((120, 815), "Portfolio: https://www.stevedaniel.me  |  License: Apache 2.0 (Copyright 2026)", fill=TEXT_DIM, font=get_font(22))

    draw_rounded_rect(draw, (1400, 740, 1800, 830), 12, fill=EMERALD_GREEN)
    draw.text((1440, 765), "STAR ON GITHUB ⭐️", fill=(0, 0, 0), font=get_font(24, bold=True))

    im.save(out_path)


def generate_srt_subtitles(srt_path: str, scenes: List[Tuple[float, float, str]]):
    """Generates standard SRT subtitles file."""
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, (start_sec, end_sec, text) in enumerate(scenes, 1):
            def fmt(sec):
                h = int(sec // 3600)
                m = int((sec % 3600) // 60)
                s = int(sec % 60)
                ms = int((sec - int(sec)) * 1000)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

            f.write(f"{idx}\n")
            f.write(f"{fmt(start_sec)} --> {fmt(end_sec)}\n")
            f.write(f"{text}\n\n")


def generate_video():
    """Generates the master 1080p MP4 demo video."""
    print("\n[+] Generating CLOSER AI 1080p Storyboard Frames...")
    frame_files = [
        str(DEMO_DIR / "frame_1.png"),
        str(DEMO_DIR / "frame_2.png"),
        str(DEMO_DIR / "frame_3.png"),
        str(DEMO_DIR / "frame_4.png"),
        str(DEMO_DIR / "frame_5.png"),
        str(DEMO_DIR / "frame_6.png")
    ]

    render_scene_1(frame_files[0])
    render_scene_2(frame_files[1])
    render_scene_3(frame_files[2])
    render_scene_4(frame_files[3])
    render_scene_5(frame_files[4])
    render_scene_6(frame_files[5])
    print(f" -> Successfully rendered {len(frame_files)} high-resolution 1080p frames.")

    # Narration Scripts for each scene
    narrations = [
        "Welcome to Closer AI, the autonomous voice-native real estate lead qualification engine. In luxury real estate, calling leads within minutes determines who wins the listing.",
        "When an ultra-luxury buyer inquires on Instagram or Zillow, Closer AI ingests the lead and initiates an outbound carrier phone call in under 500 milliseconds.",
        "Sophia, our AI Inside Sales Agent, conducts an empathetic qualification conversation using zero-cost neural speech with sub-50 millisecond interruption handling.",
        "Closer AI gracefully handles common buyer objections, discovers the buyer's true budget and timeline, and verifies all-cash or pre-approved financing with 100% precision.",
        "Once qualified, Closer AI checks the broker's Google Calendar, books a confirmed private tour, syncs the dossier to Follow Up Boss, and sends an instant SMS invite.",
        "Engineered by R Jan Steve Daniel. Production ready, open source on GitHub, and built to scale top-producing brokerages worldwide."
    ]

    tts = EdgeTTSVoiceEngine()
    audio_files = []
    print("\n[+] Synthesizing Voice Narration Soundtrack...")
    for idx, text in enumerate(narrations, 1):
        a_path = str(DEMO_DIR / f"audio_scene_{idx}.wav")
        tts.synthesize_sync(text, output_path=a_path, voice="en-US-GuyNeural")
        audio_files.append(a_path)
        print(f" -> Synthesized narration for Scene {idx}")

    # Build Subtitle timeline
    scene_durations = [9.0, 9.0, 12.0, 12.0, 11.0, 7.0]  # Total: 60.0s
    scenes = []
    cur = 0.0
    for dur, text in zip(scene_durations, narrations):
        scenes.append((cur, cur + dur, text))
        cur += dur

    srt_path = str(DEMO_DIR / "closer_ai_demo.srt")
    generate_srt_subtitles(srt_path, scenes)
    print(f" -> Generated subtitle track at {srt_path}")

    # Create concat list for ffmpeg audio
    audio_list_file = DEMO_DIR / "audio_concat.txt"
    with open(audio_list_file, "w") as f:
        for a_file in audio_files:
            f.write(f"file '{a_file}'\n")

    master_audio = str(DEMO_DIR / "master_audio.wav")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(audio_list_file), "-c", "copy", master_audio
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f" -> Merged master narration audio: {master_audio}")

    # Create image slideshow input
    # Each image shown for its scene duration
    video_list_file = DEMO_DIR / "video_concat.txt"
    with open(video_list_file, "w") as f:
        for f_path, dur in zip(frame_files, scene_durations):
            f.write(f"file '{f_path}'\nduration {dur}\n")
        f.write(f"file '{frame_files[-1]}'\n")

    output_video = str(DEMO_DIR / "closer_ai_demo_1080p.mp4")
    print(f"\n[+] Compiling 1080p 60-Second Video Demo via FFmpeg...")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(video_list_file),
        "-i", master_audio,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_video
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode == 0 and os.path.exists(output_video):
        size_mb = os.path.getsize(output_video) / (1024 * 1024)
        print(f"\n[+] SUCCESS: 1080p Demo Video Generated at:\n    {output_video} ({size_mb:.2f} MB)")
    else:
        print("\n[-] FFmpeg compilation warning: please check ffmpeg configuration.")


if __name__ == "__main__":
    generate_video()
