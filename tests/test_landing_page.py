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

    def test_html_document_metadata_and_video(self):
        """Verifies title, background video, and exact CloudFront source URL."""
        html = self.index_file.read_text(encoding="utf-8")

        self.assertIn("<title>Intelligence Designed To Evolve</title>", html)
        self.assertIn("class=\"bg\"", html)
        self.assertIn("class=\"bg-video\"", html)
        self.assertIn("autoplay", html)
        self.assertIn("muted", html)
        self.assertIn("loop", html)
        self.assertIn("playsinline", html)

        expected_video_url = (
            "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/"
            "hf_20260809_012548_ef22562c-c0ae-4816-ad9d-f8922af4e6a7.mp4"
        )
        self.assertIn(expected_video_url, html)

    def test_html_fonts_and_cdns(self):
        """Verifies exact CDNs for Inter, BubbledotICG-FinePos, and Font Awesome 6.5.2."""
        html = self.index_file.read_text(encoding="utf-8")

        self.assertIn("family=Inter:wght@400;500;600", html)
        self.assertIn("family=BubbledotICG-FinePos", html)
        self.assertIn("font-awesome/6.5.2/css/all.min.css", html)
        self.assertIn("sha512-SnH5WK+bZxgPHs44uWIX+LLJAJ9/2PkPKZ5QiAj6Ta86w+fsb2TkcmfRyVX3pBnMFcV7oQPJkl9QevSCWr3W6A==", html)

    def test_html_header_and_navigation(self):
        """Verifies desktop navigation, active indicators, and mobile burger button."""
        html = self.index_file.read_text(encoding="utf-8")

        self.assertIn("assets/logo.webp", html)
        self.assertIn('width="52"', html)
        self.assertIn('height="52"', html)
        self.assertIn("Home", html)
        self.assertIn("Product", html)
        self.assertIn("Case Studies", html)
        self.assertIn("Contact", html)
        self.assertIn("Sign in", html)
        self.assertIn('id="burgerBtn"', html)
        self.assertIn('id="mobileSheet"', html)
        self.assertIn('id="mobileOverlay"', html)

    def test_html_hero_content(self):
        """Verifies exact trust avatars, brands, headline lines, subhead copy, and CTA."""
        html = self.index_file.read_text(encoding="utf-8")

        self.assertIn("fa-brands fa-microsoft", html)
        self.assertIn("fa-brands fa-amazon", html)
        self.assertIn("fa-brands fa-google", html)
        self.assertIn("Trusted by 2000+ Enterprises", html)

        self.assertIn(">Intelligence<", html)
        self.assertIn(">Designed To Evolve<", html)

        expected_subhead = (
            "Build applications that reason, adapt and collaborate using a modular\n"
            "        AI platform designed for production."
        )
        normalized_html = re.sub(r"\s+", " ", html)
        normalized_subhead = re.sub(r"\s+", " ", expected_subhead)
        self.assertIn(normalized_subhead, normalized_html)

        self.assertIn("Get Started", html)

    def test_html_stats_footer(self):
        """Verifies 4 stats with exact glyphs, targets, suffixes, decimals, and labels."""
        html = self.index_file.read_text(encoding="utf-8")

        self.assertIn("Inference Time", html)
        self.assertIn("Platform Uptime", html)
        self.assertIn("Autonomous Runtime", html)
        self.assertIn("Context Windows", html)

        self.assertIn('data-target="120"', html)
        self.assertIn('data-suffix="ms"', html)

        self.assertIn('data-target="99.99"', html)
        self.assertIn('data-suffix="%"', html)

        self.assertIn('data-target="24"', html)
        self.assertIn('data-suffix="/7"', html)

        self.assertIn('data-target="2.4"', html)
        self.assertIn('data-suffix="M"', html)

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
        """Verifies count-up animation, mobile navigation, and dual-market demo logic."""
        js = self.main_js_file.read_text(encoding="utf-8")

        self.assertIn("easeOutCubic", js)
        self.assertIn("IntersectionObserver", js)
        self.assertIn("burgerBtn", js)
        self.assertIn("mobileSheet", js)
        self.assertIn("btnMarketUSA", js)
        self.assertIn("btnMarketIndia", js)
        self.assertIn("en-US-AriaNeural", js)
        self.assertIn("en-IN-NeerjaNeural", js)
        self.assertIn("btnVoicePreview", js)
        self.assertIn("is-closing", js)
        self.assertIn("speechSynthesis.cancel()", js)

    def test_mobile_closing_and_exit_animations(self):
        """Verifies closing keyframes, stacking z-indexes, and mobile done button exist."""
        css = self.styles_file.read_text(encoding="utf-8")
        html = self.index_file.read_text(encoding="utf-8")

        self.assertIn("@keyframes overlayOut", css)
        self.assertIn("@keyframes menuOut", css)
        self.assertIn("@keyframes modalFadeOut", css)
        self.assertIn("@keyframes modalSlideDown", css)

        # Header sits above overlay on mobile
        self.assertIn("z-index: 1001;", css)

        # Mobile input auto-zoom prevention (>= 16px)
        self.assertIn("font-size: 16px;", css)

        # Mobile done button
        self.assertIn('id="modalMobileDoneBtn"', html)
        self.assertIn('id="btnVoicePreview"', html)

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
        self.assertIn("Intelligence Designed To Evolve", handler.wfile.getvalue().decode("utf-8"))

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
        self.assertIn("luxury real estate concierge", resp["reply"].lower())
        self.assertIn("audio_base64", resp)

    def test_extended_presentation_sections(self):
        """Verifies the extended presentation sections: Product, Architecture, How to Use, Soundboard, ROI, etc."""
        html = self.index_file.read_text(encoding="utf-8")

        # Sections
        self.assertIn('id="product"', html)
        self.assertIn('id="how-it-works"', html)
        self.assertIn('id="how-to-use"', html)
        self.assertIn('id="markets"', html)
        self.assertIn('id="voice-studio"', html)
        self.assertIn('id="benchmarks"', html)
        self.assertIn('id="roi"', html)
        self.assertIn('id="integrations"', html)
        self.assertIn('id="cases"', html)
        self.assertIn('id="compliance"', html)
        self.assertIn('id="contact"', html)

        # Core copy checks
        self.assertIn("The 4-Stage Autonomous Telephony Pipeline", html)
        self.assertIn("Sub-120ms Neural Latency", html)
        self.assertIn("Deterministic Pydantic Dossiers", html)
        self.assertIn("Vanguard Luxury Realty", html)
        self.assertIn("Prestige &amp; Sobha Channel Alliance", html)
        self.assertIn("SOC-2 Type II", html)
        self.assertIn("100% RERA Compliant", html)

    def test_soundboard_and_roi_calculator_elements(self):
        """Verifies interactive soundboard controls and ROI calculator inputs."""
        html = self.index_file.read_text(encoding="utf-8")
        js = self.main_js_file.read_text(encoding="utf-8")

        self.assertIn('id="soundboardPlayBtn"', html)
        self.assertIn('id="studioWaveform"', html)
        self.assertIn('id="sliderLeads"', html)
        self.assertIn('id="sliderCommission"', html)
        self.assertIn('id="sliderConv"', html)
        self.assertIn('id="roiRevenue"', html)

        # JS functions
        self.assertIn("showMarketTab", js)
        self.assertIn("selectStudioVoice", js)
        self.assertIn("selectStudioScenario", js)
        self.assertIn("runStudioSimulation", js)
        self.assertIn("setRoiCurrency", js)
        self.assertIn("updateRoiCalc", js)


if __name__ == "__main__":
    unittest.main()
