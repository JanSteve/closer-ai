"""
Stateful turn-taking conversational engine with tool calling and Pydantic lead qualification extraction.
"""

from __future__ import annotations
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from src.closer.config import settings
from src.closer.agent.prompt import ISA_SYSTEM_PROMPT, OBJECTION_PLAYBOOK
from src.closer.agent.schemas import InboundLead, BuyerDossier, ObjectionRecord

logger = logging.getLogger(__name__)


class ConversationEngine:
    """
    Manages the live state of a qualification phone call.
    Handles user utterances, tool invocations, objection detection, and Pydantic dossier extraction.
    """

    def __init__(self, lead: Optional[InboundLead] = None):
        self.lead = lead or InboundLead(
            lead_id="sim_lead_001",
            full_name="Alex Morgan",
            phone_number="+1-310-555-0144",
            ad_campaign="Bel Air Sunset Modern Collection"
        )
        self.dossier = BuyerDossier(
            full_name=self.lead.full_name,
            phone_number=self.lead.phone_number,
            email=self.lead.email
        )
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": ISA_SYSTEM_PROMPT}
        ]
        self.objections_log: List[ObjectionRecord] = []
        self.turn_count = 0
        self.is_completed = False

    def get_initial_greeting(self) -> str:
        """Generates the sub-500ms initial call greeting."""
        first_name = self.lead.full_name.split()[0] if self.lead.full_name else "there"
        address_snippet = self.lead.listing_address or "our Bel Air estate showcase"
        
        greeting = (
            f"Hi {first_name}, this is Sophia with {settings.BROKERAGE_NAME}. "
            f"I noticed you just requested details on {address_snippet} — I wanted to catch you while it's top of mind. "
            f"Are you looking at this as a primary residence or a private investment?"
        )
        self.messages.append({"role": "assistant", "content": greeting})
        self.turn_count += 1
        return greeting

    def process_user_turn(self, user_utterance: str) -> str:
        """
        Receives buyer transcript turn, extracts qualification entities,
        handles objections if present, and returns the next ISA response.
        """
        clean_input = user_utterance.strip()
        self.messages.append({"role": "user", "content": clean_input})
        self.turn_count += 1
        
        # 1. Update dossier extraction from new utterance
        self._extract_entities(clean_input)
        
        # 2. Check for objection triggers
        objection_response = self._handle_objection(clean_input)
        if objection_response:
            self.messages.append({"role": "assistant", "content": objection_response})
            return objection_response
            
        # 3. Check for appointment scheduling request or confirmation
        booking_response = self._handle_booking_flow(clean_input)
        if booking_response:
            self.messages.append({"role": "assistant", "content": booking_response})
            return booking_response

        # 4. Standard qualification progression
        reply = self._generate_qualification_turn(clean_input)
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def _extract_entities(self, text: str) -> None:
        """Extracts budget, pre-approval, timeframe, and location from transcript."""
        t = text.lower()
        
        # Budget extraction
        # Ignore timeframe phrases like "1 to 3 months" or "30 days" so they don't corrupt budget values
        cleaned_budget_text = re.sub(r'\b\d+\s*(?:to|-)\s*\d+\s*(?:months?|weeks?|days?|years?)\b', '', t)
        cleaned_budget_text = re.sub(r'\b\d+\s*(?:months?|weeks?|days?|years?)\b', '', cleaned_budget_text)

        range_match = re.search(r'\$?(\d+(?:\.\d+)?)\s*(?:m\b|million\b)?\s*(?:to|-)\s*\$?(\d+(?:\.\d+)?)\s*(million\b|m\b)', cleaned_budget_text)
        if range_match:
            min_val = float(range_match.group(1)) * 1_000_000
            max_val = float(range_match.group(2)) * 1_000_000
            self.dossier.budget_min = int(min_val)
            self.dossier.budget_max = int(max_val)
        else:
            single_match = re.search(r'(?:\$|\bbudget\s*(?:is|of)?\s*)\s*(\d+(?:\.\d+)?)\s*(million\b|mil\b|m\b|k\b)?', cleaned_budget_text)
            if single_match:
                val = float(single_match.group(1))
                unit = (single_match.group(2) or "").lower()
                multiplier = 1_000_000 if ("m" in unit or val < 100) else (1_000 if "k" in unit else 1)
                amount = int(val * multiplier)
                if amount >= 100_000:
                    self.dossier.budget_max = amount
                    if not self.dossier.budget_min:
                        self.dossier.budget_min = int(amount * 0.8)
            else:
                digits = re.findall(r'\$?([1-9]\d{5,8})', cleaned_budget_text)
                if digits:
                    val = int(digits[0])
                    self.dossier.budget_max = val
                    self.dossier.budget_min = int(val * 0.8)

        # Pre-approval / Financing
        if any(w in t for w in ["all cash", "paying cash", "cash buyer", "liquid"]):
            self.dossier.pre_approved = True
            self.dossier.financing_type = "cash"
            self.dossier.qualification_reasons.append("Verified all-cash buyer")
        elif any(w in t for w in ["pre-approved", "pre approved", "preapproval", "bank approved"]):
            self.dossier.pre_approved = True
            self.dossier.financing_type = "pre_approved_jumbo"
            self.dossier.qualification_reasons.append("Pre-approved with lender")
        elif any(w in t for w in ["haven't talked", "not approved", "no pre-approval", "haven't spoken"]):
            self.dossier.pre_approved = False
            self.dossier.financing_type = "needs_lender_intro"

        # Timeframe
        if re.search(r'\b(immediately|asap|this month|30 days|right away)\b', t):
            self.dossier.timeframe = "immediate (0-30 days)"
        elif re.search(r'\b(1\s*(?:to|-)\s*[23]\s*months?|next month|couple months?|60 days)\b', t):
            self.dossier.timeframe = "1-3 months"
        elif re.search(r'\b(3\s*(?:to|-)\s*6\s*months?|summer|fall|by the end of the year)\b', t):
            self.dossier.timeframe = "3-6 months"
        elif re.search(r'\b(just looking|browsing|year or two|not in a rush)\b', t):
            self.dossier.timeframe = "browsing (6+ months)"

        # Target locations
        for loc in ["Beverly Hills", "Bel Air", "Malibu", "Brentwood", "Holmby Hills", "Pacific Palisades", "Tribeca", "Miami Beach"]:
            if loc.lower() in t and loc not in self.dossier.target_locations:
                self.dossier.target_locations.append(loc)

        # Property type
        if "penthouse" in t:
            self.dossier.property_type = "Penthouse"
        elif any(w in t for w in ["villa", "estate", "single family", "mansion"]):
            self.dossier.property_type = "Luxury Estate"
        elif "modern" in t or "contemporary" in t:
            self.dossier.property_type = "Modern Architectural"

        # Email detection
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            self.dossier.email = email_match.group(0)

        # Re-evaluate qualification score
        self._score_lead()

    def _score_lead(self) -> None:
        """Computes intent score (0-100) and marks qualification boolean."""
        score = 40
        reasons = []

        # Budget scoring
        if self.dossier.budget_max:
            if self.dossier.budget_max >= 5_000_000:
                score += 30
                reasons.append("Ultra-luxury budget ($5M+)")
            elif self.dossier.budget_max >= 2_000_000:
                score += 20
                reasons.append("Core luxury budget ($2M - $5M)")
            elif self.dossier.budget_max >= 1_000_000:
                score += 10
            else:
                score -= 20
                reasons.append("Budget below luxury threshold (<$1M)")

        # Financing scoring
        if self.dossier.financing_type == "cash":
            score += 20
            reasons.append("Cash verification adds high conversion confidence")
        elif self.dossier.pre_approved is True:
            score += 15
            reasons.append("Pre-approval verified")
        elif self.dossier.pre_approved is False:
            score -= 5

        # Timeline scoring
        if self.dossier.timeframe in ("immediate (0-30 days)", "1-3 months"):
            score += 20
            reasons.append("High urgency timeline (<= 90 days)")
        elif self.dossier.timeframe == "3-6 months":
            score += 10
        elif self.dossier.timeframe == "browsing (6+ months)":
            score -= 5

        # Objections handled bonus
        if self.dossier.objections_handled:
            score += 5

        self.dossier.intent_score = min(100, max(0, score))
        
        # Qualified logic: Must have budget >= $1.5M (or cash/pre-approved) and reasonable timeframe
        budget_ok = (self.dossier.budget_max is not None and self.dossier.budget_max >= 1_500_000)
        time_ok = self.dossier.timeframe != "browsing (6+ months)"
        self.dossier.qualified = (budget_ok and (self.dossier.pre_approved is True or self.dossier.financing_type == "cash")) or (score >= 70)
        self.dossier.qualification_reasons = reasons

    def _handle_objection(self, text: str) -> Optional[str]:
        """Detects customer objection and generates tailored luxury response."""
        for key, data in OBJECTION_PLAYBOOK.items():
            if re.search(data["pattern"], text, re.IGNORECASE):
                if key not in self.dossier.objections_raised:
                    self.dossier.objections_raised.append(key)
                    self.dossier.objections_handled.append(data["handled_tag"])
                    self.objections_log.append(ObjectionRecord(
                        category=key,
                        buyer_statement=text,
                        isa_response=data["response"],
                        resolved=True
                    ))
                    return data["response"]
        return None

    def _handle_booking_flow(self, text: str) -> Optional[str]:
        """Handles appointment date/time negotiation and final confirmation."""
        t = text.lower()
        
        # Check if buyer mentions days or times
        has_day = any(d in t for d in ["tomorrow", "today", "thursday", "friday", "saturday", "sunday", "monday", "tuesday", "wednesday", "weekend"])
        has_time = any(tm in t for tm in ["pm", "am", "afternoon", "morning", "o'clock", "2", "3", "4", "10", "11"])
        
        if (has_day or has_time) and ("tour" in t or "see" in t or "meet" in t or "work" in t or "available" in t or "yes" in t or ":" in t):
            # Propose or confirm slot
            slot = self._parse_preferred_slot(text)
            self.dossier.appointment_datetime = slot
            self.dossier.appointment_type = "private_vip_tour"
            self.dossier.appointment_notes = f"VIP On-Site Tour at {self.lead.listing_address} with R Jan Steve Daniel"
            self.dossier.sentiment_rating = "Urgent"
            self.is_completed = True
            
            return (
                f"Perfect. I have reserved {slot} for your private VIP showing with {settings.REALTOR_NAME}. "
                f"I'm sending a calendar invite and security gate access instructions directly to your mobile. "
                f"We look forward to welcoming you!"
            )
            
        return None

    def _parse_preferred_slot(self, text: str) -> str:
        """Parses an appointment slot string like 'Tomorrow at 2:00 PM PST'."""
        t = text.lower()
        target_day = "Tomorrow"
        for day in ["Thursday", "Friday", "Saturday", "Monday", "Tuesday", "Wednesday"]:
            if day.lower() in t:
                target_day = f"This {day}"
                break
                
        hour_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', t)
        if hour_match:
            hr = hour_match.group(1)
            minute = hour_match.group(2) or "00"
            ampm = hour_match.group(3) or "PM"
            return f"{target_day} at {hr}:{minute} {ampm.upper()} PST"
        return f"{target_day} at 2:00 PM PST"

    def _generate_qualification_turn(self, clean_input: str) -> str:
        """Executes next conversational qualifying question."""
        # Step A: Need budget
        if not self.dossier.budget_max:
            return (
                "Understood. When acquiring in prime areas like Bel Air or Beverly Hills, "
                "our private clients usually look between $3 million to $10 million. "
                "What price comfort range are you aiming for?"
            )
            
        # Step B: Need financing / pre-approval
        if self.dossier.pre_approved is None and self.dossier.financing_type != "cash":
            return (
                "That's a fantastic price corridor with remarkable inventory right now. "
                "Will you be executing this purchase through liquid funds, or would you like "
                "our private banking desk to arrange financing?"
            )
            
        # Step C: Need timeline
        if not self.dossier.timeframe:
            return (
                "Understood. In terms of your moving schedule, are you hoping to secure a property "
                "in the next 30 to 60 days, or are you exploring for later this year?"
            )
            
        # Step D: Lock in the appointment
        if not self.dossier.appointment_datetime:
            return (
                f"Given what you've shared, {settings.REALTOR_NAME} is hosting private showings "
                f"at the estate this Thursday and Friday afternoon. Would 2:00 PM or 4:00 PM suit your schedule better?"
            )

        return (
            f"Wonderful. Everything is confirmed with {settings.REALTOR_NAME}. "
            "Please feel free to text this number anytime if you have questions before our appointment."
        )

    def export_dossier(self) -> BuyerDossier:
        """Returns the final structured qualification dossier."""
        self.dossier.total_turns = self.turn_count
        if not self.dossier.summary:
            budget_str = f"${self.dossier.budget_max:,}" if self.dossier.budget_max else "Not disclosed"
            self.dossier.summary = (
                f"Lead {self.dossier.full_name} qualified with intent score {self.dossier.intent_score}/100. "
                f"Budget: {budget_str}. Financing: {self.dossier.financing_type}. "
                f"Timeline: {self.dossier.timeframe or 'Flexible'}. "
                f"Appointment: {self.dossier.appointment_datetime or 'Pending follow-up'}."
            )
        return self.dossier
