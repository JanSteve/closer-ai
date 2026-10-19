"""
Lead qualification and conversation schemas for CLOSER AI.
Pydantic v2 compatible with seamless pure-Python fallback.
"""

from __future__ import annotations
import json
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field
    _HAS_PYDANTIC = True
except ImportError:
    _HAS_PYDANTIC = False
    
    class _FieldInfo:
        def __init__(self, default=None, default_factory=None, description=""):
            self.default = default
            self.default_factory = default_factory
            self.description = description

        def get_value(self) -> Any:
            if self.default_factory is not None:
                return self.default_factory()
            if isinstance(self.default, list):
                return list(self.default)
            if isinstance(self.default, dict):
                return dict(self.default)
            return self.default

    def Field(default=None, default_factory=None, description="") -> Any:
        return _FieldInfo(default=default, default_factory=default_factory, description=description)

    class _PydanticBaseModel:
        """Lightweight Pydantic v2 compatible BaseModel shim when pydantic is not installed."""
        def __init__(self, **kwargs):
            annotations = getattr(self.__class__, "__annotations__", {})
            # Set default values from class attributes
            for k in annotations:
                if hasattr(self.__class__, k):
                    val = getattr(self.__class__, k)
                    if isinstance(val, _FieldInfo):
                        val = val.get_value()
                    elif isinstance(val, list):
                        val = list(val)
                    elif isinstance(val, dict):
                        val = dict(val)
                    setattr(self, k, val)
                else:
                    setattr(self, k, None)
            
            # Set kwargs
            for k, v in kwargs.items():
                setattr(self, k, v)

        def model_dump(self, mode: str = "python") -> Dict[str, Any]:
            annotations = getattr(self.__class__, "__annotations__", {})
            out = {}
            for k in annotations:
                val = getattr(self, k, None)
                if isinstance(val, _PydanticBaseModel):
                    out[k] = val.model_dump(mode=mode)
                elif isinstance(val, list):
                    out[k] = [item.model_dump(mode=mode) if isinstance(item, _PydanticBaseModel) else item for item in val]
                elif isinstance(val, dict):
                    out[k] = {ik: iv.model_dump(mode=mode) if isinstance(iv, _PydanticBaseModel) else iv for ik, iv in val.items()}
                else:
                    out[k] = val
            return out

        def dict(self, *args, **kwargs) -> Dict[str, Any]:
            return self.model_dump()

        def model_dump_json(self, indent: Optional[int] = None) -> str:
            return json.dumps(self.model_dump(), indent=indent, default=str)

        def json(self, *args, **kwargs) -> str:
            return self.model_dump_json()

        @classmethod
        def model_validate(cls, obj: Any) -> Any:
            if isinstance(obj, cls):
                return obj
            if isinstance(obj, dict):
                return cls(**obj)
            raise ValueError(f"Cannot validate {type(obj)} into {cls.__name__}")

        @classmethod
        def parse_obj(cls, obj: Any) -> Any:
            return cls.model_validate(obj)

        def __repr__(self) -> str:
            fields = ", ".join(f"{k}={getattr(self, k)!r}" for k in getattr(self.__class__, "__annotations__", {}))
            return f"{self.__class__.__name__}({fields})"


class InboundLead(_PydanticBaseModel):
    """Represents an inbound real estate lead captured from ads, Zillow, or webhooks."""
    lead_id: str
    source: str = "instagram_ad"  # instagram_ad, zillow, website_webhook, referral
    full_name: str
    phone_number: str
    email: Optional[str] = None
    ad_campaign: Optional[str] = "Luxury Estates Showcase - Bel Air & Beverly Hills"
    listing_address: Optional[str] = "10484 Bellagio Rd, Bel Air, CA"
    listing_price: Optional[int] = 6850000
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None


class ObjectionRecord(_PydanticBaseModel):
    """Tracks an objection raised by the buyer and how CLOSER AI handled it."""
    category: str  # "just_browsing", "has_agent", "need_email_only", "unqualified_finances", "timing_hesitation"
    buyer_statement: str
    isa_response: str
    resolved: bool = True
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BuyerDossier(_PydanticBaseModel):
    """
    Extracted qualification profile of the real estate lead.
    Matches the prompt's required specification:
    full_name, phone_number, budget_min, budget_max, pre_approved (bool),
    timeframe (str), qualified (bool), appointment_datetime (optional).
    """
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    
    # Financial Capacity
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    budget_currency: str = "USD"
    pre_approved: Optional[bool] = None
    lender_name: Optional[str] = None
    financing_type: str = "conventional"  # cash, jumbo_loan, conventional, private_banking
    
    # Timeline & Property Preferences
    timeframe: Optional[str] = None  # immediate, 1-3_months, 3-6_months, 6-12_months, browsing
    property_type: Optional[str] = None  # single_family, penthouse, architectural, gated_estate
    target_locations: List[str] = Field(default_factory=list)
    bedroom_min: Optional[int] = None
    
    # Qualification Status
    intent_score: int = 50  # 0 to 100
    qualified: bool = False
    qualification_reasons: List[str] = Field(default_factory=list)
    
    # Objections & Sentiment
    objections_raised: List[str] = Field(default_factory=list)
    objections_handled: List[str] = Field(default_factory=list)
    sentiment_rating: str = "Neutral"  # Positive, Urgency, Hesitant, Skeptical, Neutral
    
    # Booking & Dispatch
    appointment_datetime: Optional[str] = None
    appointment_type: Optional[str] = None  # private_vip_tour, zoom_buyer_strategy, phone_consultation
    appointment_notes: Optional[str] = None
    
    # Call Metrics
    call_duration_seconds: int = 0
    total_turns: int = 0
    summary: Optional[str] = None
    speed_to_lead_ms: int = 420


class AppointmentBookingRequest(_PydanticBaseModel):
    """Request payload to book a calendar slot."""
    lead_name: str
    lead_phone: str
    lead_email: Optional[str] = None
    slot_datetime: str
    realtor_name: str = "R Jan Steve Daniel"
    property_address: Optional[str] = None
    notes: Optional[str] = None


class CallSessionState(_PydanticBaseModel):
    """Real-time telephony state of an ongoing voice call."""
    session_id: str
    lead_id: str
    status: str = "IDLE"  # IDLE, DIALING, CONNECTED, LISTENING, THINKING, SPEAKING, COMPLETED, FAILED
    caller_phone: str
    recipient_phone: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    transcript: List[Dict[str, str]] = Field(default_factory=list)
    dossier: BuyerDossier = Field(default_factory=BuyerDossier)
    interrupted_count: int = 0
    average_stt_latency_ms: float = 0.0
    average_llm_latency_ms: float = 0.0
    average_tts_latency_ms: float = 0.0
