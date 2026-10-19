"""
Integrations module for CLOSER AI: Google Calendar, Follow Up Boss CRM, and Twilio Telephony.
"""

from src.closer.integrations.calendar import CalendarManager
from src.closer.integrations.crm import CRMDispatcher
from src.closer.integrations.telephony import TelephonyManager

__all__ = [
    "CalendarManager",
    "CRMDispatcher",
    "TelephonyManager"
]
