"""Tests for SOTA Indic Dialects, GitHub Voice Backends, Session Isolation & MiroFish E2E Audit."""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

import main
from closer.telephony.dialect_prosody import IndicDialectProsodyEngine
from closer.telephony.indic_neural_engine import (
    IndicNeuralVoiceEngine,
    INDIC_GITHUB_VOICE_REPOS,
)
from closer.testing.mirofish_simulator import MiroFishSwarmSimulator


class TestIndicDialectProsody:
    def test_tamil_tanglish_colloquial_and_pauses(self):
        formal = "வணக்கம் சார்! உங்கள் விஐபி சைட் விசிட் உறுதி செய்யப்பட்டுள்ளது. வாட்ஸ்அப்பில் அனுப்பப்பட்டுள்ளது."
        spoken = IndicDialectProsodyEngine.humanize(
            formal, language="tamil", dialect="chennai_tanglish", inject_pauses=True
        )
        assert "சார்" not in spoken
        assert "Sir..." in spoken
        assert "கன்ஃபார்ம் பண்ணியாச்சுங்க" in spoken
        assert "அனுப்பிட்டோமுங்க" in spoken

        clauses = IndicDialectProsodyEngine.segment_breath_clauses(spoken)
        assert len(clauses) >= 2
        assert any(pause > 0.1 for _, pause in clauses[:-1])

    def test_hindi_hinglish_dialects_and_fillers(self):
        formal = "नमस्ते सर! आपका विजिट कन्फर्म कर दिया गया है, कृपया शनिवार को पधारें।"
        mumbai = IndicDialectProsodyEngine.humanize(
            formal, language="hindi", dialect="mumbai_hinglish", inject_fillers=True
        )
        assert "नमस्ते सर..." in mumbai
        assert "पक्का कन्फ़र्म" in mumbai or "कन्फर्म" in mumbai
        assert "प्लीज़" in mumbai

    def test_english_passthrough(self):
        raw = "Look, I totally get where you are coming from on the pricing."
        assert IndicDialectProsodyEngine.humanize(raw, language="english") == raw


class TestIndicNeuralVoiceEngine:
    def test_github_repo_registry_and_capabilities(self):
        caps = IndicNeuralVoiceEngine.get_backend_capabilities()
        repos = caps["github_repos"]
        for key in ("indicf5", "indic_parler", "fish_speech", "chatterbox_indic", "orpheus_hi"):
            assert key in repos
            assert "github.com" in repos[key]["url"]
        assert repos["indicf5"]["repo"] == "ai4bharat/IndicF5"
        assert repos["indic_parler"]["repo"] == "ai4bharat/indic-parler-tts"
        assert repos["fish_speech"]["repo"] == "fishaudio/fish-speech"

    @pytest.mark.asyncio
    async def test_fish_speech_routing_when_server_available(self):
        engine = IndicNeuralVoiceEngine(fish_speech_url="http://127.0.0.1:8080")
        fake_wav = b"RIFF" + b"\x00" * 100
        with patch.object(engine, "_synthesize_fish_speech", new=AsyncMock(return_value=fake_wav)):
            audio, provider, _, fmt = await engine.synthesize(
                text="ஹலோ சார், சனிக்கிழமை பார்க்கலாமா?",
                language="tamil",
                dialect="chennai_tanglish",
                backend="fish_speech",
            )
            assert audio == fake_wav
            assert "fishaudio/fish-speech" in provider
            assert fmt == "wav"

    @pytest.mark.asyncio
    async def test_indicf5_routing_when_mocked(self):
        engine = IndicNeuralVoiceEngine()
        fake_wav = b"RIFF" + b"\x01" * 120
        with patch.object(engine, "_synthesize_indicf5", new=AsyncMock(return_value=fake_wav)):
            audio, provider, _, _ = await engine.synthesize(
                text="हाँजी सर, कल सुबह 11 बजे ठीक रहेगा?",
                language="hindi",
                dialect="delhi_hinglish",
                backend="indicf5",
            )
            assert audio == fake_wav
            assert "ai4bharat/IndicF5" in provider

    @pytest.mark.asyncio
    async def test_sarvam_female_twin_mapping_and_no_false_cooldown(self):
        import io
        import numpy as np
        import soundfile as sf
        from closer.telephony.sarvam_engine import SARVAM_FEMALE_VOICES, SarvamVoiceEngine

        assert SARVAM_FEMALE_VOICES["tamil"] == "priya"
        assert SARVAM_FEMALE_VOICES["hindi"] == "ritu"

        sarvam = SarvamVoiceEngine(api_key="sk_test_sarvam_dummy_12345")
        engine = IndicNeuralVoiceEngine(sarvam_engine=sarvam)
        IndicNeuralVoiceEngine._sarvam_cooldown_until = 0.0

        # Prepare tiny valid 24kHz PCM WAV payload
        buf = io.BytesIO()
        sf.write(buf, np.zeros(1200, dtype=np.float32), 24000, format="WAV", subtype="PCM_16")
        sample_wav = buf.getvalue()

        call_count = 0

        async def _fake_synth(text, lang, out_path, customer_mode=False, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                sarvam.last_status_code = 504
                return False
            with open(out_path, "wb") as f:
                f.write(sample_wav)
            sarvam.last_status_code = 200
            return True

        with patch.object(sarvam, "synthesize", side_effect=_fake_synth):
            audio, provider, _, fmt = await engine.synthesize(
                text="ஹலோ சார்... சனிக்கிழமை 11 மணி ஓகேங்களா?",
                language="tamil",
                dialect="chennai_tanglish",
                backend="sarvam",
                customer_mode=False,
            )
            assert len(audio) > 1000
            assert provider == "sarvam/bulbul:v3 (priya)"
            assert fmt == "wav"
            assert IndicNeuralVoiceEngine._sarvam_cooldown_until == 0.0


class TestUserReadyAPIAndSessionIsolation:
    def test_health_capabilities_and_input_validation(self):
        client = TestClient(main.app)
        h = client.get("/api/health")
        assert h.status_code == 200
        assert h.json()["status"] == "operational"

        c = client.get("/api/voices/capabilities")
        assert c.status_code == 200
        assert "chennai_tanglish" in c.json()["dialects"]
        assert "delhi_hinglish" in c.json()["dialects"]

        bad_empty = client.post("/api/turn", json={"utterance": "   ", "voice": "tamil"})
        assert bad_empty.status_code == 400

        bad_long = client.post("/api/turn", json={"utterance": "x" * 2005, "voice": "english"})
        assert bad_long.status_code == 400

    def test_concurrent_session_isolation_and_language_sync(self):
        client = TestClient(main.app)

        r_ta = client.post("/api/turn", json={
            "session_id": "iso_tamil_1",
            "utterance": "OMR 3BHK விலை எவ்வளவு? டிஸ்கவுண்ட் கிடைக்குமா?",
            "voice": "tamil",
            "dialect": "chennai_tanglish",
        })
        assert r_ta.status_code == 200
        d_ta = r_ta.json()
        assert d_ta["market_mode"] == "tamil"
        assert "Bel Air" not in d_ta["reply"]
        assert any("\u0b80" <= ch <= "\u0bff" for ch in d_ta["reply"])

        r_en = client.post("/api/turn", json={
            "session_id": "iso_usa_2",
            "utterance": "Looking for a $4M estate in Bel Air, all cash.",
            "voice": "english",
        })
        assert r_en.status_code == 200
        d_en = r_en.json()
        assert d_en["market_mode"] == "usa"
        assert "Bel Air" not in d_ta["reply"]

    def test_mirofish_live_e2e_audit_with_fake_customer_voices(self):
        sim = MiroFishSwarmSimulator()
        report = sim.run_real_e2e_audit(with_audio=True, include_customer_fish_voice=True)
        assert report["total_personas"] == 5
        assert report["total_turns"] == 10
        assert report["passed_turns"] == 10
        assert report["audio_turns_verified"] == 10
        assert report["pass_rate"] == "100.0%"

    def test_website_ui_and_priya_ritu_turn_routing(self):
        from pathlib import Path

        root = Path(__file__).resolve().parent.parent
        html = (root / "index.html").read_text(encoding="utf-8")
        js = (root / "main.js").read_text(encoding="utf-8")

        for token in ("priya_ta", "ritu_hi", "demoDialectSelect", "demoSectorSelect", "Sarvam bulbul:v3"):
            assert token in html
        for token in ("priya_ta", "ritu_hi", "dialect: selectedDialect", "sector: selectedSector"):
            assert token in js

        client = TestClient(main.app)
        r_priya = client.post("/api/turn", json={
            "session_id": "web_priya_hc",
            "utterance": "Hair transplant consultation fee எவ்வளவு?",
            "voice": "priya_ta",
            "dialect": "coimbatore_tamil",
            "sector": "healthcare",
        })
        assert r_priya.status_code == 200
        d_priya = r_priya.json()
        assert d_priya["market_mode"] == "tamil"
        assert d_priya["sector"] == "healthcare"

        r_ritu = client.post("/api/turn", json={
            "session_id": "web_ritu_solar",
            "utterance": "सब्सिडी और सोलर पैनल प्राइस बताइए।",
            "voice": "ritu_hi",
            "dialect": "delhi_hinglish",
            "sector": "solar",
        })
        assert r_ritu.status_code == 200
        d_ritu = r_ritu.json()
        assert d_ritu["market_mode"] == "hindi"
        assert d_ritu["sector"] == "solar"
