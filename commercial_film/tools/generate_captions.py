#!/usr/bin/env python3
"""generate_captions.py — Generates SRT and WebVTT caption files for CLOSER AI 78s Universal Telecaller Reel.
"""
import os

SUBS = [
    # Scene 0: Universal Need & Agency Excel Trap (0.0s – 10.8s)
    (0.4, 3.0, "Every Single Business"),
    (3.0, 5.5, "Needs Telecallers Today!"),
    (5.5, 8.0, "Clinics · Solar · Agencies · Real Estate"),
    (8.0, 10.6, "Lakhs Wasted On Dead Leads!"),

    # Scene 1: The Angry Prospect Hangup (10.8s – 17.8s)
    (10.8, 13.0, "Human Telecallers Call Hours Late"),
    (13.0, 15.4, "Customer: \"WHO ARE YOU?!\""),
    (15.4, 17.6, "\"I Never Filled Any Form!\" 💥"),

    # Scene 2: 5-Minute Intent Collapse (17.8s – 25.4s)
    (17.8, 20.4, "After 5 Minutes, Intent Collapses"),
    (20.4, 22.8, "Human Telecallers Sleep At Night..."),
    (22.8, 25.2, "...While Ad Budgets Burn 24/7!"),

    # Scene 3: CLOSER AI Hero Reveal (25.4s – 34.2s)
    (25.4, 28.0, "Meet CLOSER AI"),
    (28.0, 30.8, "Autonomous Telecalling For ANY Business"),
    (30.8, 34.0, "Instant Dials In Under 45 Seconds!"),

    # Scene 4A: Maya Luxury Real Estate (34.2s – 42.4s)
    (34.2, 38.0, "Maya: \"Villa Brochure On WhatsApp\""),
    (38.0, 42.2, "\"Sunday 11 AM Site Visit Locked!\""),

    # Scene 4B: Dr. Pallavi Dental Clinic (42.4s – 48.9s)
    (42.4, 45.4, "Pallavi: \"வணக்கம் மேடம்...\""),
    (45.4, 48.7, "\"டென்டல் அப்பாயின்மென்ட் கன்பார்ம்!\""),

    # Scene 4C: Swati Rooftop Solar (48.9s – 55.1s)
    (48.9, 51.8, "Swati: \"5kW सोलर कोटेशन...\""),
    (51.8, 54.9, "\"व्हाट्सएप पर तुरंत भेज दिया है!\""),

    # Scene 5: WhatsApp Instant Delivery (55.1s – 62.3s)
    (55.1, 58.4, "Clinics · Solar · EdTech · Real Estate"),
    (58.4, 62.1, "Drops Quotes & Passes On WhatsApp!"),

    # Scene 6: Unit Economics Showdown (62.3s – 70.4s)
    (62.3, 65.8, "Human Telecaller: ₹220 Per Lead"),
    (65.8, 70.2, "CLOSER AI: ₹1.55 With Zero Payroll!"),

    # Scene 7: Viral Comment Magnet CTA (70.4s – 78.0s)
    (70.4, 73.6, "Run ANY Business Needing Calls?"),
    (73.6, 77.5, "Comment \"CLOSER\" For Free Playbook 👇")
]

def fmt_srt(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    ms = int(round((s - int(s)) * 1000))
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

def fmt_vtt(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    ms = int(round((s - int(s)) * 1000))
    return f"{h:02d}:{m:02d}:{sec:02d}.{ms:03d}"

def generate():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(root)

    # Build SRT
    srt_lines = []
    for idx, (t0, t1, text) in enumerate(SUBS, 1):
        srt_lines.append(f"{idx}")
        srt_lines.append(f"{fmt_srt(t0)} --> {fmt_srt(t1)}")
        srt_lines.append(text)
        srt_lines.append("")

    # Build VTT
    vtt_lines = ["WEBVTT", ""]
    for idx, (t0, t1, text) in enumerate(SUBS, 1):
        vtt_lines.append(f"{fmt_vtt(t0)} --> {fmt_vtt(t1)}")
        vtt_lines.append(text)
        vtt_lines.append("")

    srt_content = "\n".join(srt_lines)
    vtt_content = "\n".join(vtt_lines)

    paths = [
        (os.path.join(root, "closer_reel.srt"), os.path.join(root, "closer_reel.vtt")),
        (os.path.join(project_root, "demos", "closer_reel.srt"), os.path.join(project_root, "demos", "closer_reel.vtt"))
    ]

    for srt_path, vtt_path in paths:
        os.makedirs(os.path.dirname(srt_path), exist_ok=True)
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        with open(vtt_path, "w", encoding="utf-8") as f:
            f.write(vtt_content)
        print(f"Wrote {srt_path} and {vtt_path}")

if __name__ == "__main__":
    generate()
