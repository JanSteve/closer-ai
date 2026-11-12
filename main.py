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
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))
# Ensure top-level `closer` package (telephony, voice_engine, testing) takes precedence at index 0,
# while `src.closer` remains importable from ROOT_DIR.
if str(ROOT_DIR) in sys.path:
    sys.path.remove(str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

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

# Engine instances & bounded session store for turn handling
_MAX_SESSIONS = 256
_session_engines: dict = {}
_live_leads: list = []

try:
    from src.closer.agent.conversation import ConversationEngine
    from src.closer.voice.tts import EdgeTTSVoiceEngine
    from src.closer.llm.models import list_available_models, get_model_profile
    from src.closer.llm.router import OpenLLMRouter
    from src.closer.integrations.apilayer import APILayerUnifiedClient
    from closer.telephony.indic_neural_engine import IndicNeuralVoiceEngine
    from closer.telephony.dialect_prosody import IndicDialectProsodyEngine, SUPPORTED_DIALECTS
    _app_conversation_engine = ConversationEngine(market_mode="usa")
    _session_engines["default"] = _app_conversation_engine
    _app_tts_engine = EdgeTTSVoiceEngine()
    _app_indic_engine = IndicNeuralVoiceEngine()
    _app_llm_router = _app_conversation_engine.llm_router
    _app_apilayer_client = APILayerUnifiedClient()
except Exception:
    _app_conversation_engine = None
    _app_tts_engine = None
    _app_indic_engine = None
    _app_llm_router = None
    _app_apilayer_client = None


def _get_session_engine(session_id: str = "default"):
    """Retrieves or creates an isolated ConversationEngine per web session."""
    global _app_conversation_engine
    sid = (session_id or "default").strip()[:64] or "default"
    if sid in _session_engines:
        return _session_engines[sid]
    if "ConversationEngine" not in globals():
        return None
    if len(_session_engines) >= _MAX_SESSIONS:
        oldest = next((k for k in _session_engines if k != "default"), None)
        if oldest:
            del _session_engines[oldest]
    eng = ConversationEngine(market_mode="usa")
    _session_engines[sid] = eng
    if sid == "default":
        _app_conversation_engine = eng
    return eng


@app.get("/", response_class=HTMLResponse)
@app.get("/landing", response_class=HTMLResponse)
@app.get("/landing.html", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def serve_landing():
    index_file = ROOT_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse(content="<h1>CLOSER AI: Intelligence Designed To Evolve</h1>", status_code=200)


@app.get("/console")
@app.get("/dashboard")
@app.get("/admin")
async def serve_console():
    """Redirects the internal developer console directly to the investor-approved live voice demo."""
    return RedirectResponse(url="/#voice-studio", status_code=302)


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


@app.get("/commercial", response_class=HTMLResponse)
@app.get("/commercial.html", response_class=HTMLResponse)
@app.get("/film", response_class=HTMLResponse)
@app.get("/ad", response_class=HTMLResponse)
async def serve_commercial():
    comm_file = ROOT_DIR / "commercial.html"
    if comm_file.exists():
        return HTMLResponse(content=comm_file.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse(content="<h1>CLOSER AI Official Launch Film</h1>", status_code=200)


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


@app.get("/demos/{filename}")
async def serve_demo_audio(filename: str):
    file_path = ROOT_DIR / "demos" / filename
    if file_path.exists() and file_path.is_file():
        if filename.endswith(".mp4"):
            media_type = "video/mp4"
        elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
            media_type = "image/jpeg"
        elif filename.endswith(".srt"):
            media_type = "text/plain; charset=utf-8"
        elif filename.endswith(".wav"):
            media_type = "audio/wav"
        else:
            media_type = "audio/mpeg"
        return FileResponse(file_path, media_type=media_type)
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


@app.get("/api/health")
async def get_health():
    """Returns operational readiness, Indic GitHub TTS backend capabilities, and session telemetry."""
    caps = {}
    if _app_indic_engine:
        try:
            caps = _app_indic_engine.get_backend_capabilities()
        except Exception:
            caps = {}
    return JSONResponse(content={
        "status": "operational",
        "active_sessions": len(_session_engines),
        "live_leads_captured": len(_live_leads),
        "tts_engine_ready": _app_tts_engine is not None or _app_indic_engine is not None,
        "conversation_engine_ready": _app_conversation_engine is not None,
        "indic_capabilities": caps,
    })


@app.get("/api/voices/capabilities")
async def get_voice_capabilities():
    """Exposes supported regional Hindi/Tamil dialects and open-source GitHub voice backends."""
    caps = _app_indic_engine.get_backend_capabilities() if _app_indic_engine else {}
    dialects = SUPPORTED_DIALECTS if "SUPPORTED_DIALECTS" in globals() else {}
    return JSONResponse(content={
        "dialects": dialects,
        "capabilities": caps,
    })


@app.get("/api/leads")
async def get_leads():
    base = []
    try:
        from src.closer.web.dashboard import MOCK_LEADS
        base = list(MOCK_LEADS)
    except Exception:
        base = []
    return JSONResponse(content=_live_leads + base)


@app.post("/api/agent/configure")
async def configure_agent(request: Request):
    """Configures a user's business sector, brand name, and market language on their session."""
    try:
        data = await request.json()
    except Exception:
        data = {}
    session_id = str(data.get("session_id", "default"))
    sector = str(data.get("sector", "real_estate"))
    business_name = data.get("business_name")
    market_mode = data.get("market_mode")

    eng = _get_session_engine(session_id)
    if not eng:
        return JSONResponse(status_code=503, content={"error": "Conversation engine unavailable"})
    if hasattr(eng, "configure_business"):
        eng.configure_business(sector=sector, business_name=business_name)
    if market_mode:
        eng.set_market_mode(str(market_mode))
    return JSONResponse(content={
        "success": True,
        "session_id": session_id,
        "sector": getattr(eng, "sector", sector),
        "business_name": getattr(eng, "business_name", business_name),
        "market_mode": eng.market_mode,
    })


@app.post("/api/market_mode")
async def set_market_mode(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    session_id = str(data.get("session_id", "default"))
    mode = str(data.get("mode", "usa")).lower()
    eng = _get_session_engine(session_id)
    if eng:
        eng.set_market_mode(mode)
        greeting = eng.get_initial_greeting()
        dossier = eng.export_dossier().model_dump()
    else:
        if mode == "tamil":
            greeting = "வணக்கம் Sir... CLOSER AI-ல இருந்து பல்லவி பேசுறேங்க. உங்க enquiry பத்தி கொஞ்சம் பேசலாமா Sir?"
        elif mode == "hindi":
            greeting = "नमस्ते जी! क्लोज़र एआई कस्टमर सपोर्ट में आपका स्वागत है। मैं आपकी प्रॉपर्टी सर्च और साइट विज़िट में किस प्रकार सहायता कर सकती हूँ?"
        elif mode == "india":
            greeting = "Namaste! How may I assist you with your luxury property or service inquiry today?"
        else:
            greeting = "Hello, this is CLOSER AI luxury real estate concierge. How can I assist you today?"
        dossier = {"market_mode": mode}
    return JSONResponse(content={"success": True, "session_id": session_id, "mode": mode, "greeting": greeting, "dossier": dossier})


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
async def reset_conversation(request: Request = None):
    global _app_conversation_engine
    session_id = "default"
    mode = "usa"
    sector = "real_estate"
    business_name = None
    if request is not None:
        try:
            body = await request.json()
            if isinstance(body, dict):
                session_id = str(body.get("session_id", "default"))
                mode = str(body.get("market_mode", "usa"))
                sector = str(body.get("sector", "real_estate"))
                business_name = body.get("business_name")
        except Exception:
            pass
    try:
        from src.closer.agent.conversation import ConversationEngine
        fresh = ConversationEngine(market_mode=mode, sector=sector, business_name=business_name)
        _session_engines[session_id] = fresh
        if session_id == "default":
            _app_conversation_engine = fresh
        greeting = fresh.get_initial_greeting()
        dossier = fresh.export_dossier().model_dump()
    except Exception:
        greeting = "Hello, this is CLOSER AI luxury real estate concierge. How can I assist you today?"
        dossier = {"market_mode": mode}
    return JSONResponse(content={"success": True, "session_id": session_id, "greeting": greeting, "dossier": dossier})


def _infer_indic_language(voice: str, utterance: str) -> str:
    v_lower = (voice or "").lower()
    if any(k in v_lower for k in ("tam", "pallavi", "valluvar", "ta-in", "priya")):
        return "tamil"
    if any(k in v_lower for k in ("hi", "swati", "swara", "madhur", "hin", "ritu")):
        return "hindi"
    if any(k in v_lower for k in ("neerja", "prabhat", "india", "en-in")):
        return "india"
    # Auto-detect Devanagari or Tamil script in customer utterance if generic voice passed
    if any("\u0b80" <= ch <= "\u0bff" for ch in utterance):
        return "tamil"
    if any("\u0900" <= ch <= "\u097f" for ch in utterance):
        return "hindi"
    return "usa"


@app.post("/api/turn")
async def process_turn(request: Request):
    global _app_conversation_engine, _app_tts_engine, _app_indic_engine
    try:
        data = await request.json()
    except Exception:
        data = {}

    session_id = str(data.get("session_id", "default"))
    utterance = str(data.get("utterance", "") or "")
    voice = str(data.get("voice", "en-US-AriaNeural") or "en-US-AriaNeural")
    custom_text = str(data.get("text", "") or "")
    rate = data.get("rate")
    pitch = data.get("pitch")
    dialect = data.get("dialect")
    tts_backend = str(data.get("tts_backend", "auto") or "auto")
    sector = data.get("sector")
    business_name = data.get("business_name")
    explicit_mode = data.get("market_mode")

    if not utterance.strip() and not custom_text.strip():
        return JSONResponse(status_code=400, content={"error": "Utterance must not be empty"})
    if len(utterance) > 2000 or len(custom_text) > 2000:
        return JSONResponse(status_code=400, content={"error": "Utterance exceeds 2000 character limit"})

    engine = _get_session_engine(session_id)
    inferred_mode = str(explicit_mode).lower().strip() if explicit_mode else _infer_indic_language(voice, utterance)
    if engine:
        if sector or business_name:
            engine.configure_business(
                sector=str(sector or getattr(engine, "sector", "real_estate")),
                business_name=business_name,
            )
        if inferred_mode in ("tamil", "hindi", "india", "usa") and engine.market_mode != inferred_mode:
            engine.set_market_mode(inferred_mode)

    if utterance in ("PREVIEW_SAMPLE", "STUDIO_SAMPLE"):
        if custom_text:
            reply = custom_text
        elif inferred_mode == "tamil":
            reply = "வணக்கம் Sir... OMR கிராண்ட் பென்ட்ஹவுஸ்ல இருந்து பிரியா பேசுறேங்க. நம்ம luxury 3BHK residences பத்தி தெரிஞ்சுக்க enquiry பண்ணியிருந்தீங்க — நீங்க ஃபேமிலியோட stay பண்ண பாக்குறீங்களா, இல்ல investment-க்காகவா Sir?"
        elif inferred_mode == "hindi":
            reply = "नमस्ते सर... ग्रैंड OMR पेंटहाउस से रितु बात कर रही हूँ। आपने हमारी luxury 3BHK residences के लिए enquiry की थी — आप अपने परिवार के साथ रहने के लिए देख रहे हैं या फिर high-yield investment के लिए?"
        else:
            reply = "Hey, good morning! Maya here from the Grand OMR Penthouse. I noticed you were exploring our private residences online. Quick question — are you looking for an investment or a spacious layout for your family?"
    elif engine:
        reply = engine.process_user_turn(utterance)
    else:
        reply = f"Thank you for your inquiry. CLOSER AI is processing: {utterance}"

    audio_b64 = ""
    audio_fmt = "wav"
    tts_provider = "none"
    tts_error = None

    if inferred_mode in ("tamil", "hindi"):
        try:
            indic_eng = _app_indic_engine or IndicNeuralVoiceEngine()
            spoken_reply = IndicDialectProsodyEngine.humanize(
                reply, language=inferred_mode, dialect=dialect, inject_pauses=True
            )
            audio_bytes, tts_provider, _, audio_fmt = await indic_eng.synthesize(
                text=spoken_reply,
                language=inferred_mode,
                dialect=dialect,
                backend=tts_backend,
                rate=rate,
                pitch=pitch,
            )
            reply = spoken_reply
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as exc:
            tts_error = f"{type(exc).__name__}: {exc}"
    else:
        v_lower = voice.lower()
        if "india" in v_lower or "neerja" in v_lower or inferred_mode == "india":
            actual_voice = "en-IN-NeerjaExpressiveNeural"
        elif "prabhat" in v_lower:
            actual_voice = "en-IN-PrabhatNeural"
        else:
            actual_voice = voice if "-" in voice else "en-US-AriaNeural"
        rate = rate or "-3%"
        pitch = pitch or "+0Hz"
        if _app_tts_engine:
            try:
                audio_bytes, _ = _app_tts_engine.synthesize_sync(reply, voice=actual_voice, rate=rate, pitch=pitch)
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                tts_provider = getattr(_app_tts_engine, "last_provider_used", "EdgeTTSVoiceEngine")
            except Exception as exc:
                audio_b64 = ""
                tts_error = f"{type(exc).__name__}: {exc}"

    dossier = engine.export_dossier().model_dump() if engine else {}
    if dossier and (dossier.get("qualified") or dossier.get("appointment_datetime") or dossier.get("whatsapp_dispatched")):
        lead_record = {
            "session_id": session_id,
            "full_name": dossier.get("full_name", "Web Lead"),
            "market_region": dossier.get("market_region", inferred_mode.upper()),
            "intent_score": dossier.get("intent_score", 0),
            "qualified": dossier.get("qualified", False),
            "appointment": dossier.get("appointment_datetime"),
            "summary": dossier.get("summary", ""),
        }
        existing_idx = next((i for i, item in enumerate(_live_leads) if item.get("session_id") == session_id), None)
        if existing_idx is not None:
            _live_leads[existing_idx] = lead_record
        else:
            _live_leads.insert(0, lead_record)

    llm_info = engine.llm_router.get_active_model_info() if (engine and hasattr(engine, "llm_router") and engine.llm_router) else {
        "model_id": "llama-3.3-70b",
        "parameter_scale": "70 Billion",
        "target_latency_ms": 88,
        "last_tier_used": "reflex_edge"
    }
    return JSONResponse(content={
        "session_id": session_id,
        "market_mode": engine.market_mode if engine else inferred_mode,
        "sector": getattr(engine, "sector", "real_estate") if engine else "real_estate",
        "reply": reply,
        "audio_base64": audio_b64,
        "audio_format": audio_fmt,
        "tts_provider": tts_provider,
        "tts_error": tts_error,
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


@app.get("/api/daily-reel")
async def get_daily_reel():
    """Returns the ready-to-publish Instagram Reel payload for Make.com / Zapier / Automated schedulers."""
    caption = """Are you paying a performance marketing agency ₹2,50,000 every month just to get an Excel sheet of dead leads? 📊📉

Watch what actually happens in India:
1️⃣ Your agency runs Meta ads promising "500 High-Intent Inquiries".
2️⃣ Your telecaller calls 4 hours later.
3️⃣ The customer yells: "WHO ARE YOU?! I NEVER FILLED ANY FORM!" and slams the phone. 📞💥

Harvard Business Review proved this:
Wait just 5 minutes, and lead qualification collapses by -391%. In 4 hours, your ad budget is literally up in smoke. 🔥

Enter CLOSER AI — the autonomous voice sales agent operating across all high-ticket sectors:

🏖️ REAL ESTATE: Maya closes ₹15.5 Cr ECR beach villas in fluent English with instant RERA floor plans.
🩺 HEALTHCARE & CLINICS: Dr. Pallavi books hair transplants & dental VIP consultations in Chennai in conversational Tamil.
☀️ SOLAR & HOME RENO: Swati calculates 40% government rooftop subsidies in Hindi for Delhi NCR homeowners.

⚡ 0.08s Speed-To-Lead: Dials while the lead is still looking at your ad.
📲 Multi-Sector WhatsApp Engine: Drops floor plans, clinic passes & quotes directly on WhatsApp mid-call.
💰 ₹1.55 Economics: Replaces ₹220/call human agency overhead.

Want to see how CLOSER AI works for your exact industry?

👇 COMMENT "AUDIT" BELOW 👇
and our system will automatically DM you:
1. The Multi-Sector Autonomous Lead-Capture Blueprint
2. Live Tamil, Hindi & English Voice Agent Demo Numbers
3. Free Unit Economics Calculator for Real Estate, Clinics & Solar

Save this reel and comment "AUDIT" right now! 🚀

#MetaAds #PerformanceMarketing #LeadGeneration #AIAgents #RealEstateIndia #DentalClinic #HairTransplantIndia #SolarEnergy #EdTech #VoiceAI #Automation #CloserAI"""

    return JSONResponse(content={
        "status": "ready",
        "title": "CLOSER AI — The Performance Agency Trap (Multi-Sector Viral Reel)",
        "video_url": "https://closer-ai-tawny.vercel.app/demos/closer_reel.mp4",
        "cover_url": "https://closer-ai-tawny.vercel.app/demos/closer_reel_poster.jpg",
        "caption": caption,
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "duration_seconds": 68.0,
        "call_to_action_keyword": "AUDIT",
        "sectors": [
            "Real Estate (ECR Beach Villas)",
            "Healthcare Clinics (Dental & Hair Transplants)",
            "Solar & Home Renovation",
            "B2B Performance Marketing Agencies"
        ],
        "target_platforms": ["Instagram Reels", "YouTube Shorts", "Facebook Reels"]
    })
