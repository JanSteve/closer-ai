"""Generate an institutional, non-AI-slop pitch deck PDF for CLOSER AI."""

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas

# 16:9 Widescreen Presentation Canvas: 960 x 540 points
PAGE_WIDTH = 960
PAGE_HEIGHT = 540

BG_COLOR = colors.HexColor("#0A0E17")       # Deep Luxury Obsidian
CARD_BG = colors.HexColor("#121826")        # Elevated Slate Card
CARD_BORDER = colors.HexColor("#1E293B")    # Subtle Border
TEXT_PRIMARY = colors.HexColor("#F8FAFC")   # Crisp Off-White
TEXT_MUTED = colors.HexColor("#94A3B8")     # Clean Muted Slate
ACCENT_GOLD = colors.HexColor("#D4AF37")    # Luxury Gold
ACCENT_BLUE = colors.HexColor("#38BDF8")    # Electric Cyan
ACCENT_GREEN = colors.HexColor("#22C55E")   # Success Emerald
CARD_INNER = colors.HexColor("#182234")


def draw_background(c):
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=True, stroke=False)
    # Subtle top accent bar
    c.setFillColor(ACCENT_GOLD)
    c.rect(0, PAGE_HEIGHT - 3, PAGE_WIDTH, 3, fill=True, stroke=False)


def draw_footer(c, current_slide, total_slides=6):
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(TEXT_MUTED)
    c.drawString(48, 24, "CLOSER AI — Confidential Investor Deck")
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_WIDTH - 48, 24, f"{current_slide} / {total_slides}")


def draw_card(c, x, y, w, h, title=None, fill=CARD_BG, stroke=CARD_BORDER):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 6, fill=True, stroke=True)
    if title:
        c.setFont("Helvetica-Bold", 13)
        c.setFillColor(TEXT_PRIMARY)
        c.drawString(x + 18, y + h - 28, title)


def make_deck(output_path):
    c = canvas.Canvas(output_path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    # =========================================================================
    # SLIDE 1: COVER
    # =========================================================================
    draw_background(c)

    # Category Pill
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setStrokeColor(ACCENT_GOLD)
    c.setLineWidth(1)
    c.roundRect(48, 430, 220, 26, 4, fill=True, stroke=True)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(60, 438, "AUTONOMOUS VOICE ENGINE")

    # Brand Title
    c.setFont("Helvetica-Bold", 52)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(48, 355, "CLOSER AI")

    # One-liner
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(ACCENT_BLUE)
    c.drawString(48, 310, "Speed-to-Lead Qualification & Calendar Booking Protocol")

    c.setFont("Helvetica", 14)
    c.setFillColor(TEXT_MUTED)
    c.drawString(48, 275, "Dials high-ticket inbound leads within 45 seconds.")
    c.drawString(48, 252, "Zero price hallucinations. Mathematically locks verified walkthroughs on broker calendars.")

    # 3 Stat Highlights
    draw_card(c, 48, 90, 260, 110)
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(68, 155, "< 45 Seconds")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(68, 130, "Autonomous Inbound Call Time")
    c.drawString(68, 114, "(vs 4-6 hr human industry avg)")

    draw_card(c, 328, 90, 260, 110)
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(ACCENT_BLUE)
    c.drawString(348, 155, "Dual-Channel")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(348, 130, "Live Phone Call + Real-Time")
    c.drawString(348, 114, "WhatsApp Visual Co-Browsing")

    draw_card(c, 608, 90, 304, 110)
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(ACCENT_GREEN)
    c.drawString(628, 155, "147 Tests / 0 Halluc.")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(628, 130, "Pydantic v2 Deflection Protocol")
    c.drawString(628, 114, "Multi-Timezone Interval Mutex")

    draw_footer(c, 1)
    c.showPage()

    # =========================================================================
    # SLIDE 2: THE PROBLEM
    # =========================================================================
    draw_background(c)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(48, 480, "THE ₹100M BLEEDING NECK")

    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(48, 442, "High-Ticket Leads Die in Minutes. Human Teams Call Too Late.")

    # 3 Problem Cards
    col_w = 272
    draw_card(c, 48, 190, col_w, 220, "1. The 5-Minute Cliff")
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(colors.HexColor("#EF4444"))
    c.drawString(68, 335, "78%")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(68, 305, "of high-ticket buyers purchase from")
    c.drawString(68, 290, "the first company that calls them back.")
    c.drawString(68, 265, "MIT & InsideSales studies show lead")
    c.drawString(68, 250, "qualification probability drops 100x")
    c.drawString(68, 235, "after just 30 minutes of delay.")

    draw_card(c, 344, 190, col_w, 220, "2. Human Telecaller Failure")
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.drawString(364, 335, "4 to 6 Hours")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(364, 305, "Average response time in Indian and")
    c.drawString(364, 290, "Gulf luxury real estate brokerages.")
    c.drawString(364, 265, "Telecaller monthly churn exceeds 40%.")
    c.drawString(364, 250, "Evening inquiries (8 PM - 11 PM) are")
    c.drawString(364, 235, "abandoned until the next afternoon.")

    draw_card(c, 640, 190, col_w, 220, "3. Existing AI Voice Bots Fail")
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(colors.HexColor("#A855F7"))
    c.drawString(660, 335, "Hallucinations")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(660, 305, "Generic LLMs (Air.ai, Bland) invent")
    c.drawString(660, 290, "discounts and misquote floor rates,")
    c.drawString(660, 275, "creating direct legal/RERA liability.")
    c.drawString(660, 250, "They charge per minute and fail on")
    c.drawString(660, 235, "Crores, Lakhs, and regional cadence.")

    # Ground truth quote card
    draw_card(c, 48, 65, 864, 105, fill=CARD_INNER)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(68, 140, "GROUND TRUTH INSIGHT (JSM INTEGRATED SERVICES, CHENNAI):")
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(68, 118, "\"My family operates JSM, serving luxury property developers. Builders spend ₹50,000 to ₹5,00,000 monthly on Meta & Google ads,")
    c.drawString(68, 100, "only for 70% of high-intent leads to vanish into thin air because sales teams don't call back in time. The market doesn't need")
    c.drawString(68, 82, "another generic chatbot—it needs an autonomous gatekeeper that puts verified buyers directly in the developer's calendar.\"")

    draw_footer(c, 2)
    c.showPage()

    # =========================================================================
    # SLIDE 3: THE SOLUTION & MOAT
    # =========================================================================
    draw_background(c)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(48, 480, "THE UNFAIR ADVANTAGE")

    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(48, 442, "CLOSER AI: Dual-Channel Speed-to-Walkthrough Engine")

    draw_card(c, 48, 250, 416, 170, "1. Sub-45s Inbound Callback")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(68, 365, "• Dials form submissions within 45 seconds while buyer intent is peak.")
    c.drawString(68, 345, "• Low-latency neural synthesis (<150ms dead-air filler bridge).")
    c.drawString(68, 325, "• Native comprehension of ₹ Crores, Lakhs, AED, and USD brackets.")
    c.drawString(68, 305, "• 15-word turn clamps ensure crisp conversational dialogues.")

    draw_card(c, 496, 250, 416, 170, "2. Live WhatsApp Co-Browsing")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(516, 365, "• Voice alone doesn't close $2M deals. Buyers need visual proof.")
    c.drawString(516, 345, "• While talking, AI pushes interactive floor plans, RERA approvals,")
    c.drawString(516, 325, "  and walkthrough slot cards directly into the buyer's WhatsApp.")
    c.drawString(516, 305, "• Zero competitors offer synchronized live voice + WhatsApp flows.")

    draw_card(c, 48, 60, 416, 170, "3. Zero-Hallucination Deflection")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(68, 175, "• AI is strictly forbidden from quoting unverified prices or discounts.")
    c.drawString(68, 155, "• Deterministic deflection protocol redirects pricing queries to the")
    c.drawString(68, 135, "  in-person site walkthrough with the master inventory broker.")
    c.drawString(68, 115, "• Eliminates RERA regulatory and commercial liability 100%.")

    draw_card(c, 496, 60, 416, 170, "4. Conflict-Free Multi-Timezone Sync")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(516, 175, "• Mathematical interval collision engine: [S1, E1) ∩ [S2, E2) = ∅.")
    c.drawString(516, 155, "• Multi-timezone normalization: Asia/Kolkata (+5:30), Asia/Dubai")
    c.drawString(516, 135, "  (+4:00), and US PST/EST aligned seamlessly to UTC.")
    c.drawString(516, 115, "• Mutex-serialized slot locking prevents double-booking across brokers.")

    draw_footer(c, 3)
    c.showPage()

    # =========================================================================
    # SLIDE 4: ARCHITECTURE & CODE VERIFICATION
    # =========================================================================
    draw_background(c)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(48, 480, "TECHNICAL RIGOR & RESILIENCE")

    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(48, 442, "Built for Production. Verified by 147 Automated Tests.")

    # Big Metric Banner
    draw_card(c, 48, 340, 864, 80, fill=CARD_INNER)
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(ACCENT_GREEN)
    c.drawString(68, 385, "147 / 147 Unit, Integration & Stress Tests Passing (4.7s)")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(68, 360, "Zero failures • Zero errors • Zero mocks • Strict SQLite WAL-mode concurrency under 50 simultaneous lead storms")

    # 4 Architecture Pillars
    col_w = 204
    draw_card(c, 48, 65, col_w, 255, "Call FSM Engine")
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ACCENT_BLUE)
    c.drawString(64, 260, "closer/core/call_session.py")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(64, 235, "• 9-State Finite Machine:")
    c.drawString(64, 220, "  IDLE → CONNECTED →")
    c.drawString(64, 205, "  QUALIFYING → SCHEDULING")
    c.drawString(64, 190, "  → COMPLETED → TEARDOWN")
    c.drawString(64, 170, "• Idempotent transitions")
    c.drawString(64, 155, "• Shielded teardown on")
    c.drawString(64, 140, "  abrupt socket hangup")
    c.drawString(64, 120, "• Tested: 16/16 OK")

    draw_card(c, 268, 65, col_w, 255, "Audio Resampling")
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ACCENT_BLUE)
    c.drawString(284, 260, "closer/audio/pipeline.py")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(284, 235, "• Polyphase filter resampler")
    c.drawString(284, 220, "  (scipy.signal.resample_poly)")
    c.drawString(284, 205, "  8k ↔ 16k STT ↔ 48k TTS")
    c.drawString(284, 185, "• BoundedAudioQueue with")
    c.drawString(284, 170, "  drop-oldest eviction")
    c.drawString(284, 155, "• 10,000 frames tested with")
    c.drawString(284, 140, "  zero memory leak")
    c.drawString(284, 120, "• Tested: 37/37 OK")

    draw_card(c, 488, 65, col_w, 255, "Pydantic Extractor")
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ACCENT_BLUE)
    c.drawString(504, 260, "closer/qualification/extractor.py")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(504, 235, "• Deterministic extraction:")
    c.drawString(504, 220, "  Budget, Timeline, Persona,")
    c.drawString(504, 205, "  Mortgage pre-approval")
    c.drawString(504, 185, "• INR Crores/Lakhs & AED")
    c.drawString(504, 170, "• Zero-crash fallback flags")
    c.drawString(504, 155, "  human review on noise")
    c.drawString(504, 140, "• ReDoS-resistant parsing")
    c.drawString(504, 120, "• Tested: 26/26 OK")

    draw_card(c, 708, 65, col_w, 255, "Calendar Sync")
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ACCENT_BLUE)
    c.drawString(724, 260, "closer/scheduling/calendar_sync.py")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(724, 235, "• Interval collision math")
    c.drawString(724, 220, "• Timezone normalization:")
    c.drawString(724, 205, "  IST, GST, PST/EST → UTC")
    c.drawString(724, 185, "• Mutex-serialized slots")
    c.drawString(724, 170, "• 50-task simultaneous storm")
    c.drawString(724, 155, "  tested: exactly 1 confirms,")
    c.drawString(724, 140, "  49 rejected gracefully")
    c.drawString(724, 120, "• Tested: 25/25 OK")

    draw_footer(c, 4)
    c.showPage()

    # =========================================================================
    # SLIDE 5: BUSINESS MODEL & MARKET OPPORTUNITY
    # =========================================================================
    draw_background(c)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(48, 480, "COMMERCIAL MODEL & UNIT ECONOMICS")

    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(48, 442, "B2B SaaS with 80%+ Gross Margins")

    # Left: Pricing Tiers
    draw_card(c, 48, 170, 416, 250, "B2B Subscription & Performance Model")
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(68, 350, "₹25,000 / month (~$300)")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(68, 330, "SMB Tier: Up to 300 lead callbacks, calendar sync, WhatsApp bridge")

    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(ACCENT_BLUE)
    c.drawString(68, 285, "₹75,000 – ₹1,50,000 / month (~$900 - $1,800)")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(68, 265, "Enterprise Tier: Multi-project developers, CRM custom webhooks, SLAs")

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(ACCENT_GREEN)
    c.drawString(68, 220, "Unit Economics:")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(68, 200, "• Average telephony & speech cost to serve: ~₹5,000 / client / month")
    c.drawString(68, 185, "• Estimated Gross Margin: > 80%")

    # Right: Market Potential
    draw_card(c, 496, 170, 416, 250, "Market Opportunity & Scalability")
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(516, 350, "₹30 Crore ARR")
    c.setFont("Helvetica", 12)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(516, 330, "($3.5M+ ARR at 1,000 SMB Real Estate Clients)")

    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(516, 290, "• Beachhead: Luxury Real Estate developers in Chennai, Mumbai, & Dubai")
    c.drawString(516, 270, "• ₹1.5 Crore ARR ($175K) achievable within 12 months with 50 clients")
    c.drawString(516, 250, "• Expansion Verticals: High-ticket elective surgery clinics (IVF, cosmetic),")
    c.drawString(516, 235, "  B2B premium services, and private wealth investment syndicates")
    c.drawString(516, 215, "• Geographic Expansion: India → UAE/Gulf (AED) → US Commercial Brokerages")

    # Bottom Banner
    draw_card(c, 48, 65, 864, 85, fill=CARD_INNER)
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(68, 115, "WHY BROKERS LOVE THIS VALUE PROPOSITION:")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(68, 95, "A single closed luxury apartment in Chennai or Gurgaon pays ₹3 Lakhs to ₹15 Lakhs in commission.")
    c.drawString(68, 77, "If CLOSER AI rescues just ONE lost lead every two months, the customer achieves an immediate 10x ROI on software spend.")

    draw_footer(c, 5)
    c.showPage()

    # =========================================================================
    # SLIDE 6: FOUNDER & ROADMAP
    # =========================================================================
    draw_background(c)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(48, 480, "TEAM & EXECUTION ROADMAP")

    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(48, 442, "Solo Technical Velocity & Immediate GTM Pilots")

    # Founder Card
    draw_card(c, 48, 175, 416, 245, "Founder & Solo Architect")
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(68, 355, "R Jan Steve Daniel")
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(68, 335, "Sole Technical Founder / CEO & CTO | Chennai, India")

    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(68, 305, "• 100% Solo Engineering: Designed and coded CLOSER AI's FSM,")
    c.drawString(68, 290, "  resamplers, extractor, and 147-test automated verification suite.")
    c.drawString(68, 270, "• Proven Systems Depth: Built ARGUS (14 Rust crates, Landlock LSM")
    c.drawString(68, 255, "  Linux kernel security sandbox, cgroups v2, 136 E2E tests).")
    c.drawString(68, 235, "• Domain Access: Direct access to real estate developers via family")
    c.drawString(68, 220, "  enterprise JSM Integrated Services in Chennai.")
    c.drawString(68, 200, "• Looking for: Enterprise B2B Sales Co-founder to scale customer acquisition.")

    # Roadmap Card
    draw_card(c, 496, 175, 416, 245, "Execution Milestones")
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(ACCENT_GREEN)
    c.drawString(516, 355, "[✓] Q3 2026: Core Engine & Testing Complete")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(536, 340, "147 automated unit/integration tests passing. FSM, queues, & extractor verified.")

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(ACCENT_BLUE)
    c.drawString(516, 310, "[→] Q4 2026: Telephony Hookup & Live Chennai Pilots")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(536, 295, "Twilio / Exotel webhooks live. 2-3 pilot clients via JSM running live calls.")

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(516, 265, "[→] Q1 2027: Dubai Chamber Championship & Gulf Expansion")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(536, 250, "Dubai Chamber Create AI Agents submission; launch UAE luxury broker pilot.")

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(516, 220, "[→] Q2 2027: Scale to 50 Paying Clients (₹1.5Cr ARR)")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(536, 205, "Onboard enterprise sales co-founder, expand across Chennai & Mumbai.")

    # Contact Bar
    draw_card(c, 48, 65, 864, 85, fill=CARD_INNER)
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(ACCENT_GOLD)
    c.drawString(68, 115, "CONTACT & DEMO REPOSITORY:")
    c.setFont("Helvetica", 11)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(68, 95, "Website: https://closer-ai-tawny.vercel.app/  •  GitHub: https://github.com/JanSteve/closer-ai")
    c.drawString(68, 77, "Founder: R Jan Steve Daniel (Chennai, India)  •  Open for Antler Pre-Seed Cohort")

    draw_footer(c, 6)
    c.showPage()

    c.save()
    print(f"Deck generated successfully at: {output_path}")


if __name__ == "__main__":
    out = os.path.expanduser("~/Downloads/CLOSER_AI_Pitch_Deck.pdf")
    make_deck(out)
