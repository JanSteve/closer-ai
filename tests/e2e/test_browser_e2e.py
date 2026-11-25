"""
tests/e2e/test_browser_e2e.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pytest wrapper for dual-viewport headless Chromium E2E checks (tests/e2e/playwright_e2e.py).
Uses sys.executable if Playwright is installed, otherwise falls back to Python 3.13
(/Library/Frameworks/Python.framework/Versions/3.13/bin/python3).
Calls pytest.skip ONLY when SKIP_BROWSER_E2E=1 or Playwright+Chromium runtime is absent.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_PATH = Path(__file__).resolve().with_name("playwright_e2e.py")
PYTHON313_CANDIDATE = "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
DEFAULT_CHROMIUM = (
    "/Users/janstevedaniel/Library/Caches/ms-playwright/"
    "chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell"
)


def _find_playwright_python() -> Optional[str]:
    if importlib.util.find_spec("playwright") is not None:
        return sys.executable
    if Path(PYTHON313_CANDIDATE).is_file():
        probe = subprocess.run(
            [PYTHON313_CANDIDATE, "-c", "import playwright, uvicorn, fastapi"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if probe.returncode == 0:
            return PYTHON313_CANDIDATE
    return None


def test_f10_playwright_desktop_and_mobile_e2e(tmp_path: Path):
    if os.environ.get("SKIP_BROWSER_E2E") == "1":
        pytest.skip("SKIP_BROWSER_E2E=1 set")

    py_bin = _find_playwright_python()
    if not py_bin:
        pytest.skip("Playwright + uvicorn + fastapi runtime not available")

    chromium_env = os.environ.get("CHROMIUM_EXECUTABLE_PATH")
    if chromium_env and not Path(chromium_env).is_file():
        pytest.skip(f"CHROMIUM_EXECUTABLE_PATH missing: {chromium_env}")
    if not chromium_env and not Path(DEFAULT_CHROMIUM).is_file():
        # Check if Playwright default browser exists
        check = subprocess.run(
            [py_bin, "-c", "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(headless=True); b.close(); p.stop()"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if check.returncode != 0:
            pytest.skip("No Playwright Chromium binary available")

    report_file = tmp_path / "playwright_report.json"
    cmd = [py_bin, str(SCRIPT_PATH), "--viewport", "both", "--json-out", str(report_file)]
    if base_url := os.environ.get("PLAYWRIGHT_BASE_URL"):
        cmd.extend(["--base-url", base_url])

    proc = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=120)
    if proc.returncode == 2:
        pytest.skip(f"Playwright runtime unavailable: {proc.stdout} {proc.stderr}")

    summary = json.loads(report_file.read_text(encoding="utf-8")) if report_file.exists() else {}
    assert proc.returncode == 0, (
        f"Playwright dual-viewport E2E failed (rc={proc.returncode}):\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}\nSUMMARY:\n{json.dumps(summary, indent=2)}"
    )
