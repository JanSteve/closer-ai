"""
Post-Call Clinical Analysis & Doctor Dispatch (Email + WhatsApp) for Amura Health / CLOSER AI.
Analyzes each patient call and sends a structured clinical intake summary to the physician's
WhatsApp or Email, with live carrier/SMTP support and instant demo-ready links when offline.
"""

from __future__ import annotations

import os
import smtplib
import urllib.parse
import urllib.request
import json
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any, Dict, List, Optional


def analyze_call_for_doctor(
    dossier: Dict[str, Any],
    transcript: List[Dict[str, Any]],
    emotion_history: Optional[List[str]] = None,
    business_name: str = "Amura Health (Velachery, Chennai)",
) -> Dict[str, Any]:
    """Produces a structured clinical call analysis & doctor-ready brief."""
    patient_name = dossier.get("full_name") or "Patient Inquiry"
    phone = dossier.get("phone_number") or "Not provided"
    concern = dossier.get("chief_concern") or dossier.get("condition_category") or "Metabolic / OPD Consultation"
    biomarker = dossier.get("hba1c_or_biomarker") or "Not yet shared"
    urgency = dossier.get("triage_urgency") or ("Emergency 108" if dossier.get("emergency_108") else "Routine")
    slot = dossier.get("consult_slot") or dossier.get("appointment_datetime") or "Pending confirmation"
    consent = dossier.get("consent_status") or "pending"
    intent = dossier.get("intent_score", 0)
    emotions = [e for e in (emotion_history or []) if e] or [dossier.get("detected_emotion") or "calm"]
    dominant_emotion = emotions[-1]

    user_turns = [t.get("content", "") for t in (transcript or []) if t.get("role") == "user" and t.get("content")]
    key_quotes = " | ".join(user_turns[-3:]) if user_turns else (dossier.get("summary") or "Initial intake captured.")

    if dossier.get("emergency_108"):
        next_step = "URGENT: Patient reported red-flag symptoms; instructed to call 108 / ER immediately. Physician review advised."
    elif slot != "Pending confirmation":
        next_step = f"Confirmed for {slot}. Fasting lab checklist queued via WhatsApp."
    else:
        next_step = "Follow up to confirm physician tele-consultation slot and collect baseline HbA1c/thyroid labs."

    summary_lines = [
        f"=== {business_name} — DOCTOR CALL SUMMARY ===",
        f"Time (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
        f"Patient: {patient_name} ({phone})",
        f"Urgency: {urgency} | Intent: {intent}/100",
        f"Primary Concern: {concern}",
        f"Biomarkers / Labs: {biomarker}",
        f"Emotion Trajectory: {' -> '.join(emotions)} (Latest: {dominant_emotion})",
        f"Consult Slot: {slot}",
        f"DPDP Consent: {consent}",
        f"Patient Quotes: {key_quotes[:280]}",
        f"Recommended Action: {next_step}",
    ]
    formatted_text = "\n".join(summary_lines)

    return {
        "patient_name": patient_name,
        "patient_phone": phone,
        "urgency": urgency,
        "concern": concern,
        "biomarker": biomarker,
        "emotion_trajectory": emotions,
        "dominant_emotion": dominant_emotion,
        "consult_slot": slot,
        "consent_status": consent,
        "turn_count": len(transcript or []),
        "recommended_action": next_step,
        "summary_text": formatted_text,
        "email_subject": f"[{urgency}] Amura Patient Brief: {patient_name} — {concern}",
    }


def dispatch_to_doctor(
    brief: Dict[str, Any],
    channel: str = "both",
    doctor_email: Optional[str] = None,
    doctor_whatsapp: Optional[str] = None,
) -> Dict[str, Any]:
    """Dispatches the analyzed clinical summary to the doctor's WhatsApp and/or Email."""
    target_email = (doctor_email or os.getenv("DOCTOR_EMAIL") or "care@amura.ai").strip()
    target_wa = (doctor_whatsapp or os.getenv("DOCTOR_WHATSAPP") or "+919456750852").strip()
    wa_digits = "".join(ch for ch in target_wa if ch.isdigit())

    summary_text = brief["summary_text"]
    wa_link = f"https://wa.me/{wa_digits}?text={urllib.parse.quote(summary_text)}" if wa_digits else ""
    mailto_link = (
        f"mailto:{urllib.parse.quote(target_email)}"
        f"?subject={urllib.parse.quote(brief['email_subject'])}"
        f"&body={urllib.parse.quote(summary_text)}"
    )

    wa_status = "skipped"
    email_status = "skipped"

    if channel in ("whatsapp", "both"):
        wa_token = os.getenv("WHATSAPP_TOKEN", "")
        wa_phone_id = os.getenv("WHATSAPP_PHONE_ID", "")
        if wa_token and wa_phone_id and wa_digits:
            try:
                req = urllib.request.Request(
                    f"https://graph.facebook.com/v19.0/{wa_phone_id}/messages",
                    data=json.dumps({
                        "messaging_product": "whatsapp",
                        "to": wa_digits,
                        "type": "text",
                        "text": {"body": summary_text},
                    }).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {wa_token}",
                        "Content-Type": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    wa_status = "sent_live" if 200 <= resp.status < 300 else "queued_wa_link"
            except Exception:
                wa_status = "queued_wa_link"
        else:
            wa_status = "ready_wa_link"

    if channel in ("email", "both"):
        smtp_host = os.getenv("SMTP_HOST", "")
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASS", "")
        smtp_port = int(os.getenv("SMTP_PORT", "587") or 587)
        if smtp_host and smtp_user and smtp_pass:
            try:
                msg = EmailMessage()
                msg["Subject"] = brief["email_subject"]
                msg["From"] = smtp_user
                msg["To"] = target_email
                msg.set_content(summary_text)
                with smtplib.SMTP(smtp_host, smtp_port, timeout=6) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                email_status = "sent_live"
            except Exception:
                email_status = "ready_mailto_link"
        else:
            email_status = "ready_mailto_link"

    return {
        "success": True,
        "channel": channel,
        "doctor_email": target_email,
        "doctor_whatsapp": target_wa,
        "whatsapp_status": wa_status,
        "email_status": email_status,
        "whatsapp_link": wa_link,
        "mailto_link": mailto_link,
        "brief": brief,
    }
