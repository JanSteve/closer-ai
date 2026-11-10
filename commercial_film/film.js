// film.js — CLOSER AI Commercial Film Assembly ("The 11:42 PM Lead")
import * as E from './engine.js';
const { W, H, PAL, clamp, lerp, seg, ss, eo, ei, eio, back, spring, font, rr, glow, panel, pill, drawWaveform, rollingNumber, lightSweep, vignette } = E;

export const DUR = 60.0;

let LINES = [];
let DURS = {};

export function setLines(lines, durs) {
  LINES = lines || [];
  DURS = durs || {};
}

export function subs() {
  return [
    { t0: 0.5, t1: 4.75, text: "At 11:42 PM, a multi-crore real estate lead arrives." },
    { t0: 5.4, t1: 9.05, text: "While traditional sales floors sleep, your commission evaporates." },
    { t0: 10.0, t1: 14.42, text: "Meet CLOSER AI. The autonomous neural closing engine." },
    { t0: 15.3, t1: 21.75, text: "Sub-250 millisecond response. Carrier-grade SIP. Zero dropped calls." },
    { t0: 22.3, t1: 29.8, text: 'Maya: "Good evening, Mr. Daniels. Regarding the Sea-Facing Penthouse, projected rental yield is 8.4%."' },
    { t0: 30.3, t1: 36.2, text: 'Pallavi: "வணக்கம் சார், சென்னை ECR வில்லாவின் RERA அப்ரூவல் மற்றும் சைட் விசிட் விவரங்கள் தயார்."' },
    { t0: 37.0, t1: 44.3, text: 'Swati: "नमस्ते सर, गोल्फ कोर्स रोड पेंटहाउस के लिए रविवार सुबह ग्यारह बजे आपकी फैमिली विज़िट बुक कर दी है।"' },
    { t0: 45.0, t1: 51.57, text: "₹1.55 per qualified call. 99.3% margin uplift." },
    { t0: 52.6, t1: 58.0, text: "CLOSER AI. Intelligence Designed To Evolve. Launching Soon." }
  ];
}

// Subtitles rendering at bottom third
function renderSubtitles(g, t) {
  const current = subs().find(s => t >= s.t0 && t <= s.t1);
  if (!current) return;

  const fadeIn = clamp((t - current.t0) / 0.25);
  const fadeOut = clamp((current.t1 - t) / 0.25);
  const alpha = Math.min(fadeIn, fadeOut);
  if (alpha <= 0) return;

  g.save();
  g.globalAlpha = alpha;
  g.font = font(26, 500, 'ui');
  const tw = g.measureText(current.text).width;
  const pw = tw + 48, ph = 52;
  const px = W / 2 - pw / 2, py = H - 90;

  // Translucent backdrop pill
  g.fillStyle = 'rgba(5, 7, 12, 0.82)';
  rr(g, px, py, pw, ph, ph / 2);
  g.fill();
  g.lineWidth = 1;
  g.strokeStyle = 'rgba(255, 255, 255, 0.12)';
  g.stroke();

  g.fillStyle = '#FFFFFF';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText(current.text, W / 2, py + ph / 2);
  g.restore();
}

// SHOT 1: The Midnight Crisis (0s – 5.0s)
function renderShot1(g, t) {
  const zoom = lerp(0.98, 1.02, t / 5.0);
  E.bg(g, { lift: 0.9, cyanGlow: 0 });
  E.grid(g, { ox: W / 2, oy: H / 2, scale: zoom, alpha: 0.7 });

  g.save();
  g.translate(W / 2, H / 2);
  g.scale(zoom, zoom);
  g.translate(-W / 2, -H / 2);

  const cardW = 820, cardH = 460;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;
  panel(g, cx, cy, cardW, cardH, { r: 24, fill: PAL.surf, stroke: 'rgba(239, 68, 68, 0.35)', shadow: 1.2 });
  glow(g, W / 2, cy + 60, 420, PAL.red, 0.15 + 0.05 * Math.sin(t * 8));

  // Red Crisis Badge
  const blink = (Math.floor(t * 3) % 2 === 0);
  pill(g, cx + 40, cy + 50, blink ? "● INBOUND LEAD DETECTED — 11:42 PM" : "○ INBOUND LEAD DETECTED — 11:42 PM", {
    color: PAL.red, bg: 'rgba(239, 68, 68, 0.12)', px: 13
  });

  // Property Details
  g.font = font(42, 600, 'disp');
  g.fillStyle = PAL.text;
  g.textAlign = 'left';
  g.fillText("₹2.85 Cr ($1.85M) Sea-Facing Penthouse", cx + 40, cy + 130);

  g.font = font(18, 400, 'ui');
  g.fillStyle = PAL.dim;
  g.fillText("Prospect: Rajiv K. · NRI Investment Desk · High Intent Inquiry", cx + 40, cy + 168);

  // Divider
  g.strokeStyle = PAL.line;
  g.lineWidth = 1;
  g.beginPath();
  g.moveTo(cx + 40, cy + 200);
  g.lineTo(cx + cardW - 40, cy + 200);
  g.stroke();

  // Status Rows
  const rows = [
    { label: "HUMAN SALES FLOOR STATUS", val: "OFFLINE / SLEEPING", color: PAL.red },
    { label: "TIME UNTIL HUMAN SHIFT", val: "08h 17m 42s DEAD AIR", color: '#F59E0B' },
    { label: "HIGH-TICKET BUYER CONVERSION", val: "BLEEDING VALUE (-391% / 5 min)", color: PAL.red }
  ];

  rows.forEach((r, i) => {
    const ry = cy + 245 + i * 55;
    g.font = font(14, 600, 'mono');
    g.fillStyle = PAL.mute;
    g.fillText(r.label, cx + 40, ry);

    g.font = font(17, 600, 'mono');
    g.fillStyle = r.color;
    g.textAlign = 'right';
    g.fillText(r.val, cx + cardW - 40, ry);
    g.textAlign = 'left';
  });

  g.restore();
}

// SHOT 2: Commission Evaporation (5.0s – 9.5s)
function renderShot2(g, t) {
  const localT = t - 5.0;
  const shake = Math.sin(localT * 30) * Math.min(6, localT * 1.5);
  E.bg(g, { lift: 0.8, cyanGlow: 0 });
  E.grid(g, { ox: W / 2 + shake, oy: H / 2, alpha: 0.5 });

  g.save();
  g.translate(shake, 0);
  const cardW = 920, cardH = 340;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;
  panel(g, cx, cy, cardW, cardH, { r: 24, fill: '#14080A', stroke: 'rgba(239, 68, 68, 0.5)', shadow: 1.4 });

  glow(g, W / 2, H / 2, 500, PAL.red, 0.22);

  g.font = font(16, 600, 'mono');
  g.fillStyle = PAL.red;
  g.textAlign = 'center';
  g.fillText("⚠️ TRADITIONAL SALES INFRASTRUCTURE FAILURE", W / 2, cy + 65);

  g.font = font(48, 600, 'disp');
  g.fillStyle = '#FFFFFF';
  g.fillText("While They Sleep, Your Commission Evaporates.", W / 2, cy + 140);

  // Big warning stat
  const lossPercent = Math.min(87, Math.floor(40 + localT * 11));
  g.font = font(64, 700, 'disp');
  g.fillStyle = PAL.red;
  g.fillText(`${lossPercent}% OF NOCTURNAL LEADS DIE`, W / 2, cy + 240);

  g.font = font(16, 400, 'ui');
  g.fillStyle = PAL.dim;
  g.fillText("Average luxury developer loses ₹1.2 Crore per month to delayed callback times.", W / 2, cy + 285);

  g.restore();
}

// SHOT 3: Autonomous Awakening & Keynote Shift (9.5s – 15.0s)
function renderShot3(g, t) {
  const localT = t - 9.5;
  const sweep = clamp(localT / 1.4);
  E.bg(g, { lift: 1.1, cyanGlow: 2.2 });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.8 });

  glow(g, W / 2, H / 2 - 40, 600, PAL.accent, 0.28);

  const cardW = 960, cardH = 460;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;

  panel(g, cx, cy, cardW, cardH, { r: 24, fill: PAL.surf, stroke: PAL.accent, shadow: 1.5 });
  lightSweep(g, cx, cy, cardW, cardH, sweep, 'rgba(0, 229, 255, 0.35)');

  // Cyan Badge
  pill(g, cx + 45, cy + 45, "● CLOSER AI AUTONOMOUS SIP ENGINE — ACTIVE", {
    color: PAL.accent, bg: 'rgba(0, 229, 255, 0.12)', px: 13
  });

  g.font = font(44, 600, 'disp');
  g.fillStyle = PAL.text;
  g.textAlign = 'left';
  g.fillText("Outbound Dial Triggered in < 0.08s", cx + 45, cy + 125);

  g.font = font(18, 400, 'ui');
  g.fillStyle = PAL.dim;
  g.fillText("Prospect is ringing. Zero human intervention required.", cx + 45, cy + 165);

  // Live connecting waveform
  drawWaveform(g, W / 2, cy + 260, 800, 75, t, { active: true, color: PAL.accent });

  // Telecom Tags
  const tags = ["CARRIER SIP 200 OK", "CALL-ID: CLS-9842", "CODEC: OPUS-HD 48kHz", "DIAL TIME: 0.078s"];
  tags.forEach((tg, i) => {
    pill(g, cx + 45 + i * 220, cy + 380, tg, { color: PAL.lime, bg: PAL.surf2, px: 11 });
  });
}

// SHOT 4: High-Precision Latency HUD (15.0s – 22.0s)
function renderShot4(g, t) {
  const localT = t - 15.0;
  E.bg(g, { lift: 1.0, cyanGlow: 1.8 });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.75 });

  const cardW = 1040, cardH = 480;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;
  panel(g, cx, cy, cardW, cardH, { r: 24, fill: PAL.surf, stroke: PAL.line, shadow: 1.3 });

  // Big Latency Number on Left
  g.font = font(18, 600, 'mono');
  g.fillStyle = PAL.dim;
  g.textAlign = 'left';
  g.fillText("GLASS-TO-GLASS TURN LATENCY", cx + 60, cy + 70);

  const latProg = clamp(localT / 0.8);
  const latencyStr = rollingNumber("<238ms", latProg, 101);
  g.font = font(92, 700, 'disp');
  g.fillStyle = PAL.accent;
  g.fillText(latencyStr, cx + 60, cy + 170);

  g.font = font(16, 400, 'ui');
  g.fillStyle = PAL.mute;
  g.fillText("Human conversational rhythm: 250ms–300ms", cx + 60, cy + 215);

  // Right Side Specs Card
  const rx = cx + 520, ry = cy + 50, rw = 460, rh = 380;
  panel(g, rx, ry, rw, rh, { r: 18, fill: PAL.surf2, stroke: 'rgba(255,255,255,0.06)', shadow: 0.5 });

  const specs = [
    { title: "TURN-TAKING", desc: "Adaptive Neural VAD (Zero overlapping)" },
    { title: "KNOWLEDGE GRAPH", desc: "Real estate inventory & dynamic pricing" },
    { title: "GUARDRAIL ARCHITECTURE", desc: "NeMo & DeepEval 100% compliance" },
    { title: "CRM AUTO-SYNC", desc: "Salesforce / HubSpot / LeadSquared" }
  ];

  specs.forEach((s, idx) => {
    const sy = ry + 40 + idx * 80;
    g.font = font(13, 600, 'mono');
    g.fillStyle = PAL.lime;
    g.fillText(`● ${s.title}`, rx + 30, sy);

    g.font = font(16, 500, 'ui');
    g.fillStyle = PAL.text;
    g.fillText(s.desc, rx + 30, sy + 25);
  });

  // Waveform along the bottom left
  drawWaveform(g, cx + 270, cy + 340, 420, 60, t, { active: true, color: PAL.accent });
}

// SHOT 5: Maya — English NRI Closer (22.0s – 30.0s)
function renderShot5(g, t) {
  E.bg(g, { lift: 1.0, cyanGlow: 1.5 });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.7 });

  const cardW = 1100, cardH = 500;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;
  panel(g, cx, cy, cardW, cardH, { r: 24, fill: PAL.surf, stroke: PAL.accent, shadow: 1.4 });

  // Avatar + Header
  glow(g, cx + 110, cy + 110, 90, PAL.accent, 0.35);
  panel(g, cx + 60, cy + 60, 100, 100, { r: 50, fill: PAL.surf2, stroke: PAL.accent });
  g.font = font(42, 600, 'disp');
  g.fillStyle = PAL.accent;
  g.textAlign = 'center';
  g.fillText("M", cx + 110, cy + 125);

  g.textAlign = 'left';
  g.font = font(14, 600, 'mono');
  g.fillStyle = PAL.lime;
  g.fillText("NEURAL CLOSER 01 · DUAL-MARKET NRI DESK", cx + 190, cy + 90);

  g.font = font(36, 600, 'disp');
  g.fillStyle = PAL.text;
  g.fillText("Maya (English Closer)", cx + 190, cy + 135);

  pill(g, cx + cardW - 220, cy + 85, "GLOBAL NRI SPECIALIST", { color: PAL.accent, bg: PAL.surf2, px: 11 });

  // Divider
  g.strokeStyle = PAL.line;
  g.lineWidth = 1;
  g.beginPath();
  g.moveTo(cx + 60, cy + 190);
  g.lineTo(cx + cardW - 60, cy + 190);
  g.stroke();

  // Speech Transcript Box
  panel(g, cx + 60, cy + 220, cardW - 120, 140, { r: 16, fill: PAL.surf2, stroke: 'rgba(0, 229, 255, 0.2)' });
  g.font = font(12, 600, 'mono');
  g.fillStyle = PAL.accent;
  g.fillText("LIVE CALL TRANSCRIPTION", cx + 90, cy + 255);

  g.font = font(22, 500, 'ui');
  g.fillStyle = '#FFFFFF';
  g.fillText('"Good evening, Mr. Daniels. Regarding the Sea-Facing Penthouse,', cx + 90, cy + 295);
  g.fillText('the projected rental yield is 8.4% with full capital gains repatriation."', cx + 90, cy + 330);

  // Live waveform
  drawWaveform(g, W / 2, cy + 420, cardW - 160, 50, t, { active: true, color: PAL.accent });
}

// SHOT 6: Pallavi — Tamil Luxury Estate Closer (30.0s – 36.5s)
function renderShot6(g, t) {
  E.bg(g, { lift: 1.0, cyanGlow: 1.5 });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.7 });

  const cardW = 1100, cardH = 500;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;
  panel(g, cx, cy, cardW, cardH, { r: 24, fill: PAL.surf, stroke: PAL.emerald, shadow: 1.4 });

  // Avatar + Header
  glow(g, cx + 110, cy + 110, 90, PAL.emerald, 0.35);
  panel(g, cx + 60, cy + 60, 100, 100, { r: 50, fill: PAL.surf2, stroke: PAL.emerald });
  g.font = font(42, 600, 'disp');
  g.fillStyle = PAL.emerald;
  g.textAlign = 'center';
  g.fillText("P", cx + 110, cy + 125);

  g.textAlign = 'left';
  g.font = font(14, 600, 'mono');
  g.fillStyle = PAL.lime;
  g.fillText("NEURAL CLOSER 02 · TAMIL NADU & SOUTH INDIA DESK", cx + 190, cy + 90);

  g.font = font(36, 600, 'disp');
  g.fillStyle = PAL.text;
  g.fillText("Pallavi (Tamil Closer)", cx + 190, cy + 135);

  pill(g, cx + cardW - 220, cy + 85, "CHENNAI & ECR EXPERT", { color: PAL.emerald, bg: PAL.surf2, px: 11 });

  // Divider
  g.strokeStyle = PAL.line;
  g.lineWidth = 1;
  g.beginPath();
  g.moveTo(cx + 60, cy + 190);
  g.lineTo(cx + cardW - 60, cy + 190);
  g.stroke();

  // Speech Transcript Box
  panel(g, cx + 60, cy + 220, cardW - 120, 140, { r: 16, fill: PAL.surf2, stroke: 'rgba(16, 185, 129, 0.2)' });
  g.font = font(12, 600, 'mono');
  g.fillStyle = PAL.emerald;
  g.fillText("நேரடி அழைப்பு பதிவு (LIVE CALL TRANSCRIPTION)", cx + 90, cy + 255);

  g.font = font(22, 500, 'ui');
  g.fillStyle = '#FFFFFF';
  g.fillText('"வணக்கம் சார், சென்னை ECR வில்லாவின் RERA அப்ரூவல் மற்றும்', cx + 90, cy + 295);
  g.fillText('சைட் விசிட் விவரங்கள் தயார். இந்த வார இறுதியில் பதிவு செய்யலாமா?"', cx + 90, cy + 330);

  // Live waveform
  drawWaveform(g, W / 2, cy + 420, cardW - 160, 50, t, { active: true, color: PAL.emerald });
}

// SHOT 7: Swati — Hindi HNW Closer (36.5s – 44.5s)
function renderShot7(g, t) {
  E.bg(g, { lift: 1.0, cyanGlow: 1.5 });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.7 });

  const cardW = 1100, cardH = 500;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;
  panel(g, cx, cy, cardW, cardH, { r: 24, fill: PAL.surf, stroke: PAL.purple, shadow: 1.4 });

  // Avatar + Header
  glow(g, cx + 110, cy + 110, 90, PAL.purple, 0.35);
  panel(g, cx + 60, cy + 60, 100, 100, { r: 50, fill: PAL.surf2, stroke: PAL.purple });
  g.font = font(42, 600, 'disp');
  g.fillStyle = PAL.purple;
  g.textAlign = 'center';
  g.fillText("S", cx + 110, cy + 125);

  g.textAlign = 'left';
  g.font = font(14, 600, 'mono');
  g.fillStyle = PAL.lime;
  g.fillText("NEURAL CLOSER 03 · DELHI NCR & NORTH INDIA DESK", cx + 190, cy + 90);

  g.font = font(36, 600, 'disp');
  g.fillStyle = PAL.text;
  g.fillText("Swati (Hindi Closer)", cx + 190, cy + 135);

  pill(g, cx + cardW - 220, cy + 85, "GURUGRAM & NCR LUXURY", { color: PAL.purple, bg: PAL.surf2, px: 11 });

  // Divider
  g.strokeStyle = PAL.line;
  g.lineWidth = 1;
  g.beginPath();
  g.moveTo(cx + 60, cy + 190);
  g.lineTo(cx + cardW - 60, cy + 190);
  g.stroke();

  // Speech Transcript Box
  panel(g, cx + 60, cy + 220, cardW - 120, 140, { r: 16, fill: PAL.surf2, stroke: 'rgba(168, 85, 247, 0.2)' });
  g.font = font(12, 600, 'mono');
  g.fillStyle = PAL.purple;
  g.fillText("लाइव कॉल ट्रांसक्रिप्शन (LIVE CALL TRANSCRIPTION)", cx + 90, cy + 255);

  g.font = font(22, 500, 'ui');
  g.fillStyle = '#FFFFFF';
  g.fillText('"नमस्ते सर, गोल्फ कोर्स रोड पेंटहाउस के लिए', cx + 90, cy + 295);
  g.fillText('रविवार सुबह ग्यारह बजे आपकी फैमिली विज़िट लॉक कर दी है।"', cx + 90, cy + 330);

  // Live waveform
  drawWaveform(g, W / 2, cy + 420, cardW - 160, 50, t, { active: true, color: PAL.purple });
}

// SHOT 8: The Giant Number & Inevitable ROI (44.5s – 52.0s)
function renderShot8(g, t) {
  const localT = t - 44.5;
  E.bg(g, { lift: 1.2, cyanGlow: 2.5 });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.85 });

  glow(g, W / 2, H / 2 - 80, 700, PAL.lime, 0.25);

  const prog = clamp(localT / 1.0);
  const numStr = rollingNumber("₹1.55", prog, 77);

  g.textAlign = 'center';
  g.font = font(18, 600, 'mono');
  g.fillStyle = PAL.dim;
  g.fillText("UNIT ECONOMICS PER QUALIFIED DIALED LEAD", W / 2, H / 2 - 160);

  // Monumental Big Number
  g.font = font(170, 700, 'disp');
  g.fillStyle = PAL.lime;
  g.fillText(numStr, W / 2, H / 2 + 10);

  // Contrast Comparison Cards
  const cardW = 900, cardH = 110;
  const cx = W / 2 - cardW / 2, cy = H / 2 + 70;
  panel(g, cx, cy, cardW, cardH, { r: 20, fill: PAL.surf, stroke: PAL.line });

  g.font = font(16, 600, 'mono');
  g.fillStyle = PAL.red;
  g.fillText("HUMAN TELECALLER: ₹220 ($2.60)", cx + 220, cy + 62);

  g.fillStyle = PAL.mute;
  g.fillText("vs", cx + 450, cy + 62);

  g.font = font(20, 700, 'mono');
  g.fillStyle = PAL.lime;
  g.fillText("CLOSER AI: ₹1.55 (-99.3% COST)", cx + 670, cy + 62);

  // Bottom statement
  g.font = font(18, 500, 'ui');
  g.fillStyle = PAL.text;
  g.fillText("Zero dropped calls. Zero sleep. 100% CRM verification.", W / 2, H / 2 + 230);
}

// SHOT 9: Hero Climax & Call to Action (52.0s – 60.0s)
function renderShot9(g, t) {
  const localT = t - 52.0;
  const sweep = clamp(localT / 2.0);
  E.bg(g, { lift: 1.3, cyanGlow: 3.0 });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.9 });

  glow(g, W / 2, H / 2 - 100, 800, PAL.accent, 0.32);

  g.save();
  g.textAlign = 'center';

  // Hero Logo Icon Mark
  const logoY = H / 2 - 140;
  panel(g, W / 2 - 50, logoY - 50, 100, 100, { r: 24, fill: PAL.surf2, stroke: PAL.accent, shadow: 1.2 });
  g.font = font(48, 700, 'disp');
  g.fillStyle = PAL.accent;
  g.fillText("C", W / 2, logoY + 16);

  // Hero Title
  g.font = font(88, 700, 'disp');
  g.fillStyle = '#FFFFFF';
  g.fillText("CLOSER AI", W / 2, logoY + 120);

  lightSweep(g, W / 2 - 400, logoY + 30, 800, 120, sweep, 'rgba(0, 229, 255, 0.4)');

  // Tagline
  g.font = font(24, 600, 'mono');
  g.fillStyle = PAL.accent;
  g.fillText("INTELLIGENCE DESIGNED TO EVOLVE", W / 2, logoY + 175);

  // Launching Soon Pill
  const pillW = 680, pillH = 64;
  const px = W / 2 - pillW / 2, py = logoY + 225;
  panel(g, px, py, pillW, pillH, { r: pillH / 2, fill: 'rgba(0, 229, 255, 0.08)', stroke: PAL.accent });

  g.font = font(20, 700, 'mono');
  g.fillStyle = PAL.lime;
  g.fillText("● LAUNCHING SOON · DUAL-MARKET CAPACITY", W / 2, py + 38);

  g.font = font(15, 400, 'ui');
  g.fillStyle = PAL.dim;
  g.fillText("Enterprise Real Estate Deployments Now Open · USA & India", W / 2, py + 95);

  g.restore();
}

// Master Render Function called frame-by-frame by video.mjs
export function renderFilm(g, t, o = {}) {
  const { nosub = false } = o;

  // Global fade out to black at the very end
  let alpha = 1.0;
  if (t > 58.5) {
    alpha = clamp((DUR - t) / 1.5);
  }

  g.save();
  g.globalAlpha = alpha;

  if (t < 5.0) {
    renderShot1(g, t);
  } else if (t < 9.5) {
    renderShot2(g, t);
  } else if (t < 15.0) {
    renderShot3(g, t);
  } else if (t < 22.0) {
    renderShot4(g, t);
  } else if (t < 30.0) {
    renderShot5(g, t);
  } else if (t < 36.5) {
    renderShot6(g, t);
  } else if (t < 44.5) {
    renderShot7(g, t);
  } else if (t < 52.0) {
    renderShot8(g, t);
  } else {
    renderShot9(g, t);
  }

  // Vignette overlay
  vignette(g, 0.5);

  // Subtitles
  if (!nosub) {
    renderSubtitles(g, t);
  }

  g.restore();
}
