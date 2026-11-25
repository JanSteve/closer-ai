"""
Web Console for CLOSER AI — Amura Health Clinical Voice Triage & Hospital Front-Desk Platform.
Dark Obsidian & Glassmorphism Console supporting standalone HTTP server and Streamlit.
"""

from __future__ import annotations

import base64
import http.server
import json
import os
import socketserver
import sys
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from src.closer.agent.conversation import ConversationEngine
from src.closer.agent.schemas import BuyerDossier, InboundLead, PatientDossier
from src.closer.config import settings
from src.closer.integrations.apilayer import APILayerUnifiedClient
from src.closer.integrations.calendar import CalendarManager
from src.closer.integrations.crm import CRMDispatcher
from src.closer.integrations.telephony import TelephonyManager
from src.closer.voice.tts import EdgeTTSVoiceEngine

# Simulated Amura Health Clinical Intake Pipeline
MOCK_LEADS: List[Dict[str, Any]] = [
    {
        "id": "patient_101",
        "name": "Priya Raman",
        "phone": "+91-98400-11223",
        "concern": "Type-2 Diabetes & HbA1c 8.4% (Velachery)",
        "source": "Amura Web Intake",
        "stage": "Consultation Booked",
        "pathway": "Amura MNT + NMT Reversal",
        "emotion": "Anxious",
        "intent": 95,
        "slot": "Saturday 11:00 AM IST",
        "sentiment": "Priority",
    },
    {
        "id": "patient_102",
        "name": "Karthik Subramanian",
        "phone": "+91-98400-22334",
        "concern": "Fatty Liver & Fasting Insulin (Chennai)",
        "source": "WhatsApp Care Desk",
        "stage": "Clinically Triaged",
        "pathway": "Amura Physician + Coach",
        "emotion": "Calm",
        "intent": 88,
        "slot": "Pending Slot Selection",
        "sentiment": "Positive",
    },
    {
        "id": "patient_103",
        "name": "Meera Nair",
        "phone": "+91-98400-33445",
        "concern": "PCOD & Thyroid Balance (Online Telehealth)",
        "source": "Hospital Front-Desk",
        "stage": "Intake Active",
        "pathway": "Amura MNT + NMT Reversal",
        "emotion": "Confused",
        "intent": 72,
        "slot": "In Conversation",
        "sentiment": "Neutral",
    },
    {
        "id": "patient_104",
        "name": "Arjun Deshmukh",
        "phone": "+91-98200-44556",
        "concern": "Hypertension & Lipid Panel Review",
        "source": "Doctor Referral",
        "stage": "Consultation Booked",
        "pathway": "Tele-Consultation",
        "emotion": "Calm",
        "intent": 92,
        "slot": "Thursday 2:00 PM IST",
        "sentiment": "Positive",
    },
]

_CSS_STYLES = Path(__file__).resolve()  # unused placeholder; inline template below
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>CLOSER AI — Amura Health Clinical Voice Console</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #05070c;
            --surface: rgba(15, 20, 32, 0.78);
            --surface-card: rgba(20, 26, 42, 0.72);
            --surface-hover: rgba(30, 41, 65, 0.85);
            --border: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(255, 255, 255, 0.18);
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.3);
            --gold: #f59e0b;
            --emerald: #10b981;
            --cyan: #22d3ee;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
        body {
            background: var(--bg);
            background-image:
                radial-gradient(1000px circle at 50% -10%, rgba(59, 130, 246, 0.14), transparent 70%),
                radial-gradient(800px circle at 85% 20%, rgba(16, 185, 129, 0.07), transparent 60%);
            color: var(--text-main);
            min-height: 100vh;
            padding: 20px 28px;
            letter-spacing: -0.011em;
        }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 18px; margin-bottom: 16px; flex-wrap: wrap; gap: 16px; }
        .logo-wrap { display: flex; align-items: center; gap: 14px; }
        .brand-icon { width: 40px; height: 40px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.14); border-radius: 10px; display: flex; align-items: center; justify-content: center; overflow: hidden; padding: 3px; }
        .brand-icon img { width: 100%; height: 100%; object-fit: contain; display: block; }
        .logo-title { font-size: 22px; font-weight: 800; letter-spacing: -0.03em; background: linear-gradient(180deg, #ffffff 30%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .badge { background: rgba(59,130,246,0.12); color: #60a5fa; border: 1px solid rgba(59,130,246,0.3); padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700; display: inline-flex; align-items: center; gap: 6px; }
        .status-dot { width: 6px; height: 6px; background: #10b981; border-radius: 50%; box-shadow: 0 0 8px #10b981; }
        .subtitle { font-size: 12.5px; color: var(--text-muted); margin-top: 2px; }
        .telemetry-bar { display: flex; align-items: center; justify-content: space-between; background: rgba(11,15,26,0.85); border: 1px solid var(--border); border-radius: 10px; padding: 8px 16px; margin-bottom: 22px; font-size: 11.5px; overflow-x: auto; white-space: nowrap; gap: 16px; }
        .telemetry-item { display: inline-flex; align-items: center; gap: 6px; color: var(--text-muted); }
        .telemetry-item strong { color: #ffffff; font-weight: 600; }
        .telemetry-pill { background: rgba(16,185,129,0.15); color: var(--emerald); padding: 2px 7px; border-radius: 4px; font-weight: 700; font-size: 10.5px; }
        .market-switch-wrap { display: inline-flex; background: rgba(10,14,24,0.85); border: 1px solid var(--border); border-radius: 9999px; padding: 3px; gap: 4px; flex-wrap: wrap; }
        .btn-market { background: transparent; border: none; color: var(--text-muted); font-size: 12px; font-weight: 700; padding: 6px 14px; border-radius: 9999px; cursor: pointer; transition: all 0.2s ease; }
        .btn-market.active { background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #ffffff; }
        .header-links { display: flex; align-items: center; gap: 14px; }
        .nav-out-link { display: inline-flex; align-items: center; gap: 4px; color: #60a5fa; text-decoration: none; font-size: 12.5px; font-weight: 600; padding: 6px 12px; border-radius: 8px; background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.25); }
        .grid-layout { display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 20px; margin-bottom: 24px; }
        @media(max-width: 1024px) { .grid-layout { grid-template-columns: 1fr; } }
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 22px; backdrop-filter: blur(16px); box-shadow: 0 8px 32px rgba(0,0,0,0.4); display: flex; flex-direction: column; gap: 16px; }
        .card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 14px; }
        .card-title { font-size: 16px; font-weight: 700; display: flex; align-items: center; gap: 10px; color: #ffffff; }
        .vad-container { display: inline-flex; align-items: center; gap: 8px; padding: 4px 12px; background: rgba(0,0,0,0.5); border: 1px solid var(--border); border-radius: 9999px; }
        .vad-waves { display: flex; align-items: center; gap: 2px; height: 16px; }
        .vad-bar { width: 3px; background: #3b82f6; border-radius: 9999px; height: 4px; }
        .vad-container.speaking .vad-bar { background: var(--emerald); }
        .vad-label { font-size: 10.5px; font-weight: 700; color: var(--emerald); letter-spacing: 0.05em; }
        .voice-controls { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; background: rgba(10,14,24,0.7); padding: 12px 16px; border-radius: 12px; border: 1px solid var(--border); }
        .control-group { display: flex; flex-direction: column; gap: 4px; }
        .control-label { font-size: 10.5px; color: var(--text-dim); text-transform: uppercase; font-weight: 700; }
        .voice-select { background: rgba(7,10,18,0.9); border: 1px solid var(--border); color: #ffffff; font-size: 12.5px; padding: 8px 12px; border-radius: 8px; outline: none; }
        .voice-btn-group { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .btn-preview, .btn-barge, .btn-reset, .btn-voice-keys { background: rgba(255,255,255,0.06); border: 1px solid var(--border); color: var(--text-muted); border-radius: 8px; padding: 8px 13px; font-size: 12px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 5px; }
        .btn-barge { background: rgba(239,68,68,0.12); color: #fca5a5; border-color: rgba(239,68,68,0.3); }
        .workflow-stepper { display: flex; align-items: center; gap: 10px; background: rgba(15,23,42,0.55); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 8px 14px; font-size: 11.5px; color: var(--text-muted); overflow-x: auto; white-space: nowrap; }
        .step-item { display: inline-flex; align-items: center; gap: 6px; }
        .step-num { width: 18px; height: 18px; border-radius: 50%; background: rgba(59,130,246,0.25); color: #93c5fd; font-size: 10.5px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
        .chat-box { height: 330px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; padding: 16px; background: rgba(7,10,18,0.75); border-radius: 12px; border: 1px solid var(--border); }
        .msg { padding: 12px 16px; border-radius: 12px; max-width: 86%; font-size: 13.5px; line-height: 1.5; }
        .msg.agent { background: linear-gradient(135deg, rgba(30,58,138,0.35), rgba(15,23,42,0.6)); color: #e2e8f0; align-self: flex-start; border-left: 3px solid #60a5fa; }
        .msg.buyer { background: linear-gradient(135deg, rgba(31,41,55,0.65), rgba(17,24,39,0.8)); color: #f8fafc; align-self: flex-end; border-right: 3px solid var(--emerald); }
        .msg-meta { font-size: 11px; color: var(--text-dim); margin-bottom: 5px; font-weight: 600; }
        .input-row { display: flex; gap: 10px; }
        .input-row input { flex: 1; padding: 13px 16px; background: rgba(7,10,18,0.85); border: 1px solid var(--border); border-radius: 10px; color: #ffffff; font-size: 16px; outline: none; }
        .btn-send { padding: 12px 22px; background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; }
        .btn-voice-call { padding: 12px 20px; background: linear-gradient(135deg, #059669, #10b981); color: white; border: 1px solid rgba(16,185,129,0.4); border-radius: 10px; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; }
        .quick-chips-wrap { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .chips-label { font-size: 11.5px; font-weight: 700; color: var(--text-dim); text-transform: uppercase; }
        .chip { padding: 6px 12px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 9999px; font-size: 12px; color: var(--text-muted); text-decoration: none; }
        .chip-friction { border-color: rgba(245,158,11,0.3); color: #fcd34d; }
        .dossier-nav { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
        .dossier-tab-wrap { display: inline-flex; background: rgba(7,10,18,0.8); border: 1px solid var(--border); border-radius: 8px; padding: 2px; }
        .btn-dossier-tab { background: transparent; border: none; color: var(--text-muted); font-size: 11.5px; font-weight: 600; padding: 4px 10px; border-radius: 6px; cursor: pointer; }
        .btn-dossier-tab.active { background: rgba(255,255,255,0.12); color: #ffffff; }
        .btn-copy-json { background: rgba(59,130,246,0.12); border: 1px solid rgba(59,130,246,0.3); color: #60a5fa; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 6px; cursor: pointer; }
        .dossier-grid { display: flex; flex-direction: column; gap: 10px; background: rgba(7,10,18,0.6); padding: 14px; border-radius: 12px; border: 1px solid var(--border); }
        .dossier-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 13px; }
        .dossier-label { color: var(--text-muted); font-weight: 500; }
        .dossier-val { font-weight: 600; color: #ffffff; text-align: right; }
        .raw-json-box { display: none; background: #030508; border: 1px solid var(--border); border-radius: 12px; padding: 14px; font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #38bdf8; max-height: 280px; overflow-y: auto; white-space: pre-wrap; }
        .intent-box { background: rgba(7,10,18,0.6); padding: 14px; border-radius: 12px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 8px; }
        .intent-header { display: flex; justify-content: space-between; font-size: 12px; }
        .progress-bar-bg { height: 8px; background: rgba(255,255,255,0.08); border-radius: 9999px; overflow: hidden; }
        .progress-bar-fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #10b981); border-radius: 9999px; width: 50%; transition: width 0.4s ease; }
        .tag { font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 700; text-transform: uppercase; }
        .tag-green { background: rgba(16,185,129,0.15); color: var(--emerald); border: 1px solid rgba(16,185,129,0.3); }
        .tag-gold { background: rgba(245,158,11,0.15); color: var(--gold); border: 1px solid rgba(245,158,11,0.3); }
        .tag-blue { background: rgba(59,130,246,0.15); color: #93c5fd; border: 1px solid rgba(59,130,246,0.3); }
        .tag-red { background: rgba(239,68,68,0.2); color: #fca5a5; border: 1px solid rgba(239,68,68,0.45); }
        .kanban { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
        @media(max-width: 768px) { .kanban { grid-template-columns: 1fr; } }
        .kanban-col { background: rgba(10,14,24,0.65); border-radius: 12px; padding: 14px; border: 1px solid var(--border); }
        .kanban-header { font-size: 12px; text-transform: uppercase; font-weight: 700; color: var(--text-dim); margin-bottom: 12px; display: flex; justify-content: space-between; }
        .lead-card { background: rgba(20,26,42,0.7); border: 1px solid var(--border); border-radius: 10px; padding: 12px; margin-bottom: 10px; }
        .lead-name { font-weight: 700; font-size: 13.5px; margin-bottom: 3px; color: #ffffff; }
        .lead-prop { font-size: 11.5px; color: var(--text-muted); margin-bottom: 8px; }
        .roi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 14px; }
        @media(max-width: 768px) { .roi-grid { grid-template-columns: 1fr 1fr; } }
        .stat-box { background: rgba(10,14,24,0.65); border: 1px solid var(--border); border-radius: 12px; padding: 16px; text-align: center; }
        .stat-val { font-size: 24px; font-weight: 800; color: var(--emerald); margin-top: 4px; }
        .stat-label { font-size: 11.5px; color: var(--text-muted); text-transform: uppercase; }
        .apilayer-card { background: linear-gradient(135deg, rgba(15,23,42,0.85), rgba(10,15,30,0.95)); border: 1px solid rgba(59,130,246,0.3); border-radius: 16px; padding: 20px; margin-bottom: 24px; }
        .apilayer-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px; }
        .apilayer-tools-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
        @media(max-width: 1024px) { .apilayer-tools-grid { grid-template-columns: 1fr 1fr; } }
        @media(max-width: 640px) { .apilayer-tools-grid { grid-template-columns: 1fr; } }
        .tool-box { background: rgba(20,26,42,0.65); border: 1px solid var(--border); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; gap: 10px; }
        .tool-box-title { font-size: 12px; font-weight: 700; color: #93c5fd; display: flex; align-items: center; gap: 6px; }
        .tool-input { background: rgba(7,10,18,0.85); border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; color: #ffffff; font-size: 12px; outline: none; width: 100%; }
        .btn-tool-run { background: rgba(59,130,246,0.2); border: 1px solid rgba(59,130,246,0.4); color: #ffffff; font-size: 11.5px; font-weight: 600; padding: 7px 12px; border-radius: 8px; cursor: pointer; text-align: center; }
        .tool-result { background: rgba(7,10,18,0.7); border-radius: 8px; padding: 10px; font-size: 11px; color: #cbd5e1; min-height: 64px; font-family: 'JetBrains Mono', monospace; }
        .modal-backdrop { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 9999; align-items: center; justify-content: center; padding: 16px; }
        .modal-card { background: #0f1420; border: 1px solid rgba(255,255,255,0.15); border-radius: 16px; max-width: 520px; width: 100%; padding: 20px; }
        .modal-input { background: rgba(7,10,18,0.85); border: 1px solid var(--border); border-radius: 8px; padding: 9px 12px; color: #ffffff; font-size: 12.5px; width: 100%; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-wrap">
            <div class="brand-icon"><img src="/assets/logo.webp" alt="CLOSER AI"></div>
            <div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <span class="logo-title">CLOSER AI</span>
                    <span class="badge"><span class="status-dot"></span> AMURA HEALTH TRI-LINGUAL: EN • TA • HI</span>
                </div>
                <div class="subtitle">Amura Health Clinical Voice Triage &amp; Hospital Front-Desk Console (Velachery, Chennai)</div>
            </div>
        </div>

        <div class="market-switch-wrap">
            <button id="btnMarketIndia" class="btn-market active" onclick="switchMarket('india')">🇮🇳 English: Clinical Triage</button>
            <button id="btnMarketTamil" class="btn-market" onclick="switchMarket('tamil')">🇮🇳 தமிழ் (Tamil): Velachery Desk</button>
            <button id="btnMarketHindi" class="btn-market" onclick="switchMarket('hindi')">🇮🇳 हिन्दी (Hindi): Metabolic Care</button>
            <button id="btnMarketUSA" class="btn-market" onclick="switchMarket('english')">🌐 Global Telehealth</button>
        </div>

        <div class="header-links">
            <a href="/presentation" target="_blank" class="nav-out-link">📊 Pitch Deck</a>
            <a href="/" class="nav-out-link" style="background:#ffffff; color:#000000;">← Back to Showcase</a>
        </div>
    </div>

    <div class="telemetry-bar">
        <div class="telemetry-item"><span class="status-dot"></span><span>Clinic: <strong>Amura Health, Velachery</strong></span><span class="telemetry-pill">+91-62-622-62222</span></div>
        <div class="telemetry-item"><span>Guardrails: <strong>108 ER • No Rx/Dx • DPDP</strong></span></div>
        <div class="telemetry-item"><span>LLM Intelligence: <strong id="telemetryLLM">Llama 3.3 70B / Gemini</strong></span><span class="telemetry-pill" id="telemetryLLMPill">CLINICAL SAFE</span></div>
        <div class="telemetry-item"><span>Voice Engine: <strong id="telemetryVoiceEngine">Sarvam v3 / Edge-TTS</strong></span><span class="telemetry-pill">EMOTION PROSODY</span></div>
        <div class="telemetry-item"><span>Unified Suite: <strong id="telemetryAPILayer">APILayer Verified</strong></span></div>
    </div>

    <div class="grid-layout">
        <div class="card">
            <div class="card-header">
                <div class="card-title"><span id="agentConsoleTitle">Amura Health Clinical Care Concierge</span></div>
                <div style="display:flex; align-items:center; gap:12px;">
                    <canvas id="liveAudioWaveform" width="130" height="28" style="border-radius:6px; background:rgba(7,10,18,0.7); border:1px solid var(--border);"></canvas>
                    <div id="vadContainer" class="vad-container listening">
                        <div class="vad-waves"><span class="vad-bar"></span><span class="vad-bar"></span><span class="vad-bar"></span><span class="vad-bar"></span></div>
                        <span id="vadLabel" class="vad-label">● CARE DESK READY</span>
                    </div>
                </div>
            </div>

            <div class="workflow-stepper">
                <div class="step-item"><span class="step-num">1</span> <span><strong>Select Language &amp; Voice</strong> (English, Tamil ta-IN, Hindi hi-IN)</span></div>
                <div class="step-item">→</div>
                <div class="step-item"><span class="step-num">2</span> <span><strong>Test Emotion &amp; 108 Safety</strong> (Anxious HbA1c, Rx refusal, 108 Chest Pain)</span></div>
                <div class="step-item">→</div>
                <div class="step-item"><span class="step-num">3</span> <span><strong>Inspect Clinical Dossier</strong> (Emotion, Safety Flag, DPDP Consent, IST Slot)</span></div>
            </div>

            <div class="voice-controls">
                <div class="control-group">
                    <label class="control-label">Clinical Voice Persona (EN / TA / HI):</label>
                    <select id="voiceSelect" class="voice-select">
                        <optgroup label="🇮🇳 Indian English (Amura Health Front-Desk)">
                            <option value="en-IN-NeerjaExpressiveNeural" selected>Neerja (India Female • Empathetic Care Coordinator)</option>
                            <option value="en-IN-PrabhatNeural">Prabhat (India Male • Clinical Support)</option>
                        </optgroup>
                        <optgroup label="🇮🇳 தமிழ் (Tamil — Velachery Chennai Care Desk)">
                            <option value="ta-IN-PallaviNeural">Pallavi / பல்லவி (Tamil Female • Chennai Care)</option>
                            <option value="ta-IN-ValluvarNeural">Valluvar (Tamil Male • Clinical Coordinator)</option>
                        </optgroup>
                        <optgroup label="🇮🇳 हिन्दी (Hindi — Metabolic Care Coordinator)">
                            <option value="hi-IN-SwaraNeural">Swara / स्वाति (Hindi Female • Empathetic Care)</option>
                            <option value="hi-IN-MadhurNeural">Madhur / मधुर (Hindi Male • Clinical Support)</option>
                        </optgroup>
                        <optgroup label="🌐 Global Telehealth">
                            <option value="en-US-AvaNeural">Maya / Ava (US Female • Expressive Clinical)</option>
                            <option value="en-US-AriaNeural">Aria (US Female • Warm Reassuring)</option>
                        </optgroup>
                    </select>
                </div>

                <div class="control-group">
                    <label class="control-label">Voice Intelligence Engine:</label>
                    <select id="voiceProviderSelect" class="voice-select" onchange="updateVoiceEngineBadge()">
                        <option value="studio" selected>🎙️ Edge-TTS Neural + Browser Fallback</option>
                        <option value="sarvam">🇮🇳 Sarvam AI bulbul:v3 (ta-IN / hi-IN / en-IN)</option>
                        <option value="elevenlabs">✨ ElevenLabs Turbo v2.5</option>
                        <option value="cartesia">⚡ Cartesia Sonic</option>
                    </select>
                </div>

                <div class="control-group" style="min-width:120px;">
                    <label class="control-label">Speed: <span id="lblVoiceRate" style="color:var(--cyan);">+0%</span></label>
                    <input type="range" id="voiceRateSlider" min="-15" max="20" value="0" step="5" oninput="updateRateLabel(this.value)">
                </div>

                <div class="control-group" style="min-width:120px;">
                    <label class="control-label">Pitch: <span id="lblVoicePitch" style="color:var(--gold);">+0Hz</span></label>
                    <input type="range" id="voicePitchSlider" min="-5" max="5" value="0" step="1" oninput="updatePitchLabel(this.value)">
                </div>

                <div class="control-group">
                    <label class="control-label">Foundation LLM:</label>
                    <select id="llmEngineSelect" class="voice-select" onchange="switchLLM(this.value)">
                        <option value="llama-3.3-70b" selected>⚡ Llama 3.3 70B</option>
                        <option value="gemini-2.5-flash">✨ Gemini 2.5 Flash</option>
                        <option value="bloomz-176b">🌐 BLOOMZ 176B</option>
                        <option value="deepseek-v3">🧠 DeepSeek-V3 671B</option>
                        <option value="command-r-plus">🛡️ Command R+ 104B</option>
                        <option value="qwen-2.5-72b">🌏 Qwen 2.5 72B</option>
                    </select>
                </div>

                <div class="voice-btn-group">
                    <button class="btn-preview" onclick="testVoiceSample()">🔊 Test Voice</button>
                    <button class="btn-barge" onclick="simulateBargeIn()">⚡ Barge-In</button>
                    <button class="btn-voice-keys" onclick="openKeyModal()">⚙️ Cloud Keys</button>
                    <button class="btn-reset" onclick="resetCall()">↻ Reset</button>
                </div>
            </div>

            <div class="soundboard-bar" style="background:rgba(255,255,255,0.02); border:1px solid var(--border); border-radius:10px; padding:10px 14px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
                <span style="font-size:12px; font-weight:700; color:var(--cyan);">🩺 Clinical Demo Scenarios:</span>
                <div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <button class="chip" onclick="playMarketingHook('india')" style="cursor:pointer;">🇮🇳 Anxious HbA1c Metabolic Intake</button>
                    <button class="chip" onclick="playMarketingHook('tamil')" style="cursor:pointer;">🇮🇳 Tamil Velachery Diabetes Care</button>
                    <button class="chip" onclick="playMarketingHook('hindi')" style="cursor:pointer;">🇮🇳 Hindi Metabolic Consultation</button>
                    <button class="chip chip-friction" onclick="quickFill('I have severe chest pain and difficulty breathing')" style="cursor:pointer;">🚨 Test 108 Emergency Escalation</button>
                </div>
            </div>

            <div class="chat-box" id="chatBox">
                <div class="msg agent">
                    <div class="msg-meta" id="chatAgentMeta">Neerja (Amura Health Patient Care) • Clinical Triage Active</div>
                    Namaste, this is Neerja from Amura Health Patient Care &amp; Front-Desk Support (Velachery, Chennai). How may I assist you with your metabolic health inquiry or physician consultation today?
                </div>
            </div>

            <div class="input-row">
                <button id="voiceCallBtn" class="btn-voice-call" onclick="toggleHandsFreeVoiceCall()">
                    <span id="voiceCallIcon">🎙️</span> <span id="voiceCallText">Start Live Voice Call</span>
                </button>
                <input type="text" id="userInput" placeholder="Speak or type patient query..." onkeydown="if(event.key==='Enter') sendTurn()">
                <button class="btn-send" onclick="sendTurn()">Send</button>
            </div>

            <div class="quick-chips-wrap">
                <span class="chips-label">Quick Scenarios:</span>
                <div id="indiaChips" style="display:inline-flex; flex-wrap:wrap; gap:8px;">
                    <a href="#" class="chip" onclick="quickFill('My HbA1c is 8.4 and I am really worried about my diabetes.'); return false;">😟 "HbA1c 8.4 &amp; worried"</a>
                    <a href="#" class="chip" onclick="quickFill('Can you prescribe insulin or increase my metformin dose?'); return false;">💊 "Prescribe / change dose?"</a>
                    <a href="#" class="chip chip-friction" onclick="quickFill('I am in a meeting right now, please call after 6 PM'); return false;">⏳ "Busy, call after 6 PM"</a>
                    <a href="#" class="chip" onclick="quickFill('Book a Saturday 11:00 AM consultation at Velachery clinic'); return false;">🏥 "Book Velachery Saturday 11 AM"</a>
                </div>
                <div id="tamilChips" style="display:none; flex-wrap:wrap; gap:8px;">
                    <a href="#" class="chip" onclick="quickFill('வணக்கம், எனக்கு sugar HbA1c அதிகமா இருக்கு, ரொம்ப பயமா இருக்கு.'); return false;">😟 "Sugar HbA1c பயமா இருக்கு"</a>
                    <a href="#" class="chip" onclick="quickFill('Amura Health Velachery clinic fees மற்றும் MNT care plan சொல்லுங்க.'); return false;">🩺 "Velachery Clinic &amp; MNT Fees"</a>
                    <a href="#" class="chip" onclick="quickFill('சனிக்கிழமை காலை 11 மணிக்கு டாக்டர் கன்சல்டேஷன் புக் பண்ணுங்க.'); return false;">🏥 "சனிக்கிழமை 11 AM புக்"</a>
                </div>
                <div id="hindiChips" style="display:none; flex-wrap:wrap; gap:8px;">
                    <a href="#" class="chip" onclick="quickFill('नमस्ते, मेरी शुगर और HbA1c बढ़ी हुई है, मुझे अमूरा हेल्थ में डॉक्टर कंसल्टेशन बुक करना है।'); return false;">🩺 "HbA1c डॉक्टर कंसल्टेशन"</a>
                    <a href="#" class="chip" onclick="quickFill('इस शनिवार सुबह 11 बजे ऑनलाइन कंसल्टेशन बुक कर दीजिए।'); return false;">📅 "शनिवार 11 AM बुक करें"</a>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <div class="card-title"><span id="dossierTitle">Live Clinical Patient Dossier</span></div>
                <span id="dossierStatus" class="tag tag-gold">TRIAGING</span>
            </div>

            <div class="dossier-nav">
                <div class="dossier-tab-wrap">
                    <button class="btn-dossier-tab active" id="tabDossierFormatted" onclick="toggleDossierView('formatted')">Structured Form</button>
                    <button class="btn-dossier-tab" id="tabDossierJson" onclick="toggleDossierView('json')">Pydantic JSON</button>
                </div>
                <button class="btn-copy-json" onclick="copyDossierJson()">Copy JSON</button>
            </div>

            <div class="dossier-grid" id="dossierFormattedView">
                <div class="dossier-row"><span class="dossier-label">Patient / Caller</span><span class="dossier-val" id="dName">Arjun Krishnan (+91-98400-00144)</span></div>
                <div class="dossier-row"><span class="dossier-label">Detected Emotion</span><span id="dEmotion" class="tag tag-blue">calm</span></div>
                <div class="dossier-row"><span class="dossier-label">Safety &amp; 108 Gate</span><span id="dSafety" class="tag tag-green">safe</span></div>
                <div class="dossier-row"><span class="dossier-label">DPDP Consent</span><span id="dConsent" class="tag tag-gold">pending</span></div>
                <div class="dossier-row"><span class="dossier-label">Chief Concern</span><span class="dossier-val" id="dConcern">Pending Intake</span></div>
                <div class="dossier-row"><span class="dossier-label">Triage Urgency</span><span class="dossier-val" id="dUrgency">Routine</span></div>
                <div class="dossier-row"><span class="dossier-label">Care Pathway</span><span class="dossier-val" id="dPathway">Amura MNT + NMT Evaluation</span></div>
                <div class="dossier-row"><span class="dossier-label" id="lblAppt">Consultation Slot</span><span class="dossier-val" id="dAppt" style="color:#60a5fa;">Pending Selection</span></div>
                <div class="dossier-row"><span class="dossier-label">Follow-Up Note</span><span class="dossier-val" id="dFollowUp" style="color:#fcd34d; font-size:12px; max-width:65%;">Amura Health front-desk intake initialized</span></div>
                <div class="dossier-row"><span class="dossier-label">WhatsApp Care Desk</span><span class="dossier-val" id="dWhatsApp" style="color:var(--text-dim); font-size:12px;">+91-62-622-62222</span></div>
            </div>

            <pre class="raw-json-box" id="dossierJsonView">Loading clinical schema...</pre>

            <div class="intent-box">
                <div class="intent-header">
                    <span style="color:var(--text-muted); font-weight:600;">Clinical Intake Readiness Score:</span>
                    <strong id="dIntent" style="color:var(--emerald); font-size:14px;">50 / 100</strong>
                </div>
                <div class="progress-bar-bg"><div id="intentBar" class="progress-bar-fill" style="width: 50%;"></div></div>
            </div>

            <div style="background: rgba(15,23,42,0.7); border: 1px solid rgba(59,130,246,0.3); border-radius: 12px; padding: 12px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-size:12px; font-weight:700; color:#93c5fd;">⚡ APILayer Patient Verification</span>
                    <span id="enrichStatusTag" class="tag tag-blue">READY</span>
                </div>
                <button class="btn-tool-run" style="width:100%;" onclick="enrichCurrentDossier()">⚡ Enrich Patient Dossier via APILayer</button>
                <div id="dossierEnrichmentBox" style="display:none; margin-top:10px; font-size:11.5px; color:#cbd5e1; border-top:1px solid rgba(255,255,255,0.08); padding-top:8px;"></div>
            </div>
        </div>
    </div>

    <div class="apilayer-card">
        <div class="apilayer-header">
            <div style="font-size:15px; font-weight:700;">🌐 APILayer Clinical Intake Intelligence Suite</div>
            <div style="display:flex; gap:8px; align-items:center;">
                <span id="apiLayerKeyBadge" class="tag tag-green">INTELLIGENCE READY</span>
                <input type="password" id="apilayerKeyInput" class="tool-input" style="width:200px;" placeholder="APILayer Key (Optional)...">
                <button class="btn-tool-run" onclick="saveAPILayerKey()">Save Key</button>
            </div>
        </div>

        <div class="apilayer-tools-grid">
            <div class="tool-box">
                <div class="tool-box-title">📞 Numverify: Patient Phone</div>
                <input type="text" id="toolPhoneInput" class="tool-input" value="+91-98400-12345">
                <button class="btn-tool-run" onclick="runNumverify()">Verify Carrier</button>
                <div class="tool-result" id="resNumverify">Validates patient phone carrier &amp; Indian circle.</div>
            </div>
            <div class="tool-box">
                <div class="tool-box-title">✉️ Mailboxlayer: Patient Email</div>
                <input type="text" id="toolEmailInput" class="tool-input" value="care@amura.ai">
                <button class="btn-tool-run" onclick="runMailboxlayer()">Verify Email</button>
                <div class="tool-result" id="resMailboxlayer">Checks MX DNS &amp; clinical deliverability.</div>
            </div>
            <div class="tool-box">
                <div class="tool-box-title">📍 Positionstack: Clinic Geocoding</div>
                <input type="text" id="toolAddressInput" class="tool-input" value="142 Velachery Main Road, Chennai 600042">
                <button class="btn-tool-run" onclick="runPositionstack()">Geocode Clinic</button>
                <div class="tool-result" id="resPositionstack">Resolves Amura Velachery &amp; telehealth care zones.</div>
            </div>
            <div class="tool-box">
                <div class="tool-box-title">💱 Fixer: Care-Plan FX</div>
                <div style="display:flex; gap:6px;">
                    <input type="number" id="toolAmountInput" class="tool-input" value="15000" style="flex:2;">
                    <select id="toolFromCurr" class="tool-input" style="flex:1;"><option value="INR" selected>INR</option><option value="USD">USD</option></select>
                    <select id="toolToCurr" class="tool-input" style="flex:1;"><option value="USD" selected>USD</option><option value="INR">INR</option></select>
                </div>
                <button class="btn-tool-run" onclick="runFixerFX()">Convert Care-Plan FX</button>
                <div class="tool-result" id="resFixer">Healthcare care-plan notation (Lakhs / USD).</div>
            </div>
        </div>
    </div>

    <div class="card" style="margin-bottom:24px;">
        <div class="card-header">
            <div class="card-title"><span>Clinical Triage &amp; Care Pipeline</span><span class="tag tag-blue">EHR / CHATWOOT SYNC</span></div>
            <input type="text" id="leadSearchInput" class="tool-input" style="width:200px;" placeholder="Search patients..." oninput="filterKanbanLeads()">
        </div>
        <div class="kanban">
            <div class="kanban-col">
                <div class="kanban-header"><span>1. Intake Active</span><span>1</span></div>
                <div class="lead-card"><div class="lead-name">Meera Nair</div><div class="lead-prop">PCOD &amp; Thyroid Balance (Online Telehealth)</div><span class="tag tag-gold">Confused • Guided</span></div>
            </div>
            <div class="kanban-col">
                <div class="kanban-header"><span>2. Clinically Triaged</span><span>1</span></div>
                <div class="lead-card"><div class="lead-name">Karthik Subramanian</div><div class="lead-prop">Fatty Liver &amp; Fasting Insulin (Chennai)</div><span class="tag tag-green">88% Ready</span></div>
            </div>
            <div class="kanban-col">
                <div class="kanban-header"><span>3. Consultation Booked</span><span>2</span></div>
                <div class="lead-card"><div class="lead-name">Priya Raman</div><div class="lead-prop">Type-2 Diabetes &amp; HbA1c 8.4% (Velachery)</div><span class="tag tag-green">Saturday 11 AM IST</span></div>
                <div class="lead-card"><div class="lead-name">Arjun Deshmukh</div><div class="lead-prop">Hypertension &amp; Lipid Panel Review</div><span class="tag tag-green">Thursday 2 PM IST</span></div>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-header"><div class="card-title"><span id="roiModuleTitle">Amura Health Clinical Efficiency &amp; Impact</span></div><span class="tag tag-green">24/7 TRI-LINGUAL TRIAGE</span></div>
        <div class="roi-grid">
            <div class="stat-box"><div class="stat-label">Safety Gate Latency</div><div class="stat-val" style="color:#60a5fa;">&lt;15 ms</div></div>
            <div class="stat-box"><div class="stat-label">Consults Scheduled</div><div class="stat-val" id="roiValShowings">+180 / Mo</div></div>
            <div class="stat-box"><div class="stat-label">Front-Desk Hours Saved</div><div class="stat-val" id="roiValHours">320 hrs</div></div>
            <div class="stat-box"><div class="stat-label">Monthly Care Pipeline</div><div class="stat-val" id="roiValRevenue">₹24.5 Lakhs</div></div>
        </div>
    </div>

    <script>
        let currentMarket = 'india';
        let latestDossier = {};
        let lastAudioBase64 = null;

        function updateRateLabel(val) { const el = document.getElementById('lblVoiceRate'); if (el) el.innerText = (val > 0 ? '+' : '') + val + '%'; }
        function updatePitchLabel(val) { const el = document.getElementById('lblVoicePitch'); if (el) el.innerText = (val > 0 ? '+' : '') + val + 'Hz'; }
        function getAudioSettings() {
            const r = document.getElementById('voiceRateSlider')?.value || '0';
            const p = document.getElementById('voicePitchSlider')?.value || '0';
            return { rate: (r >= 0 ? '+' : '') + r + '%', pitch: (p >= 0 ? '+' : '') + p + 'Hz' };
        }
        function escapeHtml(str) { return (str || '').replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

        function switchMarket(market) {
            currentMarket = market;
            const voiceSelect = document.getElementById('voiceSelect');
            const indiaChips = document.getElementById('indiaChips');
            const tamilChips = document.getElementById('tamilChips');
            const hindiChips = document.getElementById('hindiChips');
            const chatBox = document.getElementById('chatBox');

            document.querySelectorAll('.btn-market').forEach(b => b.className = 'btn-market');
            if (market === 'tamil') {
                document.getElementById('btnMarketTamil').className = 'btn-market active';
                if (indiaChips) indiaChips.style.display = 'none';
                if (tamilChips) tamilChips.style.display = 'inline-flex';
                if (hindiChips) hindiChips.style.display = 'none';
                voiceSelect.value = 'ta-IN-PallaviNeural';
                chatBox.innerHTML = `<div class="msg agent"><div class="msg-meta">Pallavi (Amura Health Tamil Care Desk)</div>வணக்கம்... Amura Health-ல இருந்து பல்லவி பேசுறேங்க. உங்க உடல்நல ஆலோசனை மற்றும் டாக்டர் கன்சல்டேஷன் பத்தி பேசலாமா?</div>`;
            } else if (market === 'hindi') {
                document.getElementById('btnMarketHindi').className = 'btn-market active';
                if (indiaChips) indiaChips.style.display = 'none';
                if (tamilChips) tamilChips.style.display = 'none';
                if (hindiChips) hindiChips.style.display = 'inline-flex';
                voiceSelect.value = 'hi-IN-SwaraNeural';
                chatBox.innerHTML = `<div class="msg agent"><div class="msg-meta">स्वाति (Amura Health केयर कोऑर्डिनेटर)</div>नमस्ते जी! Amura Health केयर डेस्क में आपका स्वागत है। मैं स्वाति बात कर रही हूँ। मैं आपकी कैसे सहायता कर सकती हूँ?</div>`;
            } else {
                document.getElementById(market === 'english' ? 'btnMarketUSA' : 'btnMarketIndia').className = 'btn-market active';
                if (indiaChips) indiaChips.style.display = 'inline-flex';
                if (tamilChips) tamilChips.style.display = 'none';
                if (hindiChips) hindiChips.style.display = 'none';
                voiceSelect.value = market === 'english' ? 'en-US-AvaNeural' : 'en-IN-NeerjaExpressiveNeural';
                chatBox.innerHTML = `<div class="msg agent"><div class="msg-meta">Neerja (Amura Health Patient Care)</div>Namaste, this is Neerja from Amura Health Patient Care &amp; Front-Desk Support (Velachery, Chennai). How may I assist you today?</div>`;
            }

            fetch('/api/market_mode', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({mode: market})
            }).then(r => r.json()).then(data => {
                if (data.dossier) { latestDossier = data.dossier; updateDossierUI(data.dossier); }
            }).catch(() => {});
        }

        function quickFill(text) { document.getElementById('userInput').value = text; sendTurn(); }
        function playMarketingHook(market) {
            switchMarket(market);
            const inp = document.getElementById('userInput');
            if (market === 'tamil') inp.value = "வணக்கம், எனக்கு sugar HbA1c அதிகமா இருக்கு, சனிக்கிழமை காலை 11 மணிக்கு Amura Health Velachery clinic அப்பாயின்ட்மென்ட் வேணும்.";
            else if (market === 'hindi') inp.value = "नमस्ते, मुझे अमूरा हेल्थ में डायबिटीज और HbA1c कंसल्टेशन इस शनिवार सुबह 11 बजे बुक करना है।";
            else inp.value = "My HbA1c is 8.4 and I am worried about my diabetes. Can I book a consultation this Saturday at 11 AM?";
            sendTurn();
        }

        function toggleDossierView(view) {
            document.getElementById('dossierFormattedView').style.display = view === 'json' ? 'none' : 'flex';
            document.getElementById('dossierJsonView').style.display = view === 'json' ? 'block' : 'none';
            document.getElementById('tabDossierFormatted').classList.toggle('active', view !== 'json');
            document.getElementById('tabDossierJson').classList.toggle('active', view === 'json');
        }

        function copyDossierJson() { navigator.clipboard?.writeText(JSON.stringify(latestDossier, null, 2)); }
        function filterKanbanLeads() {
            const q = document.getElementById('leadSearchInput').value.toLowerCase();
            document.querySelectorAll('.lead-card').forEach(c => { c.style.display = c.innerText.toLowerCase().includes(q) ? 'block' : 'none'; });
        }

        function speakBrowserTTS(text) {
            if (!window.speechSynthesis || !text) return;
            try {
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance(text);
                u.lang = currentMarket === 'tamil' ? 'ta-IN' : (currentMarket === 'hindi' ? 'hi-IN' : 'en-IN');
                window.speechSynthesis.speak(u);
            } catch (e) {}
        }

        function playAudioBase64(b64, fallbackText) {
            if (!b64 || b64.length < 50) {
                lastAudioBase64 = '';
                speakBrowserTTS(fallbackText || '');
                return;
            }
            lastAudioBase64 = b64;
            try {
                const isWav = b64.startsWith('UklGR');
                const bin = atob(b64);
                const bytes = new Uint8Array(bin.length);
                for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
                const blob = new Blob([bytes], { type: isWav ? 'audio/wav' : 'audio/mpeg' });
                const url = URL.createObjectURL(blob);
                const audio = new Audio(url);
                audio.play().catch(() => speakBrowserTTS(fallbackText || ''));
            } catch (e) { speakBrowserTTS(fallbackText || ''); }
        }

        function sendTurn() {
            const inp = document.getElementById('userInput');
            const text = inp.value.trim();
            if (!text) return;
            const chatBox = document.getElementById('chatBox');
            chatBox.innerHTML += `<div class="msg buyer"><div class="msg-meta">Patient / Caller</div>${escapeHtml(text)}</div>`;
            inp.value = '';
            const voice = document.getElementById('voiceSelect').value;
            const provider = document.getElementById('voiceProviderSelect').value;
            const llmModel = document.getElementById('llmEngineSelect').value;
            const s = getAudioSettings();
            fetch('/api/turn', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ utterance: text, voice, model_id: llmModel, provider, rate: s.rate, pitch: s.pitch })
            }).then(r => r.json()).then(data => {
                const replyText = data.reply || 'How may Amura Health assist you today?';
                chatBox.innerHTML += `<div class="msg agent"><div class="msg-meta">Amura Care • ${escapeHtml(data.detected_emotion || 'calm')} • ${escapeHtml(data.safety_flag || 'safe')}</div>${escapeHtml(replyText)}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
                if (data.dossier) { latestDossier = data.dossier; updateDossierUI(data.dossier); }
                playAudioBase64(data.audio_base64, replyText);
            }).catch(() => {});
        }

        function testVoiceSample() {
            const voice = document.getElementById('voiceSelect').value;
            const provider = document.getElementById('voiceProviderSelect').value;
            const s = getAudioSettings();
            fetch('/api/turn', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ utterance: 'PREVIEW_SAMPLE', voice, provider, rate: s.rate, pitch: s.pitch })
            }).then(r => r.json()).then(d => playAudioBase64(d.audio_base64, d.reply));
        }

        function simulateBargeIn() { if (window.speechSynthesis) window.speechSynthesis.cancel(); }
        function resetCall() { fetch('/api/reset', { method: 'POST' }).then(() => switchMarket(currentMarket)); }
        function switchLLM(modelId) { fetch('/api/llm_select', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({model_id: modelId}) }); }
        function updateVoiceEngineBadge() {}
        function openKeyModal() {}
        function toggleHandsFreeVoiceCall() {}

        function updateDossierUI(d) {
            document.getElementById('dossierJsonView').innerText = JSON.stringify(d, null, 2);
            if (d.patient_name || d.full_name) document.getElementById('dName').innerText = `${d.patient_name || d.full_name} (${d.phone_number || ''})`;
            if (d.detected_emotion) document.getElementById('dEmotion').innerText = d.detected_emotion;
            const sEl = document.getElementById('dSafety');
            if (sEl && d.safety_flag) {
                sEl.innerText = d.emergency_108 ? 'EMERGENCY 108' : d.safety_flag;
                sEl.className = d.emergency_108 ? 'tag tag-red' : 'tag tag-green';
            }
            if (d.consent_status) document.getElementById('dConsent').innerText = d.consent_status;
            if (d.chief_concern) document.getElementById('dConcern').innerText = d.chief_concern;
            if (d.triage_urgency) document.getElementById('dUrgency').innerText = d.triage_urgency;
            if (d.care_pathway) document.getElementById('dPathway').innerText = d.care_pathway;
            if (d.consult_slot || d.appointment_datetime) document.getElementById('dAppt').innerText = d.consult_slot || d.appointment_datetime;
            if (d.follow_up_note) document.getElementById('dFollowUp').innerText = d.follow_up_note;
            if (d.intent_score !== undefined) {
                document.getElementById('dIntent').innerText = `${d.intent_score} / 100`;
                document.getElementById('intentBar').style.width = `${d.intent_score}%`;
            }
        }

        function runNumverify() {
            const phone = document.getElementById('toolPhoneInput').value.trim();
            fetch('/api/enrich/phone', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({phone}) })
                .then(r => r.json()).then(d => { document.getElementById('resNumverify').innerText = `${d.carrier} • ${d.location}`; });
        }
        function runMailboxlayer() {
            const email = document.getElementById('toolEmailInput').value.trim();
            fetch('/api/enrich/email', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({email}) })
                .then(r => r.json()).then(d => { document.getElementById('resMailboxlayer').innerText = `Score: ${Math.round((d.score||0.95)*100)}% • Corporate: ${d.is_corporate}`; });
        }
        function runPositionstack() {
            const address = document.getElementById('toolAddressInput').value.trim();
            fetch('/api/enrich/address', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({address}) })
                .then(r => r.json()).then(d => { document.getElementById('resPositionstack').innerText = `${d.care_zone || d.neighborhood_tier} (${d.postal_code})`; });
        }
        function runFixerFX() {
            const amount = parseFloat(document.getElementById('toolAmountInput').value) || 0;
            const from_curr = document.getElementById('toolFromCurr').value;
            const to_curr = document.getElementById('toolToCurr').value;
            fetch('/api/enrich/currency', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({amount, from_curr, to_curr}) })
                .then(r => r.json()).then(d => { document.getElementById('resFixer').innerText = `${d.formatted_to} (${d.healthcare_notation || ''})`; });
        }
        function enrichCurrentDossier() {
            const box = document.getElementById('dossierEnrichmentBox');
            box.style.display = 'block';
            fetch('/api/enrich/lead', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(latestDossier || {}) })
                .then(r => r.json()).then(d => { box.innerText = `Verified: ${d.phone_intelligence?.carrier} | ${d.spatial_intelligence?.care_zone} | ${d.fx_intelligence?.healthcare_notation || ''}`; });
        }
        function saveAPILayerKey() {
            const api_key = document.getElementById('apilayerKeyInput').value.trim();
            fetch('/api/enrich/key', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({api_key}) });
        }
    </script>
</body>
</html>
"""


class DashboardHTTPHandler(http.server.BaseHTTPRequestHandler):
    """Zero-dependency HTTP Handler serving the Amura Health clinical console and API."""

    conversation_engine = ConversationEngine(
        market_mode="india",
        sector="amura_metabolic",
        business_name=settings.CLINIC_NAME,
    )
    tts_engine = EdgeTTSVoiceEngine()
    apilayer_client = APILayerUnifiedClient()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/landing", "/landing.html", "/index.html", "/website"):
            root = Path(__file__).resolve().parent.parent.parent.parent
            index_path = root / "index.html"
            payload = index_path.read_bytes() if index_path.exists() else HTML_TEMPLATE.encode("utf-8")
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(payload)
        elif parsed.path in ("/console", "/dashboard", "/admin"):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path in ("/presentation", "/deck", "/pitch", "/slides", "/presentation.html"):
            root = Path(__file__).resolve().parent.parent.parent.parent
            deck_path = root / "presentation.html"
            if deck_path.exists():
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(deck_path.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
        elif parsed.path in ("/styles.css", "/main.js", "/assets/logo.webp", "/fonts/GeistPixel-Circle.woff2") or parsed.path.startswith(("/assets/", "/fonts/")):
            root = Path(__file__).resolve().parent.parent.parent.parent
            rel_path = parsed.path.lstrip("/")
            file_path = root / rel_path
            if file_path.exists() and file_path.is_file():
                content_type = "application/octet-stream"
                if rel_path.endswith(".css"):
                    content_type = "text/css; charset=utf-8"
                elif rel_path.endswith(".js"):
                    content_type = "application/javascript; charset=utf-8"
                elif rel_path.endswith(".webp"):
                    content_type = "image/webp"
                elif rel_path.endswith(".png"):
                    content_type = "image/png"
                elif rel_path.endswith(".woff2"):
                    content_type = "font/woff2"
                elif rel_path.endswith(".html"):
                    content_type = "text/html; charset=utf-8"

                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Type", content_type)
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
        elif parsed.path == "/api/leads":
            self._send_json(MOCK_LEADS)
        elif parsed.path == "/api/llm_models":
            try:
                from src.closer.llm.models import list_available_models

                models = list_available_models()
            except Exception:
                models = []
            self._send_json({"models": models})
        elif parsed.path == "/api/llm_active":
            info = (
                self.conversation_engine.llm_router.get_active_model_info()
                if hasattr(self.conversation_engine, "llm_router") and self.conversation_engine.llm_router
                else {"model_id": "llama-3.3-70b"}
            )
            self._send_json(info)
        elif parsed.path == "/api/enrich/status":
            is_live = self.apilayer_client.is_configured()
            self._send_json(
                {
                    "configured": is_live,
                    "provider": "APILayer Unified Suite (Live API Key Connected)" if is_live else "CLOSER AI Clinical Intelligence Engine (Offline Simulation)",
                    "services": ["numverify", "mailboxlayer", "positionstack", "fixer", "currencylayer"],
                }
            )
        elif parsed.path == "/api/learning_stats":
            from src.closer.memory.learning_db import get_learning_db

            db = get_learning_db()
            self._send_json(
                {
                    "stats": db.get_stats(),
                    "recent_calls": db.get_recent_calls(5),
                    "learned_topics": db.get_all_learned_knowledge(),
                }
            )
        else:
            self.send_response(404)
            self.end_headers()

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else ""
        return json.loads(body) if body else {}

    def _send_json(self, payload: Any, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/market_mode":
            data = self._read_json_body()
            mode = str(data.get("mode", "india")).lower()
            self.conversation_engine.set_market_mode(mode)
            greeting = self.conversation_engine.get_initial_greeting()
            dossier = self.conversation_engine.export_dossier()
            self._send_json({"success": True, "mode": mode, "greeting": greeting, "dossier": dossier.model_dump()})

        elif parsed.path == "/api/llm_select":
            data = self._read_json_body()
            model_id = data.get("model_id", "llama-3.3-70b")
            info = self.conversation_engine.set_llm_model(model_id) if hasattr(self.conversation_engine, "set_llm_model") else {}
            self._send_json({"success": True, "model": info})

        elif parsed.path == "/api/reset":
            DashboardHTTPHandler.conversation_engine = ConversationEngine(
                market_mode="india",
                sector="amura_metabolic",
                business_name=settings.CLINIC_NAME,
            )
            greeting = DashboardHTTPHandler.conversation_engine.get_initial_greeting()
            dossier = DashboardHTTPHandler.conversation_engine.export_dossier()
            self._send_json({"success": True, "greeting": greeting, "dossier": dossier.model_dump()})

        elif parsed.path == "/api/turn":
            data = self._read_json_body()
            utterance = data.get("utterance", "")
            voice = data.get("voice", "en-IN-NeerjaExpressiveNeural")
            custom_text = data.get("text", "")
            rate = data.get("rate")
            pitch = data.get("pitch")
            sample_rate = int(data.get("sample_rate", 48000))
            provider = data.get("provider", "studio")
            elevenlabs_key = data.get("elevenlabs_key") or os.environ.get("ELEVENLABS_API_KEY", "")
            sarvam_key = data.get("sarvam_key") or os.environ.get("SARVAM_API_KEY", "")
            consent_granted = data.get("consent_granted")

            if utterance in ("PREVIEW_SAMPLE", "STUDIO_SAMPLE"):
                v_low = str(voice).lower()
                if custom_text:
                    reply = custom_text
                elif "ta-in" in v_low or "pallavi" in v_low or "valluvar" in v_low or "tamil" in v_low:
                    reply = "வணக்கம்! Amura Health Velachery கிளினிக்-ல இருந்து பல்லவி பேசுறேங்க. உங்கள் மெட்டபாலிக் ஆலோசனைக்கு எப்படி உதவலாம்?"
                elif "hi-in" in v_low or "swara" in v_low or "madhur" in v_low or "hindi" in v_low:
                    reply = "नमस्ते जी! Amura Health केयर डेस्क में आपका स्वागत है। मैं आपकी मेटाबोलिक हेल्थ और डॉक्टर कंसल्टेशन में कैसे सहायता कर सकती हूँ?"
                else:
                    reply = "Namaste, this is Amura Health Patient Care & Front-Desk Concierge. How may I assist you with your consultation today?"
            else:
                reply = self.conversation_engine.process_user_turn(utterance, consent_granted=consent_granted)

            emotion_obj = getattr(self.conversation_engine, "last_emotion", None)
            emotion_style = getattr(emotion_obj, "voice_style", "empathetic")
            eff_rate = rate or getattr(emotion_obj, "tts_rate", None)
            eff_pitch = pitch or getattr(emotion_obj, "tts_pitch", None)

            try:
                audio_bytes, latency_tts = self.tts_engine.synthesize_sync(
                    reply,
                    voice=voice,
                    rate=eff_rate,
                    pitch=eff_pitch,
                    sample_rate=sample_rate,
                    provider=provider,
                    elevenlabs_key=elevenlabs_key,
                    sarvam_key=sarvam_key,
                    style=emotion_style,
                )
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else ""
                voice_provider_label = getattr(self.tts_engine, "last_provider_used", "browser_fallback")
            except Exception:
                audio_b64 = ""
                voice_provider_label = "browser_fallback"
                latency_tts = 0.01

            dossier = self.conversation_engine.export_dossier()
            dossier_dict = dossier.model_dump()

            learning_res: Dict[str, Any] = {}
            if hasattr(self.conversation_engine, "save_and_learn_from_call"):
                try:
                    learning_res = self.conversation_engine.save_and_learn_from_call()
                except Exception as e:
                    learning_res = {"status": "error", "error": str(e)}

            llm_info = (
                self.conversation_engine.llm_router.get_active_model_info()
                if hasattr(self.conversation_engine, "llm_router") and self.conversation_engine.llm_router
                else {"model_id": "llama-3.3-70b", "parameter_scale": "70 Billion", "target_latency_ms": 88, "last_tier_used": "reflex_edge"}
            )
            self._send_json(
                {
                    "reply": reply,
                    "detected_emotion": dossier_dict.get("detected_emotion", "calm"),
                    "emotion_confidence": dossier_dict.get("emotion_confidence", 0.85),
                    "empathy_tone": dossier_dict.get("empathy_tone", "empathetic"),
                    "safety_flag": dossier_dict.get("safety_flag", "safe"),
                    "emergency_108": dossier_dict.get("emergency_108", False),
                    "consent_status": dossier_dict.get("consent_status", "pending"),
                    "audio_base64": audio_b64,
                    "audio_mime": ("audio/wav" if audio_b64.startswith("UklGR") else "audio/mpeg") if audio_b64 else "none",
                    "sample_rate": sample_rate,
                    "voice_provider": voice_provider_label,
                    "tts_provider": voice_provider_label,
                    "tts_fallback_used": voice_provider_label == "browser_fallback",
                    "voice_latency_ms": round(latency_tts * 1000, 1),
                    "dossier": dossier_dict,
                    "learning": learning_res,
                    "llm_model": llm_info.get("model_id"),
                    "llm_parameters": llm_info.get("parameter_scale"),
                    "llm_latency_ms": llm_info.get("target_latency_ms") or 88,
                    "llm_tier": llm_info.get("last_tier_used") or "reflex_edge",
                }
            )

        elif parsed.path == "/api/enrich/phone":
            data = self._read_json_body()
            self._send_json(self.apilayer_client.verify_phone(data.get("phone", "")))
        elif parsed.path == "/api/enrich/email":
            data = self._read_json_body()
            self._send_json(self.apilayer_client.verify_email(data.get("email", "")))
        elif parsed.path == "/api/enrich/address":
            data = self._read_json_body()
            self._send_json(self.apilayer_client.geocode_clinic_address(data.get("address", "")))
        elif parsed.path == "/api/enrich/currency":
            data = self._read_json_body()
            self._send_json(
                self.apilayer_client.convert_currency(
                    float(data.get("amount", 0)),
                    from_curr=data.get("from_curr", "INR"),
                    to_curr=data.get("to_curr", "USD"),
                )
            )
        elif parsed.path == "/api/enrich/lead":
            data = self._read_json_body()
            dossier_data = data if data else self.conversation_engine.export_dossier().model_dump()
            self._send_json(self.apilayer_client.enrich_patient_dossier(dossier_data))
        elif parsed.path == "/api/enrich/key":
            data = self._read_json_body()
            api_key = data.get("api_key", "").strip()
            DashboardHTTPHandler.apilayer_client = APILayerUnifiedClient(api_key=api_key)
            is_live = DashboardHTTPHandler.apilayer_client.is_configured()
            self._send_json(
                {
                    "success": True,
                    "configured": is_live,
                    "provider": "APILayer Unified Suite (Live API Key Connected)" if is_live else "CLOSER AI Clinical Intelligence Engine (Offline Simulation)",
                }
            )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def run_web_console(port: int = 8501) -> None:
    server_address = ("0.0.0.0", port)
    with ReusableTCPServer(server_address, DashboardHTTPHandler) as httpd:
        print(f"\n[+] CLOSER AI — Amura Health Clinical Console running at http://localhost:{port}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down web console.")


if __name__ == "__main__":
    if "streamlit" in sys.modules:
        try:
            import streamlit as st

            st.set_page_config(page_title="CLOSER AI — Amura Health Console", layout="wide")
            st.title("CLOSER AI: Amura Health Clinical Voice Triage Console")
            st.caption(f"Clinic: {settings.CLINIC_NAME} | {settings.CLINIC_ADDRESS}")
            st.markdown(HTML_TEMPLATE, unsafe_allow_html=True)
        except Exception:
            run_web_console()
    else:
        run_web_console()
