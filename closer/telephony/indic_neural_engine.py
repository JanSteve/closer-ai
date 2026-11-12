"""Unified Open-Source Indic Human-Voice Engine for Hindi & Tamil Telecalling.

Integrates verified top GitHub open-source TTS architectures with clean tiered routing
so CLOSER AI works both on GPU/Apple-Silicon servers (human-grade cloning & expressive prompts)
and zero-GPU serverless deployments (Sarvam Bulbul v3 + Dialect Breath-Paced Neural TTS):

1. ai4bharat/IndicF5            — Zero-shot flow-matching polyglot TTS (1,417h Rasa/IndicVoices-R;
                                  inherits regional dialects, breathing & cadence from reference wav)
2. ai4bharat/indic-parler-tts   — Expressive text-description conditioned TTS across 20+ Indic langs
3. fishaudio/fish-speech        — DualAR LLaMA + VQ-GAN server API (/v1/tts) with pause tags &
                                  cross-lingual cloning (also generates fake customer audio in MiroFish)
4. chatterbox-indic-lora        — Rank-32 LoRA + expanded tokenizer on resemble-ai/chatterbox
                                  for Hindi & Tamil with emotion exaggeration controls
5. SachinTelecmi/Orpheus-tts-hi — Llama-3B SNAC Hinglish telephony model (documented registry)
6. Sarvam AI bulbul:v3          — Low-latency commercial Indian telephony cloud API
7. Dialect Breath-Paced EdgeTTS — Serverless zero-GPU fallback with Chennai Tanglish / Delhi Hinglish
                                  spoken rewrites, micro-pauses, and comfort-noise breath gaps.
"""

from __future__ import annotations

import asyncio
import importlib.util
import io
import os
import tempfile
import time
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np
import soundfile as sf

from closer.telephony.dialect_prosody import IndicDialectProsodyEngine
from closer.telephony.sarvam_engine import SARVAM_FEMALE_VOICES, SarvamVoiceEngine


INDIC_GITHUB_VOICE_REPOS: Dict[str, Dict[str, Any]] = {
    "indicf5": {
        "repo": "ai4bharat/IndicF5",
        "url": "https://github.com/AI4Bharat/IndicF5",
        "hf_model": "ai4bharat/IndicF5",
        "languages": ["tamil", "hindi", "indian_english"],
        "strength": "Zero-shot 24kHz voice cloning preserving natural dialect, pauses & breathiness.",
        "hardware": "GPU / Apple Silicon MPS recommended (~4GB+ VRAM)",
    },
    "indic_parler": {
        "repo": "ai4bharat/indic-parler-tts",
        "url": "https://github.com/AI4Bharat/indic-parler-tts",
        "hf_model": "ai4bharat/indic-parler-tts",
        "languages": ["tamil", "hindi", "indian_english"],
        "strength": "Natural-language style prompting for mood, speaking rate, pauses & studio acoustics.",
        "hardware": "GPU / Apple Silicon MPS recommended (~4GB+ VRAM)",
    },
    "fish_speech": {
        "repo": "fishaudio/fish-speech",
        "url": "https://github.com/fishaudio/fish-speech",
        "api_endpoint": "/v1/tts",
        "languages": ["hindi", "tamil", "english"],
        "strength": "VQ-GAN + DualAR LLaMA voice cloning with pause tags; ideal for AI & fake-customer voices.",
        "hardware": "Local or remote Fish-Speech inference server (CUDA / MPS)",
    },
    "chatterbox_indic": {
        "repo": "reenigne314/chatterbox-indic-lora",
        "url": "https://github.com/reenigne314/chatterbox-indic-lora",
        "base_repo": "resemble-ai/chatterbox",
        "languages": ["hindi", "tamil"],
        "strength": "Rank-32 LoRA & Indic tokenizer over Chatterbox with emotion exaggeration control.",
        "hardware": "GPU (>=6GB VRAM)",
    },
    "orpheus_hi": {
        "repo": "SachinTelecmi/Orpheus-tts-hi",
        "url": "https://github.com/canopyai/Orpheus-TTS",
        "hf_model": "SachinTelecmi/Orpheus-tts-hi",
        "languages": ["hindi"],
        "strength": "Llama-3B SNAC codec specialized for conversational Hindi & Hinglish code-mixing.",
        "hardware": "GPU (>=8GB VRAM)",
    },
}


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _generate_comfort_silence(duration_seconds: float, sample_rate: int = 24000) -> np.ndarray:
    """Generates subtle room-tone comfort noise (-58 dB) rather than dead digital zero."""
    num_samples = max(1, int(duration_seconds * sample_rate))
    rng = np.random.default_rng(42)
    return (rng.normal(0.0, 0.0008, size=num_samples)).astype(np.float32)


class IndicNeuralVoiceEngine:
    """Routes Hindi & Tamil synthesis through GitHub neural engines with human dialect prosody."""

    DEFAULT_REF_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "models" / "prompts"

    _sarvam_cooldown_until: float = 0.0

    def __init__(
        self,
        fish_speech_url: Optional[str] = None,
        sarvam_engine: Optional[SarvamVoiceEngine] = None,
        prompts_dir: Optional[Path] = None,
    ):
        self.fish_speech_url = (
            fish_speech_url or os.getenv("FISH_SPEECH_URL", "http://127.0.0.1:8080")
        ).rstrip("/")
        self.sarvam = sarvam_engine or SarvamVoiceEngine()
        self.prompts_dir = prompts_dir or self.DEFAULT_REF_PROMPTS_DIR
        self._indicf5_model: Any = None
        self._parler_model: Any = None
        self._parler_tokenizer: Any = None
        self._parler_desc_tokenizer: Any = None
        self.last_provider_used: str = "uninitialized"

    @classmethod
    def get_backend_capabilities(cls, fish_speech_url: Optional[str] = None) -> Dict[str, Any]:
        """Reports which GitHub open-source Indic engines & accelerators are ready on this host."""
        has_torch = _has_module("torch")
        cuda_avail = False
        mps_avail = False
        if has_torch:
            try:
                import torch
                cuda_avail = bool(torch.cuda.is_available())
                mps_avail = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
            except Exception:
                pass

        return {
            "accelerators": {"cuda": cuda_avail, "mps": mps_avail},
            "backends": {
                "indicf5": _has_module("f5_tts") or bool(os.getenv("INDICF5_ENABLED")),
                "indic_parler": _has_module("parler_tts"),
                "fish_speech_configured": bool(os.getenv("FISH_SPEECH_URL") or fish_speech_url),
                "chatterbox_indic": _has_module("chatterbox"),
                "sarvam_bulbul_v3": bool(os.getenv("SARVAM_API_KEY")),
                "edge_tts_humanized": _has_module("edge_tts"),
            },
            "github_repos": INDIC_GITHUB_VOICE_REPOS,
        }

    def _find_reference_prompt(self, language: str, dialect: str) -> Tuple[Optional[str], Optional[str]]:
        """Locates optional zero-shot dialect reference .wav and matching .txt transcript."""
        if not self.prompts_dir.exists():
            return None, None
        candidates = [
            self.prompts_dir / f"{dialect}.wav",
            self.prompts_dir / f"{language}.wav",
        ]
        for wav_path in candidates:
            if wav_path.is_file():
                txt_path = wav_path.with_suffix(".txt")
                ref_text = txt_path.read_text(encoding="utf-8").strip() if txt_path.is_file() else ""
                return str(wav_path), ref_text
        return None, None

    async def _synthesize_indicf5(
        self,
        text: str,
        language: str,
        dialect: str,
        reference_audio: Optional[str] = None,
        reference_text: Optional[str] = None,
    ) -> Optional[bytes]:
        """Synthesizes 24kHz audio via ai4bharat/IndicF5 (zero-shot dialect cloning)."""
        if not (_has_module("transformers") and _has_module("torch")):
            return None
        if not os.getenv("INDICF5_ENABLED") and not _has_module("f5_tts"):
            return None

        ref_wav, ref_txt = (reference_audio, reference_text or "")
        if not ref_wav:
            ref_wav, ref_txt = self._find_reference_prompt(language, dialect)
        if not ref_wav or not os.path.isfile(ref_wav):
            return None

        def _infer() -> Optional[bytes]:
            from transformers import AutoModel
            if self._indicf5_model is None:
                self._indicf5_model = AutoModel.from_pretrained(
                    "ai4bharat/IndicF5",
                    trust_remote_code=True,
                )
            audio = self._indicf5_model(text, ref_audio_path=ref_wav, ref_text=ref_txt)
            arr = np.asarray(audio, dtype=np.float32)
            if arr.dtype == np.int16:
                arr = arr.astype(np.float32) / 32768.0
            buf = io.BytesIO()
            sf.write(buf, arr, 24000, format="WAV", subtype="PCM_16")
            return buf.getvalue()

        try:
            return await asyncio.to_thread(_infer)
        except Exception:
            return None

    async def _synthesize_indic_parler(
        self,
        text: str,
        language: str,
        dialect: str,
    ) -> Optional[bytes]:
        """Synthesizes expressive regional speech via ai4bharat/indic-parler-tts."""
        if not (_has_module("parler_tts") and _has_module("transformers") and _has_module("torch")):
            return None

        style_description = IndicDialectProsodyEngine.get_style_prompt(language, dialect)

        def _infer() -> Optional[bytes]:
            import torch
            from parler_tts import ParlerTTSForConditionalGeneration
            from transformers import AutoTokenizer

            device = "cuda:0" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
            if self._parler_model is None:
                repo_id = "ai4bharat/indic-parler-tts"
                self._parler_model = ParlerTTSForConditionalGeneration.from_pretrained(repo_id).to(device)
                self._parler_tokenizer = AutoTokenizer.from_pretrained(repo_id)
                self._parler_desc_tokenizer = AutoTokenizer.from_pretrained(
                    self._parler_model.config.text_encoder._name_or_path
                )

            desc_inputs = self._parler_desc_tokenizer(style_description, return_tensors="pt").to(device)
            prompt_inputs = self._parler_tokenizer(text, return_tensors="pt").to(device)
            generation = self._parler_model.generate(
                input_ids=desc_inputs.input_ids,
                attention_mask=desc_inputs.attention_mask,
                prompt_input_ids=prompt_inputs.input_ids,
                prompt_attention_mask=prompt_inputs.attention_mask,
            )
            audio_arr = generation.cpu().numpy().squeeze().astype(np.float32)
            buf = io.BytesIO()
            sf.write(buf, audio_arr, self._parler_model.config.sampling_rate, format="WAV", subtype="PCM_16")
            return buf.getvalue()

        try:
            return await asyncio.to_thread(_infer)
        except Exception:
            return None

    async def _synthesize_fish_speech(
        self,
        text: str,
        reference_id: Optional[str] = None,
        timeout_seconds: float = 8.0,
    ) -> Optional[bytes]:
        """Calls a local/remote fishaudio/fish-speech HTTP server (/v1/tts)."""
        payload: Dict[str, Any] = {
            "text": text,
            "format": "wav",
            "normalize": True,
            "streaming": False,
        }
        if reference_id:
            payload["reference_id"] = reference_id

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                resp = await client.post(f"{self.fish_speech_url}/v1/tts", json=payload)
                if resp.status_code == 200 and len(resp.content) > 44:
                    return resp.content
        except Exception:
            return None
        return None

    async def _synthesize_sarvam_chunk(
        self, chunk_text: str, language: str, customer_mode: bool = False
    ) -> Optional[bytes]:
        """Synthesizes a single text clause via Sarvam bulbul:v3 with 1 retry on transient failure."""
        for attempt in range(2):
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_path = tmp.name
            tmp.close()
            try:
                ok = await asyncio.wait_for(
                    self.sarvam.synthesize(chunk_text, language, tmp_path, customer_mode=customer_mode),
                    timeout=15.0,
                )
                if ok and os.path.isfile(tmp_path) and os.path.getsize(tmp_path) > 100:
                    return Path(tmp_path).read_bytes()
                if getattr(self.sarvam, "last_status_code", None) in (401, 403):
                    IndicNeuralVoiceEngine._sarvam_cooldown_until = time.time() + 120.0
                    return None
            except Exception:
                if attempt == 0:
                    await asyncio.sleep(0.25)
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
        return None

    async def _synthesize_sarvam(self, text: str, language: str, customer_mode: bool = False) -> Optional[bytes]:
        """Synthesizes natural 24kHz WAV speech via Sarvam AI bulbul:v3 with concurrent breath-clause stitching."""
        if not self.sarvam.is_configured or time.time() < IndicNeuralVoiceEngine._sarvam_cooldown_until:
            return None

        clauses = IndicDialectProsodyEngine.segment_breath_clauses(text)
        if len(clauses) <= 1:
            return await self._synthesize_sarvam_chunk(text, language, customer_mode=customer_mode)

        chunk_results = await asyncio.gather(
            *[
                self._synthesize_sarvam_chunk(clause_text, language, customer_mode=customer_mode)
                for clause_text, _ in clauses
            ]
        )
        if any(chunk is None for chunk in chunk_results):
            # Single-call fallback in case one clause failed transiently while Sarvam stays online
            return await self._synthesize_sarvam_chunk(text, language, customer_mode=customer_mode)

        segment_arrays: List[np.ndarray] = []
        sample_rate = 24000
        for wav_bytes, (_, pause_s) in zip(chunk_results, clauses):
            try:
                data, sr = sf.read(io.BytesIO(wav_bytes), dtype="float32")
                sample_rate = sr
                if data.ndim > 1:
                    data = data.mean(axis=1)
                segment_arrays.append(data)
                if pause_s > 0.01:
                    segment_arrays.append(_generate_comfort_silence(pause_s, sample_rate=sample_rate))
            except Exception:
                return await self._synthesize_sarvam_chunk(text, language, customer_mode=customer_mode)

        if not segment_arrays:
            return None
        combined = np.concatenate(segment_arrays)
        out_buf = io.BytesIO()
        sf.write(out_buf, combined, sample_rate, format="WAV", subtype="PCM_16")
        return out_buf.getvalue()

    async def _synthesize_edge_tts_breath_paced(
        self,
        text: str,
        language: str,
        dialect: str,
        customer_mode: bool = False,
        rate_override: Optional[str] = None,
        pitch_override: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        """Serverless Edge-TTS with clause segmentation and ambient breath comfort-noise stitching."""
        import edge_tts

        lang = IndicDialectProsodyEngine.resolve_language(language)
        if lang == "tamil":
            voice_id = "ta-IN-ValluvarNeural" if customer_mode else "ta-IN-PallaviNeural"
            rate = rate_override or ("+1%" if customer_mode else "-4%")
            pitch = pitch_override or ("-2Hz" if customer_mode else "+1Hz")
        elif lang == "hindi":
            voice_id = "hi-IN-MadhurNeural" if customer_mode else "hi-IN-SwaraNeural"
            rate = rate_override or ("+0%" if customer_mode else "-4%")
            pitch = pitch_override or ("-2Hz" if customer_mode else "+1Hz")
        else:
            voice_id = "en-IN-PrabhatNeural" if customer_mode else "en-US-AriaNeural"
            rate = rate_override or "-3%"
            pitch = pitch_override or "+0Hz"

        clauses = IndicDialectProsodyEngine.segment_breath_clauses(text)
        if not clauses:
            clauses = [(text, 0.04)]

        segment_arrays: List[np.ndarray] = []
        sample_rate = 24000
        tmp_files: List[str] = []

        async def _synth_clause(idx: int, clause_text: str) -> str:
            fd, seg_path = tempfile.mkstemp(prefix=f"closer_seg_{idx}_", suffix=".mp3")
            os.close(fd)
            tmp_files.append(seg_path)
            comm = edge_tts.Communicate(clause_text, voice=voice_id, rate=rate, pitch=pitch)
            await comm.save(seg_path)
            return seg_path

        try:
            seg_paths = await asyncio.gather(
                *[_synth_clause(idx, clause_text) for idx, (clause_text, _) in enumerate(clauses)]
            )
            if len(clauses) == 1:
                return Path(seg_paths[0]).read_bytes(), "mp3"

            for seg_path, (_, pause_s) in zip(seg_paths, clauses):
                try:
                    data, sr = sf.read(seg_path, dtype="float32")
                    sample_rate = sr
                    if data.ndim > 1:
                        data = data.mean(axis=1)
                    segment_arrays.append(data)
                    if pause_s > 0.01:
                        segment_arrays.append(_generate_comfort_silence(pause_s, sample_rate=sample_rate))
                except Exception:
                    fd_full, full_path = tempfile.mkstemp(prefix="closer_full_", suffix=".mp3")
                    os.close(fd_full)
                    tmp_files.append(full_path)
                    comm_full = edge_tts.Communicate(text, voice=voice_id, rate=rate, pitch=pitch)
                    await comm_full.save(full_path)
                    return Path(full_path).read_bytes(), "mp3"

            combined = np.concatenate(segment_arrays) if segment_arrays else np.zeros(1024, dtype=np.float32)
            out_buf = io.BytesIO()
            sf.write(out_buf, combined, sample_rate, format="WAV", subtype="PCM_16")
            return out_buf.getvalue(), "wav"
        finally:
            for p in tmp_files:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass

    async def synthesize(
        self,
        text: str,
        language: str = "tamil",
        dialect: Optional[str] = None,
        backend: str = "auto",
        output_path: Optional[str] = None,
        inject_fillers: bool = False,
        intent_hint: str = "ack",
        customer_mode: bool = False,
        reference_audio: Optional[str] = None,
        reference_text: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
    ) -> Tuple[bytes, str, float, str]:
        """Synthesizes humanized Indic speech and returns (audio_bytes, provider_used, latency_s, audio_fmt)."""
        start_time = time.perf_counter()
        lang = IndicDialectProsodyEngine.resolve_language(language)
        resolved_dialect = IndicDialectProsodyEngine.resolve_dialect(lang, dialect)

        spoken_text = IndicDialectProsodyEngine.humanize(
            text=text,
            language=lang,
            dialect=resolved_dialect,
            inject_pauses=True,
            inject_fillers=inject_fillers,
            intent_hint=intent_hint,
            customer_mode=customer_mode,
        )

        audio_bytes: Optional[bytes] = None
        provider_used = "unknown"
        audio_fmt = "wav"
        req_backend = (backend or "auto").lower().strip()

        if req_backend in ("auto", "indicf5"):
            audio_bytes = await self._synthesize_indicf5(
                spoken_text, lang, resolved_dialect, reference_audio, reference_text
            )
            if audio_bytes:
                provider_used = f"ai4bharat/IndicF5 ({resolved_dialect})"

        if audio_bytes is None and req_backend in ("auto", "indic_parler"):
            audio_bytes = await self._synthesize_indic_parler(spoken_text, lang, resolved_dialect)
            if audio_bytes:
                provider_used = f"ai4bharat/indic-parler-tts ({resolved_dialect})"

        if audio_bytes is None and req_backend in ("auto", "fish_speech"):
            ref_id = f"customer_{lang}" if customer_mode else resolved_dialect
            audio_bytes = await self._synthesize_fish_speech(spoken_text, reference_id=ref_id)
            if audio_bytes:
                provider_used = f"fishaudio/fish-speech ({ref_id})"

        if audio_bytes is None and req_backend in ("auto", "sarvam"):
            audio_bytes = await self._synthesize_sarvam(spoken_text, lang, customer_mode=customer_mode)
            if audio_bytes:
                speaker_tag = "shubh" if customer_mode else SARVAM_FEMALE_VOICES.get(lang, "priya")
                provider_used = f"sarvam/bulbul:v3 ({speaker_tag})"
                audio_fmt = "wav"

        if audio_bytes is None:
            audio_bytes, audio_fmt = await self._synthesize_edge_tts_breath_paced(
                spoken_text,
                lang,
                resolved_dialect,
                customer_mode=customer_mode,
                rate_override=rate,
                pitch_override=pitch,
            )
            provider_used = f"edge-tts-breath-paced ({resolved_dialect})"

        self.last_provider_used = provider_used
        latency = time.perf_counter() - start_time

        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(audio_bytes)

        return audio_bytes, provider_used, latency, audio_fmt
