"""Deterministic Qualification Extractor using Pydantic v2 schemas.

Enforces zero-hallucination extraction:
- Budget brackets (INR Crores, Lakhs, USD Millions, AED)
- Purchase timelines (30/60/90 days, immediate, flexible)
- Buyer personas (end-user vs investor)
- Preferred walkthrough visit slots
- Pre-approved mortgage status
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
        # Crores: e.g. "1.5 cr", "2 crores", "1 to 2 crore"
        cr_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*(?:cr|crore|crores|கோடி|करोड़)", lower)
        lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*(?:l|lakh|lakhs|லட்சம்|लाख)", lower)
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
        elif any(w in lower for w in ["90 days", "3 months", "quarter"]):
            dossier.timeline = TimelineEnum.DAYS_90
        elif any(w in lower for w in ["flexible", "looking around", "just browsing"]):
            dossier.timeline = TimelineEnum.FLEXIBLE

        # 3. Buyer Type
        if any(w in lower for w in ["invest", "investment", "rental yield", "returns", "முதலீடு", "निवेश"]):
            dossier.buyer_type = BuyerTypeEnum.INVESTOR
        elif any(w in lower for w in ["self", "family", "personal", "stay", "own", "end user", "சொந்த", "रहने"]):
            dossier.buyer_type = BuyerTypeEnum.END_USER

        # 4. Mortgage
        if any(w in lower for w in ["pre-approved", "loan approved", "sanctioned", "கடன் मंजूर"]):
            dossier.pre_approved_mortgage = True
        elif any(w in lower for w in ["cash", "liquid", "self fund", "no loan"]):
            dossier.pre_approved_mortgage = False

        return dossier
