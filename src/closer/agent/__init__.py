"""
Agent module for CLOSER AI (Amura Health Clinical & Hospital Front-Desk Engine).
"""

from src.closer.agent.clinical_guardrails import ClinicalSafetyGuardrails, SafetyDecision
from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.emotion import EmotionAssessment, EmotionDetector, PatientEmotion
from src.closer.agent.prompt import AMURA_CLINICAL_SYSTEM_PROMPT, ISA_SYSTEM_PROMPT, OBJECTION_PLAYBOOK
from src.closer.agent.schemas import (
    AppointmentBookingRequest,
    BuyerDossier,
    InboundLead,
    ObjectionRecord,
    PatientDossier,
)

__all__ = [
    "InboundLead",
    "PatientDossier",
    "BuyerDossier",
    "ObjectionRecord",
    "AppointmentBookingRequest",
    "AMURA_CLINICAL_SYSTEM_PROMPT",
    "ISA_SYSTEM_PROMPT",
    "OBJECTION_PLAYBOOK",
    "PatientEmotion",
    "EmotionAssessment",
    "EmotionDetector",
    "SafetyDecision",
    "ClinicalSafetyGuardrails",
    "ConversationEngine",
]
