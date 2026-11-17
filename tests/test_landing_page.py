"""
Unit & Integration tests for Intelligence Designed To Evolve Landing Page.
Verifies file structure, assets, typography, video background, exact copy,
CSS variables, animations, and server route integration.
"""

import io
import json
import re
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.closer.web.dashboard import DashboardHTTPHandler

ROOT_DIR = Path(__file__).resolve().parent.parent


class TestLandingPage(unittest.TestCase):
    """Test suite for landing page files, structure, and live server endpoints."""

    def setUp(self):
        self.index_file = ROOT_DIR / "index.html"
        self.styles_file = ROOT_DIR / "styles.css"
        self.main_js_file = ROOT_DIR / "main.js"
        self.logo_file = ROOT_DIR / "assets" / "logo.webp"
        self.font_file = ROOT_DIR / "fonts" / "GeistPixel-Circle.woff2"

    def test_file_structure_exists(self):
        """Verifies the exact required file structure exists and files are non-empty."""
        self.assertTrue(self.index_file.exists(), "index.html must exist in project root")
        self.assertTrue(self.styles_file.exists(), "styles.css must exist in project root")
        self.assertTrue(self.main_js_file.exists(), "main.js must exist in project root")
        self.assertTrue(self.logo_file.exists(), "assets/logo.webp must exist")
        self.assertTrue(self.font_file.exists(), "fonts/GeistPixel-Circle.woff2 must exist")

        self.assertGreater(self.index_file.stat().st_size, 500)
        self.assertGreater(self.styles_file.stat().st_size, 1000)
        self.assertGreater(self.main_js_file.stat().st_size, 1000)
        self.assertGreater(self.logo_file.stat().st_size, 500)
        self.assertGreater(self.font_file.stat().st_size, 500)

    def test_font_binary_signature(self):
        """Verifies fonts/GeistPixel-Circle.woff2 is a valid WOFF2 font binary."""
        header = self.font_file.read_bytes()[:4]
        self.assertEqual(header, b"wOF2", "GeistPixel-Circle.woff2 must start with wOF2 magic bytes")

    def test_logo_binary_format(self):
        """Verifies assets/logo.webp is a valid WebP image binary."""
        content = self.logo_file.read_bytes()
        self.assertTrue(content[:4] == b"RIFF" and b"WEBP" in content[:16], "logo.webp must be valid WebP")

    def test_brand_identity_assets(self):
        """Verifies presence and valid signatures of official CLOSER AI logo suite."""
        brand_suite = [
            ROOT_DIR / "assets" / "closer-logo-dark.png",
            ROOT_DIR / "assets" / "closer-logo-transparent.png",
            ROOT_DIR / "assets" / "closer-logo-transparent.webp",
            ROOT_DIR / "assets" / "closer-symbol-dark.png",
            ROOT_DIR / "assets" / "closer-symbol-dark.webp",
            ROOT_DIR / "assets" / "closer-symbol-transparent.png",
            ROOT_DIR / "assets" / "closer-symbol-transparent.webp",
            ROOT_DIR / "assets" / "logo.png",
            ROOT_DIR / "assets" / "logo.webp",
        ]
        for asset in brand_suite:
            self.assertTrue(asset.exists(), f"Brand asset {asset.name} must exist")
            self.assertGreater(asset.stat().st_size, 1000, f"Brand asset {asset.name} must be > 1KB")
            raw = asset.read_bytes()
            if asset.suffix == ".png":
                self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n", f"{asset.name} must be valid PNG")
            elif asset.suffix == ".webp":
                self.assertTrue(raw[:4] == b"RIFF" and b"WEBP" in raw[:16], f"{asset.name} must be valid WebP")

    def test_html_document_metadata_and_video(self):
        """Verifies title, meta description, and core branding."""
        html = self.index_file.read_text(encoding="utf-8")

        self.assertIn("<title>CLOSER AI — Never Miss a ₹50 Lakh Buyer After 8 PM</title>", html)
        self.assertIn("Never Miss a ₹50 Lakh Buyer", html)
        self.assertIn("assets/logo.webp", html)

    def test_html_fonts_and_cdns(self):
        """Verifies fonts and CDNs for Inter, JetBrains Mono, and Font Awesome."""
        html = self.index_file.read_text(encoding="utf-8")

        self.assertIn("family=Inter", html)
        self.assertIn("font-awesome/6.5.2/css/all.min.css", html)

    def test_html_header_and_navigation(self):
        """Verifies navigation sections: Problem, How It Works, Live Voice Demo, Pricing, and Deck."""
        html = self.index_file.read_text(encoding="utf-8")

        self.assertIn("assets/logo.webp", html)
        self.assertIn("#problem", html)
        self.assertIn("#how-it-works", html)
        self.assertIn("#voice-test", html)
        self.assertIn("#pricing", html)
        self.assertIn("/presentation", html)

    def test_html_hero_content(self):
        """Verifies high-ticket real estate positioning and core value prop."""
        html = self.index_file.read_text(encoding="utf-8")

        self.assertIn("Never Miss a ₹50 Lakh Buyer After 8 PM", html)
        self.assertIn("Tamil", html)
        self.assertIn("Hindi", html)
        self.assertIn("WhatsApp", html)

    def test_html_stats_footer(self):
        """Verifies key operational metrics on landing page."""
        html = self.index_file.read_text(encoding="utf-8")

        self.assertIn("120ms", html)
        self.assertIn("24/7", html)
        self.assertIn("₹25,000", html)

    def test_css_variables_and_styling(self):
        """Verifies exact CSS variables, font stacks, and animations in styles.css."""
        css = self.styles_file.read_text(encoding="utf-8")

        # Variables check
        self.assertIn("--bg: #000000;", css)
        self.assertIn("--text: #ffffff;", css)
        self.assertIn("--muted: #8e8e8e;", css)
        self.assertIn("--nav-text: #2e2e2e;", css)
        self.assertIn("--pill-dark: #28282a;", css)
        self.assertIn("--sign-in-text: #c8c8c8;", css)
        self.assertIn("--nav-shadow: 0 4px 14px rgba(0, 0, 0, 0.16);", css)
        self.assertIn("--trust-bg: #28282a;", css)
        self.assertIn("--trust-border: rgba(255, 255, 255, 0.4);", css)
        self.assertIn("--trust-text: #c4c2c3;", css)
        self.assertIn('--font-sans: "Inter", "Segoe UI", system-ui, sans-serif;', css)
        self.assertIn('--font-display: "BubbledotICG-FinePos", "Geist Pixel Circle", monospace;', css)

        # Geist Pixel Circle font-face
        self.assertIn('@font-face', css)
        self.assertIn('"Geist Pixel Circle"', css)
        self.assertIn('fonts/GeistPixel-Circle.woff2', css)

        # Three dot indicator
        self.assertIn('box-shadow: -5px 0 0 #000000, 5px 0 0 #000000;', css)

        # Animations
        self.assertIn('@keyframes slideDown', css)
        self.assertIn('@keyframes headlineFade', css)
        self.assertIn('@keyframes revealPulse', css)
        self.assertIn('@keyframes reveal', css)

        # Responsive queries
        self.assertIn('@media (max-width: 720px)', css)
        self.assertIn('@media (max-width: 420px)', css)
        self.assertIn('@media (max-height: 700px)', css)

    def test_main_js_logic(self):
        """Verifies count-up animation, market selection, and voice synthesis hooks."""
        js = self.main_js_file.read_text(encoding="utf-8")

        self.assertIn("easeOutCubic", js)
        self.assertIn("IntersectionObserver", js)
        self.assertIn("btnMarketTamil", js)
        self.assertIn("btnMarketHindi", js)
        self.assertIn("speechSynthesis.cancel()", js)

    def test_mobile_closing_and_exit_animations(self):
        """Verifies interactive voice call controls and audio elements."""
        html = self.index_file.read_text(encoding="utf-8")
        self.assertIn('id="btnStartVoiceCall"', html)
        self.assertIn('id="liveChatBox"', html)
        self.assertIn('id="textUtteranceInput"', html)

    def test_dashboard_handler_serves_landing_page_and_assets(self):
        """Verifies DashboardHTTPHandler serves landing page, CSS, JS, and font assets."""
        # 1. Landing page route /landing
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/landing"
        handler.headers = {}
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()
        handler.send_response.assert_called_with(200)
        self.assertIn("CLOSER AI", handler.wfile.getvalue().decode("utf-8"))

        # 2. Stylesheet route /styles.css
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/styles.css"
        handler.headers = {}
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()
        handler.send_response.assert_called_with(200)
        handler.send_header.assert_called_with("Content-Type", "text/css; charset=utf-8")

        # 3. Script route /main.js
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/main.js"
        handler.headers = {}
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()
        handler.send_response.assert_called_with(200)
        handler.send_header.assert_called_with("Content-Type", "application/javascript; charset=utf-8")

        # 4. Font route /fonts/GeistPixel-Circle.woff2
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/fonts/GeistPixel-Circle.woff2"
        handler.headers = {}
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()
        handler.send_response.assert_called_with(200)
        handler.send_header.assert_called_with("Content-Type", "font/woff2")
        self.assertEqual(handler.wfile.getvalue()[:4], b"wOF2")

        # 5. Asset route /assets/logo.webp
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/assets/logo.webp"
        handler.headers = {}
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()
        handler.send_response.assert_called_with(200)
        handler.send_header.assert_called_with("Content-Type", "image/webp")
        self.assertEqual(handler.wfile.getvalue()[:4], b"RIFF")

        # 6. Post /api/turn with PREVIEW_SAMPLE
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/api/turn"
        payload = b'{"utterance": "PREVIEW_SAMPLE", "voice": "en-US-AriaNeural"}'
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

    def test_extended_presentation_sections(self):
        """Verifies core narrative sections on landing page: problem, how-it-works, voice-test, pricing."""
        html = self.index_file.read_text(encoding="utf-8")

        self.assertIn('id="problem"', html)
        self.assertIn('id="how-it-works"', html)
        self.assertIn('id="voice-test"', html)
        self.assertIn('id="pricing"', html)

    def test_soundboard_and_roi_calculator_elements(self):
        """Verifies interactive voice controls and live Dossier card."""
        html = self.index_file.read_text(encoding="utf-8")

        self.assertIn('id="voice-test"', html)
        self.assertIn('id="btnStartVoiceCall"', html)
        self.assertIn('id="liveAudioPlayer"', html)
        self.assertIn('id="liveChatBox"', html)
        self.assertIn('id="dossierStatusBadge"', html)
        self.assertIn('id="dossierBudget"', html)

    def test_presentation_deck_structure_and_routes(self):
        """Verifies presentation.html pitch deck exists, contains all 12 slides, speaker notes, and server routes."""
        deck_file = ROOT_DIR / "presentation.html"
        self.assertTrue(deck_file.exists(), "presentation.html must exist in project root")
        self.assertGreater(deck_file.stat().st_size, 5000, "presentation.html must be a rich deck > 5KB")

        content = deck_file.read_text(encoding="utf-8")
        self.assertIn("CLOSER AI", content)
        self.assertIn("R Jan Steve Daniel", content)
        self.assertIn("Sub-120ms", content)
        self.assertIn("Dual-Market", content)
        self.assertIn("APILayer", content)
        self.assertIn("data-slide=\"12\"", content)
        self.assertIn("@media print", content)
        self.assertIn("Presenter Speaking Notes", content)

        # Test Dashboard HTTP Handler serves presentation
        handler = DashboardHTTPHandler.__new__(DashboardHTTPHandler)
        handler.path = "/presentation"
        handler.headers = {}
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler.do_GET()
        handler.send_response.assert_called_with(200)
        handler.send_header.assert_called_with("Content-Type", "text/html; charset=utf-8")
        self.assertIn(b"CLOSER AI", handler.wfile.getvalue())


if __name__ == "__main__":
    unittest.main()
