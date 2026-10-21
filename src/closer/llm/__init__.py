"""
CLOSER AI — Open-Source LLM Architecture Module.
Curated models from ever-works/awesome-open-source-llms including 175B+ scale foundation models.
"""

from src.closer.llm.models import (
    OPEN_SOURCE_LLM_CATALOG,
    OpenSourceLLMProfile,
    get_model_profile,
    list_available_models,
)
from src.closer.llm.router import OpenLLMRouter

__all__ = [
    "OPEN_SOURCE_LLM_CATALOG",
    "OpenSourceLLMProfile",
    "get_model_profile",
    "list_available_models",
    "OpenLLMRouter",
]
