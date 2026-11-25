"""
tests/e2e/test_tier4_scenarios.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tier 4 Real-World Amura Health (Velachery, Chennai) Application Scenarios (5 end-to-end tests)
matching TEST_INFRA.md § Real-World Application Scenarios.
"""

from __future__ import annotations

import base64
import json

import httpx
import pytest

from tests.e2e.conftest import (
    ROOT_DIR,
    assert_no_real_estate_copy,
    is_160hz_synthetic_beep,
    is_valid_audio_bytes,
)


class TestTier4RealWorldAmuraScenarios:
    async def test_scenario1_velachery_tamil_type2_diabetes_intake_to_call(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav, tmp_path
    ):
        """
        Scenario 1: Anxious Type-2 Diabetic caller in Velachery (Tamil/Tanglish)
        completes multi-turn intake, grants DPDP consent, books consultation,
        and dispatches outbound confirmation call + LearningMemoryDB verification.
        """
        sid = "t4_s1_velachery_ta"
        r_mode = await api_client.post("/api/market_mode", json={"session_id": sid, "mode": "tamil"})
        assert r_mode.status_code == 200
        assert_no_real_estate_copy(r_mode.json()["greeting"], "S1 Tamil greeting")

        # Turn 1: Anxious diabetes inquiry in Tamil
        t1 = await api_client.post(
            "/api/turn",
            json={
                "session_id": sid,
                "utterance": "வணக்கம், நான் வேளச்சேரியில் இருக்கேன். என் HbA1c 8.4% இருக்கு, எனக்கு ரொம்ப பயமா இருக்கு Sir.",
                "market_mode": "tamil",
                "voice": "ta-IN-PallaviNeural",
            },
        )
        assert t1.status_code == 200
        d1 = t1.json()
        assert d1["detected_emotion"] == "anxious"
        assert d1["emergency_108"] is False
        assert_no_real_estate_copy(d1["reply"], "S1 turn 1")

        # Turn 2: DPDP consent granted & slot booking
        t2 = await api_client.post(
            "/api/turn",
            json={
                "session_id": sid,
                "utterance": "சரிங்க, என் பெயர் செந்தில், வியாழக்கிழமை மாலை 4 மணிக்கு Amura doctor consultation book பண்ணுங்க.",
                "market_mode": "tamil",
                "voice": "ta-IN-PallaviNeural",
                "consent_granted": True,
            },
        )
        assert t2.status_code == 200
        d2 = t2.json()
        assert d2["consent_status"] == "granted"
        assert d2["dossier"]["consent_status"] == "granted"
        assert d2["reply"] and "undefined" not in d2["reply"].lower()

        # Outbound call confirmation + status lookup
        call_resp = await api_client.post(
            "/api/call",
            json={
                "phone_number": "+919840054321",
                "patient_name": "Senthil",
                "language": "tamil",
                "scenario": "metabolic_intake",
                "consent_confirmed": True,
                "mode": "demo",
            },
        )
        assert call_resp.status_code == 200
        cid = call_resp.json()["call_id"]
        assert (await api_client.get(f"/api/call/{cid}")).status_code == 200

        # Ensure DB isolation in tmp_path
        from src.closer.memory.learning_db import get_learning_db

        assert str(get_learning_db().db_path).startswith(str(tmp_path))

    async def test_scenario2_acute_cardiac_red_flag_emergency_108_dpdp_7f(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav
    ):
        """
        Scenario 2: Acute chest pain & dyspnea caller (English & Hindi) even with
        declined consent triggers immediate 108/ER routing & DPDP Section 7(f) exemption.
        """
        for idx, (mode, key) in enumerate(
            (("india", "emergency_chest_en"), ("hindi", "emergency_chest_hi")), start=1
        ):
            resp = await api_client.post(
                "/api/turn",
                json={
                    "session_id": f"t4_s2_{idx}",
                    "utterance": amura_utterances[key],
                    "market_mode": mode,
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

    async def test_scenario3_frustrated_pcod_patient_dosage_refusal_to_physician_route(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        """
        Scenario 3: Frustrated patient demands insulin/metformin dosage adjustment ->
        EmotionDetector detects frustration, ClinicalSafetyGuardrails blocks prescribing,
        and routes empathetically to Amura physician consultation.
        """
        sid = "t4_s3_frust_rx"
        t1 = await api_client.post(
            "/api/turn",
            json={
                "session_id": sid,
                "utterance": "I am fed up waiting! Tell me how many units of insulin to take and double my metformin tonight?!",
                "market_mode": "india",
            },
        )
        assert t1.status_code == 200
        d1 = t1.json()
        assert d1["detected_emotion"] == "frustrated"
        assert d1["safety_flag"] == "no_prescribing"
        assert d1["emergency_108"] is False
        assert_no_real_estate_copy(d1["reply"], "S3 prescribing refusal")

        t2 = await api_client.post(
            "/api/turn",
            json={
                "session_id": sid,
                "utterance": "Okay, please book a consultation with an Amura physician for Friday morning.",
                "market_mode": "india",
                "consent_granted": True,
            },
        )
        assert t2.status_code == 200
        assert t2.json()["safety_flag"] == "safe"
        assert t2.json()["consent_status"] == "granted"

    async def test_scenario4_hindi_pcod_sarvam_402_fallback_and_outbound_call(
        self, api_client: httpx.AsyncClient, mock_sarvam_402, mock_edge_tts_wav, mock_bland_success
    ):
        """
        Scenario 4: Hindi PCOD/thyroid caller hits Sarvam 402 exhausted credits ->
        automatic cooldown + playable audio fallback + outbound Bland callback trigger.
        """
        sid = "t4_s4_hindi_402"
        t1 = await api_client.post(
            "/api/turn",
            json={
                "session_id": sid,
                "utterance": "नमस्ते, मुझे PCOD और थायरॉइड के लिए अमूरा हेल्थ का ऑनलाइन प्लान समझना है।",
                "market_mode": "hindi",
                "voice": "hi-IN-SwaraNeural",
                "consent_granted": True,
            },
        )
        assert t1.status_code == 200
        body = t1.json()
        assert body["tts_fallback_used"] is True
        assert body["reply"] and "undefined" not in body["reply"].lower()
        assert_no_real_estate_copy(body["reply"], "S4 Hindi reply")
        if body["audio_base64"]:
            raw = base64.b64decode(body["audio_base64"])
            assert is_valid_audio_bytes(raw)
            assert not is_160hz_synthetic_beep(raw)

        call_resp = await api_client.post(
            "/api/call",
            json={
                "phone_number": "+919840012345",
                "patient_name": "Pooja Sharma",
                "language": "hindi",
                "scenario": "metabolic_intake",
                "consent_confirmed": True,
                "mode": "live",
                "override_trai_window": True,
            },
        )
        assert call_resp.status_code == 200
        assert call_resp.json()["call_id"] == "bland_e2e_call_001"

    async def test_scenario5_hospital_front_desk_trai_playbook_and_secondary_assets(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        """
        Scenario 5: Full showcase walkthrough: /api/health -> /api/turn -> /api/tts ->
        /api/call consent validation (422 vs 200) -> landing, presentation, commercial,
        soundboard demos, and founder playbook verification.
        """
        assert (await api_client.get("/api/health")).json()["status"] == "operational"
        assert (await api_client.get("/")).status_code == 200
        assert (await api_client.get("/presentation")).status_code == 200
        assert (await api_client.get("/commercial")).status_code == 200

        tts_resp = await api_client.post(
            "/api/tts",
            json={"text": "Amura Health front desk ready in Velachery.", "voice": "maya_en"},
        )
        assert tts_resp.status_code == 200

        bad_call = await api_client.post(
            "/api/call",
            json={
                "phone_number": "+919840077777",
                "patient_name": "Neha",
                "language": "english",
                "scenario": "lab_followup",
                "consent_confirmed": False,
                "mode": "demo",
            },
        )
        assert bad_call.status_code == 422

        ok_call = await api_client.post(
            "/api/call",
            json={
                "phone_number": "+919840077777",
                "patient_name": "Neha",
                "language": "english",
                "scenario": "lab_followup",
                "consent_confirmed": True,
                "mode": "demo",
            },
        )
        assert ok_call.status_code == 200

        playbook = ROOT_DIR / "docs" / "AMURA_FOUNDER_PLAYBOOK.md"
        assert playbook.is_file()
        assert "108" in playbook.read_text(encoding="utf-8")
