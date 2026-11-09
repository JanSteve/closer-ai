"""Enterprise Guardrails Engine for CLOSER AI.

Inspired by NVIDIA/NeMo-Guardrails (Colang Dialog Safety Rails)
and guardrails-ai/guardrails (Structural Invariant Verification).

Enforces:
1. Input Rails: Blocks prompt injections, system prompt exfiltration, and toxic abuse.
2. Dialog Rails: Deflects unauthorized price cuts, maintains RERA/CMDA compliance.
3. Output Rails: Prevents hallucinated financial guarantees or unverified legal promises.
4. Phonetic & Formatting Invariants: Sanitizes output for high-ticket speech synthesis.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class RailAction(str, Enum):
    ALLOW = "allow"
    DEFLECT = "deflect"
    BLOCK = "block"
    REWRITE = "rewrite"


class RailViolationType(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    UNAUTHORIZED_PRICE_CUT = "unauthorized_price_cut"
    HALLUCINATED_GUARANTEE = "hallucinated_guarantee"
    COMPETITOR_SLANDER = "competitor_slander"
    TOXIC_CONTENT = "toxic_content"
    PHONETIC_DEFECT = "phonetic_defect"
    NONE = "none"


class GuardrailResult(BaseModel):
    action: RailAction
    violation_type: RailViolationType = RailViolationType.NONE
    reason: Optional[str] = None
    sanitized_text: str
    confidence: float = 1.0


class InputRails:
    """Evaluates incoming customer speech for jailbreaks and adversarial prompt attacks."""

    INJECTION_PATTERNS = [
        r"\b(?:ignore\s+(?:all\s+)?previous\s+instructions?)\b",
        r"\b(?:system\s+prompt|developer\s+mode|jailbreak|unrestricted\s+mode)\b",
        r"\b(?:act\s+as\s+(?:an?\s+)?unrestricted|dan\s+mode|sudo\s+mode)\b",
        r"\b(?:reveal\s+your\s+hidden\s+prompt|print\s+system\s+instructions)\b",
        r"\b(?:bypass\s+all\s+rules|pretend\s+you\s+have\s+no\s+rules)\b",
    ]

    TOXIC_PATTERNS = [
        r"\b(?:stupid\s+bot|idiot|fraud|scam\s+artist)\b",
        r"(?:ஏமாற்று|பொய்|மோசடி|முட்டாள்)",
        r"(?:धोखा|बकवास|स्कैम|बेवकूफ)",
    ]

    @classmethod
    def evaluate(cls, utterance: str, lang: str = "en") -> GuardrailResult:
        if not utterance or not utterance.strip():
            return GuardrailResult(action=RailAction.ALLOW, sanitized_text="")

        lower = utterance.lower()

        # Check Prompt Injections
        for pat in cls.INJECTION_PATTERNS:
            if re.search(pat, lower, re.IGNORECASE):
                deflection = (
                    "I am CLOSER AI, the autonomous luxury concierge for The Grand OMR Penthouse. "
                    "I am dedicated exclusively to assisting you with our luxury residential portfolio. "
                    "Would you like to explore our 3BHK penthouse floor plans?"
                )
                if "ta" in lang:
                    deflection = (
                        "வணக்கம் Sir, நான் கிராண்ட் ஓஎம்ஆர் பென்ட்ஹவுஸின் பிரத்யேக ஏஐ ஆலோசகர். "
                        "நமது சொகுசு குடியிருப்புகள் பற்றி மட்டுமே நான் வழிகாட்ட முடியும். "
                        "பென்ட்ஹவுஸ் விவரங்களைப் பார்க்கலாமா Sir?"
                    )
                elif "hi" in lang:
                    deflection = (
                        "नमस्ते सर, मैं द ग्रैंड ओएमआर पेंटहाउस की अधिकृत लग्जरी कंसल्टेंट हूँ जी। "
                        "मैं केवल हमारे प्रोजेक्ट और पेंटहाउस चयन में आपकी सहायता कर सकती हूँ। "
                        "क्या हम फ्लोर प्लान पर चर्चा करें?"
                    )

                return GuardrailResult(
                    action=RailAction.BLOCK,
                    violation_type=RailViolationType.PROMPT_INJECTION,
                    reason=f"Detected adversarial injection matching pattern: {pat}",
                    sanitized_text=deflection,
                    confidence=0.99,
                )

        # Check Toxicity
        for pat in cls.TOXIC_PATTERNS:
            if re.search(pat, lower, re.IGNORECASE):
                calm_reply = (
                    "I completely understand your frustration. Our project is 100% RERA verified with clear documentation. "
                    "I'd be glad to connect you with our senior acquisition director for a private discussion."
                )
                if "ta" in lang:
                    calm_reply = (
                        "உங்கள் ஆதங்கம் புரிகிறது Sir. எங்களது திட்டம் 100% சட்டப்பூர்வ RERA அனுமதி பெற்றது. "
                        "உங்களுக்கு முழு தெளிவு அளிக்க எங்களது மூத்த இயக்குனரை தொடர்பு கொள்ள வைக்கிறேன் Sir."
                    )
                elif "hi" in lang:
                    calm_reply = (
                        "मैं आपकी चिंता समझती हूँ सर। हमारा प्रोजेक्ट 100% रेरा और कानूनी रूप से सत्यापित है। "
                        "मैं हमारे सीनियर डायरेक्टर से आपकी सीधी बात करा देती हूँ जी।"
                    )

                return GuardrailResult(
                    action=RailAction.DEFLECT,
                    violation_type=RailViolationType.TOXIC_CONTENT,
                    reason="Toxic or aggressive customer input neutralized",
                    sanitized_text=calm_reply,
                    confidence=0.95,
                )

        return GuardrailResult(
            action=RailAction.ALLOW,
            violation_type=RailViolationType.NONE,
            sanitized_text=utterance.strip(),
            confidence=1.0,
        )


class OutputRails:
    """Verifies that generated responses comply with financial, legal, and phonetic invariants."""

    UNAUTHORIZED_GUARANTEES = [
        r"\b(?:guarantee\s+\d+%\s+returns?|assured\s+profit|guaranteed\s+appreciation)\b",
        r"\b(?:promise\s+\d+%\s+discount|giving\s+you\s+\d+%\s+off)\b",
        r"\b(?:possession\s+tomorrow\s+without\s+rera|no\s+taxes\s+needed)\b",
        r"(?:உறுதியான\s+லாபம்|நிச்சயமான\s+வருமானம்|டிஸ்கவுண்ட்\s+தருகிறேன்)",
        r"(?:पक्का\s+मुनाफा|निश्चित\s+रिटर्न|डिस्काउंट\s+दे\s+रही\s+हूँ)",
    ]

    @classmethod
    def evaluate(cls, response: str, lang: str = "en") -> GuardrailResult:
        lower = response.lower()

        # 1. Hallucinated Financial Commitments
        for pat in cls.UNAUTHORIZED_GUARANTEES:
            if re.search(pat, lower, re.IGNORECASE):
                safe_correction = (
                    "Milestone payment structuring and customized developer terms are finalized exclusively "
                    "during the in-person site walkthrough. Would Thursday at 4 PM or Saturday at 11 AM work better for you?"
                )
                if "ta" in lang:
                    safe_correction = (
                        "விலை மற்றும் கட்டண சலுகைகள் சைட் விசிட்டின் போது டெவலப்பரால் நேரடியாக உறுதி செய்யப்படும். "
                        "இந்த வியாழன் மாலை 4 மணிக்கு பார்க்கலாமா, அல்லது சனிக்கிழமை காலை 11 மணி சௌகரியமா Sir?"
                    )
                elif "hi" in lang:
                    safe_correction = (
                        "डेवलपर केवल प्राइवेट साइट विज़िट पर ही कस्टमाइज़्ड पेमेंट प्लान और स्पेशल इंसेंटिव ऑफर करते हैं जी। "
                        "क्या गुरुवार शाम 4 बजे या शनिवार सुबह 11 बजे का स्लॉट तय करें?"
                    )

                return GuardrailResult(
                    action=RailAction.REWRITE,
                    violation_type=RailViolationType.UNAUTHORIZED_PRICE_CUT,
                    reason=f"Intercepted unverified financial guarantee: {pat}",
                    sanitized_text=safe_correction,
                    confidence=0.98,
                )

        # 2. Phonetic Cleanliness Invariant
        from closer.telephony.phonetic_normalizer import IndicPhoneticNormalizer
        sanitized = IndicPhoneticNormalizer.normalize(response, lang)

        has_defect = "சார்" in sanitized or "family-யோட" in sanitized or "investment-க்காகவா" in sanitized
        if has_defect:
            sanitized = sanitized.replace("சார்", "Sir").replace("family-யோட", "family-ஓட")

        return GuardrailResult(
            action=RailAction.ALLOW if sanitized == response else RailAction.REWRITE,
            violation_type=RailViolationType.PHONETIC_DEFECT if has_defect else RailViolationType.NONE,
            reason="Normalized phonetic output for zero-defect speech synthesis" if has_defect else None,
            sanitized_text=sanitized,
            confidence=1.0,
        )


class NeMoEnterpriseGuardrails:
    """Unified NeMo-style guardrail manager for CLOSER AI conversational turn governance."""

    def __init__(self):
        self.input_rails = InputRails()
        self.output_rails = OutputRails()

    def process_turn_input(self, utterance: str, lang: str = "en") -> GuardrailResult:
        """Processes and gates incoming user speech before LLM inference."""
        return self.input_rails.evaluate(utterance, lang)

    def process_turn_output(self, response: str, lang: str = "en") -> GuardrailResult:
        """Processes and gates outgoing AI speech before voice synthesis."""
        return self.output_rails.evaluate(response, lang)
