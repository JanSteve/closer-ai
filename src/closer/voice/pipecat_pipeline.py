"""
Pipecat-Inspired Streaming Conversational Pipeline Orchestrator for Amura Health / CLOSER AI.
Manages frame-by-frame streaming between:
Audio In -> Silero VAD -> Sarvam Saaras v3 STT -> Clinical Safety & Emotion -> LLM -> Sarvam bulbul:v3 TTS -> Audio Out.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from src.closer.agent.conversation import ConversationEngine
from src.closer.voice.vad import SileroVADDetector


@dataclass
class AudioFrame:
    """Represents a discrete audio frame in the streaming pipeline."""

    data: np.ndarray
    sample_rate: int = 16000
    timestamp_ms: float = field(default_factory=lambda: time.time() * 1000)
    is_speech: bool = False


class PipecatVoicePipeline:
    """
    Streaming Conversational Orchestrator for clinical front-desk & metabolic intake.
    """

    def __init__(
        self,
        language: str = "tamil",
        market_mode: str = "tamil",
        conversation_engine: Optional[ConversationEngine] = None,
        vad_detector: Optional[SileroVADDetector] = None,
    ):
        self.language = language
        self.market_mode = market_mode
        self.engine = conversation_engine or ConversationEngine(
            market_mode=market_mode,
            sector="amura_metabolic",
            business_name="Amura Health",
        )
        self.engine.set_market_mode(market_mode)
        self.vad = vad_detector or SileroVADDetector()

        self.ai_speaking = False
        self.interrupted = False
        self.audio_buffer: List[np.ndarray] = []
        self.total_turns_processed = 0

    def process_incoming_frame(self, frame: AudioFrame) -> Dict[str, Any]:
        """Evaluates voice activity and checks for barge-in interruptions."""
        is_speech, confidence = self.vad.is_speech_active(frame.data)
        barge_in = self.vad.detect_barge_in(frame.data, ai_currently_speaking=self.ai_speaking)

        if barge_in:
            self.interrupted = True
            self.ai_speaking = False

        if is_speech:
            self.audio_buffer.append(frame.data)

        return {
            "is_speech": is_speech,
            "confidence": confidence,
            "barge_in_triggered": barge_in,
            "buffered_chunks": len(self.audio_buffer),
        }

    async def execute_conversational_turn(self, user_transcript: str) -> Dict[str, Any]:
        """Processes transcribed patient speech with emotion & clinical safety guardrails."""
        start_time = time.perf_counter()
        self.interrupted = False
        self.ai_speaking = True
        self.total_turns_processed += 1

        response_text = self.engine.process_user_turn(user_transcript)
        llm_latency_ms = int((time.perf_counter() - start_time) * 1000)

        persona = "pallavi" if self.language == "tamil" else ("swara" if self.language == "hindi" else "neerja")

        return {
            "user_transcript": user_transcript,
            "ai_response": response_text,
            "voice_persona": persona,
            "language": self.language,
            "latency_ms": llm_latency_ms,
            "interrupted": self.interrupted,
        }

    def reset_buffer(self) -> None:
        self.audio_buffer.clear()
