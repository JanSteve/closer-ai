"""
Tamil/Tanglish & Clinical Sector Conversational Playbooks for Amura Health / CLOSER AI.
Supports Amura Metabolic & Chronic-Care Reversal, Hospital Front-Desk & Patient Triage,
and General Care Coordination in English, Tamil (Tanglish), and Hindi (Hinglish).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.closer.agent.clinical_guardrails import ClinicalSafetyGuardrails
from src.closer.agent.emotion import EmotionDetector

SECTOR_CONFIGS: Dict[str, Dict[str, Any]] = {
    "amura_metabolic": {
        "label": "Amura Health Metabolic & Chronic-Care Clinic",
        "offer_en": "physician & health-coach metabolic consultation",
        "offer_hi": "डॉक्टर और हेल्थ कोच मेटाबोलिक कंसल्टेशन",
        "offer_ta": "Amura Health டாக்டர் மற்றும் ஹெல்த் கோச் ஆலோசனை",
        "slot_en": "tomorrow at 11:30 AM IST or Saturday at 11:00 AM IST",
        "slot_hi": "कल सुबह 11:30 बजे IST या शनिवार सुबह 11:00 बजे IST",
        "slot_ta": "நாளைக்கு காலைல 11:30 மணி IST இல்ல சனிக்கிழமை காலை 11:00 மணி IST",
    },
    "hospital_triage": {
        "label": "Hospital Front-Desk & Patient Triage",
        "offer_en": "priority OPD triage & specialist appointment",
        "offer_hi": "प्रायोरिटी OPD ट्राइएज और स्पेशलिस्ट अपॉइंटमेंट",
        "offer_ta": "priority OPD triage மற்றும் specialist appointment",
        "slot_en": "today at 4:30 PM IST or tomorrow at 10:30 AM IST",
        "slot_hi": "आज शाम 4:30 बजे IST या कल सुबह 10:30 बजे IST",
        "slot_ta": "இன்னைக்கு சாயங்காலம் 4:30 மணி IST இல்ல நாளைக்கு காலைல 10:30 மணி IST",
    },
    "healthcare": {
        "label": "Amura Health & Clinical Care",
        "offer_en": "priority specialist consultation & care plan",
        "offer_hi": "स्पेशलिस्ट डॉक्टर कंसल्टेशन और केयर प्लान",
        "offer_ta": "specialist doctor consultation மற்றும் care plan",
        "slot_en": "tomorrow at 11:30 AM IST or Friday at 5:00 PM IST",
        "slot_hi": "कल सुबह 11:30 बजे IST या शुक्रवार शाम 5:00 बजे IST",
        "slot_ta": "நாளைக்கு காலைல 11:30 மணி IST இல்ல வெள்ளிக்கிழமை சாயங்காலம் 5:00 மணி IST",
    },
    "general_b2b": {
        "label": "Amura Corporate Wellness & Partner Desk",
        "offer_en": "15-minute clinical wellness briefing",
        "offer_hi": "15-मिनट कॉर्पोरेट वेलनेस ब्रीफिंग",
        "offer_ta": "15-minute corporate wellness briefing",
        "slot_en": "tomorrow at 11:00 AM IST or 4:00 PM IST",
        "slot_hi": "कल सुबह 11:00 बजे IST या शाम 4:00 बजे IST",
        "slot_ta": "நாளைக்கு காலைல 11:00 மணி IST இல்ல சாயங்காலம் 4:00 மணி IST",
    },
}


def resolve_sector_key(sector: Optional[str]) -> str:
    low = (sector or "amura_metabolic").lower().strip()
    if any(k in low for k in ("triage", "hospital", "opd", "emergency", "front_desk", "front-desk")):
        return "hospital_triage"
    if low == "healthcare":
        return "healthcare"
    if any(k in low for k in ("b2b", "corporate", "partner", "general", "saas")):
        return "general_b2b"
    if any(k in low for k in ("amura", "metabolic", "diabetes", "pcos", "pcod", "thyroid", "health", "clinic", "doctor")):
        return "amura_metabolic"
    return "amura_metabolic"


def _sync_emotion_and_safety(
    utterance: str,
    dossier: Any,
    language: str,
) -> Optional[str]:
    """Applies ClinicalSafetyGuardrails + EmotionDetector before any sector response."""
    guardrails = ClinicalSafetyGuardrails(initial_consent=getattr(dossier, "consent_status", "pending"))
    safety = guardrails.evaluate(utterance, language=language)
    emotion = EmotionDetector().assess(utterance, language=language)

    dossier.detected_emotion = emotion.emotion.value
    dossier.emotion_confidence = emotion.confidence
    dossier.empathy_tone = emotion.voice_style
    dossier.safety_flag = safety.category
    dossier.emergency_108 = safety.emergency_108
    dossier.consent_status = guardrails.consent_status

    if not safety.allowed and safety.override_reply:
        if safety.emergency_108:
            dossier.triage_urgency = "Emergency 108"
            dossier.care_pathway = "Emergency 108"
            dossier.follow_up_note = f"EMERGENCY 108 ESCALATED: Red flags detected ({', '.join(safety.red_flags)})."
        elif safety.category in ("no_diagnosis", "no_prescribing"):
            dossier.triage_urgency = "Priority"
            dossier.care_pathway = "Amura Physician Consult"
            dossier.follow_up_note = f"Clinical guardrail ({safety.category}) triggered; routed to licensed Amura physician."
        else:
            dossier.follow_up_note = f"Guardrail action ({safety.category}) applied."
        return safety.override_reply
    return None


def _is_tamil_fee_query(t: str) -> bool:
    return any(
        k in t
        for k in (
            "discount", "price", "rate", "cost", "offer", "fee", "fees", "charge", "emi",
            "விலை", "தள்ளுபடி", "கம்மி", "டிஸ்கவுண்ட்", "ரேட்", "பணம்", "கட்டணம்", "ஃபீஸ்",
        )
    )


def _is_tamil_busy_query(t: str) -> bool:
    return any(
        k in t
        for k in (
            "busy", "meeting", "later", "tomorrow", "driving", "call me", "whatsapp",
            "மீட்டிங்", "பிஸி", "நாளைக்கு", "நேரமில்லை", "அப்புறம்", "வாட்ஸ்அப்", "அனுப்பி",
        )
    )


def _is_tamil_slot_confirm(t: str) -> bool:
    return any(
        k in t
        for k in (
            "saturday", "sunday", "thursday", "friday", "11", "4", "3", "5", "6",
            "சனிக்கிழமை", "ஞாயிறு", "வியாழன்", "வெள்ளி", "ஓகே", "பார்க்கலாம்", "வர்றேன்", "புக்",
        )
    )


def _is_general_knowledge_query(utterance: str) -> bool:
    t = (utterance or "").lower().strip()
    clinical_or_booking_words = (
        "amura", "velachery", "diabetes", "sugar", "hba1c", "insulin", "pcod", "pcos",
        "thyroid", "fatty liver", "bp", "hypertension", "doctor", "consult", "appointment",
        "slot", "book", "fee", "fees", "price", "cost", "whatsapp", "busy", "meeting",
        "lab", "report", "mnt", "nmt", "சர்க்கரை", "சுகர்", "டாக்டர்", "அப்பாயின்ட்மென்ட்",
        "डायबिटीज", "शुगर", "डॉक्टर", "कंसल्टेशन", "अपॉइंटमेंट", "फीस",
    )
    if any(w in t for w in clinical_or_booking_words):
        return False
    return "?" in utterance or any(
        t.startswith(p)
        for p in ("what", "why", "how", "who", "when", "explain", "tell me", "is ", "can you", "என்ன", "ஏன்", "எப்படி", "क्या", "क्यों", "कैसे")
    )


def process_tamil_turn(
    utterance: str,
    dossier: Any,
    sector: str = "amura_metabolic",
    business_name: str = "Amura Health",
) -> str:
    """Processes clinical & front-desk conversational turns in natural Chennai Tanglish."""
    override = _sync_emotion_and_safety(utterance, dossier, language="tamil")
    if override:
        return override

    t = utterance.lower()
    sec_key = resolve_sector_key(sector)
    cfg = SECTOR_CONFIGS[sec_key]

    if _is_tamil_busy_query(t) and not _is_tamil_slot_confirm(t):
        dossier.preferred_channel = "WhatsApp"
        dossier.whatsapp_dispatched = True
        dossier.whatsapp_status = "sent"
        dossier.timeframe = "callback_scheduled"
        dossier.follow_up_note = "Patient busy; dispatched Amura Health WhatsApp care guide & callback option."
        return (
            f"சரிங்க, நோ ப்ராப்ளம்... நீங்க பிஸியா இருக்கீங்கன்னு புரியுது. "
            f"{business_name} சார்பா நம்ம {cfg['offer_ta']} details-ஐ உடனே உங்க WhatsApp-ல அனுப்பிட்டோமுங்க. "
            f"சாயங்காலம் 6 மணிக்கு அப்புறம் ஒரு 2 நிமிஷம் பேசலாமா?"
        )

    if not _is_general_knowledge_query(utterance):
        try:
            from src.closer.memory.learning_db import get_learning_db

            learned_ans = get_learning_db().find_learned_response(utterance, sector=sec_key)
            if not learned_ans and sec_key != "amura_metabolic":
                learned_ans = get_learning_db().find_learned_response(utterance, sector="amura_metabolic")
            if learned_ans and not _is_tamil_slot_confirm(t) and not _is_tamil_fee_query(t):
                if "Clinical FAQ answered" not in getattr(dossier, "objections_handled", []):
                    dossier.objections_handled.append("Clinical FAQ answered")
                dossier.follow_up_note = "Answered patient clinical care query from Amura Health knowledge base."
                return f"{learned_ans} {cfg['slot_ta']} ஆலோசனைக்கு நேரம் பதிவு செய்யலாமா?"
        except Exception:
            pass

    if _is_tamil_fee_query(t):
        if "Care plan fee clarity" not in dossier.objections_handled:
            dossier.objections_handled.append("Care plan fee clarity")
        dossier.follow_up_note = "Explained Amura Health consultation fee & care-plan EMI options in Tamil."
        return (
            f"நிச்சயமாங்க... {business_name}-ல ஆரம்ப டாக்டர் ஆலோசனை ₹1,500 முதல் இருக்குங்க, "
            f"உங்க லேப் ரிப்போர்ட்டுக்கு ஏற்ப MNT மற்றும் NMT கேர் பிளானும் EMI வசதியும் இருக்கு. "
            f"{cfg['slot_ta']} — ஆன்லைன் வீடியோ கன்சல்டேஷன் அல்லது வேளச்சேரி கிளினிக் விசிட், எது வசதியா இருக்கும்?"
        )

    if any(k in t for k in ("mnt", "nmt", "hba1c", "fasting", "insulin", "sugar", "diabetes", "pcod", "pcos", "thyroid", "doctor", "lab", "report", "டாக்டர்", "சுகர்", "சர்க்கரை", "லேப்")):
        if "Clinical care pathway clarified" not in dossier.objections_handled:
            dossier.objections_handled.append("Clinical care pathway clarified")
        dossier.care_pathway = "Amura MNT + NMT Reversal"
        dossier.follow_up_note = "Explained physician + health coach metabolic care pathway; offered consult slot."
        return (
            f"{business_name}-ல மருத்துவர்கள் மற்றும் ஹெல்த் கோச் இணைந்து MNT மற்றும் NMT மூலம் உங்கள் HbA1c, "
            "fasting insulin போன்ற பயோமார்க்கர்களை கவனிச்சு வழிகாட்டுவாங்க. "
            f"உங்க வசதிக்காக {cfg['slot_ta']} டாக்டர் ஆலோசனை புக் பண்ணட்டுமா?"
        )

    if _is_tamil_slot_confirm(t):
        slot = cfg["slot_ta"].split(" இல்ல ")[0]
        dossier.appointment_datetime = slot
        dossier.consult_slot = slot
        dossier.appointment_type = "clinic_consultation" if "velachery" in t or "clinic" in t or "வேளச்சேரி" in t else "tele_consultation"
        dossier.whatsapp_dispatched = True
        dossier.whatsapp_status = "sent"
        dossier.follow_up_note = f"Confirmed Amura Health consultation slot in Tamil: {slot}"
        dossier.timeframe = slot
        return (
            f"சூப்பர்! உங்களுக்கான {cfg['offer_ta']} slot-ஐ {slot}-க்கு கன்ஃபார்ம் பண்ணியாச்சுங்க. "
            "Velachery clinic location மற்றும் fasting lab checklist-ஐ உங்க WhatsApp-ல அனுப்பிட்டோம்!"
        )

    try:
        from src.closer.agent.prompt import get_omni_gemini_prompt
        from src.closer.llm.router import OpenLLMRouter

        router = OpenLLMRouter()
        if router.api_key:
            sys_prompt = get_omni_gemini_prompt("tamil", business_name, sec_key)
            llm_reply, _ = router.route_reasoning(utterance, sys_prompt, [], market_mode="tamil")
            if llm_reply and len(llm_reply.strip()) > 5:
                dossier.follow_up_note = f"Responded in Tanglish via {router.active_model_id}."
                return llm_reply.strip()
    except Exception:
        pass

    if _is_general_knowledge_query(utterance):
        dossier.follow_up_note = "Answered general knowledge query politely in Tanglish without clinical pitch."
        return (
            "நல்ல கேள்விங்க! நீங்க கேட்ட பொதுத் தகவலை எளிமையா சொல்லணும்னா, அறிவியல் மற்றும் தினசரி வாழ்க்கை முறை அடிப்படையில் "
            "தெளிவான தகவலை எப்போதும் பகிரத் தயாரா இருக்கேன். வேற ஏதாவது குறிப்பா தெரிஞ்சுக்கணுமா?"
        )

    dossier.follow_up_note = "Initiated Amura Health Tamil front-desk intake."
    return (
        f"வணக்கம்... {business_name}-ல இருந்து பல்லவி பேசுறேங்க. "
        f"உங்களுக்காக {cfg['offer_ta']} ஏற்பாடு செய்யத் தயாரா இருக்கோம். "
        "நீங்க ஆன்லைன் வீடியோ கன்சல்டேஷன் பாக்குறீங்களா, இல்ல வேளச்சேரி கிளினிக் வரலாமா?"
    )


def process_non_realestate_sector_turn(
    utterance: str,
    dossier: Any,
    market_mode: str,
    sector: str,
    business_name: str = "Amura Health",
) -> str:
    """Universal clinical conversational engine for Amura Health & Hospital Front-Desk workflows."""
    sec_key = resolve_sector_key(sector)
    cfg = SECTOR_CONFIGS[sec_key]
    t = utterance.lower()

    if market_mode == "tamil":
        return process_tamil_turn(utterance, dossier, sec_key, business_name)

    override = _sync_emotion_and_safety(utterance, dossier, language=market_mode)
    if override:
        return override

    if market_mode == "hindi":
        if _is_tamil_fee_query(t) or any(k in t for k in ("डिस्काउंट", "रेट", "कम", "छूट", "पैसा", "फीस")):
            dossier.follow_up_note = "Explained Amura Health INR consultation fees & EMI options in Hindi."
            return (
                f"जी बिल्कुल, {business_name} में शुरुआती डॉक्टर कंसल्टेशन ₹1,500 से शुरू होता है और {cfg['offer_hi']} "
                f"के बाद आपकी रिपोर्ट के हिसाब से कस्टमाइज़्ड प्लान व EMI विकल्प बताए जाते हैं। "
                f"क्या {cfg['slot_hi']} का समय आपके लिए ठीक रहेगा?"
            )
        if any(k in t for k in ("शनिवार", "कल", "आज", "बजे", "ओके", "हाँ", "हां", "ok", "yes", "saturday", "tomorrow")):
            slot = cfg["slot_hi"].split(" या ")[0]
            dossier.appointment_datetime = slot
            dossier.consult_slot = slot
            dossier.appointment_type = "tele_consultation"
            dossier.whatsapp_dispatched = True
            dossier.whatsapp_status = "sent"
            dossier.follow_up_note = f"Confirmed {sec_key} consultation in Hindi: {slot}"
            return (
                f"बहुत बढ़िया! {business_name} में आपका {cfg['offer_hi']} {slot} के लिए कन्फ़र्म कर दिया गया है। "
                "कंसल्टेशन लिंक और लैब चेकलिस्ट मैंने आपके वॉट्सऐप पर भेज दी है।"
            )
        if any(k in t for k in ("busy", "मीटिंग", "व्यस्त", "बाद में", "whatsapp", "व्हाट्सएप", "वॉट्सऐप")):
            dossier.whatsapp_dispatched = True
            dossier.whatsapp_status = "sent"
            dossier.preferred_channel = "WhatsApp"
            dossier.follow_up_note = "Patient busy; sent Amura Health WhatsApp care guide in Hindi."
            return (
                f"कोई बात नहीं जी, आपका समय कीमती है। मैंने {business_name} की पूरी केयर गाइड और {cfg['offer_hi']} की जानकारी "
                "वॉट्सऐप पर भेज दी है। क्या शाम 6 बजे के बाद 2 मिनट बात कर लें?"
            )
        try:
            from src.closer.agent.prompt import get_omni_gemini_prompt
            from src.closer.llm.router import OpenLLMRouter

            router = OpenLLMRouter()
            if router.api_key:
                sys_prompt = get_omni_gemini_prompt("hindi", business_name, sec_key)
                llm_reply, _ = router.route_reasoning(utterance, sys_prompt, [], market_mode="hindi")
                if llm_reply and len(llm_reply.strip()) > 5:
                    dossier.follow_up_note = f"Responded in Hindi via {router.active_model_id}."
                    return llm_reply.strip()
        except Exception:
            pass

        if _is_general_knowledge_query(utterance):
            dossier.follow_up_note = "Answered general knowledge query politely in Hindi without clinic pitch."
            return (
                "यह एक बहुत अच्छा प्रश्न है जी! सरल शब्दों में समझें तो विज्ञान और स्वास्थ्य की बुनियादी जानकारी के आधार पर "
                "सही तथ्य समझना हमेशा मददगार होता है। क्या आप इस विषय पर कुछ और जानना चाहेंगे?"
            )

        dossier.follow_up_note = "Initiated Amura Health Hindi front-desk intake."
        return (
            f"नमस्ते जी, {business_name} से स्वाति बोल रही हूँ। "
            f"हमारा {cfg['offer_hi']} आपकी सहायता के लिए तैयार है — क्या आप इसे इस हफ्ते ऑनलाइन या क्लिनिक में प्लान करना चाहेंगे?"
        )

    # English / India English
    if any(k in t for k in ("discount", "price", "cost", "fee", "fees", "rate", "quote", "emi")):
        dossier.follow_up_note = "Provided transparent Amura Health consultation fee & EMI overview."
        return (
            f"Initial consultations at {business_name} start at ₹1,500, and our care team tailors your {cfg['offer_en']} "
            f"around your biomarker reports with flexible EMI options. Would {cfg['slot_en']} work for you?"
        )
    if any(k in t for k in ("busy", "meeting", "later", "whatsapp", "email", "text")):
        dossier.whatsapp_dispatched = True
        dossier.whatsapp_status = "sent"
        dossier.preferred_channel = "WhatsApp"
        dossier.follow_up_note = "Patient busy; sent Amura Health care guide and clinic link via WhatsApp."
        return (
            f"I completely respect your schedule. I have sent the {business_name} digital care guide and {cfg['offer_en']} details "
            "to your WhatsApp — should we reconnect briefly after 6:00 PM IST?"
        )
    if any(k in t for k in ("tomorrow", "saturday", "friday", "today", "11", "4", "6", "yes", "sure", "book", "confirm")):
        slot = cfg["slot_en"].split(" or ")[0]
        dossier.appointment_datetime = slot
        dossier.consult_slot = slot
        dossier.appointment_type = "clinic_consultation" if "velachery" in t or "clinic" in t else "tele_consultation"
        dossier.whatsapp_dispatched = True
        dossier.whatsapp_status = "sent"
        dossier.follow_up_note = f"Confirmed {sec_key} consultation slot: {slot}"
        return (
            f"Confirmed — your {cfg['offer_en']} with {business_name} is reserved for {slot}. "
            "I've sent your appointment confirmation and fasting lab checklist to your WhatsApp."
        )

    try:
        from src.closer.agent.prompt import get_omni_gemini_prompt
        from src.closer.llm.router import OpenLLMRouter

        router = OpenLLMRouter()
        if router.api_key:
            sys_prompt = get_omni_gemini_prompt("english", business_name, sec_key)
            llm_reply, _ = router.route_reasoning(utterance, sys_prompt, [], market_mode="india")
            if llm_reply and len(llm_reply.strip()) > 5:
                dossier.follow_up_note = f"Responded in English via {router.active_model_id}."
                return llm_reply.strip()
    except Exception:
        pass

    if _is_general_knowledge_query(utterance):
        dossier.follow_up_note = "Answered general knowledge query directly without clinic pitch."
        return (
            "That's a great question! Speaking broadly, understanding the underlying science and everyday mechanisms clearly "
            "makes complex topics much easier to apply. Would you like me to clarify any specific part of that?"
        )

    dossier.follow_up_note = "Initiated Amura Health clinical front-desk intake."
    return (
        f"Hello! Thanks for reaching out to {business_name}. We have your {cfg['offer_en']} ready — "
        f"would {cfg['slot_en']} work for an online or Velachery clinic session?"
    )


# Canonical clinical alias
process_clinical_sector_turn = process_non_realestate_sector_turn
