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
from src.closer.agent.prompt import (
    ISA_SYSTEM_PROMPT,
    OBJECTION_PLAYBOOK,
    FRICTION_PLAYBOOK,
    INDIA_CUSTOMER_CARE_SYSTEM_PROMPT,
    INDIA_QUERY_PLAYBOOK,
    INDIA_FRICTION_PLAYBOOK,
    HINDI_CUSTOMER_CARE_SYSTEM_PROMPT,
    HINDI_QUERY_PLAYBOOK,
    HINDI_FRICTION_PLAYBOOK
)
from src.closer.agent.schemas import InboundLead, BuyerDossier, ObjectionRecord
from src.closer.llm.router import OpenLLMRouter

logger = logging.getLogger(__name__)


class ConversationEngine:
    """
    Manages the live state of a qualification phone call.
    Handles user utterances, tool invocations, objection detection, and Pydantic dossier extraction.
    Supports 3 Main Global Languages: US Luxury Real Estate ISA, India Customer Care, and Native Hindi Closing.
    """

    def __init__(self, lead: Optional[InboundLead] = None, market_mode: str = "usa"):
        self.lead = lead or InboundLead(
            lead_id="sim_lead_001",
            full_name="Alex Morgan",
            phone_number="+1-310-555-0144",
            ad_campaign="Bel Air Sunset Modern Collection"
        )
        if lead and getattr(lead, "market_region", None):
            if "hindi" in str(lead.market_region).lower():
                market_mode = "hindi"
            elif "india" in str(lead.market_region).lower() and market_mode == "usa":
                market_mode = "india"

        self._market_mode = market_mode.lower().strip()
        if self._market_mode in ("hindi", "hi", "hi-in"):
            region = "INDIA"
            currency = "INR"
            sys_prompt = HINDI_CUSTOMER_CARE_SYSTEM_PROMPT
        elif self._market_mode in ("india", "en-in"):
            region = "INDIA"
            currency = "INR"
            sys_prompt = INDIA_CUSTOMER_CARE_SYSTEM_PROMPT
        else:
            region = "USA"
            currency = "USD"
            sys_prompt = ISA_SYSTEM_PROMPT

        self.dossier = BuyerDossier(
            full_name=self.lead.full_name,
            phone_number=self.lead.phone_number,
            email=self.lead.email,
            market_region=region,
            budget_currency=currency
        )
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": sys_prompt}
        ]
        self.objections_log: List[ObjectionRecord] = []
        self.turn_count = 0
        self.is_completed = False
        self.llm_router = OpenLLMRouter()
        self.dossier.active_llm_model = self.llm_router.active_model_id
        self.dossier.llm_parameter_scale = self.llm_router.active_profile.parameter_scale

    @property
    def market_mode(self) -> str:
        return self._market_mode

    @market_mode.setter
    def market_mode(self, mode: str) -> None:
        self.set_market_mode(mode)

    def set_llm_model(self, model_id_or_alias: str) -> Dict[str, Any]:
        """Dynamically switches the active open-source foundation model (e.g., bloomz-176b, llama-3.3-70b)."""
        if self.llm_router:
            self.llm_router.set_active_model(model_id_or_alias)
            info = self.llm_router.get_active_model_info()
            self.dossier.active_llm_model = self.llm_router.active_model_id
            self.dossier.llm_parameter_scale = self.llm_router.active_profile.parameter_scale
            return info
        return {}

    def set_market_mode(self, mode: str) -> None:
        """Dynamically switches between 'usa', 'india', and 'hindi' market modes."""
        m = mode.lower().strip()
        self._market_mode = m
        if m in ("hindi", "hi", "hi-in"):
            self.dossier.market_region = "INDIA"
            self.dossier.budget_currency = "INR"
            self.messages = [{"role": "system", "content": HINDI_CUSTOMER_CARE_SYSTEM_PROMPT}]
        elif m in ("india", "en-in"):
            self.dossier.market_region = "INDIA"
            self.dossier.budget_currency = "INR"
            self.messages = [{"role": "system", "content": INDIA_CUSTOMER_CARE_SYSTEM_PROMPT}]
        else:
            self.dossier.market_region = "USA"
            self.dossier.budget_currency = "USD"
            self.messages = [{"role": "system", "content": ISA_SYSTEM_PROMPT}]

    def get_initial_greeting(self) -> str:
        """Generates the sub-500ms initial call greeting across the 3 main languages."""
        if self.market_mode == "hindi":
            greeting = (
                "नमस्ते जी! क्लोज़र एआई कस्टमर सपोर्ट में आपका स्वागत है। मैं स्वाति बात कर रही हूँ। "
                "मैं आपकी प्रॉपर्टी इंक्वायरी और साइट विज़िट में किस प्रकार सहायता कर सकती हूँ?"
            )
            self.messages.append({"role": "assistant", "content": greeting})
            self.turn_count += 1
            return greeting

        if self.market_mode == "india":
            first_name = self.lead.full_name.split()[0] if self.lead.full_name else "Sir"
            greeting = (
                f"Namaste {first_name}, this is Priya from {settings.BROKERAGE_NAME} Customer Care & Client Relations. "
                f"Thank you for contacting us — I'm following up on your recent inquiry. How may I assist you today?"
            )
            self.messages.append({"role": "assistant", "content": greeting})
            self.turn_count += 1
            return greeting

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
        handles script deviations & schedule friction, handles objections,
        and returns the next agent response.
        """
        clean_input = user_utterance.strip()
        self.messages.append({"role": "user", "content": clean_input})
        self.turn_count += 1
        
        # 1. Update dossier extraction from new utterance
        self._extract_entities(clean_input)
        
        # In Hindi Mode: Route to dedicated Hindi customer care and closing engine
        if self.market_mode == "hindi":
            hindi_reply = self._process_hindi_turn(clean_input)
            self._update_telemetry(clean_input, hindi_reply)
            self.messages.append({"role": "assistant", "content": hindi_reply})
            return hindi_reply

        # In India Customer Care Mode: Route to dedicated Indian customer care engine
        if self.market_mode == "india":
            india_reply = self._process_india_turn(clean_input)
            self._update_telemetry(clean_input, india_reply)
            self.messages.append({"role": "assistant", "content": india_reply})
            return india_reply

        # 2. Autonomous rational concierge: handle script deviations, schedule friction & busy constraints
        deviation_response = self._handle_script_deviation(clean_input)
        if deviation_response:
            self._update_telemetry(clean_input, deviation_response)
            self.messages.append({"role": "assistant", "content": deviation_response})
            return deviation_response

        # 3. Check for objection triggers
        objection_response = self._handle_objection(clean_input)
        if objection_response:
            self._update_telemetry(clean_input, objection_response)
            self.messages.append({"role": "assistant", "content": objection_response})
            return objection_response
            
        # 4. Check for appointment scheduling request or confirmation
        booking_response = self._handle_booking_flow(clean_input)
        if booking_response:
            self._update_telemetry(clean_input, booking_response)
            self.messages.append({"role": "assistant", "content": booking_response})
            return booking_response

        # 5. Standard qualification progression
        reply = self._generate_qualification_turn(clean_input)
        self._update_telemetry(clean_input, reply)
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def _update_telemetry(self, user_text: str, agent_reply: str) -> None:
        """Profiles latency tier and disfluency telemetry based on Google Duplex principles."""
        t_low = user_text.lower()
        is_reflex = bool(re.search(
            r"^(hello\??|hi\??|hey\??|can you hear me\??|are you there\??|you there\??|yeah\??|yes\??|yep\??|speaking\??|uh-huh\??|haanji\??|namaste\??)\b",
            t_low
        )) and len(user_text.split()) <= 4
        is_complex = any(k in t_low for k in ["tomorrow", "busy", "meeting", "1031", "rera", "complaint", "ticket", "site visit", "विज़िट", "शिकायत", "aspen", "jumbo", "financing"])

        if is_reflex:
            self.dossier.response_latency_tier = "reflex_sync"
            self.dossier.disfluency_type = "acknowledgment"
        elif is_complex:
            self.dossier.response_latency_tier = "cognitive_paced"
            self.dossier.disfluency_type = "cognitive_hesitation"
        else:
            self.dossier.response_latency_tier = "conversational"
            self.dossier.disfluency_type = "acknowledgment"

        if agent_reply and ("— or actually" in agent_reply.lower() or "or actually" in agent_reply.lower()):
            self.dossier.disfluency_type = "self_correction"

    def _process_india_turn(self, clean_input: str) -> str:
        """Processes turn under India Customer Care & Lead Support mode."""
        t = clean_input.lower()

        # 1. Check Indian Friction Playbook
        for key, play in INDIA_FRICTION_PLAYBOOK.items():
            if re.search(play["pattern"], t):
                tag = play["handled_tag"]
                if tag not in self.dossier.objections_handled:
                    self.dossier.objections_handled.append(tag)
                if key == "in_office_meeting":
                    self.dossier.follow_up_note = "Customer in office/meeting; scheduled callback after 6:00 PM and sent WhatsApp brochure."
                    self.dossier.timeframe = "callback_after_6pm"
                    self.dossier.bant_timeline_confirmed = "Callback after 6:00 PM today"
                    self.dossier.whatsapp_dispatched = True
                    self.dossier.whatsapp_status = "sent"
                    if "whatsapp" in t or "वॉट्सऐप" in t:
                        self.dossier.preferred_channel = "WhatsApp"
                    else:
                        self.dossier.preferred_channel = "WhatsApp/Phone"
                elif key == "whatsapp_only_friction":
                    self.dossier.preferred_channel = "WhatsApp"
                    self.dossier.whatsapp_dispatched = True
                    self.dossier.whatsapp_status = "sent"
                    self.dossier.follow_up_note = "Customer requested communication strictly on WhatsApp."
                self._score_lead()
                return play["response"]

        # 2. Check Indian Query Playbook
        for key, play in INDIA_QUERY_PLAYBOOK.items():
            if re.search(play["pattern"], t):
                tag = play["handled_tag"]
                if tag not in self.dossier.objections_handled:
                    self.dossier.objections_handled.append(tag)
                if key == "customer_complaint_support":
                    self.dossier.customer_type = "support_query"
                    self.dossier.query_type = "customer_complaint"
                    self.dossier.ticket_id = "CC-84291"
                    self.dossier.query_resolved = True
                    self.dossier.whatsapp_status = "sent"
                    self.dossier.whatsapp_dispatched = True
                    self.dossier.follow_up_note = "Logged priority ticket #CC-84291; manager resolution within 2 hours."
                    self.dossier.bant_authority_verified = self.dossier.bant_authority_verified or "Authorized Account Holder"
                    self.dossier.bant_need_identified = "Customer Complaint & SLA Resolution"
                    self.dossier.bant_timeline_confirmed = "2-hour senior manager resolution SLA"
                elif key == "whatsapp_request":
                    self.dossier.whatsapp_dispatched = True
                    self.dossier.whatsapp_status = "sent"
                    self.dossier.preferred_channel = "WhatsApp"
                elif key == "site_visit_booking":
                    if any(w in t for w in ["saturday", "sunday", "11 am", "11:00", "3 pm", "3:00"]):
                        day = "Saturday 11:00 AM" if ("saturday" in t or "11" in t) else "Sunday 3:00 PM"
                        self.dossier.appointment_datetime = day
                        self.dossier.appointment_type = "weekend_site_visit"
                        self.dossier.appointment_notes = f"Confirmed site visit for {day} with project relationship manager"
                        self.dossier.follow_up_note = f"Confirmed VIP site visit for {day}."
                        self.dossier.bant_timeline_confirmed = f"Weekend VIP Site Visit: {day}"
                        self.dossier.bant_authority_verified = self.dossier.bant_authority_verified or "Family Decision Maker"
                        self.dossier.whatsapp_dispatched = True
                        self.dossier.whatsapp_status = "sent"
                        self.is_completed = True
                        self._score_lead()
                        return (
                            f"Excellent! I have confirmed your VIP site visit for {day}. "
                            "Our project manager will welcome you and your family at the site lounge. "
                            "I have also sent the Google Maps location and visit pass directly to your WhatsApp."
                        )
                    self.dossier.appointment_type = "weekend_site_visit"
                    self.dossier.timeframe = "this_weekend"
                    self.dossier.appointment_notes = "Complimentary VIP site visit with family"
                    self.dossier.bant_authority_verified = self.dossier.bant_authority_verified or "Family Decision Maker"
                    self.dossier.bant_timeline_confirmed = "Weekend VIP Site Visit"
                self._score_lead()
                return play["response"]

        # 3. Dynamic Indian Consultative Response & Slot Confirmation
        if any(w in t for w in ["saturday", "sunday", "11 am", "11:00", "3 pm", "3:00"]):
            day = "Saturday 11:00 AM" if ("saturday" in t or "11" in t) else "Sunday 3:00 PM"
            self.dossier.appointment_datetime = day
            self.dossier.appointment_type = "weekend_site_visit"
            self.dossier.appointment_notes = f"Confirmed site visit for {day} with project relationship manager"
            self.dossier.follow_up_note = f"Confirmed VIP site visit for {day}."
            self.dossier.bant_timeline_confirmed = f"Weekend VIP Site Visit: {day}"
            self.dossier.bant_authority_verified = self.dossier.bant_authority_verified or "Family Decision Maker"
            self.dossier.whatsapp_dispatched = True
            self.dossier.whatsapp_status = "sent"
            self.is_completed = True
            self._score_lead()
            return (
                f"Excellent! I have confirmed your VIP site visit for {day}. "
                "Our project manager will welcome you and your family at the site lounge. "
                "I have also sent the Google Maps location and visit pass directly to your WhatsApp."
            )

        if any(w in t for w in ["yes", "sure", "okay", "fine"]):
            self.dossier.whatsapp_dispatched = True
            self.dossier.whatsapp_status = "sent"
            return (
                "Wonderful! I have forwarded the full digital brochure, carpet area details, and payment schedules "
                "to your WhatsApp number. Would you like to schedule a private site visit this weekend?"
            )

        return (
            "Thank you for sharing that! Our team is dedicated to providing you complete transparency and support. "
            "Shall I share the complete project details and pricing options directly on your WhatsApp?"
        )

    def _process_hindi_turn(self, clean_input: str) -> str:
        """Processes turn under Native Hindi Customer Care & Closing mode."""
        t = clean_input.lower()

        # 1. Check Hindi Friction Playbook
        for key, play in HINDI_FRICTION_PLAYBOOK.items():
            if re.search(play["pattern"], t):
                tag = play["handled_tag"]
                if tag not in self.dossier.objections_handled:
                    self.dossier.objections_handled.append(tag)
                if key == "in_office_meeting":
                    self.dossier.follow_up_note = "ग्राहक मीटिंग में हैं; शाम 6 बजे के बाद कॉल और वॉट्सऐप ब्रोशर शेड्यूल्ड।"
                    self.dossier.timeframe = "callback_after_6pm"
                    self.dossier.bant_timeline_confirmed = "आज शाम 6 बजे के बाद कॉल"
                    self.dossier.whatsapp_dispatched = True
                    self.dossier.whatsapp_status = "sent"
                    if "whatsapp" in t or "वॉट्सऐप" in t:
                        self.dossier.preferred_channel = "WhatsApp"
                    else:
                        self.dossier.preferred_channel = "WhatsApp/Phone"
                elif key == "whatsapp_only_friction":
                    self.dossier.preferred_channel = "WhatsApp"
                    self.dossier.whatsapp_dispatched = True
                    self.dossier.whatsapp_status = "sent"
                    self.dossier.follow_up_note = "ग्राहक ने केवल वॉट्सऐप पर बात करने का अनुरोध किया।"
                self._score_lead()
                return play["response"]

        # 2. Check Hindi Query Playbook
        for key, play in HINDI_QUERY_PLAYBOOK.items():
            if re.search(play["pattern"], t):
                tag = play["handled_tag"]
                if tag not in self.dossier.objections_handled:
                    self.dossier.objections_handled.append(tag)
                if key == "customer_complaint_support":
                    self.dossier.customer_type = "support_query"
                    self.dossier.query_type = "customer_complaint"
                    self.dossier.ticket_id = "CC-84291"
                    self.dossier.query_resolved = True
                    self.dossier.whatsapp_status = "sent"
                    self.dossier.whatsapp_dispatched = True
                    self.dossier.follow_up_note = "प्रायोरिटी सपोर्ट टिकट #CC-84291 दर्ज; 2 घंटे में समाधान।"
                    self.dossier.bant_authority_verified = self.dossier.bant_authority_verified or "मुख्य खाताधारक / ग्राहक"
                    self.dossier.bant_need_identified = "कस्टमर सपोर्ट व शिकायत समाधान"
                    self.dossier.bant_timeline_confirmed = "2 घंटे में सीनियर मैनेजर रिज़ॉल्यूशन एसएलए"
                elif key == "whatsapp_request":
                    self.dossier.whatsapp_dispatched = True
                    self.dossier.whatsapp_status = "sent"
                    self.dossier.preferred_channel = "WhatsApp"
                elif key == "site_visit_booking":
                    if any(w in t for w in ["शनिवार", "रविवार", "saturday", "sunday", "11 am", "11:00", "3 pm", "3:00", "11", "3"]):
                        day = "शनिवार सुबह 11:00 बजे" if any(x in t for x in ["शनिवार", "saturday", "11"]) else "रविवार दोपहर 3:00 बजे"
                        self.dossier.appointment_datetime = day
                        self.dossier.appointment_type = "weekend_site_visit"
                        self.dossier.appointment_notes = f"वीआईपी साइट विज़िट कन्फ़र्म: {day}"
                        self.dossier.follow_up_note = f"साइट विज़िट कन्फ़र्म: {day}."
                        self.dossier.bant_timeline_confirmed = f"साइट विज़िट: {day}"
                        self.dossier.bant_authority_verified = self.dossier.bant_authority_verified or "पारिवारिक निर्णय / मुख्य खरीदार"
                        self.dossier.whatsapp_dispatched = True
                        self.dossier.whatsapp_status = "sent"
                        self.is_completed = True
                        self._score_lead()
                        return (
                            f"बहुत बढ़िया! मैंने {day} की आपकी वीआईपी साइट विज़िट कन्फ़र्म कर दी है। "
                            "साइट पर हमारे सीनियर प्रोजेक्ट मैनेजर आपका स्वागत करेंगे। "
                            "लोकेशन मैप और विज़िट पास मैंने आपके वॉट्सऐप पर भेज दिया है।"
                        )
                    self.dossier.appointment_type = "weekend_site_visit"
                    self.dossier.timeframe = "this_weekend"
                    self.dossier.appointment_notes = "परिवार के साथ कॉम्प्लिमेंट्री वीआईपी साइट विज़िट"
                    self.dossier.bant_authority_verified = self.dossier.bant_authority_verified or "पारिवारिक निर्णय / मुख्य खरीदार"
                    self.dossier.bant_timeline_confirmed = "शनिवार/रविवार वीआईपी साइट विज़िट"
                self._score_lead()
                return play["response"]

        # 3. Dynamic Hindi Slot Confirmation
        if any(w in t for w in ["शनिवार", "रविवार", "saturday", "sunday", "11 am", "11:00", "3 pm", "3:00", "11", "3"]):
            day = "शनिवार सुबह 11:00 बजे" if any(x in t for x in ["शनिवार", "saturday", "11"]) else "रविवार दोपहर 3:00 बजे"
            self.dossier.appointment_datetime = day
            self.dossier.appointment_type = "weekend_site_visit"
            self.dossier.appointment_notes = f"वीआईपी साइट विज़िट कन्फ़र्म: {day}"
            self.dossier.follow_up_note = f"साइट विज़िट कन्फ़र्म: {day}."
            self.dossier.bant_timeline_confirmed = f"साइट विज़िट: {day}"
            self.dossier.bant_authority_verified = self.dossier.bant_authority_verified or "पारिवारिक निर्णय / मुख्य खरीदार"
            self.dossier.whatsapp_dispatched = True
            self.dossier.whatsapp_status = "sent"
            self.is_completed = True
            self._score_lead()
            return (
                f"बहुत बढ़िया! मैंने {day} की आपकी वीआईपी साइट विज़िट कन्फ़र्म कर दी है। "
                "साइट पर हमारे सीनियर प्रोजेक्ट मैनेजर आपका स्वागत करेंगे। "
                "लोकेशन मैप और विज़िट पास मैंने आपके वॉट्सऐप पर भेज दिया है।"
            )

        if any(w in t for w in ["हाँ", "हां", "theek", "theek hai", "sure", "okay", "yes", "achha"]):
            self.dossier.whatsapp_dispatched = True
            self.dossier.whatsapp_status = "sent"
            return (
                "शानदार! मैंने पूरा डिजिटल ब्रोशर, फ्लोर प्लान और कीमतें आपके वॉट्सऐप पर भेज दी हैं। "
                "क्या आप इस वीकेंड हमारे साथ साइट विज़िट का समय रखना चाहेंगे?"
            )

        return (
            "जानकारी साझा करने के लिए बहुत धन्यवाद! हमारी टीम आपकी पूरी सहायता के लिए तैयार है। "
            "क्या मैं प्रोजेक्ट की पूरी जानकारी और कीमतें आपके वॉट्सऐप पर शेयर कर दूँ?"
        )

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

        # Pre-approval / Jumbo Financing / Private Banking
        if any(w in t for w in ["all cash", "paying cash", "cash buyer", "liquid"]):
            self.dossier.pre_approved = True
            self.dossier.financing_type = "cash"
            self.dossier.qualification_reasons.append("Verified all-cash buyer")
        elif re.search(r'\b(jumbo(\s*loan|\s*mortgage)?|private\s*banking|first\s*republic|jp\s*morgan|j\.p\.\s*morgan|morgan\s*stanley|bespoke\s*financing)\b', t):
            self.dossier.pre_approved = True
            if re.search(r'\b(jp\s*morgan|j\.p\.\s*morgan)\b', t):
                self.dossier.lender_name = "J.P. Morgan Private Bank"
                self.dossier.financing_type = "private_banking"
            elif "first republic" in t:
                self.dossier.lender_name = "First Republic"
                self.dossier.financing_type = "private_banking"
            else:
                self.dossier.financing_type = "jumbo_loan"
            if "Private banking / jumbo financing readiness" not in self.dossier.qualification_reasons:
                self.dossier.qualification_reasons.append("Private banking / jumbo financing readiness")
        elif any(w in t for w in ["pre-approved", "pre approved", "preapproval", "bank approved"]):
            self.dossier.pre_approved = True
            self.dossier.financing_type = "pre_approved_jumbo"
            self.dossier.qualification_reasons.append("Pre-approved with lender")
        elif any(w in t for w in ["haven't talked", "not approved", "no pre-approval", "haven't spoken"]):
            self.dossier.pre_approved = False
            self.dossier.financing_type = "needs_lender_intro"

        # 1031 Tax-Deferred Exchange
        if re.search(r'\b(1031(\s*tax)?(\s*exchange)?|like[- ]kind|tax[- ]deferred|exchange\s*period|replacement\s*property|qualified\s*intermediary)\b', t):
            self.dossier.tax_exchange_1031 = True
            days_match = re.search(r'\b(45|180|\d+)\s*[- ]?days?\b', t)
            if days_match:
                self.dossier.exchange_deadline_days = int(days_match.group(1))
            else:
                self.dossier.exchange_deadline_days = 45
            self.dossier.bant_timeline_confirmed = f"{self.dossier.exchange_deadline_days}-day identification deadline"
            if not self.dossier.timeframe:
                self.dossier.timeframe = f"1031 exchange ({self.dossier.exchange_deadline_days} days)"
            if not self.dossier.bant_authority_verified:
                self.dossier.bant_authority_verified = "Qualified Intermediary / 1031 Entity"
            if "1031 tax exchange qualified with active timeline" not in self.dossier.qualification_reasons:
                self.dossier.qualification_reasons.append("1031 tax exchange qualified with active timeline")

        # Timeframe
        if re.search(r'\b(tomorrow|next day)\b', t):
            self.dossier.timeframe = "tomorrow (immediate)"
        elif re.search(r'\b(immediately|asap|this month|30 days|right away)\b', t):
            self.dossier.timeframe = "immediate (0-30 days)"
        elif re.search(r'\b(1\s*(?:to|-)\s*[23]\s*months?|next month|couple months?|60 days)\b', t):
            self.dossier.timeframe = "1-3 months"
        elif re.search(r'\b(3\s*(?:to|-)\s*6\s*months?|summer|fall|by the end of the year)\b', t):
            self.dossier.timeframe = "3-6 months"
        elif re.search(r'\b(just looking|browsing|year or two|not in a rush)\b', t):
            self.dossier.timeframe = "browsing (6+ months)"

        # Target locations
        for loc in ["Beverly Hills", "Bel Air", "Malibu", "Brentwood", "Holmby Hills", "Pacific Palisades", "Tribeca", "Miami Beach", "Aspen"]:
            if loc.lower() in t and loc not in self.dossier.target_locations:
                self.dossier.target_locations.append(loc)

        # Property type
        if "penthouse" in t:
            self.dossier.property_type = "Penthouse"
        elif any(w in t for w in ["aspen", "mountain compound", "ski compound", "ski-in"]):
            self.dossier.property_type = "Aspen Mountain Compound"
        elif any(w in t for w in ["villa", "estate", "single family", "mansion"]):
            self.dossier.property_type = "Luxury Estate"
        elif "modern" in t or "contemporary" in t:
            self.dossier.property_type = "Modern Architectural"

        # Indian INR Budget extraction (Lakhs & Crores, English & Hindi Devanagari)
        cr_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:cr\b|crores?\b|करोड़)', t)
        if cr_match:
            cr_val = float(cr_match.group(1))
            amount = int(cr_val * 10_000_000)
            self.dossier.budget_max = amount
            self.dossier.budget_min = int(amount * 0.8)
            self.dossier.budget_currency = "INR"
            self.dossier.budget_inr_text = f"₹{cr_val} Crores"
        else:
            lakh_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:lakhs?\b|lacs?\b|l\b|लाख)', t)
            if lakh_match:
                lakh_val = float(lakh_match.group(1))
                amount = int(lakh_val * 100_000)
                self.dossier.budget_max = amount
                self.dossier.budget_min = int(amount * 0.8)
                self.dossier.budget_currency = "INR"
                self.dossier.budget_inr_text = f"₹{int(lakh_val)} Lakhs"

        # Indian / Hindi BHK configuration
        bhk_match = re.search(r'(?:^|\b|\s)([1-5])\s*(?:bhk|बीएचके)', t)
        if bhk_match:
            num = bhk_match.group(1)
            self.dossier.bhk_preference = f"{num} BHK"
            self.dossier.property_type = f"{num} BHK Luxury Apartment"
            if not self.dossier.budget_max and self.market_mode in ("india", "hindi"):
                if num == "2":
                    self.dossier.budget_max = 9_500_000
                    self.dossier.budget_inr_text = "₹95 Lakhs"
                    self.dossier.budget_currency = "INR"
                elif num == "3":
                    self.dossier.budget_max = 16_500_000
                    self.dossier.budget_inr_text = "₹1.65 Crores"
                    self.dossier.budget_currency = "INR"
        elif any(w in t for w in ["villa", "विला", "विल्ला"]):
            self.dossier.bhk_preference = "Luxury Villa"
            self.dossier.property_type = "Gated Community Villa"

        # Indian Target locations
        for loc in ["Whitefield", "Sarjapur", "Indiranagar", "Koramangala", "Bengaluru", "Bangalore",
                    "Bandra", "Powai", "Andheri", "Worli", "Mumbai", "Thane",
                    "Gurgaon", "Noida", "Delhi", "Hitec City", "Gachibowli", "Hyderabad", "Pune", "Chennai"]:
            if loc.lower() in t and loc not in self.dossier.target_locations:
                self.dossier.target_locations.append(loc)

        # BANT Authority Verification
        if re.search(r'\b(family\s*office|family\s*trust|trustee|trust)\b', t):
            self.dossier.bant_authority_verified = "Family Office / Trust"
        elif re.search(r'\b(sole\s*(buyer|purchaser|decision\s*maker)|myself|on\s*my\s*own|just\s*me|i\s*am\s*the\s*(buyer|decision\s*maker))\b', t):
            self.dossier.bant_authority_verified = "Sole Decision Maker"
        elif re.search(r'\b(llc|corporate|corporation|company|entity)\b', t):
            self.dossier.bant_authority_verified = "Corporate Entity / LLC"
        elif re.search(r'\b(qualified\s*intermediary|qi|1031\s*entity)\b', t):
            self.dossier.bant_authority_verified = "Qualified Intermediary / 1031 Entity"
        elif re.search(r'\b(my\s*wife|my\s*husband|my\s*spouse|my\s*partner|wife\s*and\s*i|husband\s*and\s*i|with\s*my\s*family|our\s*family)\b', t):
            self.dossier.bant_authority_verified = "Co-Buyer with Spouse/Partner"
        elif any(w in t for w in ["परिवार", "family", "माता-पिता", "पत्नी", "पति"]):
            self.dossier.bant_authority_verified = "Family Decision Maker"
        elif any(w in t for w in ["अकेले", "खुद", "मैं खुद"]):
            self.dossier.bant_authority_verified = "Sole Decision Maker"

        # BANT Need Identification
        if self.dossier.tax_exchange_1031:
            loc_str = f" in {', '.join(self.dossier.target_locations)}" if self.dossier.target_locations else " in Bel Air / Beverly Hills / Aspen"
            self.dossier.bant_need_identified = f"1031 Exchange Replacement Estate{loc_str}"
        elif self.dossier.bhk_preference and self.dossier.target_locations:
            self.dossier.bant_need_identified = f"{self.dossier.bhk_preference} Luxury Apartment in {', '.join(self.dossier.target_locations)}"
        elif self.dossier.bhk_preference:
            self.dossier.bant_need_identified = f"{self.dossier.bhk_preference} Luxury Apartment"
        elif self.dossier.property_type and self.dossier.target_locations:
            self.dossier.bant_need_identified = f"{self.dossier.property_type} in {', '.join(self.dossier.target_locations)}"
        elif self.dossier.property_type:
            self.dossier.bant_need_identified = self.dossier.property_type
        elif "aspen" in t:
            self.dossier.bant_need_identified = "Private Mountain Compound in Aspen"
        elif any(w in t for w in ["modern", "architectural", "contemporary"]):
            self.dossier.bant_need_identified = "Modern Architectural View Estate"

        # BANT Timeline Confirmation
        if self.dossier.tax_exchange_1031 and self.dossier.exchange_deadline_days:
            self.dossier.bant_timeline_confirmed = f"{self.dossier.exchange_deadline_days}-day identification deadline"
        elif self.dossier.timeframe:
            self.dossier.bant_timeline_confirmed = self.dossier.timeframe
        if self.dossier.appointment_datetime:
            self.dossier.bant_timeline_confirmed = f"Confirmed appointment: {self.dossier.appointment_datetime}"

        # WhatsApp channel
        if "whatsapp" in t or "whats app" in t or "वॉट्सऐप" in t:
            self.dossier.preferred_channel = "WhatsApp"
            self.dossier.whatsapp_dispatched = True
            self.dossier.whatsapp_status = "sent"

        # Customer Care Dispute / Ticket
        if any(w in t for w in ["complaint", "issue", "problem", "ticket", "refund", "not working", "wrong"]):
            self.dossier.customer_type = "support_query"
            self.dossier.query_type = "customer_complaint"
            if not self.dossier.ticket_id:
                self.dossier.ticket_id = "CC-84291"
            self.dossier.query_resolved = True

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
        if self.dossier.budget_currency == "INR":
            if self.dossier.budget_max:
                if self.dossier.budget_max >= 20_000_000:
                    score += 35
                    reasons.append("Ultra-luxury INR budget (₹2 Cr+)")
                elif self.dossier.budget_max >= 10_000_000:
                    score += 25
                    reasons.append("Premium INR budget (₹1 Cr+)")
                elif self.dossier.budget_max >= 5_000_000:
                    score += 15
                    reasons.append("Standard INR budget (₹50 Lakhs+)")
            elif self.dossier.bhk_preference:
                score += 20
                reasons.append(f"Identified requirement: {self.dossier.bhk_preference}")
        elif self.dossier.budget_max:
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
        elif self.dossier.financing_type == "private_banking":
            score += 20
            reasons.append("Private banking jumbo readiness adds high qualification")
        elif self.dossier.pre_approved is True:
            score += 15
            reasons.append("Pre-approval verified")
        elif self.dossier.pre_approved is False:
            score -= 5

        # 1031 Tax-Deferred Exchange scoring
        if self.dossier.tax_exchange_1031:
            score += 20
            reasons.append("Active 1031 tax exchange qualified with statutory deadline")

        # Timeline scoring
        if self.dossier.timeframe in ("immediate (0-30 days)", "1-3 months", "tomorrow (immediate)"):
            score += 20
            reasons.append("High urgency timeline (<= 90 days)")
        elif self.dossier.timeframe and "1031" in self.dossier.timeframe:
            score += 20
            reasons.append("Strict 1031 statutory timeline")
        elif self.dossier.timeframe == "3-6 months":
            score += 10
        elif self.dossier.timeframe == "browsing (6+ months)":
            score -= 5

        # Objections handled bonus
        if self.dossier.objections_handled:
            score += 5

        # BANT Budget qualification
        if self.dossier.budget_currency == "INR":
            if self.dossier.budget_max and self.dossier.budget_max >= 5_000_000:
                self.dossier.bant_budget_qualified = True
            elif self.dossier.bhk_preference:
                self.dossier.bant_budget_qualified = True
        else:
            if self.dossier.budget_max and self.dossier.budget_max >= 1_500_000:
                self.dossier.bant_budget_qualified = True
            elif self.dossier.financing_type in ("cash", "private_banking", "pre_approved_jumbo"):
                self.dossier.bant_budget_qualified = True
            elif self.dossier.pre_approved:
                self.dossier.bant_budget_qualified = True
            elif self.dossier.tax_exchange_1031:
                self.dossier.bant_budget_qualified = True

        self.dossier.intent_score = min(100, max(0, score))
        
        # Qualified logic: Must have budget >= $1.5M (or cash/pre-approved/1031) and reasonable timeframe
        budget_ok = (self.dossier.budget_max is not None and self.dossier.budget_max >= 1_500_000) or self.dossier.tax_exchange_1031
        time_ok = self.dossier.timeframe != "browsing (6+ months)"
        self.dossier.qualified = (budget_ok and (self.dossier.pre_approved is True or self.dossier.financing_type in ("cash", "private_banking", "pre_approved_jumbo") or self.dossier.tax_exchange_1031)) or (score >= 70)
        self.dossier.qualification_reasons = reasons

    def _handle_script_deviation(self, text: str) -> Optional[str]:
        """
        Autonomous rational reasoning brain:
        Detects schedule friction, busy constraints, or async requests when
        buyers deviate from the rigid sales script SOP.
        Returns tailored high-EQ luxury concierge response.
        """
        t = text.lower()

        # 0. Direct Async Brochure Request (SMS / WhatsApp) - Prioritized even if buyer mentions being busy
        is_async_request = bool(re.search(
            r"\b(sms|text\s*(it|me|the\s*details|info|brochure)?|whats\s*app|whatsapp|send\s*(it|info|details|brochure|dossier)\s*(to|via|on)?\s*(my\s*)?(phone|mobile|whatsapp|sms)?)\b",
            t
        ))
        if is_async_request and not any(w in t for w in ["tour", "showing", "see it", "walkthrough"]):
            self.dossier.preferred_channel = "SMS/WhatsApp"
            self.dossier.follow_up_note = f"Dispatched private VIP brochure via SMS/WhatsApp to {self.lead.phone_number}."
            if not self.dossier.timeframe:
                self.dossier.timeframe = "async_brochure_sent"
            self.dossier.sentiment_rating = "Polite / Busy"
            tag = "Dispatched private VIP brochure via SMS/WhatsApp as requested."
            if tag not in self.dossier.objections_handled:
                self.dossier.objections_handled.append(tag)
            self._score_lead()
            return f"I'll text our private VIP brochure with high-resolution photography, floor plans, and pricing directly to {self.lead.phone_number or 'your mobile'} right now. Feel free to text back whenever you'd like to arrange a private showing!"

        # 1. State-aware multi-turn continuation
        # 1A. Responding to tomorrow's TOUR window offer ("Tour postponed to tomorrow... offered morning (11 AM) vs afternoon (2 PM) window")
        if self.dossier.follow_up_note and "Tour postponed to tomorrow" in self.dossier.follow_up_note and "offered morning (11 AM) vs afternoon (2 PM) window" in self.dossier.follow_up_note:
            if any(w in t for w in ["morning", "afternoon", "evening", "11", "2", "pm", "am", "works", "good", "perfect", "suit"]):
                slot = self._parse_preferred_slot(text)
                self.dossier.appointment_datetime = slot
                self.dossier.appointment_type = "private_vip_tour"
                self.dossier.appointment_notes = f"VIP On-Site Tour at {self.lead.listing_address} with {settings.REALTOR_NAME}"
                self.dossier.follow_up_note = f"Confirmed VIP tour for {slot}."
                self.dossier.sentiment_rating = "Urgent"
                self.is_completed = True
                self._score_lead()
                return (
                    f"Perfect. I have reserved {slot} for your private VIP showing with {settings.REALTOR_NAME}. "
                    f"I'm sending a calendar invite and security gate access instructions directly to your mobile. "
                    f"We look forward to welcoming you!"
                )

        # 1B. Responding to tomorrow's CALLBACK window offer
        if self.dossier.follow_up_note and "Callback requested for tomorrow; offered morning" in self.dossier.follow_up_note:
            if any(w in t for w in ["morning", "afternoon", "evening", "11", "2", "pm", "am", "works", "good", "perfect", "suit"]):
                slot = self._parse_preferred_slot(text)
                self.dossier.appointment_datetime = slot
                self.dossier.appointment_type = "phone_consultation"
                self.dossier.follow_up_note = f"Confirmed callback for {slot}."
                self.dossier.sentiment_rating = "Polite / Busy"
                self.is_completed = True
                self._score_lead()
                return (
                    f"Perfect. I have scheduled a brief 2-minute callback for {slot}. "
                    f"I look forward to speaking with you then — have a wonderful rest of your day!"
                )

        # 1C. Responding to busy callback offer ("Offered callback window and async VIP brochure")
        if self.dossier.follow_up_note and "Offered callback window and async VIP brochure" in self.dossier.follow_up_note:
            if any(w in t for w in ["callback", "call me", "call back", "give me a call", "phone call", "call later", "call"]):
                has_time = bool(re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|\bin\s+\d+\s*min|\bin\s+(?:an?|1)\s*hour|afternoon|evening)', t))
                if has_time:
                    slot = self._parse_preferred_slot(text)
                    self.dossier.appointment_datetime = slot
                    self.dossier.appointment_type = "phone_consultation"
                    self.dossier.follow_up_note = f"Callback window requested: {slot}."
                    self.dossier.timeframe = "callback_scheduled"
                    self.dossier.sentiment_rating = "Polite / Busy"
                    self.is_completed = True
                    self._score_lead()
                    return f"Understood. I have scheduled a brief 2-minute callback for you {slot}. I look forward to speaking soon — have a wonderful rest of your day!"
                else:
                    self.dossier.follow_up_note = "Callback requested for later today; tentative afternoon window."
                    self.dossier.timeframe = "callback_scheduled"
                    self.dossier.appointment_type = "phone_consultation"
                    self.dossier.sentiment_rating = "Polite / Busy"
                    self._score_lead()
                    return "Wonderful. I will schedule a brief 2-minute callback for later today. Would around 4:00 PM or 5:00 PM suit your schedule best, or is there another time you prefer?"

        # 2. Compound friction with conflicting time constraints (e.g. "I'm busy today and tomorrow morning, but tomorrow evening might work if I'm not traveling")
        has_compound_negation = bool(re.search(r'\b(busy|tied\s*up|can\'?t|won\'?t|no)\b[^.,;!?\n]*?\b(today|morning)\b', t))
        has_viable_window = bool(re.search(r'\b(evening|afternoon|\d{1,2}\s*(?:am|pm))\b.*?\b(work|might|could|better|possible)\b', t)) or \
                            bool(re.search(r'\b(might|could|would)\s*work\b', t))
        if has_compound_negation and has_viable_window and "tomorrow" in t:
            slot = self._parse_preferred_slot(text)
            self.dossier.timeframe = "tomorrow (tentative)"
            self.dossier.follow_up_note = f"Client busy earlier; tentative viable window: {slot}. Offered hold & async brochure."
            self.dossier.sentiment_rating = "Polite / Busy"
            tag = "Accommodated compound schedule constraints; offered tentative window and async brochure."
            if tag not in self.dossier.objections_handled:
                self.dossier.objections_handled.append(tag)
            self._score_lead()
            return f"I completely understand and respect your schedule! {slot} would be wonderful if your schedule permits. Would you like me to hold a tentative slot then, or shall I text our private VIP brochure via SMS or WhatsApp so you can review at your leisure?"

        # 3. Call Tomorrow / Talk Tomorrow / Contact Tomorrow (Calling deferral, NOT an on-site property tour)
        is_call_tomorrow = bool(re.search(
            r"\b(call(\s*me|\s*back)?\s*tomorrow|can\s*(you\s*)?call(\s*me)?\s*tomorrow|please\s*call\s*tomorrow|give\s*me\s*a\s*call\s*tomorrow|talk\s*tomorrow|speak\s*tomorrow|connect\s*tomorrow|reach\s*out\s*tomorrow|contact\s*me\s*tomorrow)\b",
            t
        )) or (
            bool(re.search(r"(today\s*(is\s*(not|no\s*good|bad|a\s*wash)|isn'?t|won'?t\s*work|doesn'?t\s*work)|not\s*today|can'?t\s*(do|make\s*it|talk)\s*today|busy\s*today)", t))
            and bool(re.search(r"\b(tomorrow|next\s*day)\b", t))
            and bool(re.search(r"\b(call|talk|speak|phone|ring|reach\s*out|connect)\b", t))
            and not any(w in t for w in ["tour", "see", "visit", "showing", "walkthrough"])
        )
        if is_call_tomorrow and not any(w in t for w in ["tour", "visit", "showing", "walkthrough"]):
            # Check if specific hour was given
            has_specific_time = bool(re.search(r'\b([1-9]|1[0-2])(?::(\d{2}))?\s*(am|pm)\b', t))
            if has_specific_time:
                slot = self._parse_preferred_slot(text)
                self.dossier.appointment_datetime = slot
                self.dossier.appointment_type = "phone_consultation"
                self.dossier.timeframe = "tomorrow (immediate)"
                self.dossier.follow_up_note = f"Callback scheduled for {slot} upon buyer request."
                self.dossier.sentiment_rating = "Polite / Busy"
                self.is_completed = True
                self._score_lead()
                return f"Understood, I completely respect your schedule. I have scheduled a brief 2-minute callback for {slot}. I look forward to speaking soon — have a wonderful rest of your day!"

            self.dossier.timeframe = "tomorrow (immediate)"
            self.dossier.follow_up_note = "Callback requested for tomorrow; offered morning (11 AM) vs afternoon (2 PM) window."
            self.dossier.appointment_type = "phone_consultation"
            self.dossier.sentiment_rating = "Polite / Busy"
            tag = "Accommodated call deferral to tomorrow; offered morning vs afternoon callback windows."
            if tag not in self.dossier.objections_handled:
                self.dossier.objections_handled.append(tag)
            self._score_lead()
            return "I completely understand and respect your schedule! Tomorrow would be great to reconnect. Would morning around 11:00 AM or afternoon around 2:00 PM be best for a quick 2-minute call, or shall I text our VIP brochure in the meantime?"

        # 4. Tour Deferral to Tomorrow: "Today is not good, I will come tomorrow"
        has_today_friction = bool(re.search(
            r"(today\s*(is\s*(not|no\s*good|bad|terrible|a\s*wash)|isn'?t|won'?t\s*(work|do)|doesn'?t\s*work|does\s*not\s*work)|not\s*(good\s*)?today|can'?t\s*(do|make\s*it|talk|chat)\s*today|busy\s*today|no\s*time\s*today|tied\s*up\s*today)",
            t
        ))
        mentions_tomorrow = bool(re.search(r"\b(tomorrow|next\s*day)\b", t))
        defer_to_tomorrow = bool(re.search(r"\b(come|tour|see\s*it|visit|schedule|make\s*it|do\s*it)\s*tomorrow\b", t)) or (has_today_friction and mentions_tomorrow)

        if defer_to_tomorrow or (mentions_tomorrow and any(w in t for w in ["prefer", "better", "instead", "rather"])):
            # Check if user already gave a specific time tomorrow (e.g. "Tomorrow at 3 PM")
            has_clock = bool(re.search(r'\b([1-9]|1[0-2])(?::(\d{2}))?\s*(am|pm)\b', t)) or bool(re.search(r'\b(?:at|around)\s*([1-9]|1[0-2])\b', t))
            if has_clock:
                slot = self._parse_preferred_slot(text)
                self.dossier.appointment_datetime = slot
                self.dossier.appointment_type = "private_vip_tour"
                self.dossier.appointment_notes = f"VIP On-Site Tour at {self.lead.listing_address} with {settings.REALTOR_NAME}"
                self.dossier.timeframe = "tomorrow (immediate)"
                self.dossier.follow_up_note = f"Tour scheduled for {slot} upon buyer request."
                self.dossier.sentiment_rating = "Urgent"
                self.is_completed = True
                self._score_lead()
                return (
                    f"I completely understand and respect your schedule. I have reserved {slot} for your private VIP tour "
                    f"with {settings.REALTOR_NAME}. I'm sending your calendar confirmation and gate access details directly to your mobile."
                )

            # Otherwise, offer morning vs afternoon window for tomorrow
            self.dossier.timeframe = "tomorrow (immediate)"
            self.dossier.appointment_notes = f"Private tour requested for tomorrow at {self.lead.listing_address}; morning (11 AM) vs afternoon (2 PM) offered."
            self.dossier.follow_up_note = "Tour postponed to tomorrow upon buyer request; offered morning (11 AM) vs afternoon (2 PM) window."
            self.dossier.sentiment_rating = "Urgent"
            tag = "Accommodated schedule friction; offered tomorrow morning/afternoon showing slots."
            if tag not in self.dossier.objections_handled:
                self.dossier.objections_handled.append(tag)
            self._score_lead()
            return "I completely understand and respect your schedule! Tomorrow would be wonderful for a private tour. Would morning around 11:00 AM or afternoon at 2:00 PM suit you better?"

        # 5. Colloquial Brush-Off / Reschedule ("today's a wash, catch you on the flip side", "rain check")
        is_colloquial_friction = bool(re.search(
            r"(today('?s|\s+is)\s+a\s+wash|catch\s*(you|ya)\s*(on\s*the\s*flip\s*side|later)|rain\s*check|not\s*in\s*the\s*cards|plate\s*is\s*full|swamped|crazy\s*busy)",
            t
        ))
        if is_colloquial_friction:
            self.dossier.follow_up_note = "Client requested rain check / deferred; offered async VIP brochure."
            if not self.dossier.timeframe:
                self.dossier.timeframe = "follow_up_requested"
            self.dossier.sentiment_rating = "Polite / Busy"
            tag = "Handled colloquial schedule friction; offered async VIP brochure and follow-up."
            if tag not in self.dossier.objections_handled:
                self.dossier.objections_handled.append(tag)
            self._score_lead()
            return "I completely understand — let's definitely take a rain check! I'll follow up when things settle down. In the meantime, would you like me to text our private VIP brochure over SMS or WhatsApp so you can review at your leisure?"

        # 6. Busy right now / In a meeting / Zoom / Conference / Driving / Tied up / With a client / Can't speak
        is_busy_friction = bool(re.search(
            r"\b(busy(\s*right\s*now)?|in\s*(?:an?\s+)?(?:[\w-]+\s+){0,2}meeting|in\s*a\s*conference|with\s*a\s*client|"
            r"in\s*the\s*middle\s*of\s*something|tied\s*up|working|at\s*work|driving|on\s*a\s*call|"
            r"can'?t\s*(talk|speak|chat)(\s*right\s*now)?|contact\s*me\s*later|call(\s*me|\s*back)?\s*later|"
            r"not\s*a\s*good\s*time|bad\s*time|slammed)\b",
            t
        ))
        if is_busy_friction:
            self.dossier.follow_up_note = "Client busy/in meeting; requested follow-up. Offered callback window and async VIP brochure via SMS/WhatsApp."
            if not self.dossier.timeframe:
                self.dossier.timeframe = "callback_requested"
            self.dossier.sentiment_rating = "Polite / Busy"
            tag = "Respected client schedule constraints; offered callback & async digital brochure."
            if tag not in self.dossier.objections_handled:
                self.dossier.objections_handled.append(tag)
            self._score_lead()
            return "I completely respect your time and won't keep you while you're busy! Would you prefer a quick 2-minute callback later today, or shall I text our private VIP brochure via SMS or WhatsApp for you to review at your convenience?"

        # 7. Callback timing specification: "call back in 10 minutes" / "call me at 4 PM" / "call back in an hour"
        is_callback_timing = bool(re.search(
            r"\b(call\s*(?:me\s*)?(?:back\s*)?(?:at|in|around|this|later)|reach\s*out\s*(?:at|in|around|this|later))\b",
            t
        ))
        if is_callback_timing and not any(w in t for w in ["tour", "showing", "see"]):
            slot = self._parse_preferred_slot(text)
            self.dossier.appointment_datetime = slot
            self.dossier.appointment_type = "phone_consultation"
            self.dossier.follow_up_note = f"Callback window requested: {text} (target: {slot})."
            self.dossier.timeframe = "callback_scheduled"
            self.dossier.sentiment_rating = "Polite / Busy"
            self.is_completed = True
            self._score_lead()
            return f"Understood. I have scheduled a brief 2-minute callback for you {slot}. I look forward to speaking soon — have a wonderful rest of your day!"

        return None

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
        
        # Check if buyer mentions days
        has_day = bool(re.search(r'\b(tomorrow|today|thursday|friday|saturday|sunday|monday|tuesday|wednesday|weekend)\b', t))
        
        # Check if buyer mentions specific times of day or clock hours (NOT substrings like 'am' inside 'I am')
        has_time = bool(re.search(r'\b([1-9]|1[0-2])(?::(\d{2}))?\s*(?:am|pm)\b', t)) or \
                   bool(re.search(r'\b(?:at|around)\s*([1-9]|1[0-2])\b', t)) or \
                   bool(re.search(r'\b(morning|afternoon|evening|o\'clock|noon)\b', t))
        
        # Negation check: "doesn't work", "won't work", "can't do"
        is_negated = bool(re.search(r'\b(doesn\'?t|does\s*not|won\'?t|can\'?t|not)\s*(work|suit|do)\b', t))
        if is_negated:
            return None

        has_booking_intent = bool(re.search(r'\b(tour|visit|showing|walkthrough|see\s*it|meet\s*up|schedule|reserve|book)\b', t)) or \
                             bool(re.search(r'\b(works?\s*(great|well|fine|perfect)?|sounds?\s*good|perfect|available|suit)\b', t))
        
        if (has_day or has_time) and has_booking_intent:
            slot = self._parse_preferred_slot(text)
            self.dossier.appointment_datetime = slot
            self.dossier.appointment_type = "private_vip_tour"
            self.dossier.appointment_notes = f"VIP On-Site Tour at {self.lead.listing_address} with {settings.REALTOR_NAME}"
            self.dossier.sentiment_rating = "Urgent"
            self.is_completed = True
            self._score_lead()
            return (
                f"Perfect. I have reserved {slot} for your private VIP showing with {settings.REALTOR_NAME}. "
                f"I'm sending a calendar invite and security gate access instructions directly to your mobile. "
                f"We look forward to welcoming you!"
            )
            
        return None

    def _parse_preferred_slot(self, text: str) -> str:
        """Parses an appointment or callback slot string."""
        t = text.lower()
        
        # 1. Relative offset: in X minutes / in X hours
        min_match = re.search(r'\bin\s+(\d+)\s*(?:mins?|minutes?)\b', t)
        if min_match:
            return f"Today in {min_match.group(1)} minutes"
        hr_match = re.search(r'\bin\s+(?:an?|1)\s*hour\b', t)
        if hr_match:
            return "Today in 1 hour"
        hrs_match = re.search(r'\bin\s+(\d+)\s*hours?\b', t)
        if hrs_match:
            return f"Today in {hrs_match.group(1)} hours"

        target_day = "Tomorrow"
        for day in ["Thursday", "Friday", "Saturday", "Monday", "Tuesday", "Wednesday", "Sunday"]:
            if day.lower() in t:
                target_day = f"This {day}"
                break
        if "today" in t and not re.search(r'\b(busy\s*today|today\s*(is\s*not|isn\'?t|won\'?t|doesn\'?t|is\s*bad|is\s*no\s*good|a\s*wash)|not\s*today|can\'?t\s*(do\s*)?today)\b', t):
            if "tomorrow" not in t:
                target_day = "Today"

        # Clean text of relative minutes/hours/budget/bedrooms before matching clock hour
        clean_t = re.sub(r'\b\d+\s*(?:mins?|minutes?|hours?|months?|weeks?|days?|bedrooms?|beds?|million|mil\b|m\b|k\b)\b', '', t)
        clock_match = re.search(r'\b([1-9]|1[0-2])(?::(\d{2}))?\s*(am|pm)\b', clean_t)
        if not clock_match:
            clock_match = re.search(r'\b(?:at|around)\s*([1-9]|1[0-2])(?::(\d{2}))?\b', clean_t)

        if clock_match:
            hr = int(clock_match.group(1))
            minute = clock_match.group(2) or "00"
            ampm = clock_match.group(3) if len(clock_match.groups()) >= 3 and clock_match.group(3) else ("AM" if hr in [9, 10, 11] else "PM")
            return f"{target_day} at {hr}:{minute} {ampm.upper()} PST"

        # Check evening / afternoon / morning with clause-bounded negation awareness
        has_neg_morning = bool(re.search(r'\b(busy|tied\s*up|can\'?t|won\'?t|no)\b[^.,;!?\n]*?\bmorning\b', t))
        has_neg_afternoon = bool(re.search(r'\b(busy|tied\s*up|can\'?t|won\'?t|no)\b[^.,;!?\n]*?\bafternoon\b', t))
        has_neg_evening = bool(re.search(r'\b(busy|tied\s*up|can\'?t|won\'?t|no)\b[^.,;!?\n]*?\bevening\b', t))

        if ("evening" in t or "tonight" in t) and not has_neg_evening:
            return f"{target_day} at 5:00 PM PST"
        if "afternoon" in t and not has_neg_afternoon:
            return f"{target_day} at 2:00 PM PST"
        if "morning" in t and not has_neg_morning:
            return f"{target_day} at 11:00 AM PST"

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
            if self.dossier.budget_currency == "INR":
                budget_str = self.dossier.budget_inr_text or (f"₹{self.dossier.budget_max:,}" if self.dossier.budget_max else "Not disclosed")
            else:
                budget_str = f"${self.dossier.budget_max:,}" if self.dossier.budget_max else "Not disclosed"
            notes_str = f" Notes: {self.dossier.follow_up_note}" if self.dossier.follow_up_note else ""
            ticket_str = f" Ticket: {self.dossier.ticket_id}." if self.dossier.ticket_id else ""
            self.dossier.summary = (
                f"Lead {self.dossier.full_name} qualified with intent score {self.dossier.intent_score}/100. "
                f"Budget: {budget_str}. Financing: {self.dossier.financing_type}. "
                f"Timeline: {self.dossier.timeframe or 'Flexible'}. "
                f"Appointment: {self.dossier.appointment_datetime or 'Pending follow-up'}.{ticket_str}{notes_str}"
            )
        return self.dossier
