// reel.js — CLOSER AI Official Multi-Sector Instagram Reel Engine (9:16 Vertical 1080x1920)
// Universal High-Retention Documentary Explainer for Indian Businesses & Agencies.
// Multi-Sector: Real Estate, Healthcare & Clinics, Solar & Home Reno, High-Ticket Services.
// Features: Agency Excel Nightmare, Yelling Customer Hangup, 5-Min Brain Freeze,
// Multi-Sector Closers, 3-Attachment WhatsApp Push, ₹1.55 Economics, Viral Comment Magnet.

import * as E from './engine.js';
import {
  drawAgencyExcelScene,
  drawYellingCustomerScene,
  drawBrainFreezeScene,
  drawMultiSectorScene,
  drawMultiSectorWhatsApp,
  renderHormoziCaptions,
  drawCutTransition,
  drawScanlines
} from './characters.js';

const { PAL, clamp, lerp, seg, ss, eo, ei, eio, back, spring, font, rr, glow,
        panel3D, pill, drawWaveform, drawRadialDial, rollingNumber, lightSweep,
        vignette, cinematicBokeh, anamorphicFlare, perspective3D, buf, TAU, rgba } = E;

export const W = 1080, H = 1920;
export const DUR = 68.0;

const CUT_TIMES = [0.0, 7.8, 14.0, 19.8, 26.5, 34.7, 41.1, 47.2, 53.0, 59.2];

export function reelSubs() {
  return [
    { t0: 0.4, t1: 7.6, text: "In India, every business hires an agency.", highlight: "hires an agency" },
    { t0: 7.8, t1: 13.8, text: 'Customer: "WHO ARE YOU?! I NEVER FILLED A FORM."', highlight: "WHO ARE YOU" },
    { t0: 14.0, t1: 19.6, text: "After 5 minutes, customer intent drops off a cliff.", highlight: "5-Minute Cliff" },
    { t0: 19.8, t1: 26.4, text: "CLOSER AI dials the lead in 0.08 seconds.", highlight: "0.08 seconds" },
    { t0: 26.5, t1: 34.5, text: 'Maya: "Villa brochure in WhatsApp. Sunday 11 AM locked."', highlight: "Real Estate" },
    { t0: 34.7, t1: 41.0, text: 'Pallavi: "டென்டல் அப்பாயின்மென்ட் நாளை மாலை 5 மணிக்கு கன்பார்ம்."', highlight: "Healthcare Clinic" },
    { t0: 41.1, t1: 47.1, text: 'Swati: "रूफटॉप सोलर का कोटेशन व्हाट्सएप पर भेज दिया है।"', highlight: "Solar & Interiors" },
    { t0: 47.2, t1: 52.8, text: "Drops quote, clinic pass, or floor plan in WhatsApp.", highlight: "WhatsApp Sync" },
    { t0: 53.0, t1: 59.1, text: "Human telecaller: ₹220. CLOSER AI: ₹1.55.", highlight: "₹1.55 / call" },
    { t0: 59.2, t1: 67.0, text: 'Comment "CLOSER" for the multi-sector prompt stack!', highlight: 'Comment "CLOSER"' }
  ];
}

function drawPhoneFrame(g, cx, cy, w, h, t) {
  const r = 56;
  g.save();
  g.shadowColor = 'rgba(0, 0, 0, 0.9)';
  g.shadowBlur = 75;
  g.shadowOffsetY = 34;
  g.fillStyle = '#080C14';
  rr(g, cx - w / 2, cy - h / 2, w, h, r);
  g.fill();
  g.shadowColor = 'transparent';

  const grBezel = g.createLinearGradient(0, cy - h / 2, 0, cy + h / 2);
  grBezel.addColorStop(0, '#263147');
  grBezel.addColorStop(0.5, '#121824');
  grBezel.addColorStop(1, '#1A2234');
  g.fillStyle = grBezel;
  rr(g, cx - w / 2, cy - h / 2, w, h, r);
  g.fill();

  g.strokeStyle = 'rgba(255, 255, 255, 0.28)';
  g.lineWidth = 1.5;
  rr(g, cx - w / 2 + 0.5, cy - h / 2 + 0.5, w - 1, h - 1, r);
  g.stroke();

  const border = 14;
  const sw = w - border * 2, sh = h - border * 2;
  const sx = cx - sw / 2, sy = cy - sh / 2;
  g.fillStyle = '#030509';
  rr(g, sx, sy, sw, sh, r - border / 2);
  g.fill();

  const diW = 160, diH = 36;
  const diX = cx - diW / 2, diY = sy + 18;
  g.fillStyle = '#000000';
  rr(g, diX, diY, diW, diH, diH / 2);
  g.fill();
  g.strokeStyle = 'rgba(255, 255, 255, 0.12)';
  g.lineWidth = 1;
  rr(g, diX + 0.5, diY + 0.5, diW - 1, diH - 1, diH / 2);
  g.stroke();

  const micPulse = (Math.sin(t * 8) + 1) * 0.5;
  g.fillStyle = PAL.accent;
  g.shadowColor = rgba(PAL.accent, 0.8);
  g.shadowBlur = 8;
  g.beginPath();
  g.arc(diX + diW - 22, diY + diH / 2, 3.5 + micPulse * 1.5, 0, TAU);
  g.fill();
  g.shadowColor = 'transparent';

  g.font = font(16, 600, 'mono');
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'left';
  g.fillText("11:42", sx + 32, diY + diH / 2 + 5);

  g.textAlign = 'right';
  g.fillText("5G ▮▮▮ 98%", sx + sw - 32, diY + diH / 2 + 5);

  g.restore();
  return [sx, sy, sw, sh];
}

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

export function renderReel(g, t) {
  g.save();

  // 1. CALCULATE SNAP-ZOOMS & SHAKE (MrBeast 1.4s Retention Formula)
  let camScale = 1.0;
  let shakeX = 0, shakeY = 0;

  for (const ct of CUT_TIMES) {
    const dt = t - ct;
    if (dt >= 0 && dt <= 0.35) {
      camScale += 0.12 * Math.exp(-dt / 0.16) * Math.sin(dt * 18);
      const s = 7.0 * Math.exp(-dt / 0.14);
      shakeX = Math.sin(dt * 55) * s;
      shakeY = Math.cos(dt * 45) * s;
      break;
    }
  }

  g.translate(W / 2 + shakeX, H / 2 + shakeY);
  g.scale(camScale, camScale);
  g.translate(-W / 2, -H / 2);

  E.bg(g, { lift: 1.1, cyanGlow: 2.0, t, cx: W / 2, cy: H * 0.45 });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.65 });
  cinematicBokeh(g, t, 36);

  // TOP BRAND HEADER
  const topY = 240;
  g.textAlign = 'center';
  pill(g, W / 2 - 165, topY - 40, "🔴 CLOSER AI · MULTI-SECTOR ENGINE", {
    color: PAL.accent, bg: 'rgba(0, 229, 255, 0.14)', px: 13
  });

  g.font = font(42, 800, 'disp');
  g.fillStyle = '#FFFFFF';
  g.fillText("CLOSER AI", W / 2, topY + 25);

  g.font = font(14, 700, 'mono');
  g.fillStyle = PAL.dim;
  g.fillText("HIGH-TICKET SPEED-TO-LEAD DOCUMENTARY", W / 2, topY + 54);

  // CENTER 3D IPHONE MOCKUP
  const phoneW = 780, phoneH = 1080;
  const phoneX = W / 2, phoneY = H / 2 - 40;
  const [sx, sy, sw, sh] = drawPhoneFrame(g, phoneX, phoneY, phoneW, phoneH, t);

  g.save();
  g.beginPath();
  rr(g, sx, sy, sw, sh, 42);
  g.clip();

  if (t < 7.8) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 1: THE AGENCY INVOICE & EXCEL SHEET NIGHTMARE (0.0s – 7.8s)
    // ═════════════════════════════════════════════════════════════════════════
    drawAgencyExcelScene(g, phoneX, sy + 380, t);

    pill(g, phoneX - 160, sy + 100, "💸 THE INDIAN AGENCY PARADOX", {
      color: PAL.gold, bg: 'rgba(251, 191, 36, 0.2)', px: 12
    });

    g.font = font(32, 800, 'disp');
    g.fillStyle = '#FFFFFF';
    g.textAlign = 'center';
    g.fillText("Lakhs Spent on Ads.", phoneX, sy + 165);
    g.fillText("500 Dead Leads in Excel.", phoneX, sy + 205);

  } else if (t < 14.0) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 2: THE YELLING CUSTOMER HANGUP (7.8s – 14.0s)
    // ═════════════════════════════════════════════════════════════════════════
    drawYellingCustomerScene(g, phoneX, sy + 380, t);

    pill(g, phoneX - 165, sy + 100, "📞 THE 4-HOUR FOLLOWUP FAILURE", {
      color: PAL.red, bg: 'rgba(239, 68, 68, 0.2)', px: 12
    });

    g.font = font(30, 800, 'disp');
    g.fillStyle = '#FFFFFF';
    g.textAlign = 'center';
    g.fillText("Sales Calls 4 Hours Late.", phoneX, sy + 165);
    g.fillText("Customer Hangs Up.", phoneX, sy + 205);

  } else if (t < 19.8) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 3: THE 5-MINUTE BRAIN FREEZE (14.0s – 19.8s)
    // ═════════════════════════════════════════════════════════════════════════
    drawBrainFreezeScene(g, phoneX, sy + 380, t);

    pill(g, phoneX - 150, sy + 100, "⏱️ THE 5-MINUTE BRAIN FREEZE", {
      color: PAL.accent, bg: 'rgba(0, 229, 255, 0.2)', px: 12
    });

    g.font = font(28, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.textAlign = 'center';
    g.fillText("Intent Evaporates in 5 Min.", phoneX, sy + 165);
    g.fillText("By Morning, Money is Dead.", phoneX, sy + 205);

  } else if (t < 26.5) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 4: CLOSER AI AUTONOMOUS SPEED-TO-CALL (19.8s – 26.5s)
    // ═════════════════════════════════════════════════════════════════════════
    drawNeuralOrb(g, phoneX, sy + 270, 95, t, PAL.accent);

    g.textAlign = 'center';
    pill(g, phoneX - 170, sy + 430, "● AUTONOMOUS DIAL IN 0.08 SECONDS", {
      color: PAL.accent, bg: 'rgba(0, 229, 255, 0.15)', px: 12
    });

    g.font = font(34, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("Sub-45s Inbound Callback", phoneX, sy + 495);

    g.font = font(14, 600, 'mono');
    g.fillStyle = PAL.lime;
    g.fillText("ALL SECTORS · ZERO WAIT TIME · 200 OK", phoneX, sy + 535);

    drawWaveform(g, phoneX, sy + 620, sw - 120, 50, t, { active: true, color: PAL.accent, energy: 1.3 });

  } else if (t < 34.7) {
    // ═════════════════════════════════════════════════════════════════════════
    // SECTOR 1: REAL ESTATE (Maya - English) (26.5s – 34.7s)
    // ═════════════════════════════════════════════════════════════════════════
    drawMultiSectorScene(g, phoneX, sy + 380, t, 'realestate');

    drawWaveform(g, phoneX, sy + 700, sw - 120, 48, t, { active: true, color: PAL.accent, energy: 1.2 });

  } else if (t < 41.1) {
    // ═════════════════════════════════════════════════════════════════════════
    // SECTOR 2: HEALTHCARE & CLINICS (Pallavi - Tamil) (34.7s – 41.1s)
    // ═════════════════════════════════════════════════════════════════════════
    drawMultiSectorScene(g, phoneX, sy + 380, t, 'clinic');

    drawWaveform(g, phoneX, sy + 700, sw - 120, 48, t, { active: true, color: PAL.emerald, energy: 1.2 });

  } else if (t < 47.2) {
    // ═════════════════════════════════════════════════════════════════════════
    // SECTOR 3: SOLAR & INTERIORS (Swati - Hindi) (41.1s – 47.2s)
    // ═════════════════════════════════════════════════════════════════════════
    drawMultiSectorScene(g, phoneX, sy + 380, t, 'solar');

    drawWaveform(g, phoneX, sy + 700, sw - 120, 48, t, { active: true, color: PAL.purple, energy: 1.2 });

  } else if (t < 53.0) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 5: DUAL-CHANNEL 3-SECTOR WHATSAPP PUSH (47.2s – 53.0s)
    // ═════════════════════════════════════════════════════════════════════════
    drawMultiSectorWhatsApp(g, phoneX, sy + 380, t);

    pill(g, phoneX - 165, sy + 100, "⚡ SYNCHRONIZED WHATSAPP LOCK", {
      color: PAL.lime, bg: PAL.surf2, px: 12
    });

  } else if (t < 59.2) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 6: THE UNIT ECONOMICS SHOWDOWN (53.0s – 59.2s)
    // ═════════════════════════════════════════════════════════════════════════
    const localT = t - 53.0;
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

    panel3D(g, sx + 40, cardY + 260, sw - 80, 240, { r: 20, fill: PAL.surf, stroke: PAL.line });

    g.font = font(14, 700, 'mono');
    g.fillStyle = PAL.red;
    g.textAlign = 'left';
    g.fillText("HUMAN TELECALLERS / BPO", sx + 70, cardY + 305);
    g.font = font(22, 700, 'disp');
    g.fillText("₹220 / Lead", sx + 70, cardY + 338);
    g.font = font(12, 500, 'ui');
    g.fillStyle = PAL.dim;
    g.fillText("4-6 hr delay · 40% staff churn · High burn", sx + 70, cardY + 365);

    g.strokeStyle = PAL.line;
    g.beginPath();
    g.moveTo(sx + 70, cardY + 385);
    g.lineTo(sx + sw - 70, cardY + 385);
    g.stroke();

    g.font = font(14, 700, 'mono');
    g.fillStyle = PAL.lime;
    g.fillText("CLOSER AI MULTI-SECTOR ENGINE", sx + 70, cardY + 420);
    g.font = font(22, 700, 'disp');
    g.fillText("₹1.55 / Call", sx + 70, cardY + 453);
    g.font = font(12, 500, 'ui');
    g.fillStyle = PAL.dim;
    g.fillText("0.08s speed · Real Estate · Clinics · Solar · EdTech", sx + 70, cardY + 480);

  } else {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 7: THE MULTI-SECTOR VIRAL COMMENT MAGNET (59.2s – 68.0s)
    // ═════════════════════════════════════════════════════════════════════════
    const localT = t - 59.2;
    const cardY = sy + 130;
    glow(g, phoneX, cardY + 220, 420, PAL.gold, 0.45);

    panel3D(g, sx + 30, cardY, sw - 60, 480, { r: 24, fill: '#14120A', stroke: PAL.gold, shadow: 1.6 });

    g.textAlign = 'center';
    pill(g, phoneX - 165, cardY + 40, "🔥 MULTI-SECTOR AGENCY BLUEPRINT", {
      color: PAL.gold, bg: 'rgba(251, 191, 36, 0.2)', px: 13
    });

    g.font = font(38, 800, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("Comment 'CLOSER'", phoneX, cardY + 115);
    g.fillText("Below For The Stacks", phoneX, cardY + 165);

    g.font = font(15, 600, 'ui');
    g.fillStyle = PAL.gold;
    g.fillText("Free Instant DM Delivery:", phoneX, cardY + 215);

    const perks = [
      "✅ Multi-Sector Prompt Stacks (Clinics, Real Estate, Solar)",
      "✅ Agency White-Label Reseller Blueprint",
      "✅ Live Developer Demo Phone Number"
    ];
    perks.forEach((p, idx) => {
      const py = cardY + 265 + idx * 48;
      g.textAlign = 'left';
      g.font = font(14, 600, 'ui');
      g.fillStyle = '#FFFFFF';
      g.fillText(p, sx + 60, py);
    });

    const arrowBounce = Math.sin(t * 8) * 8;
    g.textAlign = 'center';
    g.font = font(36, 700, 'disp');
    g.fillStyle = PAL.accent;
    g.fillText("👇", phoneX, cardY + 425 + arrowBounce);

    g.font = font(14, 700, 'mono');
    g.fillStyle = PAL.lime;
    g.fillText("DROP 'CLOSER' IN COMMENTS NOW", phoneX, cardY + 458);
  }

  g.restore(); // end phone screen clip

  renderHormoziCaptions(g, t, W, H);

  // BOTTOM VIRAL CTA BAR
  const ctaY = 1690;
  const ctaW = W - 100, ctaH = 80;
  panel3D(g, W / 2 - ctaW / 2, ctaY - ctaH / 2, ctaW, ctaH, {
    r: ctaH / 2, fill: 'rgba(251, 191, 36, 0.16)', stroke: PAL.gold, shadow: 1.4
  });

  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.font = font(26, 800, 'mono');
  g.fillStyle = PAL.gold;
  g.fillText("💬 COMMENT 'CLOSER' FOR MULTI-SECTOR STACKS ➔", W / 2, ctaY);

  drawCutTransition(g, t, CUT_TIMES, W, H);
  drawScanlines(g, W, H);

  vignette(g, 0.45);
  g.restore();
}
