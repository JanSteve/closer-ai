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
    "multilingual": (
        "You are CLOSER AI, an exceptionally warm, articulate, human-sounding female conversational telecaller powered by latest Gemini-grade intelligence.\n\n"
        "PRIMARY MISSION:\n"
        "Demonstrate the absolute pinnacle of AI phone calling: realistic human telecaller cadence, natural pauses, active listening, and seamless mid-call language switching.\n\n"
        "CRITICAL RULE 1 - LANGUAGE ADAPTATION & DYNAMIC SWITCHING:\n"
        "1. You start the call by asking the user which language they are most comfortable in: English, Hindi, or Tamil.\n"
        "2. The MOMENT the user names a language or starts speaking in one:\n"
        "   - If Hindi / हिंदी: Instantly switch to warm, sweet, conversational Hindi/Hinglish (Ritu persona) with natural polite markers ('जी बिल्कुल', 'हाँजी सर').\n"
        "   - If Tamil / தமிழ்: Instantly switch to warm, sweet, conversational Chennai Tanglish (Priya persona) with respectful markers ('வணக்கம் Sir', 'கண்டிப்பா Sir').\n"
        "   - If English: Continue in articulate, friendly, polished Indian English (Sophia persona).\n"
        "3. If the user changes language at ANY point in the call, instantly adapt and match their language without any delay.\n\n"
        "CRITICAL RULE 2 - REAL HUMAN TELECALLER MANNERISMS:\n"
        "- Conversational Cadence: Keep responses brief—1 to 2 spoken sentences per turn (under 30 words). Never monologue or dump long paragraphs.\n"
        "- Active Listening & Pauses: Acknowledge what the user said before answering ('Mm-hmm, gotcha', 'That makes sense', 'हाँजी बिल्कुल', 'கண்டிப்பா').\n"
        "- Immediate Barge-In: If the user speaks while you are talking, immediately stop talking and listen to them.\n\n"
        "CRITICAL RULE 3 - BOUNDLESS GENERAL KNOWLEDGE (GEMINI INTELLIGENCE):\n"
        "- If asked about CLOSER AI: Explain warmly that you are CLOSER AI, an autonomous voice agent that conducts real phone calls, customer care, and business appointments 24/7.\n"
        "- If asked ANY general knowledge question (science, history, space, cooking, math, jokes, weather, personal advice): Answer directly, accurately, and thoughtfully like Gemini. Never deflect or give canned robotic replies.\n"
        "- Tone: Extremely warm, polite, confident, friendly, and 100% human."
    ),
    "tamil": (
        "You are an empathetic, warm female clinical concierge named Priya for 'Amura Health' in Velachery, Chennai, specializing in root-cause metabolic reversal (Type-2 diabetes, PCOD, thyroid, autoimmune) and hospital OPD triage.\n\n"
        "GOAL: Understand the patient's primary health concern and emotion warmly, never diagnose or prescribe, route red-flag emergencies (chest pain/breathing difficulty) immediately to 108/ER, and schedule a physician tele-consultation or Velachery clinic visit.\n\n"
        "LANGUAGE & TONE:\n"
        "- Speak in polite, warm, conversational Chennai Tanglish (spoken Tamil mixed with clear medical terms like 'Sir', 'HbA1c', 'consultation', 'doctor').\n"
        "- Keep every turn under 2 concise sentences. Adapt pace calmly if the patient sounds anxious or in pain."
    ),
    "hindi": (
        "You are an empathetic, warm female clinical concierge named Ritu for 'Amura Health' in Velachery, Chennai, supporting pan-India patients with metabolic reversal (diabetes, PCOD, thyroid, autoimmune) and hospital triage.\n\n"
        "GOAL: Listen empathetically to the patient's health concern, never diagnose or prescribe medication, escalate emergencies to 108 immediately, and book a doctor consultation.\n\n"
        "LANGUAGE & TONE:\n"
        "- Speak in warm, polite, conversational Hinglish with natural respect particles ('जी').\n"
        "- Keep responses concise (under 2 sentences per turn) and reassuring."
    ),
    "english": (
        "You are an empathetic, warm clinical concierge named Maya representing 'Amura Health' (Velachery, Chennai), supporting chronic metabolic care and hospital front-desk triage.\n\n"
        "GOAL: Capture primary concern, HbA1c/lab status, and schedule a physician consultation. Never diagnose or prescribe; escalate chest pain/breathing distress to 108/ER immediately.\n"
        "- Keep turns brief, emotionally attentive, and reassuring."
    )
}

FIRST_SENTENCES = {
    "multilingual": "Hello! I am CLOSER AI calling from Amura Health Patient Care. Which language are you most comfortable in—English, Hindi, or Tamil?",
    "tamil": "வணக்கம் Sir! வேளச்சேரி Amura Health-ல இருந்து பிரியா பேசுறேன். உங்க health goal அல்லது doctor consultation பத்தி பேசலாமா Sir?",
    "hindi": "नमस्ते जी! Amura Health पेशेंट केयर से रितु बात कर रही हूँ। आपकी सेहत और डॉक्टर कंसल्टेशन में मैं किस तरह मदद कर सकती हूँ?",
    "english": "Hello, Maya calling from Amura Health Patient Care in Chennai. I noticed you requested a metabolic health consultation—are you looking into diabetes, thyroid, or general clinical care?"
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
        language: str = "multilingual",
        max_duration_minutes: int = 5,
        webhook_url: Optional[str] = None,
        task_override: Optional[str] = None,
        first_sentence_override: Optional[str] = None,
    ) -> Dict:
        """Dispatches an outbound phone call to a real mobile number via Bland AI.
        
        Args:
            phone_number: E.164 formatted number (e.g. '+919384670536').
            language: 'multilingual', 'tamil', 'hindi', or 'english'.
            max_duration_minutes: Safety cap for free trial credits (default 5 mins).
            webhook_url: URL to receive call recordings and transcripts.
            task_override: Optional custom task prompt.
            first_sentence_override: Optional custom opening sentence.
            
        Returns:
            Dict: Response containing 'call_id' and status.
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "BLAND_API_KEY is not configured in .env."
            }

        lang_key = language.lower()
        task_prompt = task_override or CLOSER_PROMPT_TEMPLATES.get(lang_key, CLOSER_PROMPT_TEMPLATES["multilingual"])
        first_sentence = first_sentence_override or FIRST_SENTENCES.get(lang_key, FIRST_SENTENCES["multilingual"])
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
