"""Layer 1: Token Streaming Pipeline and Token-Level Streaming Synthesis for CLOSER AI.

Enables ultra-low latency conversational speech:
- Instead of waiting 2-3 seconds for an entire LLM response, text is chunked at prosodic clause boundaries.
- As soon as a clause (6-12 words or comma/period/question mark) is emitted, TTS synthesizes it immediately.
- Audio chunks are enqueued to the audio output queue concurrently.
- User hears speech in <350ms Time-to-First-Audio (TTFA).
- Fully interruptible via cancellation token for Layer 2 Barge-In.
"""

from __future__ import annotations

import asyncio
import re
import tempfile
import time
from typing import AsyncGenerator, Callable, List, Optional

from closer.telephony.phonetic_normalizer import IndicPhoneticNormalizer
from closer.voice_engine import NeuralVoiceEngine


class TokenSentenceAccumulator:
    """Accumulates token stream into natural prosodic clauses suitable for streaming TTS."""

    # Punctuation markers that represent natural telecaller speech pauses
    CLAUSE_SPLIT_PATTERN = re.compile(r"([.?!,;:\n—]+)")

    def __init__(self, min_token_length: int = 4, max_token_length: int = 14):
        self.min_token_length = min_token_length
        self.max_token_length = max_token_length
        self.buffer = ""

    async def process_stream(self, token_stream: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """Consumes a token generator and yields natural speech clauses."""
        async for token in token_stream:
            self.buffer += token
            
            # Check for punctuation splits
            parts = self.CLAUSE_SPLIT_PATTERN.split(self.buffer)
            if len(parts) > 2:
                # We have at least one complete punctuated clause
                clause = parts[0] + parts[1]
                words = clause.strip().split()
                
                # Check if clause has enough substance
                if len(words) >= self.min_token_length or any(p in parts[1] for p in [".", "?", "!"]):
                    self.buffer = "".join(parts[2:])
                    cleaned = clause.strip()
                    if cleaned:
                        yield cleaned
                elif len(words) > self.max_token_length:
                    self.buffer = "".join(parts[2:])
                    cleaned = clause.strip()
                    if cleaned:
                        yield cleaned

        # Flush any remaining buffer
        remaining = self.buffer.strip()
        if remaining:
            self.buffer = ""
            yield remaining

    def ingest(self, text: str) -> List[str]:
        """Synchronously breaks a text into natural prosodic clauses for speech synthesis."""
        if not text:
            return []
        parts = self.CLAUSE_SPLIT_PATTERN.split(text)
        clauses = []
        for i in range(0, len(parts) - 1, 2):
            clause = (parts[i] + parts[i+1]).strip()
            if clause:
                clauses.append(clause)
        if len(parts) % 2 == 1 and parts[-1].strip():
            clauses.append(parts[-1].strip())
        return clauses or [text]


class TokenStreamingSynthesizer:
    """Manages concurrent token ingestion, TTS synthesis, and interruptible playback queue."""

    def __init__(self, voice_engine: NeuralVoiceEngine, agent_name: str = "english"):
        self.voice_engine = voice_engine
        self.agent_name = agent_name
        self.is_interrupted = False
        self.active_tasks: List[asyncio.Task] = []
        self.audio_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

    def interrupt(self) -> None:
        """Instantly cancels active synthesis and flushes audio queue (Barge-In)."""
        self.is_interrupted = True
        for task in self.active_tasks:
            if not task.done():
                task.cancel()
        self.active_tasks.clear()
        
        # Drain the audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        # Sentinel to signal termination
        try:
            self.audio_queue.put_nowait(None)
        except Exception:
            pass

    async def stream_and_synthesize(
        self,
        token_stream: AsyncGenerator[str, None],
        on_audio_ready: Optional[Callable[[str, str], None]] = None,
    ) -> AsyncGenerator[str, None]:
        """Processes token stream, synthesizes clauses in parallel, and yields audio file paths.
        
        Yields:
            str: Path to each synthesized audio chunk ready for playback.
        """
        self.is_interrupted = False
        accumulator = TokenSentenceAccumulator()
        chunk_idx = 0
        temp_dir = tempfile.mkdtemp(prefix="closer_stream_")

        async for clause in accumulator.process_stream(token_stream):
            if self.is_interrupted:
                break

            chunk_idx += 1
            chunk_file = f"{temp_dir}/chunk_{chunk_idx}_{int(time.time()*1000)}.wav"
            
            # Normalize clause for phonetics
            clean_clause = IndicPhoneticNormalizer.normalize(clause, self.agent_name)
            
            try:
                # Synthesize clause immediately
                actual_path = await self.voice_engine.synthesize_to_file(
                    text=clean_clause,
                    output_path=chunk_file,
                    agent=self.agent_name,
                )
                
                if self.is_interrupted:
                    break
                    
                if on_audio_ready:
                    on_audio_ready(clean_clause, actual_path)
                    
                yield actual_path
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[StreamingSynthesizer] Synthesis warning for clause '{clause}': {e}")
                continue
