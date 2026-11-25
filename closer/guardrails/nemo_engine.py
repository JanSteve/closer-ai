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
                    "I am CLOSER AI, the patient care concierge for Amura Health in Velachery, Chennai. "
                    "I am dedicated exclusively to helping you with clinical onboarding and physician consultations. "
                    "Would you like to book a consultation?"
                )
                if "ta" in lang:
                    deflection = (
                        "வணக்கம் Sir, நான் வேளச்சேரி Amura Health மருத்துவ மனையின் பிரத்யேக நோயாளி ஆலோசகர். "
                        "உங்கள் ஆரோக்கியம் மற்றும் மருத்துவர் ஆலோசனை குறித்து மட்டுமே நான் உதவ முடியும். "
                        "மருத்துவர் ஆலோசனை நேரம் முன்பதிவு செய்யலாமா Sir?"
                    )
                elif "hi" in lang:
                    deflection = (
                        "नमस्ते जी, मैं वेलाचेरी Amura Health क्लिनिक की अधिकृत पेशेंट केयर असिस्टेंट हूँ। "
                        "मैं केवल आपकी स्वास्थ्य जानकारी और डॉक्टर कंसल्टेशन में सहायता कर सकती हूँ। "
                        "क्या हम डॉक्टर अपॉइंटमेंट शेड्यूल करें?"
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
                    "I completely understand your frustration and apologize for any delay. "
                    "Your care is our top priority—let me connect you directly with our senior care coordinator."
                )
                if "ta" in lang:
                    calm_reply = (
                        "உங்கள் ஆதங்கம் புரிகிறது Sir. எங்கள் மருத்துவக் குழுவின் தாமதத்திற்கு மன்னிக்கவும். "
                        "உங்களுக்கு உடனடி உதவி கிடைக்க மூத்த மருத்துவ ஒருங்கிணைப்பாளரை இணைக்கிறேன் Sir."
                    )
                elif "hi" in lang:
                    calm_reply = (
                        "मैं आपकी परेशानी पूरी तरह समझती हूँ जी, देरी के लिए क्षमा चाहती हूँ। "
                        "मैं तुरंत हमारे सीनियर केयर कोऑर्डिनेटर से आपकी बात कराती हूँ।"
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

        # 1. Hallucinated Clinical/Financial Commitments
        for pat in cls.UNAUTHORIZED_GUARANTEES:
            if re.search(pat, lower, re.IGNORECASE):
                safe_correction = (
                    "Program pricing and personalized Natural Molecule Therapy protocols are finalized exclusively "
                    "after a licensed Amura Health physician reviews your biomarkers. Would tomorrow at 11:30 AM or Friday at 5:00 PM work?"
                )
                if "ta" in lang:
                    safe_correction = (
                        "கட்டணம் மற்றும் சிகிச்சைத் திட்டம் எங்கள் Amura Health மருத்துவர் உங்கள் பரிசோதனை முடிவுகளைப் பார்த்த பிறகே உறுதி செய்யப்படும். "
                        "நாளை காலை 11:30 மணி அல்லது சனிக்கிழமை காலை 11 மணி சௌகரியமா Sir?"
                    )
                elif "hi" in lang:
                    safe_correction = (
                        "प्रोग्राम शुल्क और पर्सनलाइज्ड प्रोटोकॉल हमारे Amura Health डॉक्टर द्वारा आपकी लैब रिपोर्ट देखने के बाद ही तय किए जाते हैं। "
                        "क्या कल सुबह 11:30 बजे या शनिवार सुबह 11 बजे का स्लॉट तय करें?"
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
