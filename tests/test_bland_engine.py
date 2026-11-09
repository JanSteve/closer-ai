"""Unit tests for Bland AI connector."""

import pytest
from closer.telephony.bland_engine import BlandTelephonyEngine, CLOSER_PROMPT_TEMPLATES


def test_bland_engine_templates():
    assert "tamil" in CLOSER_PROMPT_TEMPLATES
    assert "hindi" in CLOSER_PROMPT_TEMPLATES
    assert "english" in CLOSER_PROMPT_TEMPLATES
    assert "site visit" in CLOSER_PROMPT_TEMPLATES["tamil"]
    assert "special discount" in CLOSER_PROMPT_TEMPLATES["tamil"]


def test_bland_transcript_processing():
    engine = BlandTelephonyEngine(api_key="test_dummy_key")
    transcript = "Hi, my budget is around 1.5 Crores and I am looking for a 3BHK for my family."
    dossier = engine.process_call_transcript(transcript)
    assert dossier["budget"] == "₹1.50 Crores"
    assert dossier["buyer_type"] == "end_user"


@pytest.mark.asyncio
async def test_bland_unconfigured_safeguard():
    engine = BlandTelephonyEngine(api_key="")
    res = await engine.dispatch_phone_call("+919999999999")
    assert res["success"] is False
    assert "BLAND_API_KEY is not configured" in res["error"]
