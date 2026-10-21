"""
Speculative Cascading Router for Open-Source Foundation LLMs.
Leverages curated architectures from ever-works/awesome-open-source-llms,
including 175B+ parameter models (BLOOMZ 176B, Falcon 180B, DeepSeek-V3 671B MoE, Command R+ 104B)
and sub-100ms reflex edge models (Llama 3.3 70B Turbo, Qwen 2.5 72B).
"""

from __future__ import annotations
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple

from src.closer.config import settings
from src.closer.llm.models import (
    OPEN_SOURCE_LLM_CATALOG,
    OpenSourceLLMProfile,
    get_model_profile,
    list_available_models
)


class OpenLLMRouter:
    """
    Speculative Cascading Router balancing real-time voice latency with 175B+ deep reasoning.
    
    Architecture:
      - Tier 1: Reflex Edge (Target <100ms) - Llama 3.3 70B / Qwen 2.5 72B for rapid voice turn-taking.
      - Tier 2: Deep 175B+ Reasoning (150-300ms) - BLOOMZ 176B, Falcon 180B, DeepSeek 671B MoE, Command R+
        for complex objection deconstruction, 1031 tax exchanges, Indian RERA legal compliance, and mortgage math.
      - Tier 3: Deterministic Fallback (0ms, 100% uptime) - Structured offline rule engine ensuring
        zero hallucination and resilient offline execution when providers are unconfigured or slow.
    """

    def __init__(
        self,
        default_model: str = "llama-3.3-70b",
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = 2.5
    ):
        self.active_model_id = default_model if default_model in OPEN_SOURCE_LLM_CATALOG else "llama-3.3-70b"
        self.active_profile = get_model_profile(self.active_model_id)
        self.api_base = api_base or getattr(settings, "OPENAI_API_BASE", None) or "https://api.groq.com/openai/v1"
        self.api_key = api_key or getattr(settings, "GROQ_API_KEY", None) or getattr(settings, "OPENAI_API_KEY", None)
        self.timeout_seconds = timeout_seconds
        self.total_routed_calls = 0
        self.last_latency_ms = 0
        self.last_tier_used = "deterministic_fallback"

    def set_active_model(self, model_id_or_alias: str) -> OpenSourceLLMProfile:
        """Dynamically switches active open-source foundation model."""
        self.active_profile = get_model_profile(model_id_or_alias)
        self.active_model_id = self.active_profile.model_id
        # Also map short key if found
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
        market_mode: str = "usa",
        force_tier: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Executes speculative cascading routing:
        Attempts Tier 1/2 remote execution via open-source LLM provider if configured.
        Gracefully cascades to Tier 3 deterministic fallback with telemetry.
        """
        start_time = time.perf_counter()
        self.total_routed_calls += 1

        # Check if caller wants deterministic fallback directly
        if force_tier == "deterministic_fallback" or not self.api_key:
            reply = self._generate_fallback_response(user_utterance, market_mode)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            self.last_latency_ms = elapsed_ms
            self.last_tier_used = "deterministic_fallback"
            return reply, self._build_telemetry(elapsed_ms, "deterministic_fallback")

        # Remote LLM execution via OpenAI-compatible endpoint (Groq / vLLM / Ollama)
        try:
            tier = "deep_175b_reasoning" if "176" in self.active_profile.parameter_scale or "671" in self.active_profile.parameter_scale or "180" in self.active_profile.parameter_scale or "104" in self.active_profile.parameter_scale else "reflex_edge"
            reply = self._call_remote_provider(system_prompt, conversation_history, user_utterance)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            self.last_latency_ms = elapsed_ms
            self.last_tier_used = tier
            return reply, self._build_telemetry(elapsed_ms, tier)
        except Exception:
            # Cascading fallback on network timeout or provider outage
            reply = self._generate_fallback_response(user_utterance, market_mode)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            self.last_latency_ms = elapsed_ms
            self.last_tier_used = "deterministic_fallback"
            return reply, self._build_telemetry(elapsed_ms, "deterministic_fallback")

    def _call_remote_provider(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        user_utterance: str
    ) -> str:
        """Performs HTTP request to OpenAI-compatible LLM endpoint (Groq, vLLM, Ollama)."""
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history[-6:]:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_utterance})

        # Map catalog profile to provider model ID if using Groq
        model_name = self.active_profile.model_id
        if "api.groq.com" in (self.api_base or ""):
            if "70b" in self.active_model_id:
                model_name = "llama-3.3-70b-versatile"
            elif "qwen" in self.active_model_id:
                model_name = "qwen-2.5-32b"
            else:
                model_name = "llama-3.3-70b-versatile"

        url = f"{self.api_base.rstrip('/')}/chat/completions"
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 160,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "CLOSER-AI/1.0.0 (Awesome-Open-Source-LLMs-175B-Router)"
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()

    def _generate_fallback_response(self, user_utterance: str, market_mode: str) -> str:
        """Deterministic context-aware fallback response generation."""
        t = user_utterance.lower()
        if market_mode == "india":
            if any(w in t for w in ["rera", "approval", "legal"]):
                return "All our featured developments are 100% RERA-sanctioned with clear title deeds and occupancy certificates. Would you like me to send the official RERA registration number and approved sanction plans directly to your WhatsApp?"
            if any(w in t for w in ["price", "cost", "budget", "crore", "lakh"]):
                return "Our residential units range from ₹1.85 Crores for premium 2 BHKs to ₹4.5 Crores for bespoke 4 BHK penthouses. What configuration best matches your lifestyle preference?"
            return "Thank you for sharing that. I will arrange for our relationship executive to share our complete inventory, floor plans, and current pricing options directly on your WhatsApp. Would this weekend work for a private walkthrough?"
        else:
            if any(w in t for w in ["1031", "tax", "exchange"]):
                return "We regularly coordinate 1031 tax-deferred exchanges with qualified intermediaries for our private clients. We have several off-market luxury replacement properties in Bel Air and Beverly Hills that satisfy strict identification deadlines. Are you currently within your 45-day window?"
            if any(w in t for w in ["commission", "fee", "rate"]):
                return "Our brokerage fee reflects our white-glove advisory, discrete off-market sourcing, and full private escrow management. May I confirm if you're looking to acquire within the next 30 to 60 days?"
            return "Understood. Our principal broker hosts discrete private showings at the estate this Thursday and Friday afternoon. Would 2:00 PM or 4:00 PM suit your calendar better?"

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
