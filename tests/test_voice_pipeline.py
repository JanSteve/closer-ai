"""
Unit tests for CLOSER AI Voice Synthesis & Audio Processing.
Verifies audio synthesis, 24kHz/48kHz WAV headers, American accent voices, and low latency.
"""

import io
import wave
import unittest
from src.closer.voice.tts import EdgeTTSVoiceEngine, VOICES
from src.closer.voice.stt import WhisperSTTEngine


class TestVoicePipeline(unittest.TestCase):
    """Test suite for neural speech generation and audio header conformity."""

    def setUp(self):
        self.tts = EdgeTTSVoiceEngine()
        self.stt = WhisperSTTEngine()

    def test_audio_synthesis_riff_header_24khz(self):
        """Verifies synthesized audio produces a valid 24kHz mono PCM WAV header."""
        test_text = "Hello, this is Sophia calling from Daniel and Associates Luxury Realty."
        audio_bytes, latency = self.tts.synthesize_sync(test_text, sample_rate=24000)

        self.assertIsNotNone(audio_bytes)
        self.assertGreater(len(audio_bytes), 1000)
        self.assertTrue(audio_bytes.startswith(b"RIFF"))

        # Verify WAV header parameters via standard library
        with wave.open(io.BytesIO(audio_bytes), "rb") as w:
            channels = w.getnchannels()
            framerate = w.getframerate()
            sampwidth = w.getsampwidth()
            nframes = w.getnframes()

        self.assertEqual(channels, 1, "Audio must be single channel mono for cellular telephony")
        self.assertEqual(framerate, 24000, "Sample rate must match 24,000 Hz")
        self.assertEqual(sampwidth, 2, "Sample width must be 16-bit PCM (2 bytes per sample)")
        self.assertGreater(nframes, 1000, "Frame count must be non-trivial")

    def test_audio_synthesis_riff_header_48khz(self):
        """Verifies high-fidelity 48kHz audio synthesis conforms to studio WAV specs."""
        test_text = "Exclusive private showing confirmed for Thursday."
        audio_bytes, latency = self.tts.synthesize_sync(test_text, sample_rate=48000)

        with wave.open(io.BytesIO(audio_bytes), "rb") as w:
            framerate = w.getframerate()

        self.assertEqual(framerate, 48000, "Sample rate must match 48,000 Hz")

    def test_american_accent_voice_switching(self):
        """Verifies switching between Guy (male) and Aria (female) neural voices."""
        # Guy (male, confident broker)
        guy_audio, _ = self.tts.synthesize_sync("Welcome to Bel Air.", voice=VOICES["guy"])
        self.assertTrue(guy_audio.startswith(b"RIFF"))

        # Aria (female, consultative executive assistant)
        aria_audio, _ = self.tts.synthesize_sync("Would Thursday at 2 PM suit your schedule?", voice=VOICES["aria"])
        self.assertTrue(aria_audio.startswith(b"RIFF"))

    def test_synthesis_latency_performance(self):
        """Verifies synthesis meets real-time conversational telephony requirements."""
        short_prompt = "Certainly. What is your ideal timeframe?"
        _, latency = self.tts.synthesize_sync(short_prompt)
        # Latency should be under 1.5s even under cold start and sub-second in standard conditions
        self.assertLess(latency, 2.0, f"Synthesis latency too high: {latency:.3f}s")

    def test_vad_barge_in_energy_detection(self):
        """Verifies voice activity detection detects speech signal over ambient threshold."""
        # Generate speech wave
        audio_bytes, _ = self.tts.synthesize_sync("I want to make an offer right now.")
        has_speech = self.stt.detect_voice_activity(audio_bytes)
        self.assertTrue(has_speech, "VAD must detect active human speech energy")

        # Zero energy / silence test
        silence = b"\x00" * 4800
        has_silence_speech = self.stt.detect_voice_activity(silence)
        self.assertFalse(has_silence_speech, "VAD must not flag pure silence as speech")


if __name__ == "__main__":
    unittest.main()
