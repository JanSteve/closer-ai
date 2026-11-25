"""
Unit & Integration tests for CLOSER AI Amura Health Web Console (src/closer/web/dashboard.py).
Verifies HTML template rendering, clinical voice preview API, turn emotion/safety/consent output,
APILayer endpoints, and strict network/DB isolation.
"""

import io
import json
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import src.closer.memory.learning_db as ldb
from src.closer.agent.conversation import ConversationEngine
from src.closer.web.dashboard import DashboardHTTPHandler, HTML_TEMPLATE, MOCK_LEADS

_API_KEYS = (
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "SARVAM_API_KEY",
    "ELEVENLABS_API_KEY",
    "CARTESIA_API_KEY",
    "APILAYER_API_KEY",
)


def _make_dummy_wav(sample_rate: int = 24000, num_frames: int = 4000) -> bytes:
    data_size = num_frames * 2
    header = bytearray(b"RIFF")
    header.extend(struct.pack("<I", data_size + 36))
    header.extend(b"WAVEfmt ")
    header.extend(struct.pack("<I", 16))
    header.extend(struct.pack("<H", 1))
    header.extend(struct.pack("<H", 1))
    header.extend(struct.pack("<I", sample_rate))
    header.extend(struct.pack("<I", sample_rate * 2))
    header.extend(struct.pack("<H", 2))
    header.extend(struct.pack("<H", 16))
    header.extend(b"data")
    header.extend(struct.pack("<I", data_size))
    return bytes(header) + (b"\x10\x00" * num_frames)


class TestWebDashboardConsole(unittest.TestCase):
    """Test suite for Amura Health Web Console HTTP handlers and API endpoints."""

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._env_patch = patch.dict(os.environ, {k: "" for k in _API_KEYS})
        self._env_patch.start()
        ldb._GLOBAL_LEARNING_DB = None
        self._db_patch = patch(
            "src.closer.agent.conversation.get_learning_db",
            side_effect=lambda *a, **kw: ldb.LearningMemoryDB(Path(self._tmp_dir.name) / "dash.db"),
        )
        self._db_patch.start()
        self._ldb_patch = patch(
            "src.closer.memory.learning_db.get_learning_db",
            side_effect=lambda *a, **kw: ldb.LearningMemoryDB(Path(self._tmp_dir.name) / "dash.db"),
        )
        self._ldb_patch.start()

        self._orig_engine = DashboardHTTPHandler.conversation_engine
        self._orig_tts = DashboardHTTPHandler.tts_engine
        self._orig_apilayer = DashboardHTTPHandler.apilayer_client

        DashboardHTTPHandler.conversation_engine = ConversationEngine(
            market_mode="india",
            sector="amura_metabolic",
            business_name="Amura Health",
        )
        mock_tts = MagicMock()
        mock_tts.last_provider_used = "Studio Broadcast Neural (Mocked)"
        mock_tts.synthesize_sync.return_value = (_make_dummy_wav(), 0.02)
        DashboardHTTPHandler.tts_engine = mock_tts

        from src.closer.integrations.apilayer import APILayerUnifiedClient

        DashboardHTTPHandler.apilayer_client = APILayerUnifiedClient(api_key="")

    def tearDown(self):
        DashboardHTTPHandler.conversation_engine = self._orig_engine
        DashboardHTTPHandler.tts_engine = self._orig_tts
        DashboardHTTPHandler.apilayer_client = self._orig_apilayer
        self._ldb_patch.stop()
        self._db_patch.stop()
        self._env_patch.stop()
        ldb._GLOBAL_LEARNING_DB = None
        self._tmp_dir.cleanup()

    def test_html_template_clinical_and_voice_elements(self):
        """Verifies HTML template contains Amura Health UI, VAD, Tamil/Hindi/English voices, and zero real estate."""
        self.assertIn("CLOSER AI", HTML_TEMPLATE)
        self.assertIn("Amura Health", HTML_TEMPLATE)
        self.assertIn("vadContainer", HTML_TEMPLATE)
        self.assertIn("voiceSelect", HTML_TEMPLATE)
        self.assertIn("testVoiceSample", HTML_TEMPLATE)
        self.assertIn("dossierStatus", HTML_TEMPLATE)
        self.assertIn("intentBar", HTML_TEMPLATE)
        for v in (
            "en-IN-NeerjaExpressiveNeural",
            "ta-IN-PallaviNeural",
            "ta-IN-ValluvarNeural",
            "hi-IN-SwaraNeural",
            "hi-IN-MadhurNeural",
            "en-US-AvaNeural",
        ):
            self.assertIn(v, HTML_TEMPLATE)
        for forbidden in ("Bel Air", "Beverly Hills", "Daniel & Associates", "RERA", "3 BHK", "real_estate_notation"):
            self.assertNotIn(forbidden, HTML_TEMPLATE)

    def test_get_dashboard_root(self):
        """Verifies GET / returns 200 with UTF-8 HTML."""
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/"
        handler.headers = {}
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()

        handler.send_response.assert_called_with(200)
        handler.send_header.assert_called_with("Content-Type", "text/html; charset=utf-8")
        body = handler.wfile.getvalue().decode("utf-8")
        self.assertIn("CLOSER AI", body)

    def test_get_console_route(self):
        """Verifies GET /console and /dashboard return 200 with Amura Health Console HTML."""
        for path in ("/console", "/dashboard"):
            handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
            handler.path = path
            handler.headers = {}
            handler.wfile = io.BytesIO()
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()

            handler.do_GET()

            handler.send_response.assert_called_with(200)
            body = handler.wfile.getvalue().decode("utf-8")
            self.assertIn("Amura Health", body)
            self.assertIn("Clinical Care Concierge", body)

    def test_get_api_leads(self):
        """Verifies GET /api/leads returns Amura Health patient pipeline records."""
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/api/leads"
        handler.headers = {}
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()

        handler.send_response.assert_called_with(200)
        data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(len(data), len(MOCK_LEADS))
        self.assertEqual(data[0]["name"], "Priya Raman")

    def test_post_turn_preview_voice_trilingual(self):
        """Verifies POST /api/turn PREVIEW_SAMPLE across English, Tamil, and Hindi voices."""
        for voice, expected_substr in (
            ("en-IN-NeerjaExpressiveNeural", "Amura Health"),
            ("ta-IN-PallaviNeural", "வணக்கம்"),
            ("hi-IN-SwaraNeural", "नमस्ते"),
        ):
            handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
            handler.path = "/api/turn"
            payload = json.dumps({"utterance": "PREVIEW_SAMPLE", "voice": voice}).encode("utf-8")
            handler.headers = {"Content-Length": str(len(payload))}
            handler.rfile = io.BytesIO(payload)
            handler.wfile = io.BytesIO()
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()

            handler.do_POST()
            handler.send_response.assert_called_with(200)
            resp = json.loads(handler.wfile.getvalue().decode("utf-8"))
            self.assertIn(expected_substr, resp["reply"])
            self.assertGreater(len(resp["audio_base64"]), 100)

    def test_post_turn_emotion_safety_and_schedule_friction(self):
        """Verifies /api/turn populates emotion, safety_flag, emergency_108, consent_status, and follow_up_note."""
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/api/turn"
        payload = json.dumps(
            {"utterance": "My HbA1c is 8.4 and I am really worried, can I book Saturday 11 AM?", "voice": "en-IN-NeerjaExpressiveNeural"}
        ).encode("utf-8")
        handler.headers = {"Content-Length": str(len(payload))}
        handler.rfile = io.BytesIO(payload)
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_POST()
        handler.send_response.assert_called_with(200)
        resp = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(resp["detected_emotion"], "anxious")
        self.assertEqual(resp["safety_flag"], "safe")
        self.assertFalse(resp["emergency_108"])
        self.assertIn(resp["consent_status"], ("pending", "granted", "declined", "emergency_exempt_section_7f"))
        self.assertTrue(bool(resp["dossier"]["follow_up_note"]))

    def test_post_turn_browser_fallback_when_audio_empty(self):
        """Verifies /api/turn returns empty audio_base64 and tts_fallback_used=True when TTS yields b''."""
        DashboardHTTPHandler.tts_engine.synthesize_sync.return_value = (b"", 0.01)
        DashboardHTTPHandler.tts_engine.last_provider_used = "browser_fallback"

        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/api/turn"
        payload = json.dumps({"utterance": "I am in a meeting, call after 6 PM", "voice": "en-IN-NeerjaExpressiveNeural"}).encode("utf-8")
        handler.headers = {"Content-Length": str(len(payload))}
        handler.rfile = io.BytesIO(payload)
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_POST()
        resp = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(resp["audio_base64"], "")
        self.assertEqual(resp["tts_provider"], "browser_fallback")
        self.assertTrue(resp["tts_fallback_used"])

    def test_post_reset(self):
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/api/reset"
        handler.headers = {"Content-Length": "0"}
        handler.rfile = io.BytesIO(b"")
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_POST()
        handler.send_response.assert_called_with(200)
        resp = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertTrue(resp["success"])
        self.assertIn("Amura Health", resp["greeting"])

    def test_404_routing(self):
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/api/unknown"
        handler.headers = {}
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()
        handler.send_response.assert_called_with(404)
        handler.do_POST()
        handler.send_response.assert_called_with(404)

    def test_api_llm_models_and_selection_endpoints(self):
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/api/llm_models"
        handler.headers = {}
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()
        resp = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertTrue(any(m["id"] == "bloomz-176b" for m in resp["models"]))

        post_handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        post_handler.path = "/api/llm_select"
        body = json.dumps({"model_id": "bloomz-176b"}).encode("utf-8")
        post_handler.headers = {"Content-Length": str(len(body))}
        post_handler.rfile = io.BytesIO(body)
        post_handler.wfile = io.BytesIO()
        post_handler.send_response = MagicMock()
        post_handler.send_header = MagicMock()
        post_handler.end_headers = MagicMock()

        post_handler.do_POST()
        post_resp = json.loads(post_handler.wfile.getvalue().decode("utf-8"))
        self.assertTrue(post_resp["success"])
        self.assertEqual(post_resp["model"]["model_id"], "bloomz-176b")

    def test_api_enrich_endpoints(self):
        """Verifies APILayer Unified Suite endpoints return clinical Chennai & healthcare FX payloads."""
        post_handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        post_handler.path = "/api/enrich/phone"
        body = json.dumps({"phone": "+91-98400-12345"}).encode("utf-8")
        post_handler.headers = {"Content-Length": str(len(body))}
        post_handler.rfile = io.BytesIO(body)
        post_handler.wfile = io.BytesIO()
        post_handler.send_response = MagicMock()
        post_handler.send_header = MagicMock()
        post_handler.end_headers = MagicMock()
        post_handler.do_POST()
        phone_resp = json.loads(post_handler.wfile.getvalue().decode("utf-8"))
        self.assertTrue(phone_resp["valid"])
        self.assertIn("Chennai", phone_resp["location"])

        fx_handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        fx_handler.path = "/api/enrich/currency"
        fx_body = json.dumps({"amount": 1500, "from_curr": "USD", "to_curr": "INR"}).encode("utf-8")
        fx_handler.headers = {"Content-Length": str(len(fx_body))}
        fx_handler.rfile = io.BytesIO(fx_body)
        fx_handler.wfile = io.BytesIO()
        fx_handler.send_response = MagicMock()
        fx_handler.send_header = MagicMock()
        fx_handler.end_headers = MagicMock()
        fx_handler.do_POST()
        fx_resp = json.loads(fx_handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(fx_resp["to_currency"], "INR")
        self.assertIn("Lakhs", fx_resp["healthcare_notation"])

    def test_post_market_mode_hindi_and_tamil(self):
        for mode, expected_token in (("hindi", "नमस्ते"), ("tamil", "வணக்கம்")):
            handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
            handler.path = "/api/market_mode"
            payload = json.dumps({"mode": mode}).encode("utf-8")
            handler.headers = {"Content-Length": str(len(payload))}
            handler.rfile = io.BytesIO(payload)
            handler.wfile = io.BytesIO()
            handler.send_response = MagicMock()
            handler.send_header = MagicMock()
            handler.end_headers = MagicMock()

            handler.do_POST()
            handler.send_response.assert_called_with(200)
            resp = json.loads(handler.wfile.getvalue().decode("utf-8"))
            self.assertTrue(resp["success"])
            self.assertIn(expected_token, resp["greeting"])
            self.assertIn("Amura Health", resp["greeting"])

    def test_post_turn_hindi_clinical_consultation(self):
        market_handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        market_handler.path = "/api/market_mode"
        m_payload = json.dumps({"mode": "hindi"}).encode("utf-8")
        market_handler.headers = {"Content-Length": str(len(m_payload))}
        market_handler.rfile = io.BytesIO(m_payload)
        market_handler.wfile = io.BytesIO()
        market_handler.send_response = MagicMock()
        market_handler.send_header = MagicMock()
        market_handler.end_headers = MagicMock()
        market_handler.do_POST()

        turn_handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        turn_handler.path = "/api/turn"
        payload = json.dumps(
            {
                "utterance": "मुझे अमूरा हेल्थ में मेटाबोलिक कंसल्टेशन बुक करना है, क्या शनिवार दोपहर 2 बजे स्लॉट उपलब्ध है?",
                "voice": "hi-IN-SwaraNeural",
            }
        ).encode("utf-8")
        turn_handler.headers = {"Content-Length": str(len(payload))}
        turn_handler.rfile = io.BytesIO(payload)
        turn_handler.wfile = io.BytesIO()
        turn_handler.send_response = MagicMock()
        turn_handler.send_header = MagicMock()
        turn_handler.end_headers = MagicMock()

        turn_handler.do_POST()
        resp = json.loads(turn_handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("reply", resp)
        self.assertIn("dossier", resp)
        self.assertGreater(len(resp["audio_base64"]), 100)


if __name__ == "__main__":
    unittest.main()
