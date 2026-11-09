"""Zero-Hallucination Deflection Guardrails & Telephony Objection Engine.

Equips CLOSER AI with battle-cards inspired by ScrapeCreators competitor research
and MiroFish adversarial customer swarm intelligence.
Handles:
1. Walkthrough & Visit Confirmations ("Book for Thursday 4 PM / Saturday 11 AM")
2. Price & Discount Deflections (Anchors discount leverage to in-person walkthrough)
3. Competitor Comparisons (Casagrand, Prestige, DLF, Brigade counter-scripts)
4. Legal & RERA Clarity (Cites verified RERA & CMDA approvals, eliminates flood panic)
5. Timing & Brush-Off Deflections ("In a meeting", "WhatsApp details", "busy", "call tomorrow")
6. Macro Real Estate Bubble / Market Crash / Inflation Fears
7. Home Loan & Financing Inquiries (Pre-approved tie-ups with SBI/HDFC/ICICI, FEMA, NRI repatriation, flip)
8. Ultra-Luxury Specs & Amenities (Private pools, high ceilings, EV charging, Vaastu)
"""

from __future__ import annotations
from enum import Enum
import re
from typing import Dict, List, Optional


class ObjectionType(str, Enum):
    VISIT_LOCK = "walkthrough_visit_booking"
    PRICE = "price_negotiation"
    COMPETITOR = "competitor_comparison"
    LEGAL_RERA = "legal_and_compliance"
    TIMING_BUSY = "timing_brush_off"
    MARKET_BUBBLE = "market_and_macro_fears"
    FINANCING = "financing_and_mortgage"
    AMENITIES = "luxury_amenities"
    GENERAL = "general_inquiry"


class HallucinationDeflector:
    """Detects pricing, competitor attacks, and speculative queries, enforcing strict deflections."""

    DAY_TERMS = [
        "thursday", "friday", "saturday", "sunday", "weekend", "tomorrow", "today",
        "வியாழக்கிழமை", "வெள்ளிக்கிழமை", "சனிக்கிழமை", "ஞாயிற்றுக்கிழமை", "ஞாயிறு", "வீக்கெண்ட்", "நாளை",
        "गुरुवार", "शुक्रवार", "शनिवार", "रविवार", "वीकेंड", "कल", "आज"
    ]
    VISIT_TERMS = [
        "visit", "showing", "walkthrough", "book", "schedule", "appointment", "site", "lock in",
        "விசிட்", "பார்க்கலாமா", "புக்", "நேர்ல", "பார்க்க", "காட்ட",
        "विजिट", "वॉकथ्रू", "देखना", "आकर", "बुकिंग", "स्लॉट"
    ]

    PATTERNS: Dict[ObjectionType, List[str]] = {
        ObjectionType.PRICE: [
            r"\b(?:discount|discounts|cheap|cheaper|lowest price|negotiat\w*|best offer|deal|price cut|cash discount|rate per|cost per)\b",
            r"\b(?:square feet|sqft|sq\s*ft|rate|cash payment|10-90|payment plan|cut)\b",
            r"(?:छूट|डिस्काउंट|रेट|कम करो|कीमत|सस्ता|भाव|पैसा|कैश|ऑफर|पेमेंट प्लान)",
            r"(?:தள்ளுபடி|குறைவான விலை|ரேட்|விலை|கம்மி|குறைக்க|பர்சன்ட்|சலுகை|டிஸ்கவுண்ட்|கேஷ்|ஆஃபர்)",
        ],
        ObjectionType.COMPETITOR: [
            r"\b(?:casagrand|prestige|dlf|brigade|puravankara|sobha|appaswamy|hiranandani|competitor|other builder)\b",
            r"(?:காசாக்ராண்ட்|பிரெஸ்டீஜ்|கம்பேர்|வேற ப்ராஜெக்ட்|மற்ற பில்டர்)",
            r"(?:कासाग्रैंड|प्रेस्टीज|डीएलएफ|ब्रिगेड|दूसरी कंपनी|अन्य बिल्डर)",
        ],
        ObjectionType.LEGAL_RERA: [
            r"\b(?:rera|cmda|dtcp|approval|approved|litigation|court|wetland|flood|water\s*logging|delay|handover|title deed|occupancy certificate)\b",
            r"(?:ரேரா|சிஎம்டிஏ|அப்ரூவல்|வெள்ளம்|மழை நீர்|தண்ணி நிக்குமா|தாமதம்|பட்டா|ஆவணங்கள்)",
            r"(?:रेरा|स्वीकृत|अप्रूवल|बाढ़|पानी भरता|कोर्ट केस|कब्ज़ा कब|कानूनी दस्तावेज़)",
        ],
        ObjectionType.TIMING_BUSY: [
            r"\b(?:meeting|busy|call\s+(?:me\s+)?later|call\s+(?:me\s+)?tomorrow|call\s+(?:me\s+)?next week|whatsapp me|send brochure|send details|no time|dont call|don't call)\b",
            r"(?:மீட்டிங்|பிஸி|நாளைக்கு கூப்பிடு|வாட்ஸ்அப்|நேரமில்லை|அப்புறம் பேசு|கால் பண்ணாதீங்க|அனுப்பி வை)",
            r"(?:मीटिंग|व्यस्त|बाद में कॉल|कल कॉल|व्हाट्सएप पर भेजो|समय नहीं|कॉल मत करो|ब्रोशर भेजो)",
        ],
        ObjectionType.MARKET_BUBBLE: [
            r"\b(?:bubble|crash|market down|prices fall|falling prices|recession|wait 6 months|drop|depreciate|inflation)\b",
            r"(?:மார்க்கெட் குறையும்|விலை குறையுமா|சரிவு|பொருளாதாரம்|பணவீக்கம்)",
            r"(?:मंदी|प्राइस गिरेगा|मार्केट क्रैश|बुलबुला|नुकसान|गिरावट)",
        ],
        ObjectionType.AMENITIES: [
            r"\b(?:penthouse\w*|private\s*pool\w*|elevator\w*|lift\w*|vaastu|vastu|carpet\s*area\w*|balcon\w*|park\w*|charg\w*|ceiling\w*|amenit\w*|tidel park|school\w*|layout\w*)\b",
            r"(?:பென்ட்ஹவுஸ்|பிரைவேட் பூல்|லிப்ட்|வாஸ்து|பால்கனி|பார்க்கிங்|ஸ்கூல்|ஐடி பார்க்|லேஅவுட்)",
            r"(?:पेंटहाउस|स्विमिंग पूल|लिफ्ट|वास्तु|बालकनी|पार्किंग|स्कूल|आईटी पार्क|लेआउट)",
        ],
        ObjectionType.FINANCING: [
            r"\b(?:home loan|emi|interest rate|hdfc|sbi|icici|down payment|pre-sanctioned|funding|rental yield|yield|cap rate|fema|repatriation|nri|flip|upside|assign|bank)\b",
            r"(?:லோன்|வங்கி கடன்|இஎம்ஐ|வட்டி விகிதம்|முன்-அங்கீகாரம்|ரென்டல் யீல்டு|என்ஆர்ஐ|முதலீடு|வாடகை|பேங்க்)",
            r"(?:होम लोन|ईएमआई|ब्याज दर|बैंक लोन|किस्त|रेंटल यील्ड|एनआरआई|टैक्स|इन्वेस्टमेंट|बैंक)",
        ],
    }

    RESPONSES: Dict[ObjectionType, Dict[str, str]] = {
        ObjectionType.VISIT_LOCK: {
            "en": "Splendid! Your private walkthrough has been confirmed. I have dispatched your VIP security gate pass and architectural brochure directly to your WhatsApp. Our acquisition specialist looks forward to hosting you.",
            "hi": "बहुत बढ़िया सर! आपका VIP साइट विज़िट स्लॉट कन्फर्म कर दिया गया है। लोकेशन और गेट पास आपके व्हाट्सएप पर भेज दिया गया है जी। हमारे रिलेशनशिप मैनेजर आपका स्वागत करने के लिए तैयार हैं।",
            "ta": "அற்புதம் Sir! உங்களுக்கான விஐபி சைட் விசிட் ஸ்லாட் உறுதி செய்யப்பட்டுள்ளது. கேட் பாஸ் மற்றும் லொகேஷன் உங்கள் வாட்ஸ்அப்பில் அனுப்பப்பட்டுள்ளது. நேர்ல சந்திப்போம் Sir!",
        },
        ObjectionType.PRICE: {
            "en": "I completely understand price is top of mind. The developer authorizes tailored payment structuring and milestone allowances exclusively during the private walkthrough. Would this Thursday at 4 PM or Saturday at 11 AM work better for you?",
            "hi": "मैं बिल्कुल समझती हूँ कि कीमत महत्वपूर्ण है। डेवलपर केवल प्राइवेट साइट विज़िट पर ही कस्टमाइज़्ड पेमेंट प्लान और स्पेशल इंसेंटिव ऑफर करते हैं जी। क्या गुरुवार शाम 4 बजे या शनिवार सुबह 11 बजे का स्लॉट तय करें?",
            "ta": "விலை மற்றும் கட்டண சலுகைகள் சைட் விசிட்டின் போது டெவலப்பரால் நேரடியாக உறுதி செய்யப்படும். இந்த வியாழன் மாலை 4 மணிக்கு பார்க்கலாமா, அல்லது சனிக்கிழமை காலை 11 மணி சௌகரியமா Sir?",
        },
        ObjectionType.COMPETITOR: {
            "en": "Those are respected developers, but their high unit density averages 24 apartments per floor. Our residence offers low-density privacy with only 4 units per floor, double-height ceilings, and dedicated express elevators. Would you like to compare layouts during a walkthrough this Saturday?",
            "hi": "वे अच्छे प्रोजेक्ट्स हैं सर, लेकिन वहाँ एक फ्लोर पर 24 से ज्यादा फ्लैट्स हैं। हमारे यहाँ अल्ट्रा-लो डेंसिटी है—प्रति मंजिल सिर्फ 4 लग्जरी पेंटहाउस और प्राइवेट बालकनी व्यू। क्या शनिवार को आकर खुद कम्पेयर करना चाहेंगे?",
            "ta": "காசாக்ராண்ட் மற்றும் பிரெஸ்டீஜ் நல்ல திட்டங்கள் தான் Sir, ஆனால் அங்கு ஒரு ஃப்ளோருக்கு 20-க்கும் மேற்பட்ட யூனிட்டுகள் உள்ளன. நமது திட்டத்தில் ஃப்ளோருக்கு 4 சொகுசு குடியிருப்புகள் மட்டுமே, அமைதியான சூழல். சனிக்கிழமை நேர்ல வந்து கம்பேர் பண்ணி பார்க்கலாமா Sir?",
        },
        ObjectionType.LEGAL_RERA: {
            "en": "Total peace of mind: our project is 100% RERA registered (TN/01/2026/0482) and CMDA sanctioned with clear title deeds and zero litigation. The structure is elevated 4 feet above road level ensuring a zero-waterlogging zone. Shall I send the legal certificate packet to your WhatsApp and book a site walkthrough this Saturday?",
            "hi": "बिल्कुल निश्चिंत रहें! हमारा प्रोजेक्ट 100% RERA और CMDA अप्रूव्ड है। प्रोजेक्ट को मुख्य सड़क से 4 फीट ऊपर बनाया गया है ताकि जलजमाव की कोई समस्या न हो। क्या मैं सभी लीगल अप्रूवल पेपर्स आपके व्हाट्सएप पर भेजकर इस शनिवार का साइट विज़िट स्लॉट बुक करूँ जी?",
            "ta": "கண்டிப்பா Sir, முழுமையான சட்டப் பாதுகாப்பு உண்டு. இந்த திட்டம் 100% RERA பதிவு செய்யப்பட்டது (TN/01/2026/0482) மற்றும் CMDA அப்ரூவ்டு. தரை மட்டத்திலிருந்து 4 அடி உயர்த்திக் கட்டப்பட்டுள்ளதால் மழை நீர் தேங்காது. அப்ரூவல் சான்றிதழ்களை வாட்ஸ்அப்பில் அனுப்பி இந்த சனிக்கிழமை சைட் விசிட் புக் செய்யட்டுமா Sir?",
        },
        ObjectionType.TIMING_BUSY: {
            "en": "I completely respect your busy schedule! I will follow up with you tomorrow afternoon at 3:00 PM. In the meantime, I’m pinging the 4-page VIP prospectus directly to your WhatsApp so you can review at your leisure. Have a productive day!",
            "hi": "मैं आपका कीमती समय समझती हूँ सर! मैं कल दोपहर ठीक 3:00 बजे आपको दोबारा कॉल करूँगी। तब तक प्रोजेक्ट का VIP ब्रोशर और फ्लोर प्लान आपके व्हाट्सएप पर भेज रही हूँ। आपका दिन शुभ हो!",
            "ta": "கண்டிப்பா புரிஞ்சுக்க முடியுதுங்க Sir! நாளைக்கு மதியம் 3:00 மணிக்கு உங்களுக்கு சௌகரியமான நேரத்துல கூப்பிடுறேன். அதுக்குள்ள ப்ராஜெக்ட் ப்ரோஷர் மற்றும் ஃப்ளோர் பிளான் உங்க வாட்ஸ்அப்புக்கு அனுப்பி வைக்கிறேன் Sir.",
        },
        ObjectionType.MARKET_BUBBLE: {
            "en": "Historical data shows that prime luxury waterfront corridors along OMR appreciate 12-14% annually due to infrastructure scarcity. Holding institutional-grade real estate is the strongest hedge against inflation. A 20-minute site walkthrough will show you why our phase 1 sold out. Would Thursday or Saturday suit you best?",
            "hi": "सर, मेट्रो और आईटी कॉरिडोर में प्राइम लग्जरी प्रॉपर्टीज की सप्लाई बहुत लिमिटेड है, इसलिए यहाँ हर साल 12 से 14% की स्थिर कैपिटल ग्रोथ देखी जा रही है। क्या इस शनिवार हम 20 मिनट के लिए साइट देख सकते हैं?",
            "ta": "மெட்ரோ மற்றும் ஐடி காரிடார் உள்ள OMR பகுதிகளில் நில மதிப்பு தொடர்ந்து ஆண்டுக்கு 12-14% உயர்ந்து வருகிறது Sir. தரமான ரியல் எஸ்டேட் எப்போதும் பாதுகாப்பான முதலீடு. இந்த சனிக்கிழமை நேர்ல வந்து பார்த்தீங்கன்னா உங்களுக்கே முழு தெளிவு கிடைக்கும் Sir.",
        },
        ObjectionType.FINANCING: {
            "en": "We have institutional tie-ups with SBI, HDFC, and ICICI Bank offering pre-sanctioned rates starting at 8.35% with flexible milestone disbursements. For NRI buyers, our desk manages 100% of FEMA compliance and RBI tax repatriation. Would you like to review pre-approvals during a site walkthrough this Saturday?",
            "hi": "हमारे पास SBI, HDFC और ICICI बैंक से एक्सक्लूसिव टाइ-अप है जहाँ 8.35% से होम लोन और फ्लेक्सिबल ईएमआई उपलब्ध है। एनआरआई बायर्स के लिए टैक्स और फेमा कम्पलायंस भी हमारी टीम करवाती है जी। क्या इस शनिवार साइट विज़िट पर इसके बारे में चर्चा करें?",
            "ta": "SBI, HDFC மற்றும் ICICI வங்கிகளில் 8.35% ஆரம்ப வட்டி விகிதத்தில் முன்-அங்கீகரிக்கப்பட்ட வீட்டுக் கடன் வசதி உள்ளது Sir. NRI வாடிக்கையாளர்களுக்கு FEMA மற்றும் வரி நடைமுறைகளை எங்களது லீகல் டீம் இலவசமாக செய்து தரும். சனிக்கிழமை சைட் விசிட்டின் போது வங்கி மேலாளருடன் பேச ஏற்பாடு செய்யட்டுமா Sir?",
        },
        ObjectionType.AMENITIES: {
            "en": "Every penthouse residence includes high 11-foot ceilings, an Italian marble deck, a private terrace plunge pool, 4 covered basement EV-ready parking slots, and 100% Vaastu-compliant layouts. Let's arrange a walkthrough this weekend so you can experience the volume in person. Which time suits you best?",
            "hi": "हमारे हर पेंटहाउस में 11 फीट ऊँची छतें, इटैलियन मार्बल, प्राइवेट टेरेस प्लंज पूल और 100% वास्तु-सम्मत नॉर्थ-ईस्ट फेसिंग लेआउट है जी। क्या शनिवार को आकर इसे साक्षात देखना चाहेंगे?",
            "ta": "ஒவ்வொரு பென்ட்ஹவுஸிலும் 11 அடி உயரமான கூரை, இத்தாலியன் மார்பிள், பிரைவேட் டெரஸ் பூல் மற்றும் 100% வாஸ்து முறைப்படி அமைக்கப்பட்ட லேஅவுட் உள்ளது Sir. சனிக்கிழமை நேர்ல வந்து பார்க்க ஸ்லாட் புக் செய்யட்டுமா Sir?",
        },
        ObjectionType.GENERAL: {
            "en": "That fits our luxury portfolio exceptionally well. Our acquisition manager is hosting private walkthroughs this Thursday and Saturday. Which day would suit your schedule best?",
            "hi": "यह हमारी लक्जरी इन्वेंट्री से बिल्कुल मैच करता है जी। क्या आप इस गुरुवार या शनिवार को एक प्राइवेट वॉकथ्रू के लिए आना पसंद करेंगे?",
            "ta": "உங்க எதிர்பார்ப்புக்கு ஏத்த மாதிரி மிகச்சிறந்த ரெசிடென்ஸஸ் இருக்குங்க Sir. இந்த வியாழன் அல்லது சனிக்கிழமை சைட் விசிட் பார்க்க எந்த நேரம் சௌகரியமா இருக்கும் Sir?",
        },
    }

    def classify_objection(self, utterance: str) -> ObjectionType:
        """Deterministically classifies customer objection into canonical categories."""
        if not utterance:
            return ObjectionType.GENERAL
        lower = utterance.lower()

        # 1. Check Visit Booking Intent (Day/Time + Visit/Booking Action)
        has_day = any(d in lower for d in self.DAY_TERMS)
        has_visit = any(v in lower for v in self.VISIT_TERMS)
        if has_day and has_visit:
            return ObjectionType.VISIT_LOCK

        # 2. Check Timing / Busy Brush-Off
        for pat in self.PATTERNS[ObjectionType.TIMING_BUSY]:
            if re.search(pat, lower, re.IGNORECASE):
                return ObjectionType.TIMING_BUSY

        # 3. Check Price Negotiation & Discounts
        for pat in self.PATTERNS[ObjectionType.PRICE]:
            if re.search(pat, lower, re.IGNORECASE):
                return ObjectionType.PRICE

        # 4. Check Competitor Comparisons
        for pat in self.PATTERNS[ObjectionType.COMPETITOR]:
            if re.search(pat, lower, re.IGNORECASE):
                return ObjectionType.COMPETITOR

        # 5. Check Legal & RERA
        for pat in self.PATTERNS[ObjectionType.LEGAL_RERA]:
            if re.search(pat, lower, re.IGNORECASE):
                return ObjectionType.LEGAL_RERA

        # 6. Check Market Bubble & Real Estate Crashes
        for pat in self.PATTERNS[ObjectionType.MARKET_BUBBLE]:
            if re.search(pat, lower, re.IGNORECASE):
                return ObjectionType.MARKET_BUBBLE

        # 7. Check Amenities & Layout Specs
        for pat in self.PATTERNS[ObjectionType.AMENITIES]:
            if re.search(pat, lower, re.IGNORECASE):
                return ObjectionType.AMENITIES

        # 8. Check Financing, Home Loan, NRI Yields & Flips
        for pat in self.PATTERNS[ObjectionType.FINANCING]:
            if re.search(pat, lower, re.IGNORECASE):
                return ObjectionType.FINANCING

        return ObjectionType.GENERAL

    def check_and_deflect(self, utterance: str, lang: str = "en") -> Optional[str]:
        """Returns the high-converting deflection script for any objection."""
        obj_type = self.classify_objection(utterance)
        if obj_type == ObjectionType.GENERAL:
            return None
        lang_key = "ta" if ("ta" in lang or "tam" in lang) else ("hi" if ("hi" in lang or "hin" in lang) else "en")
        responses = self.RESPONSES.get(obj_type, self.RESPONSES[ObjectionType.PRICE])
        return responses.get(lang_key, responses["en"])
