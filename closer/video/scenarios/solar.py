"""
closer.video.scenarios.solar
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Solar Energy Scenarios: Rooftop Solar EPC, PM Surya Ghar ₹78,000 Subsidy, C&I Solar.
Addresses high monthly power bills, net-metering confusion, and rapid rooftop qualification.
"""

from closer.video.scenarios.base import (
    ReelScenario, Sector, ScenarioLine, CharacterRigConfig,
    WhatsAppAsset, FoleyCue, AttireType, ExpressionType, HairStyle
)


def get_rooftop_solar_scenario() -> ReelScenario:
    """Flagship Solar Scenario: Residential Rooftop Solar EPC & PM Surya Ghar."""
    return ReelScenario(
        id="solar_rooftop_epc_01",
        sector=Sector.SOLAR,
        sub_sector="Residential Rooftop Solar EPC",
        title="Solar EPC: Closing ₹78,000 PM Surya Ghar Leads Instantly",
        target_persona="Rooftop Solar EPC Contractors, Renewable Energy Founders, Solar Installers",
        target_duration=68.0,
        character_rig_configs=[
            CharacterRigConfig(role="host", name="Narrator", hair_style="fade", attire="blazer", accessories=["headset"]),
            CharacterRigConfig(role="engineer", name="Swati", skin_tone="#C68642", hair_style="ponytail", attire="vest", accessories=["hard-hat"], default_expression="smiling"),
            CharacterRigConfig(role="customer", name="Homeowner", hair_style="parted", attire="polo", accessories=["phone-right"])
        ],
        opening_hook_lines=[
            ScenarioLine(
                id="s1_hook",
                speaker="Narrator",
                text="Solar EPCs: how many ₹3 Lakh rooftop solar leads are sitting cold in your CRM right now?",
                voice="af_heart",
                speed=1.15,
                screen_tag="SOLAR EPC LEAD CRISIS",
                scene_visual="crm_leads_stagnant"
            ),
            ScenarioLine(
                id="s2_subsidy",
                speaker="Narrator",
                text="Homeowners want the government's ₹78,000 PM Surya Ghar subsidy, but your sales desk takes three days to call.",
                voice="af_heart",
                speed=1.15,
                screen_tag="PM SURYA GHAR ₹78K",
                scene_visual="subsidy_paperwork_confusion"
            )
        ],
        problem_dialogue=[
            ScenarioLine(
                id="s3_discom",
                speaker="Narrator",
                text="While your reps manually calculate shadow-free rooftop area and Discom net-metering, the buyer moves to Tata Solar.",
                voice="af_heart",
                speed=1.15,
                screen_tag="COMPETITOR POACHING",
                scene_visual="competitor_contract_lost"
            ),
            ScenarioLine(
                id="s4_freeze",
                speaker="Narrator",
                text="By day three, when your engineer calls for a site survey, the customer yells: 'Don't call me again!'",
                voice="af_heart",
                speed=1.15,
                screen_tag="DEAD INQUIRY",
                scene_visual="yelling_customer_hangup"
            )
        ],
        closer_solution_dialogue=[
            ScenarioLine(
                id="s5_closer",
                speaker="Narrator",
                text="Meet CLOSER AI. The autonomous solar closing engine. The second a form submits, Swati calls in under forty-five seconds.",
                voice="af_heart",
                speed=1.15,
                screen_tag="INSTANT < 45s DIAL",
                scene_visual="closer_hero_reveal"
            ),
            ScenarioLine(
                id="s6_hindi_solar",
                speaker="Swati",
                text="नमस्ते सर, आपके 5kW रूफटॉप सोलर का कोटेशन और ₹78,000 पीएम सूर्य घर सब्सिडी ब्रेकडाउन हमने व्हाट्सएप पर भेज दिया है। क्या कल सुबह 11 बजे इंजीनियर साइट सर्वे के लिए आ सकते हैं?",
                voice="hi-IN-SwaraNeural",
                rate="+10%",
                screen_tag="HINDI SOLAR CLOSER",
                character_id="engineer",
                scene_visual="swati_solar_call"
            ),
            ScenarioLine(
                id="s7_whatsapp",
                speaker="Narrator",
                text="During the call, it drops the exact kW sizing, monthly electricity savings, and Discom checklist straight to WhatsApp.",
                voice="af_heart",
                speed=1.15,
                screen_tag="WHATSAPP SOLAR DOSSIER",
                scene_visual="whatsapp_solar_delivery"
            ),
            ScenarioLine(
                id="s8_economics",
                speaker="Narrator",
                text="Human solar telecallers: ₹220 per booked site survey. CLOSER AI: one rupee fifty-five paise, closing deals 24/7.",
                voice="af_heart",
                speed=1.15,
                screen_tag="₹1.55 PER SURVEY",
                scene_visual="unit_economics_showdown"
            )
        ],
        whatsapp_asset_attachment=WhatsAppAsset(
            title="5kW Rooftop Solar Feasibility & ₹78,000 Subsidy Report.pdf",
            file_type="quote",
            file_size_display="3.1 MB",
            headline="5kW On-Grid Solar EPC Quotation",
            subheadline="PM Surya Ghar Muft Bijli Yojana Central Subsidy Breakdown",
            preview_bullet_points=[
                "Estimated Zero Monthly Electricity Bill",
                "₹78,000 Direct Discom Subsidy Credited",
                "3.1-Year Breakeven & 25-Year Panel Warranty"
            ]
        ),
        cta_lines=[
            ScenarioLine(
                id="s9_cta",
                speaker="Narrator",
                text="If you run a rooftop solar EPC company: comment CLOSER below.",
                voice="af_heart",
                speed=1.12,
                screen_tag="COMMENT 'CLOSER'",
                scene_visual="viral_cta_pointing"
            ),
            ScenarioLine(
                id="s10_cta2",
                speaker="Narrator",
                text="And I'll DM you our Solar Lead-to-Site-Survey Automation Playbook.",
                voice="af_heart",
                speed=1.12,
                screen_tag="FREE SOLAR PLAYBOOK",
                scene_visual="viral_cta_pointing"
            )
        ],
        foley_cues=[
            FoleyCue(0.0, "whoosh_hit", 0.85, "Intro"),
            FoleyCue(0.4, "alert_ping", 0.5, "Solar lead notification"),
            FoleyCue(12.0, "hangup_click", 0.85, "Phone hangup"),
            FoleyCue(22.0, "whoosh_hit", 0.7, "Hero transition"),
            FoleyCue(22.1, "sub_drop", 0.95, "Hero sub-bass drop"),
            FoleyCue(32.0, "solar_whoosh", 0.6, "Swati solar call whoosh"),
            FoleyCue(44.0, "whatsapp_pop", 0.85, "WhatsApp quote drop"),
            FoleyCue(52.5, "coin_clink", 0.7, "Economics coin jackpot"),
            FoleyCue(53.0, "sub_drop", 0.9, "Bass drop on ₹1.55"),
            FoleyCue(60.0, "comment_chime", 0.85, "Comment CTA sparkle")
        ],
        caption_template=(
            "Rooftop Solar EPC Contractors: How many ₹3 Lakh solar installations are you losing to slow follow-ups? ☀️\n\n"
            "With the PM Surya Ghar Muft Bijli Yojana, millions of Indian homeowners are ready to install rooftop solar. "
            "But if your sales reps take 3 days to calculate shadow-free area and Discom net-metering, the customer goes elsewhere.\n\n"
            "CLOSER AI calls every inquiry in under 45 seconds:\n"
            "⚡ Calculates kW requirements from monthly bill amount\n"
            "⚡ Explains the ₹78,000 central subsidy in fluent Hindi/English\n"
            "⚡ Dispatches feasibility reports & net-metering checklists to WhatsApp\n"
            "⚡ Locks confirmed site surveys on your engineers' Google Calendar\n"
            "💰 For ₹1.55 per call instead of ₹220 BPO telecalling benches.\n\n"
            "👇 Comment '{CTA_KEYWORD}' below and I'll send you our complete Solar EPC Lead Conversion Engine!\n\n"
            "#solarenergy #rooftopsolar #pmsuryaghar #solarepc #renewablesindia #closerai #salesautomation"
        )
    )


def get_commercial_solar_scenario() -> ReelScenario:
    """Alternate Solar Scenario: Commercial & Industrial (C&I) Solar."""
    return ReelScenario(
        id="solar_commercial_epc_02",
        sector=Sector.SOLAR,
        sub_sector="Commercial & Industrial (C&I) Solar",
        title="Commercial Solar: Closing 100kW Factory Power Installations",
        target_persona="Commercial Solar Developers, Factory Owners, Energy Consultants",
        target_duration=69.0,
        character_rig_configs=[
            CharacterRigConfig(role="host", name="Narrator", attire="blazer", accessories=["headset"]),
            CharacterRigConfig(role="engineer", name="Rajesh", attire="vest", accessories=["hard-hat", "glasses"]),
            CharacterRigConfig(role="customer", name="Factory Owner", attire="blazer", accessories=["phone-right"])
        ],
        opening_hook_lines=[
            ScenarioLine(id="cs1_hook", speaker="Narrator", text="Commercial solar developers: factory owners paying ₹1.5 Lakh power bills are clicking your ads right now.", voice="af_heart", speed=1.15, screen_tag="C&I SOLAR LEADS"),
            ScenarioLine(id="cs2_capex", speaker="Narrator", text="They want to know CAPEX vs OPEX models and accelerated depreciation before board meetings.", voice="af_heart", speed=1.15, screen_tag="BOARDROOM CAPEX")
        ],
        problem_dialogue=[
            ScenarioLine(id="cs3_slow", speaker="Narrator", text="Your sales team takes two weeks to build a financial proposal. By then, commercial buying momentum stalls.", voice="af_heart", speed=1.15, screen_tag="2-WEEK DELAYS"),
            ScenarioLine(id="cs4_loss", speaker="Narrator", text="A ₹40 Lakh commercial installation lost because your pipeline couldn't answer high-tension tariff questions in time.", voice="af_heart", speed=1.15, screen_tag="₹40 LAKH DEAL LOST")
        ],
        closer_solution_dialogue=[
            ScenarioLine(id="cs5_hero", speaker="Narrator", text="Meet CLOSER AI. It qualifies connected load, transformer capacity, and roof load-bearing within forty-five seconds.", voice="af_heart", speed=1.15, screen_tag="HT TARIFF QUALIFIED"),
            ScenarioLine(id="cs6_dial", speaker="Rajesh", text="Good morning sir, regarding your factory's 100kW solar proposal: we've sent the 40% accelerated depreciation model to WhatsApp. Can our technical director visit your plant Thursday?", voice="en-IN-PrabhatNeural", rate="+10%", screen_tag="COMMERCIAL CLOSER", character_id="engineer"),
            ScenarioLine(id="cs7_wa", speaker="Narrator", text="Pushes complete C&I financial models and payback charts straight to the promoter's WhatsApp.", voice="af_heart", speed=1.15, screen_tag="C&I FINANCIAL MODEL"),
            ScenarioLine(id="cs8_eco", speaker="Narrator", text="Enterprise qualification. Zero latency. One rupee fifty-five paise per dial.", voice="af_heart", speed=1.15, screen_tag="₹1.55 ENTERPRISE")
        ],
        whatsapp_asset_attachment=WhatsAppAsset(
            title="100kW Factory Solar - CAPEX vs OPEX & Tax Depreciation Model.pdf",
            file_type="dossier",
            file_size_display="4.2 MB",
            headline="Commercial 100kW Solar Feasibility Dossier",
            subheadline="40% Accelerated Depreciation & Discom HT Tariff Offset",
            preview_bullet_points=["Year 1 Tax Savings: ₹14.8 Lakhs", "CAPEX vs RESCO Comparison", "Plant Inspection Gate Pass"]
        ),
        cta_lines=[
            ScenarioLine(id="cs9_cta", speaker="Narrator", text="If you develop commercial or industrial solar projects: comment CLOSER below.", voice="af_heart", speed=1.12, screen_tag="COMMENT 'CLOSER'"),
            ScenarioLine(id="cs10_cta2", speaker="Narrator", text="And I'll send you our Commercial Solar Pipeline Playbook.", voice="af_heart", speed=1.12, screen_tag="C&I SOLAR PLAYBOOK")
        ],
        foley_cues=[
            FoleyCue(0.0, "whoosh_hit", 0.85, "Intro"),
            FoleyCue(0.4, "alert_ping", 0.5, "Factory lead ping"),
            FoleyCue(22.0, "sub_drop", 0.95, "Hero drop"),
            FoleyCue(42.0, "whatsapp_pop", 0.85, "Financial model pop"),
            FoleyCue(52.0, "sub_drop", 0.85, "₹1.55 drop"),
            FoleyCue(60.0, "comment_chime", 0.85, "CTA chime")
        ],
        caption_template=(
            "Commercial & Industrial Solar Installers: How long does it take your sales engineering team to qualify factory leads? 🏭☀️\n\n"
            "Factory promoters don't want generic brochures—they need connected load analysis, "
            "accelerated depreciation breakdowns, and LT/HT tariff comparisons instantly.\n\n"
            "CLOSER AI answers commercial questions on the first call and locks on-site technical surveys.\n\n"
            "👇 Comment '{CTA_KEYWORD}' for our Commercial Solar Qualification Framework!\n\n"
            "#commercialsolar #industrialsolar #epcindia #solarpower #closerai"
        )
    )
