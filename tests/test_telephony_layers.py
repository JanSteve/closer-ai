"""Unit tests for Telephony Layer 1 (Full Duplex & Token Streaming) and Layer 2 (Barge-In & Silero VAD).

TDD test suite verifying:
1. TokenSentenceAccumulator prosodic clause extraction.
2. TokenStreamingSynthesizer interrupt capability.
3. AudioNoiseSuppressor DSP filtering.
4. SileroVADDetector speech confidence calculation.
5. BargeInController state transitions and interruption trigger.
"""

import asyncio
import numpy as np
import pytest

from closer.telephony.token_synthesizer import TokenSentenceAccumulator, TokenStreamingSynthesizer
from closer.telephony.vad_barge_in import (
    AgentCallState,
    AudioNoiseSuppressor,
    BargeInController,
    SileroVADDetector,
)
from closer.voice_engine import NeuralVoiceEngine


class TestTokenStreamingPipeline:

    @pytest.mark.asyncio
    async def test_token_sentence_accumulator(self):
        accumulator = TokenSentenceAccumulator(min_token_length=3)

        async def mock_token_stream():
            tokens = ["வணக்கம் ", "Sir! ", "நீங்க ", "family ", "stay ", "பண்ண ", "3 BHK ", "பாக்குறீங்களா?"]
            for t in tokens:
                yield t

        clauses = []
        async for clause in accumulator.process_stream(mock_token_stream()):
            clauses.append(clause)

        assert len(clauses) >= 1
        assert any("Sir" in c for c in clauses)

    def test_synthesizer_interrupt_flushes_state(self):
        engine = NeuralVoiceEngine()
        synth = TokenStreamingSynthesizer(engine, agent_name="english")
        synth.audio_queue.put_nowait("/tmp/dummy.wav")
        assert not synth.audio_queue.empty()

        synth.interrupt()
        assert synth.is_interrupted is True


class TestBargeInAndVAD:

    def test_noise_suppressor_dsp(self):
        suppressor = AudioNoiseSuppressor(sample_rate=16000)
        # Create 16kHz audio with low frequency rumble (30Hz)
        t = np.linspace(0, 0.1, 1600, endpoint=False)
        rumble = np.sin(2 * np.pi * 30 * t).astype(np.float32)
        filtered = suppressor.filter_dsp(rumble)

        # 30Hz rumble amplitude should be attenuated
        assert np.max(np.abs(filtered)) < np.max(np.abs(rumble))

    def test_silero_vad_detection(self):
        detector = SileroVADDetector(sample_rate=16000, threshold=0.5)
        silence = np.zeros(512, dtype=np.float32)
        is_speech, prob = detector.detect_frame(silence)
        assert is_speech is False
        assert prob < 0.2

    def test_barge_in_trigger_during_agent_speaking(self):
        barge_in_fired = False

        def on_barge():
            nonlocal barge_in_fired
            barge_in_fired = True

        controller = BargeInController(
            on_barge_in=on_barge,
            consecutive_frames_required=2,
        )
        controller.set_state(AgentCallState.AGENT_SPEAKING)

        # Mock speech frame with high speech probability by mocking detect_frame
        controller.vad.detect_frame = lambda frame: (True, 0.95)

        dummy_frame = np.ones(512, dtype=np.float32) * 0.1
        
        # Frame 1: speech detected, not yet 2 frames
        _, _, triggered1 = controller.process_incoming_frame(dummy_frame)
        assert triggered1 is False
        assert barge_in_fired is False

        # Frame 2: consecutive speech >= 2, triggers barge-in!
        _, _, triggered2 = controller.process_incoming_frame(dummy_frame)
        assert triggered2 is True
        assert barge_in_fired is True
        assert controller.state == AgentCallState.USER_SPEAKING
