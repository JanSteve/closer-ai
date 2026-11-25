#!/usr/bin/env python3
"""
tests/e2e/playwright_e2e.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Headless Chromium dual-viewport (Desktop 1440x900 + Mobile 390x844) E2E verifier
for CLOSER AI — Amura Health (Velachery, Chennai) Healthcare Showcase.

Usage:
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 tests/e2e/playwright_e2e.py
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 tests/e2e/playwright_e2e.py --base-url https://closer-ai-tawny.vercel.app
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CACHED_CHROMIUM = (
    "/Users/janstevedaniel/Library/Caches/ms-playwright/"
    "chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell"
)

REAL_ESTATE_PATTERNS = [
    r"\bpenthouse\b",
    r"\b3\s*bhk\b",
    r"\brera\b",
    r"\bbel\s*air\b",
    r"\breal\s*estate\b",
    r"\bomr\s+grand\b",
    r"\bgrand\s+omr\b",
    r"\bbuyer\s+dossier\b",
]


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_for_health(base_url: str, timeout_sec: float = 20.0) -> None:
    deadline = time.time() + timeout_sec
    last_err = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/api/health", timeout=2.0) as resp:
                if resp.status == 200:
                    return
        except Exception as exc:
            last_err = exc
        time.sleep(0.25)
    raise RuntimeError(f"Server at {base_url} did not become healthy within {timeout_sec}s: {last_err}")


def _resolve_chromium_executable() -> Optional[str]:
    env_path = os.getenv("CHROMIUM_EXECUTABLE_PATH")
    if env_path and Path(env_path).is_file():
        return env_path
    if Path(DEFAULT_CACHED_CHROMIUM).is_file():
        return DEFAULT_CACHED_CHROMIUM
    return None


def _check_no_real_estate(text: str, label: str, errors: List[str]) -> None:
    low = (text or "").lower()
    for pat in REAL_ESTATE_PATTERNS:
        m = re.search(pat, low, re.IGNORECASE)
        if m:
            errors.append(f"Leftover real-estate term '{m.group(0)}' in {label}")


def _run_viewport_suite(browser: Any, base_url: str, viewport_name: str) -> Dict[str, Any]:
    is_mobile = viewport_name == "mobile"
    context_kwargs: Dict[str, Any] = {
        "viewport": {"width": 390, "height": 844} if is_mobile else {"width": 1440, "height": 900},
    }
    if is_mobile:
        context_kwargs.update({"is_mobile": True, "has_touch": True})

    context = browser.new_context(**context_kwargs)
    page = context.new_page()

    console_errors: List[str] = []
    page_errors: List[str] = []
    http_errors: List[str] = []
    request_failures: List[str] = []
    assertions_failed: List[str] = []

    def _on_console(msg):
        if msg.type == "error":
            console_errors.append(msg.text)

    def _on_pageerror(err):
        page_errors.append(str(err))

    def _on_response(resp):
        if resp.status >= 400:
            # Ignore deliberate negative test call if triggered, otherwise record
            http_errors.append(f"{resp.status} {resp.url}")

    def _on_requestfailed(req):
        failure = str(req.failure or "")
        if "ERR_ABORTED" in failure and req.url.endswith(".mp4"):
            return
        request_failures.append(f"{req.url}: {failure}")

    page.on("console", _on_console)
    page.on("pageerror", _on_pageerror)
    page.on("response", _on_response)
    page.on("requestfailed", _on_requestfailed)

    try:
        # 1. Load Landing Page
        resp = page.goto(base_url, wait_until="domcontentloaded", timeout=25000)
        if not resp or resp.status != 200:
            assertions_failed.append(f"Landing GET failed: {resp.status if resp else 'no response'}")
        page.wait_for_timeout(600)

        body_text = page.locator("body").inner_text()
        _check_no_real_estate(body_text, f"{viewport_name} landing", assertions_failed)
        if "amura" not in body_text.lower():
            assertions_failed.append(f"{viewport_name} landing missing 'Amura' healthcare branding")

        # 2. Scroll & Header Navigation Pointer-Interception Check
        page.locator("#voice-studio").scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        if not is_mobile:
            try:
                page.locator("#desktopSignInBtn").click(timeout=4000)
            except Exception as exc:
                assertions_failed.append(f"Desktop #desktopSignInBtn click intercepted/failed: {exc}")
        else:
            try:
                page.locator("#burgerBtn").click(timeout=4000)
                page.wait_for_timeout(200)
                page.locator("#mobileSignInBtn").click(timeout=4000)
            except Exception as exc:
                assertions_failed.append(f"Mobile nav click failed: {exc}")

        # 3. Soundboard (#voice-studio): Voice Pills, Cadence, Acoustic Mode & Play
        page.locator("#voice-studio").scroll_into_view_if_needed()
        for v in ("english", "tamil", "hindi"):
            pill = page.locator(f'.voice-pill[data-voice="{v}"]')
            if pill.count() > 0:
                pill.first.click(timeout=3000)
                page.wait_for_timeout(150)

        cadence_pills = page.locator(".cadence-pill")
        if cadence_pills.count() > 0:
            cadence_pills.first.click(timeout=3000)
        if page.locator("#btnAcousticCellular").count() > 0:
            page.locator("#btnAcousticCellular").click(timeout=3000)
        if page.locator("#btnAcousticStudio").count() > 0:
            page.locator("#btnAcousticStudio").click(timeout=3000)

        visible_scen = page.locator(".scenario-btn:visible")
        if visible_scen.count() > 0:
            visible_scen.first.click(timeout=3000)
        if page.locator("#soundboardPlayBtn").count() > 0:
            page.locator("#soundboardPlayBtn").click(timeout=4000)
            page.wait_for_timeout(500)
            speech_txt = page.locator("#studioSpeechText").inner_text()
            if not speech_txt.strip():
                assertions_failed.append(f"{viewport_name} #studioSpeechText remained empty after play")

        # 4. ROI Calculator (#roi)
        if page.locator("#roi").count() > 0:
            page.locator("#roi").scroll_into_view_if_needed()
            if page.locator("#currINR").count() > 0:
                page.locator("#currINR").click(timeout=3000)
            if page.locator("#sliderLeads").count() > 0:
                page.locator("#sliderLeads").fill("1000")
                page.locator("#sliderLeads").dispatch_event("input")
            page.wait_for_timeout(150)
            for out_id in ("#roiShowings", "#roiDeals", "#roiRevenue", "#roiHours"):
                val = page.locator(out_id).inner_text().strip()
                if not val or "nan" in val.lower() or "undefined" in val.lower():
                    assertions_failed.append(f"{viewport_name} ROI output {out_id} invalid: '{val}'")

        # 5. Interactive #demoModal Multi-turn + Emotion + 108 Safety
        if page.locator("#openLiveCallFromStudio").count() > 0:
            page.locator("#openLiveCallFromStudio").click(timeout=4000)
            page.wait_for_timeout(300)
            for btn_id in ("#btnMarketTamil", "#btnMarketUSA"):
                if page.locator(btn_id).count() > 0:
                    page.locator(btn_id).click(timeout=3000)
                    page.wait_for_timeout(150)

            for utt, expect_108 in (
                ("I am worried about my HbA1c 8.5% and want an Amura consultation in Velachery.", False),
                ("I have severe chest pain and cannot breathe.", True),
            ):
                page.locator("#demoUtteranceInput").fill(utt)
                with page.expect_response(lambda r: "/api/turn" in r.url, timeout=15000) as resp_info:
                    page.locator("#demoSendBtn").click()
                turn_resp = resp_info.value
                if turn_resp.status != 200:
                    assertions_failed.append(f"{viewport_name} /api/turn returned HTTP {turn_resp.status}")
                page.wait_for_timeout(350)
                ai_text = page.locator("#modalAIText").inner_text().strip()
                if not ai_text or "undefined" in ai_text.lower():
                    assertions_failed.append(f"{viewport_name} #modalAIText invalid: '{ai_text}'")
                _check_no_real_estate(ai_text, f"{viewport_name} #modalAIText", assertions_failed)
                if expect_108 and "108" not in ai_text:
                    assertions_failed.append(f"{viewport_name} chest pain did not surface 108 in #modalAIText")

            if page.locator("#modalCloseBtn").is_visible():
                page.locator("#modalCloseBtn").click(timeout=3000)
            elif page.locator("#modalMobileDoneBtn").is_visible():
                page.locator("#modalMobileDoneBtn").click(timeout=3000)

        # 6. Outbound Phone Call UI Verification
        tel_inputs = page.locator("#outboundPhoneInput, input[type='tel']")
        if tel_inputs.count() == 0:
            assertions_failed.append(f"{viewport_name} missing outbound call phone input UI")

        # 7. Secondary Routes (/presentation and /commercial)
        for route in ("/presentation", "/commercial"):
            r2 = page.goto(f"{base_url}{route}", wait_until="domcontentloaded", timeout=20000)
            if not r2 or r2.status != 200:
                assertions_failed.append(f"{viewport_name} {route} returned HTTP {r2.status if r2 else 'none'}")
            else:
                txt = page.locator("body").inner_text()
                _check_no_real_estate(txt, f"{viewport_name} {route}", assertions_failed)

    finally:
        context.close()

    return {
        "viewport": viewport_name,
        "console_errors": console_errors,
        "page_errors": page_errors,
        "http_errors": http_errors,
        "request_failures": request_failures,
        "assertions_failed": assertions_failed,
        "passed": not (console_errors or page_errors or http_errors or request_failures or assertions_failed),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Playwright dual-viewport E2E verifier for CLOSER AI")
    parser.add_argument("--base-url", default="", help="Target base URL (starts local uvicorn if omitted)")
    parser.add_argument("--viewport", choices=["both", "desktop", "mobile"], default="both")
    parser.add_argument("--json-out", default="", help="Optional path to write JSON summary")
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        print(json.dumps({"status": "unavailable", "reason": f"playwright import failed: {exc}"}))
        return 2

    exe_path = _resolve_chromium_executable()
    server_proc: Optional[subprocess.Popen] = None
    tmp_dir_obj: Optional[tempfile.TemporaryDirectory] = None
    base_url = args.base_url.rstrip("/")

    try:
        if not base_url:
            port = _find_free_port()
            base_url = f"http://127.0.0.1:{port}"
            tmp_dir_obj = tempfile.TemporaryDirectory(prefix="closer_pw_e2e_")
            env = os.environ.copy()
            env["CLOSER_MEMORY_DB_PATH"] = str(Path(tmp_dir_obj.name) / "pw_closer_learning.db")
            env["CLOSER_LEARNING_DB_PATH"] = str(Path(tmp_dir_obj.name) / "pw_closer_learning.db")
            env.pop("CLOSER_PERSIST_LOCAL_DB", None)
            env["CLOSER_OFFLINE_STT"] = "1"
            if env.get("CLOSER_RUN_LIVE_E2E") != "1":
                for k in (
                    "SARVAM_API_KEY",
                    "BLAND_API_KEY",
                    "GROQ_API_KEY",
                    "OPENAI_API_KEY",
                    "OPENROUTER_API_KEY",
                    "ANTHROPIC_AUTH_TOKEN",
                    "GEMINI_API_KEY",
                    "GOOGLE_API_KEY",
                    "ELEVENLABS_API_KEY",
                    "CARTESIA_API_KEY",
                ):
                    env[k] = ""

            server_proc = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
                cwd=str(ROOT_DIR),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            _wait_for_health(base_url, timeout_sec=20.0)

        viewports = ["desktop", "mobile"] if args.viewport == "both" else [args.viewport]
        results: List[Dict[str, Any]] = []

        with sync_playwright() as p:
            launch_kwargs: Dict[str, Any] = {"headless": True}
            if exe_path:
                launch_kwargs["executable_path"] = exe_path
            browser = p.chromium.launch(**launch_kwargs)
            try:
                for vp in viewports:
                    results.append(_run_viewport_suite(browser, base_url, vp))
            finally:
                browser.close()

        summary = {
            "base_url": base_url,
            "chromium_executable": exe_path or "playwright-default",
            "results": results,
            "all_passed": all(r["passed"] for r in results),
        }
        if args.json_out:
            Path(args.json_out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0 if summary["all_passed"] else 1
    finally:
        if server_proc is not None:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()
        if tmp_dir_obj is not None:
            tmp_dir_obj.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
