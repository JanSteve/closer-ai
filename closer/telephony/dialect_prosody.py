"""Regional Dialect, Colloquial Slang, Filler & Breath-Pause Engine for CLOSER AI.

Transforms formal/textbook Hindi and Tamil responses into authentic, warm, human-sounding
telecaller speech with regional dialects (Chennai Tanglish, Coimbatore respectful Tamil,
Delhi Hinglish, Mumbai Hinglish), colloquial verbs, natural micro-fillers, and breath-pause
clause segmentation.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from closer.telephony.phonetic_normalizer import IndicPhoneticNormalizer


SUPPORTED_DIALECTS: Dict[str, Dict[str, str]] = {
    "chennai_tanglish": {
        "language": "tamil",
        "label": "Chennai Tanglish (Warm Urban Telecaller)",
        "style_prompt": (
            "A warm, approachable Chennai woman speaking natural Tamil blended with "
            "conversational English words, relaxed pace, gentle pauses, close mic studio clarity."
        ),
    },
    "coimbatore_tamil": {
        "language": "tamil",
        "label": "Coimbatore Kongu Tamil (Polite '-nga' Cadence)",
        "style_prompt": (
            "A polite Coimbatore Tamil speaker with soft respectful intonation, calm steady pace, "
            "natural breathing pauses, crystal clear voice."
        ),
    },
    "madurai_warm": {
        "language": "tamil",
        "label": "Madurai Warm Hospitality (Southern Cadence)",
        "style_prompt": (
            "A friendly warm South Indian female speaker with welcoming tone, expressive pauses, "
            "and clear studio quality."
        ),
    },
    "delhi_hinglish": {
        "language": "hindi",
        "label": "Delhi NCR Hinglish (Sharp & Friendly Closer)",
        "style_prompt": (
            "A confident, friendly North Indian woman from Delhi speaking natural conversational "
            "Hindi mixed with English terms, subtle pauses, natural breath, clean studio mic."
        ),
    },
    "mumbai_hinglish": {
        "language": "hindi",
        "label": "Mumbai Hinglish (Casual Urban Rapport)",
        "style_prompt": (
            "An upbeat, warm Mumbai conversationalist speaking relaxed Hinglish with smooth "
            "rhythm, light pauses, and natural studio fidelity."
        ),
    },
    "lucknow_polite": {
        "language": "hindi",
        "label": "Lucknowi Polite Hindi (High-Touch VIP Concierge)",
        "style_prompt": (
            "A gracious, soft-spoken Indian woman with polished etiquette, measured breathing "
            "pauses, and expressive warm studio audio."
        ),
    },
    "english_consultative": {
        "language": "english",
        "label": "Consultative English (Locked Kokoro 3-Way Blend)",
        "style_prompt": "Warm, polished consultative advisor with natural pauses.",
    },
}

DEFAULT_DIALECT_BY_LANGUAGE: Dict[str, str] = {
    "tamil": "chennai_tanglish",
    "hindi": "delhi_hinglish",
    "english": "english_consultative",
}

# Formal/bookish Tamil -> everyday Chennai/Coimbatore spoken Tanglish
_TAMIL_SPOKEN_REWRITES: List[Tuple[str, str]] = [
    (r"உறுதி\s*செய்யப்பட்டுள்ளது", "கன்ஃபார்ம் பண்ணியாச்சுங்க"),
    (r"அனுப்பப்பட்டுள்ளது", "அனுப்பிட்டோமுங்க"),
    (r"பகிரப்பட்டுள்ளது", "ஷேர் பண்ணியாச்சுங்க"),
    (r"செய்யப்பட்டுள்ளது", "பண்ணியாச்சுங்க"),
    (r"செய்யப்படும்", "பண்ணிடலாம்"),
    (r"மிகச்சிறந்த", "சூப்பரான"),
    (r"எங்களது\s+", "நம்ம "),
    (r"நமது\s+", "நம்ம "),
    (r"உங்களுடைய\s+", "உங்க "),
    (r"உங்களது\s+", "உங்க "),
    (r"பார்வையிட", "நேர்ல வந்து பார்க்க"),
    (r"தயவுசெய்து", "கொஞ்சம்"),
    (r"சௌகரியமாக", "கன்வீனியன்ட்டா"),
    (r"சௌகரியமா", "கன்வீனியன்ட்டா"),
    (r"\s+மற்றும்\s+", ", அப்புறம் "),
    (r"விஐபி\s*சைட்\s*விசிட்", "VIP site visit"),
    (r"சைட்\s*விசிட்", "site visit"),
    (r"வாட்ஸ்அப்பில்", "WhatsApp-ல"),
    (r"வாட்ஸ்அப்", "WhatsApp"),
    (r"(?i)\bspecial\s+discount\b", "ஸ்பெஷல் டிஸ்கவுண்ட்"),
    (r"(?i)\bdiscount\b", "டிஸ்கவுண்ட்"),
    (r"(?i)\bbest\s+package\b", "பெஸ்ட் பேக்கேஜ்"),
    (r"(?i)\bpayment\s+plan\b", "பேமெண்ட் பிளான்"),
    (r"(?i)\bpayment\s+options?\b", "பேமெண்ட் ஆப்ஷன்ஸ்"),
    (r"(?i)\bfloor\s+plan\b", "ஃப்ளோர் பிளான்"),
]

# Formal/textbook Hindi -> warm Delhi/Mumbai spoken Hinglish
_HINDI_SPOKEN_REWRITES: List[Tuple[str, str]] = [
    (r"कन्फ़र्म\s*कर\s*दी\s*है", "पक्का कन्फ़र्म कर दिया है जी"),
    (r"कन्फर्म\s*कर\s*दिया\s*गया\s*है", "पक्का कन्फर्म हो गया है जी"),
    (r"सहायता\s*कर\s*सकती\s*हूँ", "मदद कर सकती हूँ जी"),
    (r"सहायता\s*के\s*लिए\s*तैयार", "मदद के लिए तैयार"),
    (r"उपलब्ध\s*हैं", "मिल जाएंगे जी"),
    (r"सुनिश्चित", "पक्का"),
    (r"प्रदान\s*करते\s*हैं", "देते हैं जी"),
    (r"कृपया", "प्लीज़"),
    (r"वॉट्सऐप", "व्हाट्सएप"),
    (r"जानकारी\s*साझा\s*करने\s*के\s*लिए\s*बहुत\s*धन्यवाद", "बताने के लिए थैंक यू सो मच जी"),
]

_DIALECT_FILLERS: Dict[str, Dict[str, str]] = {
    "chennai_tanglish": {
        "ack": "ஆமாங்க Sir... ",
        "thinking": "ஒரு நிமிஷம் இருங்க... ",
        "objection": "அட, ரொம்ப நியாயமான கேள்வி Sir... பாருங்க — ",
        "customer_casual": "ஹலோ பாஸ்... ",
    },
    "coimbatore_tamil": {
        "ack": "நல்லதுங்க Sir... ",
        "thinking": "கொஞ்சம் இருங்க... ",
        "objection": "நீங்க கேக்குறது கரெக்ட்டுங்க Sir... ",
        "customer_casual": "வணக்கம்ங்க... ",
    },
    "madurai_warm": {
        "ack": "சரிங்க Sir... ",
        "thinking": "ஒரு நிமிஷம்... ",
        "objection": "கண்டிப்பா நல்ல கேள்வி Sir... ",
        "customer_casual": "ஹலோ அண்ணே... ",
    },
    "delhi_hinglish": {
        "ack": "हाँजी सर... ",
        "thinking": "एक सेकंड रुकिए जी... ",
        "objection": "अरे बिल्कुल सही पूछा आपने सर... देखो — ",
        "customer_casual": "अरे भई... ",
    },
    "mumbai_hinglish": {
        "ack": "अरे हाँजी... ",
        "thinking": "सुनिए ना, एक सेकंड... ",
        "objection": "बिल्कुल समझ सकती हूँ सर... अपन एक काम करते हैं — ",
        "customer_casual": "अरे बॉस... ",
    },
    "lucknow_polite": {
        "ack": "जी बिल्कुल... ",
        "thinking": "एक पल ठहरिए जी... ",
        "objection": "आपने बहुत वाजिब बात पूछी है जी... ",
        "customer_casual": "जी सुनिए... ",
    },
}


class IndicDialectProsodyEngine:
    """Adds regional dialects, colloquial slang, conversational fillers, and breath pauses."""

    @staticmethod
    def resolve_language(language: str) -> str:
        low = (language or "english").lower()
        if any(k in low for k in ("tam", "pallavi", "ta-in", "chennai", "coimbatore", "madurai")):
            return "tamil"
        if any(k in low for k in ("hin", "swati", "swara", "madhur", "hi-in", "delhi", "mumbai", "lucknow")):
            return "hindi"
        return "english"

    @staticmethod
    def resolve_dialect(language: str, dialect: Optional[str] = None) -> str:
        lang = IndicDialectProsodyEngine.resolve_language(language)
        if dialect and dialect in SUPPORTED_DIALECTS:
            return dialect
        return DEFAULT_DIALECT_BY_LANGUAGE.get(lang, "english_consultative")

    @classmethod
    def get_style_prompt(cls, language: str, dialect: Optional[str] = None) -> str:
        resolved = cls.resolve_dialect(language, dialect)
        return SUPPORTED_DIALECTS[resolved]["style_prompt"]

    @classmethod
    def humanize(
        cls,
        text: str,
        language: str,
        dialect: Optional[str] = None,
        inject_pauses: bool = True,
        inject_fillers: bool = False,
        intent_hint: str = "ack",
        customer_mode: bool = False,
    ) -> str:
        """Applies phonetic normalization, colloquial dialect rewrites, fillers, and breath pauses."""
        if not text:
            return text

        lang = cls.resolve_language(language)
        if lang == "english":
            # Never disturb the locked-in English Kokoro phrasing unless explicit filler requested
            return IndicPhoneticNormalizer.normalize(text, "english")

        resolved_dialect = cls.resolve_dialect(lang, dialect)

        # 1. Run base phonetic normalization (சார்->Sir, hyphen fix, ₹ naturalization)
        normalized = IndicPhoneticNormalizer.normalize(text, lang)

        # 2. Apply colloquial spoken dialect rewrites (avoid altering when customer_mode keeps raw slang)
        if lang == "tamil" and not customer_mode:
            for pat, rep in _TAMIL_SPOKEN_REWRITES:
                normalized = re.sub(pat, rep, normalized)
            if resolved_dialect == "coimbatore_tamil":
                normalized = normalized.replace("பண்ணியாச்சுங்க", "பண்ணிட்டோமுங்க")
                normalized = normalized.replace("இருக்குங்க", "இருக்குதுங்க")
        elif lang == "hindi" and not customer_mode:
            for pat, rep in _HINDI_SPOKEN_REWRITES:
                normalized = re.sub(pat, rep, normalized)
            if resolved_dialect == "mumbai_hinglish":
                normalized = normalized.replace("हम ", "अपन ").replace("बिल्कुल सर", "बिल्कुल बॉस")

        # 3. Conversational pause & breath markers around discourse transitions
        if inject_pauses:
            if lang == "tamil":
                normalized = re.sub(
                    r"\b(வணக்கம் Sir|ஹலோ Sir|ஆமாங்க|சரிங்க|கண்டிப்பா Sir|அற்புதம் Sir)\s*[!,]?\s*(?!\.\.\.)",
                    r"\1... ",
                    normalized,
                )
                normalized = re.sub(r"\s+(ஆனால்|இல்லனா|அதே சமயம்)\s+", r"... \1 ", normalized)
            elif lang == "hindi":
                normalized = re.sub(
                    r"(नमस्ते सर|हाँजी बिल्कुल|बिल्कुल सर|अरे हाँजी|बहुत बढ़िया सर|जी बिल्कुल)\s*[!,।]?\s*(?!\.\.\.)",
                    r"\1... ",
                    normalized,
                )
                normalized = re.sub(r"\s+(लेकिन|तो फिर|बाकी)\s+", r", \1 ", normalized)

        # 4. Optional spoken filler prefix (without duplicating existing greeting fillers)
        if inject_fillers:
            filler_bank = _DIALECT_FILLERS.get(resolved_dialect, {})
            key = "customer_casual" if customer_mode else intent_hint
            filler = filler_bank.get(key) or filler_bank.get("ack", "")
            starter_tokens = ("ஹலோ", "வணக்கம்", "ஆமாங்க", "சரிங்க", "அட", "நல்லதுங்க", "हाँजी", "नमस्ते", "अरे", "बिल्कुल", "जी ")
            if filler and not normalized.lstrip().startswith(starter_tokens):
                normalized = f"{filler}{normalized}"

        # Clean repeated ellipses, excessive whitespace, and stray punctuation
        normalized = re.sub(r"(?:\.\.\.\s*){2,}", "... ", normalized)
        normalized = re.sub(r"\.{4,}", "...", normalized)
        normalized = re.sub(r"\s{2,}", " ", normalized).strip()
        return normalized

    @classmethod
    def segment_breath_clauses(
        cls,
        text: str,
        sentence_pause_s: float = 0.28,
        ellipsis_pause_s: float = 0.20,
        comma_pause_s: float = 0.12,
    ) -> List[Tuple[str, float]]:
        """Splits text into (spoken_clause, trailing_pause_seconds) pairs for realistic breath cadence."""
        if not text or not text.strip():
            return []

        parts = re.split(r"(\.\.\.|[?!।.]|—)", text.strip())
        clauses: List[Tuple[str, float]] = []
        buf = ""
        for part in parts:
            if not part:
                continue
            if part == "...":
                if buf.strip():
                    clauses.append((buf.strip(), ellipsis_pause_s))
                    buf = ""
            elif part == "—":
                if buf.strip():
                    clauses.append((buf.strip(), comma_pause_s))
                    buf = ""
            elif part in (".", "?", "!", "।"):
                combined = (buf + part).strip()
                if combined:
                    clauses.append((combined, sentence_pause_s))
                buf = ""
            else:
                buf += part

        if buf.strip():
            clauses.append((buf.strip(), 0.0))

        # Avoid trailing long pause at very end of utterance
        if clauses:
            last_text, _ = clauses[-1]
            clauses[-1] = (last_text, 0.04)
        return clauses
