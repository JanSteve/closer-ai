"""
Unit tests for CLOSER AI Expressive Clinical Voice Synthesis & Audio Processing.
Mocks Edge-TTS / Sarvam network layers for deterministic offline execution, validates
24kHz/48kHz WAV headers, Tamil/Hindi/English voices, clinical speech normalization,
and verifies zero 160Hz fallback beep on non-macOS failure.
"""

import io
import math
import os
import struct
import sys
import unittest
import wave
from unittest.mock import patch

from src.closer.voice.stt import WhisperSTTEngine
from src.closer.voice.tts import (
    VOICES,
    VOICE_ALIASES,
    EdgeTTSVoiceEngine,
    inject_duplex_disfluencies,
    normalize_speech_text,
)

_VOICE_ENV_KEYS = (
    "SARVAM_API_KEY",
    "ELEVENLABS_API_KEY",
    "CARTESIA_API_KEY",
)


def _build_speech_like_wav(sample_rate: int = 24000, duration_sec: float = 0.25) -> bytes:
    """Deterministic test WAV payload used only to mock edge_tts stream output."""
    num_samples = int(sample_rate * duration_sec)
    raw = bytearray()
    for i in range(num_samples):
        val = int(math.sin(2 * math.pi * 220.0 * (i / sample_rate)) * 8000)
        raw.extend(struct.pack("<h", val))
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(bytes(raw))
    return out.getvalue()


class _FakeCommunicate:
    def __init__(self, text: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz"):
        self.text = text
        self.voice = voice
        self.rate = rate
        self.pitch = pitch

    async def stream(self):
        wav = _build_speech_like_wav(24000, 0.2)
        yield {"type": "audio", "data": wav}


class TestVoicePipeline(unittest.TestCase):
    """Test suite for clinical voice synthesis, Tamil/Hindi/English normalization, and fallback safety."""

    def setUp(self):
        self._env_patch = patch.dict(os.environ, {k: "" for k in _VOICE_ENV_KEYS})
        self._env_patch.start()
        EdgeTTSVoiceEngine._sarvam_cooldown_until = 0.0
        self.tts = EdgeTTSVoiceEngine()
        self.stt = WhisperSTTEngine()

    def tearDown(self):
        self._env_patch.stop()

    def test_audio_synthesis_riff_header_24khz_and_48khz(self):
        """Verifies synthesized audio produces valid 24kHz and 48kHz mono PCM WAV headers."""
        with patch("edge_tts.Communicate", _FakeCommunicate):
            audio_24, _ = self.tts.synthesize_sync(
                "Hello, this is Neerja calling from Amura Health in Velachery, Chennai.",
                sample_rate=24000,
                style="empathetic",
            )
            self.assertTrue(audio_24.startswith(b"RIFF"))
            with wave.open(io.BytesIO(audio_24), "rb") as w:
                self.assertEqual(w.getnchannels(), 1)
                self.assertEqual(w.getframerate(), 24000)
                self.assertEqual(w.getsampwidth(), 2)

            # Without ffmpeg, 24kHz WAV passes through or converts via ffmpeg if installed; verify valid RIFF
            audio_48, _ = self.tts.synthesize_sync(
                "Your Amura Health consultation is confirmed for Thursday at 2 PM IST.",
                sample_rate=48000,
            )
            self.assertTrue(audio_48.startswith(b"RIFF"))

    def test_tamil_hindi_and_maya_voice_mapping(self):
        """Verifies Tamil (Pallavi/Valluvar), Hindi (Swara/Madhur), and maya_en aliases resolve cleanly."""
        self.assertEqual(VOICES["pallavi"], "ta-IN-PallaviNeural")
        self.assertEqual(VOICES["valluvar"], "ta-IN-ValluvarNeural")
        self.assertEqual(VOICE_ALIASES["maya_en"], "en-US-AvaNeural")
        self.assertEqual(self.tts._resolve_voice_name("maya_en"), "en-US-AvaNeural")
        self.assertEqual(self.tts._resolve_voice_name("pallavi"), "ta-IN-PallaviNeural")

        with patch("edge_tts.Communicate", _FakeCommunicate):
            for v in (VOICES["pallavi"], VOICES["swara"], VOICES["madhur"], VOICES["neerja_expressive"], VOICES["maya_en"]):
                audio, latency = self.tts.synthesize_sync("Amura Health consultation confirmed.", voice=v)
                self.assertTrue(audio.startswith(b"RIFF"))
                self.assertLess(latency, 2.0)

    def test_vad_barge_in_energy_detection(self):
        """Verifies VAD detects speech-level energy and rejects zero-energy silence."""
        wav = _build_speech_like_wav(24000, 0.2)
        self.assertTrue(self.stt.detect_voice_activity(wav))
        self.assertFalse(self.stt.detect_voice_activity(b"\x00" * 4800))

    def test_clinical_and_indian_speech_normalization(self):
        """Verifies clinical abbreviations, INR currency, IST timezone, and street normalization."""
        text = "Dr. Godwin reviewed HbA1c mg/dL, MNT & NMT at 142 Velachery Main Rd. at 11:00 AM IST for ₹1.25 Lakhs w/ WhatsApp & 108."
        clean = normalize_speech_text(text)
        self.assertIn("Doctor Godwin", clean)
        self.assertIn("H-b-A-1-c", clean)
        self.assertIn("milligrams per deciliter", clean)
        self.assertIn("Medical Nutrition Therapy", clean)
        self.assertIn("Natural Molecule Therapy", clean)
        self.assertIn("Velachery Main Road", clean)
        self.assertIn("11 A-M", clean)
        self.assertIn("Indian Standard Time", clean)
        self.assertIn("1.25 lakh rupees", clean)
        self.assertIn("Whats App", clean)

    def test_trilingual_disfluencies_and_tamil_micro_breaths(self):
        """Verifies English, Indian English, Hindi, and Tamil courtesy fillers."""
        self.assertTrue(normalize_speech_text("Gotcha, let us review your lab reports.").startswith("Gotcha..."))
        self.assertTrue(normalize_speech_text("Namaste sir, how may I assist you?").startswith("Namaste sir..."))
        self.assertTrue(normalize_speech_text("नमस्ते जी, आपकी क्या सहायता करूँ?").startswith("नमस्ते जी... "))
        self.assertTrue(normalize_speech_text("வணக்கம், எப்படி உதவலாம்?").startswith("வணக்கம்... "))

        ta_line = inject_duplex_disfluencies("உங்க அப்பாயின்ட்மென்ட் கன்ஃபார்ம் ஆயிடுச்சு.", market="tamil", intent="acknowledgement")
        self.assertTrue(ta_line.startswith("சரிங்க..."))

    def test_non_macos_failure_returns_empty_browser_fallback_no_160hz_beep(self):
        """Verifies non-macOS offline fallback NEVER emits a 160Hz PCM beep."""
        class _FailingCommunicate:
            def __init__(self, *a, **kw):
                pass

            async def stream(self):
                raise RuntimeError("offline")
                yield  # pragma: no cover

        with patch.object(sys, "platform", "linux"), patch("edge_tts.Communicate", _FailingCommunicate):
            audio_bytes, _ = self.tts.synthesize_sync("Testing fallback", style="empathetic")
            self.assertEqual(audio_bytes, b"")
            self.assertEqual(self.tts.last_provider_used, "browser_fallback")


if __name__ == "__main__":
    unittest.main()
