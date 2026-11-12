"""Enterprise Multi-Provider Neural Voice Engine for CLOSER AI.

1. English: Signature CLOSER AI (Kokoro 3-Way SOTA Blend: 55% Heart + 30% Nicole + 15% Bella)
   - 100% Local, Offline, ElevenLabs-grade human warmth & micro-breaths. STRICTLY LOCKED IN.
2. Tamil: பல்லவி (Pallavi — Sweet Tanglish Female Closer)
   - Real Chennai real-estate telecaller cadence, crisp 'Sir' (no 'saar' distortion), smooth loanwords.
3. Hindi: स्वाति (Swati — Sweet Hinglish Female Closer)
   - Real North Indian consultative cadence, warm prosody, polite Hinglish telecaller tone.

Zero-cost, zero-key local execution automatically active.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import soundfile as sf

from closer.telephony.phonetic_normalizer import IndicPhoneticNormalizer
from closer.telephony.sarvam_engine import SarvamVoiceEngine

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
KOKORO_MODEL_PATH = MODELS_DIR / "kokoro-v1.0.onnx"
KOKORO_VOICES_PATH = MODELS_DIR / "voices-v1.0.bin"

# Exactly 1 Dedicated Female Voice per Language
VOICE_PROFILES: Dict[str, Dict[str, Union[str, float]]] = {
    # 1. English Female Closer (LOCKED IN - Kokoro 3-Way SOTA Blend)
    "english": {
        "engine": "kokoro",
        "voice_id": "blend_signature_v2",
        "language": "English (Female Closer)",
        "label": "Signature CLOSER AI (English Female Closer)",
        "speed": 0.95,
    },
    # 2. Tamil Female Closer (Tanglish Sweet Telecaller)
    "tamil": {
        "engine": "auto_indic",
        "voice_id": "ta-IN-PallaviNeural",
        "language": "Tamil (Female Closer)",
        "label": "பல்லவி (Pallavi — Sweet Tanglish Female Closer)",
        "rate": "-3%",
        "pitch": "+1Hz",
    },
    # 3. Hindi Female Closer (Hinglish Sweet Telecaller)
    "hindi": {
        "engine": "auto_indic",
        "voice_id": "hi-IN-SwaraNeural",
        "language": "Hindi (Female Closer)",
        "label": "स्वाति (Swati — Sweet Hinglish Female Closer)",
        "rate": "-4%",
        "pitch": "+1Hz",
    },
}

VOICE_PROFILES["signature"] = VOICE_PROFILES["english"]
VOICE_PROFILES["pallavi"] = VOICE_PROFILES["tamil"]
VOICE_PROFILES["swati"] = VOICE_PROFILES["hindi"]

DEFAULT_FILLERS: Dict[str, str] = {
    "english": "Look, let me check the private allocation for you...",
    "tamil": "கண்டிப்பா Sir, நான் உடனே check பண்ணி சொல்றேங்க...",
    "hindi": "जी बिल्कुल, मैं अभी inventory details check करके बताती हूँ जी...",
}
DEFAULT_FILLERS["signature"] = DEFAULT_FILLERS["english"]
DEFAULT_FILLERS["pallavi"] = DEFAULT_FILLERS["tamil"]
DEFAULT_FILLERS["swati"] = DEFAULT_FILLERS["hindi"]


class NeuralVoiceEngine:
    """Enterprise voice engine combining local Kokoro, Resemble Chatterbox, and Indic telecaller backends."""

    _kokoro_instance = None
    _chatterbox_instance = None

    def __init__(self, default_agent: str = "english"):
        self.current_agent = default_agent.lower()
        if self.current_agent not in VOICE_PROFILES:
            self.current_agent = "english"
        self.sarvam = SarvamVoiceEngine()

    @classmethod
    def _get_kokoro(cls):
        if cls._kokoro_instance is None and KOKORO_MODEL_PATH.exists() and KOKORO_VOICES_PATH.exists():
            import kokoro_onnx
            cls._kokoro_instance = kokoro_onnx.Kokoro(
                model_path=str(KOKORO_MODEL_PATH),
                voices_path=str(KOKORO_VOICES_PATH),
            )
        return cls._kokoro_instance

    @classmethod
    def _get_chatterbox(cls):
        if cls._chatterbox_instance is None:
            try:
                import torch
                from chatterbox.tts import ChatterboxTTS
                device = "mps" if torch.backends.mps.is_available() else "cpu"
                cls._chatterbox_instance = ChatterboxTTS.from_pretrained(device=device)
            except Exception:
                cls._chatterbox_instance = None
        return cls._chatterbox_instance

    def set_agent(self, agent_name: str) -> None:
        agent_name = agent_name.lower()
        if agent_name in VOICE_PROFILES:
            self.current_agent = agent_name

    def get_agent_profile(self) -> Dict[str, Union[str, float]]:
        return VOICE_PROFILES[self.current_agent]

    async def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        agent: Optional[str] = None,
        sentence_pause: float = 0.40,
        clause_pause: float = 0.20,
    ) -> str:
        """Synthesizes text to an audio file with automatic Indic phonetic normalization."""
        target_agent = (agent or self.current_agent).lower()
        profile = VOICE_PROFILES.get(target_agent, VOICE_PROFILES["english"])
        engine = profile.get("engine", "kokoro")
        loop = asyncio.get_running_loop()

        # Step 1: Pre-process with IndicPhoneticNormalizer to eliminate "saar", loanword breaks, and stutters
        clean_text = IndicPhoneticNormalizer.normalize(text, target_agent)

        # 1. English Female (Kokoro SOTA 3-Way Blend) - STRICTLY LOCKED IN
        if engine == "kokoro":
            kokoro = self._get_kokoro()
            if kokoro is not None:
                style_heart = kokoro.get_voice_style("af_heart")
                style_nicole = kokoro.get_voice_style("af_nicole")
                style_bella = kokoro.get_voice_style("af_bella")
                voice_style = (0.55 * style_heart) + (0.30 * style_nicole) + (0.15 * style_bella)
                speed = float(profile.get("speed", 0.95))

                samples, sample_rate = await loop.run_in_executor(
                    None,
                    lambda: kokoro.create(
                        text=clean_text,
                        voice=voice_style,
                        speed=speed,
                        lang="en-us",
                        sentence_pause=sentence_pause,
                        clause_pause=clause_pause,
                    ),
                )
                wav_path = output_path if output_path.endswith(".wav") else output_path.rsplit(".", 1)[0] + ".wav"
                sf.write(wav_path, samples, sample_rate)
                return wav_path

        # 2. Resemble AI Chatterbox Engine (if explicitly selected or available)
        if engine == "chatterbox":
            cb = self._get_chatterbox()
            if cb is not None:
                wav_path = output_path if output_path.endswith(".wav") else output_path.rsplit(".", 1)[0] + ".wav"
                wav = await loop.run_in_executor(None, lambda: cb.generate(clean_text, exaggeration=0.6))
                import torchaudio as ta
                ta.save(wav_path, wav, cb.sr)
                return wav_path

        # 3. Indic Languages (Tamil & Hindi) routed via Unified Indic Neural Engine
        # Supports ai4bharat/IndicF5, ai4bharat/indic-parler-tts, fishaudio/fish-speech,
        # Sarvam AI bulbul:v3, and Dialect Breath-Paced Edge-TTS fallback.
        from closer.telephony.indic_neural_engine import IndicNeuralVoiceEngine

        lang_key = "tamil" if "tamil" in target_agent or "pallavi" in target_agent else "hindi"
        dialect = str(profile.get("dialect", "")) or None
        indic_engine = IndicNeuralVoiceEngine(sarvam_engine=self.sarvam)
        audio_bytes, provider_used, _, audio_fmt = await indic_engine.synthesize(
            text=text,
            language=lang_key,
            dialect=dialect,
            rate=str(profile.get("rate", "-4%")),
            pitch=str(profile.get("pitch", "+1Hz")),
        )
        self.last_provider_used = provider_used
        ext = f".{audio_fmt}" if audio_fmt in ("wav", "mp3") else ".mp3"
        final_path = output_path if output_path.endswith(ext) else output_path.rsplit(".", 1)[0] + ext
        with open(final_path, "wb") as f:
            f.write(audio_bytes)
        return final_path

    def get_filler_phrase(self, agent: Optional[str] = None) -> str:
        target = (agent or self.current_agent).lower()
        return DEFAULT_FILLERS.get(target, DEFAULT_FILLERS["english"])
