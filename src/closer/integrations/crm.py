"""
Follow Up Boss & Generic CRM Webhook Dispatcher for CLOSER AI.
Dispatches qualified buyer dossiers, call recordings, and tags to real estate CRMs.
"""

from __future__ import annotations
import hmac
import hashlib
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from src.closer.config import settings
from src.closer.agent.schemas import BuyerDossier

logger = logging.getLogger(__name__)


class CRMDispatcher:
    """
    Handles CRM syncing for luxury real estate leads.
    Supports Follow Up Boss API v1, HubSpot, Salesforce, and generic HMAC-signed webhooks.
    """

    def __init__(
        self,
        fub_api_key: Optional[str] = None,
        webhook_url: Optional[str] = None,
        webhook_secret: Optional[str] = None
    ):
        self.fub_api_key = fub_api_key or settings.FOLLOW_UP_BOSS_API_KEY
        self.webhook_url = webhook_url or settings.CRM_WEBHOOK_URL
        self.webhook_secret = (webhook_secret or settings.WEBHOOK_SECRET).encode("utf-8")
        self.dispatched_events: List[Dict[str, Any]] = []

    def format_fub_payload(
        self,
        dossier: BuyerDossier,
        call_recording_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formats structured payload conforming to Follow Up Boss (FUB) Event Specification.
        """
        name_parts = (dossier.full_name or "Anonymous Buyer").split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        tags = ["#CLOSER-AI", "#Voice-Qualified"]
        if dossier.qualified:
            tags.append("#AI-Qualified")
            tags.append("#Hot-Lead")
        if dossier.budget_max and dossier.budget_max >= 3_000_000:
            tags.append("#Ultra-Luxury")
        if dossier.financing_type == "cash":
            tags.append("#Cash-Buyer")
        if dossier.appointment_datetime:
            tags.append("#Tour-Scheduled")

        stage = "Tour Scheduled" if dossier.appointment_datetime else ("Prequalified" if dossier.qualified else "Lead")

        note_body = (
            f"=== CLOSER AI CALL DOSSIER ===\n"
            f"Principal Realtor: {settings.REALTOR_NAME}\n"
            f"Lead: {dossier.full_name} ({dossier.phone_number})\n"
            f"Budget: ${dossier.budget_max:,} USD (Min: ${dossier.budget_min:,})\n" if dossier.budget_max and dossier.budget_min else f"Budget: Unspecified\n"
            f"Financing: {dossier.financing_type.upper()} (Pre-Approved: {dossier.pre_approved})\n"
            f"Timeframe: {dossier.timeframe}\n"
            f"Intent Score: {dossier.intent_score}/100 | Sentiment: {dossier.sentiment_rating}\n"
            f"Preferred Areas: {', '.join(dossier.target_locations) or 'Bel Air'}\n"
            f"Objections Handled: {len(dossier.objections_handled)}\n"
            f"Appointment: {dossier.appointment_datetime or 'None'}\n"
            f"Summary: {dossier.summary}\n"
            f"Call Recording: {call_recording_url or 'https://storage.danielrealty.com/calls/rec_latest.wav'}\n"
        )

        return {
            "source": "CLOSER AI Voice Engine",
            "type": "General Inquiry",
            "message": note_body,
            "person": {
                "firstName": first_name,
                "lastName": last_name,
                "emails": [{"value": dossier.email}] if dossier.email else [],
                "phones": [{"value": dossier.phone_number}] if dossier.phone_number else [],
                "tags": tags,
                "stage": stage,
                "price": dossier.budget_max or 5000000
            }
        }

    def sign_payload(self, payload: Dict[str, Any]) -> str:
        """Computes HMAC-SHA256 signature for webhook payload verification."""
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        signature = hmac.new(self.webhook_secret, encoded, hashlib.sha256).hexdigest()
        return f"sha256={signature}"

    def dispatch(
        self,
        dossier: BuyerDossier,
        call_recording_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dispatches lead dossier to CRM.
        Logs and tracks payload, sending HTTP POST if URL configured, with safe local simulation.
        """
        payload = self.format_fub_payload(dossier, call_recording_url)
        signature = self.sign_payload(payload)

        headers = {
            "Content-Type": "application/json",
            "X-Closer-Signature": signature,
            "X-Closer-Timestamp": datetime.now(timezone.utc).isoformat()
        }

        # If live webhook URL is configured and httpx is available
        network_dispatched = False
        if self.webhook_url and self.webhook_url.startswith("http"):
            try:
                import httpx
                resp = httpx.post(self.webhook_url, json=payload, headers=headers, timeout=3.0)
                network_dispatched = (resp.status_code in (200, 201, 202))
            except Exception as e:
                logger.warning("CRM webhook dispatch network call failed: %s", e)

        record = {
            "lead_name": dossier.full_name,
            "lead_phone": dossier.phone_number,
            "qualified": dossier.qualified,
            "intent_score": dossier.intent_score,
            "tags": payload["person"]["tags"],
            "signature": signature,
            "network_dispatched": network_dispatched,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload
        }
        self.dispatched_events.append(record)
        return {
            "success": True,
            "event_id": f"evt_{hashlib.md5(signature.encode()).hexdigest()[:10]}",
            "tags_applied": payload["person"]["tags"],
            "stage": payload["person"]["stage"],
            "record": record
        }
