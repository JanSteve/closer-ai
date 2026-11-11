// film.js — CLOSER AI Award-Winning Cinematic Film ("The 11:42 PM Lead")
// Higgsfield / Apple Keynote / Linear Standard.
// Features: 2.5D Virtual Camera, True 3D Strip Perspective Carousel,
// Anamorphic Flares, Dual-Layer Bokeh, Mechanical Rolling Digits, Organic Waveforms.

import * as E from './engine.js';
const { W, H, PAL, clamp, lerp, seg, ss, eo, ei, eio, back, spring, font, rr, glow,
        panel3D, pill, drawWaveform, drawRadialDial, rollingNumber, lightSweep,
        vignette, cinematicBokeh, anamorphicFlare, perspective3D, buf, TAU, rgba } = E;

export const DUR = 60.0;

let LINES = [];
let DURS = {};

export function setLines(lines, durs) {
  LINES = lines || [];
  DURS = durs || {};
}

// Subtitles timed to Kokoro af_heart female voiceover
export function subs() {
  return [
    { t0: 0.5, t1: 5.0, text: "At 11:42 PM, a multi-crore real estate lead arrives." },
    { t0: 5.4, t1: 9.2, text: "While traditional sales floors sleep, your commission evaporates." },
    { t0: 9.8, t1: 13.5, text: "Meet CLOSER AI. The autonomous neural closing engine." },
    { t0: 14.0, t1: 20.2, text: "Sub-250 millisecond response. Carrier-grade SIP. Zero dropped calls." },
    { t0: 20.8, t1: 28.2, text: 'Maya: "Good evening, Mr. Daniels. Regarding the Sea-Facing Penthouse, projected rental yield is 8.4%."' },
    { t0: 28.8, t1: 34.8, text: 'Pallavi: "வணக்கம் சார், சென்னை ECR வில்லாவின் RERA அப்ரூவல் மற்றும் சைட் விசிட் விவரங்கள் தயார்."' },
    { t0: 35.4, t1: 42.8, text: 'Swati: "नमस्ते सर, गोल्फ कोर्स रोड पेंटहाउस के लिए रविवार सुबह ग्यारह बजे आपकी फैमिली विज़िट बुक कर दी है।"' },
    { t0: 43.5, t1: 49.8, text: "₹1.55 per qualified call. 99.3% margin uplift." },
    { t0: 50.5, t1: 55.5, text: "CLOSER AI. Intelligence Designed To Evolve. Launching Soon." }
  ];
}

// Subtitles rendering with frosted dark glass pill and speaking indicator
function renderSubtitles(g, t) {
  const current = subs().find(s => t >= s.t0 && t <= s.t1);
  if (!current) return;

  const fadeIn = clamp((t - current.t0) / 0.20);
  const fadeOut = clamp((current.t1 - t) / 0.20);
  const alpha = Math.min(fadeIn, fadeOut);
  if (alpha <= 0) return;

  g.save();
  g.globalAlpha = alpha;
  g.font = font(25, 500, 'ui');
  const tw = g.measureText(current.text).width;
  const pw = tw + 56, ph = 54;
  const px = W / 2 - pw / 2, py = H - 92;

  // Frosted dark pill backdrop
  g.fillStyle = 'rgba(6, 9, 15, 0.88)';
  g.shadowColor = 'rgba(0, 0, 0, 0.5)';
  g.shadowBlur = 24;
  g.shadowOffsetY = 8;
  rr(g, px, py, pw, ph, ph / 2);
  g.fill();
  g.shadowColor = 'transparent';

  // Hairline border
  g.lineWidth = 1;
  g.strokeStyle = 'rgba(255, 255, 255, 0.14)';
  rr(g, px + 0.5, py + 0.5, pw - 1, ph - 1, ph / 2);
  g.stroke();

  // Cyan speaking status dot
  g.fillStyle = PAL.accent;
  g.shadowColor = rgba(PAL.accent, 0.8);
  g.shadowBlur = 10;
  g.beginPath();
  g.arc(px + 24, py + ph / 2, 4.5, 0, TAU);
  g.fill();
  g.shadowColor = 'transparent';

  // Subtitle text
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'left';
  g.textBaseline = 'middle';
  g.fillText(current.text, px + 38, py + ph / 2 + 0.5);

  g.restore();
}

// ─────────────────────────────────────────────────────────────
// SHOT 1: The Midnight Crisis (0.0s – 5.2s)
// ─────────────────────────────────────────────────────────────
function renderShot1(g, t) {
  // Continuous cinematic push-in
  const p = t / 5.2;
  const zoom = lerp(0.95, 1.05, p);

  E.bg(g, { lift: 0.85, cyanGlow: 0, t });
  E.grid(g, { ox: W / 2, oy: H / 2, scale: zoom, alpha: 0.65 });
  cinematicBokeh(g, t, 32);

  g.save();
  g.translate(W / 2, H / 2);
  g.scale(zoom, zoom);
  g.translate(-W / 2, -H / 2);

  const cardW = 920, cardH = 490;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;

  // Floating 3D card
  const floatY = Math.sin(t * 1.8) * 6;
  panel3D(g, cx, cy + floatY, cardW, cardH, { r: 24, fill: PAL.surf, stroke: 'rgba(255, 69, 69, 0.5)', shadow: 1.5 });
  glow(g, W / 2, cy + 70 + floatY, 520, PAL.red, 0.18 + 0.08 * Math.sin(t * 7));

  // Blinking Red Emergency Badge
  const blink = (Math.floor(t * 3.5) % 2 === 0);
  pill(g, cx + 50, cy + 52 + floatY, blink ? "● INBOUND LEAD DETECTED — 11:42 PM" : "○ INBOUND LEAD DETECTED — 11:42 PM", {
    color: PAL.red, bg: 'rgba(255, 69, 69, 0.14)', px: 13
  });

  // Ticking Microsecond Stopwatch
  const ms = String(Math.floor((t * 100) % 100)).padStart(2, '0');
  pill(g, cx + cardW - 250, cy + 52 + floatY, `⏱ 08:17:42.${ms}`, {
    color: '#F59E0B', bg: PAL.surf2, px: 12
  });

  // Property Headline
  g.font = font(44, 700, 'disp');
  g.fillStyle = PAL.text;
  g.textAlign = 'left';
  g.fillText("₹2.85 Cr ($1.85M) Sea-Facing Penthouse", cx + 50, cy + 138 + floatY);

  g.font = font(18, 400, 'ui');
  g.fillStyle = PAL.dim;
  g.fillText("High-Intent NRI Buyer · Web Inquiry · Traditional Sales Team Offline", cx + 50, cy + 178 + floatY);

  // Divider
  g.strokeStyle = PAL.line;
  g.lineWidth = 1;
  g.beginPath();
  g.moveTo(cx + 50, cy + 208 + floatY);
  g.lineTo(cx + cardW - 50, cy + 208 + floatY);
  g.stroke();

  // Metric Rows with Gradient Status Bars
  const rows = [
    { label: "HUMAN TELECALLERS", val: "OFFLINE / ASLEEP", color: PAL.red, pct: 0.12 },
    { label: "TIME UNTIL HUMAN SHIFT", val: "08h 17m DEAD AIR", color: '#F59E0B', pct: 0.95 },
    { label: "BUYER CONVERSION DECAY", val: "-391% DROP IN 5 MIN", color: PAL.red, pct: 0.88 }
  ];

  rows.forEach((r, i) => {
    const ry = cy + 252 + i * 66 + floatY;
    g.font = font(13, 600, 'mono');
    g.fillStyle = PAL.mute;
    g.fillText(r.label, cx + 50, ry);

    g.font = font(16, 600, 'mono');
    g.fillStyle = r.color;
    g.textAlign = 'right';
    g.fillText(r.val, cx + cardW - 50, ry);
    g.textAlign = 'left';

    // Gauge track & active fill
    g.fillStyle = 'rgba(255, 255, 255, 0.06)';
    rr(g, cx + 50, ry + 10, cardW - 100, 6, 3);
    g.fill();

    g.fillStyle = r.color;
    rr(g, cx + 50, ry + 10, (cardW - 100) * r.pct, 6, 3);
    g.fill();
  });

  g.restore();
}

// ─────────────────────────────────────────────────────────────
// SHOT 2: Commission Evaporation (5.2s – 9.6s)
// ─────────────────────────────────────────────────────────────
function renderShot2(g, t) {
  const localT = t - 5.2;
  const p = localT / 4.4;

  // High-tension jitter vibration
  const shakeAmp = Math.min(6, localT * 1.6);
  const shakeX = Math.sin(localT * 32) * shakeAmp;
  const shakeY = Math.cos(localT * 26) * shakeAmp * 0.5;

  E.bg(g, { lift: 0.85, cyanGlow: 0, t });
  E.grid(g, { ox: W / 2 + shakeX, oy: H / 2 + shakeY, alpha: 0.55 });
  cinematicBokeh(g, t, 28);

  g.save();
  g.translate(shakeX, shakeY);

  const cardW = 980, cardH = 400;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;

  panel3D(g, cx, cy, cardW, cardH, { r: 24, fill: '#140609', stroke: 'rgba(255, 69, 69, 0.7)', shadow: 1.6 });
  glow(g, W / 2, H / 2 - 20, 600, PAL.red, 0.26 + 0.08 * Math.sin(localT * 10));

  g.font = font(15, 700, 'mono');
  g.fillStyle = PAL.red;
  g.textAlign = 'center';
  g.fillText("⚠️ TRADITIONAL TELECALLING FLOOR FAILURE", W / 2, cy + 68);

  g.font = font(50, 700, 'disp');
  g.fillStyle = '#FFFFFF';
  g.fillText("While They Sleep, Your Commission Evaporates.", W / 2, cy + 145);

  // Lost commission counter accelerating upwards
  const lostVal = Math.min(1420000, Math.floor(localT * 355000));
  const lostStr = `₹${lostVal.toLocaleString('en-IN')}`;

  g.font = font(16, 600, 'mono');
  g.fillStyle = PAL.dim;
  g.fillText("ESTIMATED PIPELINE VALUE LOST TO NOCTURNAL SILENCE", W / 2, cy + 225);

  g.font = font(74, 800, 'disp');
  g.fillStyle = PAL.red;
  g.fillText(lostStr, W / 2, cy + 305);

  // Anamorphic warning glint
  if (localT > 1.5 && localT < 3.2) {
    anamorphicFlare(g, W / 2, cy + 300, 800, PAL.red, 0.5 * Math.sin((localT - 1.5) / 1.7 * Math.PI));
  }

  g.restore();
}

// ─────────────────────────────────────────────────────────────
// SHOT 3: Autonomous Awakening & Keynote Shockwave (9.6s – 14.5s)
// ─────────────────────────────────────────────────────────────
function renderShot3(g, t) {
  const localT = t - 9.6;
  const p = localT / 4.9;
  const sweep = clamp(localT / 1.6);

  E.bg(g, { lift: 1.15, cyanGlow: 2.8, t });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.85 });
  cinematicBokeh(g, t, 48);

  // Supersonic expanding shockwave ring from center
  const swR = clamp(localT / 0.75) * 850;
  const swA = clamp(1.0 - (localT / 0.75));
  if (swA > 0) {
    g.beginPath();
    g.arc(W / 2, H / 2, swR, 0, TAU);
    g.strokeStyle = rgba(PAL.accent, swA * 0.75);
    g.lineWidth = 4;
    g.stroke();

    // Brilliant horizontal anamorphic flash on impact
    anamorphicFlare(g, W / 2, H / 2, 1400, PAL.accent, swA * 1.2);
  }

  glow(g, W / 2, H / 2 - 30, 680, PAL.accent, 0.35);

  const cardW = 1040, cardH = 490;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;

  // Spring settle bounce on entry
  const enterScale = localT < 0.6 ? back(clamp(localT / 0.6), 1.3) : 1.0;
  g.save();
  g.translate(W / 2, H / 2);
  g.scale(enterScale, enterScale);
  g.translate(-W / 2, -H / 2);

  panel3D(g, cx, cy, cardW, cardH, { r: 24, fill: PAL.surf, stroke: PAL.accent, shadow: 1.6 });
  lightSweep(g, cx, cy, cardW, cardH, sweep, 'rgba(0, 229, 255, 0.45)');

  // Cyan Active Badge
  pill(g, cx + 50, cy + 50, "● CLOSER AI AUTONOMOUS SIP ENGINE — ONLINE", {
    color: PAL.accent, bg: 'rgba(0, 229, 255, 0.15)', px: 13
  });

  g.font = font(46, 700, 'disp');
  g.fillStyle = PAL.text;
  g.textAlign = 'left';
  g.fillText("Outbound Dial Triggered in < 0.08 Seconds", cx + 50, cy + 132);

  g.font = font(18, 400, 'ui');
  g.fillStyle = PAL.dim;
  g.fillText("Zero human intervention. High-fidelity carrier SIP connection established.", cx + 50, cy + 172);

  // Hyper-dynamic audio visualizer
  drawWaveform(g, W / 2, cy + 275, 880, 85, t, { active: true, color: PAL.accent, energy: 1.25 });

  // Telecom Tags
  const tags = ["SIP TRUNK: MUMBAI-01", "CODEC: OPUS-HD 48kHz", "LATENCY: 238ms", "CARRIER: 200 OK"];
  tags.forEach((tg, i) => {
    pill(g, cx + 50 + i * 235, cy + 400, tg, { color: PAL.lime, bg: PAL.surf2, px: 11 });
  });

  g.restore();
}

// ─────────────────────────────────────────────────────────────
// SHOT 4: Sub-250ms Latency HUD with Radial Speedometer (14.5s – 20.8s)
// ─────────────────────────────────────────────────────────────
function renderShot4(g, t) {
  const localT = t - 14.5;
  const p = localT / 6.3;

  E.bg(g, { lift: 1.05, cyanGlow: 2.2, t });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.8 });
  cinematicBokeh(g, t, 42);

  const cardW = 1100, cardH = 500;
  const cx = W / 2 - cardW / 2, cy = H / 2 - cardH / 2 - 20;

  panel3D(g, cx, cy, cardW, cardH, { r: 24, fill: PAL.surf, stroke: PAL.line, shadow: 1.4 });

  // Left Side: Circular Speedometer Dial
  const dialProg = clamp(localT / 0.8);
  const latencyStr = rollingNumber("<238ms", dialProg, 99);
  drawRadialDial(g, cx + 225, cy + 250, 115, dialProg * 0.85, latencyStr, "GLASS-TO-GLASS LATENCY", PAL.accent);

  // Right Side: Technical Architecture Grid
  const rx = cx + 470, ry = cy + 45, rw = 580, rh = 410;
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

// ─────────────────────────────────────────────────────────────
// TRI-LINGUAL CLOSER CAROUSEL RENDERER (Shots 5, 6, 7)
// Uses true 3D Strip Perspective Slicing (rotY yaw)!
// ─────────────────────────────────────────────────────────────
function drawCloserCardToBuffer(bufName, config, t) {
  const [c, gOff] = buf(bufName, 1140, 520);
  const { letter, color, desk, name, pillText, transcriptHeader, line1, line2, energy } = config;

  const cardW = 1140, cardH = 520;
  panel3D(gOff, 0, 0, cardW, cardH, { r: 24, fill: PAL.surf, stroke: color, shadow: 1.5 });

  // Avatar + Animated Acoustic Soundwave Rings
  const avX = 110, avY = 110;
  glow(gOff, avX, avY, 110, color, 0.4);

  for (let r = 1; r <= 3; r++) {
    const ringR = 50 + ((t * 22 + r * 16) % 42);
    const ringA = clamp(1.0 - (ringR - 50) / 42);
    gOff.beginPath();
    gOff.arc(avX, avY, ringR, 0, TAU);
    gOff.strokeStyle = rgba(color, ringA * 0.45);
    gOff.lineWidth = 2;
    gOff.stroke();
  }

  panel3D(gOff, avX - 50, avY - 50, 100, 100, { r: 50, fill: PAL.surf2, stroke: color });
  gOff.font = font(42, 700, 'disp');
  gOff.fillStyle = color;
  gOff.textAlign = 'center';
  gOff.fillText(letter, avX, avY + 14);

  gOff.textAlign = 'left';
  gOff.font = font(14, 700, 'mono');
  gOff.fillStyle = PAL.lime;
  gOff.fillText(desk, 190, 90);

  gOff.font = font(38, 700, 'disp');
  gOff.fillStyle = PAL.text;
  gOff.fillText(name, 190, 135);

  pill(gOff, cardW - 240, 85, pillText, { color, bg: PAL.surf2, px: 11 });

  // Divider
  gOff.strokeStyle = PAL.line;
  gOff.lineWidth = 1;
  gOff.beginPath();
  gOff.moveTo(60, 190);
  gOff.lineTo(cardW - 60, 190);
  gOff.stroke();

  // Speech Transcript Box
  panel3D(gOff, 60, 220, cardW - 120, 140, { r: 16, fill: PAL.surf2, stroke: rgba(color, 0.28) });
  gOff.font = font(12, 700, 'mono');
  gOff.fillStyle = color;
  gOff.fillText(transcriptHeader, 90, 255);

  gOff.font = font(22, 500, 'ui');
  gOff.fillStyle = '#FFFFFF';
  gOff.fillText(line1, 90, 295);
  gOff.fillText(line2, 90, 330);

  // Hyper-dynamic audio visualizer
  drawWaveform(gOff, cardW / 2, 430, cardW - 160, 56, t, { active: true, color, energy });

  return c;
}

// SHOT 5: Maya — English NRI Specialist Closer (20.8s – 28.5s)
function renderShot5(g, t) {
  E.bg(g, { lift: 1.05, cyanGlow: 2.2, t });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.75 });
  cinematicBokeh(g, t, 38);

  const config = {
    letter: "M",
    color: PAL.accent,
    desk: "NEURAL CLOSER 01 · DUAL-MARKET NRI DESK",
    name: "Maya (English Closer)",
    pillText: "GLOBAL NRI SPECIALIST",
    transcriptHeader: "LIVE CALL TRANSCRIPTION",
    line1: '"Good evening, Mr. Daniels. Regarding the Sea-Facing Penthouse,',
    line2: 'the projected rental yield is 8.4% with full capital gains repatriation."',
    energy: 1.2
  };

  const canvas = drawCloserCardToBuffer('c_maya', config, t);

  // 3D Carousel Transition at end of shot (28.0s – 28.5s)
  let rotY = 0;
  if (t > 28.0) {
    const u = (t - 28.0) / 0.5;
    rotY = -0.35 * ss(u);
  }

  perspective3D(g, canvas, W / 2, H / 2 - 20, 1140, 520, rotY);
}

// SHOT 6: Pallavi — Tamil Luxury Estate Closer (28.5s – 35.0s)
function renderShot6(g, t) {
  E.bg(g, { lift: 1.05, cyanGlow: 1.8, t, tint: PAL.emerald });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.75 });
  cinematicBokeh(g, t, 38);

  const config = {
    letter: "P",
    color: PAL.emerald,
    desk: "NEURAL CLOSER 02 · TAMIL NADU & SOUTH INDIA DESK",
    name: "Pallavi (Tamil Closer)",
    pillText: "CHENNAI & ECR EXPERT",
    transcriptHeader: "நேரடி அழைப்பு பதிவு (LIVE CALL TRANSCRIPTION)",
    line1: '"வணக்கம் சார், சென்னை ECR வில்லாவின் RERA அப்ரூவல் மற்றும்',
    line2: 'சைட் விசிட் விவரங்கள் தயார். இந்த வார இறுதியில் பதிவு செய்யலாமா?"',
    energy: 1.2
  };

  const canvas = drawCloserCardToBuffer('c_pallavi', config, t);

  // 3D Carousel entrance (28.5s – 29.0s) and exit (34.5s – 35.0s)
  let rotY = 0;
  if (t < 29.0) {
    const u = (29.0 - t) / 0.5;
    rotY = 0.35 * ss(u);
  } else if (t > 34.5) {
    const u = (t - 34.5) / 0.5;
    rotY = -0.35 * ss(u);
  }

  perspective3D(g, canvas, W / 2, H / 2 - 20, 1140, 520, rotY);
}

// SHOT 7: Swati — Hindi HNW Closer (35.0s – 43.0s)
function renderShot7(g, t) {
  E.bg(g, { lift: 1.05, cyanGlow: 1.8, t, tint: PAL.purple });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.75 });
  cinematicBokeh(g, t, 38);

  const config = {
    letter: "S",
    color: PAL.purple,
    desk: "NEURAL CLOSER 03 · DELHI NCR & NORTH INDIA DESK",
    name: "Swati (Hindi Closer)",
    pillText: "GURUGRAM & NCR LUXURY",
    transcriptHeader: "लाइव कॉल ट्रांसक्रिप्शन (LIVE CALL TRANSCRIPTION)",
    line1: '"नमस्ते सर, गोल्फ कोर्स रोड पेंटहाउस के लिए',
    line2: 'रविवार सुबह ग्यारह बजे आपकी फैमिली विज़िट बुक कर दी है।"',
    energy: 1.2
  };

  const canvas = drawCloserCardToBuffer('c_swati', config, t);

  // 3D Carousel entrance (35.0s – 35.5s)
  let rotY = 0;
  if (t < 35.5) {
    const u = (35.5 - t) / 0.5;
    rotY = 0.35 * ss(u);
  }

  perspective3D(g, canvas, W / 2, H / 2 - 20, 1140, 520, rotY);
}

// ─────────────────────────────────────────────────────────────
// SHOT 8: Monumental Unit Economics (43.0s – 50.5s)
// ─────────────────────────────────────────────────────────────
function renderShot8(g, t) {
  const localT = t - 43.0;
  const p = localT / 7.5;

  E.bg(g, { lift: 1.25, cyanGlow: 2.8, t });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.85 });
  cinematicBokeh(g, t, 52);

  // Initial impact shockwave
  if (localT < 0.6) {
    const swA = 1.0 - (localT / 0.6);
    anamorphicFlare(g, W / 2, H / 2, 1200, PAL.lime, swA * 1.0);
  }

  glow(g, W / 2, H / 2 - 70, 780, PAL.lime, 0.30);

  const prog = clamp(localT / 0.85);
  const numStr = rollingNumber("₹1.55", prog, 88);

  g.textAlign = 'center';
  g.font = font(18, 700, 'mono');
  g.fillStyle = PAL.dim;
  g.fillText("UNIT ECONOMICS PER QUALIFIED DIALED LEAD", W / 2, H / 2 - 165);

  // Monumental 185px Typographic Display Number
  g.font = font(185, 800, 'disp');
  g.fillStyle = PAL.lime;
  g.shadowColor = rgba(PAL.lime, 0.6);
  g.shadowBlur = 32;
  g.fillText(numStr, W / 2, H / 2 + 15);
  g.shadowColor = 'transparent';

  // Contrast Comparison Cards
  const cardW = 940, cardH = 115;
  const cx = W / 2 - cardW / 2, cy = H / 2 + 75;
  panel3D(g, cx, cy, cardW, cardH, { r: 20, fill: PAL.surf, stroke: PAL.line });

  g.font = font(17, 700, 'mono');
  g.fillStyle = PAL.red;
  g.fillText("HUMAN TELECALLER: ₹220 ($2.60)", cx + 235, cy + 65);

  g.fillStyle = PAL.mute;
  g.fillText("vs", cx + 470, cy + 65);

  g.font = font(22, 800, 'mono');
  g.fillStyle = PAL.lime;
  g.fillText("CLOSER AI: ₹1.55 (-99.3% COST)", cx + 705, cy + 65);

  // Margin Uplift Callout
  pill(g, W / 2 - 250, H / 2 + 230, "● +99.3% GROSS MARGIN UPLIFT · ZERO SLEEP · 100% CRM SYNC", {
    color: PAL.lime, bg: PAL.surf2, px: 13
  });
}

// ─────────────────────────────────────────────────────────────
// SHOT 9: Hero Climax & Launching Soon (50.5s – 60.0s)
// ─────────────────────────────────────────────────────────────
function renderShot9(g, t) {
  const localT = t - 50.5;
  const sweep = clamp(localT / 1.8);

  // Slow majestic camera pullback
  const zoom = lerp(1.04, 0.98, clamp(localT / 8.0));

  E.bg(g, { lift: 1.35, cyanGlow: 3.5, t });
  E.grid(g, { ox: W / 2, oy: H / 2, scale: zoom, alpha: 0.9 });
  cinematicBokeh(g, t, 60);

  g.save();
  g.translate(W / 2, H / 2);
  g.scale(zoom, zoom);
  g.translate(-W / 2, -H / 2);

  glow(g, W / 2, H / 2 - 100, 920, PAL.accent, 0.38);

  g.textAlign = 'center';

  // Hero Logo Icon Mark
  const logoY = H / 2 - 145;
  panel3D(g, W / 2 - 55, logoY - 55, 110, 110, { r: 28, fill: PAL.surf2, stroke: PAL.accent, shadow: 1.5 });
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

  // Horizontal Anamorphic Glint across title
  if (localT > 0.8 && localT < 3.0) {
    anamorphicFlare(g, W / 2, logoY + 80, 1100, PAL.accent, 0.6 * Math.sin((localT - 0.8) / 2.2 * Math.PI));
  }

  g.restore();
}

// ─────────────────────────────────────────────────────────────
// MASTER RENDER ENTRYPOINT
// ─────────────────────────────────────────────────────────────
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
