"""
closer.video.scenarios.agency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
B2B Performance Agency Scenarios: Meta Ads Lead Gen, Client Retention, Appointment Setting.
Addresses the classic 'Agency Excel Trap', client churn from slow telecalling,
and instant lead qualification webhook routing.
"""

from closer.video.scenarios.base import (
    ReelScenario, Sector, ScenarioLine, CharacterRigConfig,
    WhatsAppAsset, FoleyCue, AttireType, ExpressionType, HairStyle
)


def get_meta_ads_lead_trap_scenario() -> ReelScenario:
    """Flagship Agency Scenario: Escaping the Agency Excel Trap."""
    return ReelScenario(
        id="agency_meta_lead_trap_01",
        sector=Sector.AGENCY,
        sub_sector="Performance Marketing & Meta Ads Lead Gen",
        title="Agencies: Escape The 'Dead Leads' Client Blame Game",
        target_persona="Agency Owners, Performance Marketers, Media Buyers, Growth Consultancies",
        target_duration=68.0,
        character_rig_configs=[
            CharacterRigConfig(role="host", name="Narrator", hair_style="fade", attire="blazer", accessories=["headset"]),
            CharacterRigConfig(role="closer_agent", name="Kabir", skin_tone="#D29568", hair_style="fade", attire="turtleneck", accessories=["glasses"], default_expression="confident"),
            CharacterRigConfig(role="customer", name="Frustrated Client", hair_style="parted", attire="blazer", accessories=["phone-right"])
        ],
        opening_hook_lines=[
            ScenarioLine(
                id="ag1_hook",
                speaker="Narrator",
                text="Agency owners: how many high-paying clients did you lose last month because 'the leads were dead'?",
                voice="af_heart",
                speed=1.15,
                screen_tag="AGENCY CLIENT CHURN",
                scene_visual="agency_churn_alert"
            ),
            ScenarioLine(
                id="ag2_trap",
                speaker="Narrator",
                text="You generate 500 great leads on Meta Ads at a stellar cost per lead. But you're trapped in the Agency Excel Nightmare.",
                voice="af_heart",
                speed=1.15,
                screen_tag="AGENCY EXCEL TRAP",
                scene_visual="agency_excel_nightmare"
            )
        ],
        problem_dialogue=[
            ScenarioLine(
                id="ag3_delay",
                speaker="Narrator",
                text="Your client's internal sales team takes three days to open the spreadsheet. By then, the prospect yells: 'Who are you?! I never filled a form!'",
                voice="af_heart",
                speed=1.15,
                screen_tag="3-DAY CALL DELAY",
                scene_visual="yelling_customer_hangup"
            ),
            ScenarioLine(
                id="ag4_blame",
                speaker="Narrator",
                text="The client screams: 'Your leads are complete junk!' and fires your two-lakh monthly retainer on Friday.",
                voice="af_heart",
                speed=1.15,
                screen_tag="FIRED RETAINER",
                scene_visual="slack_fired_retainer"
            )
        ],
        closer_solution_dialogue=[
            ScenarioLine(
                id="ag5_closer",
                speaker="Narrator",
                text="Meet CLOSER AI. The agency retention weapon. It hooks directly into your Meta Lead Ads webhook and dials in forty-five seconds.",
                voice="af_heart",
                speed=1.15,
                screen_tag="WEBHOOK < 45s DIAL",
                scene_visual="closer_hero_reveal"
            ),
            ScenarioLine(
                id="ag6_kabir_call",
                speaker="Kabir",
                text="Hi Vikram! Saw you requested a quote for our commercial packaging machines. I've sent our catalog to your WhatsApp. Does Thursday at 3 PM work for a 15-minute engineering demo?",
                voice="en-IN-PrabhatNeural",
                rate="+10%",
                screen_tag="AGENCY LEAD CLOSER",
                character_id="closer_agent",
                scene_visual="kabir_agency_call"
            ),
            ScenarioLine(
                id="ag7_whatsapp",
                speaker="Narrator",
                text="While on call, it pushes catalogs, audits, and Google Calendar invites straight to WhatsApp, filtering tire-kickers automatically.",
                voice="af_heart",
                speed=1.15,
                screen_tag="CALENDAR BOOKED",
                scene_visual="whatsapp_agency_delivery"
            ),
            ScenarioLine(
                id="ag8_economics",
                speaker="Narrator",
                text="Traditional BPO telecallers: ₹220 per dialed lead. CLOSER AI: one rupee fifty-five paise. 100% client retention.",
                voice="af_heart",
                speed=1.15,
                screen_tag="100% RETENTION",
                scene_visual="unit_economics_showdown"
            )
        ],
        whatsapp_asset_attachment=WhatsAppAsset(
            title="Performance Agency Client Retention Kit - Instant Lead Qualification Playbook.pdf",
            file_type="pdf",
            file_size_display="2.9 MB",
            headline="Performance Agency Client Retention Kit",
            subheadline="Instant Meta Lead Qualification Playbook & CRM Webhook Architecture",
            preview_bullet_points=[
                "Meta Lead Ads Instant Webhook Trigger Blueprint",
                "Automated BANT Qualification Scoring Framework",
                "Google Calendar & HubSpot Auto-Booking Sync"
            ]
        ),
        cta_lines=[
            ScenarioLine(
                id="ag9_cta",
                speaker="Narrator",
                text="If you run a digital marketing, performance, or lead gen agency: comment CLOSER below.",
                voice="af_heart",
                speed=1.12,
                screen_tag="COMMENT 'CLOSER'",
                scene_visual="viral_cta_pointing"
            ),
            ScenarioLine(
                id="ag10_cta2",
                speaker="Narrator",
                text="And I'll send you our Agency Client Retention Automation Playbook for free.",
                voice="af_heart",
                speed=1.12,
                screen_tag="GET FREE PLAYBOOK",
                scene_visual="viral_cta_pointing"
            )
        ],
        foley_cues=[
            FoleyCue(0.0, "whoosh_hit", 0.85, "Intro transition"),
            FoleyCue(0.4, "alert_ping", 0.5, "Meta lead notification"),
            FoleyCue(10.8, "whoosh_hit", 0.65, "Cut to client phone delay"),
            FoleyCue(15.6, "hangup_click", 0.85, "Customer hangup slam"),
            FoleyCue(23.0, "whoosh_hit", 0.7, "Cut to CLOSER AI reveal"),
            FoleyCue(23.1, "sub_drop", 0.95, "Bass drop on hero engine"),
            FoleyCue(34.0, "alert_ping", 0.4, "Kabir agency call chime"),
            FoleyCue(44.0, "whatsapp_pop", 0.85, "WhatsApp booking pop"),
            FoleyCue(52.5, "coin_clink", 0.7, "Coin jackpot clinking"),
            FoleyCue(53.0, "sub_drop", 0.9, "Bass drop on ₹1.55"),
            FoleyCue(60.4, "comment_chime", 0.85, "Comment chime sparkle")
        ],
        caption_template=(
            "Performance Marketing Agencies: Stop letting clients fire you because 'the leads were low quality'! 📈\n\n"
            "You deliver 500 great leads from Meta and Google Ads. But your client's sales team waits 3 days to call them. "
            "By then, prospects have forgotten the ad, hang up angry, and your client cancels your retainer.\n\n"
            "CLOSER AI dials the second a lead hits your webhook:\n"
            "⚡ Calls in < 45 seconds while the buyer is still holding their phone\n"
            "⚡ Qualifies budget, urgency, and decision-making authority\n"
            "⚡ Dispatches brochures, proposals, and WhatsApp meeting confirmations\n"
            "⚡ Drops qualified appointments directly into your client's Google Calendar\n"
            "💰 At ₹1.55 per call, making your agency 100% indispensable.\n\n"
            "👇 Comment '{CTA_KEYWORD}' below and I'll send you our Agency Client Retention Kit!\n\n"
            "#digitalmarketing #marketingagency #metaads #leadgeneration #agencygrowth #closerai #salesautomation"
        )
    )


def get_b2b_appointments_scenario() -> ReelScenario:
    """Alternate Agency Scenario: B2B High-Ticket Appointment Setting."""
    return ReelScenario(
        id="agency_b2b_appointments_02",
        sector=Sector.AGENCY,
        sub_sector="B2B Appointment Setting & High-Ticket SaaS",
        title="B2B Agencies: Autonomous Inbound Lead Qualification to Calendar",
        target_persona="B2B Agency Founders, RevOps Directors, Outbound SDR Leads",
        target_duration=68.0,
        character_rig_configs=[
            CharacterRigConfig(role="host", name="Narrator", attire="blazer", accessories=["headset"]),
            CharacterRigConfig(role="closer_agent", name="Sameer", attire="blazer", accessories=["glasses"]),
            CharacterRigConfig(role="customer", name="Enterprise Buyer", attire="blazer", accessories=["phone-right"])
        ],
        opening_hook_lines=[
            ScenarioLine(id="b2b1_hook", speaker="Narrator", text="B2B agencies: inbound demo requests from enterprise buyers are sitting in your CRM for twenty-four hours.", voice="af_heart", speed=1.15, screen_tag="24H DEMO DELAY"),
            ScenarioLine(id="b2b2_loss", speaker="Narrator", text="While your SDRs research LinkedIn profiles, the VP of Sales books a demo with your competitor.", voice="af_heart", speed=1.15, screen_tag="COMPETITOR DEMO")
        ],
        problem_dialogue=[
            ScenarioLine(id="b2b3_burnout", speaker="Narrator", text="Junior SDRs burn out doing 80 cold dials a day with a 2% pickup rate. Payroll bleeding ₹1.5 Lakhs per SDR.", voice="af_heart", speed=1.15, screen_tag="SDR PAYROLL DRAIN"),
            ScenarioLine(id="b2b4_ghost", speaker="Narrator", text="When they finally connect, the prospect says: 'Send an email', and disappears into the void.", voice="af_heart", speed=1.15, screen_tag="GHOSTED PROSPECT")
        ],
        closer_solution_dialogue=[
            ScenarioLine(id="b2b5_closer", speaker="Narrator", text="CLOSER AI connects via carrier SIP in sub-250ms latency, qualifying company headcount and budget.", voice="af_heart", speed=1.15, screen_tag="SUB-250ms SIP"),
            ScenarioLine(id="b2b6_sameer", speaker="Sameer", text="Hello Ankit! Regarding your enterprise telemetry inquiry: we've sent our SOC-2 report and pricing tiers to your WhatsApp. Does Friday at 11 AM work for a live architecture review with our CTO?", voice="en-IN-PrabhatNeural", rate="+10%", screen_tag="B2B QUALIFIER", character_id="closer_agent"),
            ScenarioLine(id="b2b7_wa", speaker="Narrator", text="Drops security audits, pricing matrices, and calendar invite links to WhatsApp instantly.", voice="af_heart", speed=1.15, screen_tag="WHATSAPP AUDIT SYNC"),
            ScenarioLine(id="b2b8_cost", speaker="Narrator", text="Qualified enterprise meetings on your calendar. ₹1.55 per call. Zero SDR churn.", voice="af_heart", speed=1.15, screen_tag="ZERO SDR CHURN")
        ],
        whatsapp_asset_attachment=WhatsAppAsset(
            title="Enterprise B2B Qualification Framework & SOC-2 Audit Pack.pdf",
            file_type="dossier",
            file_size_display="4.5 MB",
            headline="Enterprise Inbound Qualification Pack",
            subheadline="SOC-2 Type II Compliance & Cal.com Scheduling Bridge",
            preview_bullet_points=["Enterprise Pricing Tiers", "CTO Architecture Review Gate Pass", "Security Whitepaper"]
        ),
        cta_lines=[
            ScenarioLine(id="b2b9_cta", speaker="Narrator", text="If you run a B2B agency or SaaS sales team: comment CLOSER below.", voice="af_heart", speed=1.12, screen_tag="COMMENT 'CLOSER'"),
            ScenarioLine(id="b2b10_cta2", speaker="Narrator", text="And I'll send you our B2B Inbound Qualification Playbook.", voice="af_heart", speed=1.12, screen_tag="B2B PLAYBOOK")
        ],
        foley_cues=[
            FoleyCue(0.0, "whoosh_hit", 0.85, "Intro"),
            FoleyCue(0.4, "alert_ping", 0.5, "Demo request ping"),
            FoleyCue(20.0, "sub_drop", 0.95, "Hero drop"),
            FoleyCue(40.0, "whatsapp_pop", 0.85, "Audit pack pop"),
            FoleyCue(52.0, "sub_drop", 0.85, "₹1.55 drop"),
            FoleyCue(60.0, "comment_chime", 0.85, "Comment chime")
        ],
        caption_template=(
            "B2B Agency Founders & Sales VPs: Stop letting inbound enterprise leads go cold in your CRM! 💼\n\n"
            "Enterprise buyers evaluate software when they are at their desks. "
            "CLOSER AI calls inbound demo requests in 45 seconds, qualifies BANT criteria, and books confirmed slots on your AE's calendar.\n\n"
            "👇 Comment '{CTA_KEYWORD}' for our B2B Inbound Telecalling Blueprint!\n\n"
            "#b2bsales #appointmentsetting #leadqualification #saassales #closerai"
        )
    )
