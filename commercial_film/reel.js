// reel.js — CLOSER AI Official Instagram Reel Engine (9:16 Vertical 1080x1920)
// High-Converting Documentary Explainer for Instagram Reels & TikTok.
// Grounded in JSM Integrated Services (Chennai luxury real estate).
// Features: Meta Ad Spend Burner, 5-Minute Cliff Chart, Autonomous Callback,
// Tri-Lingual Closers, Live WhatsApp Co-Browsing, ₹1.55 Economics, Viral Comment Magnet.

import * as E from './engine.js';
const { PAL, clamp, lerp, seg, ss, eo, ei, eio, back, spring, font, rr, glow,
        panel3D, pill, drawWaveform, drawRadialDial, rollingNumber, lightSweep,
        vignette, cinematicBokeh, anamorphicFlare, perspective3D, buf, TAU, rgba } = E;

export const W = 1080, H = 1920;
export const DUR = 65.0;

// Subtitles timed for 65s Documentary Instagram Reel
export function reelSubs() {
  return [
    { t0: 0.5, t1: 4.2, text: "Builders spend lakhs on ads.", highlight: "lakhs on ads" },
    { t0: 4.3, t1: 7.9, text: "70% of luxury leads evaporate.", highlight: "70% evaporate" },
    { t0: 8.1, t1: 13.5, text: "At JSM Chennai, inquiries arrive at 11:42 PM.", highlight: "11:42 PM" },
    { t0: 13.6, t1: 19.6, text: "After 5 minutes, lead intent drops off a cliff.", highlight: "5-Minute Cliff" },
    { t0: 19.8, t1: 25.9, text: "CLOSER AI dials the lead in 0.08 seconds.", highlight: "0.08 seconds" },
    { t0: 26.2, t1: 35.0, text: 'Maya: "Rental yield is 8.4%. Sunday visit reserved."', highlight: "8.4% yield" },
    { t0: 35.2, t1: 41.0, text: 'Pallavi: "சென்னை ECR வில்லா RERA அப்ரூவல் தயார்."', highlight: "ECR வில்லா" },
    { t0: 41.2, t1: 46.0, text: 'Swati: "गोल्फ कोर्स पेंटहाउस विज़िट बुक कर दी है।"', highlight: "विज़िट बुक" },
    { t0: 46.3, t1: 52.4, text: "Live WhatsApp push: floor plans + VIP pass.", highlight: "WhatsApp push" },
    { t0: 52.6, t1: 58.7, text: "Human call: ₹220. CLOSER AI: ₹1.55.", highlight: "₹1.55 / call" },
    { t0: 58.9, t1: 64.6, text: 'Comment "CLOSER" for the free AI blueprint.', highlight: 'Comment "CLOSER"' }
  ];
}

// ───────────────────────── Instagram Safe-Zone Captions ─────────────────────────
function renderReelCaptions(g, t) {
  const current = reelSubs().find(s => t >= s.t0 && t <= s.t1);
  if (!current) return;

  const fadeIn = clamp((t - current.t0) / 0.16);
  const fadeOut = clamp((current.t1 - t) / 0.16);
  const alpha = Math.min(fadeIn, fadeOut);
  if (alpha <= 0) return;

  g.save();
  g.globalAlpha = alpha;

  const py = 1530; // Safe zone above Instagram bottom UI
  g.font = font(42, 800, 'disp');
  g.textAlign = 'center';
  g.textBaseline = 'middle';

  // Backdrop pill
  const tw = g.measureText(current.text).width;
  const pw = Math.min(W - 80, tw + 60), ph = 76;
  g.fillStyle = 'rgba(6, 9, 16, 0.94)';
  g.shadowColor = 'rgba(0, 0, 0, 0.75)';
  g.shadowBlur = 30;
  g.shadowOffsetY = 12;
  rr(g, W / 2 - pw / 2, py - ph / 2, pw, ph, ph / 2);
  g.fill();
  g.shadowColor = 'transparent';

  // Glowing border
  g.strokeStyle = 'rgba(255, 255, 255, 0.22)';
  g.lineWidth = 1.5;
  rr(g, W / 2 - pw / 2 + 0.5, py - ph / 2 + 0.5, pw - 1, ph - 1, ph / 2);
  g.stroke();

  g.fillStyle = '#FFFFFF';
  g.fillText(current.text, W / 2, py);

  g.restore();
}

// ───────────────────────── Floating 3D iPhone Mockup ─────────────────────────
function drawPhoneFrame(g, cx, cy, w, h, t) {
  const r = 56;
  g.save();
  // Titanium Drop Shadow
  g.shadowColor = 'rgba(0, 0, 0, 0.88)';
  g.shadowBlur = 70;
  g.shadowOffsetY = 32;
  g.fillStyle = '#080C14';
  rr(g, cx - w / 2, cy - h / 2, w, h, r);
  g.fill();
  g.shadowColor = 'transparent';

  // Titanium Outer Bezel
  const grBezel = g.createLinearGradient(0, cy - h / 2, 0, cy + h / 2);
  grBezel.addColorStop(0, '#263147');
  grBezel.addColorStop(0.5, '#121824');
  grBezel.addColorStop(1, '#1A2234');
  g.fillStyle = grBezel;
  rr(g, cx - w / 2, cy - h / 2, w, h, r);
  g.fill();

  // Specular Border
  g.strokeStyle = 'rgba(255, 255, 255, 0.25)';
  g.lineWidth = 1.5;
  rr(g, cx - w / 2 + 0.5, cy - h / 2 + 0.5, w - 1, h - 1, r);
  g.stroke();

  // OLED Glass Screen
  const border = 14;
  const sw = w - border * 2, sh = h - border * 2;
  const sx = cx - sw / 2, sy = cy - sh / 2;
  g.fillStyle = '#030509';
  rr(g, sx, sy, sw, sh, r - border / 2);
  g.fill();

  // Dynamic Island
  const diW = 160, diH = 36;
  const diX = cx - diW / 2, diY = sy + 18;
  g.fillStyle = '#000000';
  rr(g, diX, diY, diW, diH, diH / 2);
  g.fill();
  g.strokeStyle = 'rgba(255, 255, 255, 0.12)';
  g.lineWidth = 1;
  rr(g, diX + 0.5, diY + 0.5, diW - 1, diH - 1, diH / 2);
  g.stroke();

  // Status Bar Indicator
  const micPulse = (Math.sin(t * 8) + 1) * 0.5;
  g.fillStyle = PAL.accent;
  g.shadowColor = rgba(PAL.accent, 0.8);
  g.shadowBlur = 8;
  g.beginPath();
  g.arc(diX + diW - 22, diY + diH / 2, 3.5 + micPulse * 1.5, 0, TAU);
  g.fill();
  g.shadowColor = 'transparent';

  // Status Bar Time
  g.font = font(16, 600, 'mono');
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'left';
  g.fillText("11:42", sx + 32, diY + diH / 2 + 5);

  // Status Bar 5G & Battery
  g.textAlign = 'right';
  g.fillText("5G ▮▮▮ 98%", sx + sw - 32, diY + diH / 2 + 5);

  g.restore();
  return [sx, sy, sw, sh];
}

// ───────────────────────── Dynamic Neural Orb ─────────────────────────
function drawNeuralOrb(g, cx, cy, r, t, color = PAL.accent) {
  g.save();
  glow(g, cx, cy, r * 2.2, color, 0.35);

  for (let ring = 1; ring <= 3; ring++) {
    const ringR = r * 0.6 + ((t * 24 + ring * 25) % (r * 0.9));
    const ringA = clamp(1.0 - (ringR - r * 0.6) / (r * 0.9));
    g.beginPath();
    g.arc(cx, cy, ringR, 0, TAU);
    g.strokeStyle = rgba(color, ringA * 0.4);
    g.lineWidth = 2;
    g.stroke();
  }

  g.beginPath();
  const points = 72;
  for (let i = 0; i <= points; i++) {
    const angle = (i / points) * TAU;
    const wave1 = Math.sin(angle * 4 + t * 6) * (r * 0.12);
    const wave2 = Math.cos(angle * 7 - t * 8) * (r * 0.08);
    const rad = r * 0.75 + wave1 + wave2;
    const px = cx + Math.cos(angle) * rad;
    const py = cy + Math.sin(angle) * rad;
    if (i === 0) g.moveTo(px, py);
    else g.lineTo(px, py);
  }
  g.closePath();
  const gr = g.createRadialGradient(cx, cy, 0, cx, cy, r);
  gr.addColorStop(0, '#FFFFFF');
  gr.addColorStop(0.4, color);
  gr.addColorStop(1, rgba(color, 0.2));
  g.fillStyle = gr;
  g.shadowColor = rgba(color, 0.9);
  g.shadowBlur = 24;
  g.fill();
  g.shadowColor = 'transparent';

  g.restore();
}

// ───────────────────────── MASTER VERTICAL REEL RENDERER ─────────────────────────
export function renderReel(g, t) {
  g.save();
  // Near-black OLED vertical stage
  E.bg(g, { lift: 1.1, cyanGlow: 2.0, t, cx: W / 2, cy: H * 0.45 });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.65 });
  cinematicBokeh(g, t, 36);

  // TOP BRAND HEADER
  const topY = 245;
  g.textAlign = 'center';
  pill(g, W / 2 - 165, topY - 40, "🔴 CLOSER AI · EXPLANATORY DOCUMENTARY", {
    color: PAL.accent, bg: 'rgba(0, 229, 255, 0.14)', px: 13
  });

  g.font = font(42, 800, 'disp');
  g.fillStyle = '#FFFFFF';
  g.fillText("CLOSER AI", W / 2, topY + 25);

  g.font = font(14, 700, 'mono');
  g.fillStyle = PAL.dim;
  g.fillText("SPEED-TO-LEAD REAL ESTATE DOCUMENTARY", W / 2, topY + 54);

  // CENTER 3D IPHONE MOCKUP
  const phoneW = 780, phoneH = 1080;
  const phoneX = W / 2, phoneY = H / 2 - 40;
  const [sx, sy, sw, sh] = drawPhoneFrame(g, phoneX, phoneY, phoneW, phoneH, t);

  // IN-SCREEN PHONE CONTENT CLIPPED
  g.save();
  g.beginPath();
  rr(g, sx, sy, sw, sh, 42);
  g.clip();

  if (t < 8.0) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 1: THE ₹5 LAKH AD SPEND BURNER (Meta & Google Ads Burn)
    // ═════════════════════════════════════════════════════════════════════════
    const localT = t;
    const cardY = sy + 140;
    glow(g, phoneX, cardY + 160, 320, PAL.red, 0.35);

    // Header badge
    pill(g, sx + 50, cardY + 20, "● META & GOOGLE ADS CAMPAIGN", {
      color: PAL.gold, bg: 'rgba(251, 191, 36, 0.15)', px: 12
    });

    // Big Spend Box
    panel3D(g, sx + 40, cardY + 60, sw - 80, 160, { r: 20, fill: PAL.surf, stroke: 'rgba(251, 191, 36, 0.3)' });
    g.font = font(13, 700, 'mono');
    g.fillStyle = PAL.dim;
    g.textAlign = 'left';
    g.fillText("MONTHLY BUILDER AD BUDGET SPENT", sx + 70, cardY + 105);

    const spendCount = Math.min(500000, Math.floor(localT * 110000));
    g.font = font(44, 800, 'disp');
    g.fillStyle = PAL.gold;
    g.fillText(`₹${spendCount.toLocaleString('en-IN')}`, sx + 70, cardY + 165);

    // The Lead Funnel Evaporation Graph
    const funnelY = cardY + 245;
    panel3D(g, sx + 40, funnelY, sw - 80, 290, { r: 20, fill: '#14080A', stroke: PAL.red, shadow: 1.4 });

    g.font = font(14, 700, 'mono');
    g.fillStyle = PAL.red;
    g.fillText("⚠️ 70% HIGH-INTENT LEADS EVAPORATE", sx + 70, funnelY + 45);

    // Funnel bars
    // 1. Leads Generated
    g.fillStyle = PAL.mute;
    g.font = font(12, 600, 'mono');
    g.fillText("142 FORM SUBMISSIONS", sx + 70, funnelY + 85);
    g.fillStyle = PAL.emerald;
    rr(g, sx + 70, funnelY + 95, sw - 140, 20, 6);
    g.fill();

    // 2. Churned / Abandoned Leads
    g.fillStyle = PAL.red;
    g.fillText("99 LEADS GONE IN 4-6 HR DELAY (70%)", sx + 70, funnelY + 145);
    const lostBarW = (sw - 140) * 0.70;
    rr(g, sx + 70, funnelY + 155, lostBarW, 20, 6);
    g.fill();

    // 3. Contacted
    g.fillStyle = PAL.dim;
    g.fillText("ONLY 43 EVER CONTACTED", sx + 70, funnelY + 205);
    rr(g, sx + 70, funnelY + 215, (sw - 140) * 0.30, 20, 6);
    g.fill();

    // Floating burning currency indicators
    for (let i = 0; i < 5; i++) {
      const px = sx + 100 + ((i * 127 + localT * 50) % (sw - 200));
      const py = funnelY + 250 - ((localT * 40 + i * 35) % 180);
      const pa = clamp(1.0 - (funnelY + 250 - py) / 180);
      g.font = font(18, 700, 'disp');
      g.fillStyle = rgba(PAL.red, pa * 0.7);
      g.fillText("₹", px, py);
    }

  } else if (t < 19.8) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 2: JSM CHENNAI & THE 5-MINUTE CLIFF (Ground Truth)
    // ═════════════════════════════════════════════════════════════════════════
    const localT = t - 8.0;
    const cardY = sy + 130;
    glow(g, phoneX, cardY + 220, 360, PAL.red, 0.4);

    // Ground Truth Badge
    pill(g, sx + 50, cardY + 20, "📍 JSM INTEGRATED SERVICES · CHENNAI", {
      color: PAL.accent, bg: PAL.surf2, px: 12
    });

    // Midnight Inquiry Card
    panel3D(g, sx + 40, cardY + 60, sw - 80, 160, { r: 20, fill: PAL.surf, stroke: PAL.red });
    g.font = font(13, 700, 'mono');
    g.fillStyle = PAL.red;
    g.textAlign = 'left';
    g.fillText("🌙 11:42 PM NOCTURNAL INQUIRY", sx + 70, cardY + 95);

    g.font = font(26, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("₹15.5 Cr Beachfront Villa", sx + 70, cardY + 135);
    g.font = font(14, 500, 'ui');
    g.fillStyle = PAL.dim;
    g.fillText("Sales Team: Offline / Asleep (4-6 hr response delay)", sx + 70, cardY + 175);

    // The Interactive 5-Minute Cliff Chart
    const chartY = cardY + 245;
    panel3D(g, sx + 40, chartY, sw - 80, 330, { r: 20, fill: '#0A0E17', stroke: PAL.line });

    g.font = font(13, 700, 'mono');
    g.fillStyle = PAL.accent;
    g.fillText("THE 5-MINUTE CLIFF (LEAD INTENT DECAY)", sx + 70, chartY + 38);

    // Draw Chart Axes & Curve
    const cx0 = sx + 80, cy0 = chartY + 260;
    const cw = sw - 160, ch = 190;

    // Grid lines
    g.strokeStyle = 'rgba(255,255,255,0.06)';
    g.lineWidth = 1;
    for (let gy = 0; gy <= 4; gy++) {
      const yy = cy0 - (gy / 4) * ch;
      g.beginPath();
      g.moveTo(cx0, yy);
      g.lineTo(cx0 + cw, yy);
      g.stroke();
    }

    // Points: (0m, 100%), (5m, 21%), (15m, 8%), (30m, 3%), (4h, 1%)
    const points = [
      { x: cx0, y: cy0 - ch },
      { x: cx0 + cw * 0.22, y: cy0 - ch * 0.21 },
      { x: cx0 + cw * 0.45, y: cy0 - ch * 0.08 },
      { x: cx0 + cw * 0.72, y: cy0 - ch * 0.03 },
      { x: cx0 + cw, y: cy0 - ch * 0.01 }
    ];

    // Animated path drawing
    const drawProg = clamp(localT / 2.5);
    g.beginPath();
    g.moveTo(points[0].x, points[0].y);
    for (let p = 1; p < points.length; p++) {
      const prev = points[p - 1];
      const cur = points[p];
      const curX = lerp(prev.x, cur.x, clamp((drawProg - (p - 1) * 0.25) / 0.25));
      const curY = lerp(prev.y, cur.y, clamp((drawProg - (p - 1) * 0.25) / 0.25));
      g.lineTo(curX, curY);
      if (drawProg < p * 0.25) break;
    }
    g.strokeStyle = PAL.red;
    g.lineWidth = 4;
    g.stroke();

    // Area Fill
    g.lineTo(cx0 + cw * Math.min(1.0, drawProg), cy0);
    g.lineTo(cx0, cy0);
    g.closePath();
    const grArea = g.createLinearGradient(0, cy0 - ch, 0, cy0);
    grArea.addColorStop(0, 'rgba(255, 69, 69, 0.35)');
    grArea.addColorStop(1, 'rgba(255, 69, 69, 0.0)');
    g.fillStyle = grArea;
    g.fill();

    // Cliff Callout Marker at 5m
    if (drawProg > 0.3) {
      const mX = cx0 + cw * 0.22, mY = cy0 - ch * 0.21;
      glow(g, mX, mY, 30, PAL.red, 0.8);
      g.beginPath();
      g.arc(mX, mY, 6, 0, TAU);
      g.fillStyle = '#FFFFFF';
      g.fill();

      pill(g, mX - 85, mY - 45, "📉 -391% DROP AT 5 MIN", {
        color: '#FFFFFF', bg: PAL.red, px: 10
      });
    }

    // X Axis Labels
    g.font = font(11, 600, 'mono');
    g.fillStyle = PAL.mute;
    g.fillText("0m", cx0 - 5, cy0 + 20);
    g.fillText("5 min", cx0 + cw * 0.22 - 15, cy0 + 20);
    g.fillText("30 min", cx0 + cw * 0.65 - 15, cy0 + 20);
    g.fillText("4 hrs", cx0 + cw - 20, cy0 + 20);

  } else if (t < 26.0) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 3: CLOSER AI AUTONOMOUS SPEED-TO-CALL (0.08s Dial)
    // ═════════════════════════════════════════════════════════════════════════
    const localT = t - 19.8;
    const cardY = sy + 150;
    glow(g, phoneX, cardY + 220, 380, PAL.accent, 0.45);

    // Center Dynamic Neural Orb
    drawNeuralOrb(g, phoneX, cardY + 160, 90, t, PAL.accent);

    g.textAlign = 'center';
    pill(g, phoneX - 170, cardY + 285, "● AUTONOMOUS DIAL IN 0.08 SECONDS", {
      color: PAL.accent, bg: 'rgba(0, 229, 255, 0.15)', px: 12
    });

    g.font = font(34, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("Sub-45s Inbound Callback", phoneX, cardY + 355);

    g.font = font(14, 600, 'mono');
    g.fillStyle = PAL.lime;
    g.fillText("OPUS-HD 48kHz · LATENCY: 238ms · 200 OK", phoneX, cardY + 395);

    drawWaveform(g, phoneX, cardY + 460, sw - 120, 50, t, { active: true, color: PAL.accent, energy: 1.3 });

  } else if (t < 35.1) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 4A: MAYA (ENGLISH NRI CLOSER)
    // ═════════════════════════════════════════════════════════════════════════
    const cardY = sy + 130;
    drawNeuralOrb(g, phoneX, cardY + 120, 80, t, PAL.accent);

    g.textAlign = 'center';
    pill(g, phoneX - 150, cardY + 230, "NEURAL CLOSER: MAYA (ENGLISH)", {
      color: PAL.accent, bg: PAL.surf2, px: 12
    });

    g.font = font(28, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("Sea-Facing Penthouse Desk", phoneX, cardY + 285);

    pill(g, phoneX - 120, cardY + 305, "⭐ 8.4% PROJECTED RENTAL YIELD", {
      color: PAL.lime, bg: 'rgba(183, 243, 74, 0.15)', px: 11
    });

    // Live Voice Transcript Panel
    panel3D(g, sx + 40, cardY + 360, sw - 80, 160, { r: 18, fill: PAL.surf2, stroke: 'rgba(0, 229, 255, 0.3)' });
    g.font = font(12, 700, 'mono');
    g.fillStyle = PAL.accent;
    g.fillText("LIVE VOICE TRANSCRIPT", phoneX, cardY + 395);

    g.font = font(19, 500, 'ui');
    g.fillStyle = '#FFFFFF';
    g.fillText('"Projected rental yield is 8.4%.', phoneX, cardY + 435);
    g.fillText('Sunday 11 AM is reserved for your visit."', phoneX, cardY + 470);

    drawWaveform(g, phoneX, cardY + 560, sw - 120, 48, t, { active: true, color: PAL.accent, energy: 1.2 });

  } else if (t < 41.1) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 4B: PALLAVI (TAMIL CLOSER)
    // ═════════════════════════════════════════════════════════════════════════
    const cardY = sy + 130;
    drawNeuralOrb(g, phoneX, cardY + 120, 80, t, PAL.emerald);

    g.textAlign = 'center';
    pill(g, phoneX - 155, cardY + 230, "NEURAL CLOSER: PALLAVI (TAMIL)", {
      color: PAL.emerald, bg: PAL.surf2, px: 12
    });

    g.font = font(28, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("Chennai & ECR Luxury Desk", phoneX, cardY + 285);

    pill(g, phoneX - 110, cardY + 305, "🛡️ TN-RERA VERIFIED PROMPT", {
      color: PAL.emerald, bg: 'rgba(16, 185, 129, 0.15)', px: 11
    });

    panel3D(g, sx + 40, cardY + 360, sw - 80, 160, { r: 18, fill: PAL.surf2, stroke: 'rgba(16, 185, 129, 0.3)' });
    g.font = font(12, 700, 'mono');
    g.fillStyle = PAL.emerald;
    g.fillText("நேரடி அழைப்பு (LIVE TAMIL CALL)", phoneX, cardY + 395);

    g.font = font(18, 500, 'ui');
    g.fillStyle = '#FFFFFF';
    g.fillText('"வணக்கம் சார், சென்னை ECR வில்லாவின்', phoneX, cardY + 435);
    g.fillText('RERA அப்ரூவல் விவரங்கள் தயார்."', phoneX, cardY + 470);

    drawWaveform(g, phoneX, cardY + 560, sw - 120, 48, t, { active: true, color: PAL.emerald, energy: 1.2 });

  } else if (t < 46.2) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 4C: SWATI (HINDI CLOSER)
    // ═════════════════════════════════════════════════════════════════════════
    const cardY = sy + 130;
    drawNeuralOrb(g, phoneX, cardY + 120, 80, t, PAL.purple);

    g.textAlign = 'center';
    pill(g, phoneX - 150, cardY + 230, "NEURAL CLOSER: SWATI (HINDI)", {
      color: PAL.purple, bg: PAL.surf2, px: 12
    });

    g.font = font(28, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("Delhi NCR Luxury Desk", phoneX, cardY + 285);

    pill(g, phoneX - 130, cardY + 305, "🗓️ SUNDAY 11:00 AM CONFIRMED", {
      color: PAL.purple, bg: 'rgba(192, 132, 252, 0.15)', px: 11
    });

    panel3D(g, sx + 40, cardY + 360, sw - 80, 160, { r: 18, fill: PAL.surf2, stroke: 'rgba(192, 132, 252, 0.3)' });
    g.font = font(12, 700, 'mono');
    g.fillStyle = PAL.purple;
    g.fillText("लाइव कॉल (LIVE HINDI CALL)", phoneX, cardY + 395);

    g.font = font(18, 500, 'ui');
    g.fillStyle = '#FFFFFF';
    g.fillText('"नमस्ते सर, गोल्फ कोर्स रोड पेंटहाउस के लिए', phoneX, cardY + 435);
    g.fillText('आपकी विज़िट बुक कर दी है।"', phoneX, cardY + 470);

    drawWaveform(g, phoneX, cardY + 560, sw - 120, 48, t, { active: true, color: PAL.purple, energy: 1.2 });

  } else if (t < 52.5) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 5: DUAL-CHANNEL SPEED-TO-WALKTHROUGH (Live WhatsApp Push)
    // ═════════════════════════════════════════════════════════════════════════
    const localT = t - 46.2;
    const cardY = sy + 130;
    glow(g, phoneX, cardY + 240, 360, PAL.emerald, 0.4);

    // WhatsApp Interface Header
    panel3D(g, sx + 30, cardY, sw - 60, 68, { r: 16, fill: '#005D4B', stroke: '#128C7E' });
    g.textAlign = 'left';
    g.font = font(18, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("💬 WhatsApp · CLOSER AI Verified", sx + 55, cardY + 38);
    g.font = font(11, 500, 'mono');
    g.fillStyle = '#A3E635';
    g.fillText("ONLINE NOW · SYNCHRONIZED CO-BROWSING", sx + 55, cardY + 56);

    // Chat Message Bubble 1
    const bub1Y = cardY + 90;
    panel3D(g, sx + 40, bub1Y, sw - 100, 110, { r: 18, fill: '#005C4B', stroke: 'rgba(255,255,255,0.1)' });
    g.font = font(15, 500, 'ui');
    g.fillStyle = '#FFFFFF';
    g.fillText("Good evening Mr. Daniels! While we are on call,", sx + 60, bub1Y + 35);
    g.fillText("here are the verified RERA floor plans and your pass:", sx + 60, bub1Y + 62);
    g.font = font(11, 600, 'mono');
    g.fillStyle = '#86EFAC';
    g.textAlign = 'right';
    g.fillText("11:43 PM ✓✓", sx + sw - 80, bub1Y + 95);

    // Attachment Card 1: Architectural PDF
    const att1Y = cardY + 220;
    panel3D(g, sx + 40, att1Y, sw - 100, 95, { r: 16, fill: PAL.surf, stroke: PAL.emerald });
    g.textAlign = 'left';
    g.font = font(32, 700, 'disp');
    g.fillText("📄", sx + 60, att1Y + 58);
    g.font = font(15, 700, 'ui');
    g.fillStyle = '#FFFFFF';
    g.fillText("ECR_Villa_Architectural_FloorPlan.pdf", sx + 115, att1Y + 40);
    g.font = font(12, 500, 'mono');
    g.fillStyle = PAL.dim;
    g.fillText("4.8 MB · Tamil Nadu RERA Approved", sx + 115, att1Y + 68);

    // Attachment Card 2: Apple Wallet VIP Pass
    const att2Y = cardY + 335;
    panel3D(g, sx + 40, att2Y, sw - 100, 95, { r: 16, fill: PAL.surf, stroke: PAL.accent });
    g.font = font(32, 700, 'disp');
    g.fillText("🎟️", sx + 60, att2Y + 58);
    g.font = font(15, 700, 'ui');
    g.fillStyle = '#FFFFFF';
    g.fillText("VIP_Site_Visit_Sunday_11AM.pkpass", sx + 115, att2Y + 40);
    g.font = font(12, 500, 'mono');
    g.fillStyle = PAL.dim;
    g.fillText("Apple Wallet & Google Calendar Lock", sx + 115, att2Y + 68);

    pill(g, phoneX - 165, cardY + 455, "⚡ DUAL-CHANNEL SPEED-TO-WALKTHROUGH", {
      color: PAL.lime, bg: PAL.surf2, px: 12
    });

  } else if (t < 58.8) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 6: THE UNIT ECONOMICS SHOWDOWN (₹1.55)
    // ═════════════════════════════════════════════════════════════════════════
    const localT = t - 52.5;
    const cardY = sy + 130;
    glow(g, phoneX, cardY + 200, 380, PAL.lime, 0.45);

    const prog = clamp(localT / 1.0);
    const numStr = rollingNumber("₹1.55", prog, 77);

    g.textAlign = 'center';
    g.font = font(15, 700, 'mono');
    g.fillStyle = PAL.dim;
    g.fillText("UNIT ECONOMICS PER QUALIFIED CALL", phoneX, cardY + 50);

    g.font = font(112, 800, 'disp');
    g.fillStyle = PAL.lime;
    g.shadowColor = rgba(PAL.lime, 0.75);
    g.shadowBlur = 32;
    g.fillText(numStr, phoneX, cardY + 175);
    g.shadowColor = 'transparent';

    pill(g, phoneX - 110, cardY + 205, "⚡ 99.3% COST REDUCTION", {
      color: PAL.lime, bg: 'rgba(183, 243, 74, 0.18)', px: 12
    });

    // Showdown Battle Box
    panel3D(g, sx + 40, cardY + 260, sw - 80, 240, { r: 20, fill: PAL.surf, stroke: PAL.line });

    // Row 1: Human Call Center
    g.font = font(14, 700, 'mono');
    g.fillStyle = PAL.red;
    g.textAlign = 'left';
    g.fillText("HUMAN BROKERAGE CALL CENTER", sx + 70, cardY + 305);
    g.font = font(22, 700, 'disp');
    g.fillText("₹220 / Lead", sx + 70, cardY + 338);
    g.font = font(12, 500, 'ui');
    g.fillStyle = PAL.dim;
    g.fillText("4-6 hr delay · 40% monthly churn · Nocturnal dark", sx + 70, cardY + 365);

    // Separator line
    g.strokeStyle = PAL.line;
    g.beginPath();
    g.moveTo(sx + 70, cardY + 385);
    g.lineTo(sx + sw - 70, cardY + 385);
    g.stroke();

    // Row 2: CLOSER AI
    g.font = font(14, 700, 'mono');
    g.fillStyle = PAL.lime;
    g.fillText("CLOSER AI AUTONOMOUS GATEKEEPER", sx + 70, cardY + 420);
    g.font = font(22, 700, 'disp');
    g.fillText("₹1.55 / Call", sx + 70, cardY + 453);
    g.font = font(12, 500, 'ui');
    g.fillStyle = PAL.dim;
    g.fillText("0.08s speed · 24/7/365 · Zero hallucination", sx + 70, cardY + 480);

  } else {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 7: THE VIRAL COMMENT MAGNET (Comment "CLOSER")
    // ═════════════════════════════════════════════════════════════════════════
    const localT = t - 58.8;
    const cardY = sy + 130;
    glow(g, phoneX, cardY + 220, 420, PAL.gold, 0.45);

    // Glowing Golden Border Card
    panel3D(g, sx + 30, cardY, sw - 60, 480, { r: 24, fill: '#14120A', stroke: PAL.gold, shadow: 1.6 });

    // Comment Magnet Header
    g.textAlign = 'center';
    pill(g, phoneX - 165, cardY + 40, "🔥 INSTAGRAM EXCLUSIVE BLUEPRINT", {
      color: PAL.gold, bg: 'rgba(251, 191, 36, 0.2)', px: 13
    });

    g.font = font(38, 800, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("Comment 'CLOSER'", phoneX, cardY + 115);
    g.fillText("Below For The Guide", phoneX, cardY + 165);

    g.font = font(15, 600, 'ui');
    g.fillStyle = PAL.gold;
    g.fillText("Instant DM Delivery of our Full Blueprint:", phoneX, cardY + 215);

    // Checklist of Deliverables
    const perks = [
      "✅ Luxury Real Estate AI System Architecture",
      "✅ High-Ticket Objection Handling Scripts",
      "✅ Live Developer Demo Phone Number"
    ];
    perks.forEach((p, idx) => {
      const py = cardY + 265 + idx * 48;
      g.textAlign = 'left';
      g.font = font(14, 600, 'ui');
      g.fillStyle = '#FFFFFF';
      g.fillText(p, sx + 60, py);
    });

    // Pulsing Animated Comment Arrow
    const arrowBounce = Math.sin(t * 8) * 8;
    g.textAlign = 'center';
    g.font = font(32, 700, 'disp');
    g.fillStyle = PAL.accent;
    g.fillText("👇", phoneX, cardY + 425 + arrowBounce);

    g.font = font(14, 700, 'mono');
    g.fillStyle = PAL.lime;
    g.fillText("DROP 'CLOSER' IN COMMENTS NOW", phoneX, cardY + 455);
  }

  g.restore(); // end phone screen clip

  // ───────────────────────── BOTTOM VIRAL CTA BAR ─────────────────────────
  const ctaY = 1690;
  const ctaW = W - 100, ctaH = 80;
  panel3D(g, W / 2 - ctaW / 2, ctaY - ctaH / 2, ctaW, ctaH, {
    r: ctaH / 2, fill: 'rgba(251, 191, 36, 0.16)', stroke: PAL.gold, shadow: 1.4
  });

  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.font = font(26, 800, 'mono');
  g.fillStyle = PAL.gold;
  g.fillText("💬 COMMENT 'CLOSER' FOR FREE BLUEPRINT ➔", W / 2, ctaY);

  // Subtitle Captions
  renderReelCaptions(g, t);

  vignette(g, 0.45);
  g.restore();
}
