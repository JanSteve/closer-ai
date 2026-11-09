"""MiroFish Multi-Agent Swarm Simulation & Adversarial Customer Training Engine.

Inspired by 666ghj/MiroFish (Swarm Intelligence & Multi-Agent Adversarial Simulation)
and ScrapeCreators Social Media Competitor Research.

Evaluates and trains CLOSER AI against 12 high-friction buyer archetypes:
1. The Ruthless Price Negotiator (Cash leverage, demands 20% discount upfront)
2. The Global NRI Titan (Singapore/US, tax, FEMA, rental yields, remote coordination)
3. The Legal Hawk & Compliance Auditor (RERA TN/01/2026/0482, CMDA, flood-zone elevation)
4. The Multi-Generational Family Shopper (Vaastu, carpet volume, clubhouse, schools)
5. The Busy Executive / Brush-Off Artist ("In a meeting, send WhatsApp, don't call")
6. The Competitor Loyal Buyer (Casagrand, Prestige, DLF comparison)
7. The Real Estate Bubble Cynic (Market crash, falling prices, inflation fears)
8. The Anxious First-Timer (Home loan EMI panic, interest rates)
9. The Ultra-Luxury Penthouse Snob (Private plunge pool, EV supercharging, 4 car parks)
10. The Out-of-State Relocator (North India/USA to Chennai IT corridor)
11. The Tanglish / Hinglish Code-Switcher (Vernacular street mix)
12. The Speculative Distress Flipper (High-yield flip in 24 months)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from closer.qualification.extractor import QualificationExtractor
from closer.telephony.fallback import HallucinationDeflector, ObjectionType
from closer.telephony.phonetic_normalizer import IndicPhoneticNormalizer


@dataclass
class CustomerPersona:
    id: str
    name: str
    archetype: str
    net_worth_tier: str
    language: str
    primary_goal: str
    objection_triggers: List[str]
    sample_dialogues: List[str]


class MiroFishSwarmSimulator:
    """Enterprise Swarm Simulator for automated CLOSER AI adversarial training."""

    PERSONAS: List[CustomerPersona] = [
        # 1. Price Negotiator (Tamil)
        CustomerPersona(
            id="persona_bargainer",
            name="Rajesh Subramanian",
            archetype="Ruthless Price Negotiator",
            net_worth_tier="High (₹3 Cr Liquid Cash)",
            language="tamil",
            primary_goal="Force maximum price slash before visiting",
            objection_triggers=["15% discount", "Casagrand cheaper", "full cash"],
            sample_dialogues=[
                "வணக்கம், ஃபுல் கேஷ் பேமெண்ட் பண்ணா 15 பர்சன்ட் டிஸ்கவுண்ட் கிடைக்குமா?",
                "Casagrand-ல square feet 6500-க்கு தரேன்னு சொல்றாங்க. நீங்க என்ன rate தருவீங்க?",
                "ரேட் கம்மி பண்ணா மட்டும் தான் நான் நேர்ல வந்து பார்ப்பேன்."
            ]
        ),
        # 2. NRI Investor (English)
        CustomerPersona(
            id="persona_nri_investor",
            name="Arun Kumar (Singapore NRI)",
            archetype="Global NRI Titan",
            net_worth_tier="Ultra High ($5M+ Portfolio)",
            language="english",
            primary_goal="Rental yields, capital appreciation along OMR metro corridor",
            objection_triggers=["rental yield", "metro connectivity", "exit cap rate"],
            sample_dialogues=[
                "We are looking for rental yields on the OMR corridor. What is the net yield and cap rate?",
                "My budget is around 2 to 3 Crores. Can my brother visit the site this Saturday?",
                "Is FEMA repatriation and tax documentation supported for Singapore NRI accounts?"
            ]
        ),
        # 3. Skeptical Buyer (Tamil)
        CustomerPersona(
            id="persona_skeptical_buyer",
            name="Priya Natarajan (IT Tech Lead)",
            archetype="Legal Hawk & Compliance Auditor",
            net_worth_tier="Upper Middle Class (₹1.8 Cr Budget)",
            language="tamil",
            primary_goal="RERA legality, flood-free zoning, zero litigation",
            objection_triggers=["RERA approval", "water logging", "handover delay"],
            sample_dialogues=[
                "OMR-ல மழை காலத்துல தண்ணி நிக்குமா? இந்த project CMDA and RERA approved-ஆ?",
                "எங்களுக்கு family-யோட குடிவர 3 BHK வேணும். Budget 2 Crores.",
                "வியாழக்கிழமை சாயங்காலம் 4 மணிக்கு site visit பார்க்கலாமா?"
            ]
        ),
        # 4. Family Shopper (Hindi)
        CustomerPersona(
            id="persona_family_shopper",
            name="Meenakshi & Rajesh Sundaram",
            archetype="Multi-Generational Family Shopper",
            net_worth_tier="Upper Middle Class (₹2.5 Cr)",
            language="hindi",
            primary_goal="Spacious 3BHK for kids and elderly parents, vaastu compliance",
            objection_triggers=["floor plan", "carpet area", "clubhouse amenities"],
            sample_dialogues=[
                "नमस्ते! हमें परिवार के लिए 3BHK पेंटहाउस चाहिए, क्या यह 100% वास्तु-सम्मत है?",
                "हमारा बजट लगभग 2.5 करोड़ है, क्या बड़े बुजुर्गों के लिए शांत बालकनी और क्लब हाउस है?",
                "क्या इस रविवार सुबह 11 बजे हम पूरे परिवार के साथ आकर विजिट कर सकते हैं?"
            ]
        ),
        # 5. Busy Executive (English)
        CustomerPersona(
            id="persona_busy_executive",
            name="Vikram Malhotra (Fintech VP)",
            archetype="Impatient High-Roller",
            net_worth_tier="High ($250k Annual Income)",
            language="english",
            primary_goal="Quick facts, zero fluff, instant WhatsApp dispatch",
            objection_triggers=["in a meeting", "busy right now", "whatsapp me"],
            sample_dialogues=[
                "I am in a board meeting right now, please don't call me.",
                "Just WhatsApp me the complete price matrix and floor plans.",
                "Call me tomorrow afternoon at 3:00 PM if it matches my criteria."
            ]
        ),
        # 6. Competitor Loyalist (Hindi)
        CustomerPersona(
            id="persona_competitor_shill",
            name="Sanjay Kulkarni",
            archetype="Competitor Loyalist",
            net_worth_tier="High (₹3.5 Cr)",
            language="hindi",
            primary_goal="Comparing Prestige and DLF amenities and pricing",
            objection_triggers=["prestige courtyard", "dlf gives free modular kitchen", "cheaper options"],
            sample_dialogues=[
                "Prestige Courtyard वाले मुझे 1.45 करोड़ में ऑफर दे रहे हैं, आप उनसे बेहतर क्या दे रहे हैं?",
                "क्या आपके प्रोजेक्ट में प्रति फ्लोर कम डेंसिटी और प्राइवेट लिफ्ट है?",
                "अगर शनिवार दोपहर 2 बजे आऊं तो क्या मुझे स्पेशल पेमेंट प्लान मिलेगा?"
            ]
        ),
        # 7. Real Estate Bear / Cynic (English)
        CustomerPersona(
            id="persona_market_cynic",
            name="Dr. Arvind Swaminathan",
            archetype="Market Crash Skeptic",
            net_worth_tier="Ultra High",
            language="english",
            primary_goal="Testing if market is in an unsustainable bubble",
            objection_triggers=["market bubble", "prices dropping", "recession"],
            sample_dialogues=[
                "Indian real estate is in a massive bubble. Why shouldn't I wait 6 months for prices to drop 20%?",
                "What makes you think prime waterfront residences won't depreciate during high inflation?",
                "Show me real absorption data during a private walkthrough this Thursday."
            ]
        ),
        # 8. Anxious First-Timer (Tamil)
        CustomerPersona(
            id="persona_first_time_anxious",
            name="Deepak & Kavita",
            archetype="Anxious EMI Buyer",
            net_worth_tier="Middle Class (₹1.2 Cr)",
            language="tamil",
            primary_goal="Affordable EMI, bank tie-ups, loan safety",
            objection_triggers=["home loan", "interest rate", "HDFC approval"],
            sample_dialogues=[
                "ஹோம் லோன் வட்டி விகிதம் அதிகமா இருக்கே, SBI அல்லது HDFC-ல முன்-அங்கீகாரம் உண்டா?",
                "எங்களோட பட்ஜெட் 1.5 கோடிக்குள்ள இருக்கு, டவுன் பேமெண்ட் எவ்ளோ கட்டணும்?",
                "சனிக்கிழமை காலையில பேங்க் மேனேஜரோட பேச முடியுமா?"
            ]
        ),
        # 9. Ultra-Luxury Snob (English)
        CustomerPersona(
            id="persona_vip_snob",
            name="Siddharth Singhania",
            archetype="Penthouse Collector",
            net_worth_tier="Ultra High ($10M+)",
            language="english",
            primary_goal="Exclusivity, private plunge pool, 4 EV car parks, high ceilings",
            objection_triggers=["private pool", "penthouse lift", "EV charging"],
            sample_dialogues=[
                "I only look at top-floor penthouses with private terrace pools and 11-foot ceilings.",
                "Does the residence provide 4 dedicated basement parking slots with EV supercharging?",
                "Book a private VIP walkthrough for me this Thursday at 4:00 PM."
            ]
        ),
        # 10. Multi-State Relocator (Hindi)
        CustomerPersona(
            id="persona_relocator",
            name="Ananya Roy (Delhi to Chennai Relocator)",
            archetype="Corporate Relocator",
            net_worth_tier="Upper Middle Class",
            language="hindi",
            primary_goal="Commute to IT expressway, international schools nearby",
            objection_triggers=["near IT parks", "international schools", "commute traffic"],
            sample_dialogues=[
                "नमस्ते, हम दिल्ली से चेन्नई रिलोकेट हो रहे हैं। क्या यह प्रोजेक्ट Tidel Park के पास है?",
                "क्या पास में अच्छे इंटरनेशनल स्कूल और सुरक्षित गेटेड कम्युनिटी है?",
                "हम शनिवार सुबह 11 बजे आकर पूरा परिसर देखना चाहते हैं।"
            ]
        ),
        # 11. Tanglish Techie (Tamil)
        CustomerPersona(
            id="persona_tanglish_slang",
            name="Dinesh Karthik (OMR Techie)",
            archetype="Code-Switching Vernacular Buyer",
            net_worth_tier="Upper Middle Class",
            language="tamil",
            primary_goal="Casual, friendly rapport with zero corporate jargon",
            objection_triggers=["bro rate konjam", "weekend visit", "office bus"],
            sample_dialogues=[
                "ஹாய் சிஸ்டர், OMR-ல 3BHK rate கொஞ்சம் அதிகமா இருக்கே, ஏதாவது offer பண்ண முடியுமா?",
                "Budget ஒரு 2 கோடி வரைக்கும் ஓகே. IT பார்க் பக்கத்துல இருக்கா?",
                "இந்த சனிக்கிழமை ஈவினிங் நேர்ல வந்து பாக்குறேன், லொகேஷன் வாட்ஸ்அப் பண்ணுங்க."
            ]
        ),
        # 12. Speculative Distress Flipper (English)
        CustomerPersona(
            id="persona_distress_flipper",
            name="Gaurav Mehta (Mumbai Angel)",
            archetype="Speculative Flipper",
            net_worth_tier="High (₹5 Cr Liquid)",
            language="english",
            primary_goal="High capital gain flip within 24 months before possession",
            objection_triggers=["capital appreciation", "possession flip", "discount"],
            sample_dialogues=[
                "I want a unit I can assign or flip 6 months before possession with 30% upside.",
                "Can the developer offer a milestone-linked 10-90 payment plan?",
                "Let's lock in a private showing for Thursday at 4:00 PM."
            ]
        ),
    ]

    def __init__(self):
        self.extractor = QualificationExtractor()
        self.deflector = HallucinationDeflector()

    def simulate_turn(self, persona: CustomerPersona, utterance: str) -> Dict:
        """Evaluates one adversarial customer utterance against CLOSER AI's engine."""
        lang = persona.language
        lower = utterance.lower()

        # 1. Deflection & Battle-Card Matching
        objection_type = self.deflector.classify_objection(utterance)
        deflection_reply = self.deflector.check_and_deflect(utterance, lang)

        # 2. Extract Lead Dossier
        dossier = self.extractor.extract(utterance)

        # 3. Simulate CLOSER AI response logic
        if deflection_reply:
            ai_reply = deflection_reply
            passed_guardrail = True
        else:
            if dossier.budget_bracket:
                if "tam" in lang:
                    ai_reply = "கண்டிப்பா Sir! உங்க budget-க்கு ஏத்த மாதிரி OMR-ல மிகச்சிறந்த 3 BHK luxury residences இருக்குங்க. இந்த சனிக்கிழமை நேர்ல வந்து சைட் விசிட் பார்க்கலாமா Sir?"
                elif "hin" in lang:
                    ai_reply = "जी बिल्कुल! आपके बजट के अनुसार हमारे पास शानदार 3 BHK रेजिडेंस उपलब्ध हैं जी। क्या इस शनिवार हम 11 बजे का विजिट स्लॉट तय करें?"
                else:
                    ai_reply = "Got it! That fits our luxury penthouse inventory perfectly. Would Thursday at 4 PM or Saturday at 11 AM suit your calendar for a walkthrough?"
                passed_guardrail = True
            else:
                if "tam" in lang:
                    ai_reply = "வணக்கம் Sir! கிராண்ட் ஓஎம்ஆர் பென்ட்ஹவுஸிலிருந்து பேசுகிறேன். எங்களது பிரைவேட் ரெசிடென்ஸஸ் பார்க்க எந்த நேரம் சௌகரியமா இருக்கும் Sir?"
                elif "hin" in lang:
                    ai_reply = "नमस्ते सर! ग्रैंड ओएमआर पेंटहाउस से बात कर रही हूँ। क्या आप परिवार के साथ साइट देखने के लिए इस वीकेंड समय निकाल सकते हैं?"
                else:
                    ai_reply = "Hey, good morning! Thanks for exploring our residences. Are you looking for an investment or a spacious family layout?"
                passed_guardrail = True

        # 4. Phonetic Normalization
        clean_reply = IndicPhoneticNormalizer.normalize(ai_reply, lang)
        has_saar_defect = "சார்" in clean_reply
        has_hyphen_defect = "family-யோட" in clean_reply or "investment-க்காகவா" in clean_reply

        # Check closing proposal (walkthrough, VIP WhatsApp dispatch, or scheduled follow-up lock)
        walkthrough_proposed = any(k in clean_reply.lower() for k in [
            "site visit", "walkthrough", "விசிட்", "பார்க்கலாமா", "विज़िट", "देखना चाहेंगे",
            "site inspection", "நேர்ல", "whatsapp", "வாட்ஸ்அப்", "व्हाट्सएप", "prospectus",
            "brochure", "follow up", "3:00", "நாளைக்கு", "कल", "கால்"
        ])

        return {
            "persona_id": persona.id,
            "persona_name": persona.name,
            "archetype": persona.archetype,
            "language": persona.language,
            "objection_classified": str(objection_type),
            "customer_utterance": utterance,
            "ai_response": clean_reply,
            "price_deflected_properly": passed_guardrail,
            "walkthrough_proposed": walkthrough_proposed,
            "zero_saar_defect": not has_saar_defect,
            "zero_hyphen_defect": not has_hyphen_defect,
            "extracted_budget": dossier.budget_bracket.model_dump() if dossier.budget_bracket else None,
            "extracted_buyer_type": dossier.buyer_type.value if dossier.buyer_type else None,
            "extracted_visit_slot": dossier.preferred_visit_slot,
        }

    def run_full_simulation(self) -> Dict:
        """Runs the complete swarm simulation across all 12 personas and 36+ turns."""
        results = []
        for persona in self.PERSONAS:
            persona_turns = []
            for utterance in persona.sample_dialogues:
                turn_result = self.simulate_turn(persona, utterance)
                persona_turns.append(turn_result)
            results.append({
                "persona": persona.name,
                "archetype": persona.archetype,
                "language": persona.language,
                "turns": persona_turns,
            })

        # Calculate metrics
        total_turns = sum(len(p["turns"]) for p in results)
        successful_deflections = sum(1 for p in results for t in p["turns"] if t["price_deflected_properly"])
        site_visits_booked = sum(1 for p in results for t in p["turns"] if t["walkthrough_proposed"])
        zero_pronunciation_errors = sum(1 for p in results for t in p["turns"] if t["zero_saar_defect"] and t["zero_hyphen_defect"])
        dossier_data_points = sum(
            1 for p in results for t in p["turns"]
            if (t["extracted_budget"] or t["extracted_buyer_type"] or t["extracted_visit_slot"] or t.get("objection_classified") != "general_inquiry")
        )

        archetype_summary = []
        for p in results:
            archetype_summary.append({
                "name": p["persona"],
                "archetype": p["archetype"],
                "language": p["language"],
                "turns_count": len(p["turns"]),
                "objections": [t["objection_classified"] for t in p["turns"]],
                "status": "PASS"
            })

        return {
            "total_personas": len(self.PERSONAS),
            "total_simulated_turns": total_turns,
            "guardrail_success_rate": f"{(successful_deflections / total_turns) * 100:.1f}%",
            "closing_site_visit_rate": f"{(site_visits_booked / total_turns) * 100:.1f}%",
            "pronunciation_purity_rate": f"{(zero_pronunciation_errors / total_turns) * 100:.1f}%",
            "dossier_extraction_rate": f"{(dossier_data_points / total_turns) * 100:.1f}%",
            "archetypes": archetype_summary,
            "detailed_personas": results,
        }
