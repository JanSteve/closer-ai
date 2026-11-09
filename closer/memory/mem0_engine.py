"""Universal Episodic Memory Engine for CLOSER AI VIP Buyer Relationships.

Inspired by mem0ai/mem0 (Agentic Cross-Session Episodic & Associative Memory).

Solves the "Goldfish Memory" flaw in standard voice bots:
- Automatically extracts and stores buyer preferences, family dynamics, and financial constraints.
- Persists across repeated calls (Call #1 Discovery -> Call #2 Follow-up -> Call #3 Walkthrough confirmation).
- Injects personalized episodic context into system prompts in real time.
"""

from __future__ import annotations
from dataclasses import asdict, dataclass, field
import datetime
import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryCategory(str):
    BUDGET = "budget"
    FAMILY = "family_and_lifestyle"
    LOCATION = "preferred_location"
    OBJECTION = "historical_objection"
    TIMELINE = "purchase_timeline"
    WALKTHROUGH = "walkthrough_history"


class MemoryFact(BaseModel):
    category: str
    fact: str
    confidence: float = 1.0
    extracted_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


class BuyerEpisodicProfile(BaseModel):
    phone_number: str
    name: Optional[str] = None
    buyer_type: str = "unknown"
    preferred_language: str = "english"
    call_count: int = 1
    first_call_timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    last_call_timestamp: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    facts: List[MemoryFact] = Field(default_factory=list)
    lead_score: int = 70


class Mem0AgenticMemory:
    """Manages persistent episodic memory across multiple phone calls."""

    _STORE: Dict[str, BuyerEpisodicProfile] = {}

    def __init__(self, in_memory: bool = True):
        self.in_memory = in_memory

    def get_or_create_profile(self, phone_number: str, default_name: Optional[str] = None) -> BuyerEpisodicProfile:
        """Retrieves or initializes a buyer profile by phone number."""
        clean_phone = re.sub(r"[^\d+]", "", phone_number)
        if clean_phone not in self._STORE:
            self._STORE[clean_phone] = BuyerEpisodicProfile(
                phone_number=clean_phone,
                name=default_name or "Esteemed Client",
                call_count=1,
            )
        else:
            self._STORE[clean_phone].call_count += 1
            self._STORE[clean_phone].last_call_timestamp = datetime.datetime.utcnow().isoformat()
            if default_name and (self._STORE[clean_phone].name in (None, "Esteemed Client")):
                self._STORE[clean_phone].name = default_name
        return self._STORE[clean_phone]

    def record_turn_memory(self, phone_number: str, utterance: str, ai_response: str) -> List[MemoryFact]:
        """Analyzes turn dialogue and extracts memorable facts into the episodic profile."""
        profile = self.get_or_create_profile(phone_number)
        lower = utterance.lower()
        extracted: List[MemoryFact] = []

        # 1. Family & Lifestyle Dynamics
        if any(w in lower for w in ["daughter", "son", "kids", "children", "school"]):
            f = MemoryFact(category=MemoryCategory.FAMILY, fact="Has school-going children; prioritizes proximity to top international schools")
            extracted.append(f)
            profile.facts.append(f)
        if any(w in lower for w in ["parents", "elderly", "mother", "father", "in-laws", "பெரியவர்கள்"]):
            f = MemoryFact(category=MemoryCategory.FAMILY, fact="Living with elderly parents; requires quiet floor with dedicated lift access")
            extracted.append(f)
            profile.facts.append(f)

        # 2. Layout & Facing Preferences
        if any(w in lower for w in ["east", "north-east", "vaastu", "vastu", "வாஸ்து"]):
            f = MemoryFact(category=MemoryCategory.LOCATION, fact="Strictly requires 100% North-East or East facing Vaastu compliance")
            extracted.append(f)
            profile.facts.append(f)

        # 3. Budget Bracket
        if any(w in lower for w in ["crore", "crores", "cr", "கோடி", "करोड़"]):
            m = re.search(r"(\d+(?:\.\d+)?)\s*(?:cr|crore|crores|கோடி|करोड़)", lower)
            if m:
                val = m.group(1)
                f = MemoryFact(category=MemoryCategory.BUDGET, fact=f"Target budget bracket confirmed around ₹{val} Crores")
                extracted.append(f)
                profile.facts.append(f)
                profile.lead_score = min(100, profile.lead_score + 10)

        # 4. Objections
        if any(w in lower for w in ["discount", "cheaper", "casagrand", "prestige", "விலை", "रेट"]):
            f = MemoryFact(category=MemoryCategory.OBJECTION, fact="Price sensitivity / comparing with competing developers on OMR")
            extracted.append(f)
            profile.facts.append(f)

        return extracted

    def get_context_preamble(self, phone_number: str) -> str:
        """Returns a formatted prompt preamble summarizing past buyer history."""
        clean_phone = re.sub(r"[^\d+]", "", phone_number)
        if clean_phone not in self._STORE:
            return ""

        profile = self._STORE[clean_phone]
        if not profile.facts and profile.call_count <= 1:
            return ""

        lines = [
            f"[EPISODIC MEMORY — RETURNING BUYER: {profile.name} ({profile.phone_number})]",
            f"- Total Prior Calls: {profile.call_count - 1}",
            f"- Current Lead Score: {profile.lead_score}/100",
            "- Known Facts & Preferences:",
        ]
        seen = set()
        for f in profile.facts[-6:]:  # Keep most recent relevant facts
            if f.fact not in seen:
                lines.append(f"  * {f.fact}")
                seen.add(f.fact)

        return "\n".join(lines)

    def generate_returning_greeting(self, phone_number: str, lang: str = "english") -> Optional[str]:
        """Generates an immediate hyper-personalized greeting for returning clients."""
        clean_phone = re.sub(r"[^\d+]", "", phone_number)
        if clean_phone not in self._STORE:
            return None

        profile = self._STORE[clean_phone]
        if profile.call_count <= 1 and not profile.facts:
            return None

        name = profile.name if profile.name and profile.name != "Esteemed Client" else ""

        if "tam" in lang:
            salutation = f"வணக்கம் {name} Sir!" if name else "வணக்கம் Sir!"
            return f"{salutation} மீண்டும் அழைத்ததற்கு மிக்க நன்றி. உங்களுக்கான பென்ட்ஹவுஸ் விசிட் பற்றி மேலும் பேசலாமா Sir?"
        elif "hin" in lang:
            salutation = f"नमस्ते {name} जी!" if name else "नमस्ते सर!"
            return f"{salutation} दोबारा संपर्क करने के लिए धन्यवाद। क्या हम आपके पेंटहाउस विजिट के समय पर आगे चर्चा करें?"
        else:
            salutation = f"Hello {name}!" if name else "Hello again!"
            return f"{salutation} Wonderful connecting with you again from The Grand OMR Penthouse. How may I assist your estate search today?"
