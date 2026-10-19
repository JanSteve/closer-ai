"""
Agent module for CLOSER AI: prompt engineering, Pydantic schemas, and stateful turn engine.
"""

from src.closer.agent.schemas import InboundLead, BuyerDossier, ObjectionRecord, AppointmentBookingRequest
from src.closer.agent.prompt import ISA_SYSTEM_PROMPT, OBJECTION_PLAYBOOK
from src.closer.agent.conversation import ConversationEngine

__all__ = [
    "InboundLead",
    "BuyerDossier",
    "ObjectionRecord",
    "AppointmentBookingRequest",
    "ISA_SYSTEM_PROMPT",
    "OBJECTION_PLAYBOOK",
    "ConversationEngine"
]
