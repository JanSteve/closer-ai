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
export const DUR = 78.0;

const CUT_TIMES = [0.0, 10.8, 17.8, 25.4, 34.2, 42.4, 48.9, 55.1, 62.3, 70.4];

export function reelSubs() {
  return [
    // Scene 0: Universal Need & Agency Excel Trap (0.0s – 10.8s)
    { t0: 0.4, t1: 3.0, text: "Every Single Business", tag: "UNIVERSAL TELECALLER" },
    { t0: 3.0, t1: 5.5, text: "Needs Telecallers Today!", tag: "UNIVERSAL TELECALLER" },
    { t0: 5.5, t1: 8.0, text: "Clinics · Solar · Agencies · Real Estate", tag: "ANY INDUSTRY" },
    { t0: 8.0, t1: 10.6, text: "Lakhs Wasted On Dead Leads!", tag: "AD SPEND TRAP" },

    // Scene 1: The Angry Prospect Hangup (10.8s – 17.8s)
    { t0: 10.8, t1: 13.0, text: "Human Telecallers Call Hours Late", tag: "THE PROBLEM" },
    { t0: 13.0, t1: 15.4, text: 'Customer: "WHO ARE YOU?!"', tag: "LOST SALE" },
    { t0: 15.4, t1: 17.6, text: '"I Never Filled Any Form!" 💥', tag: "LOST SALE" },

    // Scene 2: 5-Minute Intent Collapse (17.8s – 25.4s)
    { t0: 17.8, t1: 20.4, text: "After 5 Minutes, Intent Collapses", tag: "HARVARD STUDY" },
    { t0: 20.4, t1: 22.8, text: "Human Telecallers Sleep At Night...", tag: "NIGHT LOSS" },
    { t0: 22.8, t1: 25.2, text: "...While Ad Budgets Burn 24/7!", tag: "BUDGET BURN" },

    // Scene 3: CLOSER AI Hero Reveal (25.4s – 34.2s)
    { t0: 25.4, t1: 28.0, text: "Meet CLOSER AI", tag: "AI BREAKTHROUGH" },
    { t0: 28.0, t1: 30.8, text: "Autonomous Telecalling For ANY Business", tag: "UNIVERSAL ENGINE" },
    { t0: 30.8, t1: 34.0, text: "Instant Dials In Under 45 Seconds!", tag: "< 45s SPEED" },

    // Scene 4A: Maya Luxury Real Estate (34.2s – 42.4s)
    { t0: 34.2, t1: 38.0, text: 'Maya: "Villa Brochure On WhatsApp"', tag: "REAL ESTATE" },
    { t0: 38.0, t1: 42.2, text: '"Sunday 11 AM Site Visit Locked!"', tag: "REAL ESTATE" },

    // Scene 4B: Dr. Pallavi Dental Clinic (42.4s – 48.9s)
    { t0: 42.4, t1: 45.4, text: 'Pallavi: "வணக்கம் மேடம்..."', tag: "HEALTHCARE CLINIC" },
    { t0: 45.4, t1: 48.7, text: '"டென்டல் அப்பாயின்மென்ட் கன்பார்ம்!"', tag: "TAMIL AI CALL" },

    // Scene 4C: Swati Rooftop Solar (48.9s – 55.1s)
    { t0: 48.9, t1: 51.8, text: 'Swati: "5kW सोलर कोटेशन..."', tag: "SOLAR ENERGY" },
    { t0: 51.8, t1: 54.9, text: '"व्हाट्सएप पर तुरंत भेज दिया है!"', tag: "HINDI AI CALL" },

    // Scene 5: WhatsApp Instant Delivery (55.1s – 62.3s)
    { t0: 55.1, t1: 58.4, text: "Clinics · Solar · EdTech · Real Estate", tag: "MULTI-SECTOR DISPATCH" },
    { t0: 58.4, t1: 62.1, text: "Drops Quotes & Passes On WhatsApp!", tag: "INSTANT SYNC" },

    // Scene 6: Unit Economics Showdown (62.3s – 70.4s)
    { t0: 62.3, t1: 65.8, text: "Human Telecaller: ₹220 Per Lead", tag: "BPO EXPENSE" },
    { t0: 65.8, t1: 70.2, text: "CLOSER AI: ₹1.55 With Zero Payroll!", tag: "⚡ 99.3% SAVINGS" },

    // Scene 7: Viral Comment Magnet CTA (70.4s – 78.0s)
    { t0: 70.4, t1: 73.6, text: "Run ANY Business Needing Calls?", tag: "UNIVERSAL SETUP" },
    { t0: 73.6, t1: 77.5, text: 'Comment "CLOSER" For Free Playbook 👇', tag: "GET THE STACK" }
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
  pill(g, W / 2 - 195, topY - 40, "🔴 CLOSER AI · UNIVERSAL TELECALLER", {
    color: PAL.accent, bg: 'rgba(0, 229, 255, 0.14)', px: 14
  });

  g.font = font(42, 800, 'disp');
  g.fillStyle = '#FFFFFF';
  g.fillText("CLOSER AI", W / 2, topY + 25);

  g.font = font(14, 700, 'mono');
  g.fillStyle = PAL.dim;
  g.fillText("AUTONOMOUS TELECALLING ENGINE FOR ANY BUSINESS", W / 2, topY + 54);

  // CENTER 3D IPHONE MOCKUP
  const phoneW = 780, phoneH = 1080;
  const phoneX = W / 2, phoneY = H / 2 - 40;
  const [sx, sy, sw, sh] = drawPhoneFrame(g, phoneX, phoneY, phoneW, phoneH, t);

  g.save();
  g.beginPath();
  rr(g, sx, sy, sw, sh, 42);
  g.clip();

  if (t < 10.8) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 1: THE UNIVERSAL BUSINESS LEAD NIGHTMARE (0.0s – 10.8s)
    // ═════════════════════════════════════════════════════════════════════════
    drawAgencyExcelScene(g, phoneX, sy + 380, t);

    pill(g, phoneX - 175, sy + 100, "💸 EVERY BUSINESS NEEDS TELECALLERS", {
      color: PAL.gold, bg: 'rgba(251, 191, 36, 0.2)', px: 12
    });

    g.font = font(30, 800, 'disp');
    g.fillStyle = '#FFFFFF';
    g.textAlign = 'center';
    g.fillText("Lakhs Spent on Meta Ads.", phoneX, sy + 165);
    g.font = font(22, 700, 'disp');
    g.fillStyle = PAL.dim;
    g.fillText("Clinics · Solar · Agencies · Real Estate", phoneX, sy + 205);

  } else if (t < 17.8) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 2: THE YELLING CUSTOMER HANGUP (10.8s – 17.8s)
    // ═════════════════════════════════════════════════════════════════════════
    drawYellingCustomerScene(g, phoneX, sy + 380, t);

    pill(g, phoneX - 165, sy + 100, "📞 THE 4-HOUR FOLLOWUP FAILURE", {
      color: PAL.red, bg: 'rgba(239, 68, 68, 0.2)', px: 12
    });

    g.font = font(30, 800, 'disp');
    g.fillStyle = '#FFFFFF';
    g.textAlign = 'center';
    g.fillText("Human Staff Calls Hours Late.", phoneX, sy + 165);
    g.fillText("Angry Prospect Slams Phone.", phoneX, sy + 205);

  } else if (t < 25.4) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 3: THE 5-MINUTE BRAIN FREEZE & NIGHT LOSS (17.8s – 25.4s)
    // ═════════════════════════════════════════════════════════════════════════
    drawBrainFreezeScene(g, phoneX, sy + 380, t);

    pill(g, phoneX - 150, sy + 100, "⏱️ 5-MINUTE INTENT COLLAPSE", {
      color: PAL.accent, bg: 'rgba(0, 229, 255, 0.2)', px: 12
    });

    g.font = font(28, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.textAlign = 'center';
    g.fillText("Intent Evaporates in 5 Min.", phoneX, sy + 165);
    g.fillText("Budgets Burn While Staff Sleeps.", phoneX, sy + 205);

  } else if (t < 34.2) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 4: CLOSER AI AUTONOMOUS SPEED-TO-CALL (25.4s – 34.2s)
    // ═════════════════════════════════════════════════════════════════════════
    drawNeuralOrb(g, phoneX, sy + 270, 95, t, PAL.accent);

    g.textAlign = 'center';
    pill(g, phoneX - 190, sy + 430, "● UNIVERSAL TELECALLER FOR ANY BUSINESS", {
      color: PAL.accent, bg: 'rgba(0, 229, 255, 0.15)', px: 12
    });

    g.font = font(32, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("Instant Dials In Under 45s", phoneX, sy + 495);

    g.font = font(14, 600, 'mono');
    g.fillStyle = PAL.lime;
    g.fillText("CLINICS · SOLAR · REAL ESTATE · EDTECH · B2B", phoneX, sy + 535);

    drawWaveform(g, phoneX, sy + 620, sw - 120, 50, t, { active: true, color: PAL.accent, energy: 1.3 });

  } else if (t < 42.4) {
    // ═════════════════════════════════════════════════════════════════════════
    // SECTOR 1: REAL ESTATE (Maya - English) (34.2s – 42.4s)
    // ═════════════════════════════════════════════════════════════════════════
    drawMultiSectorScene(g, phoneX, sy + 380, t);

    drawWaveform(g, phoneX, sy + 700, sw - 120, 48, t, { active: true, color: PAL.accent, energy: 1.2 });

  } else if (t < 48.9) {
    // ═════════════════════════════════════════════════════════════════════════
    // SECTOR 2: HEALTHCARE & CLINICS (Pallavi - Tamil) (42.4s – 48.9s)
    // ═════════════════════════════════════════════════════════════════════════
    drawMultiSectorScene(g, phoneX, sy + 380, t);

    drawWaveform(g, phoneX, sy + 700, sw - 120, 48, t, { active: true, color: PAL.emerald, energy: 1.2 });

  } else if (t < 55.1) {
    // ═════════════════════════════════════════════════════════════════════════
    // SECTOR 3: SOLAR & CLEAN ENERGY (Swati - Hindi) (48.9s – 55.1s)
    // ═════════════════════════════════════════════════════════════════════════
    drawMultiSectorScene(g, phoneX, sy + 380, t);

    drawWaveform(g, phoneX, sy + 700, sw - 120, 48, t, { active: true, color: PAL.purple, energy: 1.2 });

  } else if (t < 62.3) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 5: DUAL-CHANNEL MULTI-SECTOR WHATSAPP PUSH (55.1s – 62.3s)
    // ═════════════════════════════════════════════════════════════════════════
    drawMultiSectorWhatsApp(g, phoneX, sy + 380, t);

    pill(g, phoneX - 175, sy + 100, "⚡ MULTI-SECTOR WHATSAPP DELIVERY", {
      color: PAL.lime, bg: PAL.surf2, px: 12
    });

  } else if (t < 70.4) {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 6: THE UNIT ECONOMICS SHOWDOWN (62.3s – 70.4s)
    // ═════════════════════════════════════════════════════════════════════════
    const localT = t - 62.3;
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
    g.fillText("HUMAN TELECALLERS / BPO BENCH", sx + 70, cardY + 305);
    g.font = font(22, 700, 'disp');
    g.fillText("₹220 / Lead Reached", sx + 70, cardY + 338);
    g.font = font(12, 500, 'ui');
    g.fillStyle = PAL.dim;
    g.fillText("₹25k salary · slow dials · night dropoff", sx + 70, cardY + 365);

    g.strokeStyle = PAL.line;
    g.beginPath();
    g.moveTo(sx + 70, cardY + 385);
    g.lineTo(sx + sw - 70, cardY + 385);
    g.stroke();

    g.font = font(14, 700, 'mono');
    g.fillStyle = PAL.lime;
    g.fillText("CLOSER AI UNIVERSAL TELECALLER", sx + 70, cardY + 420);
    g.font = font(22, 700, 'disp');
    g.fillText("₹1.55 / Autonomous Call", sx + 70, cardY + 453);
    g.font = font(12, 500, 'ui');
    g.fillStyle = PAL.dim;
    g.fillText("0.08s speed · Clinics · Solar · Real Estate · EdTech", sx + 70, cardY + 480);

  } else {
    // ═════════════════════════════════════════════════════════════════════════
    // SCENE 7: THE UNIVERSAL VIRAL COMMENT MAGNET (70.4s – 78.0s)
    // ═════════════════════════════════════════════════════════════════════════
    const localT = t - 70.4;
    const cardY = sy + 130;
    glow(g, phoneX, cardY + 220, 420, PAL.gold, 0.45);

    panel3D(g, sx + 30, cardY, sw - 60, 480, { r: 24, fill: '#14120A', stroke: PAL.gold, shadow: 1.6 });

    g.textAlign = 'center';
    pill(g, phoneX - 180, cardY + 40, "🔥 UNIVERSAL TELECALLER PLAYBOOK", {
      color: PAL.gold, bg: 'rgba(251, 191, 36, 0.2)', px: 13
    });

    g.font = font(38, 800, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("Comment 'CLOSER'", phoneX, cardY + 115);
    g.fillText("For Your Business Stack", phoneX, cardY + 165);

    g.font = font(15, 600, 'ui');
    g.fillStyle = PAL.gold;
    g.fillText("Free Instant DM Delivery:", phoneX, cardY + 215);

    const perks = [
      "✅ Universal Telecaller Stacks (Clinics, Solar, Real Estate)",
      "✅ Make.com / CRM Webhook Auto-Dial Workflows",
      "✅ Zero-Payroll Setup & Live Demo Test Access"
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

  renderHormoziCaptions(g, t, W, H, reelSubs());

  // BOTTOM VIRAL CTA BAR (Shown during CTA Scene 7 in Safe Zone)
  if (t >= 70.4) {
    const ctaY = 1530;
    const ctaW = W - 120, ctaH = 74;
    panel3D(g, W / 2 - ctaW / 2, ctaY - ctaH / 2, ctaW, ctaH, {
      r: ctaH / 2, fill: 'rgba(251, 191, 36, 0.22)', stroke: PAL.gold, shadow: 1.4
    });

    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.font = font(22, 800, 'mono');
    g.fillStyle = PAL.gold;
    g.fillText("💬 COMMENT 'CLOSER' FOR YOUR BUSINESS PLAYBOOK ➔", W / 2, ctaY);
  }

  drawCutTransition(g, t, CUT_TIMES, W, H);
  drawScanlines(g, W, H);

  vignette(g, 0.45);
  g.restore();
}
