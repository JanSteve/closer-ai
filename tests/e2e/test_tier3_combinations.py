"""
tests/e2e/test_tier3_combinations.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tier 3 Pairwise Cross-Feature Combinations (12 tests) derived from TEST_INFRA.md & PROJECT.md.
"""

from __future__ import annotations

import asyncio
import base64
import json
import re

import httpx
import pytest

from tests.e2e.conftest import (
    ROOT_DIR,
    assert_no_real_estate_copy,
    is_160hz_synthetic_beep,
    is_valid_audio_bytes,
)


class TestTier3CrossFeatureCombinations:
    async def test_comb01_emotion_tts_prosody_across_trilingual_turns(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav
    ):
        cases = [
            ("anxious_en", "india", "en-IN-NeerjaExpressiveNeural", "anxious"),
            ("anxious_ta", "tamil", "ta-IN-PallaviNeural", "anxious"),
            ("anxious_hi", "hindi", "hi-IN-SwaraNeural", "anxious"),
            ("urgent_en", "india", "en-US-AvaNeural", "urgent"),
        ]
        for key, mode, voice, expected_emo in cases:
            resp = await api_client.post(
                "/api/turn",
                json={
                    "session_id": f"t3_c01_{key}",
                    "utterance": amura_utterances[key],
                    "market_mode": mode,
                    "voice": voice,
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["detected_emotion"] == expected_emo
            assert body["empathy_tone"]
            assert body["audio_mime"] in {"audio/wav", "audio/mpeg", "none"}

    async def test_comb02_safety_108_overrides_declined_dpdp_consent(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t3_c02",
                "utterance": amura_utterances["emergency_chest_en"],
                "market_mode": "india",
                "consent_granted": False,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["emergency_108"] is True
        assert body["safety_flag"] == "emergency_108"
        assert body["consent_status"] == "emergency_exempt_section_7f"
        assert body["dossier"]["triage_urgency"] == "Emergency 108"
        assert "108" in body["reply"]

    async def test_comb03_frustrated_plus_no_prescribing_in_tamil_and_hindi(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        prompts = [
            ("tamil", "எத்தனை தடவை கேட்கிறது?! எனக்கு எத்தனை யூனிட் இன்சுலின் எடுக்கணும் இப்போ சொல்லுங்க!"),
            ("hindi", "कितनी बार पूछूँ?! मुझे कितनी यूनिट इंसुलिन बढ़ाना है अभी दवाई लिख दो!"),
        ]
        for mode, text in prompts:
            resp = await api_client.post(
                "/api/turn",
                json={"session_id": f"t3_c03_{mode}", "utterance": text, "market_mode": mode},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["detected_emotion"] == "frustrated"
            assert body["safety_flag"] == "no_prescribing"

    async def test_comb04_sarvam_402_exhaustion_cascades_cleanly_in_api_turn(
        self, api_client: httpx.AsyncClient, mock_sarvam_402, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t3_c04_402",
                "utterance": "வணக்கம், என் சர்க்கரை அளவு 240 இருக்கு, ஆலோசனை வேணும்.",
                "market_mode": "tamil",
                "voice": "ta-IN-PallaviNeural",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["reply"] and "undefined" not in body["reply"].lower()
        assert body["tts_fallback_used"] is True
        if body["audio_base64"]:
            raw = base64.b64decode(body["audio_base64"])
            assert is_valid_audio_bytes(raw)
            assert not is_160hz_synthetic_beep(raw)

    async def test_comb05_market_mode_switch_turn_and_learning_db_isolation(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav, tmp_path
    ):
        sid = "t3_c05_switch"
        for mode, utt in (
            ("india", "Hi, my name is Vikram from Velachery looking for diabetes care."),
            ("tamil", "வணக்கம், வியாழக்கிழமை மாலை 4 மணிக்கு slot கிடைக்குமா?"),
            ("hindi", "जी हाँ, मैं डॉक्टर से कंसल्टेशन बुक करना चाहता हूँ।"),
        ):
            r_mode = await api_client.post("/api/market_mode", json={"session_id": sid, "mode": mode})
            assert r_mode.status_code == 200
            r_turn = await api_client.post(
                "/api/turn",
                json={"session_id": sid, "utterance": utt, "market_mode": mode, "consent_granted": True},
            )
            assert r_turn.status_code == 200
            assert_no_real_estate_copy(r_turn.json()["reply"], f"comb05 {mode}")

        from src.closer.memory.learning_db import get_learning_db

        db = get_learning_db()
        assert str(db.db_path).startswith(str(tmp_path))

    async def test_comb06_concurrent_bilingual_sessions_stay_isolated(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        r_a, r_b = await asyncio.gather(
            api_client.post(
                "/api/turn",
                json={
                    "session_id": "t3_c06_tamil",
                    "utterance": "என் பெயர் முருகன், Type-2 diabetes reversal பற்றி கேட்கிறேன்.",
                    "market_mode": "tamil",
                },
            ),
            api_client.post(
                "/api/turn",
                json={
                    "session_id": "t3_c06_pcos",
                    "utterance": "My name is Sneha, asking about PCOD hormonal care.",
                    "market_mode": "india",
                },
            ),
        )
        assert r_a.status_code == 200 and r_b.status_code == 200
        assert "Sneha" not in json.dumps(r_a.json()["dossier"])
        assert "முருகன்" not in json.dumps(r_b.json()["dossier"])

    async def test_comb07_turn_dossier_flows_into_api_call_and_status_lookup(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        t_resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t3_c07_flow",
                "utterance": "I am Ramesh, worried about HbA1c 8.9%. Please schedule Thursday 4 PM.",
                "market_mode": "india",
                "consent_granted": True,
            },
        )
        assert t_resp.status_code == 200
        assert t_resp.json()["consent_status"] == "granted"

        c_resp = await api_client.post(
            "/api/call",
            json={
                "phone_number": "+919840012345",
                "patient_name": "Ramesh",
                "language": "english",
                "scenario": "metabolic_intake",
                "consent_confirmed": True,
                "mode": "demo",
            },
        )
        assert c_resp.status_code == 200
        cid = c_resp.json()["call_id"]
        g_resp = await api_client.get(f"/api/call/{cid}")
        assert g_resp.status_code == 200
        assert g_resp.json()["patient_name"] == "Ramesh"

    async def test_comb08_api_tts_maya_en_and_indic_voices_contract(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        for voice, lang in (
            ("maya_en", "english"),
            ("ta-IN-PallaviNeural", "tamil"),
            ("hi-IN-SwaraNeural", "hindi"),
        ):
            resp = await api_client.post(
                "/api/tts",
                json={"text": "Amura Health Velachery consultation.", "voice": voice, "language": lang},
            )
            assert resp.status_code == 200
            body = resp.json()
            if voice == "maya_en":
                assert body.get("voice_resolved") == "en-US-AvaNeural"

    async def test_comb09_api_reset_clears_single_session_without_affecting_sibling(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        await api_client.post(
            "/api/turn",
            json={"session_id": "t3_c09_keep", "utterance": "My name is Kavya, thyroid care.", "market_mode": "india"},
        )
        await api_client.post(
            "/api/turn",
            json={"session_id": "t3_c09_wipe", "utterance": "My name is Manoj, fatty liver.", "market_mode": "india"},
        )
        r_reset = await api_client.post("/api/reset", json={"session_id": "t3_c09_wipe", "market_mode": "india"})
        assert r_reset.status_code == 200
        assert "Manoj" not in json.dumps(r_reset.json()["dossier"])

        r_keep = await api_client.post(
            "/api/turn",
            json={"session_id": "t3_c09_keep", "utterance": "Can we book Friday?", "market_mode": "india"},
        )
        assert r_keep.status_code == 200

    async def test_comb10_vercel_api_entrypoints_and_main_app_parity(self):
        import main
        from api import call as api_call_mod
        from api import health as api_health_mod
        from api import index as api_index_mod
        from api import tts as api_tts_mod
        from api import turn as api_turn_mod

        for mod in (api_index_mod, api_health_mod, api_turn_mod, api_call_mod, api_tts_mod):
            assert mod.app is main.app

    def test_comb11_roi_calculator_currency_and_slider_dom_alignment(self):
        html = (ROOT_DIR / "index.html").read_text(encoding="utf-8")
        js = (ROOT_DIR / "main.js").read_text(encoding="utf-8")
        for fn in ("setRoiCurrency", "updateRoiCalc"):
            assert fn in html and fn in js
        for el_id in ("currUSD", "currINR", "sliderLeads", "sliderCommission", "sliderConv", "roiRevenue"):
            assert el_id in html and el_id in js

    def test_comb12_soundboard_and_demo_modal_dom_contract_alignment(self):
        html = (ROOT_DIR / "index.html").read_text(encoding="utf-8")
        js = (ROOT_DIR / "main.js").read_text(encoding="utf-8")
        for el_id in (
            "voice-studio",
            "soundboardPlayBtn",
            "openLiveCallFromStudio",
            "demoModal",
            "btnMarketUSA",
            "btnMarketTamil",
            "btnMarketHindi",
            "demoUtteranceInput",
            "demoSendBtn",
            "modalAIText",
        ):
            assert el_id in html and el_id in js
