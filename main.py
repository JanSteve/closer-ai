"""
CLOSER AI — Main Vercel Application Entrypoint.
Exports the top-level FastAPI instance `app` for Vercel Serverless and local execution.
Serves the full-bleed video landing page, static assets, executive console, and speech turn APIs.
"""

import base64
import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "src"))

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

app = FastAPI(
    title="CLOSER AI",
    description="Intelligence Designed To Evolve — Autonomous Conversational Voice Engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Engine instances for turn handling
try:
    from src.closer.agent.conversation import ConversationEngine
    from src.closer.voice.tts import EdgeTTSVoiceEngine
    from src.closer.llm.models import list_available_models, get_model_profile
    from src.closer.llm.router import OpenLLMRouter
    from src.closer.integrations.apilayer import APILayerUnifiedClient
    _app_conversation_engine = ConversationEngine(market_mode="usa")
    _app_tts_engine = EdgeTTSVoiceEngine()
    _app_llm_router = _app_conversation_engine.llm_router
    _app_apilayer_client = APILayerUnifiedClient()
except Exception:
    _app_conversation_engine = None
    _app_tts_engine = None
    _app_llm_router = None
    _app_apilayer_client = None


@app.get("/", response_class=HTMLResponse)
@app.get("/landing", response_class=HTMLResponse)
@app.get("/landing.html", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def serve_landing():
    index_file = ROOT_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse(content="<h1>CLOSER AI: Intelligence Designed To Evolve</h1>", status_code=200)


@app.get("/console", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
async def serve_console():
    try:
        from src.closer.web.dashboard import HTML_TEMPLATE
        return HTMLResponse(content=HTML_TEMPLATE, status_code=200)
    except Exception:
        return HTMLResponse(content="<h1>CLOSER AI Executive Console</h1>", status_code=200)


@app.get("/presentation", response_class=HTMLResponse)
@app.get("/presentation.html", response_class=HTMLResponse)
@app.get("/deck", response_class=HTMLResponse)
@app.get("/pitch", response_class=HTMLResponse)
@app.get("/slides", response_class=HTMLResponse)
async def serve_presentation():
    deck_file = ROOT_DIR / "presentation.html"
    if deck_file.exists():
        return HTMLResponse(content=deck_file.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse(content="<h1>CLOSER AI Presentation Deck</h1>", status_code=200)


@app.get("/styles.css")
async def serve_css():
    css_file = ROOT_DIR / "styles.css"
    if css_file.exists():
        return Response(content=css_file.read_bytes(), media_type="text/css; charset=utf-8")
    return Response(status_code=404)


@app.get("/main.js")
async def serve_js():
    js_file = ROOT_DIR / "main.js"
    if js_file.exists():
        return Response(content=js_file.read_bytes(), media_type="application/javascript; charset=utf-8")
    return Response(status_code=404)


@app.get("/assets/{filename}")
async def serve_asset(filename: str):
    file_path = ROOT_DIR / "assets" / filename
    if file_path.exists() and file_path.is_file():
        media_type = "image/webp" if filename.endswith(".webp") else "application/octet-stream"
        return FileResponse(file_path, media_type=media_type)
    return Response(status_code=404)


@app.get("/fonts/{filename}")
async def serve_font(filename: str):
    file_path = ROOT_DIR / "fonts" / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path, media_type="font/woff2")
    return Response(status_code=404)


@app.get("/api/leads")
async def get_leads():
    try:
        from src.closer.web.dashboard import MOCK_LEADS
        return JSONResponse(content=MOCK_LEADS)
    except Exception:
        return JSONResponse(content=[])


@app.post("/api/market_mode")
async def set_market_mode(request: Request):
    global _app_conversation_engine
    try:
        data = await request.json()
    except Exception:
        data = {}
    mode = data.get("mode", "usa").lower()
    if _app_conversation_engine:
        _app_conversation_engine.set_market_mode(mode)
        greeting = _app_conversation_engine.get_initial_greeting()
        dossier = _app_conversation_engine.export_dossier().model_dump()
    else:
        if mode == "hindi":
            greeting = "नमस्ते जी! क्लोज़र एआई कस्टमर सपोर्ट में आपका स्वागत है। मैं आपकी प्रॉपर्टी सर्च और साइट विज़िट में किस प्रकार सहायता कर सकती हूँ?"
        elif mode == "india":
            greeting = "Namaste! How may I assist you with your luxury property or service inquiry today?"
        else:
            greeting = "Hello, this is CLOSER AI luxury real estate concierge. How can I assist you today?"
        dossier = {"market_mode": mode}
    return JSONResponse(content={"success": True, "mode": mode, "greeting": greeting, "dossier": dossier})


@app.get("/api/llm_models")
async def get_llm_models():
    try:
        from src.closer.llm.models import list_available_models
        return JSONResponse(content={"models": list_available_models()})
    except Exception:
        return JSONResponse(content={"models": []})


@app.get("/api/llm_active")
async def get_active_llm():
    global _app_conversation_engine
    if _app_conversation_engine and hasattr(_app_conversation_engine, "llm_router") and _app_conversation_engine.llm_router:
        return JSONResponse(content=_app_conversation_engine.llm_router.get_active_model_info())
    try:
        from src.closer.llm.models import get_model_profile
        p = get_model_profile("llama-3.3-70b")
        return JSONResponse(content={
            "model_id": "llama-3.3-70b",
            "display_name": p.display_name,
            "parameter_scale": p.parameter_scale,
            "latency_ms": p.target_telephony_latency_ms
        })
    except Exception:
        return JSONResponse(content={"model_id": "llama-3.3-70b"})


@app.post("/api/llm_select")
async def select_llm_model(request: Request):
    global _app_conversation_engine
    try:
        data = await request.json()
    except Exception:
        data = {}
    model_id = data.get("model_id", "llama-3.3-70b")
    if _app_conversation_engine and hasattr(_app_conversation_engine, "set_llm_model"):
        info = _app_conversation_engine.set_llm_model(model_id)
        return JSONResponse(content={"success": True, "model": info})
    return JSONResponse(content={"success": True, "model_id": model_id})


@app.post("/api/reset")
async def reset_conversation():
    global _app_conversation_engine
    try:
        from src.closer.agent.conversation import ConversationEngine
        _app_conversation_engine = ConversationEngine(market_mode="usa")
        greeting = _app_conversation_engine.get_initial_greeting()
        dossier = _app_conversation_engine.export_dossier().model_dump()
    except Exception:
        greeting = "Hello, this is CLOSER AI luxury real estate concierge. How can I assist you today?"
        dossier = {"market_mode": "usa"}
    return JSONResponse(content={"success": True, "greeting": greeting, "dossier": dossier})


@app.post("/api/turn")
async def process_turn(request: Request):
    global _app_conversation_engine, _app_tts_engine
    try:
        data = await request.json()
    except Exception:
        data = {}
    utterance = data.get("utterance", "")
    voice = data.get("voice", "en-US-AriaNeural")
    custom_text = data.get("text", "")
    rate = data.get("rate")
    pitch = data.get("pitch")

    if utterance in ("PREVIEW_SAMPLE", "STUDIO_SAMPLE"):
        if custom_text:
            reply = custom_text
        elif "hi-in" in voice.lower() or "swara" in voice.lower() or "madhur" in voice.lower():
            reply = "नमस्ते! क्लोज़र एआई कस्टमर सपोर्ट में आपका स्वागत है। मैं आपकी प्रॉपर्टी सर्च और साइट विज़िट में किस प्रकार सहायता कर सकती हूँ?"
        elif "en-in" in voice.lower() or "neerja" in voice.lower() or "prabhat" in voice.lower():
            reply = "Namaste! This is CLOSER AI client relationship concierge. How may I assist you with your premium residential inquiry today?"
        else:
            reply = "Hello, this is CLOSER AI luxury real estate concierge. How can I assist you with your estate search today?"
    elif _app_conversation_engine:
        reply = _app_conversation_engine.process_user_turn(utterance)
    else:
        reply = f"Thank you for your inquiry. CLOSER AI is processing: {utterance}"

    audio_b64 = ""
    if _app_tts_engine:
        try:
            audio_bytes, _ = _app_tts_engine.synthesize_sync(reply, voice=voice, rate=rate, pitch=pitch)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception:
            audio_b64 = ""

    dossier = _app_conversation_engine.export_dossier().model_dump() if _app_conversation_engine else {}
    llm_info = _app_conversation_engine.llm_router.get_active_model_info() if (_app_conversation_engine and hasattr(_app_conversation_engine, "llm_router") and _app_conversation_engine.llm_router) else {
        "model_id": "llama-3.3-70b",
        "parameter_scale": "70 Billion",
        "target_latency_ms": 88,
        "last_tier_used": "reflex_edge"
    }
    return JSONResponse(content={
        "reply": reply,
        "audio_base64": audio_b64,
        "dossier": dossier,
        "llm_model": llm_info.get("model_id"),
        "llm_parameters": llm_info.get("parameter_scale"),
        "llm_latency_ms": llm_info.get("target_latency_ms") or 88,
        "llm_tier": llm_info.get("last_tier_used") or "reflex_edge"
    })


# -----------------------------------------------------------------------------
# APILayer Unified Suite / Public-APIs Verification & Enrichment Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/enrich/status")
async def get_enrich_status():
    global _app_apilayer_client
    client = _app_apilayer_client or APILayerUnifiedClient()
    is_live = client.is_configured()
    return JSONResponse(content={
        "configured": is_live,
        "provider": "APILayer Unified Suite (Live API Key Connected)" if is_live else "CLOSER AI Intelligence Engine (High-Fidelity Simulation)",
        "services": ["numverify", "mailboxlayer", "positionstack", "fixer", "currencylayer"]
    })


@app.post("/api/enrich/phone")
async def enrich_phone(request: Request):
    global _app_apilayer_client
    try:
        data = await request.json()
    except Exception:
        data = {}
    phone = data.get("phone", "")
    client = _app_apilayer_client or APILayerUnifiedClient()
    result = client.verify_phone(phone)
    return JSONResponse(content=result)


@app.post("/api/enrich/email")
async def enrich_email(request: Request):
    global _app_apilayer_client
    try:
        data = await request.json()
    except Exception:
        data = {}
    email = data.get("email", "")
    client = _app_apilayer_client or APILayerUnifiedClient()
    result = client.verify_email(email)
    return JSONResponse(content=result)


@app.post("/api/enrich/address")
async def enrich_address(request: Request):
    global _app_apilayer_client
    try:
        data = await request.json()
    except Exception:
        data = {}
    address = data.get("address", "")
    client = _app_apilayer_client or APILayerUnifiedClient()
    result = client.geocode_property(address)
    return JSONResponse(content=result)


@app.post("/api/enrich/currency")
async def enrich_currency(request: Request):
    global _app_apilayer_client
    try:
        data = await request.json()
    except Exception:
        data = {}
    amount = float(data.get("amount", 0))
    from_curr = data.get("from_curr", "USD")
    to_curr = data.get("to_curr", "INR")
    client = _app_apilayer_client or APILayerUnifiedClient()
    result = client.convert_currency(amount, from_curr=from_curr, to_curr=to_curr)
    return JSONResponse(content=result)


@app.post("/api/enrich/lead")
async def enrich_lead(request: Request):
    global _app_apilayer_client, _app_conversation_engine
    try:
        data = await request.json()
    except Exception:
        data = {}
    dossier_data = data if data else (_app_conversation_engine.export_dossier().model_dump() if _app_conversation_engine else {})
    client = _app_apilayer_client or APILayerUnifiedClient()
    result = client.enrich_lead_dossier(dossier_data)
    return JSONResponse(content=result)


@app.post("/api/enrich/key")
async def set_apilayer_key(request: Request):
    global _app_apilayer_client
    try:
        data = await request.json()
    except Exception:
        data = {}
    api_key = data.get("api_key", "").strip()
    _app_apilayer_client = APILayerUnifiedClient(api_key=api_key)
    return JSONResponse(content={
        "success": True,
        "configured": _app_apilayer_client.is_configured(),
        "provider": "APILayer Unified Suite (Live API Key Connected)" if _app_apilayer_client.is_configured() else "CLOSER AI Intelligence Engine (High-Fidelity Simulation)"
    })
