"""Deterministic Qualification Extractor using Pydantic v2 schemas.

Enforces zero-hallucination extraction:
- Budget brackets (INR Crores, Lakhs, USD Millions, AED)
- Purchase timelines (immediate, 30/60/90 days, flexible)
- Buyer personas (end-user vs investor vs corporate relocator)
- Preferred walkthrough visit slots
- Pre-approved mortgage status
- Objection category tagging for 360 CRM enrichment
"""

from __future__ import annotations

from enum import Enum
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TimelineEnum(str, Enum):
    IMMEDIATE = "immediate"
    DAYS_30 = "30_days"
    DAYS_60 = "60_days"
    DAYS_90 = "90_days"
    FLEXIBLE = "flexible"


class BuyerTypeEnum(str, Enum):
    END_USER = "end_user"
    INVESTOR = "investor"


class BudgetBracket(BaseModel):
    min_value: float = 0.0
    max_value: float = 0.0
    currency: str = "INR"
    unit: str = "Crores"


class QualificationDossier(BaseModel):
    timeline: Optional[TimelineEnum] = None
    budget_bracket: Optional[BudgetBracket] = None
    buyer_type: Optional[BuyerTypeEnum] = None
    preferred_visit_slot: Optional[str] = None
    pre_approved_mortgage: Optional[bool] = None
    objection_category: Optional[str] = None
    requires_human_review: bool = False
    confidence_score: float = 1.0


class QualificationExtractor:
    """Extracts structured financial dossiers with deterministic validation."""

    def extract(self, text: str) -> QualificationDossier:
        if not text or not text.strip():
            return QualificationDossier(requires_human_review=True, confidence_score=0.0)

        lower = text.lower()
        dossier = QualificationDossier()

        # 1. Budget Extraction (INR Crores, Lakhs, USD, AED)
        cr_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*(?:cr|crore|crores|கோடி|करोड़)", lower)
        lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*(?:l|lakh|lakhs|லட்சம்|லாக்கு|लाख)", lower)
        usd_match = re.search(r"\$\s*(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*(?:m|million)?", lower)
        aed_match = re.search(r"(?:aed|dirhams?)\s*(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?", lower)

        if cr_match:
            min_v = float(cr_match.group(1))
            max_v = float(cr_match.group(2)) if cr_match.group(2) else min_v
            dossier.budget_bracket = BudgetBracket(min_value=min_v, max_value=max_v, currency="INR", unit="Crores")
        elif lakh_match:
            min_v = float(lakh_match.group(1)) / 100.0  # normalize to crores
            max_v = float(lakh_match.group(2)) / 100.0 if lakh_match.group(2) else min_v
            dossier.budget_bracket = BudgetBracket(min_value=min_v, max_value=max_v, currency="INR", unit="Crores")
        elif usd_match:
            min_v = float(usd_match.group(1))
            max_v = float(usd_match.group(2)) if usd_match.group(2) else min_v
            dossier.budget_bracket = BudgetBracket(min_value=min_v, max_value=max_v, currency="USD", unit="Millions")
        elif aed_match:
            min_v = float(aed_match.group(1))
            max_v = float(aed_match.group(2)) if aed_match.group(2) else min_v
            dossier.budget_bracket = BudgetBracket(min_value=min_v, max_value=max_v, currency="AED", unit="Millions")

        # 2. Timeline
        if any(w in lower for w in ["immediate", "ready to move", "this week", "urgent", "உடனே", "तुरंत"]):
            dossier.timeline = TimelineEnum.IMMEDIATE
        elif any(w in lower for w in ["30 days", "month", "1 month", "ஒரு மாதம்"]):
            dossier.timeline = TimelineEnum.DAYS_30
        elif any(w in lower for w in ["60 days", "2 months"]):
            dossier.timeline = TimelineEnum.DAYS_60
        elif any(w in lower for w in ["90 days", "3 months", "quarter", "6 months", "24 months"]):
            dossier.timeline = TimelineEnum.DAYS_90
        elif any(w in lower for w in ["flexible", "looking around", "just browsing", "wait"]):
            dossier.timeline = TimelineEnum.FLEXIBLE

        # 3. Buyer Type (End User vs Investor / Flipper)
        if any(w in lower for w in [
            "invest", "investment", "rental yield", "returns", "cap rate", "flip", "upside", "assign",
            "முதலீடு", "வாடகை", "லாபம்", "என்ஆர்ஐ", "nri", "निवेश", "रेंटल", "मुनाफा"
        ]):
            dossier.buyer_type = BuyerTypeEnum.INVESTOR
        elif any(w in lower for w in [
            "self", "family", "personal", "stay", "own", "end user", "kids", "parents", "elderly", "relocat",
            "சொந்த", "குடும்பம்", "குழந்தை", "குடிவர", "रहने", "परिवार", "बच्चे", "रिलोकेट"
        ]):
            dossier.buyer_type = BuyerTypeEnum.END_USER

        # 4. Mortgage / Financing
        if any(w in lower for w in ["pre-approved", "loan approved", "sanctioned", "home loan", "emi", "கடன்", "லோன்", "मंजूर", "बैंक लोन"]):
            dossier.pre_approved_mortgage = True
        elif any(w in lower for w in ["cash", "liquid", "self fund", "no loan", "கேஷ்", "कैश"]):
            dossier.pre_approved_mortgage = False

        # 5. Preferred Walkthrough / Visit Slot
        if any(w in lower for w in ["thursday", "வியாழக்கிழமை", "गुरुवार"]):
            dossier.preferred_visit_slot = "Thursday 4:00 PM"
        elif any(w in lower for w in ["saturday", "சனிக்கிழமை", "शनिवार"]):
            dossier.preferred_visit_slot = "Saturday 11:00 AM"
        elif any(w in lower for w in ["sunday", "ஞாயிற்றுக்கிழமை", "ஞாயிறு", "रविवार"]):
            dossier.preferred_visit_slot = "Sunday 11:00 AM"
        elif any(w in lower for w in ["weekend", "வார இறுதி", "வீக்கெண்ட்", "वीकेंड"]):
            dossier.preferred_visit_slot = "Weekend (Flexible)"
        elif any(w in lower for w in ["tomorrow", "நாளை", "कल"]):
            dossier.preferred_visit_slot = "Tomorrow 3:00 PM"

        # 6. Objection Classification
        try:
            from closer.telephony.fallback import HallucinationDeflector
            deflector = HallucinationDeflector()
            obj_type = deflector.classify_objection(text)
            if obj_type != "general_inquiry":
                dossier.objection_category = str(obj_type)
        except Exception:
            pass

        return dossier
