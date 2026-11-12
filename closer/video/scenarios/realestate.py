"""
closer.video.scenarios.realestate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Luxury Real Estate Scenarios: Oceanfront Villas, High-Rise Apartments, NRI Investment Desks.
Addresses nocturnal leads arriving at 11:42 PM, cross-timezone NRI inquiries,
and locking Sunday 11 AM private site visits with verified RERA documentation.
"""

from closer.video.scenarios.base import (
    ReelScenario, Sector, ScenarioLine, CharacterRigConfig,
    WhatsAppAsset, FoleyCue, AttireType, ExpressionType, HairStyle
)


def get_luxury_villa_scenario() -> ReelScenario:
    """Flagship Real Estate Scenario: Luxury Coastal Villas & NRI Desk."""
    return ReelScenario(
        id="realestate_luxury_villa_01",
        sector=Sector.REALESTATE,
        sub_sector="Luxury Coastal Villas & NRI Desk",
        title="Luxury Real Estate: The 11:42 PM ₹2.85 Cr Penthouse Lead",
        target_persona="Luxury Property Developers, Real Estate Brokers, Channel Partners",
        target_duration=71.0,
        character_rig_configs=[
            CharacterRigConfig(role="host", name="Narrator", hair_style="fade", attire="blazer", accessories=["headset"]),
            CharacterRigConfig(role="closer_agent", name="Maya", skin_tone="#D29568", hair_style="parted", attire="blazer", accessories=["glasses"], default_expression="smiling"),
            CharacterRigConfig(role="customer", name="NRI Investor", hair_style="fade", attire="blazer", accessories=["phone-right"])
        ],
        opening_hook_lines=[
            ScenarioLine(
                id="re1_hook",
                speaker="Narrator",
                text="At 11:42 PM, a multi-crore real estate lead arrives from Dubai.",
                voice="af_heart",
                speed=1.15,
                screen_tag="11:42 PM INBOUND LEAD",
                scene_visual="midnight_lead_alert"
            ),
            ScenarioLine(
                id="re2_loss",
                speaker="Narrator",
                text="Your sales floor is fast asleep. Your eighty-lakh commission is evaporating by the second.",
                voice="af_heart",
                speed=1.15,
                screen_tag="COMMISSION EVAPORATING",
                scene_visual="luxury_penthouse_night"
            )
        ],
        problem_dialogue=[
            ScenarioLine(
                id="re3_harvard",
                speaker="Narrator",
                text="Eighty-seven percent of high-ticket property buyers purchase from the very first developer who responds.",
                voice="af_heart",
                speed=1.15,
                screen_tag="87% FIRST RESPONDER",
                scene_visual="buyer_browsing_luxury"
            ),
            ScenarioLine(
                id="re4_morning",
                speaker="Narrator",
                text="When your sales executive finally calls at 11:00 AM tomorrow, the buyer has already booked a preview with your competitor.",
                voice="af_heart",
                speed=1.15,
                screen_tag="LOST TO COMPETITOR",
                scene_visual="lost_client_hangup"
            )
        ],
        closer_solution_dialogue=[
            ScenarioLine(
                id="re5_hero",
                speaker="Narrator",
                text="Meet CLOSER AI. The autonomous luxury closing engine. In under forty-five seconds, Maya awakens and dials.",
                voice="af_heart",
                speed=1.15,
                screen_tag="AUTONOMOUS DESK",
                scene_visual="closer_hero_reveal"
            ),
            ScenarioLine(
                id="re6_maya_en",
                speaker="Maya",
                text="Good evening Mr. Sharma. The sea-facing villa brochure and 8.4% rental yield breakdown are in your WhatsApp. Sunday eleven AM is locked for your private site visit.",
                voice="af_bella",
                speed=1.10,
                screen_tag="MAYA LUXURY DESK",
                character_id="closer_agent",
                scene_visual="maya_realestate_call"
            ),
            ScenarioLine(
                id="re7_tamil_rera",
                speaker="Maya",
                text="வணக்கம் சார், உங்கள் ECR விசிட் கன்ஃபர்ம் செய்யலாமா? RERA ஆவணங்கள் மற்றும் வாஸ்து திட்டங்கள் வாட்ஸ்அப்பில் அனுப்பப்பட்டுள்ளது.",
                voice="ta-IN-PallaviNeural",
                rate="+10%",
                screen_tag="TAMIL RERA VERIFIED",
                character_id="closer_agent",
                scene_visual="maya_tamil_realestate"
            ),
            ScenarioLine(
                id="re8_whatsapp",
                speaker="Narrator",
                text="Architectural floorplans, RERA sanctions, and VIP chauffeur site passes delivered right inside WhatsApp during the call.",
                voice="af_heart",
                speed=1.15,
                screen_tag="WHATSAPP VIP PASS",
                scene_visual="whatsapp_realestate_delivery"
            ),
            ScenarioLine(
                id="re9_economics",
                speaker="Narrator",
                text="Traditional brokerage call desks: ₹220 per prospect call. CLOSER AI: one rupee fifty-five paise.",
                voice="af_heart",
                speed=1.15,
                screen_tag="₹1.55 VS ₹220",
                scene_visual="unit_economics_showdown"
            )
        ],
        whatsapp_asset_attachment=WhatsAppAsset(
            title="Oceanfront Luxury Villas - 24-Page Project Dossier & RERA Pass.pdf",
            file_type="dossier",
            file_size_display="5.4 MB",
            headline="Oceanfront Residences ECR Dossier",
            subheadline="RERA TN/01/2026/0482 · 8.4% Projected Rental Yields",
            preview_bullet_points=[
                "4BHK Private Plunge Pool Floorplans",
                "Dubai & Singapore NRI Payment Milestones",
                "Sunday 11 AM Chauffeur Preview Pass"
            ]
        ),
        cta_lines=[
            ScenarioLine(
                id="re10_cta",
                speaker="Narrator",
                text="If you sell luxury villas, high-rises, or premium plots: comment CLOSER below.",
                voice="af_heart",
                speed=1.12,
                screen_tag="COMMENT 'CLOSER'",
                scene_visual="viral_cta_pointing"
            ),
            ScenarioLine(
                id="re11_cta2",
                speaker="Narrator",
                text="And I'll send you our High-Ticket Real Estate Lead Closing Engine for free.",
                voice="af_heart",
                speed=1.12,
                screen_tag="LUXURY REALTY ENGINE",
                scene_visual="viral_cta_pointing"
            )
        ],
        foley_cues=[
            FoleyCue(0.0, "whoosh_hit", 0.85, "Intro"),
            FoleyCue(0.4, "alert_ping", 0.5, "11:42 PM lead ping"),
            FoleyCue(11.0, "whoosh_hit", 0.65, "Cut to 87% stat"),
            FoleyCue(18.0, "hangup_click", 0.85, "Competitor hangup"),
            FoleyCue(25.0, "whoosh_hit", 0.7, "Hero reveal"),
            FoleyCue(25.1, "sub_drop", 0.95, "Hero sub-bass drop"),
            FoleyCue(34.2, "alert_ping", 0.35, "Maya English dialogue ping"),
            FoleyCue(42.4, "clinic_chime", 0.5, "Tamil RERA chime"),
            FoleyCue(51.0, "whatsapp_pop", 0.85, "WhatsApp 24-page dossier"),
            FoleyCue(58.0, "whoosh_hit", 0.65, "Unit economics"),
            FoleyCue(58.2, "sub_drop", 0.9, "Bass drop on ₹1.55"),
            FoleyCue(64.5, "comment_chime", 0.85, "Comment CTA sparkle")
        ],
        caption_template=(
            "Real Estate Developers & Luxury Brokers: When a ₹2.85 Cr lead arrives at 11:42 PM, who answers? 🏙️\n\n"
            "High-net-worth buyers and NRIs in Dubai or Singapore browse properties during their evening hours. "
            "If your sales desk takes 12 hours to respond, that multi-crore deal is booked with another builder.\n\n"
            "CLOSER AI awakens in under 45 seconds:\n"
            "🏡 Qualifies budget, liquid cash vs home loan pre-approval\n"
            "🏡 Answers RERA registration, Vaastu compliance & rental yields\n"
            "🏡 Drops high-res brochures & floor plans straight to WhatsApp\n"
            "🏡 Locks Sunday 11 AM private site visits directly in your CRM\n"
            "💰 All at ₹1.55 per lead call instead of expensive brokerage call centers.\n\n"
            "👇 Comment '{CTA_KEYWORD}' below to get our Luxury Real Estate Inbound Closing Engine!\n\n"
            "#luxuryrealestate #indianrealestate #nriinvestments #rera #propertysales #closerai #salesautomation"
        )
    )


def get_apartments_scenario() -> ReelScenario:
    """Alternate Real Estate Scenario: High-Rise Gated Community."""
    return ReelScenario(
        id="realestate_apartments_02",
        sector=Sector.REALESTATE,
        sub_sector="High-Rise Gated Communities",
        title="High-Rise Apartments: Eliminating Sunday Site Visit No-Shows",
        target_persona="Builder Sales Heads, Property Portals, Real Estate Marketing Agencies",
        target_duration=68.0,
        character_rig_configs=[
            CharacterRigConfig(role="host", name="Narrator", attire="blazer", accessories=["headset"]),
            CharacterRigConfig(role="closer_agent", name="Vikram", attire="blazer", accessories=["glasses"]),
            CharacterRigConfig(role="customer", name="Homebuyer", attire="polo", accessories=["phone-right"])
        ],
        opening_hook_lines=[
            ScenarioLine(id="apt1_hook", speaker="Narrator", text="Real estate marketing teams: you generate 150 leads for Sunday site visits, but 60% never show up.", voice="af_heart", speed=1.15, screen_tag="60% NO-SHOW RATE"),
            ScenarioLine(id="apt2_loss", speaker="Narrator", text="Your sales gallery sits empty while your ad budget burns ₹80,000 every single weekend.", voice="af_heart", speed=1.15, screen_tag="EMPTY SALES GALLERY")
        ],
        problem_dialogue=[
            ScenarioLine(id="apt3_followup", speaker="Narrator", text="Human reps send generic text messages that get buried under a hundred promotional WhatsApp chats.", voice="af_heart", speed=1.15, screen_tag="UNREAD TEXTS"),
            ScenarioLine(id="apt4_excuses", speaker="Narrator", text="On Sunday morning, prospects make excuses: 'Traffic was bad', or 'We lost the location pin.'", voice="af_heart", speed=1.15, screen_tag="SUNDAY EXCUSES")
        ],
        closer_solution_dialogue=[
            ScenarioLine(id="apt5_closer", speaker="Narrator", text="CLOSER AI runs automated voice re-confirmations forty-five minutes before site visits.", voice="af_heart", speed=1.15, screen_tag="CONFIRMATION CALL"),
            ScenarioLine(id="apt6_vikram", speaker="Vikram", text="नमस्ते सर, द ग्रैंड क्रेस्ट से विक्रम। आपकी रविवार सुबह 11 बजे की 3BHK विज़िट का गेट पास और गूगल मैप्स पिन हमने व्हाट्सएप पर भेज दिया है। क्या आपकी गाड़ी के लिए पार्किंग रिज़र्व कर दें?", voice="hi-IN-SwaraNeural", rate="+10%", screen_tag="HINDI GATE PASS", character_id="closer_agent"),
            ScenarioLine(id="apt7_wa", speaker="Narrator", text="Drops live GPS map pins and VIP gate pass QR codes straight into WhatsApp, lifting attendance to 88%.", voice="af_heart", speed=1.15, screen_tag="88% ATTENDANCE"),
            ScenarioLine(id="apt8_cost", speaker="Narrator", text="Zero no-shows. Packed sales lounge. One rupee fifty-five paise per call.", voice="af_heart", speed=1.15, screen_tag="₹1.55 PER VISITOR")
        ],
        whatsapp_asset_attachment=WhatsAppAsset(
            title="The Grand Crest - Sunday Site Visit Pass & GPS Directions.pdf",
            file_type="pass",
            file_size_display="2.8 MB",
            headline="Sunday Site Visit VIP Pass",
            subheadline="Reserved Parking QR Code + 3BHK Cost Sheet",
            preview_bullet_points=["Direct GPS Location Pin", "Sample Flat Video Walkthrough", "Tower B Fast-Track Pass"]
        ),
        cta_lines=[
            ScenarioLine(id="apt9_cta", speaker="Narrator", text="If you market residential apartments or gated communities: comment CLOSER below.", voice="af_heart", speed=1.12, screen_tag="COMMENT 'CLOSER'"),
            ScenarioLine(id="apt10_cta2", speaker="Narrator", text="And I'll DM you our High-Rise Site Visit Confirmation Playbook.", voice="af_heart", speed=1.12, screen_tag="SITE VISIT PLAYBOOK")
        ],
        foley_cues=[
            FoleyCue(0.0, "whoosh_hit", 0.85, "Intro"),
            FoleyCue(0.4, "alert_ping", 0.5, "Sunday no-show ping"),
            FoleyCue(20.0, "sub_drop", 0.95, "Hero reveal"),
            FoleyCue(38.0, "whatsapp_pop", 0.85, "Gate pass pop"),
            FoleyCue(50.0, "coin_clink", 0.7, "Packed lounge"),
            FoleyCue(58.0, "comment_chime", 0.85, "CTA chime")
        ],
        caption_template=(
            "Real Estate Sales Heads: Stop letting 60% of your Sunday site visits ghost your sales gallery! 🏢\n\n"
            "CLOSER AI confirms leads in under 45 seconds, dispatches WhatsApp GPS pins and gate pass QR codes, "
            "and sends proactive re-confirmation calls before their appointment.\n\n"
            "👇 Comment '{CTA_KEYWORD}' to get our Site Visit Attendance Acceleration Engine!\n\n"
            "#realestateindia #apartmentforsale #gurugramrealestate #bangalorerealty #closerai"
        )
    )
