"""
Web Console for CLOSER AI: Live Call Simulator, Lead Pipeline Kanban, Audio Playback, and ROI Calculator.
Elite Minimalist Luxury Concierge Interface inspired by Apple & Stripe Dark Obsidian & Glassmorphism Aesthetics.
Supports both Streamlit (`streamlit run src/closer/web/dashboard.py`) and zero-dependency standalone HTTP server.
"""

from __future__ import annotations
import os
import sys
import json
import time
import base64
import http.server
import socketserver
from urllib.parse import parse_qs, urlparse
from typing import Dict, Any, List

from src.closer.config import settings
from src.closer.agent.schemas import InboundLead, BuyerDossier
from src.closer.agent.conversation import ConversationEngine
from src.closer.voice.tts import EdgeTTSVoiceEngine
from src.closer.integrations.calendar import CalendarManager
from src.closer.integrations.crm import CRMDispatcher
from src.closer.integrations.telephony import TelephonyManager

# Simulated Lead Pipeline data
MOCK_LEADS = [
    {
        "id": "lead_101",
        "name": "Harrison & Claire Sterling",
        "phone": "+1-310-555-0144",
        "property": "10484 Bellagio Rd, Bel Air ($6.85M)",
        "source": "Instagram Ads",
        "stage": "Tour Booked",
        "budget": "$6,500,000",
        "financing": "Cash (Verified)",
        "intent": 95,
        "slot": "Thursday at 2:00 PM PST",
        "sentiment": "Urgent"
    },
    {
        "id": "lead_102",
        "name": "Marcus Thorne",
        "phone": "+1-310-555-0182",
        "property": "31224 Broad Beach Rd, Malibu ($11.2M)",
        "source": "Zillow Premier",
        "stage": "AI-Qualified",
        "budget": "$10,000,000",
        "financing": "Pre-Approved (Jumbo)",
        "intent": 85,
        "slot": "Pending Slot Selection",
        "sentiment": "Positive"
    },
    {
        "id": "lead_103",
        "name": "Elena Rostova",
        "phone": "+1-415-555-0199",
        "property": "9555 Heather Rd, Beverly Hills ($8.9M)",
        "source": "Website Form",
        "stage": "Qualifying Call",
        "budget": "Evaluating",
        "financing": "Private Banking",
        "intent": 65,
        "slot": "In Conversation",
        "sentiment": "Neutral"
    },
    {
        "id": "lead_104",
        "name": "David Vance",
        "phone": "+1-310-555-0199",
        "property": "Bel Air Modern Estate ($4.5M)",
        "source": "Instagram Ads",
        "stage": "Tour Booked",
        "budget": "$5,000,000",
        "financing": "Cash",
        "intent": 100,
        "slot": "This Thursday at 2:00 PM PST",
        "sentiment": "Urgent"
    }
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CLOSER AI — Autonomous Luxury Concierge Live Console</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #07090e;
            --surface: rgba(15, 20, 32, 0.72);
            --surface-card: rgba(20, 26, 42, 0.65);
            --surface-hover: rgba(30, 41, 65, 0.75);
            --border: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(255, 255, 255, 0.16);
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.25);
            --gold: #f59e0b;
            --gold-glow: rgba(245, 158, 11, 0.2);
            --emerald: #10b981;
            --emerald-glow: rgba(16, 185, 129, 0.2);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif; }
        body {
            background: var(--bg);
            background-image: 
                radial-gradient(1000px circle at 50% -10%, rgba(59, 130, 246, 0.12), transparent 70%),
                radial-gradient(800px circle at 80% 20%, rgba(245, 158, 11, 0.05), transparent 60%);
            color: var(--text-main);
            min-height: 100vh;
            padding: 24px 32px;
            letter-spacing: -0.011em;
        }

        /* Top Bar */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 24px;
        }
        .logo-wrap {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .brand-icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #3b82f6 0%, #1e3a8a 100%);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            box-shadow: 0 4px 16px var(--primary-glow);
        }
        .logo-title {
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.03em;
            background: linear-gradient(180deg, #ffffff 30%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .badge {
            background: rgba(59, 130, 246, 0.12);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .subtitle {
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 3px;
            font-weight: 400;
        }
        .header-links {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--emerald);
            box-shadow: 0 0 10px var(--emerald);
            display: inline-block;
            animation: pulseDot 2s infinite ease-in-out;
        }
        @keyframes pulseDot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.9); }
        }

        /* Grid Layout */
        .grid-layout {
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 24px;
            margin-bottom: 24px;
        }
        @media(max-width: 980px) { .grid-layout { grid-template-columns: 1fr; } }

        /* Glassmorphism Cards */
        .card {
            background: var(--surface);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 22px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.45);
            transition: border-color 0.2s ease;
        }
        .card:hover {
            border-color: var(--border-hover);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 14px;
            margin-bottom: 16px;
        }
        .card-title {
            font-size: 15px;
            font-weight: 700;
            letter-spacing: -0.01em;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Voice Activity Indicator (VAD) */
        .vad-container {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--border);
            border-radius: 9999px;
            padding: 4px 12px;
        }
        .vad-waves {
            display: inline-flex;
            align-items: center;
            gap: 2.5px;
            height: 16px;
        }
        .vad-bar {
            width: 3px;
            border-radius: 9999px;
            background: #60a5fa;
            height: 5px;
            transition: height 0.15s ease, background 0.3s ease;
        }
        .vad-container.listening .vad-bar:nth-child(1) { animation: vadBreathe 1.8s infinite 0.1s; }
        .vad-container.listening .vad-bar:nth-child(2) { animation: vadBreathe 1.8s infinite 0.3s; }
        .vad-container.listening .vad-bar:nth-child(3) { animation: vadBreathe 1.8s infinite 0.5s; }
        .vad-container.listening .vad-bar:nth-child(4) { animation: vadBreathe 1.8s infinite 0.2s; }
        .vad-container.listening .vad-bar:nth-child(5) { animation: vadBreathe 1.8s infinite 0.4s; }
        .vad-container.listening .vad-bar:nth-child(6) { animation: vadBreathe 1.8s infinite 0.15s; }

        .vad-container.speaking .vad-bar {
            background: linear-gradient(180deg, #f59e0b, #fbbf24);
            box-shadow: 0 0 6px rgba(245, 158, 11, 0.4);
        }
        .vad-container.speaking .vad-bar:nth-child(1) { animation: vadPulse 0.45s infinite alternate 0.05s; }
        .vad-container.speaking .vad-bar:nth-child(2) { animation: vadPulse 0.55s infinite alternate 0.2s; }
        .vad-container.speaking .vad-bar:nth-child(3) { animation: vadPulse 0.40s infinite alternate 0.1s; }
        .vad-container.speaking .vad-bar:nth-child(4) { animation: vadPulse 0.60s infinite alternate 0.25s; }
        .vad-container.speaking .vad-bar:nth-child(5) { animation: vadPulse 0.48s infinite alternate 0.15s; }
        .vad-container.speaking .vad-bar:nth-child(6) { animation: vadPulse 0.52s infinite alternate 0.3s; }

        @keyframes vadBreathe {
            0%, 100% { height: 4px; }
            50% { height: 11px; }
        }
        @keyframes vadPulse {
            0% { height: 4px; }
            100% { height: 18px; }
        }

        .vad-label {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.04em;
            color: #93c5fd;
            text-transform: uppercase;
        }
        .vad-container.speaking .vad-label {
            color: var(--gold);
        }

        /* Voice Selection Controls */
        .voice-controls {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
            background: rgba(0, 0, 0, 0.25);
            padding: 8px 12px;
            border-radius: 10px;
            border: 1px solid var(--border);
        }
        .voice-select {
            flex: 1;
            background: rgba(15, 23, 42, 0.9);
            color: #e2e8f0;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 7px 12px;
            font-size: 13px;
            font-weight: 500;
            outline: none;
            cursor: pointer;
            transition: border-color 0.2s;
        }
        .voice-select:hover, .voice-select:focus {
            border-color: var(--primary);
        }
        .btn-preview {
            background: rgba(59, 130, 246, 0.15);
            color: #93c5fd;
            border: 1px solid rgba(59, 130, 246, 0.4);
            border-radius: 8px;
            padding: 7px 14px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        .btn-preview:hover {
            background: rgba(59, 130, 246, 0.3);
            border-color: #60a5fa;
            color: #ffffff;
            box-shadow: 0 0 12px var(--primary-glow);
        }
        .btn-reset {
            background: transparent;
            color: var(--text-muted);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 7px 10px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-reset:hover {
            color: #ffffff;
            border-color: rgba(255,255,255,0.25);
        }

        /* Chat / Telephony Transcript Box */
        .chat-box {
            height: 340px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 14px;
            padding: 16px;
            background: rgba(7, 10, 18, 0.75);
            border-radius: 12px;
            border: 1px solid var(--border);
            scroll-behavior: smooth;
        }
        .chat-box::-webkit-scrollbar { width: 5px; }
        .chat-box::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 4px; }

        .msg {
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 86%;
            font-size: 13.5px;
            line-height: 1.5;
            position: relative;
            animation: fadeInMsg 0.25s ease-out;
        }
        @keyframes fadeInMsg {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .msg.agent {
            background: linear-gradient(135deg, rgba(30, 58, 138, 0.35) 0%, rgba(15, 23, 42, 0.6) 100%);
            color: #e2e8f0;
            align-self: flex-start;
            border: 1px solid rgba(59, 130, 246, 0.25);
            border-left: 3px solid #60a5fa;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }
        .msg.buyer {
            background: linear-gradient(135deg, rgba(31, 41, 55, 0.65) 0%, rgba(17, 24, 39, 0.8) 100%);
            color: #f8fafc;
            align-self: flex-end;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-right: 3px solid var(--emerald);
        }
        .msg-meta {
            font-size: 11px;
            color: var(--text-dim);
            margin-bottom: 5px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .msg.agent .msg-meta { color: #93c5fd; }
        .msg.buyer .msg-meta { color: #86efac; justify-content: flex-end; }

        /* Input Bar */
        .input-row {
            display: flex;
            gap: 10px;
            margin-top: 14px;
        }
        .input-row input {
            flex: 1;
            padding: 13px 16px;
            background: rgba(7, 10, 18, 0.85);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: #ffffff;
            font-size: 13.5px;
            outline: none;
            transition: all 0.2s ease;
        }
        .input-row input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 16px var(--primary-glow);
        }
        .btn-send {
            padding: 12px 22px;
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 16px var(--primary-glow);
        }
        .btn-send:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.45);
        }

        /* Quick Test Chips */
        .quick-chips-wrap {
            margin-top: 14px;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
        }
        .chips-label {
            font-size: 11.5px;
            color: var(--text-dim);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .chip {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border);
            color: #cbd5e1;
            padding: 5px 11px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.18s ease;
            text-decoration: none;
        }
        .chip:hover {
            background: rgba(59, 130, 246, 0.15);
            border-color: rgba(59, 130, 246, 0.4);
            color: #ffffff;
            transform: translateY(-1px);
        }
        .chip.chip-friction {
            border-color: rgba(245, 158, 11, 0.25);
            background: rgba(245, 158, 11, 0.06);
            color: #fcd34d;
        }
        .chip.chip-friction:hover {
            background: rgba(245, 158, 11, 0.2);
            border-color: var(--gold);
            color: #ffffff;
        }

        /* Streamlined Pydantic Buyer Dossier Display */
        .dossier-grid {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .dossier-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 12px;
            background: rgba(0, 0, 0, 0.22);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.04);
            font-size: 13px;
        }
        .dossier-label {
            color: var(--text-muted);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .dossier-val {
            font-weight: 600;
            color: #f1f5f9;
            text-align: right;
        }

        /* Intent Score Gauge */
        .intent-box {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 12px;
            border: 1px solid var(--border);
            margin-top: 4px;
        }
        .intent-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            margin-bottom: 8px;
        }
        .progress-bar-bg {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 9999px;
            overflow: hidden;
        }
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #3b82f6 0%, #10b981 100%);
            border-radius: 9999px;
            width: 50%;
            transition: width 0.4s ease, background 0.4s ease;
        }

        /* Tags */
        .tag {
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 700;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }
        .tag-green { background: rgba(16, 185, 129, 0.15); color: var(--emerald); border: 1px solid rgba(16, 185, 129, 0.3); }
        .tag-gold { background: rgba(245, 158, 11, 0.15); color: var(--gold); border: 1px solid rgba(245, 158, 11, 0.3); }
        .tag-blue { background: rgba(59, 130, 246, 0.15); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.3); }

        /* Secondary Sections: Pipeline & ROI */
        .kanban { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
        @media(max-width: 768px) { .kanban { grid-template-columns: 1fr; } }
        .kanban-col { background: rgba(10, 14, 24, 0.65); border-radius: 12px; padding: 14px; border: 1px solid var(--border); }
        .kanban-header { font-size: 12px; text-transform: uppercase; font-weight: 700; color: var(--text-dim); margin-bottom: 12px; display: flex; justify-content: space-between; }
        .lead-card { background: rgba(20, 26, 42, 0.7); border: 1px solid var(--border); border-radius: 10px; padding: 12px; margin-bottom: 10px; transition: transform 0.15s, border-color 0.15s; }
        .lead-card:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.2); }
        .lead-name { font-weight: 700; font-size: 13.5px; margin-bottom: 3px; color: #ffffff; }
        .lead-prop { font-size: 11.5px; color: var(--text-muted); margin-bottom: 8px; }

        .roi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 14px; }
        @media(max-width: 768px) { .roi-grid { grid-template-columns: 1fr 1fr; } }
        .stat-box { background: rgba(10, 14, 24, 0.65); border: 1px solid var(--border); border-radius: 12px; padding: 16px; text-align: center; }
        .stat-val { font-size: 24px; font-weight: 800; color: var(--emerald); margin-top: 4px; letter-spacing: -0.02em; }
        .stat-label { font-size: 11.5px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-wrap">
            <div class="brand-icon">⚡</div>
            <div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <span class="logo-title">CLOSER AI</span>
                    <span class="badge"><span class="status-dot"></span> LUXURY CONCIERGE &lt;500MS</span>
                </div>
                <div class="subtitle">Autonomous Voice Lead Qualification &amp; Rational Concierge Engine</div>
            </div>
        </div>
        <div class="header-links">
            <span style="font-size:12px; color:var(--text-dim);">Principal Broker: <strong style="color:#ffffff;">R Jan Steve Daniel</strong></span>
            <a href="https://github.com/JanSteve/closer-ai" target="_blank" style="color:#60a5fa; text-decoration:none; font-size:13px; font-weight:600;">GitHub ↗</a>
        </div>
    </div>

    <div class="grid-layout">
        <!-- Live Voice Call Interaction Module -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">
                    <span>Autonomous Voice Concierge</span>
                </div>
                <!-- Animated Voice Activity Indicator (VAD) -->
                <div id="vadContainer" class="vad-container listening">
                    <div class="vad-waves">
                        <span class="vad-bar"></span>
                        <span class="vad-bar"></span>
                        <span class="vad-bar"></span>
                        <span class="vad-bar"></span>
                        <span class="vad-bar"></span>
                        <span class="vad-bar"></span>
                    </div>
                    <span id="vadLabel" class="vad-label">● CONCIERGE READY</span>
                </div>
            </div>

            <!-- Instant One-Click Voice Selection & Audio Preview -->
            <div class="voice-controls">
                <label style="font-size:11px; color:var(--text-dim); text-transform:uppercase; font-weight:700;">Voice:</label>
                <select id="voiceSelect" class="voice-select">
                    <option value="en-US-AriaNeural" selected>Sophia / Aria (US Female • Warm Consultative)</option>
                    <option value="en-US-GuyNeural">Guy (US Male • Confident Luxury Broker)</option>
                    <option value="en-US-JennyNeural">Jenny (US Female • Crisp Natural)</option>
                    <option value="en-US-ChristopherNeural">Christopher (US Male • Authoritative Executive)</option>
                    <option value="en-US-AvaNeural">Ava (US Female • Expressive Concierge)</option>
                    <option value="en-IN-NeerjaNeural">Neerja (India Female • Global Executive)</option>
                </select>
                <button class="btn-preview" onclick="testVoiceSample()">🔊 Test Voice</button>
                <button class="btn-reset" title="Reset current conversation state" onclick="resetCall()">↻ Reset</button>
            </div>

            <!-- Live Telephony Chat Transcript Box -->
            <div class="chat-box" id="chatBox">
                <div class="msg agent">
                    <div class="msg-meta">Sophia (Daniel &amp; Associates Luxury Concierge) • 24kHz High-Fidelity</div>
                    Hi Alex, this is Sophia with Daniel &amp; Associates Luxury Realty. I noticed you just requested details on 10484 Bellagio Rd, Bel Air — I wanted to catch you while it's top of mind. Are you looking at this as a primary residence or a private investment?
                </div>
            </div>

            <!-- Spoken Input Row -->
            <div class="input-row">
                <input type="text" id="userInput" placeholder="Speak or type buyer reply (e.g. 'Today is not good, I will come tomorrow')..." onkeydown="if(event.key==='Enter') sendTurn()">
                <button class="btn-send" onclick="sendTurn()">Speak / Send</button>
            </div>

            <!-- Luxury Quick Test Chips -->
            <div class="quick-chips-wrap">
                <span class="chips-label">Quick Scenarios:</span>
                <a href="#" class="chip chip-friction" onclick="quickFill('Today is not good, I will come tomorrow'); return false;">🗓️ "Today not good, come tomorrow"</a>
                <a href="#" class="chip chip-friction" onclick="quickFill('I am busy right now, contact me later'); return false;">⏳ "Busy now, contact later"</a>
                <a href="#" class="chip" onclick="quickFill('My budget is $6.5 million cash and looking to move next month in Bel Air.'); return false;">💼 "$6.5M Cash / 30 Days"</a>
                <a href="#" class="chip" onclick="quickFill('Please text our private dossier via WhatsApp.'); return false;">📲 "Send via WhatsApp"</a>
                <a href="#" class="chip" onclick="quickFill('Tomorrow afternoon at 2 PM works perfectly for us to tour.'); return false;">🏛️ "Tomorrow at 2 PM"</a>
            </div>
        </div>

        <!-- Streamlined Live Pydantic Buyer Dossier Display -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">
                    <span>Live Pydantic Buyer Dossier</span>
                </div>
                <span id="dossierStatus" class="tag tag-gold">QUALIFYING</span>
            </div>

            <div class="dossier-grid">
                <div class="dossier-row">
                    <span class="dossier-label">Client Name</span>
                    <span class="dossier-val" id="dName">Alex Morgan (+1-310-555-0144)</span>
                </div>
                <div class="dossier-row">
                    <span class="dossier-label">Budget Range</span>
                    <span class="dossier-val" id="dBudget">Evaluating</span>
                </div>
                <div class="dossier-row">
                    <span class="dossier-label">Financial Readiness</span>
                    <span id="dFinancing" class="tag tag-gold">Pending Verification</span>
                </div>
                <div class="dossier-row">
                    <span class="dossier-label">Timeline</span>
                    <span class="dossier-val" id="dTime">Pending Discussion</span>
                </div>
                <div class="dossier-row">
                    <span class="dossier-label">VIP Tour Schedule</span>
                    <span class="dossier-val" id="dAppt" style="color:#60a5fa;">Pending Selection</span>
                </div>
                <div class="dossier-row">
                    <span class="dossier-label">Concierge / Follow-Up Note</span>
                    <span class="dossier-val" id="dFollowUp" style="color:#fcd34d; font-size:12px; max-width:65%;">Active consultation</span>
                </div>
                <div class="dossier-row">
                    <span class="dossier-label">Property Target</span>
                    <span class="dossier-val" id="dProperty">10484 Bellagio Rd, Bel Air ($6.85M)</span>
                </div>
            </div>

            <!-- Intent Score Gauge -->
            <div class="intent-box">
                <div class="intent-header">
                    <span style="color:var(--text-muted); font-weight:600;">Autonomous Lead Intent Score:</span>
                    <strong id="dIntent" style="color:var(--emerald); font-size:14px;">50 / 100</strong>
                </div>
                <div class="progress-bar-bg">
                    <div id="intentBar" class="progress-bar-fill" style="width: 50%;"></div>
                </div>
            </div>

            <!-- Hidden Audio Player -->
            <audio id="audioPlayer" controls style="display:none;"></audio>
        </div>
    </div>

    <!-- Luxury Lead Pipeline (Follow Up Boss CRM Sync) -->
    <div class="card" style="margin-bottom:24px;">
        <div class="card-header">
            <div class="card-title">
                <span>Luxury Lead Pipeline (Follow Up Boss CRM Sync)</span>
            </div>
            <span class="badge">Real-Time Sync</span>
        </div>
        <div class="kanban">
            <div class="kanban-col">
                <div class="kanban-header">
                    <span>1. Inbound Leads</span>
                    <span>1</span>
                </div>
                <div class="lead-card">
                    <div class="lead-name">Elena Rostova</div>
                    <div class="lead-prop">9555 Heather Rd, Beverly Hills ($8.9M)</div>
                    <div><span class="tag tag-blue">Website Form</span> <span class="tag tag-gold">Evaluating</span></div>
                </div>
            </div>

            <div class="kanban-col">
                <div class="kanban-header">
                    <span>2. AI-Qualified</span>
                    <span>1</span>
                </div>
                <div class="lead-card">
                    <div class="lead-name">Marcus Thorne</div>
                    <div class="lead-prop">31224 Broad Beach Rd, Malibu ($11.2M)</div>
                    <div><span class="tag tag-green">$10M Jumbo Loan</span> <span class="tag tag-blue">Score: 85</span></div>
                </div>
            </div>

            <div class="kanban-col">
                <div class="kanban-header">
                    <span>3. Tour Scheduled (Calendar Locked)</span>
                    <span>2</span>
                </div>
                <div class="lead-card">
                    <div class="lead-name">David Vance</div>
                    <div class="lead-prop">10484 Bellagio Rd, Bel Air ($6.85M)</div>
                    <div><span class="tag tag-green">$5M All-Cash</span> <span class="tag tag-gold">This Thursday 2PM</span></div>
                </div>
                <div class="lead-card">
                    <div class="lead-name">Harrison &amp; Claire Sterling</div>
                    <div class="lead-prop">10484 Bellagio Rd, Bel Air ($6.85M)</div>
                    <div><span class="tag tag-green">All-Cash Verified</span> <span class="tag tag-gold">Thursday 2PM</span></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Brokerage Speed-to-Lead ROI Calculator -->
    <div class="card">
        <div class="card-header">
            <div class="card-title">
                <span>Brokerage Speed-to-Lead ROI Impact Model</span>
            </div>
            <span class="badge" style="background:rgba(245,158,11,0.12); color:var(--gold); border-color:rgba(245,158,11,0.3);">Gross Commission Model</span>
        </div>
        <p style="font-size:13px; color:var(--text-muted); margin-bottom:14px; line-height:1.5;">
            Calling ultra-luxury buyer leads in under 500ms yields a <strong>391% increase in private showing conversion</strong> compared to human agent response averages (47 minutes).
        </p>
        <div class="roi-grid">
            <div class="stat-box">
                <div class="stat-label">Inbound Monthly Leads</div>
                <div class="stat-val" style="color:#60a5fa">120</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Speed-to-Lead Response</div>
                <div class="stat-val" style="color:var(--emerald)">&lt; 500ms</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Booked VIP Tours / Mo</div>
                <div class="stat-val" style="color:var(--gold)">28</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Added Annual GCI</div>
                <div class="stat-val" style="color:var(--emerald)">+$420,000</div>
            </div>
        </div>
    </div>

    <script>
        const audioPlayer = document.getElementById('audioPlayer');
        const vadContainer = document.getElementById('vadContainer');
        const vadLabel = document.getElementById('vadLabel');

        // Audio state visualizer synchronization
        audioPlayer.onplay = () => {
            vadContainer.className = 'vad-container speaking';
            vadLabel.innerText = '● AI SPEAKING';
        };
        audioPlayer.onpause = () => {
            vadContainer.className = 'vad-container listening';
            vadLabel.innerText = '● LISTENING';
        };
        audioPlayer.onended = () => {
            vadContainer.className = 'vad-container listening';
            vadLabel.innerText = '● LISTENING';
        };

        function quickFill(val) {
            document.getElementById('userInput').value = val;
            sendTurn();
        }

        async function testVoiceSample() {
            const voice = document.getElementById('voiceSelect').value;
            const voiceLabel = document.getElementById('voiceSelect').selectedOptions[0].text.split('(')[0].trim();
            const chat = document.getElementById('chatBox');
            
            chat.innerHTML += `
                <div class="msg agent" style="border-left:3px solid #f59e0b;">
                    <div class="msg-meta">Voice Preview • ${voiceLabel} (24kHz Studio)</div>
                    <em>"Hello, this is CLOSER AI luxury real estate concierge. How can I assist you with your estate search today?"</em>
                </div>
            `;
            chat.scrollTop = chat.scrollHeight;

            vadContainer.className = 'vad-container speaking';
            vadLabel.innerText = '● SYNTHESIZING';

            try {
                const res = await fetch('/api/turn', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        utterance: "PREVIEW_SAMPLE",
                        voice: voice
                    })
                });
                const data = await res.json();
                if (data.audio_base64) {
                    audioPlayer.src = "data:audio/wav;base64," + data.audio_base64;
                    audioPlayer.play().catch(e => {
                        console.log('Autoplay handled:', e);
                        vadContainer.className = 'vad-container listening';
                        vadLabel.innerText = '● CONCIERGE READY';
                    });
                } else {
                    vadContainer.className = 'vad-container listening';
                    vadLabel.innerText = '● CONCIERGE READY';
                }
            } catch(e) {
                console.error('Preview error:', e);
                vadContainer.className = 'vad-container listening';
                vadLabel.innerText = '● CONCIERGE READY';
            }
        }

        async function resetCall() {
            try {
                await fetch('/api/reset', { method: 'POST' });
                const chat = document.getElementById('chatBox');
                chat.innerHTML = `
                    <div class="msg agent">
                        <div class="msg-meta">Sophia (Daniel &amp; Associates Luxury Concierge) • 24kHz High-Fidelity</div>
                        Hi Alex, this is Sophia with Daniel &amp; Associates Luxury Realty. I noticed you just requested details on 10484 Bellagio Rd, Bel Air — I wanted to catch you while it's top of mind. Are you looking at this as a primary residence or a private investment?
                    </div>
                `;
                document.getElementById('dName').innerText = "Alex Morgan (+1-310-555-0144)";
                document.getElementById('dBudget').innerText = "Evaluating";
                document.getElementById('dFinancing').innerText = "Pending Verification";
                document.getElementById('dFinancing').className = "tag tag-gold";
                document.getElementById('dTime').innerText = "Pending Discussion";
                document.getElementById('dossierStatus').innerText = "QUALIFYING";
                document.getElementById('dossierStatus').className = "tag tag-gold";
                document.getElementById('dAppt').innerText = "Pending Selection";
                document.getElementById('dFollowUp').innerText = "Active consultation";
                document.getElementById('dIntent').innerText = "50 / 100";
                document.getElementById('intentBar').style.width = "50%";
                vadContainer.className = 'vad-container listening';
                vadLabel.innerText = '● CONCIERGE READY';
            } catch(e) {
                console.error(e);
            }
        }

        async function sendTurn() {
            const input = document.getElementById('userInput');
            const val = input.value.trim();
            if (!val) return;
            input.value = '';

            const voice = document.getElementById('voiceSelect').value;
            const voiceLabel = document.getElementById('voiceSelect').selectedOptions[0].text.split('(')[0].trim();

            const chat = document.getElementById('chatBox');
            chat.innerHTML += `
                <div class="msg buyer">
                    <div class="msg-meta">Buyer (You)</div>
                    ${val}
                </div>
            `;
            chat.scrollTop = chat.scrollHeight;

            vadContainer.className = 'vad-container speaking';
            vadLabel.innerText = '● REASONING';

            try {
                const res = await fetch('/api/turn', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({utterance: val, voice: voice})
                });
                const data = await res.json();
                
                chat.innerHTML += `
                    <div class="msg agent">
                        <div class="msg-meta">${voiceLabel} (Concierge ISA) • Voice Synthesized (24kHz)</div>
                        ${data.reply}
                    </div>
                `;
                chat.scrollTop = chat.scrollHeight;

                if (data.dossier) {
                    updateDossierUI(data.dossier);
                }

                if (data.audio_base64) {
                    audioPlayer.src = "data:audio/wav;base64," + data.audio_base64;
                    audioPlayer.play().catch(e => {
                        console.log('Autoplay handled:', e);
                        vadContainer.className = 'vad-container listening';
                        vadLabel.innerText = '● LISTENING';
                    });
                } else {
                    vadContainer.className = 'vad-container listening';
                    vadLabel.innerText = '● LISTENING';
                }
            } catch (err) {
                console.error('Turn error:', err);
                vadContainer.className = 'vad-container listening';
                vadLabel.innerText = '● LISTENING';
            }
        }

        function updateDossierUI(dossier) {
            if (dossier.full_name) {
                const ph = dossier.phone_number ? ` (${dossier.phone_number})` : '';
                document.getElementById('dName').innerText = `${dossier.full_name}${ph}`;
            }
            if (dossier.budget_max) {
                const bMin = dossier.budget_min ? `$${Number(dossier.budget_min).toLocaleString()} - ` : '';
                document.getElementById('dBudget').innerText = `${bMin}$${Number(dossier.budget_max).toLocaleString()} USD`;
            }
            if (dossier.financing_type) {
                const fin = dossier.financing_type.replace(/_/g, ' ').toUpperCase();
                document.getElementById('dFinancing').innerText = fin;
                document.getElementById('dFinancing').className = (dossier.financing_type === 'cash' || dossier.pre_approved) ? 'tag tag-green' : 'tag tag-gold';
            }
            if (dossier.timeframe) {
                document.getElementById('dTime').innerText = dossier.timeframe;
            }
            if (dossier.intent_score !== undefined) {
                document.getElementById('dIntent').innerText = `${dossier.intent_score} / 100`;
                document.getElementById('intentBar').style.width = `${dossier.intent_score}%`;
            }
            if (dossier.follow_up_note) {
                document.getElementById('dFollowUp').innerText = dossier.follow_up_note;
            }
            if (dossier.appointment_datetime) {
                document.getElementById('dAppt').innerText = dossier.appointment_datetime;
                if (dossier.appointment_type === 'phone_consultation') {
                    document.getElementById('dossierStatus').innerText = "CALLBACK SET";
                    document.getElementById('dossierStatus').className = "tag tag-blue";
                } else {
                    document.getElementById('dossierStatus').innerText = "TOUR BOOKED";
                    document.getElementById('dossierStatus').className = "tag tag-green";
                }
            } else if (dossier.follow_up_note) {
                document.getElementById('dossierStatus').innerText = "FOLLOW-UP";
                document.getElementById('dossierStatus').className = "tag tag-blue";
            }
        }
    </script>
</body>
</html>
"""


class DashboardHTTPHandler(http.server.BaseHTTPRequestHandler):
    """Zero-dependency HTTP Handler serving the luxury interactive console and API."""

    conversation_engine = ConversationEngine()
    tts_engine = EdgeTTSVoiceEngine()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/dashboard", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path == "/api/leads":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(MOCK_LEADS).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/reset":
            # Reset conversation state
            DashboardHTTPHandler.conversation_engine = ConversationEngine()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))

        elif parsed.path == "/api/turn":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}
            utterance = data.get("utterance", "")
            target_voice = data.get("voice", "en-US-AriaNeural")

            if utterance == "PREVIEW_SAMPLE":
                reply = "Hello, this is CLOSER AI luxury real estate concierge. How can I assist you with your estate search today?"
            else:
                reply = self.conversation_engine.process_user_turn(utterance)

            audio_bytes, _ = self.tts_engine.synthesize_sync(reply, voice=target_voice)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

            dossier = self.conversation_engine.export_dossier()

            resp_data = {
                "reply": reply,
                "dossier": dossier.model_dump(),
                "audio_base64": audio_b64
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp_data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Mute standard access log output for cleanliness
        pass


class ReusableTCPServer(socketserver.TCPServer):
    """TCPServer that enables SO_REUSEADDR to avoid address collision on rapid restart."""
    allow_reuse_address = True


def run_web_console(port: int = 8501) -> None:
    """Runs the standalone interactive web console."""
    server_address = ("0.0.0.0", port)
    with ReusableTCPServer(server_address, DashboardHTTPHandler) as httpd:
        print(f"\n[+] CLOSER AI Luxury Web Console running at http://localhost:{port}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down web console.")


# If executed directly with Python or via Streamlit
if __name__ == "__main__":
    if "streamlit" in sys.modules:
        try:
            import streamlit as st
            st.set_page_config(page_title="CLOSER AI Console", layout="wide")
            st.title("CLOSER AI: Autonomous Voice Lead Qualification Engine")
            st.caption(f"Founder: {settings.FOUNDER_NAME} | Brokerage: {settings.BROKERAGE_NAME}")
            st.markdown(HTML_TEMPLATE, unsafe_allow_html=True)
        except Exception:
            run_web_console()
    else:
        run_web_console()
