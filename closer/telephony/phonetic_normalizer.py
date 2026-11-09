"""Indic Phonetic and Conversational Normalizer for CLOSER AI.

Solves the classic issues in Indian Code-Mixed (Tanglish & Hinglish) Telecaller TTS:
1. "Saar" vs "Sir": Replaces Tamil orthographic 'சார்' (/saːr/) with crisp, respectful 'Sir' (/sɜːr/).
2. De-duplication: Prevents awkward telecaller repetition of 'Sir... Sir... Sir'.
3. Hyphenation Artifacts: Fixes stuttering caused by mixed-script hyphens like 'family-யோட' -> 'ஃபேமிலியோட' or 'family ஓட'.
4. Natural Currency & Number Cadence: Translates '1.5 Crores' into colloquial 'ஒன்றரை கோடி' (Tamil) or 'डेढ़ करोड़' (Hindi).
5. Spoken Telecaller Warmth: Converts stiff textbook Tamil (செந்தமிழ்) and stiff Hindi into sweet, consultative telecaller cadence.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


class IndicPhoneticNormalizer:
    """Enterprise text normalizer for conversational Tanglish, Hinglish, and English."""

    # Tamil colloquial transliterations using Unicode boundary lookarounds
    TAMIL_REPLACEMENTS: List[Tuple[str, str]] = [
        # The 'Saar' fix: replace Tamil grapheme 'சார்' with crisp English token 'Sir'
        (r"(?<![\u0B80-\u0BFF])சார்(?![\u0B80-\u0BFF])", "Sir"),
        (r"(?<![\u0B80-\u0BFF])சாருக்கு(?![\u0B80-\u0BFF])", "Sir-க்கு"),
        (r"(?<![\u0B80-\u0BFF])சார்கிட்ட(?![\u0B80-\u0BFF])", "Sir-கிட்ட"),
        
        # Hyphenated code-switching fixes
        (r"\bfamily[-–]யோட\b", "ஃபேமிலியோட"),
        (r"\bfamily[-–]உடன்\b", "ஃபேமிலியோட"),
        (r"\binvestment[-–]க்காகவா\b", "இன்வெஸ்ட்மென்ட்க்காகவா"),
        (r"\binvestment[-–]க்காக\b", "இன்வெஸ்ட்மென்ட்க்காக"),
        (r"\bbudget[-–]க்கு\b", "பட்ஜெட்டுக்கு"),
        (r"\bsite visit[-–]க்கு\b", "site visit-க்கு"),
        
        # Real estate conversational currency & units
        (r"\b1\.5\s*(?:Crores?|Cr|கோடி)[-–]?(?:க்குள்ள|க்கு)?\b", "ஒன்றரை கோடிக்குள்ள"),
        (r"\b1\.5\s*(?:Crores?|Cr|கோடி)\b", "ஒன்றரை கோடி"),
        (r"\b2\.5\s*(?:Crores?|Cr|கோடி)\b", "இரண்டரை கோடி"),
        (r"\b3BHK\b", "3 BHK"),
        (r"\b2BHK\b", "2 BHK"),
        (r"\b4BHK\b", "4 BHK"),
        
        # Time and calendar conversational phrasing
        (r"\b4\s*PM\b", "சாயங்காலம் 4 மணி"),
        (r"\bmorning\b", "காலைல"),
        (r"\bafternoon\b", "மதியம்"),
        (r"\bweekend\b", "இந்த weekend"),
    ]

    HINDI_REPLACEMENTS: List[Tuple[str, str]] = [
        # Currency and unit naturalization
        (r"\b1\.5\s*(?:Crores?|Cr|करोड़)\b", "डेढ़ करोड़"),
        (r"\b2\.5\s*(?:Crores?|Cr|करोड़)\b", "ढाई करोड़"),
        (r"\b3BHK\b", "3 BHK"),
        (r"\b2BHK\b", "2 BHK"),
        (r"\b4BHK\b", "4 BHK"),
        
        # Telecaller courtesy terms
        (r"(?<![\u0900-\u097F])साहब(?![\u0900-\u097F])", "सर"),
        (r"(?<![\u0900-\u097F])सरजी(?![\u0900-\u097F])", "सर"),
    ]

    @classmethod
    def deduplicate_sir(cls, text: str) -> str:
        """Ensures 'Sir' doesn't sound spammy by limiting to 1 natural occurrence per sentence."""
        sentences = re.split(r"([.?!])", text)
        cleaned_sentences = []
        
        for i in range(0, len(sentences), 2):
            s = sentences[i]
            punct = sentences[i + 1] if i + 1 < len(sentences) else ""
            
            matches = list(re.finditer(r"\bSir\b", s, flags=re.IGNORECASE))
            if len(matches) > 1:
                parts = []
                last_end = 0
                for idx, m in enumerate(matches):
                    parts.append(s[last_end:m.start()])
                    if idx == 0:
                        parts.append("Sir")
                    elif idx == len(matches) - 1 and len(matches) == 2:
                        parts.append("ங்க")
                    else:
                        parts.append("")
                    last_end = m.end()
                parts.append(s[last_end:])
                s = "".join(parts)
            
            cleaned_sentences.append(s + punct)
            
        result = "".join(cleaned_sentences)
        result = re.sub(r"\s+", " ", result).strip()
        return result

    @classmethod
    def normalize_tamil(cls, text: str) -> str:
        """Transforms stiff/broken Tamil text into warm, sweet, phonetically crisp Tanglish."""
        normalized = text
        for pattern, replacement in cls.TAMIL_REPLACEMENTS:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
            
        # Clean hyphens between any English letters and Tamil script: e.g. "project-க்கு" -> "project க்கு"
        normalized = re.sub(r"([a-zA-Z0-9]+)[-–]([\u0B80-\u0BFF]+)", r"\1 \2", normalized)
        
        # Deduplicate "Sir"
        normalized = cls.deduplicate_sir(normalized)
        
        # Ensure clean spacing around punctuation
        normalized = re.sub(r"\s+([,?!])", r"\1", normalized)
        return normalized

    @classmethod
    def normalize_hindi(cls, text: str) -> str:
        """Transforms stiff Hindi text into warm, polite, conversational Hinglish."""
        normalized = text
        for pattern, replacement in cls.HINDI_REPLACEMENTS:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
            
        # Clean hyphens between Latin and Devanagari
        normalized = re.sub(r"([a-zA-Z0-9]+)[-–]([\u0900-\u097F]+)", r"\1 \2", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    @classmethod
    def normalize(cls, text: str, language: str) -> str:
        """Route to appropriate phonetic normalizer based on language."""
        lang_lower = language.lower()
        if "tamil" in lang_lower or "ta" in lang_lower or "pallavi" in lang_lower:
            return cls.normalize_tamil(text)
        elif "hindi" in lang_lower or "hi" in lang_lower or "swati" in lang_lower or "swara" in lang_lower:
            return cls.normalize_hindi(text)
        else:
            # English passes through untouched to maintain signature voice precision
            return text
