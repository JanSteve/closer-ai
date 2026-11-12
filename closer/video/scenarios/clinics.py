"""
closer.video.scenarios.clinics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Healthcare & Clinic Scenarios: Dental Implants, Hair Restoration & IVF.
Addresses patient drop-offs, busy reception desks, after-hours inquiries,
and instant appointment confirmations in Tamil, Hindi, and English.
"""

from closer.video.scenarios.base import (
    ReelScenario, Sector, ScenarioLine, CharacterRigConfig,
    WhatsAppAsset, FoleyCue, AttireType, ExpressionType, HairStyle
)


def get_dental_implant_scenario() -> ReelScenario:
    """Flagship Healthcare Scenario: Dental Implants & Invisible Aligners."""
    return ReelScenario(
        id="clinic_dental_implant_01",
        sector=Sector.CLINICS,
        sub_sector="Dental Implants & Invisible Aligners",
        title="Dental Clinic: 40% Lead Drop-off Solved in 45 Seconds",
        target_persona="Dental Clinic Founders, Maxillofacial Surgeons, Practice Managers",
        target_duration=68.0,
        character_rig_configs=[
            CharacterRigConfig(
                role="host",
                name="Narrator",
                hair_style="fade",
                attire="blazer",
                accessories=["headset"],
                default_expression="smiling"
            ),
            CharacterRigConfig(
                role="doctor",
                name="Dr. Pallavi",
                skin_tone="#D29568",
                hair_style="bun",
                attire="labcoat",
                accessories=["stethoscope", "glasses"],
                default_expression="smiling"
            ),
            CharacterRigConfig(
                role="customer",
                name="Hesitant Patient",
                hair_style="parted",
                attire="polo",
                accessories=["phone-right"],
                default_expression="stressed"
            )
        ],
        opening_hook_lines=[
            ScenarioLine(
                id="c1_hook",
                speaker="Narrator",
                text="Doctors: why does your front desk miss 40% of high-ticket dental implant leads?",
                voice="af_heart",
                speed=1.15,
                screen_tag="DENTAL CLINIC CLINICIAN",
                scene_visual="clinic_reception_chaos"
            ),
            ScenarioLine(
                id="c2_burn",
                speaker="Narrator",
                text="You spend ₹60,000 every month on Google Ads, but your patients slip away into thin air.",
                voice="af_heart",
                speed=1.15,
                screen_tag="AD SPEND COLLAPSE",
                scene_visual="ad_spend_burn"
            )
        ],
        problem_dialogue=[
            ScenarioLine(
                id="c3_reception",
                speaker="Narrator",
                text="At 8:30 PM, your staff packed up and went home. The inbound patient calls three competing clinics.",
                voice="af_heart",
                speed=1.15,
                screen_tag="THE MISSED WINDOW",
                scene_visual="empty_reception_night"
            ),
            ScenarioLine(
                id="c4_delay",
                speaker="Narrator",
                text="When your receptionist finally calls at noon tomorrow, the patient slams the phone: 'I already booked elsewhere!'",
                voice="af_heart",
                speed=1.15,
                screen_tag="LOST ₹35,000 PATIENT",
                scene_visual="yelling_patient_hangup"
            )
        ],
        closer_solution_dialogue=[
            ScenarioLine(
                id="c5_hero",
                speaker="Narrator",
                text="Meet CLOSER AI. The autonomous clinical telecaller. In under forty-five seconds, Dr. Pallavi dials the patient.",
                voice="af_heart",
                speed=1.15,
                screen_tag="AUTONOMOUS TRIAGE",
                scene_visual="closer_hero_reveal"
            ),
            ScenarioLine(
                id="c6_tamil_ai",
                speaker="Dr. Pallavi",
                text="வணக்கம் மேடம், டாக்டர் பல்லவி டென்டல் கிளினிக்கிலிருந்து அழைக்கிறேன். உங்கள் டென்டல் இம்ப்ளான்ட் ஆலோசனையை நாளை மாலை 5 மணிக்கு கன்பார்ம் செய்யலாமா?",
                voice="ta-IN-PallaviNeural",
                rate="+10%",
                screen_tag="TAMIL AI CLINICAL DIAL",
                character_id="doctor",
                scene_visual="pallavi_clinical_call"
            ),
            ScenarioLine(
                id="c7_whatsapp",
                speaker="Narrator",
                text="While on the call, it drops the CBCT scan checklist and zero percent EMI schedule straight to their WhatsApp.",
                voice="af_heart",
                speed=1.15,
                screen_tag="INSTANT WHATSAPP SYNC",
                scene_visual="whatsapp_implant_delivery"
            ),
            ScenarioLine(
                id="c8_economics",
                speaker="Narrator",
                text="Human clinic call desks cost ₹220 per booked patient. CLOSER AI costs one rupee fifty-five paise with zero payroll.",
                voice="af_heart",
                speed=1.15,
                screen_tag="⚡ 99.3% COST REDUCTION",
                scene_visual="unit_economics_showdown"
            )
        ],
        whatsapp_asset_attachment=WhatsAppAsset(
            title="Dr. Pallavi Dental Studio - Implant Guide & 0% EMI Plan.pdf",
            file_type="pdf",
            file_size_display="2.2 MB",
            headline="Personalized Implant Treatment Plan",
            subheadline="CBCT Scan Protocol + Bajaj Finserv 0% EMI Schedule",
            preview_bullet_points=[
                "Single Tooth vs All-on-4 Cost Comparison",
                "Titanium Grade 5 Biocompatibility Certificate",
                "Same-Day Consultation Gate Pass"
            ]
        ),
        cta_lines=[
            ScenarioLine(
                id="c9_cta_prompt",
                speaker="Narrator",
                text="If you run a dental, aesthetic, or healthcare clinic: comment CLOSER below.",
                voice="af_heart",
                speed=1.12,
                screen_tag="COMMENT 'CLOSER'",
                scene_visual="viral_cta_pointing"
            ),
            ScenarioLine(
                id="c10_cta_deliver",
                speaker="Narrator",
                text="And I'll DM you our Dental Clinic Auto-Caller Setup Playbook for free.",
                voice="af_heart",
                speed=1.12,
                screen_tag="GET FREE PLAYBOOK",
                scene_visual="viral_cta_pointing"
            )
        ],
        foley_cues=[
            FoleyCue(0.0, "whoosh_hit", 0.85, "Opening scene transition"),
            FoleyCue(0.4, "alert_ping", 0.5, "Lead inquiry ping"),
            FoleyCue(10.5, "whoosh_hit", 0.65, "Cut to night reception"),
            FoleyCue(16.2, "hangup_click", 0.85, "Patient phone slam click"),
            FoleyCue(23.0, "whoosh_hit", 0.7, "Cut to CLOSER AI reveal"),
            FoleyCue(23.1, "sub_drop", 0.95, "Bass drop on autonomous hero"),
            FoleyCue(31.5, "clinic_chime", 0.6, "Dr. Pallavi clinical chime"),
            FoleyCue(44.2, "whatsapp_pop", 0.85, "WhatsApp implant guide delivery"),
            FoleyCue(52.8, "whoosh_hit", 0.65, "Unit economics transition"),
            FoleyCue(53.0, "sub_drop", 0.85, "Bass drop on ₹1.55"),
            FoleyCue(60.5, "comment_chime", 0.85, "CTA comment sparkle chime")
        ],
        caption_template=(
            "Doctors & Clinic Owners: How many high-ticket dental implant consultations did your front desk miss this week? 🦷\n\n"
            "Patients inquiring after 8 PM don't wait for your clinic to open at 10 AM tomorrow. "
            "They call three competitors, and the first responder books the appointment.\n\n"
            "CLOSER AI responds in under 45 seconds:\n"
            "✅ Speaks fluent Tamil, Hindi, and Indian English\n"
            "✅ Qualifies procedure requirements & answers treatment FAQs\n"
            "✅ Delivers pre-op guides & 0% EMI schedules to WhatsApp\n"
            "✅ Directly confirms consults on your practice calendar\n"
            "💰 All at ₹1.55 per call instead of ₹220 BPO telecalling benches.\n\n"
            "👇 Comment '{CTA_KEYWORD}' below and I'll DM you our step-by-step Dental Clinic Setup Playbook!\n\n"
            "#dentalclinic #dentistsofindia #clinicgrowth #healthcareautomation #closerai #telecalling #salesautomation"
        )
    )


def get_hair_clinic_scenario() -> ReelScenario:
    """Alternate Healthcare Scenario: Hair Restoration & PRP Clinic."""
    return ReelScenario(
        id="clinic_hair_transplant_02",
        sector=Sector.CLINICS,
        sub_sector="Hair Restoration & Trichology",
        title="Hair Clinics: Converting Midnight Scalp Assessment Inquiries",
        target_persona="Cosmetic Surgeons, Hair Restoration Clinic Owners, Trichologists",
        target_duration=67.0,
        character_rig_configs=[
            CharacterRigConfig(role="host", name="Narrator", hair_style="fade", attire="blazer", accessories=["headset"]),
            CharacterRigConfig(role="doctor", name="Dr. Ashwin", hair_style="parted", attire="scrubs", accessories=["glasses"]),
            CharacterRigConfig(role="customer", name="Inquiring Patient", hair_style="messy", attire="polo", accessories=["phone-right"])
        ],
        opening_hook_lines=[
            ScenarioLine(
                id="h1_hook",
                speaker="Narrator",
                text="Hair restoration clinics: what happens when someone looks in the mirror at 11:30 PM and fills out your form?",
                voice="af_heart",
                speed=1.15,
                screen_tag="11:30 PM INQUIRY"
            ),
            ScenarioLine(
                id="h2_intent",
                speaker="Narrator",
                text="That emotional buying intent vanishes completely if they don't get a call before they fall asleep.",
                voice="af_heart",
                speed=1.15,
                screen_tag="INTENT COLLAPSE"
            )
        ],
        problem_dialogue=[
            ScenarioLine(
                id="h3_embarrassment",
                speaker="Narrator",
                text="Human sales reps call next afternoon during their office hours. The prospect is embarrassed and ignores your call.",
                voice="af_heart",
                speed=1.15,
                screen_tag="GHOSTED CALL"
            ),
            ScenarioLine(
                id="h4_cost",
                speaker="Narrator",
                text="You just paid ₹1,800 on Meta Ads for a lead that never even spoke to your doctor.",
                voice="af_heart",
                speed=1.15,
                screen_tag="₹1,800 CPL WASTED"
            )
        ],
        closer_solution_dialogue=[
            ScenarioLine(
                id="h5_closer",
                speaker="Narrator",
                text="CLOSER AI calls in under forty seconds with complete medical confidentiality.",
                voice="af_heart",
                speed=1.15,
                screen_tag="SUB-45s DIAL"
            ),
            ScenarioLine(
                id="h6_hindi_call",
                speaker="Dr. Ashwin",
                text="नमस्ते राहुल जी, हेयर ट्रांसप्लांट क्लिनिक से बोल रहा हूँ। आपका ग्राफ्ट असेसमेंट और ट्रीटमेंट एस्टीमेट व्हाट्सएप पर भेज दिया है। क्या शनिवार शाम 4 बजे डॉक्टर से मिल सकते हैं?",
                voice="hi-IN-SwaraNeural",
                rate="+10%",
                screen_tag="CONFIDENTIAL HINDI DIAL",
                character_id="doctor"
            ),
            ScenarioLine(
                id="h7_whatsapp",
                speaker="Narrator",
                text="It drops the 2,500 graft FUE calculator and pre-procedure guide straight to WhatsApp while locking Saturday's scalp consult.",
                voice="af_heart",
                speed=1.15,
                screen_tag="WHATSAPP DOSSIER"
            ),
            ScenarioLine(
                id="h8_roi",
                speaker="Narrator",
                text="Zero dropped leads. Full doctor calendar. ₹1.55 per call.",
                voice="af_heart",
                speed=1.15,
                screen_tag="₹1.55 AUTONOMOUS"
            )
        ],
        whatsapp_asset_attachment=WhatsAppAsset(
            title="Follicular Hair Restoration - Graft Assessment & Price Guide.pdf",
            file_type="pdf",
            file_size_display="1.9 MB",
            headline="Personalized Scalp & Graft Analysis",
            subheadline="FUE Technique Breakdown + Doctor Availability",
            preview_bullet_points=[
                "Norwood Scale Assessment Breakdown",
                "Pre-Procedure Care Guidelines",
                "Saturday VIP Appointment Confirmation"
            ]
        ),
        cta_lines=[
            ScenarioLine(
                id="h9_cta",
                speaker="Narrator",
                text="If you own a hair transplant or cosmetic clinic: comment CLOSER below.",
                voice="af_heart",
                speed=1.12,
                screen_tag="COMMENT 'CLOSER'"
            ),
            ScenarioLine(
                id="h10_cta2",
                speaker="Narrator",
                text="And I'll send you our complete Aesthetic Clinic Inbound Playbook.",
                voice="af_heart",
                speed=1.12,
                screen_tag="INBOUND PLAYBOOK"
            )
        ],
        foley_cues=[
            FoleyCue(0.0, "whoosh_hit", 0.85, "Opening hook"),
            FoleyCue(0.4, "alert_ping", 0.5, "11:30 PM notification"),
            FoleyCue(12.0, "hangup_click", 0.8, "Ghosted call"),
            FoleyCue(22.0, "whoosh_hit", 0.7, "CLOSER reveal"),
            FoleyCue(22.1, "sub_drop", 0.95, "Hero drop"),
            FoleyCue(40.0, "whatsapp_pop", 0.85, "WhatsApp graft guide"),
            FoleyCue(51.0, "sub_drop", 0.85, "₹1.55 economics"),
            FoleyCue(59.0, "comment_chime", 0.85, "Comment chime")
        ],
        caption_template=(
            "Cosmetic & Hair Clinics: Stop losing high-ticket patients to slow daytime callbacks! 💇‍♂️\n\n"
            "Inbound leads inquiring late at night are in high emotional pain. "
            "If your clinic calls 16 hours later during their office meetings, they won't answer.\n\n"
            "CLOSER AI dials in 40 seconds:\n"
            "✅ Private, consultative qualification\n"
            "✅ Norwood scale triage & procedure breakdown\n"
            "✅ WhatsApp delivery of graft estimates & consultation passes\n"
            "✅ 24/7 calendar booking for your surgeons\n\n"
            "👇 Comment '{CTA_KEYWORD}' to get our Aesthetic Clinic Telecalling Blueprint!\n\n"
            "#hairtransplant #prptreatment #trichology #aestheticclinic #closerai #salesautomation"
        )
    )
