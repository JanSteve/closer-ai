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
    from src.closer.engine.dialogue import ConversationEngine
    from src.closer.tts.engine import EdgeTTSEngine
    _app_conversation_engine = ConversationEngine(market_mode="usa")
    _app_tts_engine = EdgeTTSEngine()
except Exception:
    _app_conversation_engine = None
    _app_tts_engine = None


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
        greeting = "Namaste! How may I assist you today?" if mode == "india" else "Hello, this is CLOSER AI luxury real estate concierge. How can I assist you today?"
        dossier = {"market_mode": mode}
    return JSONResponse(content={"success": True, "mode": mode, "greeting": greeting, "dossier": dossier})


@app.post("/api/reset")
async def reset_conversation():
    global _app_conversation_engine
    try:
        from src.closer.engine.dialogue import ConversationEngine
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

    if utterance == "PREVIEW_SAMPLE":
        if "en-IN" in voice:
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
            audio_bytes, _ = _app_tts_engine.synthesize_sync(reply, voice=voice)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception:
            audio_b64 = ""

    dossier = _app_conversation_engine.export_dossier().model_dump() if _app_conversation_engine else {}
    return JSONResponse(content={"reply": reply, "audio_base64": audio_b64, "dossier": dossier})
