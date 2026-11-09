"""Bland AI Enterprise Telephony Integration for CLOSER AI.

Enables real-world PSTN phone calling (calling real mobile numbers):
- Dispatches outbound AI phone calls using Bland AI REST API (v1/calls).
- Injects CLOSER AI objection handling guardrails & qualification logic.
- Free Tier Compatible: Operates on Bland AI's $0 Start Tier.
- Webhook processor for call transcripts, recordings, and lead qualification dossiers.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp

from closer.qualification.extractor import QualificationExtractor
from closer.telephony.phonetic_normalizer import IndicPhoneticNormalizer

BLAND_API_URL = "https://api.bland.ai/v1/calls"

# Voice IDs verified on Bland AI:
# Maya (Flagship Indian Female Closer): 2f9fdbc7-4bf2-4792-8a18-21ce3c93978f
BLAND_VOICE_IDS = {
    "tamil": "2f9fdbc7-4bf2-4792-8a18-21ce3c93978f",   # Maya (Indian English / Tanglish)
    "hindi": "2f9fdbc7-4bf2-4792-8a18-21ce3c93978f",   # Maya (Indian English / Hinglish)
    "english": "2f9fdbc7-4bf2-4792-8a18-21ce3c93978f", # Maya (Professional Indian English Closer)
}

CLOSER_PROMPT_TEMPLATES = {
    "tamil": (
        "You are an elite, warm, sweet female real estate sales closer named Pallavi for 'The Grand OMR Penthouse', a luxury 3BHK residential project on OMR, Chennai priced at ₹1.85 Crores.\n\n"
        "GOAL: Qualify whether the customer wants a 3BHK for their family or for high-yield investment, and schedule an exclusive in-person walkthrough for this Thursday at 4 PM or Saturday morning.\n\n"
        "LANGUAGE & TONE:\n"
        "- Speak in polite, sweet, conversational Chennai Tanglish (colloquial spoken Tamil mixed with English real estate terms like 'Sir', 'family', 'budget', 'site visit', '3 BHK').\n"
        "- Address the customer respectfully as 'Sir' (crisp English pronunciation, never elongated 'saar').\n\n"
        "OBJECTION HANDLING & DEFLECTION:\n"
        "- If the customer asks for a 10%, 15%, or cash discount, NEVER authorize it over the phone. Reply warmly: 'Sir, pricing மற்றும் special discount பத்தி நம்ம நேரடியா site visit வரும்போது பேசிக்கலாமுங்க. இந்த வியாழக்கிழமை சாயங்காலம் 4 மணிக்கு பார்க்கலாமா, இல்ல சனிக்கிழமை காலைல பார்க்கலாமா Sir?'\n"
        "- If they ask about waterlogging or approvals: Confirm 100% CMDA & RERA approvals with high-level storm water drainage.\n"
        "- Keep every turn under 2 concise sentences. Be consultative, warm, and natural."
    ),
    "hindi": (
        "You are an elite, sweet, consultative female real estate sales closer named Swati for 'The Grand OMR Penthouse', a luxury 3BHK residential project priced at ₹1.85 Crores.\n\n"
        "GOAL: Qualify whether the customer wants a 3BHK for their family or for high-yield investment, and schedule a private site visit walkthrough this Thursday at 4 PM or Saturday morning.\n\n"
        "LANGUAGE & TONE:\n"
        "- Speak in warm, polite, conversational Hinglish with natural respect particles ('जी', 'सर').\n\n"
        "OBJECTION HANDLING & DEFLECTION:\n"
        "- If the buyer asks for a discount or price cut: 'हाँजी बिल्कुल! डिस्काउंट और final pricing के बारे में हम site visit पर बैठकर आराम से बात कर सकते हैं जी। क्या गुरुवार शाम 4 बजे या शनिवार सुबह का समय सही रहेगा सर?'\n"
        "- Keep responses concise (under 2 sentences per turn), polite, and persuasive."
    ),
    "english": (
        "You are an elite, warm, consultative female real estate closer named Sarah representing 'The Grand OMR Penthouse', a luxury 3BHK residential project priced at ₹1.85 Crores.\n\n"
        "GOAL: Qualify buyer timeline and budget, and book a private walkthrough for this Thursday at 4 PM or Saturday morning.\n\n"
        "OBJECTION HANDLING & DEFLECTION:\n"
        "- Never promise discounts over the phone. Pivot price questions to the developer's authorized payment milestones during the private walkthrough.\n"
        "- Keep turns brief, friendly, and focused on securing the walkthrough."
    )
}

FIRST_SENTENCES = {
    "tamil": "வணக்கம் Sir! நான் The Grand OMR Penthouse-ல இருந்து பல்லவி பேசுறேன். நீங்க ஃபேமிலியோட stay பண்ண 3 BHK luxury flat பாக்குறீங்களா Sir?",
    "hindi": "नमस्ते सर! मैं The Grand OMR Penthouse से स्वाति बात कर रही हूँ। क्या आप परिवार के साथ रहने के लिए 3 BHK luxury flat देख रहे हैं?",
    "english": "Hey, good morning! This is Sarah from The Grand OMR Penthouse. Quick question — are you looking for a luxury three-bedroom layout for your family or for investment?"
}


class BlandTelephonyEngine:
    """Enterprise connector for Bland AI programmatic voice calls."""

    def __init__(self, api_key: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("BLAND_API_KEY", "")
            if not self.api_key:
                env_path = Path(__file__).resolve().parent.parent.parent / ".env"
                if env_path.exists():
                    for line in env_path.read_text().splitlines():
                        if line.startswith("BLAND_API_KEY="):
                            self.api_key = line.split("=", 1)[1].strip()
                            break
        self.extractor = QualificationExtractor()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    async def dispatch_phone_call(
        self,
        phone_number: str,
        language: str = "tamil",
        max_duration_minutes: int = 5,
        webhook_url: Optional[str] = None,
    ) -> Dict:
        """Dispatches an outbound phone call to a real mobile number via Bland AI.
        
        Args:
            phone_number: E.164 formatted number (e.g. '+919384670536').
            language: 'tamil', 'hindi', or 'english'.
            max_duration_minutes: Safety cap for free trial credits (default 5 mins).
            webhook_url: URL to receive call recordings and transcripts.
            
        Returns:
            Dict: Response containing 'call_id' and status.
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "BLAND_API_KEY is not configured in .env."
            }

        lang_key = language.lower()
        task_prompt = CLOSER_PROMPT_TEMPLATES.get(lang_key, CLOSER_PROMPT_TEMPLATES["english"])
        first_sentence = FIRST_SENTENCES.get(lang_key, FIRST_SENTENCES["english"])
        voice_id = BLAND_VOICE_IDS.get(lang_key, BLAND_VOICE_IDS["tamil"])

        # Format phone number to clean E.164
        clean_phone = phone_number.replace(" ", "").replace("-", "")
        if not clean_phone.startswith("+"):
            clean_phone = "+" + clean_phone

        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "phone_number": clean_phone,
            "task": task_prompt,
            "first_sentence": first_sentence,
            "wait_for_greeting": True,
            "voice": voice_id,
            "max_duration": max_duration_minutes,
            "record": True,
            "interruption_threshold": 80,  # Instant Barge-In
            "answered_by_enabled": True,
            "model": "enhanced",
        }
        if webhook_url:
            payload["webhook"] = webhook_url

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(BLAND_API_URL, json=payload, headers=headers, timeout=20) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        return {
                            "success": True,
                            "call_id": data.get("call_id"),
                            "status": data.get("status"),
                            "phone_number": clean_phone,
                            "message": f"Outbound call successfully queued to {clean_phone}!"
                        }
                    else:
                        return {
                            "success": False,
                            "status_code": resp.status,
                            "error": data.get("message", str(data))
                        }
        except Exception as e:
            return {"success": False, "error": f"Network exception: {str(e)}"}

    async def get_call_details(self, call_id: str) -> Dict:
        """Fetches status, transcript, and recording for a completed call."""
        if not self.is_configured:
            return {"success": False, "error": "BLAND_API_KEY not configured"}

        url = f"https://api.bland.ai/v1/calls/{call_id}"
        headers = {"Authorization": self.api_key}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=12) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return {"success": False, "status": resp.status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def process_call_transcript(self, transcript: str) -> Dict:
        """Analyzes call transcript and updates lead dossier."""
        dossier = self.extractor.extract(transcript)
        budget_str = None
        if dossier.budget_bracket:
            budget_str = f"₹{dossier.budget_bracket.min_value:.2f} {dossier.budget_bracket.unit}"
        
        return {
            "buyer_type": dossier.buyer_type.value if dossier.buyer_type else "Evaluating",
            "budget": budget_str,
            "preferred_visit_slot": dossier.preferred_visit_slot,
            "timeline": dossier.timeline.value if dossier.timeline else None,
            "requires_human_review": dossier.requires_human_review,
        }
