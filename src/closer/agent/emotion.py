"""
Human Emotion Detection & Expressive Voice Prosody Mapping for Amura Health / CLOSER AI.
Recognizes patient emotional states across English, Tamil/Tanglish, and Hindi/Hinglish
and outputs calibrated empathy directives and TTS prosody controls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class PatientEmotion(str, Enum):
    CALM = "calm"
    ANXIOUS = "anxious"
    URGENT = "urgent"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    PAIN_DISTRESS = "pain_distress"


@dataclass
class EmotionAssessment:
    emotion: PatientEmotion
    confidence: float  # 0.0 - 1.0
    empathy_directive: str
    tts_rate: str
    tts_pitch: str
    sarvam_pace: float
    voice_style: str
    signals: List[str] = field(default_factory=list)


_PROSODY_MAP: Dict[PatientEmotion, Dict[str, object]] = {
    PatientEmotion.PAIN_DISTRESS: {
        "tts_rate": "-6%",
        "tts_pitch": "-3Hz",
        "sarvam_pace": 0.92,
        "voice_style": "calm_reassuring",
        "directive": (
            "Respond with immediate gentle calm, validate physical discomfort first, "
            "and prioritize safety or rapid clinical care."
        ),
    },
    PatientEmotion.URGENT: {
        "tts_rate": "+6%",
        "tts_pitch": "+2Hz",
        "sarvam_pace": 1.04,
        "voice_style": "urgent_clear",
        "directive": (
            "Respond briskly, clearly, and action-first with zero filler so the patient "
            "gets immediate routing."
        ),
    },
    PatientEmotion.ANXIOUS: {
        "tts_rate": "-5%",
        "tts_pitch": "-2Hz",
        "sarvam_pace": 0.94,
        "voice_style": "empathetic",
        "directive": (
            "Lead with warm reassurance, steady unhurried cadence, and remind the patient "
            "they are in caring medical hands."
        ),
    },
    PatientEmotion.FRUSTRATED: {
        "tts_rate": "-3%",
        "tts_pitch": "-2Hz",
        "sarvam_pace": 0.96,
        "voice_style": "warm_patient",
        "directive": (
            "Acknowledge frustration sincerely without defensiveness, take ownership, "
            "and give one concrete resolution step."
        ),
    },
    PatientEmotion.CONFUSED: {
        "tts_rate": "-4%",
        "tts_pitch": "+0Hz",
        "sarvam_pace": 0.95,
        "voice_style": "warm_patient",
        "directive": (
            "Use simple, jargon-free explanation with warm patience and check understanding "
            "gently."
        ),
    },
    PatientEmotion.CALM: {
        "tts_rate": "+2%",
        "tts_pitch": "+1Hz",
        "sarvam_pace": 1.00,
        "voice_style": "empathetic",
        "directive": (
            "Maintain warm, attentive, conversational clinical concierge tone."
        ),
    },
}


# Ordered by clinical precedence: PAIN_DISTRESS > URGENT > ANXIOUS > FRUSTRATED > CONFUSED
_EMOTION_PATTERNS: List[Tuple[PatientEmotion, List[Tuple[str, str]]]] = [
    (
        PatientEmotion.PAIN_DISTRESS,
        [
            (r"\b(unbearable|terrible|severe|excruciating|intense|crushing)\s+(pain|ache|discomfort)\b", "severe_pain_en"),
            (r"\b(in\s+(a\s+lot\s+of\s+)?pain|hurting\s+(so\s+)?bad|can'?t\s+breathe|cannot\s+breathe|chest\s+pain|chest\s+tightness|dizzy|fainting)\b", "distress_en"),
            (r"(வலி\s*தாங்க\s*முடியல|நெஞ்சு\s*வலி|நெஞ்சுவலி|மூச்சு\s*விட\s*முடியல|ரொம்ப\s*வலி|தாங்க\s*முடியல|அதிகமா\s*வலி)", "pain_ta"),
            (r"\b(thanga\s*mudiyala|romba\s*vali|nenju\s*vali|moochu\s*vida\s*mudiyala|valikkudhu)\b", "pain_tanglish"),
            (r"(असहनीय\s*दर्द|तेज\s*दर्द|सीने\s*में\s*दर्द|सांस\s*(?:लेने\s*में\s*)?तकलीफ|बहुत\s*दर्द\s*हो\s*रहा)", "pain_hi"),
            (r"\b(bahut\s*tez\s*dard|asahniya\s*dard|seene\s*mein\s*dard|dard\s*ho\s*raha|saans\s*nahi)\b", "pain_hinglish"),
        ],
    ),
    (
        PatientEmotion.URGENT,
        [
            (r"\b(right\s*now|immediately|asap|urgent|urgently|emergency|critical|hurry|quick|straight\s*away)\b", "urgent_en"),
            (r"\b108\b|\bambulance\b|\ber\b|\bemergency\s*room\b", "emergency_en"),
            (r"(அவசரம்|உடனே|இப்போவே|தயவுசெய்து\s*உடனே)", "urgent_ta"),
            (r"\b(udane|avasarama|avasaram|ippove|doctor\s*venum\s*udane)\b", "urgent_tanglish"),
            (r"(तुरंत|जल्दी|अभी\s*के\s*अभी|इमरजेंसी|आपातकालीन)", "urgent_hi"),
            (r"\b(turant|jaldi\s*(?:se|karo|chahiye)?|abhi\s*chahiye|emergency\s*hai)\b", "urgent_hinglish"),
        ],
    ),
    (
        PatientEmotion.ANXIOUS,
        [
            (r"\b(worried|worry|scared|afraid|anxious|anxiety|nervous|panic|panicking|terrified|frightened|stressed|freaking\s*out)\b", "anxious_en"),
            (r"(பயமா\s*இருக்கு|பயம்|டென்ஷன்|கவலையா\s*இருக்கு|பதட்டமா)", "anxious_ta"),
            (r"\b(bayama\s*irukku|romba\s*bayam|bayam|tension\s*aagudhu|tension\s*irukku|kavalai)\b", "anxious_tanglish"),
            (r"(घबराहट|डर\s*लग\s*रहा|चिंता|बहुत\s*डर|परेशान\s*हूँ)", "anxious_hi"),
            (r"\b(ghabrahat|bahut\s*darr?|dar\s*lag\s*raha|chinta\s*ho\s*rahi|tension\s*ho\s*rahi)\b", "anxious_hinglish"),
        ],
    ),
    (
        PatientEmotion.FRUSTRATED,
        [
            (r"\b(already\s*told\s*you|told\s*you\s*twice|nobody\s*call(?:s|ed)|no\s*one\s*called|fed\s*up|frustrated|ridiculous|waste\s*of\s*time|useless|sick\s*of|annoyed|angry|waiting\s*forever)\b", "frustrated_en"),
            (r"\?\!+|\!\?+", "frustrated_punct"),
            (r"(எத்தனை\s*தடவை|யாரும்\s*பேசல|கோபம்|சலிப்பா)", "frustrated_ta"),
            (r"\b(ethana\s*thadava|solradhu|yaarum\s*call\s*pannala|kovam|ketkave\s*illa)\b", "frustrated_tanglish"),
            (r"(कितनी\s*बार|कोई\s*सुनता\s*नहीं|गुस्सा|तंग\s*आ\s*गया|परेशान\s*हो\s*गया)", "frustrated_hi"),
            (r"\b(kitni\s*baar|koi\s*sunta\s*nahi|koi\s*call\s*nahi|gussa|pareshan\s*ho\s*gaya)\b", "frustrated_hinglish"),
        ],
    ),
    (
        PatientEmotion.CONFUSED,
        [
            (r"\b(don'?t\s*understand|do\s*not\s*understand|confused|what\s*does\s*.+\s*mean|what\s*is\s*(?:mnt|nmt|hba1c)|can\s*you\s*explain|unclear|not\s*sure\s*what|lost\s*me)\b", "confused_en"),
            (r"(புரியல|புரியவில்லை|என்ன\s*அர்த்தம்|விளக்க\s*முடியுமா)", "confused_ta"),
            (r"\b(puriyala|puriyavillai|enna\s*meaning|enna\s*artham|explain\s*pannunga)\b", "confused_tanglish"),
            (r"(समझ\s*नहीं|क्या\s*मतलब|समझा\s*दीजिए|कन्फ्यूज़)", "confused_hi"),
            (r"\b(samajh\s*nahi|kya\s*matlab|samjha\s*do|confused\s*hoon)\b", "confused_hinglish"),
        ],
    ),
]


class EmotionDetector:
    """
    Lightweight, deterministic zero-latency tri-lingual patient emotion detector.
    Detects calm, anxious, urgent, frustrated, confused, and pain_distress across
    English, Tamil/Tanglish, and Hindi/Hinglish.
    """

    def assess(
        self,
        text: str,
        language: str = "english",
        history: Optional[List[Dict[str, str]]] = None,
    ) -> EmotionAssessment:
        clean = (text or "").strip()
        if not clean:
            meta = _PROSODY_MAP[PatientEmotion.CALM]
            return EmotionAssessment(
                emotion=PatientEmotion.CALM,
                confidence=0.80,
                empathy_directive=str(meta["directive"]),
                tts_rate=str(meta["tts_rate"]),
                tts_pitch=str(meta["tts_pitch"]),
                sarvam_pace=float(meta["sarvam_pace"]),
                voice_style=str(meta["voice_style"]),
                signals=["neutral_empty"],
            )

        t_low = clean.lower()
        matched_by_emotion: Dict[PatientEmotion, List[str]] = {}

        for emotion, patterns in _EMOTION_PATTERNS:
            for pattern, signal_name in patterns:
                if re.search(pattern, t_low, re.IGNORECASE):
                    matched_by_emotion.setdefault(emotion, []).append(signal_name)

        # Check repetition / unresolved frustration across recent user history
        prior_user_turns = [
            (m.get("content") or "").lower().strip()
            for m in (history or [])
            if m.get("role") == "user" and (m.get("content") or "").strip()
        ]
        repeated_query = len(prior_user_turns) >= 2 and any(
            prev == t_low for prev in prior_user_turns[-3:]
        )
        if repeated_query:
            matched_by_emotion.setdefault(PatientEmotion.FRUSTRATED, []).append("repeated_unresolved_turn")

        chosen_emotion = PatientEmotion.CALM
        signals: List[str] = ["baseline_calm"]
        confidence = 0.84

        for candidate in (
            PatientEmotion.PAIN_DISTRESS,
            PatientEmotion.URGENT,
            PatientEmotion.ANXIOUS,
            PatientEmotion.FRUSTRATED,
            PatientEmotion.CONFUSED,
        ):
            if candidate in matched_by_emotion:
                chosen_emotion = candidate
                signals = matched_by_emotion[candidate]
                confidence = min(0.98, 0.78 + 0.08 * len(signals))
                break

        # Boost confidence slightly for exclamation emphasis or all-caps distress
        if chosen_emotion != PatientEmotion.CALM and ("!" in clean or (len(clean) > 8 and clean.isupper())):
            confidence = min(0.99, round(confidence + 0.05, 2))
            if "punctuation_or_caps_emphasis" not in signals:
                signals.append("punctuation_or_caps_emphasis")

        meta = _PROSODY_MAP[chosen_emotion]
        return EmotionAssessment(
            emotion=chosen_emotion,
            confidence=round(confidence, 2),
            empathy_directive=str(meta["directive"]),
            tts_rate=str(meta["tts_rate"]),
            tts_pitch=str(meta["tts_pitch"]),
            sarvam_pace=float(meta["sarvam_pace"]),
            voice_style=str(meta["voice_style"]),
            signals=signals,
        )
