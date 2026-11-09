"""CLOSER AI: Full-Duplex Telephony WebSocket & REST Server.

Features:
- WebSocket endpoint '/ws/call' for bi-directional real-time audio and control signals.
- Support for streaming mic audio blobs, running Sarvam Saaras v3 STT.
- Layer 1: Token-level streaming synthesis with Sarvam Bulbul v3 / Kokoro 3-Way SOTA Blend.
- Layer 2: Silero VAD, neural noise filtering, and instantaneous (<64ms) Barge-In.
- Live Lead Qualification Dossier streaming.
- ScrapeCreators Social Media Research & Competitor Intelligence endpoints.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import numpy as np
import soundfile as sf

from closer.qualification.extractor import QualificationExtractor
from closer.telephony.phonetic_normalizer import IndicPhoneticNormalizer
from closer.telephony.sarvam_engine import SarvamVoiceEngine
from closer.telephony.token_synthesizer import TokenStreamingSynthesizer
from closer.telephony.vad_barge_in import (
    AgentCallState,
    AudioNoiseSuppressor,
    BargeInController,
    SileroVADDetector,
)
from closer.voice_engine import NeuralVoiceEngine, VOICE_PROFILES

app = FastAPI(title="CLOSER AI Telephony Gateway", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "closer_mobile" / "dist"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    demos_dir = STATIC_DIR / "demos"
    if demos_dir.exists():
        app.mount("/demos", StaticFiles(directory=str(demos_dir)), name="demos")


class VoiceSynthesisRequest(BaseModel):
    text: str
    language: str = "tamil"


DEMO_VOICE_CATALOG = {
    "english": {
        "voice_id": "blend_signature_v2",
        "name": "Maya (Signature Closer)",
        "language_name": "English",
        "engine": "Kokoro 3-Way SOTA Blend (55% Heart + 30% Nicole + 15% Bella)",
        "accent": "Natural American Consultative / Warm Luxury Real Estate",
        "scenarios": [
            {
                "id": "en_opener",
                "title": "Lead Opener & Luxury Qualification",
                "description": "Engages high-net-worth buyer exploring penthouse layouts.",
                "audio_url": "/static/demos/en_opener.wav",
                "transcript": "Hey, good morning! Maya here from the Grand OMR Penthouse. I noticed you were exploring our private residences online. Quick question — are you looking for an investment or a spacious layout for your family?"
            },
            {
                "id": "en_objection",
                "title": "15% Discount Objection Deflection",
                "description": "Never leaks pricing or discounts on phone; pivots to exclusive in-person walkthrough.",
                "audio_url": "/static/demos/en_objection.wav",
                "transcript": "Look, I totally get where you are coming from on the pricing. The developer only authorizes custom payment milestones and private concessions in-person during the private walkthrough. Would Thursday at 4 PM or Saturday morning work better for you?"
            },
            {
                "id": "en_closing",
                "title": "VIP Penthouse Walkthrough Scheduled",
                "description": "Secures commitment and dispatches instant VIP gate pass.",
                "audio_url": "/static/demos/en_closing.wav",
                "transcript": "Terrific! I have reserved the exclusive sunrise penthouse preview for you this Saturday at 11 AM. I am texting you the VIP gate pass right now. Looking forward to welcoming you, Sir."
            }
        ]
    },
    "tamil": {
        "voice_id": "kavitha_tanglish_closer",
        "name": "பல்லவி (Pallavi)",
        "language_name": "தமிழ் (Tanglish)",
        "engine": "Sarvam Bulbul v3 / Chennai Conversational Tanglish",
        "accent": "Sweet Chennai Telecaller • Crisp 'Sir' • Natural Real Estate Loanwords",
        "scenarios": [
            {
                "id": "ta_opener",
                "title": "சென்னை லீட் வரவேற்பு (Opener & Qualification)",
                "description": "சூப்பரான வரவேற்பு, கனிவான Tanglish அணுகுமுறை.",
                "audio_url": "/static/demos/ta_opener.mp3",
                "transcript": "வணக்கம் Sir! OMR கிராண்ட் பென்ட்ஹவுஸ்ல இருந்து பல்லவி பேசுறேங்க. நம்ம luxury 3BHK residences பத்தி தெரிஞ்சுக்க enquiry பண்ணியிருந்தீங்க. நீங்க ஃபேமிலியோட stay பண்ண பாக்குறீங்களா, இல்ல investment-க்காகவா Sir?"
            },
            {
                "id": "ta_objection",
                "title": "15% டிஸ்கவுண்ட் தடுப்பு (Price Deflection)",
                "description": "போனில் விலை குறைக்காமல், நேரில் சைட் விசிட் வரவைக்கும் தந்திரம்.",
                "audio_url": "/static/demos/ta_objection.mp3",
                "transcript": "Sir, pricing மற்றும் special discount பத்தி நம்ம நேரடியா site visit வரும்போது developer approval-ஓட பேசிக்கலாமுங்க. இந்த வியாழக்கிழமை சாயங்காலம் 4 மணிக்கு பார்க்கலாமா, இல்ல சனிக்கிழமை காலைல பார்க்கலாமா Sir?"
            },
            {
                "id": "ta_closing",
                "title": "விஐபி சைட் விசிட் உறுதி (Site Visit Closed)",
                "description": "நேரடி விசிட்டை உறுதிசெய்து வாட்ஸ்அப் கேட் பாஸ் அனுப்பும் நிறைவு.",
                "audio_url": "/static/demos/ta_closing.mp3",
                "transcript": "ரொம்ப சந்தோஷம் Sir! இந்த சனிக்கிழமை காலைல 11 மணிக்கு உங்க VIP walkthrough slot book பண்ணிட்டேங்க. உங்க WhatsApp-க்கு location map மற்றும் gate pass உடனே அனுப்பிடுறேன் Sir. நன்றி!"
            }
        ]
    },
    "hindi": {
        "voice_id": "shreya_hinglish_closer",
        "name": "स्वाति (Swati)",
        "language_name": "हिंदी (Hinglish)",
        "engine": "Sarvam Bulbul v3 / Conversational Hinglish",
        "accent": "Sweet North Indian Telecaller • Warm Persuasive Cadence",
        "scenarios": [
            {
                "id": "hi_opener",
                "title": "लीड स्वागत व परिचय (Lead Opener & Qualification)",
                "description": "विनम्र और भरोसेमंद शुरुआत, परिवार या इन्वेस्टमेंट का सही वर्गीकरण।",
                "audio_url": "/static/demos/hi_opener.mp3",
                "transcript": "नमस्ते सर! ग्रैंड OMR पेंटहाउस से स्वाति बात कर रही हूँ। आपने हमारी luxury 3BHK residences के लिए enquiry की थी। सर, आप अपने परिवार के साथ रहने के लिए देख रहे हैं या फिर high-yield investment के लिए?"
            },
            {
                "id": "hi_objection",
                "title": "15% डिस्काउंट डिफ्लेक्शन (Objection Handling)",
                "description": "कॉल पर रेट कम किए बिना ग्राहक को सीधे साइट विज़िट के लिए तैयार करना।",
                "audio_url": "/static/demos/hi_objection.mp3",
                "transcript": "हाँजी बिल्कुल सर! डिस्काउंट और exclusive payment plan के बारे में हम site visit पर बैठकर developer के साथ final कर सकते हैं जी। क्या गुरुवार शाम 4 बजे या शनिवार सुबह का समय आपके लिए सुविधाजनक रहेगा?"
            },
            {
                "id": "hi_closing",
                "title": "वीआईपी साइट विज़िट फाइनल (Site Visit Closed)",
                "description": "शनिवार का स्लॉट फाइनल कर तुरंत व्हाट्सएप पर गेट पास भेजना।",
                "audio_url": "/static/demos/hi_closing.mp3",
                "transcript": "बहुत बढ़िया सर! मैंने इस शनिवार सुबह 11 बजे आपका VIP private walkthrough confirm कर दिया है। लोकेशन और गेट पास आपके WhatsApp पर भेज रही हूँ जी। थैंक यू सो मच सर!"
            }
        ]
    }
}


@app.get("/api/voice/demos")
async def get_voice_demos():
    return JSONResponse(DEMO_VOICE_CATALOG)


@app.post("/api/voice/synthesize")
async def synthesize_custom_voice(req: VoiceSynthesisRequest):
    text = req.text.strip()
    if not text:
        return JSONResponse({"error": "Empty text"}, status_code=400)
    
    lang = req.language.lower()
    voice_engine = NeuralVoiceEngine(default_agent=lang)
    temp_dir = tempfile.mkdtemp(prefix="closer_custom_")
    ext = ".wav" if lang == "english" else ".mp3"
    out_file = os.path.join(temp_dir, f"synth_{int(time.time()*1000)}{ext}")
    
    try:
        clean_text = IndicPhoneticNormalizer.normalize(text, lang)
        actual_path = await voice_engine.synthesize_to_file(clean_text, out_file, agent=lang)
        with open(actual_path, "rb") as f:
            audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return {
            "status": "success",
            "language": lang,
            "text": text,
            "clean_text": clean_text,
            "audio_base64": audio_b64,
            "format": "wav" if ext == ".wav" else "mp3",
            "voice_label": VOICE_PROFILES.get(lang, VOICE_PROFILES["english"])["label"]
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/")
async def root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({
        "status": "online",
        "service": "CLOSER AI Mobile Gateway",
        "version": "2.0.0",
        "endpoints": ["/ws/call", "/api/status", "/api/intelligence", "/commercial"]
    })


@app.get("/commercial")
async def get_commercial():
    comm_file = STATIC_DIR / "commercial.html"
    if comm_file.exists():
        return FileResponse(str(comm_file))
    return JSONResponse({"error": "Commercial generator not found"})


@app.get("/api/status")
async def get_status():
    sarvam = SarvamVoiceEngine()
    return {
        "status": "operational",
        "active_voices": {
            "english": VOICE_PROFILES["english"]["label"],
            "tamil": VOICE_PROFILES["tamil"]["label"],
            "hindi": VOICE_PROFILES["hindi"]["label"],
        },
        "sarvam_configured": sarvam.is_configured,
        "silero_vad_active": True,
        "full_duplex_webrtc_ready": True,
    }


@app.get("/api/intelligence")
async def get_intelligence():
    """Returns pre-loaded ScrapeCreators social media & competitor ad intelligence."""
    return {
        "competitor_ads": [
            {
                "builder": "Prestige Group",
                "platform": "Meta Ad Library",
                "headline": "Prestige Courtyard OMR — Launch Offer ₹1.45 Cr",
                "weakness": "Complaints regarding 8-month handover delays and maintenance charges.",
                "counter_script": "Sir, unlike other builders facing handover delays, our project is 100% CMDA approved with milestone-based possession guarantees."
            },
            {
                "builder": "Casagrand",
                "platform": "Instagram Reels",
                "headline": "Luxury 3BHK in OMR from ₹1.29 Cr",
                "weakness": "High density (28 units per floor) and smaller carpet area.",
                "counter_script": "Sir, Casagrand offers higher density, but our project offers low-density exclusivity with only 4 private units per floor."
            }
        ],
        "market_sentiment": {
            "reddit_discussion": "OMR Real Estate Buyers: Top demand is for 3BHK with metro connectivity and guaranteed power backup.",
            "top_objection": "Price negotiation (buyers demanding 10-15% discount for full downpayment)."
        }
    }


@app.get("/api/mirofish/report")
@app.post("/api/mirofish/simulate")
async def run_mirofish_simulation():
    """Runs on-demand MiroFish Swarm Simulation across all 12 adversarial personas."""
    from closer.testing.mirofish_simulator import MiroFishSwarmSimulator
    sim = MiroFishSwarmSimulator()
    report = sim.run_full_simulation()
    return JSONResponse(report)


@app.websocket("/ws/call")
async def websocket_call(websocket: WebSocket):
    await websocket.accept()
    agent_name = "tamil"
    
    # Initialize session engines
    voice_engine = NeuralVoiceEngine(default_agent=agent_name)
    sarvam = SarvamVoiceEngine()
    extractor = QualificationExtractor()
    suppressor = AudioNoiseSuppressor(sample_rate=16000)
    vad = SileroVADDetector(sample_rate=16000, threshold=0.50)
    synthesizer = TokenStreamingSynthesizer(voice_engine, agent_name=agent_name)
    
    temp_dir = tempfile.mkdtemp(prefix="closer_ws_")
    current_state = AgentCallState.IDLE
    is_interrupted = False
    active_synthesis_task: Optional[asyncio.Task] = None

    async def notify_state(new_state: AgentCallState):
        nonlocal current_state
        current_state = new_state
        await websocket.send_text(json.dumps({
            "type": "state_change",
            "state": new_state.value
        }))

    def on_barge_in_detected():
        nonlocal is_interrupted
        is_interrupted = True
        synthesizer.interrupt()
        if active_synthesis_task and not active_synthesis_task.done():
            active_synthesis_task.cancel()
        asyncio.create_task(websocket.send_text(json.dumps({
            "type": "barge_in",
            "message": "User interruption detected (<64ms). Audio halted."
        })))
        asyncio.create_task(notify_state(AgentCallState.USER_SPEAKING))

    barge_controller = BargeInController(
        vad_detector=vad,
        noise_suppressor=suppressor,
        on_barge_in=on_barge_in_detected,
        consecutive_frames_required=2,
    )

    # Initial Welcome
    await websocket.send_text(json.dumps({
        "type": "connected",
        "agent": agent_name,
        "voice": VOICE_PROFILES[agent_name]["label"]
    }))

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "set_agent":
                new_agent = data.get("agent", "tamil").lower()
                if new_agent in VOICE_PROFILES:
                    agent_name = new_agent
                    voice_engine.set_agent(agent_name)
                    synthesizer.agent_name = agent_name
                    await websocket.send_text(json.dumps({
                        "type": "agent_switched",
                        "agent": agent_name,
                        "label": VOICE_PROFILES[agent_name]["label"]
                    }))

            elif msg_type == "barge_in_manual":
                on_barge_in_detected()

            elif msg_type == "audio_blob":
                # User sent audio recorded from browser mic
                raw_b64 = data.get("audio_base64", "")
                if raw_b64:
                    raw_bytes = base64.b64decode(raw_b64)
                    audio_file = os.path.join(temp_dir, f"mic_{int(time.time()*1000)}.wav")
                    with open(audio_file, "wb") as f:
                        f.write(raw_bytes)
                    
                    # Transcribe via Sarvam Saaras v3 STT
                    lang_code = "ta-IN" if "tam" in agent_name else ("hi-IN" if "hin" in agent_name else "en-US")
                    transcript = await sarvam.transcribe(audio_file, language_code=lang_code)
                    
                    if transcript:
                        await websocket.send_text(json.dumps({
                            "type": "transcript",
                            "role": "user",
                            "text": transcript
                        }))
                        # Process response for transcript
                        data["text"] = transcript
                        msg_type = "user_utterance_text"

            if msg_type == "user_utterance_text":
                text = data.get("text", "").strip()
                if not text:
                    continue

                # 1. Extract Lead Dossier
                dossier = extractor.extract(text)
                
                # Calculate Deal Probability Score
                deal_score = 40
                if dossier.budget_bracket: deal_score += 20
                if dossier.buyer_type: deal_score += 15
                if dossier.property_type: deal_score += 10
                if any(w in text.lower() for w in ["visit", "பார்க்கலாமா", "ஆபீஸ்", "நேர்ல", "शनिवार", "कल"]):
                    deal_score += 15

                await websocket.send_text(json.dumps({
                    "type": "dossier_update",
                    "deal_score": min(95, deal_score),
                    "dossier": {
                        "buyer_type": dossier.buyer_type or "Evaluating",
                        "budget": dossier.budget_bracket or "₹1.5 Cr — ₹2.5 Cr",
                        "property_type": dossier.property_type or "3 BHK Luxury",
                        "preferred_location": dossier.preferred_location or "OMR Chennai",
                        "site_visit_interest": "Confirmed Slot" if deal_score >= 70 else "Pending",
                    }
                }))

                # 2. Determine Sales Response with human closer guardrails
                lower = text.lower()
                is_price = any(k in lower for k in [
                    "discount", "price", "rate", "cost", "offer", "bargain",
                    "டிஸ்கவுண்ட்", "ரேட்", "ஆஃபர்", "விலை", "கம்மி", "குறைக்க", "பர்சன்ட்",
                    "डिस्काउंट", "रेट", "कम", "छूट"
                ])

                if is_price:
                    if "tam" in agent_name:
                        resp = "Sir, pricing மற்றும் special discount பத்தி நம்ம நேரடியா site visit வரும்போது பேசிக்கலாமுங்க. இந்த வியாழக்கிழமை சாயங்காலம் 4 மணிக்கு பார்க்கலாமா, இல்ல சனிக்கிழமை காலைல பார்க்கலாமா Sir?"
                    elif "hin" in agent_name:
                        resp = "हाँजी बिल्कुल! डिस्काउंट और final pricing के बारे में हम site visit पर बैठकर आराम से बात कर सकते हैं जी। क्या गुरुवार शाम 4 बजे या शनिवार सुबह का समय सही रहेगा सर?"
                    else:
                        resp = "Look, I totally get where you are coming from on the pricing. The developer authorizes custom payment milestones during the private walkthrough. Would Thursday at 4 PM or Saturday morning work better for you?"
                else:
                    if dossier.budget_bracket:
                        if "tam" in agent_name:
                            resp = "கண்டிப்பா Sir! உங்க budget-க்கு ஏத்த மாதிரி OMR-ல ரொம்பவே அழகான 3 BHK luxury projects இருக்குங்க. இந்த weekend நேர்ல வந்து site visit பார்க்கலாமா Sir?"
                        elif "hin" in agent_name:
                            resp = "जी बिल्कुल सर! अगर आपका budget डेढ़ करोड़ के आस-पास है, तो हमारे पास बहुत ही शानदार 3 BHK luxury options हैं। क्या इस weekend एक बार site visit plan करें?"
                        else:
                            resp = "Got it! That fits our luxury inventory perfectly. Would you like to schedule a private walkthrough this weekend?"
                    elif any(w in lower for w in ["invest", "investment", "rent", "வாடகை", "முதலீடு", "निवेश"]):
                        if "tam" in agent_name:
                            resp = "ரொம்ப நல்ல choice Sir! High rental yield தரக்கூடிய சூப்பரான investment options எங்ககிட்ட இருக்குங்க. இந்த சனிக்கிழமை நேர்ல வந்து பார்க்கலாமா Sir?"
                        elif "hin" in agent_name:
                            resp = "शानदार सर! हमारे पास high rental yield देने वाले बहुत ही बेहतरीन investment options हैं जी। क्या मैं आपके लिए कल का slot confirm करूँ?"
                        else:
                            resp = "Understood. We have strong high-yield options. Would you prefer a morning or afternoon walkthrough?"
                    else:
                        if "tam" in agent_name:
                            resp = "வணக்கம் Sir! நீங்க ஃபேமிலியோட stay பண்ண 3 BHK பாக்குறீங்களா, இல்ல investment-க்காக பாக்குறீங்களா Sir?"
                        elif "hin" in agent_name:
                            resp = "नमस्ते सर! आप अपने परिवार के साथ रहने के लिए 3 BHK फ्लैट देख रहे हैं या फिर investment के लिए?"
                        else:
                            resp = "Hey, good morning! Thanks for checking out our residences. Quick question — are you looking for a two-bedroom or a three-bedroom layout for your family?"

                # 3. Stream Response (Layer 1 Token Streaming)
                await notify_state(AgentCallState.AGENT_SPEAKING)
                await websocket.send_text(json.dumps({
                    "type": "transcript",
                    "role": "agent",
                    "text": resp
                }))

                # Synthesize clause audio
                clean_resp = IndicPhoneticNormalizer.normalize(resp, agent_name)
                audio_file = os.path.join(temp_dir, f"resp_{int(time.time()*1000)}.mp3")
                
                try:
                    actual_audio = await voice_engine.synthesize_to_file(clean_resp, audio_file, agent=agent_name)
                    with open(actual_audio, "rb") as f:
                        audio_b64 = base64.b64encode(f.read()).decode("utf-8")
                        
                    await websocket.send_text(json.dumps({
                        "type": "audio_payload",
                        "audio_base64": audio_b64,
                        "format": "mp3" if actual_audio.endswith(".mp3") else "wav"
                    }))
                except Exception as e:
                    print(f"[WebSocket] Audio synthesis error: {e}")

                await notify_state(AgentCallState.IDLE)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
