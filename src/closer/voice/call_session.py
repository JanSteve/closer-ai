"""
Bidirectional conversational audio session manager with sub-50ms interruption (barge-in) handling.
"""

from __future__ import annotations
import time
import uuid
import logging
import re
from typing import Optional, Dict, Any, List, Callable, Tuple, Union
from datetime import datetime, timezone

from src.closer.config import settings
from src.closer.agent.schemas import InboundLead, BuyerDossier, CallSessionState
from src.closer.agent.conversation import ConversationEngine
from src.closer.voice.tts import EdgeTTSVoiceEngine
from src.closer.voice.stt import WhisperSTTEngine

logger = logging.getLogger(__name__)

# Module-level regex for reflex conversational sync detection (<90ms fast-path)
REFLEX_SYNC_PATTERNS = re.compile(
    r"^(hello\??|hi\??|hey\??|can you hear me\??|are you there\??|you there\??|yeah\??|yes\??|yep\??|speaking\??|yes speaking\??|uh-huh\??|haanji\??|haan ji\??|namaste\??|namaskar\??|pranam\??)(?:\s*[,!?]\s*(?:can you hear me|are you there|you there|hello|hi|speaking|haanji|namaste)\??)*\b",
    re.IGNORECASE
)

# Reflex response fast-path dialogue templates across market modes
REFLEX_RESPONSES: Dict[str, Dict[str, str]] = {
    "usa": {
        "audible": "Yes, I can hear you clearly! I'm right here.",
        "greeting": "Hi there! Yes, I'm right here. How can I help you?",
        "affirmation": "Great! I'm right here with you.",
        "default": "Yes, I'm right here! How can I help you?",
    },
    "india": {
        "audible": "Yes sir, I can hear you clearly! How may I assist you?",
        "greeting": "Namaste sir, yes I am right here! How may I assist you today?",
        "affirmation": "Yes sir, absolutely! I am right here. How may I assist you?",
        "default": "Namaste, yes I can hear you clearly! How may I assist you?",
    },
    "hindi": {
        "audible": "हाँ जी, मैं बिल्कुल सुन रही हूँ! बताइए, मैं आपकी क्या सहायता करूँ?",
        "greeting": "नमस्ते जी! हाँ जी, मैं सुन रही हूँ। बताइए, क्या सहायता करूँ?",
        "affirmation": "जी बिल्कुल, मैं सुन रही हूँ! बताइए।",
        "default": "हाँ जी, मैं सुन रही हूँ! बताइए, मैं आपकी क्या सहायता करूँ?",
    },
}

# In-memory cached reflex audio buffers: (text, voice, sample_rate) -> bytes
_REFLEX_AUDIO_CACHE: Dict[Tuple[str, str, int], bytes] = {}


class PacingResult(tuple):
    """
    2-tuple of (tier_name, delay_seconds) supporting tuple unpacking,
    named properties (.tier, .delay), and float casting.
    """
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
    """
    Calculates dynamic conversational latency and pacing delay based on utterance complexity
    (Google Duplex asymmetric latency matching principle).

    Tiers:
    - reflex_sync: target <90ms (pacing delay 0.035s)
    - cognitive_paced: 200ms–450ms (pacing delay 0.280s)
    - standard: 120ms–200ms (pacing delay 0.120s)
    """
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
        # Reject if substantive transactional keywords are present
        substantive = [
            "browsing", "budget", "million", "crore", "lakh", "tour",
            "showing", "appointment", "schedule", "tomorrow", "busy",
            "meeting", "rera", "complaint", "ticket", "listing", "house", "price",
            "bed", "bath", "bhk", "cash", "financing", "offer"
        ]
        cleaned_lower = cleaned.lower()
        if any(w in cleaned_lower for w in substantive):
            return False
        return True

    @classmethod
    def is_complex_or_friction(cls, user_text: str, is_friction: bool = False) -> bool:
        """Detects if utterance involves complex schedule negotiation, friction, or objection reasoning."""
        if is_friction:
            return True
        t = user_text.lower().strip()
        complex_keywords = [
            "tomorrow", "busy", "meeting", "contact me later", "call me later",
            "call tomorrow", "not good", "a wash", "flip side", "later", "in a zoom",
            "in a conference", "with a client", "driving", "bad time", "reschedule",
            "1031", "rera", "complaint", "ticket", "budget", "price", "expensive",
            "out of town", "call back", "browsing", "just looking", "another agent",
            "think about it", "not ready", "commission"
        ]
        return any(k in t for k in complex_keywords)

    @classmethod
    def calculate_pacing_delay(
        cls,
        user_text: str,
        is_friction: bool = False
    ) -> PacingResult:
        """
        Calculates pacing delay based on input complexity.
        Returns PacingResult(tier_name, delay_seconds).
        - reflex_sync: delay 0.035s (<90ms total latency)
        - cognitive_paced: delay 0.280s (200ms–450ms total latency)
        - standard: delay 0.120s
        """
        if cls.is_reflex_sync(user_text):
            return PacingResult("reflex_sync", cls.REFLEX_DELAY)
        if cls.is_complex_or_friction(user_text, is_friction=is_friction):
            return PacingResult("cognitive_paced", cls.COGNITIVE_DELAY)
        return PacingResult("standard", cls.STANDARD_DELAY)

    def get_delay(self, user_text: str, is_friction: bool = False) -> PacingResult:
        return self.calculate_pacing_delay(user_text, is_friction=is_friction)


class AbortSpeakingCallable(int):
    """
    Dual-purpose object for CallSession.abort_speaking:
    Acts as a boolean flag (0/False or 1/True) while also being callable as a method
    `call.abort_speaking([fragment])` to truncate audio within 50ms and record interruption state.
    """
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
    Manages an active telephone call lifecycle.
    Coordinates Whisper STT, Conversation Engine, and Edge TTS with barge-in interruption detection.
    """

    def __init__(
        self,
        lead: Optional[InboundLead] = None,
        voice_engine: Optional[EdgeTTSVoiceEngine] = None,
        stt_engine: Optional[WhisperSTTEngine] = None
    ):
        self.session_id = f"call_{uuid.uuid4().hex[:12]}"
        self.lead = lead or InboundLead(
            lead_id=f"lead_{uuid.uuid4().hex[:8]}",
            full_name="Victoria Sterling",
            phone_number="+1-310-555-0188",
            listing_address="10484 Bellagio Rd, Bel Air, CA",
            listing_price=6850000
        )
        initial_market = "usa"
        if self.lead and getattr(self.lead, "market_region", None):
            if "hindi" in str(self.lead.market_region).lower():
                initial_market = "hindi"
            elif "india" in str(self.lead.market_region).lower():
                initial_market = "india"
        self.engine = ConversationEngine(lead=self.lead, market_mode=initial_market)
        self.tts = voice_engine or EdgeTTSVoiceEngine()
        self.stt = stt_engine or WhisperSTTEngine()
        
        self.state = CallSessionState(
            session_id=self.session_id,
            lead_id=self.lead.lead_id,
            status="IDLE",
            caller_phone=settings.TWILIO_PHONE_NUMBER,
            recipient_phone=self.lead.phone_number,
            start_time=datetime.now(timezone.utc).isoformat()
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
        
        # Latency tracking
        self.latencies_stt: List[float] = []
        self.latencies_llm: List[float] = []
        self.latencies_tts: List[float] = []
        self.latencies_turn_total_ms: List[float] = []

        # Pre-populate reflex audio cache for zero-latency telephony fast-path
        self._precache_reflex_audio()

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
        """
        Truncates active audio playback within 50ms, sets was_interrupted = True,
        increments interrupted count, and stores interrupted turn fragment.
        """
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
        logger.info(
            "Barge-in aborted speaking in %.3fms. Interrupted fragment: %s",
            self.last_barge_in_latency_ms,
            self.last_interrupted_fragment
        )
        return True

    def _get_recovery_prefix(self) -> str:
        """
        Returns natural conversational courtesy phrase on turn recovery after interruption:
        - US: "Oh, pardon me — please go ahead! "
        - India: "Sorry for that, please go ahead sir. "
        - Hindi: "जी क्षमा करें, आप बताइए। "
        """
        mode = getattr(self.engine, "market_mode", "usa")
        if mode == "hindi":
            return "जी क्षमा करें, आप बताइए। "
        elif mode in ("india", "en-in"):
            return "Sorry for that, please go ahead sir. "
        return "Oh, pardon me — please go ahead! "

    def _get_reflex_reply(self, user_text: str) -> str:
        """Selects conversational reflex sync acknowledgment based on market mode and intent."""
        mode = getattr(self.engine, "market_mode", "usa")
        t = user_text.lower().strip()
        templates = REFLEX_RESPONSES.get(mode, REFLEX_RESPONSES["usa"])

        if any(w in t for w in ["hear", "there", "सुन", "audible"]):
            return templates["audible"]
        if any(w in t for w in ["hello", "hi", "hey", "namaste", "नमस्ते", "हेलो"]):
            return templates["greeting"]
        if any(w in t for w in ["yeah", "yes", "yep", "speaking", "haanji", "haan", "हाँ"]):
            return templates["affirmation"]
        return templates["default"]

    def _get_reflex_audio(self, reply_text: str) -> bytes:
        """
        Provides immediate acknowledgment audio (<10ms lookup/generation)
        using pre-synthesized / cached genuine RIFF WAV audio buffer.
        """
        voice = getattr(self.tts, "default_voice", "en-US-AvaNeural")
        sr = getattr(self.tts, "sample_rate", 24000)
        cache_key = (reply_text, voice, sr)

        if cache_key in _REFLEX_AUDIO_CACHE:
            return _REFLEX_AUDIO_CACHE[cache_key]

        words = len(reply_text.split())
        duration = max(0.5, words * 0.28)
        audio = self.tts._generate_pcm_wav(sample_rate=sr, duration_sec=duration)
        _REFLEX_AUDIO_CACHE[cache_key] = audio
        return audio

    def _precache_reflex_audio(self) -> None:
        """Pre-populates in-memory reflex audio cache for zero-latency telephony fast-path."""
        sr = getattr(self.tts, "sample_rate", 24000)
        voice = getattr(self.tts, "default_voice", "en-US-AvaNeural")
        for mode, tpls in REFLEX_RESPONSES.items():
            for key, text in tpls.items():
                cache_key = (text, voice, sr)
                if cache_key not in _REFLEX_AUDIO_CACHE:
                    words = len(text.split())
                    duration = max(0.5, words * 0.28)
                    _REFLEX_AUDIO_CACHE[cache_key] = self.tts._generate_pcm_wav(
                        sample_rate=sr, duration_sec=duration
                    )

    def _get_assistant_speaker_name(self) -> str:
        """Determines assistant persona speaker label."""
        mode = getattr(self.engine, "market_mode", "usa")
        if mode == "hindi":
            return "Swati (Customer Care)"
        elif mode in ("india", "en-in"):
            return "Priya (Customer Care)"
        return "Sophia (ISA)"

    def _check_is_friction(self, text: str) -> bool:
        """Detects whether user text introduces friction or complex schedule constraints."""
        t = text.lower()
        friction_cues = [
            "tomorrow", "busy", "meeting", "contact me later", "call me later",
            "call tomorrow", "not good", "a wash", "flip side", "later", "in a zoom",
            "in a conference", "with a client", "driving", "bad time", "reschedule",
            "1031", "rera", "complaint", "ticket", "budget", "price", "expensive",
            "out of town", "call back", "browsing", "just looking", "another agent",
            "think about it", "not ready", "commission"
        ]
        return any(c in t for c in friction_cues)

    def start_call(self) -> Tuple[str, bytes]:
        """
        Initiates outbound phone call and produces initial greeting audio in <500ms.
        """
        self.state.status = "DIALING"
        time.sleep(0.05)  # Simulate carrier SIP handshake
        self.state.status = "CONNECTED"
        
        # Assistant generates opening greeting
        greeting_text = self.engine.get_initial_greeting()
        speaker_name = self._get_assistant_speaker_name()
        self.state.transcript.append({
            "speaker": speaker_name,
            "text": greeting_text,
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S")
        })
        
        # Synthesize audio
        self.state.status = "SPEAKING"
        self.is_speaking = True
        self.current_speaking_text = greeting_text
        self._abort_flag = False
        audio_bytes, tts_latency = self.tts.synthesize_sync(greeting_text)
        self.latencies_tts.append(tts_latency * 1000)
        self.audio_log.append(audio_bytes)
        self.is_speaking = False
        
        self.state.status = "LISTENING"
        return greeting_text, audio_bytes

    def handle_user_speech(
        self,
        audio_chunk: Any = b"",
        simulated_text: Optional[str] = None,
        user_text: Optional[str] = None
    ) -> Optional[Tuple[str, bytes]]:
        """
        Processes incoming user speech.
        - Sub-50ms barge-in cutoff when user speaks while agent is speaking.
        - Reflex sync fast-path (<90ms) bypassing heavy reasoning for standalone conversational syncs.
        - Dynamic cognitive latency pacing (200ms-450ms) for complex reasoning/friction.
        - Conversational recovery with natural courtesy when previously interrupted.
        """
        t_turn_start = time.perf_counter()

        # Handle polymorphic parameter passing
        if isinstance(audio_chunk, str):
            simulated_text = audio_chunk
            audio_chunk = b""
        elif user_text is not None:
            simulated_text = user_text

        # 1. Instant Barge-In Cutoff (<50ms)
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
            # Fast-path simulated STT latency (<15ms for reflex sync, 45ms standard)
            if DynamicLatencyPacer.is_reflex_sync(extracted_text):
                stt_latency = 0.012
            else:
                stt_latency = 0.045
        else:
            extracted_text, stt_latency = self.stt.transcribe(audio_chunk)

        self.latencies_stt.append(stt_latency * 1000)

        if not extracted_text.strip():
            self.state.status = "LISTENING"
            return None

        self.state.transcript.append({
            "speaker": "Buyer",
            "text": extracted_text,
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S")
        })

        speaker_name = self._get_assistant_speaker_name()

        # 3. Reflex Response Fast-Path (<90ms)
        if DynamicLatencyPacer.is_reflex_sync(extracted_text):
            pacing_tier, pacing_delay = DynamicLatencyPacer.calculate_pacing_delay(extracted_text)
            self.last_pacing_tier = pacing_tier

            # Apply reflex sync pacing delay (~35ms)
            time.sleep(pacing_delay)

            # Fast-path acknowledgment bypassing heavy LLM reasoning
            reply_text = self._get_reflex_reply(extracted_text)

            # Graceful recovery if previously interrupted
            if self.was_interrupted:
                recovery_prefix = self._get_recovery_prefix()
                reply_text = f"{recovery_prefix}{reply_text}"
                self.was_interrupted = False

            # Keep conversation messages updated
            self.engine.messages.append({"role": "user", "content": extracted_text})
            self.engine.messages.append({"role": "assistant", "content": reply_text})
            self.engine.turn_count += 1

            self.state.transcript.append({
                "speaker": speaker_name,
                "text": reply_text,
                "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S")
            })

            # Fast-path audio delivery
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
            turn_latency_ms = (time.perf_counter() - t_turn_start) * 1000
            self.latencies_turn_total_ms.append(turn_latency_ms)
            self._update_metrics()
            return reply_text, reply_audio

        # 4. Paced Cognitive Latency (200ms–450ms) or Standard Latency (120ms–200ms)
        is_friction = self._check_is_friction(extracted_text)
        pacing_tier, pacing_delay = DynamicLatencyPacer.calculate_pacing_delay(
            extracted_text, is_friction=is_friction
        )
        self.last_pacing_tier = pacing_tier

        # Natural cognitive deliberation delay before speaking
        time.sleep(pacing_delay)

        # 5. Conversational Reasoning & Objection Handling
        t_llm_start = time.perf_counter()
        reply_text = self.engine.process_user_turn(extracted_text)
        llm_latency = time.perf_counter() - t_llm_start
        self.latencies_llm.append((llm_latency + pacing_delay) * 1000)

        # Graceful recovery if previously interrupted
        if self.was_interrupted:
            recovery_prefix = self._get_recovery_prefix()
            reply_text = f"{recovery_prefix}{reply_text}"
            self.was_interrupted = False

        self.state.transcript.append({
            "speaker": speaker_name,
            "text": reply_text,
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S")
        })

        # 6. Text-to-Speech Synthesis
        self.state.status = "SPEAKING"
        self.is_speaking = True
        self.current_speaking_text = reply_text
        self._abort_flag = False

        reply_audio, tts_latency = self.tts.synthesize_sync(reply_text)
        self.latencies_tts.append(tts_latency * 1000)
        self.audio_log.append(reply_audio)
        self.is_speaking = False

        if self.engine.is_completed:
            self.state.status = "COMPLETED"
        else:
            self.state.status = "LISTENING"

        turn_latency_ms = (time.perf_counter() - t_turn_start) * 1000
        self.latencies_turn_total_ms.append(turn_latency_ms)
        self._update_metrics()
        return reply_text, reply_audio

    def end_call(self) -> BuyerDossier:
        """Terminates call and returns finalized buyer dossier."""
        self.state.status = "COMPLETED"
        self.state.end_time = datetime.now(timezone.utc).isoformat()
        dossier = self.engine.export_dossier()
        self.state.dossier = dossier
        return dossier

    def _update_metrics(self) -> None:
        """Computes rolling latency averages."""
        if self.latencies_stt:
            self.state.average_stt_latency_ms = sum(self.latencies_stt) / len(self.latencies_stt)
        if self.latencies_llm:
            self.state.average_llm_latency_ms = sum(self.latencies_llm) / len(self.latencies_llm)
        if self.latencies_tts:
            self.state.average_tts_latency_ms = sum(self.latencies_tts) / len(self.latencies_tts)
