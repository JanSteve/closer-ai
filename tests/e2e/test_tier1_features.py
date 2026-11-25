"""
tests/e2e/test_tier1_features.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tier 1 Feature Coverage (>=5 isolated happy-path tests per feature F1-F10; 54 tests total)
derived from ORIGINAL_REQUEST.md, PROJECT.md § Interface Contracts, and TEST_INFRA.md.
"""

from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path

import httpx
import pytest

from tests.e2e.conftest import (
    ROOT_DIR,
    assert_no_real_estate_copy,
    is_160hz_synthetic_beep,
    is_valid_audio_bytes,
)

REQUIRED_TURN_KEYS = {
    "session_id",
    "reply",
    "detected_emotion",
    "emotion_confidence",
    "empathy_tone",
    "safety_flag",
    "emergency_108",
    "consent_status",
    "dossier",
    "audio_base64",
    "audio_mime",
    "tts_provider",
    "tts_fallback_used",
    "latency_ms",
    "llm_tier",
}

REQUIRED_DOSSIER_KEYS = {
    "patient_name",
    "chief_concern",
    "condition_category",
    "triage_urgency",
    "care_pathway",
    "consent_status",
    "intent_score",
    "consult_slot",
    "follow_up_note",
    "detected_emotion",
    "safety_flag",
}

VALID_EMOTIONS = {"calm", "anxious", "urgent", "frustrated", "confused", "pain_distress"}


# ==============================================================================
# F1: Amura AI Clinical Identity & Domain Pivot (6 tests)
# ==============================================================================


class TestTier1F1ClinicalIdentity:
    async def test_f1_english_market_mode_amura_clinical_greeting(self, api_client: httpx.AsyncClient):
        resp = await api_client.post("/api/market_mode", json={"session_id": "t1_f1_en", "mode": "india"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "amura" in body["greeting"].lower() or "clinic" in body["greeting"].lower() or "health" in body["greeting"].lower()
        assert_no_real_estate_copy(body["greeting"], "market_mode india greeting")
        assert_no_real_estate_copy(json.dumps(body["dossier"]), "market_mode india dossier")

    async def test_f1_tamil_market_mode_amura_clinical_greeting(self, api_client: httpx.AsyncClient):
        resp = await api_client.post("/api/market_mode", json={"session_id": "t1_f1_ta", "mode": "tamil"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["mode"] == "tamil"
        assert len(body["greeting"].strip()) > 10
        assert_no_real_estate_copy(body["greeting"], "market_mode tamil greeting")

    async def test_f1_hindi_market_mode_amura_clinical_greeting(self, api_client: httpx.AsyncClient):
        resp = await api_client.post("/api/market_mode", json={"session_id": "t1_f1_hi", "mode": "hindi"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["mode"] == "hindi"
        assert len(body["greeting"].strip()) > 10
        assert_no_real_estate_copy(body["greeting"], "market_mode hindi greeting")

    async def test_f1_turn_diabetes_metabolic_intake_and_clinical_dossier(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t1_f1_diab",
                "utterance": "Hi, I live in Velachery Chennai and want to reverse Type-2 diabetes with Amura Health.",
                "market_mode": "india",
                "voice": "en-IN-NeerjaExpressiveNeural",
                "sector": "amura_metabolic",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["reply"] and "undefined" not in data["reply"].lower()
        assert_no_real_estate_copy(data["reply"], "diabetes turn reply")
        missing_dossier = REQUIRED_DOSSIER_KEYS - set(data["dossier"].keys())
        assert not missing_dossier, f"Missing clinical dossier keys: {missing_dossier}"
        assert_no_real_estate_copy(json.dumps(data["dossier"]), "diabetes turn dossier")

    def test_f1_learning_db_seeds_amura_clinical_knowledge(self, tmp_path: Path):
        from src.closer.memory.learning_db import LearningMemoryDB

        db = LearningMemoryDB(db_path=tmp_path / "clinical_seed.db")
        try:
            stats = db.get_stats()
            assert stats["total_learned_topics"] >= 1
            topics = db.get_all_learned_knowledge()
            serialized = json.dumps(topics)
            assert_no_real_estate_copy(serialized, "LearningMemoryDB seeded topics")
            assert any(
                kw in serialized.lower()
                for kw in ("amura", "velachery", "diabetes", "pcod", "metabolic", "clinic")
            )
        finally:
            db.close()

    async def test_f1_configure_agent_amura_metabolic_and_hospital_triage(self, api_client: httpx.AsyncClient):
        for sector in ("amura_metabolic", "hospital_triage"):
            resp = await api_client.post(
                "/api/agent/configure",
                json={
                    "session_id": f"t1_f1_{sector}",
                    "sector": sector,
                    "business_name": "Amura Health Velachery",
                    "market_mode": "india",
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["success"] is True
            assert "Amura" in (body.get("business_name") or "")


# ==============================================================================
# F2: Human Emotion Detection Engine (6 tests)
# ==============================================================================


class TestTier1F2EmotionDetection:
    async def test_f2_calm_baseline_in_turn_response(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t1_f2_calm",
                "utterance": amura_utterances["calm_en"],
                "market_mode": "india",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["detected_emotion"] == "calm"
        assert 0.0 <= float(data["emotion_confidence"]) <= 1.0
        assert isinstance(data["empathy_tone"], str) and len(data["empathy_tone"]) > 0

    def test_f2_anxious_detected_across_en_ta_hi(self, amura_utterances):
        from src.closer.agent.emotion import EmotionDetector, PatientEmotion

        det = EmotionDetector()
        for key, lang in (("anxious_en", "english"), ("anxious_ta", "tamil"), ("anxious_hi", "hindi")):
            res = det.assess(amura_utterances[key], language=lang)
            assert res.emotion == PatientEmotion.ANXIOUS, f"Expected ANXIOUS for {key}, got {res.emotion}"
            assert 0.5 <= res.confidence <= 1.0
            assert res.sarvam_pace <= 1.0
            assert res.empathy_directive

    def test_f2_urgent_detected_with_urgent_clear_style(self, amura_utterances):
        from src.closer.agent.emotion import EmotionDetector, PatientEmotion

        res = EmotionDetector().assess(amura_utterances["urgent_en"], language="english")
        assert res.emotion == PatientEmotion.URGENT
        assert res.voice_style in {"urgent_clear", "empathetic", "calm_reassuring"}
        assert res.tts_rate
        assert res.tts_pitch

    async def test_f2_frustrated_wired_into_api_turn(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t1_f2_frust",
                "utterance": amura_utterances["frustrated_en"],
                "market_mode": "india",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["detected_emotion"] == "frustrated"
        assert data["dossier"]["detected_emotion"] == "frustrated"

    def test_f2_confused_detected_on_clinical_jargon(self, amura_utterances):
        from src.closer.agent.emotion import EmotionDetector, PatientEmotion

        res = EmotionDetector().assess(amura_utterances["confused_en"], language="english")
        assert res.emotion == PatientEmotion.CONFUSED
        assert 0.0 <= res.confidence <= 1.0
        assert res.empathy_directive

    def test_f2_pain_distress_detected_with_calming_pace(self, amura_utterances):
        from src.closer.agent.emotion import EmotionDetector, PatientEmotion

        res = EmotionDetector().assess(amura_utterances["pain_distress_en"], language="english")
        assert res.emotion == PatientEmotion.PAIN_DISTRESS
        assert res.sarvam_pace <= 0.95
        assert res.voice_style == "calm_reassuring"


# ==============================================================================
# F3: Clinical Safety & Compliance Guardrails (6 tests)
# ==============================================================================


class TestTier1F3ClinicalSafetyGuardrails:
    @pytest.mark.parametrize(
        "key,mode",
        [
            ("emergency_chest_en", "india"),
            ("emergency_chest_ta", "tamil"),
            ("emergency_chest_hi", "hindi"),
        ],
    )
    async def test_f3_emergency_108_escalation_trilingual(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav, key: str, mode: str
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": f"t1_f3_108_{key}",
                "utterance": amura_utterances[key],
                "market_mode": mode,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["emergency_108"] is True
        assert data["safety_flag"] == "emergency_108"
        assert "108" in data["reply"]
        assert data["dossier"]["triage_urgency"] == "Emergency 108"
        assert data["consent_status"] == "emergency_exempt_section_7f"

    def test_f3_stroke_and_self_harm_trigger_108_and_dpdp_7f(self, amura_utterances):
        from src.closer.agent.clinical_guardrails import ClinicalSafetyGuardrails

        for key in ("emergency_stroke_en", "emergency_self_harm_en"):
            guard = ClinicalSafetyGuardrails()
            decision = guard.evaluate(amura_utterances[key], language="english")
            assert decision.allowed is False
            assert decision.emergency_108 is True
            assert decision.dpdp_emergency_exemption is True
            assert decision.category == "emergency_108"
            assert decision.override_reply and "108" in decision.override_reply

    async def test_f3_no_diagnosis_refusal_routes_to_physician(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t1_f3_diag",
                "utterance": amura_utterances["no_diagnosis_en"],
                "market_mode": "india",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["safety_flag"] == "no_diagnosis"
        assert data["emergency_108"] is False
        assert any(w in data["reply"].lower() for w in ("diagnos", "physician", "doctor"))

    @pytest.mark.parametrize(
        "key,mode",
        [
            ("no_prescribing_en", "india"),
            ("no_prescribing_ta", "tamil"),
            ("no_prescribing_hi", "hindi"),
        ],
    )
    async def test_f3_no_prescribing_refusal_trilingual(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav, key: str, mode: str
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": f"t1_f3_rx_{key}",
                "utterance": amura_utterances[key],
                "market_mode": mode,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["safety_flag"] == "no_prescribing"
        assert data["emergency_108"] is False

    async def test_f3_dpdp_explicit_consent_tracking_on_turn(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav
    ):
        r1 = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t1_f3_consent",
                "utterance": amura_utterances["calm_en"],
                "market_mode": "india",
                "consent_granted": True,
            },
        )
        assert r1.status_code == 200
        assert r1.json()["consent_status"] == "granted"
        assert r1.json()["dossier"]["consent_status"] == "granted"

    def test_f3_pii_masking_redacts_sensitive_identifiers(self):
        from src.closer.agent.clinical_guardrails import ClinicalSafetyGuardrails

        raw = "Patient Rajesh Aadhaar 1234 5678 9012 PAN ABCDE1234F Phone +919840012345 Email raj@example.com"
        masked = ClinicalSafetyGuardrails().mask_pii(raw)
        assert "1234 5678 9012" not in masked
        assert "ABCDE1234F" not in masked
        assert "9840012345" not in masked
        assert "raj@example.com" not in masked


# ==============================================================================
# F4: src/closer/ Runtime & Expressive TTS Fallback (5 tests)
# ==============================================================================


class TestTier1F4RuntimeAndTTSFallback:
    async def test_f4_no_160hz_synthetic_beep_in_turn_audio_or_fallback(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_offline
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t1_f4_nobeep",
                "utterance": amura_utterances["calm_en"],
                "market_mode": "india",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        if data["audio_base64"]:
            audio_bytes = base64.b64decode(data["audio_base64"])
            assert not is_160hz_synthetic_beep(audio_bytes), "Legacy 160Hz synthetic tone detected!"
        else:
            assert data["audio_mime"] == "none"

    def test_f4_sarvam_engine_uses_bulbul_v3_and_tamil_smoothing(self):
        from closer.telephony.sarvam_engine import SarvamVoiceEngine

        eng = SarvamVoiceEngine(api_key="test-key")
        assert eng.model == "bulbul:v3"
        prepared = eng._prepare_text("Sir, Amura clinic HbA1c test available", "tamil")
        assert isinstance(prepared, str) and len(prepared) > 0

    def test_f4_whisper_stt_fallback_has_no_bel_air_real_estate(self):
        from src.closer.voice.stt import WhisperSTTEngine

        stt = WhisperSTTEngine()
        transcript, latency = stt.transcribe(b"")
        assert isinstance(transcript, str)
        assert latency >= 0.0
        assert_no_real_estate_copy(transcript, "WhisperSTTEngine fallback")

    def test_f4_llm_router_tier3_deterministic_clinical_fallback(self):
        from src.closer.llm.router import OpenLLMRouter

        router = OpenLLMRouter(api_key="")
        for mode in ("india", "tamil", "hindi"):
            reply, meta = router.route_reasoning(
                "I want to reverse diabetes at Amura Health.",
                "Amura clinical coordinator",
                [],
                market_mode=mode,
                force_tier="deterministic_fallback",
            )
            assert reply and "undefined" not in reply.lower()
            assert_no_real_estate_copy(reply, f"OpenLLMRouter Tier 3 ({mode})")
            assert meta["tier"] == "deterministic_fallback"

    def test_f4_crm_dispatcher_formats_long_clinical_notes_intact(self):
        from src.closer.agent.schemas import PatientDossier
        from src.closer.integrations.crm import CRMDispatcher

        dossier = PatientDossier(
            patient_name="Meenakshi Sundaram",
            phone_number="+919840099887",
            chief_concern="Type-2 Diabetes & Fatty Liver",
            care_pathway="Amura MNT + NMT Reversal",
            summary="Detailed clinical intake completed cleanly.",
        )
        payload = CRMDispatcher(fub_api_key="test", webhook_url="http://127.0.0.1/hook").format_fub_payload(dossier)
        msg = payload["message"]
        assert "Meenakshi Sundaram" in msg
        assert "Detailed clinical intake completed cleanly." in msg
        assert_no_real_estate_copy(msg, "CRMDispatcher message")


# ==============================================================================
# F5: closer/ Telephony, Voice Fallback, Guardrails & Evals (5 tests)
# ==============================================================================


class TestTier1F5TelephonyAndIndicModules:
    async def test_f5_indic_neural_engine_402_triggers_cooldown_and_wav_fallback(
        self, mock_sarvam_402, mock_edge_tts_wav
    ):
        from closer.telephony.indic_neural_engine import IndicNeuralVoiceEngine

        engine = IndicNeuralVoiceEngine()
        audio, ext = await engine.synthesize(
            "வணக்கம், Amura Health Velachery clinic-ல இருந்து பேசுறேன்.",
            language="tamil",
            dialect="chennai_tanglish",
        )
        assert IndicNeuralVoiceEngine._sarvam_cooldown_until > 0.0
        assert audio is not None and is_valid_audio_bytes(audio)
        assert ext in {"wav", "mp3"}

    def test_f5_bland_telephony_engine_amura_prompts_zero_real_estate(self):
        from closer.telephony.bland_engine import CLOSER_PROMPT_TEMPLATES, FIRST_SENTENCES

        for k, prompt in CLOSER_PROMPT_TEMPLATES.items():
            assert_no_real_estate_copy(prompt, f"CLOSER_PROMPT_TEMPLATES[{k}]")
        for k, sentence in FIRST_SENTENCES.items():
            assert_no_real_estate_copy(sentence, f"FIRST_SENTENCES[{k}]")

    def test_f5_nemo_enterprise_guardrails_clinical_protection(self):
        from closer.guardrails.nemo_engine import NeMoEnterpriseGuardrails

        rails = NeMoEnterpriseGuardrails()
        safe_check = rails.evaluate_input("I have chest pain and trouble breathing")
        assert safe_check.allowed is False
        rx_check = rails.evaluate_input("Prescribe me 20 units insulin")
        assert rx_check.allowed is False

    async def test_f5_telephony_server_status_and_voice_demos(self, telephony_client: httpx.AsyncClient):
        r_status = await telephony_client.get("/api/status")
        assert r_status.status_code == 200
        assert r_status.json()["status"] == "operational"

        r_demos = await telephony_client.get("/api/voice/demos")
        assert r_demos.status_code == 200
        demos_json = json.dumps(r_demos.json(), ensure_ascii=False)
        assert_no_real_estate_copy(demos_json, "telephony /api/voice/demos")

    def test_f5_qualification_extractor_clinical_fields(self):
        from closer.qualification.extractor import QualificationExtractor

        ext = QualificationExtractor()
        summary = ext.extract_from_transcript(
            [
                {"role": "user", "content": "My HbA1c is 8.5 and I live in Velachery, Chennai."},
                {"role": "assistant", "content": "Amura Health physician consultation is available tomorrow."},
            ]
        )
        assert summary is not None
        assert_no_real_estate_copy(json.dumps(summary, default=str), "QualificationExtractor")


# ==============================================================================
# F6: Backend API & Vercel Serverless Layer (6 tests)
# ==============================================================================


class TestTier1F6BackendAPIAndVercel:
    async def test_f6_api_health_operational(self, api_client: httpx.AsyncClient):
        resp = await api_client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "operational"
        assert body["conversation_engine_ready"] is True

    async def test_f6_api_turn_contract_schema_and_non_undefined(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/turn",
            json={
                "session_id": "t1_f6_turn",
                "utterance": amura_utterances["calm_en"],
                "market_mode": "india",
                "voice": "maya_en",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        missing = REQUIRED_TURN_KEYS - set(body.keys())
        assert not missing, f"Missing /api/turn keys: {missing}"
        assert body["reply"] and "undefined" not in body["reply"].lower()
        assert body["detected_emotion"] in VALID_EMOTIONS
        assert body["audio_mime"] in {"audio/wav", "audio/mpeg", "none"}

    async def test_f6_api_tts_endpoint_maya_en_alias_and_playable_or_clean_fallback(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/api/tts",
            json={"text": "Welcome to Amura Health in Velachery, Chennai.", "voice": "maya_en", "emotion": "calm"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("voice_resolved") in {"en-US-AvaNeural", "en-IN-NeerjaExpressiveNeural", "en-US-AriaNeural"} or "Ava" in json.dumps(body)
        if body.get("audio_base64"):
            raw = base64.b64decode(body["audio_base64"])
            assert is_valid_audio_bytes(raw)
            assert not is_160hz_synthetic_beep(raw)

    async def test_f6_api_call_demo_mode_and_get_status(self, api_client: httpx.AsyncClient):
        resp = await api_client.post(
            "/api/call",
            json={
                "phone_number": "+919840012345",
                "patient_name": "Karthik Subramanian",
                "language": "tamil",
                "scenario": "metabolic_intake",
                "consent_confirmed": True,
                "mode": "demo",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["call_id"]
        assert body["status"] in {"demo_simulated", "dispatched", "queued"}

        status_resp = await api_client.get(f"/api/call/{body['call_id']}")
        assert status_resp.status_code == 200
        assert status_resp.json()["call_id"] == body["call_id"]

    async def test_f6_api_call_live_mode_with_mocked_bland(
        self, api_client: httpx.AsyncClient, mock_bland_success
    ):
        resp = await api_client.post(
            "/api/call",
            json={
                "phone_number": "+919840012345",
                "patient_name": "Ananya Iyer",
                "language": "english",
                "scenario": "appointment_reminder",
                "consent_confirmed": True,
                "mode": "live",
                "override_trai_window": True,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["call_id"] == "bland_e2e_call_001"
        assert body["status"] == "dispatched"
        mock_bland_success.assert_awaited_once()

    def test_f6_vercel_json_and_api_entrypoints_unified(self):
        vercel_cfg = json.loads((ROOT_DIR / "vercel.json").read_text(encoding="utf-8"))
        redirects = vercel_cfg.get("redirects", [])
        assert any(r.get("destination") == "/#voice-studio" for r in redirects)
        rewrites = vercel_cfg.get("rewrites", [])
        assert any("/api" in r.get("source", "") for r in rewrites)
        for ep in ("index.py", "health.py", "turn.py", "call.py", "tts.py"):
            assert (ROOT_DIR / "api" / ep).is_file(), f"Missing Vercel entrypoint api/{ep}"


# ==============================================================================
# F7: Obsidian Showcase Frontend, Soundboard & ROI (5 tests)
# ==============================================================================


class TestTier1F7ShowcaseFrontendAndSoundboard:
    def test_f7_index_html_preserves_obsidian_luxury_without_onlinewebfonts(self):
        html = (ROOT_DIR / "index.html").read_text(encoding="utf-8")
        assert "db.onlinewebfonts.com" not in html
        for marker in (".bg-video", "stats-footer", "voice-studio", "roi", "demoModal", "desktopSignInBtn"):
            assert marker in html, f"Preserved obsidian design element '{marker}' missing from index.html"

    def test_f7_index_html_healthcare_copy_and_outbound_call_ui(self):
        html = (ROOT_DIR / "index.html").read_text(encoding="utf-8")
        assert_no_real_estate_copy(html, "index.html")
        assert "amura" in html.lower()
        assert "velachery" in html.lower() or "chennai" in html.lower()
        assert "/api/call" in (ROOT_DIR / "main.js").read_text(encoding="utf-8") or "call" in html.lower()

    def test_f7_styles_css_header_stacking_and_contrast_fixed(self):
        css = (ROOT_DIR / "styles.css").read_text(encoding="utf-8")
        assert ".dossier-badge.green" in css or ".dossier-badge .green" in css or "dossier-badge.green" in css
        # .page must not trap .header.is-scrolled below .extended-content (z-index: 2)
        page_block = re.search(r"\.page\s*\{[^}]*\}", css)
        assert page_block is not None
        assert "z-index: 1;" not in page_block.group(0) or "z-index: 100" in css

    def test_f7_main_js_defines_studio_handlers_and_reply_guards(self):
        js = (ROOT_DIR / "main.js").read_text(encoding="utf-8")
        assert_no_real_estate_copy(js, "main.js")
        assert "function setStudioCadence" in js or "window.setStudioCadence" in js
        assert "function setAcousticMode" in js or "window.setAcousticMode" in js
        assert "scen-voice-" in js
        assert "ta-IN" in js and "hi-IN" in js

    @pytest.mark.parametrize(
        "filename",
        [
            "en_opener.wav",
            "en_objection.wav",
            "en_closing.wav",
            "ta_opener.mp3",
            "ta_objection.mp3",
            "ta_closing.mp3",
            "hi_opener.mp3",
            "hi_objection.mp3",
            "hi_closing.mp3",
        ],
    )
    async def test_f7_soundboard_audio_served_with_valid_headers(
        self, api_client: httpx.AsyncClient, filename: str
    ):
        resp = await api_client.get(f"/demos/{filename}")
        assert resp.status_code == 200
        assert is_valid_audio_bytes(resp.content), f"Invalid audio header in /demos/{filename}"


# ==============================================================================
# F8: Secondary Assets, Mobile & Founder Playbook (5 tests)
# ==============================================================================


class TestTier1F8SecondaryAssetsAndPlaybook:
    async def test_f8_presentation_html_pivoted_to_amura_healthcare(self, api_client: httpx.AsyncClient):
        resp = await api_client.get("/presentation")
        assert resp.status_code == 200
        assert "amura" in resp.text.lower()
        assert_no_real_estate_copy(resp.text, "presentation.html")

    async def test_f8_commercial_html_pivoted_to_healthcare(self, api_client: httpx.AsyncClient):
        resp = await api_client.get("/commercial")
        assert resp.status_code == 200
        assert any(w in resp.text.lower() for w in ("amura", "patient", "clinic", "hospital", "health"))
        assert_no_real_estate_copy(resp.text, "commercial.html")

    def test_f8_closer_mobile_healthcare_copy_and_mic_permission(self):
        mobile_dir = ROOT_DIR / "closer_mobile"
        assert mobile_dir.is_dir()
        mobile_html = list(mobile_dir.glob("**/*.html"))
        assert len(mobile_html) >= 1
        for p in mobile_html:
            if "node_modules" in p.parts:
                continue
            assert_no_real_estate_copy(p.read_text(encoding="utf-8", errors="ignore"), str(p))
        plist_files = [p for p in mobile_dir.glob("**/Info.plist") if "node_modules" not in p.parts]
        if plist_files:
            assert any("NSMicrophoneUsageDescription" in p.read_text(encoding="utf-8") for p in plist_files)

    def test_f8_demos_sanitized_no_personal_phone_leak(self):
        demos_dir = ROOT_DIR / "demos"
        leaked_dirs = [p for p in demos_dir.glob("call_9456750852*")]
        assert not leaked_dirs, f"Unsanitized personal phone demo path remains: {leaked_dirs}"

    def test_f8_amura_founder_playbook_complete(self):
        playbook_path = ROOT_DIR / "docs" / "AMURA_FOUNDER_PLAYBOOK.md"
        assert playbook_path.is_file(), "Missing docs/AMURA_FOUNDER_PLAYBOOK.md"
        doc = playbook_path.read_text(encoding="utf-8")
        low = doc.lower()
        for required_topic in ("108", "dpdp", "trai", "160", "sarvam", "emotion", "amura", "velachery"):
            assert required_topic in low, f"Founder playbook missing required topic: {required_topic}"


# ==============================================================================
# F9: Offline Isolation, Session Hygiene & DB Safety (5 tests)
# ==============================================================================


class TestTier1F9OfflineIsolationAndSessionHygiene:
    async def test_f9_repo_learning_db_untouched_during_turns(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav
    ):
        repo_db = ROOT_DIR / "data" / "closer_learning.db"
        before = repo_db.stat() if repo_db.exists() else None
        await api_client.post(
            "/api/turn",
            json={"session_id": "t1_f9_db", "utterance": amura_utterances["calm_en"], "market_mode": "india"},
        )
        await api_client.post("/api/reset", json={"session_id": "t1_f9_db", "market_mode": "india"})
        after = repo_db.stat() if repo_db.exists() else None
        if before and after:
            assert (before.st_mtime_ns, before.st_size) == (after.st_mtime_ns, after.st_size)

    async def test_f9_session_isolation_independent_dossiers(
        self, api_client: httpx.AsyncClient, mock_edge_tts_wav
    ):
        await api_client.post(
            "/api/turn",
            json={"session_id": "patient_alpha", "utterance": "My name is Arvind and I have diabetes.", "market_mode": "india"},
        )
        r_beta = await api_client.post(
            "/api/turn",
            json={"session_id": "patient_beta", "utterance": "Hello, asking about PCOD care.", "market_mode": "india"},
        )
        assert r_beta.status_code == 200
        assert "Arvind" not in json.dumps(r_beta.json()["dossier"])

    async def test_f9_api_reset_returns_clean_clinical_greeting(self, api_client: httpx.AsyncClient):
        resp = await api_client.post(
            "/api/reset",
            json={"session_id": "t1_f9_reset", "market_mode": "india", "sector": "amura_metabolic"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert_no_real_estate_copy(body["greeting"], "/api/reset greeting")

    async def test_f9_offline_socket_guard_blocks_external_hosts(self):
        if os.environ.get("CLOSER_RUN_LIVE_E2E") == "1":
            pytest.skip("Skipped when CLOSER_RUN_LIVE_E2E=1")
        async with httpx.AsyncClient() as client:
            with pytest.raises(httpx.ConnectError):
                await client.get("https://huggingface.co/")

    async def test_f9_leads_endpoint_serves_clinical_records(self, api_client: httpx.AsyncClient):
        resp = await api_client.get("/api/leads")
        assert resp.status_code == 200
        leads = resp.json()
        assert isinstance(leads, list)
        assert_no_real_estate_copy(json.dumps(leads), "/api/leads")


# ==============================================================================
# F10: Release Readiness Contracts (5 tests)
# ==============================================================================


class TestTier1F10ReleaseReadinessContracts:
    @pytest.mark.parametrize("path", ["/", "/landing", "/index.html"])
    async def test_f10_landing_routes_return_200(self, api_client: httpx.AsyncClient, path: str):
        resp = await api_client.get(path)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    @pytest.mark.parametrize("path", ["/console", "/dashboard", "/admin"])
    async def test_f10_console_routes_redirect_to_voice_studio(self, api_client: httpx.AsyncClient, path: str):
        resp = await api_client.get(path, follow_redirects=False)
        assert resp.status_code in {302, 307}
        assert resp.headers.get("location") == "/#voice-studio"

    async def test_f10_turn_alias_matches_api_turn_contract(
        self, api_client: httpx.AsyncClient, amura_utterances, mock_edge_tts_wav
    ):
        resp = await api_client.post(
            "/turn",
            json={"session_id": "t1_f10_alias", "utterance": amura_utterances["calm_en"], "market_mode": "india"},
        )
        assert resp.status_code == 200
        missing = REQUIRED_TURN_KEYS - set(resp.json().keys())
        assert not missing, f"/turn alias missing keys: {missing}"

    async def test_f10_llm_models_active_and_select_endpoints(self, api_client: httpx.AsyncClient):
        r_models = await api_client.get("/api/llm_models")
        assert r_models.status_code == 200
        assert isinstance(r_models.json().get("models"), list)
        r_active = await api_client.get("/api/llm_active")
        assert r_active.status_code == 200
        r_sel = await api_client.post("/api/llm_select", json={"model_id": "llama-3.3-70b"})
        assert r_sel.status_code == 200 and r_sel.json()["success"] is True

    async def test_f10_voices_capabilities_and_daily_reel_healthcare(self, api_client: httpx.AsyncClient):
        r_caps = await api_client.get("/api/voices/capabilities")
        assert r_caps.status_code == 200
        assert "dialects" in r_caps.json()
        r_reel = await api_client.get("/api/daily-reel")
        assert r_reel.status_code == 200
        assert_no_real_estate_copy(json.dumps(r_reel.json()), "/api/daily-reel")
