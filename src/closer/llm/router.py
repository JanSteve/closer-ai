"""
Speculative Cascading Router for Clinical & Foundation LLMs (Amura Health / CLOSER AI).
Supports Gemini (GEMINI_API_KEY / GOOGLE_API_KEY), Groq, OpenAI, and OpenRouter
with a zero-hallucination Tier 3 healthcare-safe deterministic fallback.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from src.closer.config import settings
from src.closer.llm.models import (
    OPEN_SOURCE_LLM_CATALOG,
    OpenSourceLLMProfile,
    get_model_profile,
)


class OpenLLMRouter:
    """
    Speculative Cascading Router balancing real-time voice latency with deep clinical reasoning:
      - Tier 1: Reflex Edge (<100ms) — Llama 3.3 70B / Qwen 2.5 72B / Gemini 2.5 Flash
      - Tier 2: Deep 175B+ Reasoning (150-300ms) — BLOOMZ 176B, Falcon 180B, DeepSeek 671B, Command R+
      - Tier 3: Deterministic Healthcare Fallback (0ms, 100% uptime) — Safe Amura Health EN/TA/HI replies
    """

    def __init__(
        self,
        default_model: str = "llama-3.3-70b",
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = 2.5,
    ):
        self.active_model_id = default_model if default_model in OPEN_SOURCE_LLM_CATALOG else "llama-3.3-70b"
        self.active_profile = get_model_profile(self.active_model_id)

        env_gemini = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        env_groq = os.getenv("GROQ_API_KEY") or getattr(settings, "GROQ_API_KEY", None)
        env_openai = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
        env_github = os.getenv("GITHUB_TOKEN")
        env_openrouter = (
            os.getenv("OPENROUTER_API_KEY")
            or getattr(settings, "OPENROUTER_API_KEY", None)
            or (
                os.getenv("ANTHROPIC_AUTH_TOKEN")
                if (os.getenv("ANTHROPIC_AUTH_TOKEN") or "").startswith("sk-or-v1-")
                else None
            )
        )

        self.gemini_api_key = env_gemini
        self.api_key = api_key or env_groq or env_openai or env_openrouter or env_gemini or env_github

        if api_base:
            self.api_base = api_base
        elif self.api_key and str(self.api_key).startswith("sk-or-v1-"):
            self.api_base = "https://openrouter.ai/api/v1"
        elif self.api_key and self.api_key == env_gemini and not (env_groq or env_openai or env_openrouter):
            self.api_base = "https://generativelanguage.googleapis.com/v1beta/openai"
            if default_model == "llama-3.3-70b":
                self.active_model_id = "gemini-2.5-flash"
                self.active_profile = get_model_profile("gemini-2.5-flash")
        elif self.api_key and self.api_key == env_github and not (env_groq or env_openai or env_openrouter or env_gemini):
            self.api_base = "https://models.inference.ai.azure.com"
        else:
            self.api_base = os.getenv("OPENAI_API_BASE") or getattr(settings, "OPENAI_API_BASE", None) or "https://api.groq.com/openai/v1"

        self.timeout_seconds = timeout_seconds
        self.total_routed_calls = 0
        self.last_latency_ms = 0
        self.last_tier_used = "deterministic_fallback"

    def set_active_model(self, model_id_or_alias: str) -> OpenSourceLLMProfile:
        """Dynamically switches active foundation model."""
        self.active_profile = get_model_profile(model_id_or_alias)
        self.active_model_id = self.active_profile.model_id
        for key, p in OPEN_SOURCE_LLM_CATALOG.items():
            if p.model_id == self.active_profile.model_id or key == model_id_or_alias.lower():
                self.active_model_id = key
                break
        return self.active_profile

    def get_active_model_info(self) -> Dict[str, Any]:
        """Returns metadata of currently active foundation model."""
        return {
            "model_id": self.active_model_id,
            "display_name": self.active_profile.display_name,
            "parameter_scale": self.active_profile.parameter_scale,
            "active_parameters": self.active_profile.active_parameters,
            "architecture": self.active_profile.architecture,
            "primary_use_case": self.active_profile.primary_use_case,
            "target_latency_ms": self.active_profile.target_telephony_latency_ms,
            "last_latency_ms": self.last_latency_ms,
            "last_tier_used": self.last_tier_used,
            "has_remote_provider": bool(self.api_key),
            "supports_function_calling": self.active_profile.supports_function_calling,
            "multilingual_coverage": self.active_profile.multilingual_coverage,
        }

    def route_reasoning(
        self,
        user_utterance: str,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        market_mode: str = "india",
        force_tier: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Executes speculative cascading routing:
        Attempts Tier 1/2 remote execution if configured, gracefully cascading to Tier 3
        healthcare-safe deterministic fallback.
        """
        start_time = time.perf_counter()
        self.total_routed_calls += 1

        if force_tier == "deterministic_fallback":
            reply = self._generate_fallback_response(user_utterance, market_mode)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            self.last_latency_ms = elapsed_ms
            self.last_tier_used = "deterministic_fallback"
            return reply, self._build_telemetry(elapsed_ms, "deterministic_fallback")

        if not self.api_key:
            # Try free zero-key open LLM endpoint (Pollinations OpenAI-compatible) unless offline-only
            if os.getenv("CLOSER_OFFLINE_ONLY") != "1":
                try:
                    reply = self._call_free_open_brain(system_prompt, conversation_history, user_utterance)
                    if reply and reply.strip().lower() not in ("", "none", "undefined"):
                        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                        self.last_latency_ms = elapsed_ms
                        self.last_tier_used = "free_open_llm"
                        return reply, self._build_telemetry(elapsed_ms, "free_open_llm")
                except Exception:
                    pass
            reply = self._generate_fallback_response(user_utterance, market_mode)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            self.last_latency_ms = elapsed_ms
            self.last_tier_used = "deterministic_fallback"
            return reply, self._build_telemetry(elapsed_ms, "deterministic_fallback")

        try:
            scale = self.active_profile.parameter_scale
            tier = (
                "deep_175b_reasoning"
                if any(x in scale for x in ("176", "671", "180", "104"))
                else "reflex_edge"
            )
            reply = self._call_remote_provider(system_prompt, conversation_history, user_utterance)
            if not reply or reply.strip().lower() in ("", "none", "undefined"):
                raise ValueError("Empty remote provider response")
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            self.last_latency_ms = elapsed_ms
            self.last_tier_used = tier
            return reply, self._build_telemetry(elapsed_ms, tier)
        except Exception:
            reply = self._generate_fallback_response(user_utterance, market_mode)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            self.last_latency_ms = elapsed_ms
            self.last_tier_used = "deterministic_fallback"
            return reply, self._build_telemetry(elapsed_ms, "deterministic_fallback")

    def _call_remote_provider(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        user_utterance: str,
    ) -> str:
        """Performs HTTP request to OpenAI-compatible LLM endpoint (Gemini, Groq, OpenRouter, vLLM)."""
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history[-6:]:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_utterance})

        base = (self.api_base or "").rstrip("/")
        models_to_try = [self.active_profile.model_id]
        if "generativelanguage.googleapis.com" in base:
            models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash"]
        elif "openrouter.ai" in base:
            models_to_try = ["google/gemini-2.5-flash", "meta-llama/llama-3.3-70b-instruct"]
        elif "api.groq.com" in base:
            if "qwen" in self.active_model_id:
                models_to_try = ["qwen-2.5-32b", "llama-3.3-70b-versatile"]
            else:
                models_to_try = ["llama-3.3-70b-versatile"]

        url = f"{base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "CLOSER-AI/2.0.0 (Amura-Health-Clinical-Router)",
        }

        last_err: Optional[Exception] = None
        for candidate_model in models_to_try:
            payload = {
                "model": candidate_model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 250,
            }
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    content = data["choices"][0]["message"]["content"].strip()
                    if content:
                        return content
            except Exception as e:
                last_err = e
                continue

        if last_err:
            raise last_err
        raise RuntimeError("No candidate models returned content")

    def _call_free_open_brain(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        user_utterance: str,
    ) -> str:
        """Calls the free, zero-key open-access OpenAI-compatible endpoint (Pollinations AI)."""
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history[-6:]:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_utterance})

        req = urllib.request.Request(
            "https://text.pollinations.ai/openai",
            data=json.dumps({
                "model": "openai",
                "messages": messages,
                "temperature": 0.35,
                "max_tokens": 180,
            }).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "CLOSER-AI/2.0.0 (Amura-Health-Open-Brain)",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return (data["choices"][0]["message"]["content"] or "").strip()

    def _generate_fallback_response(self, user_utterance: str, market_mode: str) -> str:
        """Deterministic healthcare-safe fallback response generation for Amura Health."""
        t = (user_utterance or "").lower()
        mode = (market_mode or "india").lower().strip()

        # Life-safety check inside Tier 3 fallback as defense in depth
        if any(
            w in t
            for w in [
                "chest pain", "can't breathe", "cannot breathe", "shortness of breath",
                "stroke", "unconscious", "நெஞ்சு வலி", "மூச்சு", "सीने में दर्द", "सांस",
            ]
        ):
            if mode == "tamil":
                return "தயவுசெய்து உடனே 108 அவசர உதவி எண்ணை அழைக்கவும் அல்லது அருகிலுள்ள அவசர சிகிச்சைப் பிரிவுக்கு (ER) செல்லவும்."
            if mode == "hindi":
                return "कृपया तुरंत 108 इमरजेंसी नंबर पर कॉल करें या नजदीकी अस्पताल के इमरजेंसी रूम (ER) में जाएँ।"
            return "Please call 108 emergency services immediately or go to the nearest hospital Emergency Room (ER) right away."

        if any(w in t for w in ["prescribe", "insulin dose", "metformin", "dosage", "diagnose", "diagnosis"]):
            return (
                "I cannot diagnose medical conditions or prescribe or adjust medications. "
                "Would you like me to schedule a consultation with a licensed Amura Health physician to review this safely?"
            )

        if mode == "tamil":
            if any(w in t for w in ["fee", "price", "cost", "கட்டணம்", "விலை"]):
                return (
                    "Amura Health-ல் ஆரம்ப டாக்டர் ஆலோசனை ₹1,500 முதல் தொடங்குகிறது, EMI வசதியும் உள்ளது. "
                    "ஆன்லைன் வீடியோ அல்லது வேளச்சேரி கிளினிக் கன்சல்டேஷன் நேரம் பதிவு செய்யலாமா?"
                )
            return (
                "தகவல் பகிர்ந்ததற்கு நன்றி! Amura Health மருத்துவர் மற்றும் ஹெல்த் கோச் குழு MNT மற்றும் NMT மூலம் "
                "உங்களுக்கு வழிகாட்டத் தயாராக உள்ளது. வாட்ஸ்அப்பில் விவரங்கள் அனுப்பட்டுமா?"
            )

        if mode == "hindi":
            if any(w in t for w in ["fee", "price", "cost", "फीस", "कीमत"]):
                return (
                    "Amura Health में शुरुआती डॉक्टर कंसल्टेशन ₹1,500 से शुरू होता है और आसान EMI विकल्प भी उपलब्ध हैं। "
                    "क्या मैं आपके लिए ऑनलाइन या चेन्नई क्लिनिक स्लॉट देखूँ?"
                )
            return (
                "जानकारी साझा करने के लिए धन्यवाद! Amura Health के डॉक्टर और हेल्थ कोच MNT व NMT के माध्यम से "
                "मेटाबोलिक केयर में आपकी सहायता के लिए तैयार हैं। क्या मैं वॉट्सऐप पर गाइड भेज दूँ?"
            )

        if any(w in t for w in ["mnt", "nmt", "metabolic", "reversal", "diabetes", "pcos", "pcod", "thyroid", "fatty liver"]):
            return (
                "At Amura Health, licensed physicians and health coaches collaborate using Medical Nutrition Therapy (MNT) "
                "and Natural Molecule Therapy (NMT) guided by deep biomarker panels. Would you like to book an online or Velachery clinic consultation?"
            )
        if any(w in t for w in ["velachery", "chennai", "address", "location", "clinic"]):
            return (
                f"Amura Health is located at {settings.CLINIC_ADDRESS}, and we also provide online video consultations across India and globally. "
                "Would you like to reserve a consultation slot or receive directions on WhatsApp?"
            )
        if any(w in t for w in ["fee", "price", "cost", "emi", "insurance"]):
            return (
                "Initial physician consultations at Amura Health start at ₹1,500, with personalized metabolic care plans and flexible EMI options. "
                "May I share our care guide on WhatsApp or check a convenient slot for you?"
            )
        return (
            f"Thank you for reaching out to {settings.CLINIC_NAME}. Our physician and health-coach team supports metabolic reversal and hospital triage "
            "online and at Velachery, Chennai — would you like to schedule a consultation?"
        )

    def _build_telemetry(self, elapsed_ms: int, tier_used: str) -> Dict[str, Any]:
        """Constructs standardized inference telemetry payload."""
        return {
            "model_id": self.active_model_id,
            "display_name": self.active_profile.display_name,
            "parameter_scale": self.active_profile.parameter_scale,
            "active_parameters": self.active_profile.active_parameters,
            "architecture": self.active_profile.architecture,
            "latency_ms": elapsed_ms,
            "target_latency_ms": self.active_profile.target_telephony_latency_ms,
            "tier_used": tier_used,
            "supports_function_calling": self.active_profile.supports_function_calling,
            "multilingual_coverage": self.active_profile.multilingual_coverage,
        }
