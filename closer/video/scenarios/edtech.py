"""
closer.video.scenarios.edtech
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
EdTech & Higher Education Scenarios: Executive AI Bootcamps, 0% EMI Financing, Study Abroad.
Addresses brochure drop-offs, aggressive BPO telecalling burnout,
and consultative academic advising with instant curriculum WhatsApp drops.
"""

from closer.video.scenarios.base import (
    ReelScenario, Sector, ScenarioLine, CharacterRigConfig,
    WhatsAppAsset, FoleyCue, AttireType, ExpressionType, HairStyle
)


def get_ai_bootcamp_scenario() -> ReelScenario:
    """Flagship EdTech Scenario: Executive AI & Data Science Bootcamps."""
    return ReelScenario(
        id="edtech_ai_bootcamp_01",
        sector=Sector.EDTECH,
        sub_sector="Generative AI & Tech Career Bootcamps",
        title="EdTech: Stop Burning ₹1,200 CPL on Unresponsive Leads",
        target_persona="EdTech Founders, Admissions Heads, Bootcamp Growth Leaders",
        target_duration=68.0,
        character_rig_configs=[
            CharacterRigConfig(role="host", name="Narrator", hair_style="fade", attire="blazer", accessories=["headset"]),
            CharacterRigConfig(role="counselor", name="Rohan", skin_tone="#C68642", hair_style="parted", attire="smart_casual", accessories=["glasses", "lanyard"], default_expression="smiling"),
            CharacterRigConfig(role="customer", name="Tech Professional", hair_style="messy", attire="polo", accessories=["phone-right"])
        ],
        opening_hook_lines=[
            ScenarioLine(
                id="ed1_hook",
                speaker="Narrator",
                text="EdTech founders: why is your cost per acquisition doubling every single quarter?",
                voice="af_heart",
                speed=1.15,
                screen_tag="CAC CRISIS IN EDTECH",
                scene_visual="edtech_cac_chart"
            ),
            ScenarioLine(
                id="ed2_cpl",
                speaker="Narrator",
                text="You spend ₹1,200 per lead on LinkedIn and Meta. But your telecallers call two days late with scripted hard-sells.",
                voice="af_heart",
                speed=1.15,
                screen_tag="₹1,200 CPL WASTED",
                scene_visual="call_center_hard_sell"
            )
        ],
        problem_dialogue=[
            ScenarioLine(
                id="ed3_spam",
                speaker="Narrator",
                text="The prospective student is in an office meeting. Your call gets flagged as telemarketer spam and blocked forever.",
                voice="af_heart",
                speed=1.15,
                screen_tag="BLOCKED AS SPAM",
                scene_visual="truecaller_spam_block"
            ),
            ScenarioLine(
                id="ed4_drain",
                speaker="Narrator",
                text="Lakhs in monthly ad budget flushed because human call centers can't deliver consultative career guidance.",
                voice="af_heart",
                speed=1.15,
                screen_tag="AD BUDGET FLUSH",
                scene_visual="ad_budget_drain"
            )
        ],
        closer_solution_dialogue=[
            ScenarioLine(
                id="ed5_closer",
                speaker="Narrator",
                text="Meet CLOSER AI. The consultative academic counselor. Within forty-five seconds of a brochure download, Rohan calls.",
                voice="af_heart",
                speed=1.15,
                screen_tag="CONSULTATIVE AI DIAL",
                scene_visual="closer_hero_reveal"
            ),
            ScenarioLine(
                id="ed6_rohan_call",
                speaker="Rohan",
                text="Hello Karthik! Noticed you were exploring the Generative AI Executive Program. I just dropped the syllabus and 0% EMI schedule to your WhatsApp. Tomorrow 6 PM counselor slot confirmed.",
                voice="en-IN-PrabhatNeural",
                rate="+10%",
                screen_tag="COUNSELOR ROHAN",
                character_id="counselor",
                scene_visual="rohan_counseling_call"
            ),
            ScenarioLine(
                id="ed7_whatsapp",
                speaker="Narrator",
                text="Pushes the complete 16-week curriculum, alumni placement reports, and demo class link directly to WhatsApp during the conversation.",
                voice="af_heart",
                speed=1.15,
                screen_tag="WHATSAPP SYLLABUS SYNC",
                scene_visual="whatsapp_edtech_delivery"
            ),
            ScenarioLine(
                id="ed8_economics",
                speaker="Narrator",
                text="Outsourced BPO telecalling benches: ₹220 per connection. CLOSER AI: one rupee fifty-five paise per qualified enrollment.",
                voice="af_heart",
                speed=1.15,
                screen_tag="₹1.55 PER ENROLLMENT",
                scene_visual="unit_economics_showdown"
            )
        ],
        whatsapp_asset_attachment=WhatsAppAsset(
            title="Generative AI Executive Bootcamp - Curriculum & 0% EMI Guide.pdf",
            file_type="pdf",
            file_size_display="3.8 MB",
            headline="Generative AI Executive Program Dossier",
            subheadline="16-Week Weekend Curriculum + 0% EMI Installment Schedule",
            preview_bullet_points=[
                "Hands-On LLM & Multi-Agent Architecture Projects",
                "₹5,500/Month No-Cost EMI Breakdown",
                "Saturday Live Masterclass Pass with Tech VP"
            ]
        ),
        cta_lines=[
            ScenarioLine(
                id="ed9_cta",
                speaker="Narrator",
                text="If you run an EdTech platform, bootcamp, or university: comment CLOSER below.",
                voice="af_heart",
                speed=1.12,
                screen_tag="COMMENT 'CLOSER'",
                scene_visual="viral_cta_pointing"
            ),
            ScenarioLine(
                id="ed10_cta2",
                speaker="Narrator",
                text="And I'll DM you our EdTech Lead-to-Enrollment AI Telecalling Blueprint.",
                voice="af_heart",
                speed=1.12,
                screen_tag="EDTECH BLUEPRINT",
                scene_visual="viral_cta_pointing"
            )
        ],
        foley_cues=[
            FoleyCue(0.0, "whoosh_hit", 0.85, "Intro"),
            FoleyCue(0.4, "alert_ping", 0.5, "Brochure download ping"),
            FoleyCue(11.5, "hangup_click", 0.85, "Spam block sound"),
            FoleyCue(22.0, "whoosh_hit", 0.7, "Hero reveal"),
            FoleyCue(22.1, "sub_drop", 0.95, "Hero sub-bass drop"),
            FoleyCue(33.0, "alert_ping", 0.4, "Rohan counselor tone"),
            FoleyCue(44.0, "whatsapp_pop", 0.85, "Syllabus WhatsApp pop"),
            FoleyCue(52.0, "sub_drop", 0.85, "Bass drop on ₹1.55"),
            FoleyCue(60.0, "comment_chime", 0.85, "Comment chime")
        ],
        caption_template=(
            "EdTech Founders & Growth Leaders: Why are your prospective students blocking your telecallers? 🎓\n\n"
            "Tech professionals downloading course brochures hate robotic hard-sells. "
            "If your BPO calls 48 hours late with pushy scripts, your ₹1,200 CPL is wasted.\n\n"
            "CLOSER AI acts as a consultative admissions advisor in 45 seconds:\n"
            "📘 Answers syllabus & prerequisite questions intelligently\n"
            "📘 Clarifies 0% interest EMI options & weekend timings\n"
            "📘 Drops complete curriculum PDFs & alumni placement reports to WhatsApp\n"
            "📘 Books warm 1-on-1 counselor slots on your team's calendar\n"
            "💰 All at ₹1.55 per call instead of ₹220 BPO telecalling benches.\n\n"
            "👇 Comment '{CTA_KEYWORD}' below and I'll send you our EdTech Inbound Enrollment Playbook!\n\n"
            "#edtech #upskilling #datascience #generativeai #admissions #closerai #salesautomation"
        )
    )


def get_study_abroad_scenario() -> ReelScenario:
    """Alternate EdTech Scenario: Study Abroad & Overseas Admissions."""
    return ReelScenario(
        id="edtech_study_abroad_02",
        sector=Sector.EDTECH,
        sub_sector="Overseas Education & Admissions Counseling",
        title="Study Abroad: Instant IELTS & Visa Eligibility Qualification",
        target_persona="Study Abroad Consultants, Overseas Education Agents, University Reps",
        target_duration=68.0,
        character_rig_configs=[
            CharacterRigConfig(role="host", name="Narrator", attire="blazer", accessories=["headset"]),
            CharacterRigConfig(role="counselor", name="Ananya", attire="smart_casual", accessories=["glasses"]),
            CharacterRigConfig(role="customer", name="Student", attire="polo", accessories=["phone-right"])
        ],
        opening_hook_lines=[
            ScenarioLine(id="ab1_hook", speaker="Narrator", text="Study abroad consultants: thousands of students fill forms for Fall 2027 intake, but 70% have low GPAs or no visa funds.", voice="af_heart", speed=1.15, screen_tag="UNQUALIFIED LEADS"),
            ScenarioLine(id="ab2_waste", speaker="Narrator", text="Your premium counselors spend entire afternoons manually filtering students instead of closing high-value enrollments.", voice="af_heart", speed=1.15, screen_tag="COUNSELOR BURNOUT")
        ],
        problem_dialogue=[
            ScenarioLine(id="ab3_slow", speaker="Narrator", text="High-intent candidates with 8.5 CGPA get tired of waiting and sign up with IDP or Leap Scholar.", voice="af_heart", speed=1.15, screen_tag="LOST TOP STUDENTS"),
            ScenarioLine(id="ab4_drop", speaker="Narrator", text="By the time your agency schedules a diagnostic test, the admission deadline window has closed.", voice="af_heart", speed=1.15, screen_tag="MISSED DEADLINES")
        ],
        closer_solution_dialogue=[
            ScenarioLine(id="ab5_closer", speaker="Narrator", text="CLOSER AI filters country preferences, IELTS scores, and tuition budgets in forty-five seconds.", voice="af_heart", speed=1.15, screen_tag="45s ADMISSIONS FILTER"),
            ScenarioLine(id="ab6_ananya", speaker="Ananya", text="Hello Priya! Regarding your US Fall 2027 Masters application: we've qualified your GRE profile and sent the top 10 STEM university shortlist to your WhatsApp. Tomorrow 4 PM visa session confirmed.", voice="en-IN-NeerjaNeural", rate="+10%", screen_tag="COUNSELOR ANANYA", character_id="counselor"),
            ScenarioLine(id="ab7_wa", speaker="Narrator", text="Delivers STEM program fees, scholarship eligibility, and counselor booking passes directly to WhatsApp.", voice="af_heart", speed=1.15, screen_tag="WHATSAPP ADMISSIONS PASS"),
            ScenarioLine(id="ab8_cost", speaker="Narrator", text="Only verified applicants reach your senior counselors. ₹1.55 per qualification.", voice="af_heart", speed=1.15, screen_tag="₹1.55 PER FILTERED LEAD")
        ],
        whatsapp_asset_attachment=WhatsAppAsset(
            title="Fall 2027 US & Germany STEM Admissions Shortlist & Visa Guide.pdf",
            file_type="dossier",
            file_size_display="3.2 MB",
            headline="Personalized University Shortlist Dossier",
            subheadline="GRE/IELTS Cutoffs + 100% Scholarship Eligibility",
            preview_bullet_points=["Top 10 Ranked STEM Universities", "Post-Study Work Visa Protocol", "1-on-1 Visa Counselor Pass"]
        ),
        cta_lines=[
            ScenarioLine(id="ab9_cta", speaker="Narrator", text="If you run an overseas education or study abroad agency: comment CLOSER below.", voice="af_heart", speed=1.12, screen_tag="COMMENT 'CLOSER'"),
            ScenarioLine(id="ab10_cta2", speaker="Narrator", text="And I'll send you our Overseas Admissions Qualification Stack.", voice="af_heart", speed=1.12, screen_tag="ADMISSIONS STACK")
        ],
        foley_cues=[
            FoleyCue(0.0, "whoosh_hit", 0.85, "Intro"),
            FoleyCue(0.4, "alert_ping", 0.5, "Application ping"),
            FoleyCue(20.0, "sub_drop", 0.95, "Hero drop"),
            FoleyCue(40.0, "whatsapp_pop", 0.85, "University dossier pop"),
            FoleyCue(52.0, "sub_drop", 0.85, "₹1.55 drop"),
            FoleyCue(60.0, "comment_chime", 0.85, "Comment chime")
        ],
        caption_template=(
            "Study Abroad Agents: Stop letting your senior counselors waste hours on unqualified inquiries! ✈️🎓\n\n"
            "CLOSER AI qualifies IELTS scores, university budgets, and target intakes in under 45 seconds, "
            "delivering shortlist dossiers to WhatsApp and passing only hot students to your advisors.\n\n"
            "👇 Comment '{CTA_KEYWORD}' for our Overseas Education AI Qualification Blueprint!\n\n"
            "#studyabroad #overseaseducation #ielts #mastersinusa #closerai"
        )
    )
