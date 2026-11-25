"""
Clinical intake, patient triage, and conversation schemas for CLOSER AI (Amura Health).
Pydantic v2 compatible with seamless pure-Python fallback.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field, PrivateAttr

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

    def PrivateAttr(default=None) -> Any:
        return default

    class _PydanticBaseModel:
        """Lightweight Pydantic v2 compatible BaseModel shim when pydantic is not installed."""

        def __init__(self, **kwargs):
            annotations = getattr(self.__class__, "__annotations__", {})
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
    """Represents an inbound patient inquiry captured from clinic web forms, telehealth, or WhatsApp webhooks."""

    lead_id: str
    source: str = "amura_web_intake"  # amura_web_intake, hospital_front_desk, whatsapp_care, referral
    full_name: str
    phone_number: str
    email: Optional[str] = None
    market_region: str = "INDIA"  # "INDIA", "TAMIL", "HINDI", "ENGLISH"
    ad_campaign: Optional[str] = "Amura Health Metabolic Reversal & Front-Desk Triage"
    clinic_location: Optional[str] = "11th Floor, One National Park, 142 Velachery Main Road, Chennai - 600042"
    primary_concern: Optional[str] = None
    preferred_language: str = "english"
    listing_address: Optional[str] = None
    listing_price: Optional[int] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None


class ObjectionRecord(_PydanticBaseModel):
    """Tracks a patient concern or scheduling friction point and how Amura AI handled it."""

    category: str  # "program_skepticism", "has_physician", "async_whatsapp", "cost_clarity", "timing_hesitation"
    buyer_statement: str
    isa_response: str
    resolved: bool = True
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def patient_statement(self) -> str:
        return self.buyer_statement

    @property
    def agent_response(self) -> str:
        return self.isa_response


class PatientDossier(_PydanticBaseModel):
    """
    Extracted clinical intake, emotional intelligence, safety, and appointment dossier
    for Amura Health metabolic & chronic-care workflows and hospital front-desk triage.
    """

    patient_name: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    market_region: str = "INDIA"
    customer_type: str = "patient"  # "patient", "existing_patient", "support_query", "caregiver"

    # Clinical Intake & Triage Fields (PROJECT.md Contract #3)
    chief_concern: Optional[str] = None
    condition_category: Optional[str] = None  # metabolic_diabetes, pcod_hormonal, thyroid, fatty_liver, hypertension, gut_health, hospital_triage
    triage_urgency: str = "Routine"  # "Routine", "Priority", "Emergency 108"
    care_pathway: Optional[str] = None  # "Amura MNT + NMT Reversal", "Physician Consult", "Hospital OPD", "Emergency 108"
    biomarkers_mentioned: List[str] = Field(default_factory=list)
    consent_status: str = "pending"  # "pending", "granted", "declined", "emergency_exempt_section_7f"

    # Emotion & Clinical Safety
    detected_emotion: str = "calm"
    emotion_confidence: float = 0.85
    empathy_tone: str = "empathetic"
    safety_flag: str = "safe"
    emergency_108: bool = False

    # Care Plan & Consultation Fee Context
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    budget_currency: str = "INR"
    budget_inr_text: Optional[str] = None
    pre_approved: Optional[bool] = None
    financing_type: str = "care_plan"  # care_plan, insurance, corporate_wellness, self_pay, emi

    # Timeline & Location Preferences
    timeframe: Optional[str] = None
    target_locations: List[str] = Field(default_factory=list)

    # Front-Desk Support & WhatsApp Care Coordination
    ticket_id: Optional[str] = None
    query_type: Optional[str] = None
    query_resolved: bool = False
    whatsapp_dispatched: bool = False
    whatsapp_status: Optional[str] = None

    # Readiness & Intent Scoring
    intent_score: int = 50
    qualified: bool = False
    qualification_reasons: List[str] = Field(default_factory=list)
    response_latency_tier: Optional[str] = None
    disfluency_type: Optional[str] = None

    # Concerns & Sentiment
    objections_raised: List[str] = Field(default_factory=list)
    objections_handled: List[str] = Field(default_factory=list)
    sentiment_rating: str = "Neutral"

    # Consultation Scheduling & Follow-Up
    consult_slot: Optional[str] = None
    appointment_datetime: Optional[str] = None
    appointment_type: Optional[str] = None  # tele_consultation, clinic_consultation, phone_consultation
    appointment_notes: Optional[str] = None
    follow_up_note: str = (
        "Amura Health front-desk intake initialized; WhatsApp care coordinator available (+91-62-622-62222)."
    )
    preferred_channel: Optional[str] = None

    # Open-Source Foundation LLM Telemetry
    active_llm_model: Optional[str] = "llama-3.3-70b"
    llm_parameter_scale: Optional[str] = "70 Billion"
    llm_latency_ms: Optional[int] = None
    llm_tier: Optional[str] = "reflex_edge"

    # Call Metrics
    call_duration_seconds: int = 0
    total_turns: int = 0
    summary: Optional[str] = None
    speed_to_lead_ms: int = 420

    # Private transitional attributes (excluded from model_dump())
    _bant_authority: Optional[str] = PrivateAttr(default=None)
    _bant_budget: bool = PrivateAttr(default=False)

    def __init__(self, **data: Any):
        bant_auth = data.pop("bant_authority_verified", data.pop("bant_authority", None))
        bant_need = data.pop("bant_need_identified", data.pop("bant_need", None))
        bant_budget = data.pop("bant_budget_qualified", data.pop("bant_budget", None))
        bant_timeline = data.pop("bant_timeline_confirmed", data.pop("bant_timeline", None))
        data.pop("tax_exchange_1031", None)
        data.pop("exchange_deadline_days", None)
        data.pop("bhk_preference", None)
        data.pop("property_type", None)
        data.pop("lender_name", None)
        data.pop("bedroom_min", None)

        if data.get("patient_name") is None and data.get("full_name"):
            data["patient_name"] = data["full_name"]
        elif data.get("full_name") is None and data.get("patient_name"):
            data["full_name"] = data["patient_name"]

        if data.get("consult_slot") is None and data.get("appointment_datetime"):
            data["consult_slot"] = data["appointment_datetime"]
        elif data.get("appointment_datetime") is None and data.get("consult_slot"):
            data["appointment_datetime"] = data["consult_slot"]

        if not data.get("follow_up_note"):
            data["follow_up_note"] = (
                "Amura Health front-desk intake initialized; WhatsApp care coordinator available (+91-62-622-62222)."
            )

        if bant_need and not data.get("chief_concern"):
            data["chief_concern"] = bant_need
        if bant_timeline and not data.get("timeframe"):
            data["timeframe"] = bant_timeline

        super().__init__(**data)

        if bant_auth is not None:
            self._bant_authority = bant_auth
        if bant_budget is not None:
            self._bant_budget = bool(bant_budget)

    # Transitional @property shims (never serialized in model_dump())
    @property
    def bant_authority_verified(self) -> Optional[str]:
        return getattr(self, "_bant_authority", None)

    @bant_authority_verified.setter
    def bant_authority_verified(self, value: Optional[str]) -> None:
        self._bant_authority = value

    @property
    def bant_authority(self) -> Optional[str]:
        return self.bant_authority_verified

    @bant_authority.setter
    def bant_authority(self, value: Optional[str]) -> None:
        self.bant_authority_verified = value

    @property
    def bant_need_identified(self) -> Optional[str]:
        return self.chief_concern

    @bant_need_identified.setter
    def bant_need_identified(self, value: Optional[str]) -> None:
        self.chief_concern = value

    @property
    def bant_need(self) -> Optional[str]:
        return self.chief_concern

    @bant_need.setter
    def bant_need(self, value: Optional[str]) -> None:
        self.chief_concern = value

    @property
    def bant_budget_qualified(self) -> bool:
        return bool(getattr(self, "_bant_budget", False) or self.qualified)

    @bant_budget_qualified.setter
    def bant_budget_qualified(self, value: bool) -> None:
        self._bant_budget = bool(value)

    @property
    def bant_budget(self) -> bool:
        return self.bant_budget_qualified

    @bant_budget.setter
    def bant_budget(self, value: bool) -> None:
        self.bant_budget_qualified = value

    @property
    def bant_timeline_confirmed(self) -> Optional[str]:
        return self.timeframe

    @bant_timeline_confirmed.setter
    def bant_timeline_confirmed(self, value: Optional[str]) -> None:
        self.timeframe = value

    @property
    def bant_timeline(self) -> Optional[str]:
        return self.timeframe

    @bant_timeline.setter
    def bant_timeline(self, value: Optional[str]) -> None:
        self.timeframe = value


# Transitional alias for legacy callers (main.py, integrations, older tests)
BuyerDossier = PatientDossier


class AppointmentBookingRequest(_PydanticBaseModel):
    """Request payload to book an Amura Health consultation slot."""

    lead_name: str
    lead_phone: str
    lead_email: Optional[str] = None
    slot_datetime: str
    clinician_name: str = "Dr. Godwin Samuel Christudas & Amura Care Team"
    realtor_name: str = "Dr. Godwin Samuel Christudas & Amura Care Team"
    clinic_location: Optional[str] = "11th Floor, One National Park, 142 Velachery Main Road, Chennai - 600042"
    property_address: Optional[str] = None
    notes: Optional[str] = None


class CallSessionState(_PydanticBaseModel):
    """Real-time telephony state of an ongoing clinical voice call."""

    session_id: str
    lead_id: str
    status: str = "IDLE"  # IDLE, DIALING, CONNECTED, LISTENING, THINKING, SPEAKING, COMPLETED, FAILED
    caller_phone: str
    recipient_phone: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    transcript: List[Dict[str, str]] = Field(default_factory=list)
    dossier: PatientDossier = Field(default_factory=PatientDossier)
    interrupted_count: int = 0
    average_stt_latency_ms: float = 0.0
    average_llm_latency_ms: float = 0.0
    average_tts_latency_ms: float = 0.0
    latency_tier: Optional[str] = "conversational"
    target_latency_ms: Optional[int] = 180
