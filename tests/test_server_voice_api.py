import pytest
from httpx import AsyncClient, ASGITransport
from closer.telephony.server import app

@pytest.mark.asyncio
async def test_get_voice_demos_catalog():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/voice/demos")
        assert resp.status_code == 200
        data = resp.json()
        assert "english" in data
        assert "tamil" in data
        assert "hindi" in data
        
        # Verify English signature is preserved
        assert "Kokoro" in data["english"]["engine"]
        assert len(data["english"]["scenarios"]) == 3
        
        # Verify Tamil has 3 scenarios
        assert len(data["tamil"]["scenarios"]) == 3
        assert "Pallavi" in data["tamil"]["name"]
        
        # Verify Hindi has 3 scenarios
        assert len(data["hindi"]["scenarios"]) == 3
        assert "Swati" in data["hindi"]["name"]

@pytest.mark.asyncio
async def test_voice_synthesis_api_validation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Empty text should fail with 400
        resp = await client.post("/api/voice/synthesize", json={"text": "", "language": "tamil"})
        assert resp.status_code == 400
