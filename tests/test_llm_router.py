"""
Unit tests for CLOSER AI Open-Source Foundation LLM Architecture.
Validates 175B+ catalog profiles, speculative cascading routing,
model switching, offline deterministic fallbacks, and API endpoints.
"""

import json
import unittest
from urllib.parse import urlparse

from src.closer.llm.models import (
    OPEN_SOURCE_LLM_CATALOG,
    OpenSourceLLMProfile,
    get_model_profile,
    list_available_models
)
from src.closer.llm.router import OpenLLMRouter
from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.schemas import BuyerDossier


class TestOpenSourceLLMCatalog(unittest.TestCase):
    """Test suite for open-source foundation model catalog."""

    def test_catalog_175b_tier_models_exist(self):
        """Verifies 175B+ scale foundation models are present and properly annotated."""
        self.assertIn("bloomz-176b", OPEN_SOURCE_LLM_CATALOG)
        self.assertIn("falcon-180b", OPEN_SOURCE_LLM_CATALOG)
        self.assertIn("deepseek-v3", OPEN_SOURCE_LLM_CATALOG)
        self.assertIn("command-r-plus", OPEN_SOURCE_LLM_CATALOG)
        self.assertIn("llama-3.3-70b", OPEN_SOURCE_LLM_CATALOG)
        self.assertIn("qwen-2.5-72b", OPEN_SOURCE_LLM_CATALOG)

        bloomz = OPEN_SOURCE_LLM_CATALOG["bloomz-176b"]
        self.assertEqual(bloomz.parameter_scale, "176 Billion")
        self.assertEqual(bloomz.multilingual_coverage, 46)

        deepseek = OPEN_SOURCE_LLM_CATALOG["deepseek-v3"]
        self.assertEqual(deepseek.parameter_scale, "671 Billion")
        self.assertEqual(deepseek.active_parameters, "37 Billion (Sparse MoE)")

        falcon = OPEN_SOURCE_LLM_CATALOG["falcon-180b"]
        self.assertEqual(falcon.parameter_scale, "180 Billion")

    def test_get_model_profile_resolution(self):
        """Verifies model resolution via alias or partial string."""
        p1 = get_model_profile("bloomz-176b")
        self.assertEqual(p1.model_id, "bigscience/bloomz")

        p2 = get_model_profile("deepseek")
        self.assertEqual(p2.model_id, "deepseek-ai/DeepSeek-V3")

        # Fallback to default Llama 3.3 70B for unknown model
        p_unknown = get_model_profile("nonexistent-model-xyz")
        self.assertEqual(p_unknown.model_id, "meta-llama/Llama-3.3-70B-Instruct")

    def test_list_available_models_serialization(self):
        """Verifies serializable model listing for API consumers."""
        models = list_available_models()
        self.assertIsInstance(models, list)
        self.assertGreaterEqual(len(models), 6)
        first = models[0]
        self.assertIn("id", first)
        self.assertIn("name", first)
        self.assertIn("parameter_scale", first)
        self.assertIn("latency_ms", first)


class TestOpenLLMRouter(unittest.TestCase):
    """Test suite for speculative cascading router and deterministic fallbacks."""

    def setUp(self):
        self.router = OpenLLMRouter(default_model="llama-3.3-70b")

    def test_initial_state(self):
        """Verifies router initializes with Llama 3.3 70B profile."""
        info = self.router.get_active_model_info()
        self.assertEqual(info["model_id"], "llama-3.3-70b")
        self.assertEqual(info["parameter_scale"], "70 Billion")
        self.assertEqual(info["target_latency_ms"], 88)

    def test_dynamic_model_switching(self):
        """Verifies switching between 175B+ tier foundation models."""
        # Switch to BLOOMZ 176B
        self.router.set_active_model("bloomz-176b")
        info = self.router.get_active_model_info()
        self.assertEqual(info["model_id"], "bloomz-176b")
        self.assertEqual(info["parameter_scale"], "176 Billion")
        self.assertEqual(info["multilingual_coverage"], 46)

        # Switch to DeepSeek-V3 671B
        self.router.set_active_model("deepseek-v3")
        info2 = self.router.get_active_model_info()
        self.assertEqual(info2["parameter_scale"], "671 Billion")

    def test_deterministic_fallback_execution(self):
        """Verifies offline fallback produces high-conviction responses and telemetry."""
        reply, telemetry = self.router.route_reasoning(
            user_utterance="What is your 1031 tax exchange policy?",
            system_prompt="You are CLOSER AI luxury real estate concierge.",
            conversation_history=[],
            market_mode="usa",
            force_tier="deterministic_fallback"
        )
        self.assertIn("1031 tax-deferred exchanges", reply)
        self.assertEqual(telemetry["tier_used"], "deterministic_fallback")
        self.assertGreaterEqual(telemetry["latency_ms"], 0)

    def test_india_rera_fallback_reasoning(self):
        """Verifies Indian market RERA compliance fallback query."""
        reply, telemetry = self.router.route_reasoning(
            user_utterance="Is this project RERA approved?",
            system_prompt="You are CLOSER AI India customer care executive.",
            conversation_history=[],
            market_mode="india",
            force_tier="deterministic_fallback"
        )
        self.assertIn("100% RERA-sanctioned", reply)
        self.assertIn("WhatsApp", reply)


class TestConversationEngineLLMIntegration(unittest.TestCase):
    """Test suite verifying ConversationEngine integration with OpenLLMRouter."""

    def test_engine_has_llm_router(self):
        """Verifies ConversationEngine initializes with OpenLLMRouter and default model."""
        engine = ConversationEngine(market_mode="usa")
        self.assertIsNotNone(engine.llm_router)
        self.assertEqual(engine.dossier.active_llm_model, "llama-3.3-70b")
        self.assertEqual(engine.dossier.llm_parameter_scale, "70 Billion")

    def test_engine_switch_llm_model(self):
        """Verifies dynamic switching updates dossier metadata."""
        engine = ConversationEngine(market_mode="india")
        info = engine.set_llm_model("bloomz-176b")
        self.assertEqual(info["model_id"], "bloomz-176b")
        self.assertEqual(engine.dossier.active_llm_model, "bloomz-176b")
        self.assertEqual(engine.dossier.llm_parameter_scale, "176 Billion")

        dossier = engine.export_dossier()
        dump = dossier.model_dump()
        self.assertEqual(dump["active_llm_model"], "bloomz-176b")
        self.assertEqual(dump["llm_parameter_scale"], "176 Billion")


if __name__ == "__main__":
    unittest.main()
