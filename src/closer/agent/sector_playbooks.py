"""Tamil Tanglish & Multi-Sector Conversational Playbooks for CLOSER AI.

Enables CLOSER AI to operate as a human-sounding telecaller across ANY business sector
(Real Estate, Healthcare & Clinics, Solar & Home Energy, EdTech, and General B2B/D2C)
in authentic conversational Tamil (Tanglish), Hindi (Hinglish), and English.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

SECTOR_CONFIGS: Dict[str, Dict[str, Any]] = {
    "real_estate": {
        "label": "Luxury Real Estate & Builders",
        "offer_en": "private penthouse & 3BHK walkthrough",
        "offer_hi": "वीआईपी साइट विज़िट और फ्लोर प्लान",
        "offer_ta": "VIP site visit மற்றும் floor plan",
        "slot_en": "Thursday at 4:00 PM or Saturday at 11:00 AM",
        "slot_hi": "गुरुवार शाम 4 बजे या शनिवार सुबह 11 बजे",
        "slot_ta": "இந்த வியாழன் சாயங்காலம் 4 மணி இல்ல சனிக்கிழமை காலை 11 மணி",
    },
    "healthcare": {
        "label": "Healthcare, Dental & Aesthetic Clinics",
        "offer_en": "priority specialist consultation & treatment plan",
        "offer_hi": "स्पेशलिस्ट डॉक्टर कंसल्टेशन और ट्रीटमेंट गाइड",
        "offer_ta": "specialist doctor consultation மற்றும் treatment plan",
        "slot_en": "tomorrow at 11:30 AM or Friday at 5:00 PM",
        "slot_hi": "कल सुबह 11:30 बजे या शुक्रवार शाम 5 बजे",
        "slot_ta": "நாளைக்கு காலைல 11:30 மணி இல்ல வெள்ளிக்கிழமை சாயங்காலம் 5 மணி",
    },
    "solar": {
        "label": "Rooftop Solar & Home Energy",
        "offer_en": "free roof survey & PM Surya Ghar subsidy calculation",
        "offer_hi": "फ्री रूफटॉप सर्वे और सरकारी सब्सिडी कैलकुलेशन",
        "offer_ta": "free roof inspection மற்றும் 40% subsidy calculation",
        "slot_en": "tomorrow morning at 10:30 AM or Saturday afternoon at 3:00 PM",
        "slot_hi": "कल सुबह 10:30 बजे या शनिवार दोपहर 3 बजे",
        "slot_ta": "நாளைக்கு காலைல 10:30 மணி இல்ல சனிக்கிழமை மதியம் 3 மணி",
    },
    "edtech": {
        "label": "EdTech, Coaching & Skill Academies",
        "offer_en": "1-on-1 career roadmap & live scholarship assessment",
        "offer_hi": "वन-ऑन-वन करियर काउंसलिंग और स्कॉलरशिप डेमो",
        "offer_ta": "1-on-1 demo class மற்றும் scholarship counselling",
        "slot_en": "today at 6:00 PM or Saturday at 11:00 AM",
        "slot_hi": "आज शाम 6 बजे या शनिवार सुबह 11 बजे",
        "slot_ta": "இன்னைக்கு சாயங்காலம் 6 மணி இல்ல சனிக்கிழமை காலை 11 மணி",
    },
    "general_b2b": {
        "label": "Custom Business Telecaller (SaaS / Services / Local Business)",
        "offer_en": "tailored 15-minute solution walkthrough & ROI quote",
        "offer_hi": "कस्टम सॉल्यूशन डेमो और कोटेशन",
        "offer_ta": "15-minute live demo மற்றும் custom quote",
        "slot_en": "tomorrow at 11:00 AM or 4:00 PM",
        "slot_hi": "कल सुबह 11 बजे या शाम 4 बजे",
        "slot_ta": "நாளைக்கு காலைல 11 மணி இல்ல சாயங்காலம் 4 மணி",
    },
}


def resolve_sector_key(sector: Optional[str]) -> str:
    low = (sector or "real_estate").lower().strip()
    if any(k in low for k in ("health", "clinic", "dental", "hair", "doctor", "hospital")):
        return "healthcare"
    if any(k in low for k in ("solar", "energy", "roof")):
        return "solar"
    if any(k in low for k in ("edtech", "course", "coach", "academy", "student")):
        return "edtech"
    if any(k in low for k in ("b2b", "general", "saas", "service", "agency", "shop", "custom")):
        return "general_b2b"
    return "real_estate"


def _is_tamil_price_query(t: str) -> bool:
    return any(
        k in t
        for k in (
            "discount", "price", "rate", "cost", "offer", "bargain", "lowest", "fee", "fees", "charge",
            "விலை", "தள்ளுபடி", "கம்மி", "டிஸ்கவுண்ட்", "ரேட்", "ஆஃபர்", "குறைக்க", "பர்சன்ட்", "பணம்", "கட்டணம்",
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


def process_tamil_turn(
    utterance: str,
    dossier: Any,
    sector: str = "real_estate",
    business_name: str = "CLOSER AI Partner",
) -> str:
    """Processes conversational turns in natural Chennai/Coimbatore Tanglish."""
    t = utterance.lower()
    sec_key = resolve_sector_key(sector)
    cfg = SECTOR_CONFIGS[sec_key]

    if _is_tamil_busy_query(t) and not _is_tamil_slot_confirm(t):
        dossier.preferred_channel = "WhatsApp"
        dossier.whatsapp_dispatched = True
        dossier.whatsapp_status = "sent"
        dossier.timeframe = "callback_scheduled"
        dossier.follow_up_note = "Customer requested async WhatsApp details / callback."
        return (
            f"சரிங்க Sir, நோ ப்ராப்ளம்... நீங்க பிஸியா இருக்கீங்கன்னு புரியுது. "
            f"{business_name} சார்பா நம்ம {cfg['offer_ta']} details-ஐ உடனே உங்க WhatsApp-ல அனுப்பிட்டோமுங்க. "
            f"சாயங்காலம் 6 மணிக்கு அப்புறம் ஒரு 2 நிமிஷம் பேசலாமா Sir?"
        )

    if _is_tamil_price_query(t):
        if "Price deflection" not in dossier.objections_handled:
            dossier.objections_handled.append("Price deflection & value anchor")
        return (
            f"ஹலோ Sir... விலை பத்தி கேக்குறது ரொம்ப நியாயந்தான். "
            f"ஆனா best ஆஃபர், payment plan எல்லாமே நம்ம {cfg['offer_ta']} அப்போ நேர்ல உட்கார்ந்து பேசினா சூப்பரா செட் பண்ணிடலாமுங்க. "
            f"{cfg['slot_ta']} — எது உங்களுக்கு வசதியா இருக்கும் Sir?"
        )

    if any(k in t for k in ("rera", "cmda", "approval", "approved", "ரேரா", "அப்ரூவல்", "வெள்ளம்", "flood", "warranty", "doctor")):
        if "Trust & compliance verified" not in dossier.objections_handled:
            dossier.objections_handled.append("Trust & compliance verified")
        return (
            "கண்டிப்பா Sir... 100% verified approvals, transparent documentation, மற்றும் complete clarity எங்ககிட்ட இருக்குங்க. "
            f"எல்லா proof-உம் WhatsApp-ல ஷேர் பண்றேன் — {cfg['slot_ta']} நேரடியா பார்க்கலாமா Sir?"
        )

    if _is_tamil_slot_confirm(t):
        slot = cfg["slot_ta"].split(" இல்ல ")[0]
        dossier.appointment_datetime = slot
        dossier.appointment_type = f"{sec_key}_consultation"
        dossier.whatsapp_dispatched = True
        dossier.whatsapp_status = "sent"
        dossier.follow_up_note = f"Confirmed Tanglish appointment slot: {slot}"
        dossier.bant_timeline_confirmed = slot
        return (
            f"சூப்பர் Sir! உங்களுக்கான {cfg['offer_ta']} slot-ஐ {slot}-க்கு பக்கா கன்ஃபார்ம் பண்ணியாச்சுங்க. "
            "Google Maps location மற்றும் VIP pass-ஐ உங்க WhatsApp-ல அனுப்பிட்டோமுங்க — நேர்ல சந்திப்போம் Sir!"
        )

    if dossier.budget_max or any(k in t for k in ("crore", "lakh", "கோடி", "லட்சம்", "bhk", "villa", "3bhk", "2bhk")):
        return (
            f"ஆமாங்க Sir, சூப்பர்! உங்க requirement-க்கு ஏத்த மாதிரி {business_name}-ல பெஸ்ட் options ரெடியா இருக்குங்க. "
            f"{cfg['slot_ta']} நேர்ல வந்து {cfg['offer_ta']} பார்க்கலாமா Sir?"
        )

    return (
        f"வணக்கம் Sir... {business_name}-ல இருந்து பல்லவி பேசுறேங்க. "
        f"உங்களுக்காக {cfg['offer_ta']} ரெடியா இருக்கு. "
        f"நீங்க உடனே start பண்ண பாக்குறீங்களா, இல்ல இந்த வீக்கெண்ட்ல பார்க்கலாமா Sir?"
    )


def process_non_realestate_sector_turn(
    utterance: str,
    dossier: Any,
    market_mode: str,
    sector: str,
    business_name: str,
) -> str:
    """Universal conversational telecaller engine for Clinics, Solar, EdTech, and B2B Businesses."""
    sec_key = resolve_sector_key(sector)
    cfg = SECTOR_CONFIGS[sec_key]
    t = utterance.lower()

    if market_mode == "tamil":
        return process_tamil_turn(utterance, dossier, sec_key, business_name)

    if market_mode == "hindi":
        if _is_tamil_price_query(t) or any(k in t for k in ("डिस्काउंट", "रेट", "कम", "छूट", "पैसा", "फीस")):
            return (
                f"अरे बिल्कुल सर... रेट और डिस्काउंट की टेंशन मत लीजिए, जब हम {cfg['offer_hi']} करेंगे ना, "
                f"तो वहीं बैठकर बेस्ट ऑफर आराम से फाइनल कर देंगे जी। "
                f"क्या {cfg['slot_hi']} का टाइम आपके लिए ठीक रहेगा सर?"
            )
        if any(k in t for k in ("शनिवार", "कल", "आज", "बजे", "ओके", "हाँ", "हां", "ok", "yes", "saturday", "tomorrow")):
            slot = cfg["slot_hi"].split(" या ")[0]
            dossier.appointment_datetime = slot
            dossier.whatsapp_dispatched = True
            dossier.whatsapp_status = "sent"
            dossier.follow_up_note = f"Confirmed {sec_key} appointment: {slot}"
            return (
                f"बहुत बढ़िया सर! {business_name} के लिए आपका {cfg['offer_hi']} {slot} को पक्का कन्फ़र्म कर दिया है जी। "
                "सारी डिटेल्स और लोकेशन मैंने आपके व्हाट्सएप पर भेज दी हैं!"
            )
        if any(k in t for k in ("busy", "मीटिंग", "व्यस्त", "बाद में", "whatsapp", "व्हाट्सएप")):
            dossier.whatsapp_dispatched = True
            dossier.whatsapp_status = "sent"
            dossier.preferred_channel = "WhatsApp"
            return (
                f"अरे कोई बात नहीं जी, आप काम कर लीजिए... मैंने {business_name} का पूरा ब्रोशर और {cfg['offer_hi']} व्हाट्सएप पर भेज दिया है। "
                "शाम 6 बजे के बाद 2 मिनट कॉल कर लें?"
            )
        return (
            f"नमस्ते सर... {business_name} से स्वाति बोल रही हूँ। "
            f"आपने हमारे {cfg['offer_hi']} के लिए इंक्वायरी की थी — क्या आप इसे इस हफ्ते प्लान कर रहे हैं?"
        )

    # English / India English
    if any(k in t for k in ("discount", "price", "cost", "fee", "rate", "quote")):
        return (
            f"I completely get why pricing matters for {cfg['label']}. "
            f"We tailor custom packages right after your {cfg['offer_en']}. "
            f"Would {cfg['slot_en']} work better for you?"
        )
    if any(k in t for k in ("busy", "meeting", "later", "whatsapp", "email", "text")):
        dossier.whatsapp_dispatched = True
        dossier.whatsapp_status = "sent"
        return (
            f"Totally respect your schedule! I have just sent the {business_name} digital guide and {cfg['offer_en']} details to your WhatsApp. "
            "Should we reconnect for 2 minutes after 6 PM?"
        )
    if any(k in t for k in ("tomorrow", "saturday", "friday", "today", "11", "4", "6", "yes", "sure", "book", "confirm")):
        slot = cfg["slot_en"].split(" or ")[0]
        dossier.appointment_datetime = slot
        dossier.whatsapp_dispatched = True
        dossier.whatsapp_status = "sent"
        dossier.follow_up_note = f"Confirmed {sec_key} session: {slot}"
        return (
            f"Awesome — your {cfg['offer_en']} with {business_name} is locked in for {slot}! "
            "I've sent your confirmation pass and calendar invite directly to your WhatsApp."
        )
    return (
        f"Hi! Thanks for reaching out to {business_name}. We have your {cfg['offer_en']} ready — "
        f"would {cfg['slot_en']} work for a quick session?"
    )
