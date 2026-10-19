"""
Unit & Integration tests for CLOSER AI Luxury Web Console (dashboard.py).
Verifies HTML template rendering, voice sample preview API, turn processing, and dossier sync.
"""

import io
import json
import unittest
from unittest.mock import MagicMock
from src.closer.web.dashboard import DashboardHTTPHandler, HTML_TEMPLATE, MOCK_LEADS


class TestWebDashboardConsole(unittest.TestCase):
    """Test suite for Web Console HTTP handlers and API endpoints."""

    def test_html_template_luxury_elements(self):
        """Verifies HTML template contains Apple/Stripe luxury styling, VAD, and voice dropdown."""
        self.assertIn("CLOSER AI", HTML_TEMPLATE)
        self.assertIn("vadContainer", HTML_TEMPLATE)
        self.assertIn("vad-waves", HTML_TEMPLATE)
        self.assertIn("voiceSelect", HTML_TEMPLATE)
        self.assertIn("testVoiceSample", HTML_TEMPLATE)
        self.assertIn("dossierStatus", HTML_TEMPLATE)
        self.assertIn("intentBar", HTML_TEMPLATE)
        
        # Verify required voices in dropdown
        self.assertIn("en-US-AriaNeural", HTML_TEMPLATE)
        self.assertIn("en-US-GuyNeural", HTML_TEMPLATE)
        self.assertIn("en-US-JennyNeural", HTML_TEMPLATE)
        self.assertIn("en-US-ChristopherNeural", HTML_TEMPLATE)
        self.assertIn("en-US-AvaNeural", HTML_TEMPLATE)
        self.assertIn("en-IN-NeerjaNeural", HTML_TEMPLATE)

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
        self.assertIn("Autonomous Voice Concierge", body)

    def test_get_api_leads(self):
        """Verifies GET /api/leads returns JSON lead list."""
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
        self.assertEqual(data[0]["name"], "Harrison & Claire Sterling")

    def test_post_turn_preview_voice(self):
        """Verifies POST /api/turn with PREVIEW_SAMPLE synthesizes voice preview without corrupting conversation."""
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/api/turn"
        payload = json.dumps({"utterance": "PREVIEW_SAMPLE", "voice": "en-US-GuyNeural"}).encode("utf-8")
        handler.headers = {"Content-Length": str(len(payload))}
        handler.rfile = io.BytesIO(payload)
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_POST()

        handler.send_response.assert_called_with(200)
        resp = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("reply", resp)
        self.assertIn("audio_base64", resp)
        self.assertGreater(len(resp["audio_base64"]), 100)

    def test_post_turn_schedule_friction(self):
        """Verifies POST /api/turn handles off-script schedule friction and updates dossier."""
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/api/turn"
        payload = json.dumps({
            "utterance": "Today is not good, I will come tomorrow",
            "voice": "en-US-AriaNeural"
        }).encode("utf-8")
        handler.headers = {"Content-Length": str(len(payload))}
        handler.rfile = io.BytesIO(payload)
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_POST()

        handler.send_response.assert_called_with(200)
        resp = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("respect your schedule", resp["reply"].lower())
        self.assertEqual(resp["dossier"]["timeframe"], "tomorrow (immediate)")

    def test_post_reset(self):
        """Verifies POST /api/reset resets conversation engine state."""
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

    def test_post_turn_preview_all_six_voices(self):
        """Verifies POST /api/turn with PREVIEW_SAMPLE synthesizes audio across all 6 specified voices."""
        voices = [
            "en-US-AriaNeural",
            "en-US-GuyNeural",
            "en-US-JennyNeural",
            "en-US-ChristopherNeural",
            "en-US-AvaNeural",
            "en-IN-NeerjaNeural"
        ]
        for voice in voices:
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
            self.assertIn("reply", resp)
            self.assertIn("audio_base64", resp)
            self.assertGreater(len(resp["audio_base64"]), 100, f"Voice {voice} returned insufficient audio bytes")

    def test_post_turn_busy_friction(self):
        """Verifies POST /api/turn handles busy constraints and updates dossier with follow-up note."""
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/api/turn"
        payload = json.dumps({
            "utterance": "I am busy right now, contact me later",
            "voice": "en-US-AriaNeural"
        }).encode("utf-8")
        handler.headers = {"Content-Length": str(len(payload))}
        handler.rfile = io.BytesIO(payload)
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_POST()

        handler.send_response.assert_called_with(200)
        resp = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("respect your time", resp["reply"].lower())
        self.assertIn("busy", resp["dossier"]["follow_up_note"].lower())
        self.assertEqual(resp["dossier"]["sentiment_rating"], "Polite / Busy")

    def test_404_routing(self):
        """Verifies unknown GET and POST routes return 404."""
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


if __name__ == "__main__":
    unittest.main()
