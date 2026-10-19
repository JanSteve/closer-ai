"""
Voice subsystem for CLOSER AI: EdgeTTS, Whisper STT, and CallSession.
"""

from src.closer.voice.tts import EdgeTTSVoiceEngine, VOICES
from src.closer.voice.stt import WhisperSTTEngine
from src.closer.voice.call_session import CallSession

__all__ = [
    "EdgeTTSVoiceEngine",
    "VOICES",
    "WhisperSTTEngine",
    "CallSession"
]
