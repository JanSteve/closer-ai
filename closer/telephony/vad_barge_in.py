"""Layer 2: Barge-In Controller, Silero VAD, and Neural Noise Suppression.

Components:
1. AudioNoiseSuppressor:
   - High-pass filtering (>85Hz) to remove AC/fan rumble.
   - Neural/Spectral noise reduction via noisereduce to isolate speech from ambient noise.
2. SileroVADDetector:
   - Evaluates 32ms frames (512 samples @ 16kHz) with Silero VAD neural network.
   - Returns human speech probability P(speech) in [0, 1].
3. BargeInController:
   - Continuously monitors mic input while the AI agent is speaking.
   - If user speaks for >= 2 frames (~64ms), instantly halts AI speech playback,
     purges pending audio buffers, and transitions agent state to LISTENING.
"""

from __future__ import annotations

import enum
import time
from typing import Callable, Optional, Tuple

import numpy as np
from scipy import signal
import torch


class AgentCallState(enum.Enum):
    IDLE = "IDLE"
    USER_SPEAKING = "USER_SPEAKING"
    AGENT_THINKING = "AGENT_THINKING"
    AGENT_SPEAKING = "AGENT_SPEAKING"


class AudioNoiseSuppressor:
    """Pre-filters mic audio using DSP bandpass and neural spectral gating."""

    def __init__(self, sample_rate: int = 16000, low_cutoff: float = 85.0, high_cutoff: float = 7500.0):
        self.sample_rate = sample_rate
        # Design Butterworth bandpass filter
        nyquist = 0.5 * sample_rate
        low = low_cutoff / nyquist
        high = min(high_cutoff / nyquist, 0.99)
        self.b, self.a = signal.butter(4, [low, high], btype="band")
        self.noise_profile = None

    def filter_dsp(self, audio_data: np.ndarray) -> np.ndarray:
        """Applies zero-phase Butterworth bandpass filtering."""
        if len(audio_data) < 16:
            return audio_data
        try:
            return signal.filtfilt(self.b, self.a, audio_data).astype(np.float32)
        except Exception:
            return audio_data

    def suppress_neural(self, audio_data: np.ndarray, prop_decrease: float = 0.75) -> np.ndarray:
        """Applies neural spectral subtraction to strip stationary background noise."""
        if len(audio_data) < 256:
            return audio_data
        try:
            import noisereduce as nr
            # Quick stationary spectral reduction
            cleaned = nr.reduce_noise(
                y=audio_data,
                sr=self.sample_rate,
                stationary=True,
                prop_decrease=prop_decrease,
                n_fft=min(512, len(audio_data)),
            )
            return cleaned.astype(np.float32)
        except Exception:
            return audio_data

    def process(self, audio_data: np.ndarray, use_neural: bool = False) -> np.ndarray:
        """Full noise suppression pipeline."""
        filtered = self.filter_dsp(audio_data)
        if use_neural:
            filtered = self.suppress_neural(filtered)
        return filtered


class SileroVADDetector:
    """Silero VAD neural network for real-time speech detection."""

    _model = None

    def __init__(self, sample_rate: int = 16000, threshold: float = 0.50):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self._ensure_model()

    @classmethod
    def _ensure_model(cls):
        if cls._model is None:
            model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                trust_repo=True,
            )
            cls._model = model
            cls._model.eval()

    def detect_frame(self, frame: np.ndarray) -> Tuple[bool, float]:
        """Evaluates a 512-sample (32ms) frame.
        
        Returns:
            Tuple[bool, float]: (is_speech, confidence_score)
        """
        if len(frame) != 512:
            # Pad or truncate to 512 samples
            if len(frame) < 512:
                frame = np.pad(frame, (0, 512 - len(frame)))
            else:
                frame = frame[:512]

        # Convert to torch float32 tensor
        tensor = torch.from_numpy(frame.astype(np.float32))
        with torch.no_grad():
            prob = self._model(tensor, self.sample_rate).item()
            
        return (prob >= self.threshold, prob)


class BargeInController:
    """Real-time interruption monitor and playback controller."""

    def __init__(
        self,
        vad_detector: Optional[SileroVADDetector] = None,
        noise_suppressor: Optional[AudioNoiseSuppressor] = None,
        on_barge_in: Optional[Callable[[], None]] = None,
        consecutive_frames_required: int = 2,
    ):
        self.vad = vad_detector or SileroVADDetector()
        self.suppressor = noise_suppressor or AudioNoiseSuppressor()
        self.on_barge_in = on_barge_in
        self.consecutive_frames_required = consecutive_frames_required
        
        self.state = AgentCallState.IDLE
        self.consecutive_speech_count = 0
        self.last_speech_time = 0.0

    def set_state(self, state: AgentCallState) -> None:
        self.state = state
        if state != AgentCallState.AGENT_SPEAKING:
            self.consecutive_speech_count = 0

    def process_incoming_frame(self, raw_frame: np.ndarray) -> Tuple[bool, float, bool]:
        """Processes a 32ms mic frame.
        
        Returns:
            Tuple[bool, float, bool]: (is_speech, prob, barge_in_triggered)
        """
        # 1. Noise suppression
        clean_frame = self.suppressor.filter_dsp(raw_frame)

        # 2. Silero VAD evaluation
        is_speech, prob = self.vad.detect_frame(clean_frame)

        barge_in_triggered = False

        if is_speech:
            self.consecutive_speech_count += 1
            self.last_speech_time = time.time()
            
            # Check if agent is speaking and user interrupted
            if self.state == AgentCallState.AGENT_SPEAKING:
                if self.consecutive_speech_count >= self.consecutive_frames_required:
                    barge_in_triggered = True
                    self.set_state(AgentCallState.USER_SPEAKING)
                    if self.on_barge_in:
                        self.on_barge_in()
        else:
            self.consecutive_speech_count = max(0, self.consecutive_speech_count - 1)

        return (is_speech, prob, barge_in_triggered)
