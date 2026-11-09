"""Sarvam AI Bulbul & Saaras Integration for CLOSER AI.

Models:
- TTS: bulbul:v3
  - Tamil: 'kavitha' (Authentic Chennai dialect, sweet consultative closer)
  - Hindi: 'shreya' (Authentic Hinglish telecaller prosody)
- STT: saaras:v3 (Ultra-low latency multilingual speech-to-text)

Zero-cost developer tier with automatic local offline fallback.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Optional, Tuple
import aiohttp

SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"

SARVAM_FEMALE_VOICES = {
    "tamil": "kavitha",   # Flagship sweet Tamil closer
    "hindi": "shreya",    # Flagship sweet Hindi closer
    "english": "shreya",  # Multilingual English
}


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

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    async def synthesize(
        self,
        text: str,
        target_language: str,  # "tamil" or "hindi"
        output_path: str,
        speed: float = 0.95,
    ) -> bool:
        """Synthesizes conversational speech via Sarvam AI API."""
        if not self.is_configured:
            return False

        lang_code = "ta-IN" if "tam" in target_language.lower() else "hi-IN"
        speaker = SARVAM_FEMALE_VOICES.get(target_language.lower(), "shreya")

        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": [text],
            "target_language_code": lang_code,
            "speaker": speaker,
            "pitch": 0,
            "pace": speed,
            "loudness": 1.0,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "model": "bulbul:v3",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(SARVAM_TTS_URL, json=payload, headers=headers, timeout=12) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        audios = data.get("audios", [])
                        if audios:
                            raw_bytes = base64.b64decode(audios[0])
                            with open(output_path, "wb") as f:
                                f.write(raw_bytes)
                            return True
                    else:
                        err_body = await resp.text()
                        print(f"[SarvamVoice] Warning: API status {resp.status}: {err_body[:100]}")
                        return False
        except Exception as e:
            print(f"[SarvamVoice] Network error: {e}")
            return False

        return False

    async def transcribe(self, audio_path: str, language_code: str = "ta-IN") -> Optional[str]:
        """Transcribes speech using Sarvam Saaras v3 multilingual STT."""
        if not self.is_configured or not os.path.exists(audio_path):
            return None

        headers = {"api-subscription-key": self.api_key}
        data = {
            "model": "saaras:v3",
            "language_code": language_code,
        }

        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

            form = aiohttp.FormData()
            form.add_field("file", audio_bytes, filename="audio.wav", content_type="audio/wav")
            form.add_field("model", "saaras:v3")
            form.add_field("language_code", language_code)

            async with aiohttp.ClientSession() as session:
                async with session.post(SARVAM_STT_URL, headers=headers, data=form, timeout=12) as resp:
                    if resp.status == 200:
                        res = await resp.json()
                        return res.get("transcript", "").strip()
                    else:
                        print(f"[SarvamSTT] Error {resp.status}: {await resp.text()}")
        except Exception as e:
            print(f"[SarvamSTT] Exception: {e}")
        return None
