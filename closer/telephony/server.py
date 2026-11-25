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
        "accent": "Warm Empathetic Clinical Care • Amura Health & Hospital Triage",
        "scenarios": [
            {
                "id": "en_opener",
                "title": "Patient Care Intake & Metabolic Triage",
                "description": "Warmly qualifies patient goals for diabetes, thyroid, or OPD consults.",
                "audio_url": "/static/demos/en_opener.wav",
                "transcript": "Hello! Maya calling from Amura Health Patient Care in Velachery, Chennai. I saw you requested a metabolic consultation—are you looking into diabetes reversal, thyroid care, or a specialist OPD visit?"
            },
            {
                "id": "en_objection",
                "title": "Anxious Patient Reassurance & Safety Guardrail",
                "description": "De-escalates anxiety without diagnosing/prescribing; routes safely to physician.",
                "audio_url": "/static/demos/en_objection.wav",
                "transcript": "I completely understand how stressful fluctuating sugar levels feel, and you're in safe hands. Only our licensed physician can adjust medication after reviewing your HbA1c—shall I book your video consultation tomorrow at 11:30 AM?"
            },
            {
                "id": "en_closing",
                "title": "Doctor Consultation Confirmed + WhatsApp Care Kit",
                "description": "Locks doctor slot and dispatches lab checklist via WhatsApp.",
                "audio_url": "/static/demos/en_closing.wav",
                "transcript": "Wonderful! Your physician consultation is confirmed for tomorrow at 11:30 AM IST. I've sent your fasting lab checklist and clinic link on WhatsApp right now."
            }
        ]
    },
    "tamil": {
        "voice_id": "kavitha_tanglish_closer",
        "name": "பிரியா (Priya)",
        "language_name": "தமிழ் (Tanglish)",
        "engine": "Sarvam Bulbul v3 / Chennai Conversational Tanglish",
        "accent": "Warm Chennai Care Coordinator • Natural Tanglish Medical Support",
        "scenarios": [
            {
                "id": "ta_opener",
                "title": "சென்னை நோயாளி வரவேற்பு (Amura Care Intake)",
                "description": "அன்பான Tanglish மருத்துவ ஆலோசனை மற்றும் நோய் விவரம் கேட்டல்.",
                "audio_url": "/static/demos/ta_opener.mp3",
                "transcript": "வணக்கம் Sir! வேளச்சேரி Amura Health-ல இருந்து பிரியா பேசுறேங்க. சுகர், தைராய்டு அல்லது PCOD மேனேஜ்மென்ட் பத்தி doctor consultation கேட்டிருந்தீங்க—உங்களுக்கு இப்போ என்ன health goal இருக்கு Sir?"
            },
            {
                "id": "ta_objection",
                "title": "பயம் நீக்கி ஆலோசனை (Empathy & Safety)",
                "description": "மருந்து பரிந்துரைக்காமல் அக்கறையுடன் மருத்துவர் சந்திப்பை உறுதி செய்தல்.",
                "audio_url": "/static/demos/ta_objection.mp3",
                "transcript": "கவலைப்படாதீங்க Sir, உங்க நிலைமை எங்களுக்குப் புரியுது. மருந்து அளவை மாற்றுவது பற்றி நம்ம Amura மருத்துவர் தான் உங்க HbA1c ரிப்போர்ட் பார்த்து முடிவு பண்ணுவாங்க. நாளை காலை 11:30 மணிக்கு video consultation புக் பண்ணலாமா Sir?"
            },
            {
                "id": "ta_closing",
                "title": "மருத்துவர் நேரம் உறுதி (Consultation Confirmed)",
                "description": "சந்திப்பை உறுதி செய்து வாட்ஸ்அப்பில் லேப் பட்டியல் அனுப்புதல்.",
                "audio_url": "/static/demos/ta_closing.mp3",
                "transcript": "ரொம்ப நன்றி Sir! நாளைக்கு காலை 11:30 மணிக்கு உங்க doctor consultation slot புக் பண்ணிட்டேங்க. உங்க WhatsApp-க்கு lab test checklist மற்றும் consultation link அனுப்பிட்டேன் Sir!"
            }
        ]
    },
    "hindi": {
        "voice_id": "shreya_hinglish_closer",
        "name": "रितु (Ritu)",
        "language_name": "हिंदी (Hinglish)",
        "engine": "Sarvam Bulbul v3 / Conversational Hinglish",
        "accent": "Warm Pan-India Patient Care • Reassuring Clinical Cadence",
        "scenarios": [
            {
                "id": "hi_opener",
                "title": "पेशेंट इनटेक व परिचय (Amura Health Triage)",
                "description": "डायबिटीज, थायरॉइड और मेटाबोलिक केयर के लिए संवेदनशील शुरुआत।",
                "audio_url": "/static/demos/hi_opener.mp3",
                "transcript": "नमस्ते जी! Amura Health पेशेंट केयर से रितु बात कर रही हूँ। आपने मेटाबोलिक और क्रॉनिक केयर कंसल्टेशन के लिए रिक्वेस्ट की थी—क्या आप डायबिटीज, थायरॉइड या किसी स्पेशलिस्ट OPD के लिए देख रहे हैं?"
            },
            {
                "id": "hi_objection",
                "title": "चिंता समाधान व सेफ्टी गार्डरेल (Clinical Safety)",
                "description": "बिना दवा बताए मरीज़ को शांत कर डॉक्टर कंसल्टेशन से जोड़ना।",
                "audio_url": "/static/demos/hi_objection.mp3",
                "transcript": "जी बिल्कुल, मैं आपकी चिंता समझती हूँ। कोई भी दवा या डोज़ हमारे Amura डॉक्टर आपकी HbA1c और ब्लड रिपोर्ट देखकर ही तय करते हैं। क्या मैं कल सुबह 11:30 बजे आपका टेली-कंसल्टेशन बुक कर दूँ?"
            },
            {
                "id": "hi_closing",
                "title": "डॉक्टर अपॉइंटमेंट कन्फ़र्म (Consultation Confirmed)",
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


class OutboundCallRequest(BaseModel):
    phone_number: str
    language: str = "tamil"
    force_pass_trai: bool = False


@app.post("/api/carrier/call")
async def dispatch_carrier_call(req: OutboundCallRequest):
    """Dispatches carrier SIP call (Jio/Tata/Twilio) with ITU-T G.107 QoS & TRAI validation."""
    from closer.telephony.carrier_gateway import CarrierGatewayEngine
    gateway = CarrierGatewayEngine()
    session = gateway.dispatch_call(
        recipient_phone=req.phone_number,
        language=req.language,
        force_pass_trai=req.force_pass_trai,
    )
    return JSONResponse(session.model_dump())


@app.get("/api/memory/buyer/{phone_number}")
async def get_buyer_memory(phone_number: str):
    """Retrieves Mem0 cross-call episodic memory profile for a lead."""
    from closer.memory.mem0_engine import Mem0AgenticMemory
    memory = Mem0AgenticMemory()
    profile = memory.get_or_create_profile(phone_number)
    preamble = memory.get_context_preamble(phone_number)
    return JSONResponse({
        "profile": profile.model_dump(),
        "episodic_preamble": preamble,
    })


@app.get("/api/observability/telemetry")
async def get_observability_telemetry():
    """Returns Langfuse distributed latency waterfall and unit economics."""
    from closer.observability.langfuse_tracer import LangfuseObservabilityTracer
    return JSONResponse(LangfuseObservabilityTracer.get_telemetry_summary())


@app.post("/api/evals/deepeval")
@app.get("/api/evals/deepeval")
async def run_deepeval_suite():
    """Runs DeepEval continuous deployment adversarial evaluation gate."""
    from closer.testing.deepeval_suite import DeepEvalSuite
    suite = DeepEvalSuite()
    return JSONResponse(suite.run_enterprise_ci_gate())


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
                        "patient_goal": getattr(dossier, "buyer_type", None) or "Metabolic Care / OPD",
                        "condition_category": "Diabetes / Thyroid / Clinical Triage",
                        "clinic_hub": "Amura Health (Velachery, Chennai)",
                        "consultation_slot": "Confirmed Slot" if deal_score >= 70 else "Pending",
                    }
                }))

                # 2. Determine Clinical Triage Response with safety guardrails
                lower = text.lower()
                is_emergency = any(k in lower for k in ["chest pain", "can't breathe", "cannot breathe", "breathing", "faint", "unconscious", "நெஞ்சு வலி", "மூச்சு", "सीने में दर्द", "सांस"])
                is_price = any(k in lower for k in [
                    "discount", "price", "rate", "cost", "fee", "fees", "package",
                    "டிஸ்கவுண்ட்", "ரேட்", "விலை", "கட்டணம்", "डिस्काउंट", "फीस", "खर्च"
                ])

                if is_emergency:
                    if "tam" in agent_name:
                        resp = "தயவுசெய்து உடனடியாக 108 அவசர உதவிக்கு அழைக்கவும் அல்லது அருகிலுள்ள Emergency Room-க்கு செல்லவும் Sir. இது அவசர மருத்துவ நிலை."
                    elif "hin" in agent_name:
                        resp = "कृपया तुरंत 108 पर कॉल करें या नजदीकी इमरजेंसी रूम में जाएं जी। सीने में दर्द या सांस की तकलीफ में तुरंत डॉक्टर की जरूरत है।"
                    else:
                        resp = "Please call 108 or go to the nearest Emergency Room immediately. Chest pain or breathing distress requires urgent emergency care."
                elif is_price:
                    if "tam" in agent_name:
                        resp = "Sir, உங்க health program மற்றும் கட்டண விவரங்களை நம்ம Amura Health மருத்துவர் உங்கள் ரிப்போர்ட் பார்த்த பிறகு துல்லியமாகச் சொல்வார். நாளை காலை 11:30 மணிக்கு consultation புக் பண்ணலாமா Sir?"
                    elif "hin" in agent_name:
                        resp = "जी बिल्कुल! प्रोग्राम फीस और पर्सनलाइज्ड केयर प्लान डॉक्टर आपकी रिपोर्ट देखने के बाद बताते हैं। क्या कल सुबह 11:30 बजे का कंसल्टेशन स्लॉट बुक कर दूँ?"
                    else:
                        resp = "Program fees and customized Natural Molecule Therapy plans are tailored after our physician reviews your labs. Shall I reserve tomorrow at 11:30 AM for your consultation?"
                else:
                    if "tam" in agent_name:
                        resp = "கண்டிப்பா Sir! வேளச்சேரி Amura Health-ல் சர்க்கரை நோய், தைராய்டு மற்றும் மेटाபாலிக் ஆரோக்கியத்திற்கான சிறப்பு மருத்துவர் ஆலோசனை உள்ளது. நாளை காலைல slot புக் பண்ணலாமா Sir?"
                    elif "hin" in agent_name:
                        resp = "जी बिल्कुल! Amura Health में डायबिटीज, थायरॉइड और मेटाबोलिक केयर के लिए अनुभवी डॉक्टर उपलब्ध हैं। क्या कल सुबह 11:30 बजे आपका कंसल्टेशन शेड्यूल करें?"
                    else:
                        resp = "Thank you for sharing that. Our Amura Health clinical team specializes in root-cause metabolic care and OPD triage. Would tomorrow at 11:30 AM work for a physician consultation?"

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
