"""Zero-Hallucination Deflection Guardrails & Telephony Fallbacks."""

from __future__ import annotations
import re
from typing import Optional


class HallucinationDeflector:
    """Detects pricing, discounts, and inventory speculation, enforcing strict deflections."""

    PRICE_TRIGGERS = [
        r"\b(?:discount|discounts|cheap|cheaper|lowest price|negotiat\w*|best offer|deal)\b",
        r"\b(?:per sq\s*ft|rate per foot|exact price|cost per sqft)\b",
        r"\b(?:छूट|डिस्काउंट|रेट|कम करो|कीमत)\b",
        r"\b(?:தள்ளுபடி|குறைவான விலை|ரேட்)\b",
    ]

    DEFLECTION_RESPONSES = {
        "en": "Pricing and milestone discounts are confirmed exclusively during the private site walkthrough. Would Thursday at 4 PM or Saturday 11 AM suit your calendar?",
        "hi": "कीमत और विशेष छूट का निर्णय सीधे साइट विज़िट पर फाइनल होता है। क्या हम इस गुरुवार को 4 बजे का स्लॉट तय करें?",
        "ta": "விலை மற்றும் சிறப்பு சலுகைகள் சைட் விசிட்டின் போது நேரடியாக உறுதி செய்யப்படும். இந்த வியாழன் மாலை 4 மணிக்கு பார்க்கலாமா?",
    }

    def check_and_deflect(self, utterance: str, lang: str = "en") -> Optional[str]:
        lower = utterance.lower()
        for pattern in self.PRICE_TRIGGERS:
            if re.search(pattern, lower, re.IGNORECASE):
                return self.DEFLECTION_RESPONSES.get(lang, self.DEFLECTION_RESPONSES["en"])
        return None
