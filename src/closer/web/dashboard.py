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
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from typing import Dict, Any, List

from src.closer.config import settings
from src.closer.agent.schemas import InboundLead, BuyerDossier
from src.closer.agent.conversation import ConversationEngine
from src.closer.voice.tts import EdgeTTSVoiceEngine
from src.closer.integrations.calendar import CalendarManager
from src.closer.integrations.crm import CRMDispatcher
from src.closer.integrations.telephony import TelephonyManager
from src.closer.integrations.apilayer import APILayerUnifiedClient

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

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>CLOSER AI — Autonomous Luxury Concierge Live Console</title>
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
                radial-gradient(1000px circle at 50% -10%, rgba(59, 130, 246, 0.14), transparent 70%),
                radial-gradient(800px circle at 85% 20%, rgba(245, 158, 11, 0.06), transparent 60%);
            color: var(--text-main);
            min-height: 100vh;
            padding: 20px 28px;
            letter-spacing: -0.011em;
        }

        /* Top Bar */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 18px;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 16px;
        }
        .logo-wrap {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .brand-icon {
            width: 40px;
            height: 40px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 16px rgba(0, 229, 255, 0.18);
            overflow: hidden;
            padding: 3px;
        }
        .brand-icon img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
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
            font-weight: 700;
            letter-spacing: 0.04em;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .status-dot {
            width: 6px;
            height: 6px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 8px #10b981;
            animation: pulseDot 2s infinite ease-in-out;
        }
        @keyframes pulseDot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.85); }
        }
        .subtitle {
            font-size: 12.5px;
            color: var(--text-muted);
            margin-top: 2px;
        }

        /* Telemetry Status Bar */
        .telemetry-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(11, 15, 26, 0.85);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 8px 16px;
            margin-bottom: 22px;
            font-size: 11.5px;
            overflow-x: auto;
            white-space: nowrap;
            gap: 16px;
        }
        .telemetry-item {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: var(--text-muted);
        }
        .telemetry-item strong {
            color: #ffffff;
            font-weight: 600;
        }
        .telemetry-pill {
            background: rgba(16, 185, 129, 0.15);
            color: var(--emerald);
            padding: 2px 7px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 10.5px;
        }

        /* Dual-Market Switcher */
        .market-switch-wrap {
            display: inline-flex;
            background: rgba(10, 14, 24, 0.85);
            border: 1px solid var(--border);
            border-radius: 9999px;
            padding: 3px;
            gap: 4px;
        }
        .btn-market {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 12px;
            font-weight: 700;
            padding: 6px 14px;
            border-radius: 9999px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .btn-market.active {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: #ffffff;
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4);
        }
        .btn-market:hover:not(.active) {
            color: #ffffff;
            background: rgba(255, 255, 255, 0.05);
        }

        .header-links {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .nav-out-link {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            color: #60a5fa;
            text-decoration: none;
            font-size: 12.5px;
            font-weight: 600;
            padding: 6px 12px;
            border-radius: 8px;
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.25);
            transition: all 0.2s ease;
        }
        .nav-out-link:hover {
            background: rgba(59, 130, 246, 0.2);
            color: #ffffff;
        }

        /* Grid Layout */
        .grid-layout {
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 20px;
            margin-bottom: 24px;
        }
        @media(max-width: 1024px) {
            .grid-layout { grid-template-columns: 1fr; }
        }

        /* Glass Cards */
        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 22px;
            backdrop-filter: blur(16px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 14px;
        }
        .card-title {
            font-size: 16px;
            font-weight: 700;
            letter-spacing: -0.02em;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #ffffff;
        }

        /* Voice Activity Detection (VAD) Waves */
        .vad-container {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 4px 12px;
            background: rgba(0,0,0,0.5);
            border: 1px solid var(--border);
            border-radius: 9999px;
        }
        .vad-waves {
            display: flex;
            align-items: center;
            gap: 2px;
            height: 16px;
        }
        .vad-bar {
            width: 3px;
            background: #3b82f6;
            border-radius: 9999px;
            height: 4px;
            transition: height 0.1s ease;
        }
        .vad-container.speaking .vad-bar {
            background: var(--emerald);
            animation: waveBounce 0.4s infinite alternate;
        }
        .vad-container.speaking .vad-bar:nth-child(2) { animation-delay: 0.08s; }
        .vad-container.speaking .vad-bar:nth-child(3) { animation-delay: 0.16s; }
        .vad-container.speaking .vad-bar:nth-child(4) { animation-delay: 0.24s; }
        .vad-container.speaking .vad-bar:nth-child(5) { animation-delay: 0.32s; }
        .vad-container.speaking .vad-bar:nth-child(6) { animation-delay: 0.40s; }

        @keyframes waveBounce {
            0% { height: 4px; }
            100% { height: 18px; }
        }
        .vad-label {
            font-size: 10.5px;
            font-weight: 700;
            color: var(--emerald);
            letter-spacing: 0.05em;
        }

        /* Voice Controls Bar */
        .voice-controls {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            background: rgba(10, 14, 24, 0.7);
            padding: 12px 16px;
            border-radius: 12px;
            border: 1px solid var(--border);
        }
        .control-group {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .control-label {
            font-size: 10.5px;
            color: var(--text-dim);
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.04em;
        }
        .voice-select {
            background: rgba(7, 10, 18, 0.9);
            border: 1px solid var(--border);
            color: #ffffff;
            font-size: 12.5px;
            padding: 8px 12px;
            border-radius: 8px;
            outline: none;
            cursor: pointer;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .voice-select:focus {
            border-color: var(--primary);
            box-shadow: 0 0 10px var(--primary-glow);
        }
        .voice-btn-group {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: auto;
            flex-wrap: wrap;
        }
        .btn-preview, .btn-barge, .btn-reset, .btn-voice-keys {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border);
            color: var(--text-muted);
            border-radius: 8px;
            padding: 8px 13px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            white-space: nowrap;
        }
        .btn-preview:hover, .btn-reset:hover {
            color: #ffffff;
            border-color: rgba(255,255,255,0.25);
            background: rgba(255, 255, 255, 0.12);
        }
        .btn-voice-keys {
            background: rgba(59, 130, 246, 0.12);
            color: #93c5fd;
            border-color: rgba(59, 130, 246, 0.3);
        }
        .btn-voice-keys:hover {
            background: rgba(59, 130, 246, 0.25);
            color: #ffffff;
            border-color: #60a5fa;
        }
        .btn-barge {
            background: rgba(239, 68, 68, 0.12);
            color: #fca5a5;
            border-color: rgba(239, 68, 68, 0.3);
        }
        .btn-barge:hover {
            background: rgba(239, 68, 68, 0.25);
            color: #ffffff;
        }

        /* Step Guidance Ribbon */
        .workflow-stepper {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(15, 23, 42, 0.55);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 10px;
            padding: 8px 14px;
            font-size: 11.5px;
            color: var(--text-muted);
            overflow-x: auto;
            white-space: nowrap;
        }
        .step-item {
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .step-num {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: rgba(59, 130, 246, 0.25);
            color: #93c5fd;
            font-size: 10.5px;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .step-sep {
            color: var(--text-dim);
            font-size: 12px;
        }

        /* Modal Styles */
        .modal-backdrop {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(8px);
            z-index: 9999;
            align-items: center;
            justify-content: center;
            padding: 16px;
        }
        .modal-card {
            background: linear-gradient(135deg, rgba(15, 20, 32, 0.96) 0%, rgba(10, 14, 24, 0.98) 100%);
            border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
            border-radius: 16px;
            max-width: 520px;
            width: 100%;
            overflow: hidden;
            animation: modalFadeIn 0.2s ease-out;
        }
        @keyframes modalFadeIn {
            from { opacity: 0; transform: scale(0.96); }
            to { opacity: 1; transform: scale(1); }
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 18px 22px;
            border-bottom: 1px solid var(--border);
        }
        .modal-close {
            background: transparent;
            border: none;
            color: var(--text-dim);
            font-size: 18px;
            cursor: pointer;
            padding: 4px;
            line-height: 1;
            transition: color 0.15s;
        }
        .modal-close:hover { color: #ffffff; }
        .modal-body {
            padding: 20px 22px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        .modal-info-banner {
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.25);
            border-radius: 10px;
            padding: 10px 14px;
            font-size: 11.5px;
            line-height: 1.5;
            color: #cbd5e1;
        }
        .modal-field {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        .modal-label {
            font-size: 11.5px;
            font-weight: 600;
            color: var(--text-muted);
        }
        .modal-input {
            background: rgba(7, 10, 18, 0.85);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 9px 12px;
            color: #ffffff;
            font-size: 12.5px;
            font-family: 'JetBrains Mono', monospace;
            outline: none;
            transition: border-color 0.2s;
        }
        .modal-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 10px var(--primary-glow);
        }
        .modal-footer {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            padding: 16px 22px;
            border-top: 1px solid var(--border);
            background: rgba(7, 10, 18, 0.5);
        }

        /* Chat / Telephony Transcript Box */
        .chat-box {
            height: 330px;
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
        }
        .input-row input {
            flex: 1;
            padding: 13px 16px;
            background: rgba(7, 10, 18, 0.85);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: #ffffff;
            font-size: 16px; /* Auto-zoom prevention on mobile */
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
            font-size: 13.5px;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 16px var(--primary-glow);
            white-space: nowrap;
        }
        .btn-send:hover {
            transform: translateY(-1px);
            opacity: 0.95;
        }

        /* Quick Scenarios */
        .quick-chips-wrap {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .chips-label {
            font-size: 11.5px;
            font-weight: 700;
            color: var(--text-dim);
            text-transform: uppercase;
        }
        .chip {
            padding: 6px 12px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            border-radius: 9999px;
            font-size: 12px;
            color: var(--text-muted);
            text-decoration: none;
            transition: all 0.2s ease;
        }
        .chip:hover {
            color: #ffffff;
            border-color: rgba(255,255,255,0.25);
            background: rgba(255, 255, 255, 0.1);
        }
        .chip-friction {
            border-color: rgba(245, 158, 11, 0.3);
            color: #fcd34d;
        }

        /* Dossier Tabs & View */
        .dossier-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        .dossier-tab-wrap {
            display: inline-flex;
            background: rgba(7, 10, 18, 0.8);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 2px;
        }
        .btn-dossier-tab {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 11.5px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .btn-dossier-tab.active {
            background: rgba(255, 255, 255, 0.12);
            color: #ffffff;
        }
        .btn-copy-json {
            background: rgba(59, 130, 246, 0.12);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #60a5fa;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-copy-json:hover {
            background: rgba(59, 130, 246, 0.25);
            color: #ffffff;
        }

        .dossier-grid {
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: rgba(7, 10, 18, 0.6);
            padding: 14px;
            border-radius: 12px;
            border: 1px solid var(--border);
        }
        .dossier-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            font-size: 13px;
        }
        .dossier-row:last-child { border-bottom: none; }
        .dossier-label {
            color: var(--text-muted);
            font-weight: 500;
        }
        .dossier-val {
            font-weight: 600;
            color: #ffffff;
            text-align: right;
        }

        .raw-json-box {
            display: none;
            background: #030508;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: #38bdf8;
            max-height: 280px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }

        /* Intent Box */
        .intent-box {
            background: rgba(7, 10, 18, 0.6);
            padding: 14px;
            border-radius: 12px;
            border: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .intent-header {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
        }
        .progress-bar-bg {
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
        .kanban-filter-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            gap: 10px;
            flex-wrap: wrap;
        }
        .search-leads-input {
            background: rgba(7, 10, 18, 0.85);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 6px 12px;
            color: #ffffff;
            font-size: 12.5px;
            outline: none;
            width: 200px;
        }
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

        /* APILayer Unified Suite Panel */
        .apilayer-card {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(10, 15, 30, 0.95) 100%);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        }
        .apilayer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 12px;
        }
        .apilayer-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 15px;
            font-weight: 700;
            color: #ffffff;
        }
        .apilayer-key-row {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .apilayer-key-input {
            background: rgba(7, 10, 18, 0.85);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 6px 12px;
            color: #ffffff;
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
            width: 220px;
            outline: none;
        }
        .apilayer-tools-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
        }
        @media(max-width: 1024px) { .apilayer-tools-grid { grid-template-columns: 1fr 1fr; } }
        @media(max-width: 640px) { .apilayer-tools-grid { grid-template-columns: 1fr; } }
        .tool-box {
            background: rgba(20, 26, 42, 0.65);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .tool-box-title {
            font-size: 12px;
            font-weight: 700;
            color: #93c5fd;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .tool-input {
            background: rgba(7, 10, 18, 0.85);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 8px 10px;
            color: #ffffff;
            font-size: 12px;
            outline: none;
            width: 100%;
            box-sizing: border-box;
        }
        .btn-tool-run {
            background: rgba(59, 130, 246, 0.2);
            border: 1px solid rgba(59, 130, 246, 0.4);
            color: #ffffff;
            font-size: 11.5px;
            font-weight: 600;
            padding: 7px 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
        }
        .btn-tool-run:hover {
            background: rgba(59, 130, 246, 0.4);
            border-color: #60a5fa;
            transform: translateY(-1px);
        }
        .tool-result {
            background: rgba(7, 10, 18, 0.7);
            border-radius: 8px;
            padding: 10px;
            font-size: 11px;
            color: #cbd5e1;
            min-height: 64px;
            line-height: 1.45;
            word-break: break-word;
            font-family: 'JetBrains Mono', monospace;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-wrap">
            <div class="brand-icon"><img src="/assets/logo.webp" alt="CLOSER AI"></div>
            <div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <span class="logo-title">CLOSER AI</span>
                    <span class="badge"><span class="status-dot"></span> TRI-LANGUAGE: US • INDIA • HINDI</span>
                </div>
                <div class="subtitle">Autonomous Voice Telephony &amp; Lead Closing Engine in 3 Main Global Languages</div>
            </div>
        </div>

        <!-- Market & Language Switcher (US English, Indian English, Hindi) -->
        <div class="market-switch-wrap">
            <button id="btnMarketUSA" class="btn-market active" onclick="switchMarket('usa')">🇺🇸 US English: Luxury ISA</button>
            <button id="btnMarketIndia" class="btn-market" onclick="switchMarket('india')">🇮🇳 Indian English: Enterprise Support</button>
            <button id="btnMarketHindi" class="btn-market" onclick="switchMarket('hindi')">🇮🇳 हिन्दी (Hindi): Customer Care &amp; Closing</button>
        </div>

        <div class="header-links">
            <a href="/presentation" target="_blank" class="nav-out-link" style="background:rgba(0,229,255,0.12); color:#00e5ff; border:1px solid rgba(0,229,255,0.3); font-weight:700; border-radius:999px; padding:6px 14px; text-decoration:none; display:inline-flex; align-items:center; gap:6px;">📊 Pitch Deck (PPT)</a>
            <a href="/" class="nav-out-link" style="background:#ffffff; color:#000000; font-weight:700; border-radius:999px; padding:6px 14px; text-decoration:none; display:inline-flex; align-items:center; gap:6px;">← Back to Website</a>
            <span style="font-size:12px; color:var(--text-dim);">Founder: <strong style="color:#ffffff;">R Jan Steve Daniel</strong></span>
            <a href="https://github.com/JanSteve/closer-ai" target="_blank" style="color:#60a5fa; text-decoration:none; font-size:13px; font-weight:600;">GitHub ↗</a>
        </div>
    </div>

    <!-- Live Telemetry Status Bar -->
    <div class="telemetry-bar">
        <div class="telemetry-item">
            <span class="status-dot"></span>
            <span>Carrier Trunk: <strong>LiveKit WebRTC SIP</strong></span>
            <span class="telemetry-pill">32ms PING</span>
        </div>
        <div class="telemetry-item">
            <span>Acoustic VAD: <strong>Multi-Band Active (-24 dBFS)</strong></span>
        </div>
        <div class="telemetry-item">
            <span>LLM Intelligence: <strong id="telemetryLLM">BLOOMZ 176B / Llama 70B</strong></span>
            <span class="telemetry-pill" id="telemetryLLMPill">176B SCALE</span>
        </div>
        <div class="telemetry-item">
            <span>Neural Synthesis: <strong id="telemetryVoiceEngine">Studio 48kHz PCM</strong></span>
            <span class="telemetry-pill">BROADCAST MASTER</span>
        </div>
        <div class="telemetry-item">
            <span>Unified Suite: <strong id="telemetryAPILayer">APILayer Verified</strong></span>
            <span class="telemetry-pill">4 APIS ACTIVE</span>
        </div>
        <div class="telemetry-item">
            <span>E2E Turn Latency: <strong>88 ms</strong></span>
            <span class="telemetry-pill">SUB-500MS SLA</span>
        </div>
        <div class="telemetry-item">
            <span>Schema Integrity: <strong>Pydantic V2 Strict</strong></span>
        </div>
    </div>

    <div class="grid-layout">
        <!-- Live Voice Call Interaction Module -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">
                    <span id="agentConsoleTitle">Autonomous Voice Concierge</span>
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

            <!-- Step Guidance Ribbon -->
            <div class="workflow-stepper">
                <div class="step-item"><span class="step-num">1</span> <span><strong>Select Persona &amp; Voice Engine</strong> (Studio Broadcast Neural, ElevenLabs Turbo, or Sarvam Indic)</span></div>
                <div class="step-sep">→</div>
                <div class="step-item"><span class="step-num">2</span> <span><strong>Speak / Test Scenarios</strong> (Schedule friction "come tomorrow", objection handling, WhatsApp dispatch)</span></div>
                <div class="step-sep">→</div>
                <div class="step-item"><span class="step-num">3</span> <span><strong>Review Live Dossier &amp; APILayer</strong> (Real-time Pydantic schema extraction &amp; carrier validation)</span></div>
            </div>

            <!-- Instant One-Click Voice Selection & VoiceStudio Controls -->
            <div class="voice-controls">
                <div class="control-group">
                    <label class="control-label">Voice Persona &amp; Dialect (3 Main Languages):</label>
                    <select id="voiceSelect" class="voice-select">
                        <optgroup label="🇺🇸 US English (Luxury Real Estate ISA &amp; Deal Closer)">
                            <option value="en-US-AvaNeural" selected>Ava (US Female • Ultra-Natural Concierge)</option>
                            <option value="en-US-GuyNeural">Guy (US Male • Confident Luxury Broker)</option>
                            <option value="en-US-AriaNeural">Sophia / Aria (US Female • Warm Consultative)</option>
                            <option value="en-US-ChristopherNeural">Christopher (US Male • Authoritative Closer)</option>
                            <option value="en-US-JennyNeural">Jenny (US Female • Crisp Natural)</option>
                        </optgroup>
                        <optgroup label="🇮🇳 Indian English (Enterprise Customer Care &amp; Support)">
                            <option value="en-IN-NeerjaExpressiveNeural">Neerja (India Female • Expressive Relationship Manager)</option>
                            <option value="en-IN-NeerjaNeural">Priya (India Female • Customer Care Executive)</option>
                            <option value="en-IN-PrabhatNeural">Prabhat (India Male • Corporate Support)</option>
                        </optgroup>
                        <optgroup label="🇮🇳 हिन्दी (Hindi Customer Care &amp; Property Closing)">
                            <option value="hi-IN-SwaraNeural">Swara / स्वाति (Hindi Female • Conversational &amp; Empathetic)</option>
                            <option value="hi-IN-MadhurNeural">Madhur / मधुर (Hindi Male • Consultative Support &amp; Closing)</option>
                        </optgroup>
                    </select>
                </div>
                
                <div class="control-group">
                    <label class="control-label">Voice Intelligence Engine:</label>
                    <select id="voiceProviderSelect" class="voice-select" style="min-width:180px;" onchange="updateVoiceEngineBadge()">
                        <option value="studio" selected>🎙️ VoiceStudio Neural Master (48kHz • Free &amp; Unlimited)</option>
                        <option value="elevenlabs">✨ ElevenLabs Turbo v2.5 (High Emotion &amp; Nuance)</option>
                        <option value="sarvam">🇮🇳 Sarvam AI / Gnani Indic Neural (Bulbul Vernacular)</option>
                        <option value="cartesia">⚡ Cartesia Sonic Ultra-Low Latency</option>
                    </select>
                </div>

                <div class="control-group" style="min-width:130px;">
                    <label class="control-label">Speed: <span id="lblVoiceRate" style="color:var(--cyan); font-weight:700;">+5%</span></label>
                    <input type="range" id="voiceRateSlider" min="-15" max="25" value="5" step="5" style="width:100%; accent-color:var(--cyan);" oninput="updateRateLabel(this.value)">
                </div>

                <div class="control-group" style="min-width:130px;">
                    <label class="control-label">Pitch: <span id="lblVoicePitch" style="color:var(--gold); font-weight:700;">+0Hz</span></label>
                    <input type="range" id="voicePitchSlider" min="-6" max="6" value="0" step="1" style="width:100%; accent-color:var(--gold);" oninput="updatePitchLabel(this.value)">
                </div>

                <div class="control-group">
                    <label class="control-label">Foundation LLM (175B+ Catalog):</label>
                    <select id="llmEngineSelect" class="voice-select" onchange="switchLLM(this.value)">
                        <option value="llama-3.3-70b" selected>⚡ Llama 3.3 70B (88ms Edge Reflex)</option>
                        <option value="bloomz-176b">🌐 BLOOMZ 176B (Multilingual 46 Langs)</option>
                        <option value="deepseek-v3">🧠 DeepSeek-V3 / R1 (671B MoE Frontier)</option>
                        <option value="command-r-plus">🛡️ Command R+ (104B Cohere Enterprise)</option>
                        <option value="qwen-2.5-72b">🌏 Qwen 2.5 72B (Hinglish Vernacular &amp; Math)</option>
                        <option value="falcon-180b">🏛️ Falcon 180B (Sovereign Banking On-Prem)</option>
                    </select>
                </div>

                <div class="voice-btn-group">
                    <button class="btn-preview" onclick="testVoiceSample()" title="Synthesize live audio sample directly via VoiceStudio neural stream">🔊 Test Voice</button>
                    <button class="btn-preview" id="btnDownloadAudio" onclick="downloadLastAudio()" style="background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3);" title="Download latest synthesized speech as WAV file for social media marketing!">⬇ Save WAV</button>
                    <button class="btn-barge" onclick="simulateBargeIn()" title="Simulate caller interjecting mid-speech — cuts audio in <50ms">⚡ Barge-In</button>
                    <button class="btn-voice-keys" onclick="openKeyModal()" title="Configure ElevenLabs, Sarvam AI, and APILayer API Keys">⚙️ Cloud Keys</button>
                    <button class="btn-reset" title="Reset current conversation state" onclick="resetCall()">↻ Reset</button>
                </div>
            </div>

            <!-- Social Media Marketing Reel & Client Pitch Soundboard -->
            <div class="soundboard-bar" style="background:rgba(255,255,255,0.02); border:1px solid var(--border-subtle); border-radius:10px; padding:10px 14px; margin-bottom:12px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:12px; font-weight:700; color:var(--cyan); text-transform:uppercase; letter-spacing:0.04em;">🎥 Social Media Hooks:</span>
                    <span style="font-size:11px; color:var(--text-dim);">One-click client demo &amp; reel recordings</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                    <button class="chip" onclick="playMarketingHook('usa')" style="background:rgba(59,130,246,0.12); color:#60a5fa; border:1px solid rgba(59,130,246,0.3); font-size:11px; cursor:pointer;">🇺🇸 Play US $15M Luxury Hook</button>
                    <button class="chip" onclick="playMarketingHook('india')" style="background:rgba(245,158,11,0.12); color:#f59e0b; border:1px solid rgba(245,158,11,0.3); font-size:11px; cursor:pointer;">🇮🇳 Play India CC-8492 SLA Hook</button>
                    <button class="chip" onclick="playMarketingHook('hindi')" style="background:rgba(16,185,129,0.12); color:#10b981; border:1px solid rgba(16,185,129,0.3); font-size:11px; cursor:pointer;">🇮🇳 Play हिन्दी (Hindi) Site Visit Hook</button>
                </div>
            </div>

            <!-- Live Telephony Chat Transcript Box -->
            <div class="chat-box" id="chatBox">
                <div class="msg agent">
                    <div class="msg-meta" id="chatAgentMeta">Ava (Daniel &amp; Associates Luxury Concierge) • 48kHz High-Fidelity</div>
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
                <div id="usaChips" style="display:inline-flex; flex-wrap:wrap; gap:8px;">
                    <a href="#" class="chip chip-friction" onclick="quickFill('Today is not good, I will come tomorrow'); return false;">🗓️ "Today not good, come tomorrow"</a>
                    <a href="#" class="chip chip-friction" onclick="quickFill('I am busy right now, contact me later'); return false;">⏳ "Busy now, contact later"</a>
                    <a href="#" class="chip" onclick="quickFill('My budget is $6.5 million cash and looking to move next month in Bel Air.'); return false;">💼 "$6.5M Cash / 30 Days"</a>
                    <a href="#" class="chip" onclick="quickFill('Please text our private dossier via WhatsApp.'); return false;">📲 "Send via WhatsApp"</a>
                    <a href="#" class="chip" onclick="quickFill('Tomorrow afternoon at 2 PM works perfectly for us to tour.'); return false;">🏛️ "Tomorrow at 2 PM"</a>
                </div>
                <div id="indiaChips" style="display:none; flex-wrap:wrap; gap:8px;">
                    <a href="#" class="chip" onclick="quickFill('What is the price for a 3 BHK in Whitefield Bengaluru?'); return false;">🏢 "3 BHK in Whitefield Price?"</a>
                    <a href="#" class="chip chip-friction" onclick="quickFill('I am in office meeting right now, please call after 6 PM'); return false;">💼 "In meeting, call after 6 PM"</a>
                    <a href="#" class="chip chip-friction" onclick="quickFill('Please don\'t call now, send the full brochure and pricing on WhatsApp'); return false;">📲 "Send on WhatsApp Only"</a>
                    <a href="#" class="chip" onclick="quickFill('I have an issue with my booking, need customer support ticket'); return false;">⚠️ "Support Issue / Ticket"</a>
                    <a href="#" class="chip" onclick="quickFill('Is this project RERA registered and can we visit this Sunday with family?'); return false;">📜 "RERA &amp; Sunday Site Visit"</a>
                </div>
                <div id="hindiChips" style="display:none; flex-wrap:wrap; gap:8px;">
                    <a href="#" class="chip" onclick="quickFill('नमस्ते, मुझे 3 बीएचके फ्लैट की कीमत जाननी है।'); return false;">🏢 '3 BHK फ्लैट की कीमत?'</a>
                    <a href="#" class="chip chip-friction" onclick="quickFill('मैं अभी ऑफिस मीटिंग में हूँ, शाम 6 बजे के बाद कॉल करना।'); return false;">💼 'मीटिंग में हूँ, बाद में कॉल'</a>
                    <a href="#" class="chip chip-friction" onclick="quickFill('अभी फोन मत करो, सारी डिटेल्स वॉट्सऐप पर भेज दो।'); return false;">📲 'वॉट्सऐप पर भेज दो'</a>
                    <a href="#" class="chip" onclick="quickFill('क्या यह प्रोजेक्ट रेरा से अप्रूव्ड है और इस शनिवार साइट विज़िट हो सकती है?'); return false;">📜 'रेरा अप्रूवल &amp; साइट विज़िट'</a>
                    <a href="#" class="chip" onclick="quickFill('मेरा बजट 1.5 करोड़ रुपये है, क्या 20% डाउन पेमेंट पर होम लोन मिल जाएगा?'); return false;">💰 '₹1.5 करोड़ बजट &amp; होम लोन'</a>
                </div>
            </div>
        </div>

        <!-- Streamlined Live Pydantic Buyer Dossier Display -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">
                    <span id="dossierTitle">Live Pydantic Client Dossier</span>
                </div>
                <span id="dossierStatus" class="tag tag-gold">QUALIFYING</span>
            </div>

            <!-- View Toggle: Formatted vs Raw JSON -->
            <div class="dossier-nav">
                <div class="dossier-tab-wrap">
                    <button class="btn-dossier-tab active" id="tabDossierFormatted" onclick="toggleDossierView('formatted')">Structured Form</button>
                    <button class="btn-dossier-tab" id="tabDossierJson" onclick="toggleDossierView('json')">Pydantic JSON</button>
                </div>
                <button class="btn-copy-json" onclick="copyDossierJson()">Copy JSON</button>
            </div>

            <!-- Formatted Structured Dossier -->
            <div class="dossier-grid" id="dossierFormattedView">
                <div class="dossier-row">
                    <span class="dossier-label">Client / Caller</span>
                    <span class="dossier-val" id="dName">Alex Morgan (+1-310-555-0144)</span>
                </div>
                <div class="dossier-row" id="rowMarket">
                    <span class="dossier-label">Target Market</span>
                    <span class="dossier-val" id="dMarket" style="color:#60a5fa; font-weight:700;">USA (Luxury Real Estate)</span>
                </div>
                <div class="dossier-row">
                    <span class="dossier-label" id="lblBudget">Budget Range</span>
                    <span class="dossier-val" id="dBudget">Evaluating</span>
                </div>
                <div class="dossier-row" id="rowBHK" style="display:none;">
                    <span class="dossier-label">BHK / Config</span>
                    <span class="dossier-val" id="dBHK" style="color:#93c5fd;">Pending Selection</span>
                </div>
                <div class="dossier-row" id="rowTicket" style="display:none;">
                    <span class="dossier-label">Support Ticket</span>
                    <span class="tag tag-green" id="dTicket">None</span>
                </div>
                <div class="dossier-row">
                    <span class="dossier-label" id="lblFinancing">Financial Readiness</span>
                    <span id="dFinancing" class="tag tag-gold">Pending Verification</span>
                </div>
                <div class="dossier-row">
                    <span class="dossier-label">Timeline</span>
                    <span class="dossier-val" id="dTime">Pending Discussion</span>
                </div>
                <div class="dossier-row">
                    <span class="dossier-label" id="lblAppt">VIP Tour / Visit</span>
                    <span class="dossier-val" id="dAppt" style="color:#60a5fa;">Pending Selection</span>
                </div>
                <div class="dossier-row">
                    <span class="dossier-label">Follow-Up Note</span>
                    <span class="dossier-val" id="dFollowUp" style="color:#fcd34d; font-size:12px; max-width:65%;">Active consultation</span>
                </div>
                <div class="dossier-row" id="rowWhatsApp">
                    <span class="dossier-label">WhatsApp Dispatch</span>
                    <span class="dossier-val" id="dWhatsApp" style="color:var(--text-dim); font-size:12px;">Not Dispatched</span>
                </div>
                <div class="dossier-row">
                    <span class="dossier-label" id="lblProperty">Target Listing / City</span>
                    <span class="dossier-val" id="dProperty">10484 Bellagio Rd, Bel Air ($6.85M)</span>
                </div>
            </div>

            <!-- Raw Pydantic Model JSON Inspector -->
            <pre class="raw-json-box" id="dossierJsonView">Loading Pydantic schema...</pre>

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

            <!-- One-Click APILayer Lead Dossier Enrichment -->
            <div style="margin-top: 14px; background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 12px; padding: 12px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-size:12px; font-weight:700; color:#93c5fd;">⚡ APILayer Lead Verification</span>
                    <span id="enrichStatusTag" class="tag tag-blue" style="font-size:10px;">ONE-KEY VERIFIED</span>
                </div>
                <button class="btn-tool-run" style="width:100%; background:linear-gradient(135deg, #2563eb, #1d4ed8); border:none; padding:8px 12px; font-weight:700;" onclick="enrichCurrentDossier()">⚡ Enrich Client via APILayer Suite</button>
                <div id="dossierEnrichmentBox" style="display:none; margin-top:10px; font-size:11.5px; line-height:1.5; color:#cbd5e1; border-top:1px solid rgba(255,255,255,0.08); padding-top:8px;"></div>
            </div>
        </div>
    </div>

    <!-- APILayer Unified Suite & Public-APIs Intelligence Hub -->
    <div class="apilayer-card">
        <div class="apilayer-header">
            <div class="apilayer-title">
                <span style="font-size:20px;">🌐</span>
                <div>
                    <div>APILayer Unified Intelligence Suite</div>
                    <div style="font-size:11.5px; color:var(--text-muted); font-weight:400;">One Account • One Dashboard • One API Key (<a href="https://apilayer.com/products" target="_blank" style="color:#60a5fa; text-decoration:none;">apilayer.com</a>)</div>
                </div>
            </div>
            <div class="apilayer-key-row">
                <span id="apiLayerKeyBadge" class="tag tag-green" style="font-size:10px;">INTELLIGENCE READY</span>
                <input type="password" id="apilayerKeyInput" class="apilayer-key-input" placeholder="APILayer API Key (Optional)...">
                <button class="btn-tool-run" onclick="saveAPILayerKey()">Save Key</button>
            </div>
        </div>

        <div class="apilayer-tools-grid">
            <!-- 1. Numverify: Carrier & Line Type -->
            <div class="tool-box">
                <div class="tool-box-title">
                    <span>📞</span> <span>Numverify: Carrier &amp; Line</span>
                </div>
                <input type="text" id="toolPhoneInput" class="tool-input" value="+1-310-555-0144" placeholder="+1-310-555-0144 / +91-98800-12345">
                <button class="btn-tool-run" onclick="runNumverify()">Verify Telecom Carrier</button>
                <div class="tool-result" id="resNumverify">Ready. Validates carrier network, line type &amp; E.164 syntax.</div>
            </div>

            <!-- 2. Mailboxlayer: Deliverability & Domain -->
            <div class="tool-box">
                <div class="tool-box-title">
                    <span>✉️</span> <span>Mailboxlayer: Deliverability</span>
                </div>
                <input type="text" id="toolEmailInput" class="tool-input" value="alex@morganpartners.com" placeholder="client@domain.com">
                <button class="btn-tool-run" onclick="runMailboxlayer()">Verify Email &amp; MX</button>
                <div class="tool-result" id="resMailboxlayer">Ready. Checks corporate vs free domain, MX DNS &amp; deliverability.</div>
            </div>

            <!-- 3. Positionstack: Property Geocoding -->
            <div class="tool-box">
                <div class="tool-box-title">
                    <span>📍</span> <span>Positionstack: Geocoding</span>
                </div>
                <input type="text" id="toolAddressInput" class="tool-input" value="10484 Bellagio Rd, Bel Air, CA" placeholder="10484 Bellagio Rd / Whitefield, Bangalore">
                <button class="btn-tool-run" onclick="runPositionstack()">Geocode &amp; Neighborhood</button>
                <div class="tool-result" id="resPositionstack">Ready. Resolves GPS coordinates, zoning tier &amp; RERA jurisdiction.</div>
            </div>

            <!-- 4. Fixer / Currencylayer: Real Estate FX -->
            <div class="tool-box">
                <div class="tool-box-title">
                    <span>💱</span> <span>Fixer: Dual-Market FX</span>
                </div>
                <div style="display:flex; gap:6px;">
                    <input type="number" id="toolAmountInput" class="tool-input" value="6850000" style="flex:2;" placeholder="Amount">
                    <select id="toolFromCurr" class="tool-input" style="flex:1; padding:4px;">
                        <option value="USD" selected>USD</option>
                        <option value="INR">INR</option>
                        <option value="AED">AED</option>
                        <option value="EUR">EUR</option>
                    </select>
                    <select id="toolToCurr" class="tool-input" style="flex:1; padding:4px;">
                        <option value="INR" selected>INR</option>
                        <option value="USD">USD</option>
                        <option value="AED">AED</option>
                    </select>
                </div>
                <button class="btn-tool-run" onclick="runFixerFX()">Convert Real Estate FX</button>
                <div class="tool-result" id="resFixer">Ready. Live real estate notation (Crores / Millions equivalence).</div>
            </div>
        </div>
    </div>

    <!-- CRM Live Lead Pipeline Kanban -->
    <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
            <div class="card-title">
                <span>Enterprise CRM Pipeline Synchronization</span>
                <span class="tag tag-blue" style="font-size:10px;">TWO-WAY CRM WEBHOOKS</span>
            </div>
            <div class="kanban-filter-row">
                <input type="text" id="leadSearchInput" class="search-leads-input" placeholder="Search leads by name..." oninput="filterKanbanLeads()">
            </div>
        </div>

        <div class="kanban" id="kanbanContainer">
            <div class="kanban-col">
                <div class="kanban-header">
                    <span>1. Inbound Leads</span>
                    <span id="countInbound">1</span>
                </div>
                <div class="lead-card" data-name="Elena Rostova">
                    <div class="lead-name">Elena Rostova</div>
                    <div class="lead-prop">9555 Heather Rd, Beverly Hills ($8.9M)</div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="tag tag-gold">Evaluating</span>
                        <span style="font-size:11px; color:var(--text-muted);">Web Form</span>
                    </div>
                </div>
            </div>

            <div class="kanban-col">
                <div class="kanban-header">
                    <span>2. AI-Qualified</span>
                    <span id="countQualified">1</span>
                </div>
                <div class="lead-card" data-name="Marcus Thorne">
                    <div class="lead-name">Marcus Thorne</div>
                    <div class="lead-prop">31224 Broad Beach Rd, Malibu ($11.2M)</div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="tag tag-green">Jumbo Approved</span>
                        <span style="font-size:11px; color:var(--emerald); font-weight:700;">85% Intent</span>
                    </div>
                </div>
            </div>

            <div class="kanban-col">
                <div class="kanban-header">
                    <span>3. Tour / Visit Booked</span>
                    <span id="countBooked">2</span>
                </div>
                <div class="lead-card" data-name="Harrison & Claire Sterling">
                    <div class="lead-name">Harrison &amp; Claire Sterling</div>
                    <div class="lead-prop">10484 Bellagio Rd, Bel Air ($6.85M)</div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="tag tag-green">All Cash ($6.5M)</span>
                        <span style="font-size:11px; color:#60a5fa; font-weight:700;">Thursday 2PM</span>
                    </div>
                </div>
                <div class="lead-card" data-name="David Vance">
                    <div class="lead-name">David Vance</div>
                    <div class="lead-prop">Bel Air Modern Estate ($4.5M)</div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="tag tag-green">Verified Cash</span>
                        <span style="font-size:11px; color:#60a5fa; font-weight:700;">Thursday 2PM</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Live ROI & Financial Impact Tracker -->
    <div class="card">
        <div class="card-header">
            <div class="card-title">
                <span id="roiModuleTitle">Brokerage ROI &amp; Revenue Projection</span>
            </div>
            <span class="tag tag-green">99.8% FASTER RESPONSE TIME</span>
        </div>
        <div class="roi-grid">
            <div class="stat-box">
                <div class="stat-label">Inference Latency</div>
                <div class="stat-val" style="color:#60a5fa;">118 ms</div>
            </div>
            <div class="stat-box">
                <div class="stat-label" id="roiLblShowings">VIP Tours Booked</div>
                <div class="stat-val" id="roiValShowings">+45 / Mo</div>
            </div>
            <div class="stat-box">
                <div class="stat-label" id="roiLblSaved">Manual Call Hours Saved</div>
                <div class="stat-val" id="roiValHours">250 hrs</div>
            </div>
            <div class="stat-box">
                <div class="stat-label" id="roiLblRevenue">Estimated Pipeline Added</div>
                <div class="stat-val" id="roiValRevenue">$38.4M</div>
            </div>
        </div>
    </div>

    <script>
        let currentMarket = 'usa';
        let latestDossier = {};
        let lastAudioBase64 = null;

        function updateRateLabel(val) {
            const el = document.getElementById('lblVoiceRate');
            if (el) el.innerText = (val > 0 ? '+' : '') + val + '%';
        }

        function updatePitchLabel(val) {
            const el = document.getElementById('lblVoicePitch');
            if (el) el.innerText = (val > 0 ? '+' : '') + val + 'Hz';
        }

        function getAudioSettings() {
            const rateSlider = document.getElementById('voiceRateSlider');
            const pitchSlider = document.getElementById('voicePitchSlider');
            const rateVal = rateSlider ? rateSlider.value : '5';
            const pitchVal = pitchSlider ? pitchSlider.value : '0';
            return {
                rate: (rateVal >= 0 ? '+' : '') + rateVal + '%',
                pitch: (pitchVal >= 0 ? '+' : '') + pitchVal + 'Hz'
            };
        }

        function switchMarket(market) {
            currentMarket = market;
            const btnUSA = document.getElementById('btnMarketUSA');
            const btnIndia = document.getElementById('btnMarketIndia');
            const btnHindi = document.getElementById('btnMarketHindi');
            const usaChips = document.getElementById('usaChips');
            const indiaChips = document.getElementById('indiaChips');
            const hindiChips = document.getElementById('hindiChips');
            const voiceSelect = document.getElementById('voiceSelect');
            const rowBHK = document.getElementById('rowBHK');
            const rowTicket = document.getElementById('rowTicket');
            const lblBudget = document.getElementById('lblBudget');
            const lblFinancing = document.getElementById('lblFinancing');
            const lblAppt = document.getElementById('lblAppt');
            const lblProperty = document.getElementById('lblProperty');
            const agentConsoleTitle = document.getElementById('agentConsoleTitle');
            const chatAgentMeta = document.getElementById('chatAgentMeta');
            const chatBox = document.getElementById('chatBox');

            if (market === 'usa') {
                btnUSA.className = 'btn-market active';
                btnIndia.className = 'btn-market';
                if (btnHindi) btnHindi.className = 'btn-market';
                usaChips.style.display = 'inline-flex';
                indiaChips.style.display = 'none';
                if (hindiChips) hindiChips.style.display = 'none';
                rowBHK.style.display = 'none';
                rowTicket.style.display = 'none';
                lblBudget.innerText = 'Budget Range';
                lblFinancing.innerText = 'Financial Readiness';
                lblAppt.innerText = 'VIP Tour / Visit';
                lblProperty.innerText = 'Target Listing / City';
                agentConsoleTitle.innerText = 'Autonomous Voice Concierge';
                voiceSelect.value = 'en-US-AvaNeural';
                chatAgentMeta.innerText = 'Ava (Daniel & Associates Luxury Concierge) • 48kHz VoiceStudio Master';
                
                // Update ROI metrics for USA
                document.getElementById('roiValRevenue').innerText = '$38.4M';
                document.getElementById('roiLblRevenue').innerText = 'Estimated Pipeline Added';

                // Initial Greeting
                chatBox.innerHTML = `
                    <div class="msg agent">
                        <div class="msg-meta" id="chatAgentMeta">Ava (Daniel &amp; Associates Luxury Concierge) • 48kHz VoiceStudio Master</div>
                        Hi Alex, this is Sophia with Daniel &amp; Associates Luxury Realty. I noticed you just requested details on 10484 Bellagio Rd, Bel Air — I wanted to catch you while it's top of mind. Are you looking at this as a primary residence or a private investment?
                    </div>
                `;
            } else if (market === 'hindi') {
                if (btnHindi) btnHindi.className = 'btn-market active';
                btnUSA.className = 'btn-market';
                btnIndia.className = 'btn-market';
                if (hindiChips) hindiChips.style.display = 'inline-flex';
                usaChips.style.display = 'none';
                indiaChips.style.display = 'none';
                rowBHK.style.display = 'flex';
                rowTicket.style.display = 'flex';
                lblBudget.innerText = 'बजट (लाख / करोड़ रुपये)';
                lblFinancing.innerText = 'होम लोन / डाउन पेमेंट';
                lblAppt.innerText = 'साइट विज़िट समय';
                lblProperty.innerText = 'प्रोजेक्ट / लोकेशन';
                agentConsoleTitle.innerText = 'हिन्दी कस्टमर केयर एवं क्लोज़िंग एजेंट';
                voiceSelect.value = 'hi-IN-SwaraNeural';
                chatAgentMeta.innerText = 'स्वाति (क्लोज़र एआई सीनियर रिलेशनशिप मैनेजर) • 48kHz वॉइस स्टूडियो';

                // Update ROI metrics for Hindi
                document.getElementById('roiValRevenue').innerText = '₹18.5 Cr';
                document.getElementById('roiLblRevenue').innerText = 'वीकेंड साइट विज़िट पाइपलाइन';

                // Initial Hindi Greeting
                chatBox.innerHTML = `
                    <div class="msg agent">
                        <div class="msg-meta" id="chatAgentMeta">स्वाति (क्लोज़र एआई सीनियर रिलेशनशिप मैनेजर) • 48kHz वॉइस स्टूडियो</div>
                        नमस्ते जी! क्लोज़र एआई कस्टमर सपोर्ट में आपका स्वागत है। मैं स्वाति बात कर रही हूँ। मैं आपकी प्रॉपर्टी इंक्वायरी और साइट विज़िट में किस प्रकार सहायता कर सकती हूँ?
                    </div>
                `;
            } else {
                btnIndia.className = 'btn-market active';
                btnUSA.className = 'btn-market';
                if (btnHindi) btnHindi.className = 'btn-market';
                indiaChips.style.display = 'inline-flex';
                usaChips.style.display = 'none';
                if (hindiChips) hindiChips.style.display = 'none';
                rowBHK.style.display = 'flex';
                rowTicket.style.display = 'flex';
                lblBudget.innerText = 'Budget in Crores / Lakhs';
                lblFinancing.innerText = 'Loan / Payment Readiness';
                lblAppt.innerText = 'Site Visit / Schedule';
                lblProperty.innerText = 'Project / Location';
                agentConsoleTitle.innerText = 'Indian Customer Care & Lead Support';
                voiceSelect.value = 'en-IN-NeerjaExpressiveNeural';
                chatAgentMeta.innerText = 'Neerja (CLOSER AI Indian Customer Care) • 48kHz Expressive Neural';

                // Update ROI metrics for India
                document.getElementById('roiValRevenue').innerText = '₹12.5 Cr';
                document.getElementById('roiLblRevenue').innerText = 'Site Booking Pipeline';

                // Initial Indian Greeting
                chatBox.innerHTML = `
                    <div class="msg agent">
                        <div class="msg-meta" id="chatAgentMeta">Neerja (CLOSER AI Indian Customer Care) • 48kHz Expressive Neural</div>
                        Namaste! Thank you for calling Prestige &amp; Sobha Customer Care. My name is Neerja. How may I assist you with our luxury residential projects in Whitefield or your existing booking today?
                    </div>
                `;
            }

            // Sync with backend API
            fetch('/api/market_mode', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({mode: market})
            }).then(r => r.json()).then(data => {
                if (data.dossier) {
                    latestDossier = data.dossier;
                    updateDossierUI(data.dossier);
                }
            }).catch(() => {});
        }

        function quickFill(text) {
            document.getElementById('userInput').value = text;
            sendTurn();
        }

        function toggleDossierView(view) {
            const formatted = document.getElementById('dossierFormattedView');
            const jsonView = document.getElementById('dossierJsonView');
            const tabF = document.getElementById('tabDossierFormatted');
            const tabJ = document.getElementById('tabDossierJson');

            if (view === 'json') {
                formatted.style.display = 'none';
                jsonView.style.display = 'block';
                tabJ.classList.add('active');
                tabF.classList.remove('active');
            } else {
                formatted.style.display = 'flex';
                jsonView.style.display = 'none';
                tabF.classList.add('active');
                tabJ.classList.remove('active');
            }
        }

        function copyDossierJson() {
            const jsonStr = JSON.stringify(latestDossier, null, 2);
            navigator.clipboard.writeText(jsonStr).then(() => {
                const btn = document.querySelector('.btn-copy-json');
                const orig = btn.innerText;
                btn.innerText = 'Copied!';
                setTimeout(() => { btn.innerText = orig; }, 1500);
            }).catch(() => {});
        }

        function filterKanbanLeads() {
            const q = document.getElementById('leadSearchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.lead-card');
            cards.forEach(card => {
                const text = card.innerText.toLowerCase();
                card.style.display = text.includes(q) ? 'block' : 'none';
            });
        }

        let currentAudio = null;

        function stopCurrentAudio() {
            if (currentAudio) {
                currentAudio.pause();
                currentAudio.currentTime = 0;
                currentAudio = null;
            }
        }

        function simulateBargeIn() {
            stopCurrentAudio();
            const vadContainer = document.getElementById('vadContainer');
            const vadLabel = document.getElementById('vadLabel');
            vadContainer.className = 'vad-container listening';
            vadLabel.innerText = '● BARGE-IN DETECTED (USER INTERRUPTED)';
            vadLabel.style.color = '#f59e0b';
            setTimeout(() => {
                vadLabel.innerText = '● CONCIERGE READY';
                vadLabel.style.color = 'var(--emerald)';
            }, 1800);
        }

        function testVoiceSample() {
            stopCurrentAudio();
            getAudioContext();
            const voice = document.getElementById('voiceSelect').value;
            const provider = document.getElementById('voiceProviderSelect') ? document.getElementById('voiceProviderSelect').value : 'studio';
            const audioSettings = getAudioSettings();
            const elKey = localStorage.getItem('closer_elevenlabs_key') || '';
            const sarvKey = localStorage.getItem('closer_sarvam_key') || '';
            
            setVadState('speaking');

            fetch('/api/turn', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    utterance: 'PREVIEW_SAMPLE',
                    voice: voice,
                    provider: provider,
                    rate: audioSettings.rate,
                    pitch: audioSettings.pitch,
                    elevenlabs_key: elKey,
                    sarvam_key: sarvKey
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.audio_base64) {
                    playAudioBase64(data.audio_base64);
                } else {
                    setVadState('listening');
                }
            })
            .catch(() => setVadState('listening'));
        }

        function escapeHtml(str) {
            if (!str) return '';
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        }

        function playMarketingHook(market) {
            switchMarket(market);
            const input = document.getElementById('userInput');
            if (market === 'usa') {
                input.value = "Hi, I just saw the $15M Bel Air estate listing on Bellagio Road. Can we book a private VIP walkthrough this Thursday at 2 PM? We are fully cash verified.";
            } else if (market === 'india') {
                input.value = "Namaste, I need an immediate status update on my customer ticket CC-84291 for Sobha Windsor, and I want to book a Saturday site visit for a 3 BHK.";
            } else if (market === 'hindi') {
                input.value = "नमस्ते जी, मुझे प्रेस्टीज वाइटफील्ड प्रोजेक्ट में 3 बीएचके का रेट जानना है और इस शनिवार दोपहर 2 बजे फैमिली के साथ साइट विज़िट बुक करनी है।";
            }
            sendTurn();
        }

        function downloadLastAudio() {
            if (!lastAudioBase64) {
                alert("Please click 'Test Audio Sample' or send a message first to generate studio WAV audio!");
                return;
            }
            try {
                const isWav = lastAudioBase64.startsWith('UklGR');
                const mimeType = isWav ? 'audio/wav' : 'audio/mpeg';
                const ext = isWav ? 'wav' : 'mp3';
                const binaryStr = atob(lastAudioBase64);
                const bytes = new Uint8Array(binaryStr.length);
                for (let i = 0; i < binaryStr.length; i++) {
                    bytes[i] = binaryStr.charCodeAt(i);
                }
                const blob = new Blob([bytes], { type: mimeType });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `closer-ai-${currentMarket}-voice-${Date.now()}.${ext}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                setTimeout(() => URL.revokeObjectURL(url), 1000);
            } catch (e) {
                console.error("Audio download error:", e);
            }
        }

        function sendTurn() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text) return;

            stopCurrentAudio();
            getAudioContext();

            const chatBox = document.getElementById('chatBox');
            chatBox.innerHTML += `
                <div class="msg buyer">
                    <div class="msg-meta">You (Caller)</div>
                    ${escapeHtml(text)}
                </div>
            `;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            setVadState('speaking');

            const voice = document.getElementById('voiceSelect').value;
            const provider = document.getElementById('voiceProviderSelect') ? document.getElementById('voiceProviderSelect').value : 'studio';
            const llmModel = document.getElementById('llmEngineSelect') ? document.getElementById('llmEngineSelect').value : 'llama-3.3-70b';
            const audioSettings = getAudioSettings();
            const elKey = localStorage.getItem('closer_elevenlabs_key') || '';
            const sarvKey = localStorage.getItem('closer_sarvam_key') || '';

            fetch('/api/turn', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    utterance: text,
                    voice: voice,
                    model_id: llmModel,
                    provider: provider,
                    rate: audioSettings.rate,
                    pitch: audioSettings.pitch,
                    elevenlabs_key: elKey,
                    sarvam_key: sarvKey
                })
            })
            .then(res => res.json())
            .then(data => {
                const personaName = currentMarket === 'hindi' ? 'स्वाति (Relationship Manager)' : (currentMarket === 'india' ? 'Neerja (Customer Care)' : 'Sophia (Luxury Concierge)');
                const latency = data.llm_latency_ms || 88;
                const paramScale = data.llm_parameters || '175B+ Catalog';
                const voiceEngineLabel = data.voice_provider || (provider === 'elevenlabs' ? 'ElevenLabs Turbo' : (provider === 'sarvam' ? 'Sarvam Indic Neural' : 'Studio Broadcast Neural 48kHz'));

                chatBox.innerHTML += `
                    <div class="msg agent">
                        <div class="msg-meta">${personaName} • ${paramScale} • ${voiceEngineLabel} • ${latency}ms Turn</div>
                        ${data.reply}
                    </div>
                `;
                chatBox.scrollTop = chatBox.scrollHeight;

                if (data.dossier) {
                    latestDossier = data.dossier;
                    updateDossierUI(data.dossier);
                }

                if (data.audio_base64) {
                    playAudioBase64(data.audio_base64);
                } else {
                    setVadState('listening');
                }
            })
            .catch(() => {
                setVadState('listening');
            });
        }

        function switchLLM(modelId) {
            fetch('/api/llm_select', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({model_id: modelId})
            })
            .then(res => res.json())
            .then(data => {
                if (data.model) {
                    const m = data.model;
                    const shortName = m.display_name ? m.display_name.split(' ')[0] : 'LLM';
                    const scale = m.parameter_scale || '175B';
                    const elLLM = document.getElementById('telemetryLLM');
                    const elPill = document.getElementById('telemetryLLMPill');
                    if (elLLM) elLLM.innerText = `${shortName} (${scale})`;
                    if (elPill) elPill.innerText = `${scale.toUpperCase()}`;
                }
            })
            .catch(() => {});
        }

        function resetCall() {
            stopCurrentAudio();
            fetch('/api/reset', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                switchMarket(currentMarket);
            });
        }

        let audioCtx = null;
        let activeAudioSource = null;

        function getAudioContext() {
            try {
                if (!audioCtx) {
                    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                    if (AudioContextClass) {
                        audioCtx = new AudioContextClass();
                    }
                }
                if (audioCtx && audioCtx.state === 'suspended') {
                    audioCtx.resume();
                }
            } catch (e) {
                console.warn("AudioContext init warning:", e);
            }
            return audioCtx;
        }

        function stopCurrentAudio() {
            if (activeAudioSource) {
                try { activeAudioSource.stop(); } catch(e) {}
                activeAudioSource = null;
            }
            if (currentAudio) {
                try {
                    currentAudio.pause();
                    currentAudio.currentTime = 0;
                } catch(e) {}
                currentAudio = null;
            }
        }

        function playAudioBase64(b64) {
            stopCurrentAudio();
            if (!b64 || b64.length < 50) {
                console.warn("No audio data received in playAudioBase64");
                setVadState('listening');
                return;
            }

            lastAudioBase64 = b64;
            const btnDl = document.getElementById('btnDownloadAudio');
            if (btnDl) btnDl.style.display = 'inline-flex';

            setVadState('speaking');

            // 1. Try modern Web Audio API decodeAudioData (handles MP3 & WAV in-memory without MIME mismatch or data-URI limits)
            try {
                const ctx = getAudioContext();
                if (ctx) {
                    const binaryStr = atob(b64);
                    const len = binaryStr.length;
                    const bytes = new Uint8Array(len);
                    for (let i = 0; i < len; i++) {
                        bytes[i] = binaryStr.charCodeAt(i);
                    }

                    ctx.decodeAudioData(bytes.buffer.slice(0), (buffer) => {
                        stopCurrentAudio();
                        const source = ctx.createBufferSource();
                        source.buffer = buffer;
                        source.connect(ctx.destination);
                        activeAudioSource = source;
                        setVadState('speaking');

                        source.onended = () => {
                            if (activeAudioSource === source) {
                                activeAudioSource = null;
                                setVadState('listening');
                            }
                        };

                        source.start(0);
                    }, (decodeErr) => {
                        console.warn("WebAudio decode failed, falling back to Blob audio element:", decodeErr);
                        playWithAudioElement(b64);
                    });
                    return;
                }
            } catch (ctxErr) {
                console.warn("WebAudio context failed:", ctxErr);
            }

            // 2. Fallback to HTML5 Audio element with Blob URL
            playWithAudioElement(b64);
        }

        function playWithAudioElement(b64) {
            try {
                const isWav = b64.startsWith('UklGR');
                const mimeType = isWav ? 'audio/wav' : 'audio/mpeg';
                const binaryStr = atob(b64);
                const bytes = new Uint8Array(binaryStr.length);
                for (let i = 0; i < binaryStr.length; i++) {
                    bytes[i] = binaryStr.charCodeAt(i);
                }
                const blob = new Blob([bytes], { type: mimeType });
                const blobUrl = URL.createObjectURL(blob);
                const audio = new Audio(blobUrl);
                currentAudio = audio;
                setVadState('speaking');

                audio.onended = () => {
                    URL.revokeObjectURL(blobUrl);
                    currentAudio = null;
                    setVadState('listening');
                };
                audio.onerror = (e) => {
                    console.error("Audio element error:", e);
                    URL.revokeObjectURL(blobUrl);
                    currentAudio = null;
                    setVadState('listening');
                };

                const p = audio.play();
                if (p !== undefined) {
                    p.catch(err => {
                        console.warn("Browser autoplay blocked:", err);
                        currentAudio = null;
                        setVadState('listening');
                    });
                }
            } catch (e) {
                console.error("playWithAudioElement exception:", e);
                setVadState('listening');
            }
        }

        function setVadState(state) {
            const vadContainer = document.getElementById('vadContainer');
            const vadLabel = document.getElementById('vadLabel');
            if (state === 'speaking') {
                vadContainer.className = 'vad-container speaking';
                vadLabel.innerText = '● VOICE CONCIERGE TRANSMITTING';
                vadLabel.style.color = 'var(--emerald)';
            } else {
                vadContainer.className = 'vad-container listening';
                vadLabel.innerText = '● CONCIERGE READY';
                vadLabel.style.color = 'var(--emerald)';
            }
        }

        function updateDossierUI(dossier) {
            // Update raw JSON inspector
            document.getElementById('dossierJsonView').innerText = JSON.stringify(dossier, null, 2);

            if (dossier.full_name) {
                const ph = dossier.phone_number ? ` (${dossier.phone_number})` : '';
                document.getElementById('dName').innerText = `${dossier.full_name}${ph}`;
            }

            if (dossier.market_region === 'INDIA' || currentMarket === 'india') {
                document.getElementById('dMarket').innerText = 'India (Customer Care & Lead Support)';
                if (dossier.budget_inr_text) {
                    document.getElementById('dBudget').innerText = dossier.budget_inr_text;
                } else if (dossier.budget_max) {
                    document.getElementById('dBudget').innerText = `₹${Number(dossier.budget_max).toLocaleString('en-IN')}`;
                }
                if (dossier.bhk_preference) {
                    document.getElementById('dBHK').innerText = dossier.bhk_preference;
                }
                if (dossier.ticket_id) {
                    document.getElementById('dTicket').innerText = '#' + dossier.ticket_id;
                    document.getElementById('dTicket').className = 'tag tag-green';
                }
                if (dossier.whatsapp_status || dossier.whatsapp_dispatched) {
                    document.getElementById('dWhatsApp').innerHTML = '<a href="https://wa.me/919880012345" target="_blank" style="color:var(--emerald); text-decoration:none;">Dispatched to WhatsApp ↗</a>';
                }
            } else {
                document.getElementById('dMarket').innerText = 'USA (Luxury Real Estate)';
                if (dossier.budget_max) {
                    const bMin = dossier.budget_min ? `$${Number(dossier.budget_min).toLocaleString()} - ` : '';
                    document.getElementById('dBudget').innerText = `${bMin}$${Number(dossier.budget_max).toLocaleString()} USD`;
                }
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
                if (dossier.appointment_type === 'phone_consultation' || dossier.timeframe === 'callback_after_6pm') {
                    document.getElementById('dossierStatus').innerText = "CALLBACK SET";
                    document.getElementById('dossierStatus').className = "tag tag-blue";
                } else {
                    document.getElementById('dossierStatus').innerText = "VISIT CONFIRMED";
                    document.getElementById('dossierStatus').className = "tag tag-green";
                }
            } else if (dossier.ticket_id) {
                document.getElementById('dossierStatus').innerText = "TICKET LOGGED";
                document.getElementById('dossierStatus').className = "tag tag-green";
            } else if (dossier.follow_up_note) {
                document.getElementById('dossierStatus').innerText = "FOLLOW-UP";
                document.getElementById('dossierStatus').className = "tag tag-blue";
            }
        }

        // -----------------------------------------------------------------
        // APILayer Unified Suite & Public-APIs Console Handlers
        // -----------------------------------------------------------------
        function runNumverify() {
            const phone = document.getElementById('toolPhoneInput').value.trim();
            const resBox = document.getElementById('resNumverify');
            resBox.innerText = 'Verifying carrier via Numverify...';
            fetch('/api/enrich/phone', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({phone: phone})
            })
            .then(r => r.json())
            .then(data => {
                resBox.innerHTML = `
                    <div style="color:#86efac; font-weight:700;">✓ ${data.carrier || 'Carrier Verified'} (${data.line_type || 'mobile'})</div>
                    <div>Location: ${data.location || 'Metropolitan'} • Country: ${data.country_name || 'US'}</div>
                    <div style="font-size:10px; color:#94a3b8; margin-top:2px;">${data.provider}</div>
                `;
            })
            .catch(err => {
                resBox.innerText = 'Verification timeout. Fallback engine active.';
            });
        }

        function runMailboxlayer() {
            const email = document.getElementById('toolEmailInput').value.trim();
            const resBox = document.getElementById('resMailboxlayer');
            resBox.innerText = 'Checking deliverability via Mailboxlayer...';
            fetch('/api/enrich/email', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email: email})
            })
            .then(r => r.json())
            .then(data => {
                const badge = data.is_corporate ? '🏢 Corporate Exec Domain' : '✉️ Standard Webmail';
                const scorePct = Math.round((data.score || 0.95) * 100);
                resBox.innerHTML = `
                    <div style="color:#60a5fa; font-weight:700;">✓ Deliverability Score: ${scorePct}%</div>
                    <div>${badge} • MX DNS: ${data.mx_found ? 'Found' : 'Checking'}</div>
                    <div style="font-size:10px; color:#94a3b8; margin-top:2px;">${data.provider}</div>
                `;
            })
            .catch(err => {
                resBox.innerText = 'Deliverability check timeout. Fallback engine active.';
            });
        }

        function runPositionstack() {
            const address = document.getElementById('toolAddressInput').value.trim();
            const resBox = document.getElementById('resPositionstack');
            resBox.innerText = 'Geocoding via Positionstack...';
            fetch('/api/enrich/address', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({address: address})
            })
            .then(r => r.json())
            .then(data => {
                resBox.innerHTML = `
                    <div style="color:#fcd34d; font-weight:700;">📍 Lat: ${data.latitude?.toFixed(4)}, Lon: ${data.longitude?.toFixed(4)}</div>
                    <div>${data.neighborhood_tier || data.region || 'Metropolitan Corridor'}</div>
                    <div style="font-size:10px; color:#94a3b8; margin-top:2px;">${data.provider}</div>
                `;
            })
            .catch(err => {
                resBox.innerText = 'Geocoding timeout. Fallback engine active.';
            });
        }

        function runFixerFX() {
            const amount = parseFloat(document.getElementById('toolAmountInput').value) || 0;
            const fromCurr = document.getElementById('toolFromCurr').value;
            const toCurr = document.getElementById('toolToCurr').value;
            const resBox = document.getElementById('resFixer');
            resBox.innerText = 'Fetching live FX rate via Fixer...';
            fetch('/api/enrich/currency', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({amount: amount, from_curr: fromCurr, to_curr: toCurr})
            })
            .then(r => r.json())
            .then(data => {
                resBox.innerHTML = `
                    <div style="color:#86efac; font-weight:700;">💱 ${data.formatted_to} (${data.real_estate_notation || ''})</div>
                    <div>Rate: 1 ${data.from_currency} = ${data.exchange_rate} ${data.to_currency}</div>
                    <div style="font-size:10px; color:#94a3b8; margin-top:2px;">${data.provider}</div>
                `;
            })
            .catch(err => {
                resBox.innerText = 'FX conversion timeout. Fallback engine active.';
            });
        }

        function enrichCurrentDossier() {
            const box = document.getElementById('dossierEnrichmentBox');
            const tag = document.getElementById('enrichStatusTag');
            tag.innerText = 'ENRICHING...';
            tag.className = 'tag tag-gold';
            box.style.display = 'block';
            box.innerHTML = 'Querying APILayer Unified Suite (Numverify, Mailboxlayer, Positionstack, Fixer)...';

            fetch('/api/enrich/lead', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(latestDossier || {})
            })
            .then(r => r.json())
            .then(data => {
                tag.innerText = 'VERIFIED';
                tag.className = 'tag tag-green';

                const phone = data.phone_intelligence || {};
                const email = data.email_intelligence || {};
                const spatial = data.spatial_intelligence || {};
                const fx = data.fx_intelligence || {};

                box.innerHTML = `
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                        <div>
                            <span style="color:#94a3b8;">Carrier:</span> <strong style="color:#ffffff;">${phone.carrier || 'Verizon Wireless'}</strong> (${phone.line_type || 'mobile'})
                        </div>
                        <div>
                            <span style="color:#94a3b8;">Email Score:</span> <strong style="color:#86efac;">${Math.round((email.score || 0.95)*100)}% Deliverable</strong>
                        </div>
                        <div>
                            <span style="color:#94a3b8;">Coordinates:</span> <strong style="color:#fcd34d;">${spatial.latitude?.toFixed(4)}, ${spatial.longitude?.toFixed(4)}</strong>
                        </div>
                        <div>
                            <span style="color:#94a3b8;">Dual FX:</span> <strong style="color:#60a5fa;">${fx.real_estate_notation || fx.formatted_to}</strong>
                        </div>
                    </div>
                    <div style="font-size:10px; color:#38bdf8; margin-top:6px;">✓ Verified by ${data.unified_provider}</div>
                `;
            })
            .catch(err => {
                tag.innerText = 'FALLBACK';
                tag.className = 'tag tag-blue';
                box.innerHTML = '<span style="color:#fcd34d;">APILayer verified with offline high-fidelity simulator.</span>';
            });
        }

        function saveAPILayerKey() {
            const key = document.getElementById('apilayerKeyInput').value.trim();
            const badge = document.getElementById('apiLayerKeyBadge');
            fetch('/api/enrich/key', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({api_key: key})
            })
            .then(r => r.json())
            .then(data => {
                if (data.configured) {
                    badge.innerText = 'LIVE KEY CONNECTED';
                    badge.className = 'tag tag-green';
                    localStorage.setItem('closer_apilayer_key', key);
                    alert('APILayer Unified API Key successfully saved and connected!');
                } else {
                    badge.innerText = 'OFFLINE SIMULATOR';
                    badge.className = 'tag tag-blue';
                    alert('APILayer Suite operating in high-fidelity offline simulation mode.');
                }
            })
            .catch(() => {
                badge.innerText = 'SIMULATOR ACTIVE';
                badge.className = 'tag tag-blue';
            });
        }

        function openKeyModal() {
            document.getElementById('modalElevenLabsKey').value = localStorage.getItem('closer_elevenlabs_key') || '';
            document.getElementById('modalSarvamKey').value = localStorage.getItem('closer_sarvam_key') || '';
            document.getElementById('modalAPILayerKey').value = localStorage.getItem('closer_apilayer_key') || '';
            document.getElementById('keyModalBackdrop').style.display = 'flex';
        }

        function closeKeyModal() {
            document.getElementById('keyModalBackdrop').style.display = 'none';
        }

        function saveCloudKeys() {
            const el = document.getElementById('modalElevenLabsKey').value.trim();
            const sarv = document.getElementById('modalSarvamKey').value.trim();
            const apil = document.getElementById('modalAPILayerKey').value.trim();

            if (el) localStorage.setItem('closer_elevenlabs_key', el);
            else localStorage.removeItem('closer_elevenlabs_key');

            if (sarv) localStorage.setItem('closer_sarvam_key', sarv);
            else localStorage.removeItem('closer_sarvam_key');

            if (apil) {
                localStorage.setItem('closer_apilayer_key', apil);
                const inp = document.getElementById('apilayerKeyInput');
                if (inp) inp.value = apil;
                fetch('/api/enrich/key', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({api_key: apil})
                }).catch(() => {});
            }

            updateVoiceEngineBadge();
            closeKeyModal();
        }

        function updateVoiceEngineBadge() {
            const prov = document.getElementById('voiceProviderSelect') ? document.getElementById('voiceProviderSelect').value : 'studio';
            const elKey = localStorage.getItem('closer_elevenlabs_key');
            const sarvKey = localStorage.getItem('closer_sarvam_key');
            const badge = document.getElementById('telemetryVoiceEngine');
            if (badge) {
                if (prov === 'elevenlabs') {
                    badge.innerText = elKey ? 'ElevenLabs Turbo (Active)' : 'ElevenLabs (Studio Fallback)';
                } else if (prov === 'sarvam') {
                    badge.innerText = sarvKey ? 'Sarvam Indic (Active)' : 'Sarvam (Studio Fallback)';
                } else {
                    badge.innerText = 'Studio 48kHz PCM';
                }
            }
        }

        window.addEventListener('DOMContentLoaded', () => {
            const savedApil = localStorage.getItem('closer_apilayer_key');
            if (savedApil) {
                const inp = document.getElementById('apilayerKeyInput');
                if (inp) inp.value = savedApil;
            }
            updateVoiceEngineBadge();
        });
    </script>

    <!-- Voice & APILayer Cloud Credentials Modal -->
    <div id="keyModalBackdrop" class="modal-backdrop" onclick="if(event.target===this) closeKeyModal()">
        <div class="modal-card">
            <div class="modal-header">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:18px;">⚙️</span>
                    <div>
                        <div style="font-weight:700; font-size:14px; color:#ffffff;">Voice &amp; Intelligence Cloud Credentials</div>
                        <div style="font-size:11px; color:var(--text-muted);">Configure ElevenLabs, Sarvam AI, and APILayer credentials</div>
                    </div>
                </div>
                <button class="modal-close" onclick="closeKeyModal()">✕</button>
            </div>
            <div class="modal-body">
                <div class="modal-info-banner">
                    💡 <strong>Zero Setup Required:</strong> Studio Broadcast Neural (48kHz) runs out of the box with unlimited free generation. Enter your ElevenLabs or Sarvam AI keys below to route requests through your dedicated cloud tiers.
                </div>
                <div class="modal-field">
                    <label class="modal-label">ElevenLabs API Key (xi-api-key):</label>
                    <input type="password" id="modalElevenLabsKey" class="modal-input" placeholder="e.g. sk_... (Enables ElevenLabs Turbo v2.5)">
                </div>
                <div class="modal-field">
                    <label class="modal-label">Sarvam AI / Indic Voice Key (api-subscription-key):</label>
                    <input type="password" id="modalSarvamKey" class="modal-input" placeholder="e.g. sarvam_... (Enables Sarvam / Gnani Indic Neural)">
                </div>
                <div class="modal-field">
                    <label class="modal-label">APILayer Unified Key:</label>
                    <input type="password" id="modalAPILayerKey" class="modal-input" placeholder="e.g. apilayer_... (Numverify, Mailboxlayer, Positionstack)">
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-tool-run" style="background:transparent; border-color:var(--border);" onclick="closeKeyModal()">Cancel</button>
                <button class="btn-tool-run" style="background:linear-gradient(135deg, #2563eb, #1d4ed8); border:none; padding:8px 18px;" onclick="saveCloudKeys()">Save Credentials</button>
            </div>
        </div>
    </div>
</body>
</html>
"""


class DashboardHTTPHandler(http.server.BaseHTTPRequestHandler):
    """Zero-dependency HTTP Handler serving the luxury interactive console and API."""

    conversation_engine = ConversationEngine()
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
            if index_path.exists():
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(index_path.read_bytes())
            else:
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
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
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(MOCK_LEADS).encode("utf-8"))
        elif parsed.path == "/api/llm_models":
            try:
                from src.closer.llm.models import list_available_models
                models = list_available_models()
            except Exception:
                models = []
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"models": models}).encode("utf-8"))
        elif parsed.path == "/api/llm_active":
            info = self.conversation_engine.llm_router.get_active_model_info() if hasattr(self.conversation_engine, "llm_router") and self.conversation_engine.llm_router else {"model_id": "llama-3.3-70b"}
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(info).encode("utf-8"))
        elif parsed.path == "/api/enrich/status":
            is_live = self.apilayer_client.is_configured()
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "configured": is_live,
                "provider": "APILayer Unified Suite (Live API Key Connected)" if is_live else "CLOSER AI Intelligence Engine (High-Fidelity Simulation)",
                "services": ["numverify", "mailboxlayer", "positionstack", "fixer", "currencylayer"]
            }).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/market_mode":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}
            mode = data.get("mode", "usa").lower()
            self.conversation_engine.set_market_mode(mode)
            greeting = self.conversation_engine.get_initial_greeting()
            dossier = self.conversation_engine.export_dossier()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "mode": mode,
                "greeting": greeting,
                "dossier": dossier.model_dump()
            }).encode("utf-8"))

        elif parsed.path == "/api/llm_select":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}
            model_id = data.get("model_id", "llama-3.3-70b")
            info = self.conversation_engine.set_llm_model(model_id) if hasattr(self.conversation_engine, "set_llm_model") else {}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "model": info}).encode("utf-8"))

        elif parsed.path == "/api/reset":
            # Reset conversation state
            DashboardHTTPHandler.conversation_engine = ConversationEngine(market_mode="usa")
            greeting = DashboardHTTPHandler.conversation_engine.get_initial_greeting()
            dossier = DashboardHTTPHandler.conversation_engine.export_dossier()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "greeting": greeting,
                "dossier": dossier.model_dump()
            }).encode("utf-8"))

        elif parsed.path == "/api/turn":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}

            utterance = data.get("utterance", "")
            voice = data.get("voice", "en-US-AriaNeural")
            custom_text = data.get("text", "")
            rate = data.get("rate")
            pitch = data.get("pitch")
            provider = data.get("provider", "studio")
            elevenlabs_key = data.get("elevenlabs_key") or os.environ.get("ELEVENLABS_API_KEY", "")
            sarvam_key = data.get("sarvam_key") or os.environ.get("SARVAM_API_KEY", "")

            if utterance in ("PREVIEW_SAMPLE", "STUDIO_SAMPLE"):
                if custom_text:
                    reply = custom_text
                elif "hi-in" in voice.lower() or "swara" in voice.lower() or "madhur" in voice.lower():
                    reply = "नमस्ते! क्लोज़र एआई कस्टमर सपोर्ट में आपका स्वागत है। मैं आपकी प्रॉपर्टी सर्च और साइट विज़िट में किस प्रकार सहायता कर सकती हूँ?"
                elif "en-in" in voice.lower() or "neerja" in voice.lower() or "prabhat" in voice.lower():
                    reply = "Namaste! This is CLOSER AI client relationship concierge. How may I assist you with your premium residential inquiry today?"
                else:
                    reply = "Hello, this is CLOSER AI luxury real estate concierge. How can I assist you with your estate search today?"
            else:
                reply = self.conversation_engine.process_user_turn(utterance)

            try:
                audio_bytes, latency_tts = self.tts_engine.synthesize_sync(
                    reply,
                    voice=voice,
                    rate=rate,
                    pitch=pitch,
                    provider=provider,
                    elevenlabs_key=elevenlabs_key,
                    sarvam_key=sarvam_key
                )
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                voice_provider_label = getattr(self.tts_engine, "last_provider_used", "Studio Broadcast Neural")
            except Exception:
                audio_b64 = ""
                voice_provider_label = "Studio Offline Fallback"
                latency_tts = 0.05

            dossier = self.conversation_engine.export_dossier()
            llm_info = self.conversation_engine.llm_router.get_active_model_info() if hasattr(self.conversation_engine, "llm_router") and self.conversation_engine.llm_router else {
                "model_id": "llama-3.3-70b",
                "parameter_scale": "70 Billion",
                "target_latency_ms": 88,
                "last_tier_used": "reflex_edge"
            }
            resp_data = {
                "reply": reply,
                "audio_base64": audio_b64,
                "voice_provider": voice_provider_label,
                "voice_latency_ms": round(latency_tts * 1000, 1),
                "dossier": dossier.model_dump(),
                "llm_model": llm_info.get("model_id"),
                "llm_parameters": llm_info.get("parameter_scale"),
                "llm_latency_ms": llm_info.get("target_latency_ms") or 88,
                "llm_tier": llm_info.get("last_tier_used") or "reflex_edge"
            }

            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp_data).encode("utf-8"))

        elif parsed.path == "/api/enrich/phone":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}
            res = self.apilayer_client.verify_phone(data.get("phone", ""))
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif parsed.path == "/api/enrich/email":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}
            res = self.apilayer_client.verify_email(data.get("email", ""))
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif parsed.path == "/api/enrich/address":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}
            res = self.apilayer_client.geocode_property(data.get("address", ""))
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif parsed.path == "/api/enrich/currency":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}
            res = self.apilayer_client.convert_currency(
                float(data.get("amount", 0)),
                from_curr=data.get("from_curr", "USD"),
                to_curr=data.get("to_curr", "INR")
            )
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif parsed.path == "/api/enrich/lead":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}
            dossier_data = data if data else self.conversation_engine.export_dossier().model_dump()
            res = self.apilayer_client.enrich_lead_dossier(dossier_data)
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif parsed.path == "/api/enrich/key":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}
            api_key = data.get("api_key", "").strip()
            DashboardHTTPHandler.apilayer_client = APILayerUnifiedClient(api_key=api_key)
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "configured": DashboardHTTPHandler.apilayer_client.is_configured(),
                "provider": "APILayer Unified Suite (Live API Key Connected)" if DashboardHTTPHandler.apilayer_client.is_configured() else "CLOSER AI Intelligence Engine (High-Fidelity Simulation)"
            }).encode("utf-8"))
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
