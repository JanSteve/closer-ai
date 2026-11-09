"""CLOSER AI: Full-Duplex Live Voice Telephony Agent.

Architecture:
- Layer 1: Full-Duplex Audio & WebRTC Pipeline + Token Streaming Pipeline & Token-Level Streaming Synthesis.
- Layer 2: Real-time Barge-In + Silero VAD + Neural Noise Suppression + Instant Interruption.

Languages Supported:
- 1. English (Signature CLOSER AI Kokoro SOTA Blend — 100% Local, Offline)
- 2. Tamil (Sweet Tanglish Closer — Sarvam Bulbul Kavitha / Neural Pallavi)
- 3. Hindi (Sweet Hinglish Closer — Sarvam Bulbul Shreya / Neural Swati)

Run directly on your Mac:
    python3 live_voice_agent.py --agent tamil
    python3 live_voice_agent.py --agent hindi
    python3 live_voice_agent.py --agent english
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import tempfile
import time
from typing import AsyncGenerator, List, Optional

import numpy as np
import soundfile as sf

from closer.qualification.extractor import QualificationExtractor
from closer.telephony.audio_duplex import AudioDuplexManager
from closer.telephony.phonetic_normalizer import IndicPhoneticNormalizer
from closer.telephony.sarvam_engine import SarvamVoiceEngine
from closer.telephony.token_synthesizer import TokenStreamingSynthesizer
from closer.telephony.vad_barge_in import (
    AgentCallState,
    AudioNoiseSuppressor,
    BargeInController,
    SileroVADDetector,
)
from closer.voice_engine import NeuralVoiceEngine, VOICE_PROFILES


class LiveVoiceAgent:
    """Full-Duplex Interactive Telecaller Agent with Token Streaming and Barge-In."""

    def __init__(self, agent_name: str = "english"):
        self.agent_name = agent_name.lower()
        if self.agent_name not in VOICE_PROFILES:
            self.agent_name = "english"

        print(f"\n=======================================================")
        print(f"  🎙️  CLOSER AI: FULL-DUPLEX LIVE VOICE TELEPHONY AGENT")
        print(f"  Active Closer: {VOICE_PROFILES[self.agent_name]['label']}")
        print(f"  Layer 1: Full-Duplex Audio Transport + Token Streaming Synthesis")
        print(f"  Layer 2: Silero VAD + Neural Noise Suppression + Barge-In")
        print(f"=======================================================\n")

        # Core Engines
        self.voice_engine = NeuralVoiceEngine(default_agent=self.agent_name)
        self.sarvam = SarvamVoiceEngine()
        self.extractor = QualificationExtractor()
        self.suppressor = AudioNoiseSuppressor(sample_rate=16000)
        self.vad = SileroVADDetector(sample_rate=16000, threshold=0.50)
        self.synthesizer = TokenStreamingSynthesizer(self.voice_engine, agent_name=self.agent_name)

        # Barge-in Interruption Controller
        self.barge_in_controller = BargeInController(
            vad_detector=self.vad,
            noise_suppressor=self.suppressor,
            on_barge_in=self._handle_barge_in,
            consecutive_frames_required=2,
        )

        # Audio Stream Manager
        self.duplex = AudioDuplexManager(
            sample_rate=16000,
            frame_duration_ms=32,
            on_mic_frame=self._on_mic_audio_frame,
        )

        # Buffers & Event Loop Coordination
        self.loop = asyncio.get_event_loop()
        self.speech_buffer: List[np.ndarray] = []
        self.silence_frame_count = 0
        self.is_user_speaking = False
        self.temp_dir = tempfile.mkdtemp(prefix="closer_live_")
        self.active_playback_task: Optional[asyncio.Task] = None

    def _handle_barge_in(self) -> None:
        """Triggered within <64ms when user speaks over the AI."""
        print("\n⚡ [BARGE-IN TRIGGERED] User interrupted AI speech! Halting playback instantly...")
        self.duplex.interrupt_playback()
        self.synthesizer.interrupt()
        if self.active_playback_task and not self.active_playback_task.done():
            self.active_playback_task.cancel()
        self.barge_in_controller.set_state(AgentCallState.USER_SPEAKING)

    def _on_mic_audio_frame(self, frame: np.ndarray) -> None:
        """Processes real-time 32ms microphone frame."""
        # Process frame through Layer 2 pipeline (Noise Filter -> Silero VAD -> Barge-In check)
        is_speech, prob, barge_triggered = self.barge_in_controller.process_incoming_frame(frame)

        if is_speech:
            self.speech_buffer.append(frame)
            self.silence_frame_count = 0
            if not self.is_user_speaking:
                self.is_user_speaking = True
                self.barge_in_controller.set_state(AgentCallState.USER_SPEAKING)
                print(f"🗣️  [Listening...] (Speech detected: conf={prob:.2f})")
        else:
            if self.is_user_speaking:
                self.speech_buffer.append(frame)
                self.silence_frame_count += 1
                
                # ~500ms of silence after speech signals end of user turn
                if self.silence_frame_count >= 16:  # 16 frames * 32ms ~= 512ms
                    self.is_user_speaking = False
                    user_audio = np.concatenate(self.speech_buffer)
                    self.speech_buffer.clear()
                    self.silence_frame_count = 0
                    
                    # Schedule turn processing
                    if len(user_audio) > 16000 * 0.4:  # At least 400ms of audio
                        asyncio.run_coroutine_threadsafe(self._process_user_turn(user_audio), self.loop)

    async def _process_user_turn(self, audio_data: np.ndarray) -> None:
        """Runs STT, Qualification, and Token-Streaming Synthesis."""
        self.barge_in_controller.set_state(AgentCallState.AGENT_THINKING)
        
        # 1. Save user audio to temp wav
        wav_path = os.path.join(self.temp_dir, f"user_utterance_{int(time.time()*1000)}.wav")
        sf.write(wav_path, audio_data, 16000)

        # 2. Speech-to-Text Transcription via Sarvam Saaras
        lang_code = "ta-IN" if "tam" in self.agent_name else ("hi-IN" if "hin" in self.agent_name else "en-US")
        transcript = await self.sarvam.transcribe(wav_path, language_code=lang_code)
        
        if not transcript:
            # Fallback prompt if background noise or empty
            print("⚠️  [Audio] No clear speech detected.")
            self.barge_in_controller.set_state(AgentCallState.IDLE)
            return

        print(f"\n👤 [You (Customer)]: \"{transcript}\"")

        # 3. Decision Logic & Token Streaming
        response_tokens = self._generate_response_stream(transcript)
        
        # 4. Layer 1: Token Streaming Synthesis
        self.barge_in_controller.set_state(AgentCallState.AGENT_SPEAKING)
        self.active_playback_task = asyncio.create_task(self._stream_and_play(response_tokens))

    async def _stream_and_play(self, token_stream: AsyncGenerator[str, None]) -> None:
        """Streams tokens directly into streaming synthesis and audio duplex playback."""
        start_time = time.time()
        first_audio_logged = False
        
        async for audio_chunk_path in self.synthesizer.stream_and_synthesize(token_stream):
            if not first_audio_logged:
                ttfa_ms = int((time.time() - start_time) * 1000)
                print(f"🚀 [Layer 1] Time-to-First-Audio (TTFA): {ttfa_ms}ms")
                first_audio_logged = True
                
            # Enqueue audio chunk to non-blocking speaker playback
            self.duplex.enqueue_audio_file(audio_chunk_path)

        # Wait until playback completes (unless interrupted)
        while self.duplex.is_playing:
            await asyncio.sleep(0.05)
            
        self.barge_in_controller.set_state(AgentCallState.IDLE)
        print("\n🤖 [CLOSER AI finished turn. Listening for your response...]")

    async def _generate_response_stream(self, customer_utterance: str) -> AsyncGenerator[str, None]:
        """Simulates LLM token streaming with sales closing guardrails."""
        lower = customer_utterance.lower()

        # Check for price deflection
        is_price_query = any(k in lower for k in [
            "discount", "price", "rate", "cost", "offer", "lowest", "how much", "bargain",
            "डिस्काउंट", "रेट", "कीमत", "कम", "ऑफर", "सस्ता", "छूट",
            "விலை", "தள்ளுபடி", "கம்மி", "டிஸ்கவுண்ட்", "ரேட்", "ஆஃபர்", "குறைக்க", "பர்சன்ட்"
        ])

        if is_price_query:
            if "tam" in self.agent_name:
                text = "Sir, pricing மற்றும் special discount பத்தி நம்ம நேரடியா site visit வரும்போது பேசிக்கலாமுங்க. இந்த வியாழக்கிழமை சாயங்காலம் 4 மணிக்கு பார்க்கலாமா, இல்ல சனிக்கிழமை காலைல பார்க்கலாமா Sir?"
            elif "hin" in self.agent_name:
                text = "हाँजी बिल्कुल! डिस्काउंट और final pricing के बारे में हम site visit पर बैठकर आराम से बात कर सकते हैं जी। क्या गुरुवार शाम 4 बजे या शनिवार सुबह का समय सही रहेगा सर?"
            else:
                text = "Look, I totally get where you are coming from on the pricing. The developer authorizes custom payment milestones during the private walkthrough. Would Thursday at 4 PM or Saturday morning work better for you?"
        else:
            dossier = self.extractor.extract(customer_utterance)
            if dossier.budget_bracket:
                if "tam" in self.agent_name:
                    text = "கண்டிப்பா Sir! உங்க budget-க்கு ஏத்த மாதிரி OMR-ல ரொம்பவே அழகான 3 BHK luxury projects இருக்குங்க. இந்த weekend நேர்ல வந்து site visit பார்க்கலாமா Sir?"
                elif "hin" in self.agent_name:
                    text = "जी बिल्कुल सर! अगर आपका budget डेढ़ करोड़ के आस-पास है, तो हमारे पास बहुत ही शानदार 3 BHK luxury options हैं। क्या इस weekend एक बार site visit plan करें?"
                else:
                    text = "Got it! That fits our luxury inventory perfectly. Would you like to schedule a private walkthrough this weekend?"
            else:
                if "tam" in self.agent_name:
                    text = "வணக்கம் Sir! நீங்க ஃபேமிலியோட stay பண்ண 3 BHK பாக்குறீங்களா, இல்ல investment-க்காக பாக்குறீங்களா Sir?"
                elif "hin" in self.agent_name:
                    text = "नमस्ते सर! आप अपने परिवार के साथ रहने के लिए 3 BHK फ्लैट देख रहे हैं या फिर investment के लिए?"
                else:
                    text = "Hey, good morning! Thanks for checking out our residences. Quick question — are you looking for a two-bedroom or a three-bedroom layout for your family?"

        # Stream words as tokens with micro-delays (simulating streaming LLM)
        words = text.split(" ")
        for w in words:
            yield w + " "
            await asyncio.sleep(0.02)  # 20ms token pace

    async def run(self) -> None:
        """Starts live full-duplex session."""
        self.duplex.start()
        print("🟢 Live Full-Duplex Session Active! Start speaking into your microphone...")
        print("💡 TIP: While CLOSER AI is speaking, speak over it to test Instant Barge-In (<64ms)!\n")

        # Initial opening greeting
        await asyncio.sleep(1.0)
        initial_greeting = self._generate_response_stream("hello")
        self.barge_in_controller.set_state(AgentCallState.AGENT_SPEAKING)
        self.active_playback_task = asyncio.create_task(self._stream_and_play(initial_greeting))

        try:
            while True:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            self.duplex.stop()


def main():
    parser = argparse.ArgumentParser(description="CLOSER AI Full-Duplex Voice Telephony Agent")
    parser.add_argument("--agent", choices=["english", "tamil", "hindi"], default="tamil", help="Select telecaller voice")
    args = parser.parse_args()

    agent = LiveVoiceAgent(agent_name=args.agent)
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\n🛑 Telephony session ended.")
        agent.duplex.stop()


if __name__ == "__main__":
    main()
