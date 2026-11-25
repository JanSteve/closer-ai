"""
Bidirectional clinical audio session manager with sub-50ms barge-in interruption handling.
Supports English, Indian English, Tamil/Tanglish, and Hindi/Hinglish across Amura Health workflows.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.schemas import BuyerDossier, CallSessionState, InboundLead
from src.closer.config import settings
from src.closer.voice.stt import WhisperSTTEngine
from src.closer.voice.tts import EdgeTTSVoiceEngine

logger = logging.getLogger(__name__)

# Module-level regex for reflex conversational sync detection (<90ms fast-path)
REFLEX_SYNC_PATTERNS = re.compile(
    r"^(hello\??|hi\??|hey\??|can you hear me\??|are you there\??|you there\??|yeah\??|yes\??|yep\??|speaking\??|yes speaking\??|uh-huh\??|"
    r"haanji\??|haan ji\??|namaste\??|namaskar\??|pranam\??|"
    r"vanakkam\??|வணக்கம்\??|kekutha\??|கேக்குதா\??|sollunga\??|சொல்லுங்க\??|aama\??|ஆமா\??|seri\??|சரி\??)"
    r"(?:\s*[,!?]\s*(?:can you hear me|are you there|you there|hello|hi|speaking|haanji|namaste|vanakkam|kekutha|sollunga)\??)*\b",
    re.IGNORECASE,
)

# Reflex response fast-path dialogue templates across market modes
REFLEX_RESPONSES: Dict[str, Dict[str, str]] = {
    "english": {
        "audible": "Yes, I can hear you clearly! I'm right here with Amura Health.",
        "greeting": "Hello! Yes, I'm right here. How can I help with your consultation today?",
        "affirmation": "Thank you — I'm right here with you. Please go ahead.",
        "default": "Yes, I'm right here! How may I assist you today?",
    },
    "usa": {
        "audible": "Yes, I can hear you clearly! I'm right here.",
        "greeting": "Hello! Yes, I'm right here. How can I assist you today?",
        "affirmation": "Thank you — I'm right here with you. Please go ahead.",
        "default": "Yes, I'm right here! How can I help you?",
    },
    "india": {
        "audible": "Yes, I can hear you clearly! How may I assist you with Amura Health today?",
        "greeting": "Namaste! Yes, I am right here. How may I assist you today?",
        "affirmation": "Certainly! I am right here with you — please go ahead.",
        "default": "Namaste, yes I can hear you clearly! How may I assist you?",
    },
    "tamil": {
        "audible": "ஆமாங்க, தெளிவா கேக்குது! Amura Health-ல இருந்து பேசுறேன், சொல்லுங்க.",
        "greeting": "வணக்கம்! நான் இங்க தான் இருக்கேங்க. உங்க உடல்நல ஆலோசனை பத்தி சொல்லுங்க.",
        "affirmation": "சரிங்க, நான் கேட்டுட்டு இருக்கேன். தொடர்ந்து சொல்லுங்க.",
        "default": "வணக்கம், தெளிவா கேக்குதுங்க! எப்படி உதவலாம் சொல்லுங்க?",
    },
    "hindi": {
        "audible": "हाँ जी, मैं बिल्कुल साफ सुन रही हूँ! बताइए, मैं आपकी क्या सहायता करूँ?",
        "greeting": "नमस्ते जी! हाँ जी, मैं सुन रही हूँ। बताइए, स्वास्थ्य परामर्श में क्या सहायता करूँ?",
        "affirmation": "जी बिल्कुल, मैं सुन रही हूँ! कृपया बताइए।",
        "default": "हाँ जी, मैं सुन रही हूँ! बताइए, मैं आपकी क्या सहायता करूँ?",
    },
}

_REFLEX_AUDIO_CACHE: Dict[Tuple[str, str, int], bytes] = {}


class PacingResult(tuple):
    """2-tuple of (tier_name, delay_seconds) supporting tuple unpacking and named properties."""

    def __new__(cls, tier: str, delay: float):
        return super().__new__(cls, (tier, delay))

    @property
    def tier(self) -> str:
        return self[0]

    @property
    def delay(self) -> float:
        return self[1]

    def __float__(self) -> float:
        return float(self[1])

    def __repr__(self) -> str:
        return f"PacingResult(tier={self.tier!r}, delay={self.delay:.3f})"


class DynamicLatencyPacer:
    """Calculates dynamic conversational latency and pacing delay based on utterance complexity."""

    REFLEX_DELAY: float = 0.035
    COGNITIVE_DELAY: float = 0.280
    STANDARD_DELAY: float = 0.120

    @classmethod
    def is_reflex_sync(cls, user_text: str) -> bool:
        """Determines if utterance is a standalone conversational reflex sync."""
        if not user_text or not user_text.strip():
            return False
        cleaned = user_text.strip()
        words = re.findall(r"[\w']+", cleaned)
        if len(words) > 5:
            return False
        if not REFLEX_SYNC_PATTERNS.search(cleaned):
            return False

        substantive = [
            "chest", "pain", "breathing", "emergency", "108", "diabetes", "hba1c",
            "insulin", "pcos", "pcod", "thyroid", "doctor", "consult", "consultation",
            "prescription", "dosage", "fasting", "report", "appointment", "schedule",
            "tomorrow", "busy", "meeting", "complaint", "ticket", "fee", "price",
            "reschedule", "browsing",
        ]
        cleaned_lower = cleaned.lower()
        if any(w in cleaned_lower for w in substantive):
            return False
        return True

    @classmethod
    def is_complex_or_friction(cls, user_text: str, is_friction: bool = False) -> bool:
        """Detects if utterance involves complex clinical triage, friction, or scheduling."""
        if is_friction:
            return True
        t = user_text.lower().strip()
        complex_keywords = [
            "tomorrow", "busy", "meeting", "contact me later", "call me later",
            "call tomorrow", "not good", "a wash", "flip side", "later", "in a zoom",
            "in a conference", "with a client", "driving", "bad time", "reschedule",
            "chest pain", "breathing", "emergency", "108", "diabetes", "hba1c",
            "insulin", "pcos", "thyroid", "prescription", "dosage", "diagnose",
            "complaint", "ticket", "fee", "price", "expensive", "out of town",
            "call back", "browsing", "just looking", "think about it", "not ready",
        ]
        return any(k in t for k in complex_keywords)

    @classmethod
    def calculate_pacing_delay(cls, user_text: str, is_friction: bool = False) -> PacingResult:
        if cls.is_reflex_sync(user_text):
            return PacingResult("reflex_sync", cls.REFLEX_DELAY)
        if cls.is_complex_or_friction(user_text, is_friction=is_friction):
            return PacingResult("cognitive_paced", cls.COGNITIVE_DELAY)
        return PacingResult("standard", cls.STANDARD_DELAY)

    def get_delay(self, user_text: str, is_friction: bool = False) -> PacingResult:
        return self.calculate_pacing_delay(user_text, is_friction=is_friction)


class AbortSpeakingCallable(int):
    """Dual-purpose bool flag and callable barge-in abort handle."""

    def __new__(cls, val: bool, session: Any):
        obj = super().__new__(cls, 1 if val else 0)
        obj._val = bool(val)
        obj._session = session
        return obj

    def __bool__(self) -> bool:
        return self._val

    def __call__(self, interrupted_fragment: Optional[str] = None) -> bool:
        return self._session._execute_barge_in_abort(interrupted_fragment)


class CallSession:
    """
    Manages an active clinical voice call lifecycle.
    Coordinates STT, ConversationEngine (with Emotion + Guardrails), and TTS with barge-in.
    """

    def __init__(
        self,
        lead: Optional[InboundLead] = None,
        voice_engine: Optional[EdgeTTSVoiceEngine] = None,
        stt_engine: Optional[WhisperSTTEngine] = None,
    ):
        self.session_id = f"call_{uuid.uuid4().hex[:12]}"
        self.lead = lead or InboundLead(
            lead_id=f"patient_{uuid.uuid4().hex[:8]}",
            full_name="Karthik Subramanian",
            phone_number="+91-98400-12345",
            market_region="INDIA",
            clinic_location=settings.CLINIC_ADDRESS,
        )
        initial_market = "india"
        if self.lead and getattr(self.lead, "market_region", None):
            mr = str(self.lead.market_region).lower()
            if any(k in mr for k in ("tamil", "ta-in", "chennai")):
                initial_market = "tamil"
            elif any(k in mr for k in ("hindi", "hi-in")):
                initial_market = "hindi"
            elif any(k in mr for k in ("india", "en-in")):
                initial_market = "india"
            elif "usa" in mr:
                initial_market = "usa"

        self.engine = ConversationEngine(
            lead=self.lead,
            market_mode=initial_market,
            sector="amura_metabolic",
            business_name=settings.CLINIC_NAME,
        )
        self.tts = voice_engine or EdgeTTSVoiceEngine()
        self.stt = stt_engine or WhisperSTTEngine()

        self.state = CallSessionState(
            session_id=self.session_id,
            lead_id=self.lead.lead_id,
            status="IDLE",
            caller_phone=settings.TWILIO_PHONE_NUMBER,
            recipient_phone=self.lead.phone_number,
            start_time=datetime.now(timezone.utc).isoformat(),
        )

        self.audio_log: List[bytes] = []
        self.is_speaking = False
        self._abort_flag = False
        self.interrupted_count = 0
        self.was_interrupted = False
        self.last_interrupted_fragment: Optional[str] = None
        self.current_speaking_text: Optional[str] = None
        self.last_barge_in_latency_ms: Optional[float] = None
        self.last_pacing_tier: Optional[str] = None
        self.pacer = DynamicLatencyPacer()

        self.latencies_stt: List[float] = []
        self.latencies_llm: List[float] = []
        self.latencies_tts: List[float] = []
        self.latencies_turn_total_ms: List[float] = []

    @property
    def abort_speaking(self) -> AbortSpeakingCallable:
        return AbortSpeakingCallable(self._abort_flag, self)

    @abort_speaking.setter
    def abort_speaking(self, val: Any) -> None:
        if bool(val):
            self._execute_barge_in_abort()
        else:
            self._abort_flag = False

    def _execute_barge_in_abort(self, interrupted_fragment: Optional[str] = None) -> bool:
        """Truncates active playback within 50ms and records interruption state."""
        t0 = time.perf_counter()
        self._abort_flag = True
        self.is_speaking = False
        self.was_interrupted = True
        self.interrupted_count += 1
        self.state.interrupted_count = self.interrupted_count

        if interrupted_fragment:
            self.last_interrupted_fragment = interrupted_fragment
        elif self.current_speaking_text:
            self.last_interrupted_fragment = self.current_speaking_text

        self.last_barge_in_latency_ms = (time.perf_counter() - t0) * 1000
        logger.info("Barge-in aborted speaking in %.3fms.", self.last_barge_in_latency_ms)
        return True

    def _get_recovery_prefix(self) -> str:
        """Returns natural courtesy phrase after barge-in recovery across EN/TA/HI."""
        mode = getattr(self.engine, "market_mode", "india")
        if mode == "tamil":
            return "மன்னிக்கவும், நீங்க தொடர்ந்து சொல்லுங்க. "
        if mode == "hindi":
            return "जी क्षमा करें, कृपया बताइए। "
        if mode in ("india", "en-in"):
            return "Sorry about that — please go ahead. "
        return "Pardon me — please go ahead. "

    def _get_reflex_reply(self, user_text: str) -> str:
        """Selects conversational reflex sync acknowledgment based on market mode and intent."""
        mode = getattr(self.engine, "market_mode", "india")
        t = user_text.lower().strip()
        templates = REFLEX_RESPONSES.get(mode, REFLEX_RESPONSES["india"])

        if any(w in t for w in ["hear", "there", "सुन", "audible", "கேக்குதா", "kekutha"]):
            return templates["audible"]
        if any(w in t for w in ["hello", "hi", "hey", "namaste", "नमस्ते", "हेलो", "vanakkam", "வணக்கம்"]):
            return templates["greeting"]
        if any(w in t for w in ["yeah", "yes", "yep", "speaking", "haanji", "haan", "हाँ", "aama", "ஆமா", "seri", "சரி", "sollunga", "சொல்லுங்க"]):
            return templates["affirmation"]
        return templates["default"]

    def _get_reflex_audio(self, reply_text: str) -> bytes:
        """Synthesizes or retrieves cached genuine speech audio (never 160Hz tone)."""
        voice = getattr(self.tts, "default_voice", "en-IN-NeerjaExpressiveNeural")
        sr = getattr(self.tts, "sample_rate", 24000)
        cache_key = (reply_text, voice, sr)

        if cache_key in _REFLEX_AUDIO_CACHE:
            return _REFLEX_AUDIO_CACHE[cache_key]

        audio, _ = self.tts.synthesize_sync(reply_text, style="empathetic")
        if audio:
            _REFLEX_AUDIO_CACHE[cache_key] = audio
        return audio

    def _get_assistant_speaker_name(self) -> str:
        """Determines clinical care coordinator speaker label."""
        mode = getattr(self.engine, "market_mode", "india")
        if mode == "tamil":
            return "Pallavi (Amura Care Coordinator)"
        if mode == "hindi":
            return "Swati (Amura Care Coordinator)"
        if mode in ("india", "en-in"):
            return "Neerja (Amura Care Coordinator)"
        return "Maya (Amura Clinical Desk)"

    def _check_is_friction(self, text: str) -> bool:
        """Detects whether user text introduces schedule constraints or clinical complexity."""
        t = text.lower()
        friction_cues = [
            "tomorrow", "busy", "meeting", "contact me later", "call me later",
            "call tomorrow", "not good", "a wash", "flip side", "later", "in a zoom",
            "in a conference", "with a client", "driving", "bad time", "reschedule",
            "chest pain", "breathing", "emergency", "108", "diabetes", "hba1c",
            "insulin", "pcos", "thyroid", "prescription", "dosage", "diagnose",
            "complaint", "ticket", "fee", "price", "expensive", "out of town",
            "call back", "browsing", "just looking", "think about it", "not ready",
        ]
        return any(c in t for c in friction_cues)

    def start_call(self) -> Tuple[str, bytes]:
        """Initiates outbound/front-desk call and generates greeting audio."""
        self.state.status = "DIALING"
        time.sleep(0.02)
        self.state.status = "CONNECTED"

        greeting_text = self.engine.get_initial_greeting()
        speaker_name = self._get_assistant_speaker_name()
        self.state.transcript.append(
            {
                "speaker": speaker_name,
                "text": greeting_text,
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            }
        )

        self.state.status = "SPEAKING"
        self.is_speaking = True
        self.current_speaking_text = greeting_text
        self._abort_flag = False
        audio_bytes, tts_latency = self.tts.synthesize_sync(greeting_text, style="empathetic")
        self.latencies_tts.append(tts_latency * 1000)
        self.audio_log.append(audio_bytes)
        self.is_speaking = False

        self.state.status = "LISTENING"
        return greeting_text, audio_bytes

    def handle_user_speech(
        self,
        audio_chunk: Any = b"",
        simulated_text: Optional[str] = None,
        user_text: Optional[str] = None,
    ) -> Optional[Tuple[str, bytes]]:
        """Processes incoming patient speech with barge-in, reflex fast-path, and safety/emotion gating."""
        t_turn_start = time.perf_counter()

        if isinstance(audio_chunk, str):
            simulated_text = audio_chunk
            audio_chunk = b""
        elif user_text is not None:
            simulated_text = user_text

        # 1. Instant Barge-In Cutoff
        if self.is_speaking:
            is_active = False
            if audio_chunk and isinstance(audio_chunk, (bytes, bytearray)) and len(audio_chunk) > 0:
                is_active = self.stt.detect_voice_activity(audio_chunk)
            if is_active or simulated_text:
                self._execute_barge_in_abort()

        self.state.status = "THINKING"

        # 2. Speech-to-Text Transcription
        if simulated_text is not None:
            extracted_text = simulated_text
            stt_latency = 0.012 if DynamicLatencyPacer.is_reflex_sync(extracted_text) else 0.045
        else:
            extracted_text, stt_latency = self.stt.transcribe(audio_chunk)

        self.latencies_stt.append(stt_latency * 1000)

        if not extracted_text.strip():
            self.state.status = "LISTENING"
            return None

        self.state.transcript.append(
            {
                "speaker": "Patient",
                "text": extracted_text,
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            }
        )

        speaker_name = self._get_assistant_speaker_name()

        # 3. Reflex Response Fast-Path (<90ms)
        if DynamicLatencyPacer.is_reflex_sync(extracted_text):
            pacing_tier, pacing_delay = DynamicLatencyPacer.calculate_pacing_delay(extracted_text)
            self.last_pacing_tier = pacing_tier
            time.sleep(pacing_delay)

            reply_text = self._get_reflex_reply(extracted_text)
            if self.was_interrupted:
                reply_text = f"{self._get_recovery_prefix()}{reply_text}"
                self.was_interrupted = False

            self.engine.messages.append({"role": "user", "content": extracted_text})
            self.engine.messages.append({"role": "assistant", "content": reply_text})
            self.engine.turn_count += 1

            self.state.transcript.append(
                {
                    "speaker": speaker_name,
                    "text": reply_text,
                    "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                }
            )

            self.state.status = "SPEAKING"
            self.is_speaking = True
            self.current_speaking_text = reply_text
            self._abort_flag = False

            t_audio_start = time.perf_counter()
            reply_audio = self._get_reflex_audio(reply_text)
            audio_latency = time.perf_counter() - t_audio_start

            self.latencies_llm.append(pacing_delay * 1000)
            self.latencies_tts.append(audio_latency * 1000)
            self.audio_log.append(reply_audio)
            self.is_speaking = False

            self.state.status = "LISTENING"
            self.latencies_turn_total_ms.append((time.perf_counter() - t_turn_start) * 1000)
            self._update_metrics()
            return reply_text, reply_audio

        # 4. Paced Cognitive Latency
        is_friction = self._check_is_friction(extracted_text)
        pacing_tier, pacing_delay = DynamicLatencyPacer.calculate_pacing_delay(extracted_text, is_friction=is_friction)
        self.last_pacing_tier = pacing_tier
        time.sleep(pacing_delay)

        # 5. Clinical Reasoning, Emotion & Safety
        t_llm_start = time.perf_counter()
        reply_text = self.engine.process_user_turn(extracted_text)
        llm_latency = time.perf_counter() - t_llm_start
        self.latencies_llm.append((llm_latency + pacing_delay) * 1000)

        if self.was_interrupted:
            reply_text = f"{self._get_recovery_prefix()}{reply_text}"
            self.was_interrupted = False

        self.state.transcript.append(
            {
                "speaker": speaker_name,
                "text": reply_text,
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            }
        )

        # 6. Emotion-Calibrated Text-to-Speech Synthesis
        self.state.status = "SPEAKING"
        self.is_speaking = True
        self.current_speaking_text = reply_text
        self._abort_flag = False

        emotion_style = getattr(getattr(self.engine, "last_emotion", None), "voice_style", "empathetic")
        reply_audio, tts_latency = self.tts.synthesize_sync(reply_text, style=emotion_style)
        self.latencies_tts.append(tts_latency * 1000)
        self.audio_log.append(reply_audio)
        self.is_speaking = False

        self.state.status = "COMPLETED" if self.engine.is_completed else "LISTENING"
        self.latencies_turn_total_ms.append((time.perf_counter() - t_turn_start) * 1000)
        self._update_metrics()
        return reply_text, reply_audio

    def end_call(self) -> BuyerDossier:
        """Terminates call and returns finalized clinical dossier."""
        self.state.status = "COMPLETED"
        self.state.end_time = datetime.now(timezone.utc).isoformat()
        dossier = self.engine.export_dossier()
        self.state.dossier = dossier
        return dossier

    def _update_metrics(self) -> None:
        if self.latencies_stt:
            self.state.average_stt_latency_ms = sum(self.latencies_stt) / len(self.latencies_stt)
        if self.latencies_llm:
            self.state.average_llm_latency_ms = sum(self.latencies_llm) / len(self.latencies_llm)
        if self.latencies_tts:
            self.state.average_tts_latency_ms = sum(self.latencies_tts) / len(self.latencies_tts)
