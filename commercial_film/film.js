// film.js — CLOSER AI Award-Winning Cinematic Film ("The 11:42 PM Lead")
// Benchmarked against Apple Keynote, Linear, and Teenage Engineering launch trailers.
import * as E from './engine.js';
const { W, H, PAL, clamp, lerp, seg, ss, eo, ei, eio, back, spring, font, rr, glow, panel3D, pill, drawWaveform, drawRadialDial, rollingNumber, lightSweep, vignette, particles, TAU, rgba } = E;

export const DUR = 60.0;

let LINES = [];
let DURS = {};

export function setLines(lines, durs) {
  LINES = lines || [];
  DURS = durs || {};
}

// Synchronized subtitles for Kokoro female English voiceover
export function subs() {
  return [
    { t0: 0.5, t1: 5.0, text: "At 11:42 PM, a multi-crore real estate lead arrives." },
    { t0: 5.4, t1: 9.0, text: "While traditional sales floors sleep, your commission evaporates." },
    { t0: 9.8, t1: 13.5, text: "Meet CLOSER AI. The autonomous neural closing engine." },
    { t0: 14.0, t1: 20.2, text: "Sub-250 millisecond response. Carrier-grade SIP. Zero dropped calls." },
    { t0: 20.8, t1: 28.2, text: 'Maya: "Good evening, Mr. Daniels. Regarding the Sea-Facing Penthouse, projected rental yield is 8.4%."' },
    { t0: 28.8, t1: 34.8, text: 'Pallavi: "வணக்கம் சார், சென்னை ECR வில்லாவின் RERA அப்ரூவல் மற்றும் சைட் விசிட் விவரங்கள் தயார்."' },
    { t0: 35.4, t1: 42.8, text: 'Swati: "नमस्ते सर, गोल्फ कोर्स रोड पेंटहाउस के लिए रविवार सुबह ग्यारह बजे आपकी फैमिली विज़िट बुक कर दी है।"' },
    { t0: 43.5, t1: 49.8, text: "₹1.55 per qualified call. 99.3% margin uplift." },
    { t0: 50.5, t1: 55.0, text: "CLOSER AI. Intelligence Designed To Evolve. Launching Soon." }
  ];
}

// Subtitles rendering with glass pill backdrop
function renderSubtitles(g, t) {
  const current = subs().find(s => t >= s.t0 && t <= s.t1);
  if (!current) return;

  const fadeIn = clamp((t - current.t0) / 0.22);
  const fadeOut = clamp((current.t1 - t) / 0.22);
  const alpha = Math.min(fadeIn, fadeOut);
  if (alpha <= 0) return;

  g.save();
  g.globalAlpha = alpha;
  g.font = font(26, 500, 'ui');
  const tw = g.measureText(current.text).width;
  const pw = tw + 48, ph = 54;
  const px = W / 2 - pw / 2, py = H - 95;

  g.fillStyle = 'rgba(3, 5, 8, 0.86)';
  rr(g, px, py, pw, ph, ph / 2);
  g.fill();
  g.lineWidth = 1;
  g.strokeStyle = 'rgba(255, 255, 255, 0.15)';
  g.stroke();

  g.fillStyle = '#FFFFFF';
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText(current.text, W / 2, py + ph / 2);
  g.restore();
}

// SHOT 1: The Midnight Crisis (0s – 5.2s)
function renderShot1(g, t) {
  const zoom = lerp(0.96, 1.04, t / 5.2);
  E.bg(g, { lift: 0.9, cyanGlow: 0, t });
  E.grid(g, { ox: W / 2, oy: H / 2, scale: zoom, alpha: 0.7 });
  particles(g, t, 30);

  g.save();
  g.translate(W / 2, H / 2);
  g.scale(zoom, zoom);
  g.translate(-W / 2, -H / 2);

  const cardW = 880, cardH = 480;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;

  // 3D Card with subtle float
  const floatY = Math.sin(t * 2.0) * 6;
  panel3D(g, cx, cy + floatY, cardW, cardH, { r: 24, fill: PAL.surf, stroke: 'rgba(255, 69, 69, 0.45)', shadow: 1.4 });
  glow(g, W / 2, cy + 60 + floatY, 480, PAL.red, 0.2 + 0.08 * Math.sin(t * 8));

  // Glowing Red Emergency Badge
  const blink = (Math.floor(t * 4) % 2 === 0);
  pill(g, cx + 45, cy + 50 + floatY, blink ? "● INBOUND LEAD DETECTED — 11:42 PM" : "○ INBOUND LEAD DETECTED — 11:42 PM", {
    color: PAL.red, bg: 'rgba(255, 69, 69, 0.15)', px: 13
  });

  // Ticking Digital Stopwatch
  const ms = String(Math.floor((t * 100) % 100)).padStart(2, '0');
  pill(g, cx + cardW - 240, cy + 50 + floatY, `⏱ 08:17:42.${ms}`, {
    color: '#F59E0B', bg: PAL.surf2, px: 12
  });

  // Headline
  g.font = font(44, 700, 'disp');
  g.fillStyle = PAL.text;
  g.textAlign = 'left';
  g.fillText("₹2.85 Cr ($1.85M) Sea-Facing Penthouse", cx + 45, cy + 135 + floatY);

  g.font = font(18, 400, 'ui');
  g.fillStyle = PAL.dim;
  g.fillText("High-Intent NRI Buyer · Web Inquiry · Traditional Sales Team Offline", cx + 45, cy + 175 + floatY);

  // Divider
  g.strokeStyle = PAL.line;
  g.lineWidth = 1;
  g.beginPath();
  g.moveTo(cx + 45, cy + 205 + floatY);
  g.lineTo(cx + cardW - 45, cy + 205 + floatY);
  g.stroke();

  // Metrics Rows with Dynamic Visual Bars
  const rows = [
    { label: "HUMAN TELECALLERS", val: "OFFLINE / ASLEEP", color: PAL.red, pct: 0.1 },
    { label: "TIME UNTIL HUMAN SHIFT", val: "08h 17m DEAD AIR", color: '#F59E0B', pct: 0.95 },
    { label: "BUYER CONVERSION RISK", val: "-391% DROP IN 5 MIN", color: PAL.red, pct: 0.88 }
  ];

  rows.forEach((r, i) => {
    const ry = cy + 250 + i * 65 + floatY;
    g.font = font(13, 600, 'mono');
    g.fillStyle = PAL.mute;
    g.fillText(r.label, cx + 45, ry);

    g.font = font(16, 600, 'mono');
    g.fillStyle = r.color;
    g.textAlign = 'right';
    g.fillText(r.val, cx + cardW - 45, ry);
    g.textAlign = 'left';

    // Gauge bar
    g.fillStyle = 'rgba(255, 255, 255, 0.06)';
    rr(g, cx + 45, ry + 10, cardW - 90, 6, 3);
    g.fill();

    g.fillStyle = r.color;
    rr(g, cx + 45, ry + 10, (cardW - 90) * r.pct, 6, 3);
    g.fill();
  });

  g.restore();
}

// SHOT 2: Commission Evaporation (5.2s – 9.6s)
function renderShot2(g, t) {
  const localT = t - 5.2;
  const shake = Math.sin(localT * 28) * Math.min(5, localT * 1.8);
  E.bg(g, { lift: 0.8, cyanGlow: 0, t });
  E.grid(g, { ox: W / 2 + shake, oy: H / 2, alpha: 0.5 });
  particles(g, t, 25);

  g.save();
  g.translate(shake, 0);

  const cardW = 960, cardH = 380;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;
  panel3D(g, cx, cy, cardW, cardH, { r: 24, fill: '#140608', stroke: 'rgba(255, 69, 69, 0.65)', shadow: 1.6 });

  glow(g, W / 2, H / 2, 550, PAL.red, 0.28);

  g.font = font(15, 700, 'mono');
  g.fillStyle = PAL.red;
  g.textAlign = 'center';
  g.fillText("⚠️ TRADITIONAL TELECALLING FLOOR FAILURE", W / 2, cy + 65);

  g.font = font(50, 700, 'disp');
  g.fillStyle = '#FFFFFF';
  g.fillText("While They Sleep, Your Commission Evaporates.", W / 2, cy + 140);

  // Lost commission counter
  const lostVal = Math.min(1420000, Math.floor(localT * 340000));
  const lostStr = `₹${lostVal.toLocaleString('en-IN')}`;

  g.font = font(16, 600, 'mono');
  g.fillStyle = PAL.dim;
  g.fillText("ESTIMATED PIPELINE VALUE LOST TO NOCTURNAL SILENCE", W / 2, cy + 220);

  g.font = font(72, 700, 'disp');
  g.fillStyle = PAL.red;
  g.fillText(lostStr, W / 2, cy + 295);

  g.restore();
}

// SHOT 3: Autonomous Awakening & Keynote Shockwave (9.6s – 14.5s)
function renderShot3(g, t) {
  const localT = t - 9.6;
  const sweep = clamp(localT / 1.5);
  E.bg(g, { lift: 1.15, cyanGlow: 2.8, t });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.85 });
  particles(g, t, 45);

  // Powerful Shockwave ring on entrance
  const swR = clamp(localT / 0.8) * 800;
  const swA = clamp(1.0 - (localT / 0.8));
  if (swA > 0) {
    g.beginPath();
    g.arc(W / 2, H / 2, swR, 0, TAU);
    g.strokeStyle = rgba(PAL.accent, swA * 0.7);
    g.lineWidth = 4;
    g.stroke();
  }

  glow(g, W / 2, H / 2 - 30, 650, PAL.accent, 0.32);

  const cardW = 1000, cardH = 480;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;

  panel3D(g, cx, cy, cardW, cardH, { r: 24, fill: PAL.surf, stroke: PAL.accent, shadow: 1.5 });
  lightSweep(g, cx, cy, cardW, cardH, sweep, 'rgba(0, 229, 255, 0.45)');

  // Cyan Active Badge
  pill(g, cx + 50, cy + 50, "● CLOSER AI AUTONOMOUS SIP ENGINE — ONLINE", {
    color: PAL.accent, bg: 'rgba(0, 229, 255, 0.14)', px: 13
  });

  g.font = font(46, 700, 'disp');
  g.fillStyle = PAL.text;
  g.textAlign = 'left';
  g.fillText("Outbound Dial Triggered in < 0.08 Seconds", cx + 50, cy + 130);

  g.font = font(18, 400, 'ui');
  g.fillStyle = PAL.dim;
  g.fillText("Zero human intervention. High-fidelity carrier SIP connection established.", cx + 50, cy + 170);

  // Hyper-dynamic audio visualizer
  drawWaveform(g, W / 2, cy + 270, 840, 85, t, { active: true, color: PAL.accent, energy: 1.2 });

  // Telecom Tags
  const tags = ["SIP TRUNK: MUMBAI-01", "CODEC: OPUS-HD 48kHz", "LATENCY: 238ms", "CARRIER: 200 OK"];
  tags.forEach((tg, i) => {
    pill(g, cx + 50 + i * 225, cy + 395, tg, { color: PAL.lime, bg: PAL.surf2, px: 11 });
  });
}

// SHOT 4: Sub-250ms Latency HUD with Radial Speedometer (14.5s – 20.8s)
function renderShot4(g, t) {
  const localT = t - 14.5;
  E.bg(g, { lift: 1.05, cyanGlow: 2.2, t });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.8 });
  particles(g, t, 40);

  const cardW = 1080, cardH = 500;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;
  panel3D(g, cx, cy, cardW, cardH, { r: 24, fill: PAL.surf, stroke: PAL.line, shadow: 1.4 });

  // Left Side: Circular Speedometer Dial
  const dialProg = clamp(localT / 0.8);
  const latencyStr = rollingNumber("<238ms", dialProg, 99);
  drawRadialDial(g, cx + 220, cy + 250, 110, dialProg * 0.85, latencyStr, "GLASS-TO-GLASS LATENCY", PAL.accent);

  // Right Side: Technical Architecture Grid
  const rx = cx + 460, ry = cy + 45, rw = 570, rh = 410;
  panel3D(g, rx, ry, rw, rh, { r: 18, fill: PAL.surf2, stroke: 'rgba(255,255,255,0.08)', shadow: 0.6 });

  const specs = [
    { title: "ADAPTIVE NEURAL VAD", desc: "Sub-second speech interruption & zero-awkward overlap" },
    { title: "DYNAMIC REAL ESTATE GRAPH", desc: "Live inventory, payment plans & localized pricing" },
    { title: "DEEPEVAL & NEMO GUARDRAILS", desc: "100% RERA & regulatory compliance verified" },
    { title: "BI-DIRECTIONAL CRM SYNC", desc: "Instant sync with Salesforce, HubSpot & LeadSquared" }
  ];

  specs.forEach((s, idx) => {
    const sy = ry + 40 + idx * 85;
    g.font = font(13, 700, 'mono');
    g.fillStyle = PAL.lime;
    g.fillText(`● ${s.title}`, rx + 30, sy);

    g.font = font(16, 500, 'ui');
    g.fillStyle = PAL.text;
    g.fillText(s.desc, rx + 30, sy + 25);
  });
}

// SHOT 5: Maya — English NRI Specialist Closer (20.8s – 28.5s)
function renderShot5(g, t) {
  E.bg(g, { lift: 1.05, cyanGlow: 2.0, t });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.75 });
  particles(g, t, 35);

  const cardW = 1120, cardH = 510;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;
  panel3D(g, cx, cy, cardW, cardH, { r: 24, fill: PAL.surf, stroke: PAL.accent, shadow: 1.5 });

  // Avatar + Animated Soundwave Rings
  const avX = cx + 110, avY = cy + 110;
  glow(g, avX, avY, 110, PAL.accent, 0.4);
  
  // Dynamic soundwave rings
  for (let r = 1; r <= 3; r++) {
    const ringR = 50 + ((t * 20 + r * 15) % 40);
    const ringA = clamp(1.0 - (ringR - 50) / 40);
    g.beginPath();
    g.arc(avX, avY, ringR, 0, TAU);
    g.strokeStyle = rgba(PAL.accent, ringA * 0.4);
    g.lineWidth = 2;
    g.stroke();
  }

  panel3D(g, avX - 50, avY - 50, 100, 100, { r: 50, fill: PAL.surf2, stroke: PAL.accent });
  g.font = font(42, 700, 'disp');
  g.fillStyle = PAL.accent;
  g.textAlign = 'center';
  g.fillText("M", avX, avY + 14);

  g.textAlign = 'left';
  g.font = font(14, 700, 'mono');
  g.fillStyle = PAL.lime;
  g.fillText("NEURAL CLOSER 01 · DUAL-MARKET NRI DESK", cx + 190, cy + 90);

  g.font = font(38, 700, 'disp');
  g.fillStyle = PAL.text;
  g.fillText("Maya (English Closer)", cx + 190, cy + 135);

  pill(g, cx + cardW - 240, cy + 85, "GLOBAL NRI SPECIALIST", { color: PAL.accent, bg: PAL.surf2, px: 11 });

  // Divider
  g.strokeStyle = PAL.line;
  g.lineWidth = 1;
  g.beginPath();
  g.moveTo(cx + 60, cy + 190);
  g.lineTo(cx + cardW - 60, cy + 190);
  g.stroke();

  // Speech Transcript Box
  panel3D(g, cx + 60, cy + 220, cardW - 120, 140, { r: 16, fill: PAL.surf2, stroke: 'rgba(0, 229, 255, 0.25)' });
  g.font = font(12, 700, 'mono');
  g.fillStyle = PAL.accent;
  g.fillText("LIVE CALL TRANSCRIPTION", cx + 90, cy + 255);

  g.font = font(22, 500, 'ui');
  g.fillStyle = '#FFFFFF';
  g.fillText('"Good evening, Mr. Daniels. Regarding the Sea-Facing Penthouse,', cx + 90, cy + 295);
  g.fillText('the projected rental yield is 8.4% with full capital gains repatriation."', cx + 90, cy + 330);

  // Hyper-dynamic audio visualizer
  drawWaveform(g, W / 2, cy + 425, cardW - 160, 55, t, { active: true, color: PAL.accent, energy: 1.1 });
}

// SHOT 6: Pallavi — Tamil Luxury Estate Closer (28.5s – 35.0s)
function renderShot6(g, t) {
  E.bg(g, { lift: 1.05, cyanGlow: 1.8, t });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.75 });
  particles(g, t, 35);

  const cardW = 1120, cardH = 510;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;
  panel3D(g, cx, cy, cardW, cardH, { r: 24, fill: PAL.surf, stroke: PAL.emerald, shadow: 1.5 });

  // Avatar + Animated Soundwave Rings
  const avX = cx + 110, avY = cy + 110;
  glow(g, avX, avY, 110, PAL.emerald, 0.4);

  for (let r = 1; r <= 3; r++) {
    const ringR = 50 + ((t * 20 + r * 15) % 40);
    const ringA = clamp(1.0 - (ringR - 50) / 40);
    g.beginPath();
    g.arc(avX, avY, ringR, 0, TAU);
    g.strokeStyle = rgba(PAL.emerald, ringA * 0.4);
    g.lineWidth = 2;
    g.stroke();
  }

  panel3D(g, avX - 50, avY - 50, 100, 100, { r: 50, fill: PAL.surf2, stroke: PAL.emerald });
  g.font = font(42, 700, 'disp');
  g.fillStyle = PAL.emerald;
  g.textAlign = 'center';
  g.fillText("P", avX, avY + 14);

  g.textAlign = 'left';
  g.font = font(14, 700, 'mono');
  g.fillStyle = PAL.lime;
  g.fillText("NEURAL CLOSER 02 · TAMIL NADU & SOUTH INDIA DESK", cx + 190, cy + 90);

  g.font = font(38, 700, 'disp');
  g.fillStyle = PAL.text;
  g.fillText("Pallavi (Tamil Closer)", cx + 190, cy + 135);

  pill(g, cx + cardW - 240, cy + 85, "CHENNAI & ECR EXPERT", { color: PAL.emerald, bg: PAL.surf2, px: 11 });

  // Divider
  g.strokeStyle = PAL.line;
  g.lineWidth = 1;
  g.beginPath();
  g.moveTo(cx + 60, cy + 190);
  g.lineTo(cx + cardW - 60, cy + 190);
  g.stroke();

  // Speech Transcript Box
  panel3D(g, cx + 60, cy + 220, cardW - 120, 140, { r: 16, fill: PAL.surf2, stroke: 'rgba(16, 185, 129, 0.25)' });
  g.font = font(12, 700, 'mono');
  g.fillStyle = PAL.emerald;
  g.fillText("நேரடி அழைப்பு பதிவு (LIVE CALL TRANSCRIPTION)", cx + 90, cy + 255);

  g.font = font(22, 500, 'ui');
  g.fillStyle = '#FFFFFF';
  g.fillText('"வணக்கம் சார், சென்னை ECR வில்லாவின் RERA அப்ரூவல் மற்றும்', cx + 90, cy + 295);
  g.fillText('சைட் விசிட் விவரங்கள் தயார். இந்த வார இறுதியில் பதிவு செய்யலாமா?"', cx + 90, cy + 330);

  // Hyper-dynamic audio visualizer
  drawWaveform(g, W / 2, cy + 425, cardW - 160, 55, t, { active: true, color: PAL.emerald, energy: 1.1 });
}

// SHOT 7: Swati — Hindi HNW Closer (35.0s – 43.0s)
function renderShot7(g, t) {
  E.bg(g, { lift: 1.05, cyanGlow: 1.8, t });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.75 });
  particles(g, t, 35);

  const cardW = 1120, cardH = 510;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;
  panel3D(g, cx, cy, cardW, cardH, { r: 24, fill: PAL.surf, stroke: PAL.purple, shadow: 1.5 });

  // Avatar + Animated Soundwave Rings
  const avX = cx + 110, avY = cy + 110;
  glow(g, avX, avY, 110, PAL.purple, 0.4);

  for (let r = 1; r <= 3; r++) {
    const ringR = 50 + ((t * 20 + r * 15) % 40);
    const ringA = clamp(1.0 - (ringR - 50) / 40);
    g.beginPath();
    g.arc(avX, avY, ringR, 0, TAU);
    g.strokeStyle = rgba(PAL.purple, ringA * 0.4);
    g.lineWidth = 2;
    g.stroke();
  }

  panel3D(g, avX - 50, avY - 50, 100, 100, { r: 50, fill: PAL.surf2, stroke: PAL.purple });
  g.font = font(42, 700, 'disp');
  g.fillStyle = PAL.purple;
  g.textAlign = 'center';
  g.fillText("S", avX, avY + 14);

  g.textAlign = 'left';
  g.font = font(14, 700, 'mono');
  g.fillStyle = PAL.lime;
  g.fillText("NEURAL CLOSER 03 · DELHI NCR & NORTH INDIA DESK", cx + 190, cy + 90);

  g.font = font(38, 700, 'disp');
  g.fillStyle = PAL.text;
  g.fillText("Swati (Hindi Closer)", cx + 190, cy + 135);

  pill(g, cx + cardW - 240, cy + 85, "GURUGRAM & NCR LUXURY", { color: PAL.purple, bg: PAL.surf2, px: 11 });

  // Divider
  g.strokeStyle = PAL.line;
  g.lineWidth = 1;
  g.beginPath();
  g.moveTo(cx + 60, cy + 190);
  g.lineTo(cx + cardW - 60, cy + 190);
  g.stroke();

  // Speech Transcript Box
  panel3D(g, cx + 60, cy + 220, cardW - 120, 140, { r: 16, fill: PAL.surf2, stroke: 'rgba(192, 132, 252, 0.25)' });
  g.font = font(12, 700, 'mono');
  g.fillStyle = PAL.purple;
  g.fillText("लाइव कॉल ट्रांसक्रिप्शन (LIVE CALL TRANSCRIPTION)", cx + 90, cy + 255);

  g.font = font(22, 500, 'ui');
  g.fillStyle = '#FFFFFF';
  g.fillText('"नमस्ते सर, गोल्फ कोर्स रोड पेंटहाउस के लिए', cx + 90, cy + 295);
  g.fillText('रविवार सुबह ग्यारह बजे आपकी फैमिली विज़िट बुक कर दी है।"', cx + 90, cy + 330);

  // Hyper-dynamic audio visualizer
  drawWaveform(g, W / 2, cy + 425, cardW - 160, 55, t, { active: true, color: PAL.purple, energy: 1.1 });
}

// SHOT 8: Monumental Unit Economics (43.0s – 50.5s)
function renderShot8(g, t) {
  const localT = t - 43.0;
  E.bg(g, { lift: 1.25, cyanGlow: 2.8, t });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.85 });
  particles(g, t, 50);

  glow(g, W / 2, H / 2 - 70, 750, PAL.lime, 0.28);

  const prog = clamp(localT / 0.9);
  const numStr = rollingNumber("₹1.55", prog, 88);

  g.textAlign = 'center';
  g.font = font(18, 700, 'mono');
  g.fillStyle = PAL.dim;
  g.fillText("UNIT ECONOMICS PER QUALIFIED DIALED LEAD", W / 2, H / 2 - 165);

  // Monumental 180px Typographic Number
  g.font = font(180, 800, 'disp');
  g.fillStyle = PAL.lime;
  g.fillText(numStr, W / 2, H / 2 + 15);

  // Contrast Comparison Cards
  const cardW = 920, cardH = 115;
  const cx = W / 2 - cardW / 2, cy = H / 2 + 75;
  panel3D(g, cx, cy, cardW, cardH, { r: 20, fill: PAL.surf, stroke: PAL.line });

  g.font = font(17, 700, 'mono');
  g.fillStyle = PAL.red;
  g.fillText("HUMAN TELECALLER: ₹220 ($2.60)", cx + 230, cy + 65);

  g.fillStyle = PAL.mute;
  g.fillText("vs", cx + 460, cy + 65);

  g.font = font(22, 800, 'mono');
  g.fillStyle = PAL.lime;
  g.fillText("CLOSER AI: ₹1.55 (-99.3% COST)", cx + 690, cy + 65);

  // Margin Uplift Callout
  pill(g, W / 2 - 250, H / 2 + 230, "● +99.3% GROSS MARGIN UPLIFT · ZERO SLEEP · 100% CRM SYNC", {
    color: PAL.lime, bg: PAL.surf2, px: 13
  });
}

// SHOT 9: Hero Climax & Launching Soon (50.5s – 60.0s)
function renderShot9(g, t) {
  const localT = t - 50.5;
  const sweep = clamp(localT / 1.8);
  E.bg(g, { lift: 1.35, cyanGlow: 3.5, t });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.9 });
  particles(g, t, 60);

  glow(g, W / 2, H / 2 - 100, 900, PAL.accent, 0.35);

  g.save();
  g.textAlign = 'center';

  // Hero Logo Icon Mark
  const logoY = H / 2 - 145;
  panel3D(g, W / 2 - 55, logoY - 55, 110, 110, { r: 28, fill: PAL.surf2, stroke: PAL.accent, shadow: 1.4 });
  g.font = font(54, 800, 'disp');
  g.fillStyle = PAL.accent;
  g.fillText("C", W / 2, logoY + 18);

  // Hero Title
  g.font = font(92, 800, 'disp');
  g.fillStyle = '#FFFFFF';
  g.fillText("CLOSER AI", W / 2, logoY + 125);

  lightSweep(g, W / 2 - 450, logoY + 30, 900, 130, sweep, 'rgba(0, 229, 255, 0.45)');

  // Tagline
  g.font = font(24, 700, 'mono');
  g.fillStyle = PAL.accent;
  g.fillText("INTELLIGENCE DESIGNED TO EVOLVE", W / 2, logoY + 185);

  // Launching Soon Banner
  const pillW = 720, pillH = 68;
  const px = W / 2 - pillW / 2, py = logoY + 235;
  panel3D(g, px, py, pillW, pillH, { r: pillH / 2, fill: 'rgba(0, 229, 255, 0.12)', stroke: PAL.accent });

  g.font = font(21, 800, 'mono');
  g.fillStyle = PAL.lime;
  g.fillText("● LAUNCHING SOON · DUAL-MARKET CAPACITY", W / 2, py + 41);

  g.font = font(16, 500, 'ui');
  g.fillStyle = PAL.dim;
  g.fillText("Enterprise Deployments Now Open · USA & India", W / 2, py + 102);

  g.restore();
}

// Master Render Entrypoint
export function renderFilm(g, t, o = {}) {
  const { nosub = false } = o;

  let alpha = 1.0;
  if (t > 58.5) {
    alpha = clamp((DUR - t) / 1.5);
  }

  g.save();
  g.globalAlpha = alpha;

  if (t < 5.2) {
    renderShot1(g, t);
  } else if (t < 9.6) {
    renderShot2(g, t);
  } else if (t < 14.5) {
    renderShot3(g, t);
  } else if (t < 20.8) {
    renderShot4(g, t);
  } else if (t < 28.5) {
    renderShot5(g, t);
  } else if (t < 35.0) {
    renderShot6(g, t);
  } else if (t < 43.0) {
    renderShot7(g, t);
  } else if (t < 50.5) {
    renderShot8(g, t);
  } else {
    renderShot9(g, t);
  }

  vignette(g, 0.52);

  if (!nosub) {
    renderSubtitles(g, t);
  }

  g.restore();
}
