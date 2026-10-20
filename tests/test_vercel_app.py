"""
Unit tests for Vercel deployment entrypoints (app.py and api/index.py).
Verifies that app is importable, exports a callable ASGI application,
and that static files, console, and API routes respond accurately.
"""

import asyncio
import os
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


class TestVercelAppEntrypoint(unittest.TestCase):
    """Test suite for Vercel FastAPI / ASGI entrypoint."""

    def test_app_import_and_callable(self):
        """Verifies app.py exists and exports a callable app."""
        import app
        self.assertTrue(hasattr(app, "app"))
        self.assertTrue(callable(app.app))

    def test_api_index_reexports_app(self):
        """Verifies api/index.py re-exports app for Vercel serverless."""
        from api.index import app as vercel_app
        import app
        self.assertIs(vercel_app, app.app)

    def test_pyproject_vercel_entrypoint_matches(self):
        """Verifies pyproject.toml defines [tool.vercel] entrypoint = 'app.py:app'."""
        pyproject_file = ROOT_DIR / "pyproject.toml"
        self.assertTrue(pyproject_file.exists())
        content = pyproject_file.read_text(encoding="utf-8")
        self.assertIn("[tool.vercel]", content)
        self.assertIn('entrypoint = "app.py:app"', content)

    def test_vercel_json_validity(self):
        """Verifies vercel.json exists and contains cleanUrls."""
        vercel_json = ROOT_DIR / "vercel.json"
        self.assertTrue(vercel_json.exists())
        content = vercel_json.read_text(encoding="utf-8")
        self.assertIn("cleanUrls", content)

    def test_asgi_routing_responses(self):
        """Verifies ASGI app responds to HTTP GET requests for root, styles, and js."""
        import app

        async def run_asgi(path: str):
            messages = []

            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}

            async def send(message):
                messages.append(message)

            scope = {
                "type": "http",
                "method": "GET",
                "path": path,
                "headers": [],
            }

            await app.app(scope, receive, send)
            return messages

        # Test root path
        messages = asyncio.run(run_asgi("/"))
        self.assertTrue(any(m.get("type") == "http.response.start" and m.get("status") == 200 for m in messages))
        body_parts = [m.get("body", b"") for m in messages if m.get("type") == "http.response.body"]
        full_body = b"".join(body_parts).decode("utf-8", errors="ignore")
        self.assertIn("Intelligence Designed To Evolve", full_body)

        # Test styles.css
        messages = asyncio.run(run_asgi("/styles.css"))
        self.assertTrue(any(m.get("type") == "http.response.start" and m.get("status") == 200 for m in messages))

        # Test main.js
        messages = asyncio.run(run_asgi("/main.js"))
        self.assertTrue(any(m.get("type") == "http.response.start" and m.get("status") == 200 for m in messages))

        # Test console route
        messages = asyncio.run(run_asgi("/console"))
        self.assertTrue(any(m.get("type") == "http.response.start" and m.get("status") == 200 for m in messages))


if __name__ == "__main__":
    unittest.main()
