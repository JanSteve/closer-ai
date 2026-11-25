"""
Unit tests for CLOSER AI Foundation LLM Architecture & Speculative Cascading Router.
Validates catalog profiles, Gemini + Groq/OpenRouter routing, model switching,
and healthcare-safe Tier 3 deterministic fallbacks (zero real-estate terms).
"""

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import src.closer.memory.learning_db as ldb
from src.closer.agent.conversation import ConversationEngine
from src.closer.llm.models import OPEN_SOURCE_LLM_CATALOG, get_model_profile, list_available_models
from src.closer.llm.router import OpenLLMRouter

_API_KEYS = (
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
)


class TestOpenSourceLLMCatalog(unittest.TestCase):
    """Test suite for foundation model catalog."""

    def test_catalog_175b_and_gemini_models_exist(self):
        self.assertIn("gemini-2.5-flash", OPEN_SOURCE_LLM_CATALOG)
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
        p1 = get_model_profile("bloomz-176b")
        self.assertEqual(p1.model_id, "bigscience/bloomz")

        p2 = get_model_profile("deepseek")
        self.assertEqual(p2.model_id, "deepseek-ai/DeepSeek-V3")

        p_unknown = get_model_profile("nonexistent-model-xyz")
        self.assertEqual(p_unknown.model_id, "meta-llama/Llama-3.3-70B-Instruct")

    def test_list_available_models_serialization(self):
        models = list_available_models()
        self.assertIsInstance(models, list)
        self.assertGreaterEqual(len(models), 7)
        first = models[0]
        for k in ("id", "name", "parameter_scale", "latency_ms"):
            self.assertIn(k, first)


class TestOpenLLMRouter(unittest.TestCase):
    """Test suite for speculative cascading router, Gemini support, and clinical Tier 3 fallbacks."""

    def setUp(self):
        self._env_patch = patch.dict(os.environ, {k: "" for k in _API_KEYS})
        self._env_patch.start()
        with patch("src.closer.llm.router.settings.GEMINI_API_KEY", None), patch(
            "src.closer.llm.router.settings.GROQ_API_KEY", None
        ), patch("src.closer.llm.router.settings.OPENAI_API_KEY", None), patch(
            "src.closer.llm.router.settings.OPENROUTER_API_KEY", None
        ):
            self.router = OpenLLMRouter(default_model="llama-3.3-70b")

    def tearDown(self):
        self._env_patch.stop()

    def test_initial_state(self):
        info = self.router.get_active_model_info()
        self.assertEqual(info["model_id"], "llama-3.3-70b")
        self.assertEqual(info["parameter_scale"], "70 Billion")
        self.assertEqual(info["target_latency_ms"], 88)

    def test_dynamic_model_switching(self):
        self.router.set_active_model("bloomz-176b")
        info = self.router.get_active_model_info()
        self.assertEqual(info["model_id"], "bloomz-176b")
        self.assertEqual(info["parameter_scale"], "176 Billion")
        self.assertEqual(info["multilingual_coverage"], 46)

        self.router.set_active_model("deepseek-v3")
        info2 = self.router.get_active_model_info()
        self.assertEqual(info2["parameter_scale"], "671 Billion")

    def test_deterministic_clinical_fallback_execution(self):
        """Verifies Tier 3 fallback produces Amura Health clinical responses without real-estate text."""
        reply, telemetry = self.router.route_reasoning(
            user_utterance="What is Amura Health's MNT and NMT metabolic reversal program?",
            system_prompt="You are Amura Health clinical front-desk concierge.",
            conversation_history=[],
            market_mode="india",
            force_tier="deterministic_fallback",
        )
        self.assertIn("Medical Nutrition Therapy", reply)
        self.assertIn("Natural Molecule Therapy", reply)
        self.assertEqual(telemetry["tier_used"], "deterministic_fallback")
        self.assertGreaterEqual(telemetry["latency_ms"], 0)
        for forbidden in ("1031", "rera", "bel air", "bhk", "penthouse"):
            self.assertNotIn(forbidden, reply.lower())

    def test_velachery_and_trilingual_clinical_fallbacks(self):
        """Verifies Velachery Chennai location, Tamil, and Hindi Tier 3 healthcare fallbacks."""
        reply_loc, _ = self.router.route_reasoning(
            user_utterance="Where is the Velachery Chennai clinic located?",
            system_prompt="Amura Health",
            conversation_history=[],
            market_mode="india",
            force_tier="deterministic_fallback",
        )
        self.assertIn("Velachery Main Road", reply_loc)

        reply_ta, _ = self.router.route_reasoning(
            user_utterance="Amura Health fees எவ்வளவு?",
            system_prompt="Amura Health",
            conversation_history=[],
            market_mode="tamil",
            force_tier="deterministic_fallback",
        )
        self.assertIn("Amura Health", reply_ta)

        reply_hi, _ = self.router.route_reasoning(
            user_utterance="फीस कितनी है?",
            system_prompt="Amura Health",
            conversation_history=[],
            market_mode="hindi",
            force_tier="deterministic_fallback",
        )
        self.assertIn("Amura Health", reply_hi)

    def test_gemini_api_key_routing_and_mocked_remote_call(self):
        """Verifies GEMINI_API_KEY activates Gemini endpoint and gracefully falls back on timeout."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyTestDummyKey12345"}):
            gemini_router = OpenLLMRouter()
            self.assertEqual(gemini_router.active_model_id, "gemini-2.5-flash")
            self.assertIn("generativelanguage.googleapis.com", gemini_router.api_base)

            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(
                {"choices": [{"message": {"content": "Amura Health pairs a physician and health coach for metabolic care."}}]}
            ).encode("utf-8")
            mock_ctx = MagicMock()
            mock_ctx.__enter__.return_value = mock_resp
            mock_ctx.__exit__.return_value = False

            with patch("urllib.request.urlopen", return_value=mock_ctx) as mock_open:
                reply, telemetry = gemini_router.route_reasoning(
                    "How does Amura Health care team work?",
                    "You are Amura Health coordinator.",
                    [],
                    market_mode="india",
                )
                self.assertIn("Amura Health", reply)
                self.assertEqual(telemetry["tier_used"], "reflex_edge")
                mock_open.assert_called_once()

            # Network error gracefully cascades to clinical Tier 3 fallback
            with patch("urllib.request.urlopen", side_effect=TimeoutError("simulated timeout")):
                fallback_reply, fb_telemetry = gemini_router.route_reasoning(
                    "Tell me about metabolic reversal",
                    "You are Amura Health coordinator.",
                    [],
                    market_mode="india",
                )
                self.assertIn("Amura Health", fallback_reply)
                self.assertEqual(fb_telemetry["tier_used"], "deterministic_fallback")


class TestConversationEngineLLMIntegration(unittest.TestCase):
    """Verifies ConversationEngine integration with OpenLLMRouter."""

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._env_patch = patch.dict(os.environ, {k: "" for k in _API_KEYS})
        self._env_patch.start()
        ldb._GLOBAL_LEARNING_DB = None
        self._db_patch = patch(
            "src.closer.agent.conversation.get_learning_db",
            side_effect=lambda *a, **kw: ldb.LearningMemoryDB(Path(self._tmp_dir.name) / "llm.db"),
        )
        self._db_patch.start()

    def tearDown(self):
        self._db_patch.stop()
        self._env_patch.stop()
        ldb._GLOBAL_LEARNING_DB = None
        self._tmp_dir.cleanup()

    def test_engine_has_llm_router(self):
        with patch("src.closer.llm.router.settings.GEMINI_API_KEY", None), patch(
            "src.closer.llm.router.settings.GROQ_API_KEY", None
        ), patch("src.closer.llm.router.settings.OPENAI_API_KEY", None), patch(
            "src.closer.llm.router.settings.OPENROUTER_API_KEY", None
        ):
            engine = ConversationEngine(market_mode="india")
        self.assertIsNotNone(engine.llm_router)
        self.assertEqual(engine.dossier.active_llm_model, "llama-3.3-70b")
        self.assertEqual(engine.dossier.llm_parameter_scale, "70 Billion")

    def test_engine_switch_llm_model(self):
        engine = ConversationEngine(market_mode="india")
        info = engine.set_llm_model("bloomz-176b")
        self.assertEqual(info["model_id"], "bloomz-176b")
        self.assertEqual(engine.dossier.active_llm_model, "bloomz-176b")
        self.assertEqual(engine.dossier.llm_parameter_scale, "176 Billion")

        dump = engine.export_dossier().model_dump()
        self.assertEqual(dump["active_llm_model"], "bloomz-176b")
        self.assertEqual(dump["llm_parameter_scale"], "176 Billion")


if __name__ == "__main__":
    unittest.main()
