"""
Web Console for CLOSER AI: Live Call Simulator, Lead Pipeline Kanban, Audio Playback, and ROI Calculator.
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
    <title>CLOSER AI — Autonomous Voice Lead Engine</title>
    <style>
        :root {
            --bg: #090d16;
            --surface: #111827;
            --surface-hover: #1f2937;
            --border: #374151;
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.35);
            --gold: #f59e0b;
            --emerald: #10b981;
            --text-main: #f9fafb;
            --text-dim: #9ca3af;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
        body { background: var(--bg); color: var(--text-main); min-height: 100vh; padding: 24px; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 20px; margin-bottom: 24px; }
        .badge { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid #3b82f6; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        .logo-title { font-size: 26px; font-weight: 800; letter-spacing: -0.5px; display: flex; align-items: center; gap: 10px; }
        .subtitle { font-size: 14px; color: var(--text-dim); margin-top: 4px; }
        .grid-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
        @media(max-width: 900px) { .grid-layout { grid-template-columns: 1fr; } }
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
        .card-title { font-size: 17px; font-weight: 700; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 10px; }
        
        /* Chat Simulator */
        .chat-box { height: 320px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; padding: 12px; background: #0c111d; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); }
        .msg { padding: 10px 14px; border-radius: 8px; max-width: 85%; font-size: 14px; line-height: 1.45; }
        .msg.agent { background: #1e3a8a; color: #dbeafe; align-self: flex-start; border-left: 3px solid #60a5fa; }
        .msg.buyer { background: #374151; color: #f3f4f6; align-self: flex-end; border-right: 3px solid var(--emerald); }
        .msg-meta { font-size: 11px; opacity: 0.7; margin-bottom: 4px; font-weight: 600; }
        .input-row { display: flex; gap: 10px; margin-top: 14px; }
        .input-row input { flex: 1; padding: 12px 14px; background: #0c111d; border: 1px solid var(--border); border-radius: 8px; color: white; font-size: 14px; }
        .btn { padding: 10px 18px; background: var(--primary); color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.2s; }
        .btn:hover { background: #2563eb; }
        .btn-gold { background: var(--gold); color: #000; }
        .btn-gold:hover { background: #d97706; }

        /* Kanban Columns */
        .kanban { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
        @media(max-width: 768px) { .kanban { grid-template-columns: 1fr; } }
        .kanban-col { background: #0c111d; border-radius: 8px; padding: 12px; border: 1px solid rgba(255,255,255,0.05); }
        .kanban-header { font-size: 12px; text-transform: uppercase; font-weight: 700; color: var(--text-dim); margin-bottom: 12px; display: flex; justify-content: space-between; }
        .lead-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin-bottom: 10px; transition: transform 0.15s; }
        .lead-card:hover { transform: translateY(-2px); border-color: #4b5563; }
        .lead-name { font-weight: 700; font-size: 14px; margin-bottom: 4px; }
        .lead-prop { font-size: 12px; color: var(--text-dim); margin-bottom: 8px; }
        .tag { font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 700; }
        .tag-green { background: rgba(16, 185, 129, 0.2); color: var(--emerald); }
        .tag-gold { background: rgba(245, 158, 11, 0.2); color: var(--gold); }
        .tag-blue { background: rgba(59, 130, 246, 0.2); color: #93c5fd; }

        /* ROI Calculator */
        .roi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 14px; }
        @media(max-width: 768px) { .roi-grid { grid-template-columns: 1fr 1fr; } }
        .stat-box { background: #0c111d; border: 1px solid var(--border); border-radius: 8px; padding: 14px; text-align: center; }
        .stat-val { font-size: 24px; font-weight: 800; color: var(--emerald); margin-top: 4px; }
        .stat-label { font-size: 12px; color: var(--text-dim); }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="logo-title">
                <span>CLOSER AI</span>
                <span class="badge">Speed-to-Lead: &lt;500ms</span>
            </div>
            <div class="subtitle">Autonomous Voice-Native Real Estate Lead Qualification Engine | Founder: R Jan Steve Daniel</div>
        </div>
        <div>
            <a href="https://github.com/JanSteve/closer-ai" target="_blank" style="color:#60a5fa; text-decoration:none; font-size:14px; font-weight:600;">GitHub: JanSteve/closer-ai ↗</a>
        </div>
    </div>

    <div class="grid-layout">
        <!-- Live Voice/Chat Simulator -->
        <div class="card">
            <div class="card-title">
                <span>Live Voice Call Simulator (Sophia ISA)</span>
                <span class="badge" style="background:rgba(16,185,129,0.15); color:var(--emerald); border-color:var(--emerald)">CALL ACTIVE</span>
            </div>
            <div class="chat-box" id="chatBox">
                <div class="msg agent">
                    <div class="msg-meta">Sophia (Daniel & Associates ISA) • Voice Synthesized (24kHz)</div>
                    Hi David, this is Sophia with Daniel &amp; Associates Luxury Realty. I noticed you just requested details on 10484 Bellagio Rd, Bel Air — I wanted to catch you while it's top of mind. Are you looking at this as a primary residence or a private investment?
                </div>
            </div>
            <div class="input-row">
                <input type="text" id="userInput" placeholder="Type buyer reply (e.g. 'I'm browsing, budget is $4M cash')..." onkeydown="if(event.key==='Enter') sendTurn()">
                <button class="btn" onclick="sendTurn()">Speak / Send</button>
            </div>
            <div style="margin-top:10px; font-size:12px; color:var(--text-dim);">
                💡 Quick test buyer phrases: 
                <a href="#" onclick="quickFill('I am just browsing online right now.'); return false;" style="color:#60a5fa">"Just browsing"</a> |
                <a href="#" onclick="quickFill('My budget is around $4 million cash and looking to move next month.'); return false;" style="color:#60a5fa">"$4M Cash / 30 Days"</a> |
                <a href="#" onclick="quickFill('Can we tour Thursday at 2 PM?'); return false;" style="color:#60a5fa">"Tour Thursday at 2 PM"</a>
            </div>
        </div>

        <!-- Live Buyer Dossier Extracted -->
        <div class="card">
            <div class="card-title">
                <span>Live Pydantic Buyer Dossier</span>
                <span id="dossierStatus" class="tag tag-gold">QUALIFYING</span>
            </div>
            <div style="display:flex; flex-direction:column; gap:10px; font-size:13px;">
                <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px;">
                    <span style="color:var(--text-dim)">Client Name:</span>
                    <strong id="dName">David Vance</strong>
                </div>
                <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px;">
                    <span style="color:var(--text-dim)">Budget Range:</span>
                    <strong id="dBudget">$4,000,000 - $5,000,000 USD</strong>
                </div>
                <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px;">
                    <span style="color:var(--text-dim)">Financing Status:</span>
                    <span id="dFinancing" class="tag tag-green">All-Cash Verified</span>
                </div>
                <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px;">
                    <span style="color:var(--text-dim)">Timeframe:</span>
                    <strong id="dTime">1-3 months (High Urgency)</strong>
                </div>
                <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px;">
                    <span style="color:var(--text-dim)">Intent Score:</span>
                    <strong id="dIntent" style="color:var(--emerald)">95 / 100</strong>
                </div>
                <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px;">
                    <span style="color:var(--text-dim)">Google Calendar Tour:</span>
                    <strong id="dAppt" style="color:#60a5fa">Thursday at 2:00 PM PST</strong>
                </div>
                <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px;">
                    <span style="color:var(--text-dim)">Principal Broker:</span>
                    <strong>R Jan Steve Daniel</strong>
                </div>
            </div>
            <div style="margin-top:16px;">
                <audio id="audioPlayer" controls style="width:100%; height:36px; border-radius:6px; outline:none; display:none;"></audio>
            </div>
        </div>
    </div>

    <!-- Lead Pipeline Kanban -->
    <div class="card" style="margin-bottom:24px;">
        <div class="card-title">
            <span>Luxury Lead Pipeline (Follow Up Boss CRM Sync)</span>
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

    <!-- Real Estate Speed-to-Lead ROI Calculator -->
    <div class="card">
        <div class="card-title">
            <span>Brokerage Speed-to-Lead ROI Calculator</span>
            <span class="badge" style="background:rgba(245,158,11,0.15); color:var(--gold); border-color:var(--gold)">Gross Commission Model</span>
        </div>
        <p style="font-size:13px; color:var(--text-dim); margin-bottom:14px;">
            Calling luxury buyer leads within 500ms yields a <strong>391% increase</strong> in tour conversions compared to standard agent response times (47 minutes).
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
        function quickFill(val) {
            document.getElementById('userInput').value = val;
            sendTurn();
        }

        async function sendTurn() {
            const input = document.getElementById('userInput');
            const val = input.value.trim();
            if (!val) return;
            input.value = '';

            const chat = document.getElementById('chatBox');
            chat.innerHTML += `
                <div class="msg buyer">
                    <div class="msg-meta">Buyer (You)</div>
                    ${val}
                </div>
            `;
            chat.scrollTop = chat.scrollHeight;

            try {
                const res = await fetch('/api/turn', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({utterance: val})
                });
                const data = await res.json();
                
                chat.innerHTML += `
                    <div class="msg agent">
                        <div class="msg-meta">Sophia (Daniel & Associates ISA) • Voice Synthesized</div>
                        ${data.reply}
                    </div>
                `;
                chat.scrollTop = chat.scrollHeight;

                if (data.dossier) {
                    if (data.dossier.budget_max) {
                        document.getElementById('dBudget').innerText = `$${Number(data.dossier.budget_max).toLocaleString()} USD`;
                    }
                    if (data.dossier.financing_type) {
                        document.getElementById('dFinancing').innerText = data.dossier.financing_type.toUpperCase();
                    }
                    if (data.dossier.timeframe) {
                        document.getElementById('dTime').innerText = data.dossier.timeframe;
                    }
                    if (data.dossier.intent_score) {
                        document.getElementById('dIntent').innerText = `${data.dossier.intent_score} / 100`;
                    }
                    if (data.dossier.appointment_datetime) {
                        document.getElementById('dAppt').innerText = data.dossier.appointment_datetime;
                        document.getElementById('dossierStatus').innerText = "TOUR BOOKED";
                        document.getElementById('dossierStatus').className = "tag tag-green";
                    }
                }

                if (data.audio_base64) {
                    const audio = document.getElementById('audioPlayer');
                    audio.src = "data:audio/wav;base64," + data.audio_base64;
                    audio.style.display = "block";
                    audio.play().catch(e => console.log('Audio autoplay prevented'));
                }
            } catch (err) {
                console.error('Turn error:', err);
            }
        }
    </script>
</body>
</html>
"""


class DashboardHTTPHandler(http.server.BaseHTTPRequestHandler):
    """Zero-dependency HTTP Handler serving the interactive console and API."""

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
        if parsed.path == "/api/turn":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}
            utterance = data.get("utterance", "")

            reply = self.conversation_engine.process_user_turn(utterance)
            audio_bytes, _ = self.tts_engine.synthesize_sync(reply)
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


def run_web_console(port: int = 8501) -> None:
    """Runs the standalone interactive web console."""
    server_address = ("0.0.0.0", port)
    with socketserver.TCPServer(server_address, DashboardHTTPHandler) as httpd:
        print(f"\n[+] CLOSER AI Web Console running at http://localhost:{port}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down web console.")


# If executed directly with Python or via Streamlit
if __name__ == "__main__":
    # Check if run with Streamlit
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
