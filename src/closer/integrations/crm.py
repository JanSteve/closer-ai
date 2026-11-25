"""
Clinical EHR & CRM Webhook Dispatcher for CLOSER AI (Amura Health).
Dispatches triaged patient dossiers, emotion & safety flags, consent state, and call recordings
to Practo Ray, KareXpert, HubSpot Health, or generic HMAC-signed webhooks.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.closer.agent.schemas import PatientDossier
from src.closer.config import settings

logger = logging.getLogger(__name__)


class CRMDispatcher:
    """
    Handles clinical EHR/CRM syncing for Amura Health & Hospital Front-Desk workflows.
    Supports Practo Ray, KareXpert, HubSpot, and generic HMAC-signed webhooks.
    """

    def __init__(
        self,
        fub_api_key: Optional[str] = None,
        webhook_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self.fub_api_key = fub_api_key or settings.CRM_API_KEY
        self.webhook_url = webhook_url or settings.CRM_WEBHOOK_URL
        self.webhook_secret = (webhook_secret or settings.WEBHOOK_SECRET).encode("utf-8")
        self.dispatched_events: List[Dict[str, Any]] = []

    def format_clinical_payload(
        self,
        dossier: PatientDossier,
        call_recording_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Formats structured clinical intake payload with emotion, safety, and DPDP consent metadata."""
        patient_name = dossier.patient_name or dossier.full_name or "Anonymous Patient"
        name_parts = patient_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        tags = ["#CLOSER-AI", "#Amura-Health", "#Voice-Triage"]
        if dossier.emergency_108:
            tags.append("#Emergency-108-Escalated")
        if dossier.qualified:
            tags.append("#Intake-Qualified")
        if dossier.consent_status == "granted":
            tags.append("#Consent-Granted")
        elif dossier.consent_status == "emergency_exempt_section_7f":
            tags.append("#DPDP-7f-Emergency")
        else:
            tags.append("#Consent-Pending")
        if dossier.appointment_datetime:
            tags.append("#Consult-Scheduled")

        if dossier.emergency_108:
            stage = "Emergency 108 Escalated"
        elif dossier.appointment_datetime:
            stage = "Consultation Scheduled"
        elif dossier.qualified:
            stage = "Clinically Triaged"
        else:
            stage = "Patient Inquiry"

        # Pre-compute fee line cleanly to prevent ternary precedence truncation
        if dossier.budget_max and dossier.budget_min:
            fee_line = f"Care Plan Estimate: {dossier.budget_currency} {dossier.budget_min:,} - {dossier.budget_max:,}\n"
        elif dossier.budget_inr_text:
            fee_line = f"Care Plan Estimate: {dossier.budget_inr_text}\n"
        else:
            fee_line = "Care Plan Estimate: Standard Consultation (₹1,500+)\n"

        biomarkers_str = ", ".join(dossier.biomarkers_mentioned) if dossier.biomarkers_mentioned else "None mentioned"
        areas_str = ", ".join(dossier.target_locations) if dossier.target_locations else "Velachery Chennai / Online Telehealth"
        rec_url = call_recording_url or "https://amura.ai/calls/rec_latest.wav"

        note_body = (
            f"=== AMURA HEALTH CLINICAL CALL DOSSIER ===\n"
            f"Clinic: {settings.CLINIC_NAME} ({settings.CLINIC_ADDRESS})\n"
            f"Attending Care Team: {settings.CLINICAL_DIRECTOR_NAME}\n"
            f"Patient: {patient_name} ({dossier.phone_number})\n"
            f"Chief Concern: {dossier.chief_concern or 'Metabolic & Chronic Care Evaluation'}\n"
            f"Condition Category: {dossier.condition_category or 'General Triage'} | Urgency: {dossier.triage_urgency}\n"
            f"Care Pathway: {dossier.care_pathway or 'Amura MNT + NMT Reversal'}\n"
            f"Biomarkers: {biomarkers_str}\n"
            f"Emotion: {dossier.detected_emotion} ({dossier.emotion_confidence:.2f}) | Empathy Tone: {dossier.empathy_tone}\n"
            f"Safety Flag: {dossier.safety_flag} | Emergency 108: {dossier.emergency_108}\n"
            f"DPDP Consent Status: {dossier.consent_status}\n"
            + fee_line
            + f"Payment Mode: {dossier.financing_type.upper()} (Verified: {dossier.pre_approved})\n"
            f"Timeframe: {dossier.timeframe}\n"
            f"Intent Score: {dossier.intent_score}/100 | Sentiment: {dossier.sentiment_rating}\n"
            f"Preferred Clinic / Mode: {areas_str}\n"
            f"Concerns Addressed: {len(dossier.objections_handled)}\n"
            f"Consultation Slot: {dossier.appointment_datetime or 'None'}\n"
            f"Follow-Up Note: {dossier.follow_up_note}\n"
            f"Summary: {dossier.summary}\n"
            f"Call Recording: {rec_url}\n"
        )

        return {
            "source": "CLOSER AI — Amura Health Clinical Voice Engine",
            "type": "Clinical Triage & Metabolic Intake",
            "message": note_body,
            "clinical_triage": {
                "chief_concern": dossier.chief_concern,
                "condition_category": dossier.condition_category,
                "triage_urgency": dossier.triage_urgency,
                "care_pathway": dossier.care_pathway,
                "detected_emotion": dossier.detected_emotion,
                "safety_flag": dossier.safety_flag,
                "emergency_108": dossier.emergency_108,
                "consent_status": dossier.consent_status,
                "consult_slot": dossier.appointment_datetime,
            },
            "person": {
                "firstName": first_name,
                "lastName": last_name,
                "emails": [{"value": dossier.email}] if dossier.email else [],
                "phones": [{"value": dossier.phone_number}] if dossier.phone_number else [],
                "tags": tags,
                "stage": stage,
                "care_plan_estimate_inr": dossier.budget_max or 1500,
            },
        }

    # Transitional alias for existing callers
    def format_fub_payload(
        self,
        dossier: PatientDossier,
        call_recording_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.format_clinical_payload(dossier, call_recording_url)

    def sign_payload(self, payload: Dict[str, Any]) -> str:
        """Computes HMAC-SHA256 signature for webhook payload verification."""
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        signature = hmac.new(self.webhook_secret, encoded, hashlib.sha256).hexdigest()
        return f"sha256={signature}"

    def dispatch(
        self,
        dossier: PatientDossier,
        call_recording_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Dispatches patient clinical dossier to EHR/CRM webhook."""
        payload = self.format_clinical_payload(dossier, call_recording_url)
        signature = self.sign_payload(payload)

        headers = {
            "Content-Type": "application/json",
            "X-Closer-Signature": signature,
            "X-Closer-Timestamp": datetime.now(timezone.utc).isoformat(),
        }

        network_dispatched = False
        if self.webhook_url and self.webhook_url.startswith("http"):
            try:
                import httpx

                resp = httpx.post(self.webhook_url, json=payload, headers=headers, timeout=3.0)
                network_dispatched = resp.status_code in (200, 201, 202)
            except Exception as e:
                logger.warning("CRM webhook dispatch network call failed: %s", e)

        patient_name = dossier.patient_name or dossier.full_name
        record = {
            "patient_name": patient_name,
            "lead_name": patient_name,
            "lead_phone": dossier.phone_number,
            "qualified": dossier.qualified,
            "intent_score": dossier.intent_score,
            "triage_urgency": dossier.triage_urgency,
            "emergency_108": dossier.emergency_108,
            "tags": payload["person"]["tags"],
            "signature": signature,
            "network_dispatched": network_dispatched,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        self.dispatched_events.append(record)
        return {
            "success": True,
            "event_id": f"evt_{hashlib.md5(signature.encode()).hexdigest()[:10]}",
            "tags_applied": payload["person"]["tags"],
            "stage": payload["person"]["stage"],
            "record": record,
        }
