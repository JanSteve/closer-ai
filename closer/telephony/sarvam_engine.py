"""Sarvam AI Bulbul & Saaras Integration for CLOSER AI.

Models:
- TTS: bulbul:v3
  - Tamil: 'priya' (female twin of 'shubh', authentic Chennai conversational closer)
  - Hindi: 'ritu' (female twin of 'shubh', expressive Delhi/Mumbai Hinglish closer)
- STT: saaras:v3 (Ultra-low latency multilingual speech-to-text)

Zero-cost developer tier with automatic local offline fallback.
"""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path
from typing import Optional
import httpx

SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"

SARVAM_FEMALE_VOICES = {
    "tamil": "priya",    # Warm conversational female twin of shubh (Chennai Tanglish)
    "hindi": "ritu",     # Warm expressive female twin of shubh (Delhi/Mumbai Hinglish)
    "english": "ritu",   # Multilingual Indian English
}

SARVAM_MALE_CUSTOMER_VOICES = {
    "tamil": "shubh",
    "hindi": "shubh",
    "english": "shubh",
}

_SARVAM_TAMIL_SCRIPT_LOANWORDS = (
    ("special discount", "ஸ்பெஷல் டிஸ்கவுண்ட்"),
    ("payment options", "பேமெண்ட் ஆப்ஷன்ஸ்"),
    ("payment option", "பேமெண்ட் ஆப்ஷன்"),
    ("payment plan", "பேமெண்ட் பிளான்"),
    ("best package", "பெஸ்ட் பேக்கேஜ்"),
    ("floor plan", "ஃப்ளோர் பிளான்"),
    ("site visit", "சைட் விசிட்"),
    ("whatsapp", "வாட்ஸ்அப்"),
    ("discount", "டிஸ்கவுண்ட்"),
    ("budget", "பட்ஜெட்"),
    ("sir", "சார்"),
    ("vip", "விஐபி"),
    ("bro", "ப்ரோ"),
    ("ok", "ஓகே"),
)


class SarvamVoiceEngine:
    """Enterprise voice & speech-to-text engine using Sarvam AI Bulbul and Saaras."""

    def __init__(self, api_key: Optional[str] = None):
        # Load from argument, env variable, or fallback .env
        self.api_key = api_key or os.getenv("SARVAM_API_KEY", "")
        if not self.api_key:
            env_path = Path(__file__).resolve().parent.parent.parent / ".env"
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if line.startswith("SARVAM_API_KEY="):
                        self.api_key = line.split("=", 1)[1].strip()
                        break

        self.last_status_code: Optional[int] = None

    @staticmethod
    def _smooth_tamil_for_sarvam(text: str) -> str:
        """Converts common mixed Latin loanwords to spoken Tamil script for smooth ta-IN inflection."""
        out = text
        for latin_term, tamil_phonetic in _SARVAM_TAMIL_SCRIPT_LOANWORDS:
            out = re.sub(rf"\b{re.escape(latin_term)}\b", tamil_phonetic, out, flags=re.IGNORECASE)
        return out

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    async def synthesize(
        self,
        text: str,
        target_language: str,  # "tamil" or "hindi"
        output_path: str,
        speed: float = 0.96,
        customer_mode: bool = False,
        speaker_override: Optional[str] = None,
    ) -> bool:
        """Synthesizes natural conversational speech via Sarvam AI Bulbul v3 REST API."""
        if not self.is_configured:
            return False

        self.last_status_code = None
        t_low = target_language.lower()
        lang_key = "tamil" if "tam" in t_low else ("hindi" if "hin" in t_low else "english")
        lang_code = "ta-IN" if lang_key == "tamil" else ("hi-IN" if lang_key == "hindi" else "en-IN")
        default_map = SARVAM_MALE_CUSTOMER_VOICES if customer_mode else SARVAM_FEMALE_VOICES
        speaker = speaker_override or default_map.get(lang_key, "priya" if lang_key == "tamil" else "ritu")
        spoken_text = self._smooth_tamil_for_sarvam(text) if lang_key == "tamil" else text

        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": spoken_text,
            "target_language_code": lang_code,
            "speaker": speaker,
            "pace": speed,
            "speech_sample_rate": 24000,
            "enable_preprocessing": True,
            "model": "bulbul:v3",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(SARVAM_TTS_URL, json=payload, headers=headers)
                self.last_status_code = resp.status_code
                if resp.status_code == 200:
                    data = resp.json()
                    audios = data.get("audios", [])
                    if audios:
                        raw_bytes = base64.b64decode(audios[0])
                        with open(output_path, "wb") as f:
                            f.write(raw_bytes)
                        return True
                else:
                    print(f"[SarvamVoice] Warning: API status {resp.status_code}: {resp.text[:140]}")
                    return False
        except Exception as e:
            print(f"[SarvamVoice] Network error: {type(e).__name__}: {e}")
            return False

        return False

    async def transcribe(self, audio_path: str, language_code: str = "ta-IN") -> Optional[str]:
        """Transcribes speech using Sarvam Saaras v3 multilingual STT."""
        if not self.is_configured or not os.path.exists(audio_path):
            return None

        headers = {"api-subscription-key": self.api_key}
        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
            data = {"model": "saaras:v3", "language_code": language_code}

            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(SARVAM_STT_URL, headers=headers, data=data, files=files)
                if resp.status_code == 200:
                    return resp.json().get("transcript", "").strip()
                print(f"[SarvamSTT] Error {resp.status_code}: {resp.text[:140]}")
        except Exception as e:
            print(f"[SarvamSTT] Exception: {type(e).__name__}: {e}")
        return None
