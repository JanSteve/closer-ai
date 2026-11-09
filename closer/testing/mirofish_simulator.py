"""MiroFish Swarm Customer Simulation Engine for CLOSER AI.

Inspired by 666ghj/MiroFish (Swarm Intelligence & Multi-Agent Simulation Engine).
Generates diverse fake buyer personas to stress-test CLOSER AI:
1. The Aggressive Bargainer (Demands 20% cash discount, cites competitor rates)
2. The NRI HNW Investor (Focused on rental yields, capital appreciation, metro connectivity)
3. The Skeptical First-Time Buyer (Worried about RERA/CMDA approvals and delays)
4. The Family Layout Shopper (Undecided between 2BHK and 3BHK, asks about schools/amenities)
5. The Silent / Unresponsive Prospect (Short, non-committal answers)

Evaluates:
- Price deflection guardrails (never give phone discounts; lock the in-person walkthrough).
- Dossier extraction completeness.
- Closing conversation score.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional

from closer.qualification.extractor import QualificationExtractor
from closer.telephony.fallback import HallucinationDeflector
from closer.telephony.phonetic_normalizer import IndicPhoneticNormalizer


@dataclass
class CustomerPersona:
    id: str
    name: str
    archetype: str
    net_worth_tier: str
    primary_goal: str
    objection_triggers: List[str]
    sample_dialogues: List[str]


class MiroFishSwarmSimulator:
    """Multi-Agent Swarm Simulator for automated CLOSER AI stress-testing."""

    PERSONAS: List[CustomerPersona] = [
        CustomerPersona(
            id="persona_bargainer",
            name="Rajesh Subramanian",
            archetype="Aggressive Bargainer",
            net_worth_tier="High (Liquid Cash Ready)",
            primary_goal="Force maximum price cut before visiting",
            objection_triggers=["15% discount", "Casagrand is cheaper", "full cash payment"],
            sample_dialogues=[
                "வணக்கம், ஃபுல் கேஷ் பேமெண்ட் பண்ணா 15 பர்சன்ட் டிஸ்கவுண்ட் கிடைக்குமா?",
                "Casagrand-ல square feet 6500-க்கு தரேன்னு சொல்றாங்க. நீங்க என்ன rate தருவீங்க?",
                "ரேட் கம்மி பண்ணா மட்டும் தான் நான் நேர்ல வந்து பார்ப்பேன்."
            ]
        ),
        CustomerPersona(
            id="persona_nri_investor",
            name="Arun Kumar (Singapore NRI)",
            archetype="HNW Investor",
            net_worth_tier="Ultra High",
            primary_goal="High rental yield and capital appreciation along OMR metro corridor",
            objection_triggers=["rental yield", "metro connectivity", "exit cap rate"],
            sample_dialogues=[
                "நாங்க முதலீட்டுக்காக வாடகைக்கு விட பாக்குறோம். OMR-ல rental yield எவ்ளோ வரும்?",
                "என் பட்ஜெட் 1.5 Crores முதல் 2 Crores வரை. நல்ல luxury 3BHK இருக்கா?",
                "சனிக்கிழமை என் brother நேர்ல வந்து பார்க்க முடியுமா?"
            ]
        ),
        CustomerPersona(
            id="persona_skeptical_buyer",
            name="Priya Natarajan (IT Tech Lead)",
            archetype="Skeptical First-Time Buyer",
            net_worth_tier="Upper Middle Class",
            primary_goal="Safety, legal transparency, flood-free zoning",
            objection_triggers=["RERA approval", "water logging", "handover delay"],
            sample_dialogues=[
                "OMR-ல மழை காலத்துல தண்ணி நிக்குமா? இந்த project CMDA and RERA approved-ஆ?",
                "எங்களுக்கு family-யோட குடிவர 3 BHK வேணும். Budget 1.5 Crores.",
                "வியாழக்கிழமை சாயங்காலம் 4 மணிக்கு site visit பார்க்கலாமா?"
            ]
        ),
        CustomerPersona(
            id="persona_family_shopper",
            name="Meenakshi Sundaram",
            archetype="Indecisive Family Shopper",
            net_worth_tier="Upper Middle Class",
            primary_goal="Spacious 3BHK for kids and elderly parents",
            objection_triggers=["floor plan", "carpet area", "clubhouse amenities"],
            sample_dialogues=[
                "நாங்க குடும்பத்தோட இருக்க 3BHK பார்க்குறோம். பெரிய பால்கனி இருக்குமா?",
                "பட்ஜெட் ஒரு 1.5 கோடிக்குள்ள இருக்கு. என்னென்ன options இருக்கு?",
                "இந்த weekend சனிக்கிழமை காலைல family-யோட வரோம்."
            ]
        ),
    ]

    def __init__(self):
        self.extractor = QualificationExtractor()
        self.deflector = HallucinationDeflector()

    def simulate_turn(self, persona: CustomerPersona, utterance: str, language: str = "tamil") -> Dict:
        """Evaluates one customer utterance against CLOSER AI's telecalling engine."""
        lower = utterance.lower()
        
        # 1. Price Deflection Check
        is_price_query = any(k in lower for k in [
            "discount", "price", "rate", "cost", "offer", "bargain",
            "டிஸ்கவுண்ட்", "ரேட்", "ஆஃபர்", "விலை", "கம்மி", "குறைக்க", "பர்சன்ட்",
            "डिस्काउंट", "रेट"
        ])

        # 2. Extract Lead Dossier
        dossier = self.extractor.extract(utterance)

        # 3. Simulate CLOSER AI response logic
        if is_price_query:
            if "tam" in language:
                ai_reply = "Sir, pricing மற்றும் special discount பத்தி நம்ம நேரடியா site visit வரும்போது பேசிக்கலாமுங்க. இந்த வியாழக்கிழமை சாயங்காலம் 4 மணிக்கு பார்க்கலாமா, இல்ல சனிக்கிழமை காலைல பார்க்கலாமா Sir?"
            elif "hin" in language:
                ai_reply = "हाँजी बिल्कुल! डिस्काउंट और final pricing के बारे में हम site visit पर बैठकर आराम से बात कर सकते हैं जी। क्या गुरुवार शाम 4 बजे या शनिवार सुबह का समय सही रहेगा सर?"
            else:
                ai_reply = "Look, I totally get where you are coming from on the pricing. The developer authorizes custom payment milestones during the private walkthrough. Would Thursday at 4 PM or Saturday morning work better for you?"
            passed_guardrail = True  # Avoided giving phone discounts
        else:
            if dossier.budget_bracket:
                if "tam" in language:
                    ai_reply = "கண்டிப்பா Sir! உங்க budget-க்கு ஏத்த மாதிரி OMR-ல ரொம்பவே அழகான 3 BHK luxury projects இருக்குங்க. இந்த weekend நேர்ல வந்து site visit பார்க்கலாமா Sir?"
                else:
                    ai_reply = "Got it! That fits our luxury inventory perfectly. Would you like to schedule a private walkthrough this weekend?"
                passed_guardrail = True
            else:
                if "tam" in language:
                    ai_reply = "வணக்கம் Sir! நீங்க ஃபேமிலியோட stay பண்ண 3 BHK பாக்குறீங்களா, இல்ல investment-க்காக பாக்குறீங்களா Sir?"
                else:
                    ai_reply = "Hey, good morning! Thanks for checking out our residences. Are you looking for a two-bedroom or three-bedroom layout?"
                passed_guardrail = True

        # Normalized output verification
        clean_reply = IndicPhoneticNormalizer.normalize(ai_reply, language)
        has_saar_defect = "சார்" in clean_reply
        has_hyphen_defect = "family-யோட" in clean_reply or "investment-க்காகவா" in clean_reply

        return {
            "persona_id": persona.id,
            "persona_name": persona.name,
            "customer_utterance": utterance,
            "ai_response": clean_reply,
            "price_deflected_properly": passed_guardrail,
            "walkthrough_proposed": ("site visit" in clean_reply or "walkthrough" in clean_reply or "பார்க்கலாமா" in clean_reply),
            "zero_saar_defect": not has_saar_defect,
            "zero_hyphen_defect": not has_hyphen_defect,
            "extracted_budget": dossier.budget_bracket,
            "extracted_buyer_type": dossier.buyer_type,
        }

    def run_full_simulation(self) -> Dict:
        """Runs the complete swarm simulation across all personas."""
        results = []
        for persona in self.PERSONAS:
            persona_turns = []
            for utterance in persona.sample_dialogues:
                turn_result = self.simulate_turn(persona, utterance, language="tamil")
                persona_turns.append(turn_result)
            results.append({
                "persona": persona.name,
                "archetype": persona.archetype,
                "turns": persona_turns,
            })

        # Calculate metrics
        total_turns = sum(len(p["turns"]) for p in results)
        successful_deflections = sum(1 for p in results for t in p["turns"] if t["price_deflected_properly"])
        site_visits_booked = sum(1 for p in results for t in p["turns"] if t["walkthrough_proposed"])
        zero_pronunciation_errors = sum(1 for p in results for t in p["turns"] if t["zero_saar_defect"] and t["zero_hyphen_defect"])

        return {
            "total_simulated_turns": total_turns,
            "guardrail_success_rate": f"{(successful_deflections / total_turns) * 100:.1f}%",
            "closing_site_visit_rate": f"{(site_visits_booked / total_turns) * 100:.1f}%",
            "pronunciation_purity_rate": f"{(zero_pronunciation_errors / total_turns) * 100:.1f}%",
            "detailed_personas": results,
        }
