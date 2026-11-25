"""
High-Fidelity Expressive Neural Speech Engine (Sarvam bulbul:v3 + ElevenLabs + Cartesia + Edge-TTS + Safe Browser Fallback).
Supports English, Tamil (ta-IN), and Hindi (hi-IN) with emotion-calibrated prosody
and zero 160Hz synthetic tone emissions when cloud/OS neural synthesis is unavailable.
"""

from __future__ import annotations

import asyncio
import base64
import io
import math
import os
import re
import struct
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import certifi

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass

from src.closer.config import settings

__all__ = [
    "EdgeTTSVoiceEngine",
    "VOICES",
    "VOICE_ALIASES",
    "normalize_speech_text",
    "inject_duplex_disfluencies",
    "generate_silence_pcm",
    "inject_silence_wav",
    "apply_pitch_contour",
]

# Supported high-fidelity neural voices across English, Indian English, Tamil, and Hindi
VOICES: Dict[str, str] = {
    # English Clinical Concierge Voices
    "maya": "en-US-AvaNeural",
    "maya_en": "en-US-AvaNeural",
    "ava": "en-US-AvaNeural",
    "aria": "en-US-AriaNeural",
    "sophia": "en-US-AvaNeural",
    "jenny": "en-US-JennyNeural",
    "emma": "en-US-EmmaMultilingualNeural",
    "michelle": "en-US-MichelleNeural",
    "guy": "en-US-GuyNeural",
    "andrew": "en-US-AndrewMultilingualNeural",
    "christopher": "en-US-ChristopherNeural",
    "brian": "en-US-BrianNeural",
    "eric": "en-US-EricNeural",
    # Indian English Patient Care Voices
    "neerja_expressive": "en-IN-NeerjaExpressiveNeural",
    "neerja": "en-IN-NeerjaExpressiveNeural",
    "neerja_standard": "en-IN-NeerjaNeural",
    "priya": "ta-IN-PallaviNeural",
    "kavya": "en-IN-NeerjaExpressiveNeural",
    "prabhat": "en-IN-PrabhatNeural",
    "aarav": "en-IN-PrabhatNeural",
    "rishi": "en-IN-PrabhatNeural",
    # Tamil (ta-IN) Voices
    "pallavi": "ta-IN-PallaviNeural",
    "valluvar": "ta-IN-ValluvarNeural",
    # Hindi (hi-IN) Voices
    "swara": "hi-IN-SwaraNeural",
    "swati": "hi-IN-SwaraNeural",
    "madhur": "hi-IN-MadhurNeural",
    # UK English Voices
    "sonia": "en-GB-SoniaNeural",
    "ryan": "en-GB-RyanNeural",
}

VOICE_ALIASES: Dict[str, str] = {
    "maya": "en-US-AvaNeural",
    "maya_en": "en-US-AvaNeural",
    "sophia": "en-US-AvaNeural",
    "female": "en-US-AvaNeural",
    "female_warm": "en-US-AriaNeural",
    "female_expressive": "en-US-AvaNeural",
    "female_crisp": "en-US-JennyNeural",
    "female_clinical": "en-US-EmmaMultilingualNeural",
    "male": "en-US-GuyNeural",
    "male_confident": "en-US-GuyNeural",
    "male_authoritative": "en-US-ChristopherNeural",
    "male_conversational": "en-US-AndrewMultilingualNeural",
    "india_female": "en-IN-NeerjaExpressiveNeural",
    "india_male": "en-IN-PrabhatNeural",
    "neerja": "en-IN-NeerjaExpressiveNeural",
    "prabhat": "en-IN-PrabhatNeural",
    "aarav": "en-IN-PrabhatNeural",
    "india_customer_care": "en-IN-NeerjaExpressiveNeural",
    "india_support_male": "en-IN-PrabhatNeural",
    "amura_english": "en-IN-NeerjaExpressiveNeural",
    "tamil_female": "ta-IN-PallaviNeural",
    "tamil_male": "ta-IN-ValluvarNeural",
    "pallavi": "ta-IN-PallaviNeural",
    "valluvar": "ta-IN-ValluvarNeural",
    "priya": "ta-IN-PallaviNeural",
    "amura_tamil": "ta-IN-PallaviNeural",
    "hindi_female": "hi-IN-SwaraNeural",
    "hindi_male": "hi-IN-MadhurNeural",
    "swara": "hi-IN-SwaraNeural",
    "swati": "hi-IN-SwaraNeural",
    "madhur": "hi-IN-MadhurNeural",
    "amura_hindi": "hi-IN-SwaraNeural",
    "uk_female": "en-GB-SoniaNeural",
    "uk_male": "en-GB-RyanNeural",
}

_STYLE_PROSODY: Dict[str, Dict[str, Any]] = {
    "calm_reassuring": {"rate": "-8%", "pitch": "-2Hz", "pace": 0.90, "el_stability": 0.62, "el_style": 0.30},
    "empathetic": {"rate": "-5%", "pitch": "-1Hz", "pace": 0.93, "el_stability": 0.56, "el_style": 0.35},
    "warm_patient": {"rate": "-6%", "pitch": "+0Hz", "pace": 0.94, "el_stability": 0.58, "el_style": 0.32},
    "urgent_clear": {"rate": "+3%", "pitch": "+1Hz", "pace": 1.03, "el_stability": 0.45, "el_style": 0.25},
}


def normalize_speech_text(text: str) -> str:
    """
    Normalizes clinical conversational text for natural human speech:
    - Converts USD & INR currency into spoken words (₹1.25 Lakhs -> 1.25 lakh rupees, ₹12,500 -> 12500 rupees)
    - Expands clinical abbreviations (HbA1c -> H-b-A-1-c, PCOS -> P-C-O-S, PCOD -> P-C-O-D, BP -> B-P, MNT, NMT, OPD, ECG, mg/dL, mmHg)
    - Expands temporal & thoroughfare abbreviations (11:00 AM -> 11 A-M, IST -> Indian Standard Time, Rd. -> Road)
    - Shapes natural breathing pauses across English, Tamil, and Hindi
    """
    if not text:
        return text

    clean = re.sub(r"[*_`#]", "", text)

    # 1. US & Global Currency Normalization
    clean = re.sub(r"\$(\d+(?:\.\d+)?)\s*(?:m\b|million\b)", r"\1 million dollars", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\$(\d+(?:\.\d+)?)\s*(?:k\b|thousand\b)", r"\1 thousand dollars", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\$(\d+(?:,\d{3})+)", lambda m: f"{int(m.group(1).replace(',', '')):,} dollars", clean)
    clean = re.sub(r"\$(\d+)\b", r"\1 dollars", clean)

    # 2. Indian Currency Normalization
    clean = re.sub(r"(?:₹|rs\.?|inr)\s*(\d+(?:\.\d+)?)\s*(?:cr\b|crores?\b)", r"\1 crore rupees", clean, flags=re.IGNORECASE)
    clean = re.sub(r"(?:₹|rs\.?|inr)\s*(\d+(?:\.\d+)?)\s*(?:lakhs?\b|lacs?\b|l\b)", r"\1 lakh rupees", clean, flags=re.IGNORECASE)
    clean = re.sub(r"(?:₹|rs\.?|inr)\s*(\d+(?:,\d+)*)", lambda m: f"{m.group(1).replace(',', '')} rupees", clean, flags=re.IGNORECASE)

    # 3. Clinical & Healthcare Abbreviations
    clean = re.sub(r"\bhba1c\b", "H-b-A-1-c", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bpcos\b", "P-C-O-S", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bpcod\b", "P-C-O-D", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bbmi\b", "B-M-I", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bbp\b", "B-P", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\becg\b", "E-C-G", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bopd\b", "O-P-D", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bicu\b", "I-C-U", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bmnt\b", "Medical Nutrition Therapy", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bnmt\b", "Natural Molecule Therapy", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bdpdp\b", "D-P-D-P", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bmg/dl\b", "milligrams per deciliter", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bmmhg\b", "millimeters of mercury", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bdr\.\s*", "Doctor ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bapprox\.?\b", "approximately", clean, flags=re.IGNORECASE)
    clean = re.sub(r"(?:\s|^)w/(?:\s|$)", " with ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\best\.?\b", "estimated", clean, flags=re.IGNORECASE)

    # 4. Indian Communication & Support Tokens
    clean = re.sub(r"\bwhatsapp\b", "Whats App", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bsms\b", "S-M-S", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\botp\b", "O-T-P", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bkyc\b", "K-Y-C", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bemi\b", "E-M-I", clean, flags=re.IGNORECASE)
    clean = re.sub(r"(?:Ticket\s*)?#?CC-(\d+)", r"Ticket C-C \1", clean, flags=re.IGNORECASE)
    clean = re.sub(r"(?:Ticket\s*)?#?AM-(\d+)", r"Ticket A-M \1", clean, flags=re.IGNORECASE)

    # 5. Time & Scheduling Normalization
    clean = re.sub(r"\b(\d{1,2}):00\s*(am|a\.m\.)\b", r"\1 A-M", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\b(\d{1,2}):00\s*(pm|p\.m\.)\b", r"\1 P-M", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\b(\d{1,2}):(\d{2})\s*(am|a\.m\.)\b", r"\1 \2 A-M", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\b(\d{1,2}):(\d{2})\s*(pm|p\.m\.)\b", r"\1 \2 P-M", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\b(\d{1,2})\s*(am|a\.m\.)\b", r"\1 A-M", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\b(\d{1,2})\s*(pm|p\.m\.)\b", r"\1 P-M", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bpst\b", "Pacific Time", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\best\b", "Eastern Time", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bist\b", "Indian Standard Time", clean, flags=re.IGNORECASE)

    # 6. Street & Address Expansions
    clean = re.sub(r"\b([A-Z][a-zA-Z]+)\s+Blvd\.?\b", r"\1 Boulevard", clean)
    clean = re.sub(r"\b([A-Z][a-zA-Z]+)\s+Ave\.?\b", r"\1 Avenue", clean)
    clean = re.sub(r"\b([A-Z][a-zA-Z]+)\s+St\.?\b", r"\1 Street", clean)
    clean = re.sub(r"\b([A-Z][a-zA-Z]+)\s+Dr\.?\b", r"\1 Drive", clean)
    clean = re.sub(r"\b([A-Z][a-zA-Z]+)\s+Rd\.?\b", r"\1 Road", clean)
    clean = re.sub(r"\b([A-Z][a-zA-Z]+)\s+Ct\.?\b", r"\1 Court", clean)
    clean = re.sub(r"\b([A-Z][a-zA-Z]+)\s+Pkwy\.?\b", r"\1 Parkway", clean)

    # 7. Cognitive Pause / Break Normalization
    clean = re.sub(r"\[(?:pause|cognitive_pause|break)(?::\s*\d+m?s)?\]", "... ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"<break\s+[^>]*\/?>", "... ", clean, flags=re.IGNORECASE)

    # 8. Acoustic Breathing Pauses (English)
    clean = re.sub(
        r"^(Gotcha|Understood|Certainly|Wonderful|I understand|Totally understand|Right|Fair enough)\b(?:\.{2,}|[,!.]*)\s*",
        r"\1... ",
        clean,
        flags=re.IGNORECASE,
    )
    clean = re.sub(r"^(Mm-hmm|mm-hmm|Mmhmm|mmhmm)\b(?:\.{2,}|[,!.]*)\s*", "Mm-hmm... ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"^(Uh|uh|Um|um)\b(?:\.{2,}|[,!.]*)\s*", lambda m: f"{m.group(1).capitalize()}... ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"^(Well)\b(?:\.{2,}|[,!.]*)\s*", "Well... ", clean, flags=re.IGNORECASE)

    clean = re.sub(r"([.!?।]\s+)(mm-hmm|mmhmm)\b(?:\.{2,}|[,!.]*)\s*", r"\1Mm-hmm... ", clean, flags=re.IGNORECASE)
    clean = re.sub(
        r"([.!?।]\s+)(uh|um)\b(?:\.{2,}|[,!.]*)\s*",
        lambda m: f"{m.group(1)}{m.group(2).capitalize()}... ",
        clean,
        flags=re.IGNORECASE,
    )

    # 9. Indian English & Tamil Courtesy Markers
    clean = re.sub(r"^(Namaste\s+(?:sir|ma'?am|ji)?)\b(?:\.{2,}|[,!.]*)\s*", r"\1... ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"^(Haanji\s+bilkul|Haanji|Haan\s+ji|Bilkul|Definitely\s+(?:sir|ma'?am)?)\b(?:\.{2,}|[,!.]*)\s*", r"\1... ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"^(வணக்கம்|சரிங்க|புரியுதுங்க|நிச்சயமாக|கவலைப்படாதீங்க)(?:\.{2,}|[,!.?]*)\s*", r"\1... ", clean)

    # 10. Native Hindi Courtesy Markers
    clean = re.sub(r"^(नमस्ते|नमस्कार|प्रणाम)(?:\s*जी)?(?:\.{2,}|[,!.।?]*)\s*", r"\1 जी... ", clean)
    clean = re.sub(r"^(जी\s+हाँ\s+बिल्कुल|जी\s+हाँ|जी\s+बिल्कुल|हाँ\s+जी|हाँजी|बिल्कुल|अच्छा)(?:\.{2,}|[,!.।?]*)\s*", r"\1... ", clean)
    clean = re.sub(r"^(?:कृपया\s+)?(माफ़ी\s+चाहते\s+हैं|माफ़ी\s+चाहती\s+हूँ|क्षमा\s+करें)(?:\.{2,}|[,!.।?]*)\s*", r"\1... ", clean)
    clean = re.sub(r"^(बहुत\s+बढ़िया|शानदार|ज़रूर)(?:\.{2,}|[,!.।?]*)\s*", r"\1... ", clean)

    clean = re.sub(r"\s*--\s*", " — ", clean)
    clean = re.sub(r"\.{3,}", "...", clean)
    clean = re.sub(r"\s{2,}", " ", clean)
    return clean.strip()


def generate_silence_pcm(duration_ms: int, sample_rate: int = 48000) -> bytes:
    """Generates millisecond-bounded 16-bit mono PCM silence."""
    if duration_ms <= 0:
        return b""
    duration_sec = duration_ms / 1000.0
    num_bytes = int(sample_rate * 2 * duration_sec)
    if num_bytes % 2 != 0:
        num_bytes += 1
    return b"\x00" * num_bytes


def inject_silence_wav(wav_bytes: bytes, duration_ms: int, sample_rate: Optional[int] = None) -> bytes:
    """Prepends exact millisecond-bounded PCM silence into a RIFF WAV audio stream."""
    if not wav_bytes or duration_ms <= 0:
        return wav_bytes
    if not wav_bytes.startswith(b"RIFF"):
        sr = sample_rate or 48000
        return generate_silence_pcm(duration_ms, sr) + wav_bytes

    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as r:
            nchannels = r.getnchannels()
            sampwidth = r.getsampwidth()
            framerate = r.getframerate()
            comptype = r.getcomptype()
            compname = r.getcompname()
            audio_frames = r.readframes(r.getnframes())

        num_frames = int(framerate * (duration_ms / 1000.0))
        silence_bytes = b"\x00" * (num_frames * nchannels * sampwidth)

        out_io = io.BytesIO()
        with wave.open(out_io, "wb") as w:
            w.setnchannels(nchannels)
            w.setsampwidth(sampwidth)
            w.setframerate(framerate)
            w.setcomptype(comptype, compname)
            w.writeframes(silence_bytes + audio_frames)

        return out_io.getvalue()
    except Exception:
        return wav_bytes


def apply_pitch_contour(text: str, pitch: Optional[str] = None) -> str:
    """Shapes pitch contour for conversational realism."""
    if pitch and pitch.strip() not in ("", "+0Hz", "0Hz", "+0", "-0", "auto", "default"):
        return pitch.strip()
    if not text:
        return "+0Hz"
    clean_t = text.strip()
    if clean_t.endswith("?"):
        return "+3Hz"
    if clean_t.endswith((".", "!", "।")):
        return "-2Hz"
    return "+0Hz"


def inject_duplex_disfluencies(
    text: str,
    market: str = "india",
    intent: str = "general",
    is_friction: bool = False,
    filler: Optional[str] = None,
) -> str:
    """Inserts natural conversational micro-fillers across English, Indian English, Tamil, and Hindi."""
    if not text or not text.strip():
        if filler:
            return normalize_speech_text(f"{filler}... ")
        return text

    clean_text = text.strip()
    existing_filler_match = re.match(
        r"^(mm-hmm|mmhmm|uh|um|well|gotcha|certainly|understood|fair enough|i understand|totally understand|right|"
        r"namaste\s*(?:sir|ma'?am|ji)?|haanji\s*bilkul|haanji|haan\s*ji|bilkul|"
        r"vanakkam|seringa|puriyudhu|nichayama|வணக்கம்|சரிங்க|புரியுதுங்க|நிச்சயமாக|"
        r"नमस्ते(?:\s*जी)?|नमस्कार(?:\s*जी)?|प्रणाम(?:\s*जी)?|"
        r"जी\s*हाँ\s*बिल्कुल|जी\s*हाँ|जी\s*बिल्कुल|हाँ\s*जी|हाँजी|माफ़ी\s*चाहते\s*हैं|माफ़ी\s*चाहती\s*हूँ|अच्छा|ज़रूर)\b",
        clean_text,
        flags=re.IGNORECASE,
    )

    if existing_filler_match and not filler and not (is_friction and clean_text.lower().startswith("i understand")):
        return normalize_speech_text(clean_text)

    if is_friction and clean_text.lower().startswith("i understand"):
        clean_text = re.sub(r"^i\s+understand\b[,.]*\s*", "", clean_text, flags=re.IGNORECASE)

    if filler:
        chosen_filler = filler.strip()
    else:
        m_low = (market or "india").lower().strip()
        i_low = (intent or "general").lower().strip()

        if any(t in m_low for t in ["tamil", "ta", "ta-in"]):
            if is_friction or i_low in ("friction", "objection", "schedule_friction"):
                chosen_filler = "புரியுதுங்க"
            elif i_low in ("acknowledgement", "sync", "affirmation"):
                chosen_filler = "சரிங்க"
            else:
                chosen_filler = "நிச்சயமாக"
        elif any(h in m_low for h in ["hindi", "hi", "hi-in"]):
            if is_friction or i_low in ("friction", "objection", "schedule_friction"):
                chosen_filler = "जी बिल्कुल"
            elif i_low in ("acknowledgement", "sync", "affirmation"):
                chosen_filler = "हाँ जी"
            elif i_low in ("thinking", "schedule", "negotiation"):
                chosen_filler = "जी"
            else:
                chosen_filler = "जी बिल्कुल"
        elif any(ind in m_low for ind in ["india", "in", "en-in", "enterprise"]):
            if is_friction or i_low in ("friction", "objection", "schedule_friction"):
                chosen_filler = "Understood"
            elif i_low in ("acknowledgement", "sync", "affirmation"):
                chosen_filler = "Haanji"
            elif i_low in ("thinking", "schedule", "negotiation"):
                chosen_filler = "Well"
            else:
                chosen_filler = "Right"
        else:
            if is_friction or i_low in ("friction", "objection", "schedule_friction"):
                chosen_filler = "Mm-hmm"
            elif i_low in ("thinking", "schedule", "negotiation"):
                chosen_filler = "Um"
            elif i_low in ("acknowledgement", "sync"):
                chosen_filler = "Gotcha"
            elif i_low == "affirmation":
                chosen_filler = "Mm-hmm"
            else:
                chosen_filler = "Well"

    clean_filler = chosen_filler.rstrip(".—, ")
    combined = f"{clean_filler}... {clean_text}"
    return normalize_speech_text(combined)


class EdgeTTSVoiceEngine:
    """
    Synthesizes expressive speech using Sarvam AI bulbul:v3, ElevenLabs, Cartesia, or Edge-TTS,
    with safe macOS 'say' fallback and clean 'browser_fallback' signaling (returning b'')
    instead of emitting synthetic 160Hz tones.
    """

    _sarvam_cooldown_until: float = 0.0

    def __init__(
        self,
        default_voice: Optional[str] = None,
        rate: Optional[str] = None,
        sample_rate: Optional[int] = None,
    ):
        raw_voice = default_voice or settings.DEFAULT_VOICE
        self.default_voice = self._resolve_voice_name(raw_voice)
        self.fallback_voice = settings.FALLBACK_VOICE
        self.rate = rate or settings.SPEECH_RATE
        self.sample_rate = sample_rate or settings.AUDIO_SAMPLE_RATE
        self.last_provider_used: str = "Studio Broadcast Neural (Edge-TTS 48kHz)"

    @staticmethod
    def _resolve_voice_name(voice: Optional[str]) -> str:
        """Resolves alias or key to full neural voice ID."""
        if not voice:
            return "en-IN-NeerjaExpressiveNeural"
        v_lower = voice.lower().strip()
        if v_lower in VOICE_ALIASES:
            return VOICE_ALIASES[v_lower]
        if v_lower in VOICES:
            return VOICES[v_lower]
        return voice

    @staticmethod
    def _parse_rate_to_pace(rate: Optional[str], style: Optional[str]) -> float:
        if rate:
            m = re.match(r"([+-]?\d+)\s*%", str(rate).strip())
            if m:
                pct = int(m.group(1))
                return max(0.75, min(1.35, round(1.0 + (pct / 100.0), 2)))
        if style and style in _STYLE_PROSODY:
            return float(_STYLE_PROSODY[style]["pace"])
        return 1.00

    async def synthesize(
        self,
        text: str,
        output_path: Optional[str] = None,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        sample_rate: Optional[int] = None,
        provider: Optional[str] = None,
        elevenlabs_key: Optional[str] = None,
        sarvam_key: Optional[str] = None,
        pause_ms: Optional[int] = None,
        cognitive_pause_ms: Optional[int] = None,
        style: Optional[str] = None,
    ) -> Tuple[bytes, float]:
        """
        Synthesizes expressive speech to WAV/MP3 bytes.
        If all cloud and OS speech engines fail, returns (b"", latency) and sets
        self.last_provider_used = "browser_fallback" (NEVER a 160Hz synthetic tone).
        """
        start_time = time.perf_counter()
        target_voice = self._resolve_voice_name(voice or self.default_voice)
        style_meta = _STYLE_PROSODY.get(style or "", {})
        target_rate = rate or style_meta.get("rate") or self.rate
        target_pitch = apply_pitch_contour(text, pitch or style_meta.get("pitch"))
        target_sr = sample_rate or self.sample_rate
        target_pace = self._parse_rate_to_pace(rate, style)

        clean_text = normalize_speech_text(text)
        audio_bytes: Optional[bytes] = None
        self.last_provider_used = "Studio Broadcast Neural (Edge-TTS 48kHz)"

        prov = (provider or "studio").lower().strip()
        el_key = (elevenlabs_key or os.environ.get("ELEVENLABS_API_KEY", "")).strip()
        sarv_key = (sarvam_key or os.environ.get("SARVAM_API_KEY", "")).strip()
        cartesia_key = os.environ.get("CARTESIA_API_KEY", "").strip()

        # 1. ElevenLabs
        if prov == "elevenlabs" or (prov == "auto" and el_key):
            if el_key:
                try:
                    audio_bytes = await self._synthesize_elevenlabs(
                        clean_text,
                        target_voice,
                        el_key,
                        target_sr,
                        style=style,
                    )
                    if audio_bytes and len(audio_bytes) > 44:
                        self.last_provider_used = "ElevenLabs Turbo v2.5"
                except Exception:
                    audio_bytes = None

        # 2. Sarvam AI bulbul:v3 (with 401/402/403/429 cooldown protection)
        if not audio_bytes and (prov == "sarvam" or (prov == "auto" and sarv_key)):
            if sarv_key and time.time() >= EdgeTTSVoiceEngine._sarvam_cooldown_until:
                try:
                    audio_bytes = await self._synthesize_sarvam(
                        clean_text,
                        target_voice,
                        sarv_key,
                        target_sr,
                        pace=target_pace,
                        style=style,
                    )
                    if audio_bytes and len(audio_bytes) > 44:
                        self.last_provider_used = "Sarvam AI bulbul:v3"
                except Exception:
                    audio_bytes = None

        # 3. Cartesia
        if not audio_bytes and (prov == "cartesia" or (prov == "auto" and cartesia_key)):
            if cartesia_key:
                try:
                    audio_bytes = await self._synthesize_cartesia(clean_text, target_voice, cartesia_key, target_sr)
                    if audio_bytes and len(audio_bytes) > 44:
                        self.last_provider_used = "Cartesia Sonic"
                except Exception:
                    audio_bytes = None

        # 4. Edge-TTS Neural Broadcast
        if not audio_bytes:
            try:
                import edge_tts

                voices_to_try = [target_voice]
                if "Expressive" in target_voice:
                    voices_to_try.append(target_voice.replace("Expressive", ""))
                elif target_voice == "en-US-AvaNeural":
                    voices_to_try.append("en-US-AriaNeural")

                for v_attempt in voices_to_try:
                    try:
                        communicate = edge_tts.Communicate(
                            clean_text,
                            v_attempt,
                            rate=str(target_rate),
                            pitch=str(target_pitch),
                        )
                        raw_audio = bytearray()
                        async for chunk in communicate.stream():
                            if chunk["type"] == "audio":
                                raw_audio.extend(chunk["data"])
                        if len(raw_audio) > 0:
                            raw_bytes = bytes(raw_audio)
                            converted = self._ensure_wav_format(raw_bytes, target_sr)
                            if converted and len(converted) > 44:
                                audio_bytes = converted
                                self.last_provider_used = f"Studio Broadcast Neural ({v_attempt})"
                                break
                    except Exception:
                        continue
            except Exception:
                audio_bytes = None

        # 5. Safe local macOS fallback or clean browser_fallback (NO 160Hz tone!)
        if not audio_bytes:
            local_bytes = self._synthesize_local_fallback(clean_text, target_voice, target_sr)
            if local_bytes and len(local_bytes) > 44:
                audio_bytes = local_bytes
                self.last_provider_used = "macOS Native Speech Fallback"
            else:
                audio_bytes = b""
                self.last_provider_used = "browser_fallback"

        pause_duration = cognitive_pause_ms or pause_ms or 0
        if pause_duration > 0 and audio_bytes:
            audio_bytes = inject_silence_wav(audio_bytes, pause_duration, sample_rate=target_sr)

        latency = time.perf_counter() - start_time

        if output_path and audio_bytes:
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "wb") as f:
                f.write(audio_bytes)

        return audio_bytes, latency

    async def _synthesize_cartesia(self, text: str, voice: str, api_key: str, sample_rate: int) -> Optional[bytes]:
        import httpx

        url = "https://api.cartesia.ai/tts/bytes"
        headers = {
            "X-API-Key": api_key,
            "Cartesia-Version": "2024-06-10",
            "Content-Type": "application/json",
        }
        is_indic = any(w in voice.lower() for w in ["india", "neerja", "prabhat", "priya", "rishi", "pallavi", "swara"])
        voice_id = "e043697e-1dc6-4f44-ad26-78cc7ce4f526" if is_indic else "a0e99841-438c-4a64-b679-ae501e7d6091"
        payload = {
            "model_id": "sonic-multilingual" if is_indic else "sonic-english",
            "transcript": text,
            "voice": {"mode": "id", "id": voice_id},
            "output_format": {"container": "wav", "sample_rate": sample_rate, "encoding": "pcm_s16le"},
        }
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200 and len(resp.content) > 44:
                return resp.content
        return None

    async def _synthesize_elevenlabs(
        self,
        text: str,
        voice: str,
        api_key: str,
        sample_rate: int = 24000,
        style: Optional[str] = None,
    ) -> Optional[bytes]:
        import httpx

        v_low = voice.lower()
        if any(w in v_low for w in ["guy", "male", "christopher", "brian", "eric", "prabhat", "aarav", "valluvar", "madhur"]):
            voice_id = "pNInz6obpgDQGcFmaJgB"
        else:
            voice_id = "21m00Tcm4TlvDq8ikWAM"

        style_meta = _STYLE_PROSODY.get(style or "", {})
        stability = float(style_meta.get("el_stability", 0.50))
        el_style = float(style_meta.get("el_style", 0.15))

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": 0.85,
                "style": el_style,
                "use_speaker_boost": True,
            },
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200 and len(resp.content) > 44:
                return self._ensure_wav_format(resp.content, sample_rate)
        return None

    async def _synthesize_sarvam(
        self,
        text: str,
        voice: str,
        api_key: str,
        sample_rate: int = 24000,
        pace: Optional[float] = None,
        style: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Synthesizes Indic speech using Sarvam AI bulbul:v3 REST API across ta-IN, hi-IN, and en-IN,
        with automatic 180s cooldown on 401/402/403/429 credit or auth exhaustion.
        """
        import httpx

        if time.time() < EdgeTTSVoiceEngine._sarvam_cooldown_until:
            return None

        url = "https://api.sarvam.ai/text-to-speech"
        headers = {
            "api-subscription-key": api_key,
            "Content-Type": "application/json",
        }
        v_low = (voice or "").lower()
        has_tamil_script = any("\u0b80" <= ch <= "\u0bff" for ch in text)
        has_hindi_script = any("\u0900" <= ch <= "\u097f" for ch in text)
        is_male = any(w in v_low for w in ["male", "prabhat", "aarav", "rishi", "madhur", "guy", "valluvar", "shubh"])

        if has_tamil_script or any(w in v_low for w in ["ta-in", "tamil", "pallavi", "valluvar", "priya"]):
            lang_code = "ta-IN"
            speaker = "shubh" if is_male else "priya"
        elif has_hindi_script or any(w in v_low for w in ["hi-in", "hindi", "swara", "madhur", "swati", "ritu"]):
            lang_code = "hi-IN"
            speaker = "shubh" if is_male else "ritu"
        else:
            lang_code = "en-IN"
            speaker = "shubh" if is_male else "ritu"

        style_meta = _STYLE_PROSODY.get(style or "", {})
        target_pace = pace if pace is not None else float(style_meta.get("pace", 1.00))
        target_pace = max(0.75, min(1.35, float(target_pace)))

        payload = {
            "text": text,
            "target_language_code": lang_code,
            "speaker": speaker,
            "pace": target_pace,
            "speech_sample_rate": sample_rate,
            "enable_preprocessing": True,
            "model": settings.SARVAM_TTS_MODEL or "bulbul:v3",
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in (401, 402, 403, 429):
                EdgeTTSVoiceEngine._sarvam_cooldown_until = time.time() + 180.0
                return None
            if resp.status_code == 200:
                data = resp.json()
                audios = data.get("audios", [])
                if audios and len(audios) > 0:
                    wav_data = base64.b64decode(audios[0])
                    if len(wav_data) > 44:
                        return self._ensure_wav_format(wav_data, sample_rate)
        return None

    def synthesize_sync(
        self,
        text: str,
        output_path: Optional[str] = None,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        sample_rate: Optional[int] = None,
        provider: Optional[str] = None,
        elevenlabs_key: Optional[str] = None,
        sarvam_key: Optional[str] = None,
        pause_ms: Optional[int] = None,
        cognitive_pause_ms: Optional[int] = None,
        style: Optional[str] = None,
    ) -> Tuple[bytes, float]:
        """Synchronous wrapper for synthesize."""
        resolved_voice = self._resolve_voice_name(voice or self.default_voice)
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.synthesize(
                            text,
                            output_path=output_path,
                            voice=resolved_voice,
                            rate=rate,
                            pitch=pitch,
                            sample_rate=sample_rate,
                            provider=provider,
                            elevenlabs_key=elevenlabs_key,
                            sarvam_key=sarvam_key,
                            pause_ms=pause_ms,
                            cognitive_pause_ms=cognitive_pause_ms,
                            style=style,
                        ),
                    )
                    return future.result()

            return asyncio.run(
                self.synthesize(
                    text,
                    output_path=output_path,
                    voice=resolved_voice,
                    rate=rate,
                    pitch=pitch,
                    sample_rate=sample_rate,
                    provider=provider,
                    elevenlabs_key=elevenlabs_key,
                    sarvam_key=sarvam_key,
                    pause_ms=pause_ms,
                    cognitive_pause_ms=cognitive_pause_ms,
                    style=style,
                )
            )
        except Exception:
            data, latency = self._synthesize_local_fallback_with_latency(text, resolved_voice, sample_rate, output_path)
            pause_duration = cognitive_pause_ms or pause_ms or 0
            if pause_duration > 0 and data:
                data = inject_silence_wav(data, pause_duration, sample_rate=sample_rate or self.sample_rate)
            return data, latency

    def _ensure_wav_format(self, audio_data: bytes, target_sr: int) -> bytes:
        """Converts raw audio bytes to standard RIFF WAV via ffmpeg if needed; preserves valid MP3/WAV or returns b''."""
        if not audio_data:
            return b""
        if audio_data.startswith(b"RIFF") and len(audio_data) >= 28:
            try:
                current_sr = struct.unpack("<I", audio_data[24:28])[0]
                if current_sr == target_sr:
                    return audio_data
            except Exception:
                return audio_data

        suffix = ".wav" if audio_data.startswith(b"RIFF") else ".mp3"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf_in:
            tf_in.write(audio_data)
            in_name = tf_in.name

        out_name = in_name + "_out.wav"
        try:
            cmd = ["ffmpeg", "-y", "-i", in_name, "-ar", str(target_sr), "-ac", "1", "-f", "wav", out_name]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            with open(out_name, "rb") as f:
                wav_data = f.read()
            return wav_data
        except Exception:
            if audio_data and len(audio_data) > 100:
                return audio_data
            return b""
        finally:
            for p in (in_name, out_name):
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass

    def _synthesize_local_fallback(
        self,
        text: str,
        voice: Optional[str] = None,
        sample_rate: int = 48000,
    ) -> bytes:
        """
        Attempts native macOS 'say' synthesis when running on Darwin;
        returns empty bytes b'' on non-macOS or failure so browser Web Speech fallback handles playback cleanly
        (never emits a synthetic 160Hz tone).
        """
        target_v = (voice or self.default_voice).lower()
        if any(w in target_v for w in ["india", "neerja", "prabhat", "priya", "rishi", "aarav", "kavya", "pallavi", "valluvar"]):
            mac_voice = "Rishi"
        elif any(w in target_v for w in ["guy", "male", "christopher", "brian", "eric"]):
            mac_voice = "Eddy (English (US))"
        elif "flo" in target_v or "jenny" in target_v:
            mac_voice = "Flo (English (US))"
        elif "shelley" in target_v or "aria" in target_v or "ava" in target_v:
            mac_voice = "Shelley (English (US))"
        else:
            mac_voice = "Samantha"

        if sys.platform == "darwin":
            wav_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf_wav:
                    wav_path = tf_wav.name

                say_cmd = [
                    "say",
                    "-v",
                    mac_voice,
                    "--file-format=WAVE",
                    f"--data-format=LEI16@{sample_rate}",
                    "-r",
                    "185",
                    text,
                    "-o",
                    wav_path,
                ]
                res = subprocess.run(say_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                if res.returncode == 0 and os.path.exists(wav_path) and os.path.getsize(wav_path) > 44:
                    with open(wav_path, "rb") as f:
                        return f.read()
            except Exception:
                pass
            finally:
                if wav_path and os.path.exists(wav_path):
                    try:
                        os.remove(wav_path)
                    except OSError:
                        pass

        return b""

    def _synthesize_local_fallback_with_latency(
        self,
        text: str,
        voice: Optional[str],
        sample_rate: Optional[int],
        output_path: Optional[str],
    ) -> Tuple[bytes, float]:
        t0 = time.perf_counter()
        target_sr = sample_rate or self.sample_rate
        data = self._synthesize_local_fallback(text, voice, target_sr)
        if data and len(data) > 44:
            self.last_provider_used = "macOS Native Speech Fallback"
        else:
            data = b""
            self.last_provider_used = "browser_fallback"
        latency = time.perf_counter() - t0
        if output_path and data:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(data)
        return data, latency

    @staticmethod
    def _generate_pcm_wav(sample_rate: int = 48000, duration_sec: float = 1.0) -> bytes:
        """Retained only as an explicit utility helper for acoustic unit tests (never used as TTS speech fallback)."""
        num_samples = int(sample_rate * duration_sec)
        raw_samples = bytearray()
        freq = 160.0
        for i in range(num_samples):
            t = float(i) / sample_rate
            envelope = math.sin(math.pi * (i / max(1, num_samples)))
            sample = (
                0.6 * math.sin(2 * math.pi * freq * t)
                + 0.3 * math.sin(2 * math.pi * 2 * freq * t)
                + 0.1 * math.sin(2 * math.pi * 3 * freq * t)
            ) * envelope
            int_sample = max(-32768, min(32767, int(sample * 16384)))
            raw_samples.extend(struct.pack("<h", int_sample))

        header = bytearray()
        data_size = len(raw_samples)
        header.extend(b"RIFF")
        header.extend(struct.pack("<I", data_size + 36))
        header.extend(b"WAVEfmt ")
        header.extend(struct.pack("<I", 16))
        header.extend(struct.pack("<H", 1))
        header.extend(struct.pack("<H", 1))
        header.extend(struct.pack("<I", sample_rate))
        header.extend(struct.pack("<I", sample_rate * 2))
        header.extend(struct.pack("<H", 2))
        header.extend(struct.pack("<H", 16))
        header.extend(b"data")
        header.extend(struct.pack("<I", data_size))
        return bytes(header + raw_samples)
