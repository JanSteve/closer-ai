"""
Open-Source & Foundation LLM Catalog & Architecture Profiles for CLOSER AI (Amura Health).
Provides model metadata, parameter counts, context limits, and clinical telephony latency profiles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class OpenSourceLLMProfile:
    """Metadata specification for foundation models."""

    model_id: str
    display_name: str
    parameter_scale: str
    active_parameters: str
    context_window: int
    architecture: str
    primary_use_case: str
    target_telephony_latency_ms: int
    open_license: str
    supports_function_calling: bool
    multilingual_coverage: int


OPEN_SOURCE_LLM_CATALOG: Dict[str, OpenSourceLLMProfile] = {
    "gemini-2.5-flash": OpenSourceLLMProfile(
        model_id="google/gemini-2.5-flash",
        display_name="Gemini 2.5 Flash (Google Multimodal)",
        parameter_scale="Flash Reasoning Tier",
        active_parameters="MoE Multimodal",
        context_window=1048576,
        architecture="Multimodal Sparse Transformer",
        primary_use_case="Sub-second tri-lingual clinical front-desk dialogue, emotion-aware empathy, and safe triage routing",
        target_telephony_latency_ms=95,
        open_license="Google Gemini API",
        supports_function_calling=True,
        multilingual_coverage=100,
    ),
    "bloomz-176b": OpenSourceLLMProfile(
        model_id="bigscience/bloomz",
        display_name="BLOOMZ 176B (BigScience Multilingual)",
        parameter_scale="176 Billion",
        active_parameters="176B (Dense)",
        context_window=2048,
        architecture="Transformer Decoder (ALiBi Positional Embeddings)",
        primary_use_case="Multilingual patient intake across 46 natural languages including Tamil and Hindi dialects",
        target_telephony_latency_ms=280,
        open_license="BigScience OpenRAIL-M v1",
        supports_function_calling=True,
        multilingual_coverage=46,
    ),
    "llama-3.3-70b": OpenSourceLLMProfile(
        model_id="meta-llama/Llama-3.3-70B-Instruct",
        display_name="Llama 3.3 70B Turbo (Meta AI)",
        parameter_scale="70 Billion",
        active_parameters="70B (Dense GQA)",
        context_window=128000,
        architecture="Dense Auto-regressive Transformer (GQA 8 Heads)",
        primary_use_case="Real-time clinical voice telephony reflex engine (<100ms first-token latency on Groq/vLLM)",
        target_telephony_latency_ms=88,
        open_license="Llama 3.3 Community License",
        supports_function_calling=True,
        multilingual_coverage=32,
    ),
    "command-r-plus": OpenSourceLLMProfile(
        model_id="CohereForAI/c4ai-command-r-plus",
        display_name="Command R+ (104B Cohere Enterprise)",
        parameter_scale="104 Billion",
        active_parameters="104B (Dense)",
        context_window=128000,
        architecture="Transformer Decoder with Multi-Step Tooling",
        primary_use_case="Enterprise EHR/CRM dispatch, clinical RAG, and DPDP healthcare compliance verification",
        target_telephony_latency_ms=175,
        open_license="CC-BY-NC-4.0",
        supports_function_calling=True,
        multilingual_coverage=23,
    ),
    "deepseek-v3": OpenSourceLLMProfile(
        model_id="deepseek-ai/DeepSeek-V3",
        display_name="DeepSeek-V3 / R1 (671B Frontier MoE)",
        parameter_scale="671 Billion",
        active_parameters="37 Billion (Sparse MoE)",
        context_window=128000,
        architecture="Multi-head Latent Attention (MLA) + DeepSeekMoE",
        primary_use_case="Complex metabolic care-plan explanations, MNT/NMT education, and empathetic patient guidance",
        target_telephony_latency_ms=195,
        open_license="MIT License",
        supports_function_calling=True,
        multilingual_coverage=50,
    ),
    "qwen-2.5-72b": OpenSourceLLMProfile(
        model_id="Qwen/Qwen2.5-72B-Instruct",
        display_name="Qwen 2.5 72B (Alibaba Sovereign)",
        parameter_scale="72 Billion",
        active_parameters="72B (Dense)",
        context_window=131072,
        architecture="RoPE + SwiGLU + RMSNorm",
        primary_use_case="Code-mixing, Hinglish & Tanglish patient dialogue, and care-schedule coordination",
        target_telephony_latency_ms=115,
        open_license="Apache-2.0",
        supports_function_calling=True,
        multilingual_coverage=29,
    ),
    "falcon-180b": OpenSourceLLMProfile(
        model_id="tiiuae/falcon-180B",
        display_name="Falcon 180B (TII Sovereign Foundation)",
        parameter_scale="180 Billion",
        active_parameters="180B (Dense Multi-Query)",
        context_window=4096,
        architecture="Multiquery Attention (MQA) Transformer",
        primary_use_case="Sovereign high-security on-premise hospital front-desk & DPDP-compliant patient intake",
        target_telephony_latency_ms=310,
        open_license="Falcon 180B TII License",
        supports_function_calling=False,
        multilingual_coverage=10,
    ),
}


def get_model_profile(model_id_or_alias: str) -> OpenSourceLLMProfile:
    """Resolves profile by key or returns the default Llama 3.3 70B profile."""
    key = model_id_or_alias.lower().strip()
    if key in OPEN_SOURCE_LLM_CATALOG:
        return OPEN_SOURCE_LLM_CATALOG[key]
    for profile in OPEN_SOURCE_LLM_CATALOG.values():
        if key in profile.model_id.lower() or key in profile.display_name.lower():
            return profile
    return OPEN_SOURCE_LLM_CATALOG["llama-3.3-70b"]


def list_available_models() -> List[Dict[str, Any]]:
    """Returns a serializable list of foundation models for API consumers."""
    return [
        {
            "id": key,
            "name": p.display_name,
            "parameter_scale": p.parameter_scale,
            "active_parameters": p.active_parameters,
            "context_window": p.context_window,
            "architecture": p.architecture,
            "primary_use_case": p.primary_use_case,
            "latency_ms": p.target_telephony_latency_ms,
            "license": p.open_license,
            "languages": p.multilingual_coverage,
        }
        for key, p in OPEN_SOURCE_LLM_CATALOG.items()
    ]
