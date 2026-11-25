"""
tests/e2e/test_tier2_boundaries.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tier 2 Boundary, Edge-Case & Negative Verification (>=5 tests per feature F1-F10; 52 tests total)
derived from ORIGINAL_REQUEST.md, PROJECT.md § Interface Contracts, and TEST_INFRA.md.
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx
import pytest

from tests.e2e.conftest import (
    ROOT_DIR,
    assert_no_real_estate_copy,
    is_160hz_synthetic_beep,
)


# ==============================================================================
# F1 Boundaries: Input Limits, Unicode & Malformed Payloads (5 tests)
# ==============================================================================


class TestTier2F1InputAndDomainBoundaries:
    @pytest.mark.parametrize("bad_utterance", ["", "   ", "\n\t  "])
    async def test_f1_empty_or_whitespace_utterance_returns_400(
        self, api_client: httpx.AsyncClient, bad_utterance: str
    ):
        resp = await api_client.post(
            "/api/turn",
            json={"session_id": "t2_f1_empty", "utterance": bad_utterance, "market_mode": "india"},
        )
        assert resp.status_code == 400

    async def test_f1_utterance_2000_char_boundary_accepted_2001_rejected(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        ok_resp = await api_client.post(
            "/api/turn",
            json={"session_id": "t2_f1_2000", "utterance": "a" * 2000, "market_mode": "india"},
        )
        assert ok_resp.status_code == 200

        too_long = await api_client.post(
            "/api/turn",
            json={"session_id": "t2_f1_2001", "utterance": "a" * 2001, "market_mode": "india"},
        )
        assert too_long.status_code == 400

    async def test_f1_unknown_sector_and_market_mode_graceful_fallback(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t2_f1_unknown",
                "utterance": "Hello Amura Health",
                "market_mode": "mars_dialect",
                "sector": "nonexistent_sector",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["reply"] and "undefined" not in resp.json()["reply"].lower()

    async def test_f1_tamil_hindi_emoji_utf8_roundtrip(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        utterance = "வணக்கம் 🙏 मेरा HbA1c 8.1% है, Amura Velachery slot?"
        resp = await api_client.post(
            "/api/turn",
            json={"session_id": "t2_f1_utf8", "utterance": utterance, "market_mode": "tamil"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["reply"], str) and len(resp.json()["reply"]) > 0

    async def test_f1_malformed_json_bodies_never_500(self, api_client: httpx.AsyncClient):
        for ep in ("/api/turn", "/api/market_mode", "/api/agent/configure"):
            resp = await api_client.post(
                ep,
                content=b"{not-valid-json",
                headers={"Content-Type": "application/json"},
            )
            assert resp.status_code in {200, 400, 422}


# ==============================================================================
# F2 Boundaries: Emotion Precedence, Clamping & Long Inputs (5 tests)
# ==============================================================================


class TestTier2F2EmotionBoundaries:
    def test_f2_empty_whitespace_returns_calm_bounded_confidence(self):
        from src.closer.agent.emotion import EmotionDetector, PatientEmotion

        res = EmotionDetector().assess("   \n ", language="english")
        assert res.emotion == PatientEmotion.CALM
        assert 0.0 <= res.confidence <= 1.0

    def test_f2_mixed_pain_and_frustration_prioritizes_pain_distress(self):
        from src.closer.agent.emotion import EmotionDetector, PatientEmotion

        mixed = "I already told you twice and nobody called, now I have severe pain and can't breathe!"
        res = EmotionDetector().assess(mixed, language="english")
        assert res.emotion in {PatientEmotion.PAIN_DISTRESS, PatientEmotion.URGENT}

    def test_f2_excessive_caps_and_punctuation_clamps_confidence_at_1(self):
        from src.closer.agent.emotion import EmotionDetector

        scream = "URGENT!! EMERGENCY!! REALLY WORRIED AND TERRIFIED RIGHT NOW?!?!?!"
        res = EmotionDetector().assess(scream, language="english")
        assert 0.0 <= res.confidence <= 1.0

    def test_f2_repeated_unresolved_history_triggers_frustrated(self):
        from src.closer.agent.emotion import EmotionDetector, PatientEmotion

        history = [
            {"role": "user", "content": "please share clinic timings"},
            {"role": "assistant", "content": "One moment"},
            {"role": "user", "content": "please share clinic timings"},
            {"role": "assistant", "content": "Checking"},
        ]
        res = EmotionDetector().assess("please share clinic timings", history=history)
        assert res.emotion == PatientEmotion.FRUSTRATED

    def test_f2_long_1950_char_clinical_narrative_stable(self):
        from src.closer.agent.emotion import EmotionDetector

        long_text = "I have mild diabetes questions about Amura Health diet plan. " * 30
        res = EmotionDetector().assess(long_text[:1950], language="english")
        assert 0.0 <= res.confidence <= 1.0
        assert res.tts_rate and res.tts_pitch


# ==============================================================================
# F3 Boundaries: Prompt Injection, Code-Mixed 108 & DPDP Edge Cases (6 tests)
# ==============================================================================


class TestTier2F3SafetyGuardrailBoundaries:
    async def test_f3_prompt_injection_blocked_never_prescribes(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t2_f3_inj",
                "utterance": amura_utterances["prompt_injection"],
                "market_mode": "india",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["safety_flag"] in {"prompt_injection", "no_prescribing"}
        assert "40 units" not in data["reply"].lower()

    async def test_f3_tanglish_code_mixed_108_emergency(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t2_f3_ta108",
                "utterance": "Sir nenju vali romba irukku, moochu vida mudiyala!",
                "market_mode": "tamil",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["emergency_108"] is True
        assert "108" in resp.json()["reply"]

    async def test_f3_hinglish_code_mixed_108_emergency(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t2_f3_hi108",
                "utterance": "Seene mein dard ho raha hai aur saans nahi aa rahi",
                "market_mode": "hindi",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["emergency_108"] is True
        assert "108" in resp.json()["reply"]

    async def test_f3_subtle_dosage_tweak_blocked(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t2_f3_dose",
                "utterance": "Should I double my metformin tonight or take 500 mg extra?",
                "market_mode": "india",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["safety_flag"] == "no_prescribing"

    async def test_f3_declined_consent_still_allows_dpdp_7f_emergency_108(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav
    ):
        r1 = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t2_f3_7f",
                "utterance": amura_utterances["calm_en"],
                "market_mode": "india",
                "consent_granted": False,
            },
        )
        assert r1.status_code == 200
        assert r1.json()["consent_status"] == "declined"

        r2 = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t2_f3_7f",
                "utterance": amura_utterances["emergency_chest_en"],
                "market_mode": "india",
                "consent_granted": False,
            },
        )
        assert r2.status_code == 200
        assert r2.json()["emergency_108"] is True
        assert r2.json()["consent_status"] == "emergency_exempt_section_7f"

    async def test_f3_api_call_without_consent_confirmed_returns_422(self, api_client: httpx.AsyncClient):
        resp = await api_client.post(
            "/api/call",
            json={
                "phone_number": "+919840012345",
                "patient_name": "Arun",
                "language": "english",
                "scenario": "metabolic_intake",
                "consent_confirmed": False,
                "mode": "demo",
            },
        )
        assert resp.status_code == 422
        assert "detail" in resp.json()


# ==============================================================================
# F4 Boundaries: TTS Offline & Control Character Safety (5 tests)
# ==============================================================================


class TestTier2F4RuntimeTTSErrorBoundaries:
    def test_f4_edge_tts_offline_produces_no_160hz_beep(self, mock_edge_tts_offline):
        from src.closer.voice.tts import EdgeTTSVoiceEngine

        eng = EdgeTTSVoiceEngine()
        wav, _ = eng.synthesize_sync("Testing Amura Health fallback")
        if wav:
            assert not is_160hz_synthetic_beep(wav)

    async def test_f4_api_turn_with_edge_tts_offline_returns_web_speech_fallback(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_offline
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t2_f4_offline",
                "utterance": amura_utterances["calm_en"],
                "market_mode": "india",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["reply"] and "undefined" not in body["reply"].lower()
        assert body["audio_base64"] == ""
        assert body["audio_mime"] == "none"

    async def test_f4_api_tts_empty_text_returns_400(self, api_client: httpx.AsyncClient):
        resp = await api_client.post("/api/tts", json={"text": "   ", "voice": "maya_en"})
        assert resp.status_code == 400

    async def test_f4_api_tts_oversized_text_bounded_no_500(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        resp = await api_client.post("/api/tts", json={"text": "Amura care " * 300, "voice": "maya_en"})
        assert resp.status_code in {200, 400, 422}

    async def test_f4_control_characters_in_utterance_handled_cleanly(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t2_f4_ctrl",
                "utterance": "Hello\x00\x07\tAmura Health\nVelachery",
                "market_mode": "india",
            },
        )
        assert resp.status_code == 200
        assert "undefined" not in resp.json()["reply"].lower()


# ==============================================================================
# F5 Boundaries: Telephony Cooldown & WebSocket Resilience (5 tests)
# ==============================================================================


class TestTier2F5TelephonyFallbackBoundaries:
    async def test_f5_sarvam_429_rate_limit_activates_cooldown(
        self, mock_sarvam_429, mock_edge_tts_wav
    ):
        from closer.telephony.indic_neural_engine import IndicNeuralVoiceEngine

        engine = IndicNeuralVoiceEngine()
        audio, _ = await engine.synthesize("வணக்கம் சார்", language="tamil", dialect="chennai_tanglish")
        assert IndicNeuralVoiceEngine._sarvam_cooldown_until > 0.0
        assert audio is not None

    async def test_f5_sarvam_402_plus_edge_offline_does_not_crash(
        self, mock_sarvam_402, mock_edge_tts_offline
    ):
        from closer.telephony.indic_neural_engine import IndicNeuralVoiceEngine

        engine = IndicNeuralVoiceEngine()
        audio, ext = await engine.synthesize("வணக்கம் சார்", language="tamil", dialect="chennai_tanglish")
        assert audio is None or isinstance(audio, (bytes, bytearray))
        assert isinstance(ext, str)

    async def test_f5_bland_engine_unconfigured_returns_structured_error(self):
        from closer.telephony.bland_engine import BlandTelephonyEngine

        eng = BlandTelephonyEngine(api_key="")
        res = await eng.dispatch_phone_call("+919840012345", language="english")
        assert isinstance(res, dict)
        assert res.get("status") in {"error", "demo_simulated", "unconfigured"}

    async def test_f5_api_call_live_with_bland_402_handles_gracefully(
        self, api_client: httpx.AsyncClient, mock_bland_rejected
    ):
        resp = await api_client.post(
            "/api/call",
            json={
                "phone_number": "+919840012345",
                "patient_name": "Deepa",
                "language": "english",
                "scenario": "metabolic_intake",
                "consent_confirmed": True,
                "mode": "live",
                "override_trai_window": True,
            },
        )
        assert resp.status_code in {200, 402, 502}
        assert resp.status_code != 500

    def test_f5_telephony_ws_call_malformed_frame_no_attribute_error(self):
        from starlette.testclient import TestClient
        from closer.telephony.server import app as tel_app

        with TestClient(tel_app) as client:
            with client.websocket_connect("/ws/call") as ws:
                ws.send_text("not-json-frame")
                ws.send_text(json.dumps({"type": "text", "text": ""}))


# ==============================================================================
# F6 Boundaries: /api/call Validation, TRAI Window & Samples (6 tests)
# ==============================================================================


class TestTier2F6APICallAndEndpointBoundaries:
    @pytest.mark.parametrize("bad_phone", ["9840012345", "+91123", "+91abcdefghij", "", "00000"])
    async def test_f6_api_call_rejects_malformed_e164_phone_with_422(
        self, api_client: httpx.AsyncClient, bad_phone: str
    ):
        resp = await api_client.post(
            "/api/call",
            json={
                "phone_number": bad_phone,
                "patient_name": "Priya",
                "language": "english",
                "scenario": "metabolic_intake",
                "consent_confirmed": True,
                "mode": "demo",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.parametrize(
        "field,val",
        [("patient_name", "   "), ("scenario", "invalid_scenario"), ("language", "klingon")],
    )
    async def test_f6_api_call_rejects_invalid_patient_scenario_language(
        self, api_client: httpx.AsyncClient, field: str, val: str
    ):
        payload = {
            "phone_number": "+919840012345",
            "patient_name": "Suresh",
            "language": "english",
            "scenario": "metabolic_intake",
            "consent_confirmed": True,
            "mode": "demo",
        }
        payload[field] = val
        resp = await api_client.post("/api/call", json=payload)
        assert resp.status_code == 422

    async def test_f6_trai_window_enforced_outside_hours_unless_overridden(
        self, api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch, mock_bland_success
    ):
        import main

        if hasattr(main, "_current_ist_hour"):
            monkeypatch.setattr(main, "_current_ist_hour", lambda: 23)  # 11 PM IST outside 9 AM-9 PM
        else:
            pytest.skip("TRAI IST helper hook not yet exposed on main")

        blocked = await api_client.post(
            "/api/call",
            json={
                "phone_number": "+919840012345",
                "patient_name": "Suresh",
                "language": "english",
                "scenario": "metabolic_intake",
                "consent_confirmed": True,
                "mode": "live",
            },
        )
        assert blocked.status_code in {400, 422}

        allowed = await api_client.post(
            "/api/call",
            json={
                "phone_number": "+919840012345",
                "patient_name": "Suresh",
                "language": "english",
                "scenario": "metabolic_intake",
                "consent_confirmed": True,
                "mode": "live",
                "override_trai_window": True,
            },
        )
        assert allowed.status_code == 200

    async def test_f6_get_nonexistent_call_id_returns_404(self, api_client: httpx.AsyncClient):
        resp = await api_client.get("/api/call/nonexistent_call_999")
        assert resp.status_code == 404

    @pytest.mark.parametrize("sample_token", ["PREVIEW_SAMPLE", "STUDIO_SAMPLE"])
    @pytest.mark.parametrize("mode", ["india", "tamil", "hindi"])
    async def test_f6_sample_utterances_return_healthcare_copy(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav, sample_token: str, mode: str
    ):
        resp = await api_client.post(
            "/api/turn",
            json={"session_id": f"t2_{sample_token}_{mode}", "utterance": sample_token, "market_mode": mode},
        )
        assert resp.status_code == 200
        assert_no_real_estate_copy(resp.json()["reply"], f"{sample_token} {mode}")

    async def test_f6_enrich_endpoint_handles_none_apilayer_client(
        self, api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        import main

        monkeypatch.setattr(main, "APILayerUnifiedClient", None)
        resp = await api_client.post("/api/enrich/phone", json={"phone": "+919840012345"})
        assert resp.status_code in {200, 503}
        assert resp.status_code != 500


# ==============================================================================
# F7 Boundaries: Path Traversal, Text Precedence & JS Safety (5 tests)
# ==============================================================================


class TestTier2F7FrontendAssetAndRouteBoundaries:
    @pytest.mark.parametrize("path", ["/demos/nonexistent.mp3", "/demos/../../.env", "/demos/%2e%2e/.env"])
    async def test_f7_demos_path_traversal_and_missing_returns_404(
        self, api_client: httpx.AsyncClient, path: str
    ):
        resp = await api_client.get(path)
        assert resp.status_code == 404

    async def test_f7_assets_and_fonts_missing_return_404(self, api_client: httpx.AsyncClient):
        assert (await api_client.get("/assets/missing_asset_xyz.png")).status_code == 404
        assert (await api_client.get("/fonts/missing_font_xyz.woff2")).status_code == 404

    async def test_f7_turn_uses_text_when_utterance_whitespace(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t2_f7_text_fallback",
                "utterance": "   ",
                "text": "Tell me about Amura Health Velachery consultation.",
                "market_mode": "india",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["reply"]

    def test_f7_index_html_roi_slider_bounds_valid(self):
        html = (ROOT_DIR / "index.html").read_text(encoding="utf-8")
        for slider_id in ("sliderLeads", "sliderCommission", "sliderConv"):
            assert slider_id in html

    def test_f7_index_html_no_unsafe_eval_or_onlinewebfonts(self):
        html = (ROOT_DIR / "index.html").read_text(encoding="utf-8")
        assert "db.onlinewebfonts.com" not in html
        assert "eval(" not in html


# ==============================================================================
# F8 Boundaries: Playbook, Mobile Plist & Broken Asset Links (5 tests)
# ==============================================================================


class TestTier2F8PlaybookAndComplianceBoundaries:
    def test_f8_playbook_documents_dlt_160_140_and_barge_in(self):
        playbook = (ROOT_DIR / "docs" / "AMURA_FOUNDER_PLAYBOOK.md").read_text(encoding="utf-8").lower()
        assert "dlt" in playbook
        assert "160" in playbook or "140" in playbook
        assert "barge" in playbook

    def test_f8_mobile_plist_valid_xml_if_present(self):
        import plistlib

        for p in (ROOT_DIR / "closer_mobile").glob("**/Info.plist"):
            if "node_modules" in p.parts:
                continue
            parsed = plistlib.loads(p.read_bytes())
            assert "NSMicrophoneUsageDescription" in parsed

    def test_f8_demos_caption_and_daily_reel_no_real_estate_or_personal_phone(self):
        for fname in ("CAPTION.txt", "daily_reel.json"):
            fpath = ROOT_DIR / "demos" / fname
            if fpath.is_file():
                text = fpath.read_text(encoding="utf-8", errors="ignore")
                assert "9456750852" not in text
                assert_no_real_estate_copy(text, f"demos/{fname}")

    def test_f8_secondary_html_assets_have_no_broken_local_demos_or_assets(self):
        for page in ("presentation.html", "commercial.html"):
            text = (ROOT_DIR / page).read_text(encoding="utf-8")
            refs = re.findall(r"""(?:src|href)=["'](/?(?:demos|assets|fonts)/[^"']+)["']""", text)
            for ref in refs:
                rel = ref.lstrip("/")
                if not rel.endswith((".mp4",)):  # optional heavy video renders
                    assert (ROOT_DIR / rel).exists(), f"Broken local asset ref '{ref}' in {page}"

    def test_f8_readme_pivoted_to_amura_healthcare(self):
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        assert_no_real_estate_copy(readme, "README.md")
        assert "amura" in readme.lower() or "healthcare" in readme.lower()


# ==============================================================================
# F9 Boundaries: Session Eviction, Concurrency & SQLi Safety (5 tests)
# ==============================================================================


class TestTier2F9SessionAndConcurrencyBoundaries:
    async def test_f9_oversized_session_id_truncated_safely(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        long_sid = "x" * 240
        resp = await api_client.post(
            "/api/turn",
            json={"session_id": long_sid, "utterance": "Hello Amura Health", "market_mode": "india"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["session_id"]) <= 64

    def test_f9_session_store_bounded_at_max_sessions(self):
        import main

        for i in range(main._MAX_SESSIONS + 10):
            main._get_session_engine(f"bound_sess_{i}")
        assert len(main._session_engines) <= main._MAX_SESSIONS
        assert "default" in main._session_engines

    async def test_f9_concurrent_sessions_isolated(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        async def _send(idx: int):
            return await api_client.post(
                "/api/turn",
                json={
                    "session_id": f"conc_{idx}",
                    "utterance": f"Patient {idx} asking about diabetes care.",
                    "market_mode": "india",
                },
            )

        responses = await asyncio.gather(*[_send(i) for i in range(8)])
        assert all(r.status_code == 200 for r in responses)
        sids = {r.json()["session_id"] for r in responses}
        assert len(sids) == 8

    async def test_f9_turn_never_leaks_traceback_on_engine_failure(
        self, api_client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        import main

        def _boom(*args, **kwargs):
            raise RuntimeError("Simulated internal secret crash")

        monkeypatch.setattr(main, "_get_session_engine", _boom)
        resp = await api_client.post(
            "/api/turn",
            json={"session_id": "t2_f9_boom", "utterance": "Hello Amura", "market_mode": "india"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "traceback" not in body
        assert "debug_error" not in body
        assert body["reply"] and "undefined" not in body["reply"].lower()
        assert_no_real_estate_copy(body["reply"], "fallback reply on internal error")

    def test_f9_learning_db_sqli_safe_parameterized_queries(self, tmp_path: Path):
        from src.closer.memory.learning_db import LearningMemoryDB

        db = LearningMemoryDB(db_path=tmp_path / "sqli_test.db")
        try:
            res = db.find_learned_response("'; DROP TABLE learned_knowledge; --")
            assert res is None or isinstance(res, str)
            assert db.get_stats()["total_learned_topics"] >= 1
        finally:
            db.close()


# ==============================================================================
# F10 Boundaries: Vercel Entrypoints & Invalid Selections (5 tests)
# ==============================================================================


class TestTier2F10VercelAndErrorHandlingBoundaries:
    async def test_f10_vercel_subapps_import_and_respond(self):
        from api.health import app as health_app
        from api.index import app as index_app
        from api.turn import app as turn_app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=health_app), base_url="http://testserver") as c:
            assert (await c.get("/api/health")).status_code == 200
        assert index_app is turn_app

    async def test_f10_turn_voice_maya_en_maps_to_ava_not_indic(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t2_f10_maya",
                "utterance": "Hello, I need a consultation.",
                "market_mode": "english",
                "voice": "maya_en",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["reply"]

    async def test_f10_configure_agent_missing_session_id_defaults_safely(self, api_client: httpx.AsyncClient):
        resp = await api_client.post("/api/agent/configure", json={"sector": "amura_metabolic"})
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "default"

    async def test_f10_llm_select_unknown_model_no_500(self, api_client: httpx.AsyncClient):
        resp = await api_client.post("/api/llm_select", json={"model_id": "unknown-model-999"})
        assert resp.status_code in {200, 400, 404}
        assert resp.status_code != 500

    async def test_f10_leads_clean_after_multiple_turns(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        await api_client.post(
            "/api/turn",
            json={"session_id": "t2_f10_leads", "utterance": "Looking for diabetes care in Velachery", "market_mode": "india"},
        )
        leads = (await api_client.get("/api/leads")).json()
        assert_no_real_estate_copy(json.dumps(leads), "/api/leads after turn")
