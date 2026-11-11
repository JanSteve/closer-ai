// characters.js — CLOSER AI Multi-Sector Character Animation & Visual FX Engine
// Procedural Canvas 2D character animation for ultra-high retention short-form video.
// Universal Multi-Sector Story: Agency Excel Nightmare, Yelling Customer Hangup,
// 5-Minute Brain Freeze, Multi-Sector Demos (Real Estate, Clinics, Solar), WhatsApp Lock, Viral CTA.

import { clamp, lerp, TAU, rgba } from './engine.js';

function rr(g, x, y, w, h, r) {
  g.beginPath();
  g.roundRect(x, y, w, h, Math.max(0, Math.min(r, w / 2, h / 2)));
}

function pill(g, x, y, text, opts = {}) {
  const { color = '#00E5FF', bg = 'rgba(0,229,255,0.15)', px = 12 } = opts;
  g.save();
  g.font = '700 13px JBMono, monospace';
  const tw = g.measureText(text).width;
  const pw = tw + px * 2, ph = 28;
  g.fillStyle = bg;
  rr(g, x, y, pw, ph, ph / 2);
  g.fill();
  g.strokeStyle = color;
  g.lineWidth = 1;
  rr(g, x + 0.5, y + 0.5, pw - 1, ph - 1, ph / 2);
  g.stroke();
  g.fillStyle = color;
  g.textAlign = 'left';
  g.textBaseline = 'middle';
  g.fillText(text, x + px, y + ph / 2);
  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. THE AGENCY & EXCEL SHEET NIGHTMARE (0.0s – 7.8s)
// Founder looking at agency report with ₹2,50,000 fee and 500 leads sheet
// ─────────────────────────────────────────────────────────────────────────────
export function drawAgencyExcelScene(g, cx, cy, t) {
  g.save();
  g.translate(cx, cy);

  // Agency Presentation Card
  const cardW = 460, cardH = 340;
  g.fillStyle = '#0B132B';
  rr(g, -cardW / 2, -160, cardW, cardH, 24);
  g.fill();
  g.strokeStyle = 'rgba(251, 191, 36, 0.4)';
  g.lineWidth = 2;
  g.stroke();

  pill(g, -190, -135, "💼 AD AGENCY MONTHLY INVOICE", {
    color: '#FBBF24', bg: 'rgba(251, 191, 36, 0.15)', px: 12
  });

  g.font = '800 32px InterTight, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'left';
  g.fillText("₹2,50,000 Spent", -190, -70);

  g.font = '500 14px Inter, sans-serif';
  g.fillStyle = '#94A3B8';
  g.fillText("Meta & Google Ads Campaign Retainer", -190, -42);

  // Excel Spreadsheet Graphic
  const xlY = 0;
  g.fillStyle = '#064E3B'; // Excel Dark Green
  rr(g, -190, xlY, 380, 140, 14);
  g.fill();
  g.strokeStyle = '#10B981';
  g.lineWidth = 1.5;
  g.stroke();

  // Excel icon badge
  g.fillStyle = '#10B981';
  rr(g, -175, xlY + 16, 36, 36, 8);
  g.fill();
  g.font = '900 20px InterTight, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'center';
  g.fillText("X", -157, xlY + 41);

  g.textAlign = 'left';
  g.font = '700 16px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.fillText("leads_sheet_may2026.xlsx", -125, xlY + 30);
  g.font = '600 12px JBMono, monospace';
  g.fillStyle = '#86EFAC';
  g.fillText("500 RAW FORM LEADS DELIVERED", -125, xlY + 48);

  // Spreadsheet Rows
  const rows = [
    { name: "Rahul S.", ph: "+91 98840*****", st: "UNREACHABLE" },
    { name: "Vikram M.", ph: "+91 99401*****", st: "NO ANSWER" }
  ];
  rows.forEach((r, idx) => {
    const ry = xlY + 70 + idx * 30;
    g.font = '500 12px Inter, sans-serif';
    g.fillStyle = '#E2E8F0';
    g.fillText(r.name, -170, ry + 15);
    g.font = '500 11px JBMono, monospace';
    g.fillStyle = '#94A3B8';
    g.fillText(r.ph, -70, ry + 15);
    g.fillStyle = '#EF4444';
    g.textAlign = 'right';
    g.fillText(r.st, 170, ry + 15);
    g.textAlign = 'left';
  });

  // Floating Rupee Notes flying out
  for (let i = 0; i < 6; i++) {
    const pProg = ((t * 1.8 + i * 0.16) % 1.0);
    const fx = -120 + i * 48 + Math.sin(t * 6 + i) * 15;
    const fy = 120 - pProg * 140;
    const fa = (1.0 - pProg) * 0.85;
    g.font = '700 16px InterTight, sans-serif';
    g.fillStyle = `rgba(239, 68, 68, ${fa})`;
    g.fillText("💸 ₹", fx, fy);
  }

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. THE YELLING CUSTOMER HANGUP SCENE (7.8s – 14.0s)
// Customer on phone yelling "Who are you?! I never filled a form!" + phone hangup click
// ─────────────────────────────────────────────────────────────────────────────
export function drawYellingCustomerScene(g, cx, cy, t) {
  g.save();
  g.translate(cx, cy);

  // Split Container Card
  const cardW = 460, cardH = 340;
  g.fillStyle = '#17060A';
  rr(g, -cardW / 2, -160, cardW, cardH, 24);
  g.fill();
  g.strokeStyle = '#EF4444';
  g.lineWidth = 2;
  g.stroke();

  pill(g, -190, -135, "⚠️ 4 HOURS LATER · THE PHONE CALL", {
    color: '#EF4444', bg: 'rgba(239, 68, 68, 0.18)', px: 12
  });

  // Animated Yelling Customer Avatar
  const custX = 0, custY = -10;
  // Head
  g.fillStyle = '#F59E0B';
  g.beginPath();
  g.ellipse(custX, custY, 54, 60, 0, 0, TAU);
  g.fill();

  // Furious eyebrows & angry eyes
  g.strokeStyle = '#0F172A';
  g.lineWidth = 4;
  g.beginPath();
  g.moveTo(custX - 35, custY - 18);
  g.lineTo(custX - 8, custY - 8);
  g.stroke();
  g.beginPath();
  g.moveTo(custX + 35, custY - 18);
  g.lineTo(custX + 8, custY - 8);
  g.stroke();

  // Eyes wide & enraged
  g.fillStyle = '#FFFFFF';
  g.beginPath();
  g.arc(custX - 18, custY - 6, 8, 0, TAU);
  g.fill();
  g.beginPath();
  g.arc(custX + 18, custY - 6, 8, 0, TAU);
  g.fill();
  g.fillStyle = '#0F172A';
  g.beginPath();
  g.arc(custX - 18, custY - 6, 4, 0, TAU);
  g.fill();
  g.beginPath();
  g.arc(custX + 18, custY - 6, 4, 0, TAU);
  g.fill();

  // Yelling Wide Open Mouth
  const yellWarp = Math.sin(t * 18) * 4;
  g.fillStyle = '#7F1D1D';
  g.beginPath();
  g.ellipse(custX, custY + 28, 24 + yellWarp, 18, 0, 0, TAU);
  g.fill();

  // Phone to Ear
  g.fillStyle = '#020617';
  rr(g, custX + 44, custY - 20, 24, 65, 8);
  g.fill();

  // Yelling Soundwaves
  for (let s = 1; s <= 3; s++) {
    const swR = 40 + s * 22;
    g.strokeStyle = `rgba(239, 68, 68, ${0.8 - s * 0.22})`;
    g.lineWidth = 3;
    g.beginPath();
    g.arc(custX, custY + 28, swR, -0.4, 0.4);
    g.stroke();
  }

  // Giant Speech Bubble: "WHO ARE YOU?!"
  const bubY = 95;
  g.fillStyle = '#0F172A';
  rr(g, -190, bubY, 380, 68, 16);
  g.fill();
  g.strokeStyle = '#EF4444';
  g.lineWidth = 1.5;
  g.stroke();

  g.font = '800 20px InterTight, sans-serif';
  g.fillStyle = '#EF4444';
  g.textAlign = 'center';
  g.fillText('"WHO ARE YOU?!', 0, bubY + 28);
  g.font = '600 13px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.fillText('I NEVER FILLED ANY FORM." [CLICK 📞]', 0, bubY + 52);

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. THE 5-MINUTE BRAIN FREEZE & INTENT COLLAPSE (14.0s – 19.8s)
// Brain timer counting down + Intent curve dropping -391%
// ─────────────────────────────────────────────────────────────────────────────
export function drawBrainFreezeScene(g, cx, cy, t) {
  g.save();
  g.translate(cx, cy);

  const cardW = 460, cardH = 340;
  g.fillStyle = '#0F172A';
  rr(g, -cardW / 2, -160, cardW, cardH, 24);
  g.fill();
  g.strokeStyle = 'rgba(0, 229, 255, 0.3)';
  g.lineWidth = 2;
  g.stroke();

  pill(g, -190, -135, "🧠 HARVARD & MIT BUYER INTENT STUDY", {
    color: '#00E5FF', bg: 'rgba(0, 229, 255, 0.15)', px: 12
  });

  // Big Timer
  const timerProg = clamp((t - 14.0) / 4.0);
  const secondsLeft = Math.max(0, Math.floor((1.0 - timerProg) * 300));
  const mins = Math.floor(secondsLeft / 60);
  const secs = secondsLeft % 60;
  const timeStr = `0${mins}:${secs < 10 ? '0' : ''}${secs}`;

  g.font = '800 48px JBMono, monospace';
  g.fillStyle = (timerProg > 0.4) ? '#EF4444' : '#FBBF24';
  g.textAlign = 'center';
  g.fillText(timeStr, 0, -60);

  g.font = '700 13px mono';
  g.fillStyle = '#94A3B8';
  g.fillText("CRITICAL RESPONSE WINDOW: 5 MINUTES", 0, -32);

  // Intent Falloff Bar Graph
  const barY = 0;
  g.fillStyle = 'rgba(255, 255, 255, 0.05)';
  rr(g, -180, barY, 360, 28, 8);
  g.fill();

  const intentW = Math.max(30, 360 * (1.0 - timerProg * 0.85));
  const grBar = g.createLinearGradient(-180, 0, 180, 0);
  grBar.addColorStop(0, '#10B981');
  grBar.addColorStop(0.3, '#FBBF24');
  grBar.addColorStop(1, '#EF4444');
  g.fillStyle = grBar;
  rr(g, -180, barY, intentW, 28, 8);
  g.fill();

  g.font = '800 13px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.fillText(`${Math.round(100 - timerProg * 82)}% INTENT`, 0, barY + 19);

  // Collapse Callout
  const boxY = barY + 45;
  g.fillStyle = 'rgba(239, 68, 68, 0.12)';
  rr(g, -180, boxY, 360, 68, 12);
  g.fill();
  g.strokeStyle = '#EF4444';
  g.lineWidth = 1;
  g.stroke();

  g.font = '800 18px InterTight, sans-serif';
  g.fillStyle = '#EF4444';
  g.fillText("📉 -391% QUALIFICATION COLLAPSE", 0, boxY + 28);
  g.font = '500 12px Inter, sans-serif';
  g.fillStyle = '#E2E8F0';
  g.fillText("After 30 mins, lead conversion probability is zero.", 0, boxY + 50);

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. MULTI-SECTOR DEMO CARDS (Real Estate, Clinics, Solar) (26.5s – 47.2s)
// ─────────────────────────────────────────────────────────────────────────────
export function drawMultiSectorScene(g, cx, cy, t, sector) {
  g.save();
  g.translate(cx, cy);

  let title = "LUXURY REAL ESTATE";
  let tag = "🏖️ ECR VILLA · CHENNAI";
  let mainColor = '#00E5FF';
  let icon = "🏢";
  let detail1 = "Maya (English NRI Desk)";
  let detail2 = "8.4% Projected Rental Yield Locked";
  let persona = 'maya';

  if (sector === 'clinic') {
    title = "HEALTHCARE & CLINICS";
    tag = "🩺 DENTAL IMPLANT & HAIR CLINIC";
    mainColor = '#10B981';
    icon = "🦷";
    detail1 = "Pallavi (Tamil Coastal Desk)";
    detail2 = "VIP Doctor Consultation Tomorrow 5 PM";
    persona = 'pallavi';
  } else if (sector === 'solar') {
    title = "SOLAR & HOME RENOVATION";
    tag = "☀️ ROOFTOP SOLAR & INTERIORS";
    mainColor = '#C084FC';
    icon = "⚡";
    detail1 = "Swati (Hindi NCR Desk)";
    detail2 = "5kW Subsidy Quotation Sent to WhatsApp";
    persona = 'swati';
  }

  // Header Pill
  pill(g, -170, -145, title, {
    color: mainColor, bg: 'rgba(15, 23, 42, 0.9)', px: 12
  });

  // Sector Showcase Card
  const cardW = 460, cardH = 340;
  g.fillStyle = '#0F172A';
  rr(g, -cardW / 2, -110, cardW, cardH, 24);
  g.fill();
  g.strokeStyle = mainColor;
  g.lineWidth = 2;
  g.stroke();

  // Big Sector Icon & Tag
  g.font = '48px sans-serif';
  g.textAlign = 'center';
  g.fillText(icon, 0, -45);

  g.font = '800 24px InterTight, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.fillText(tag, 0, 10);

  // Closer Details Box
  const dY = 35;
  g.fillStyle = 'rgba(255, 255, 255, 0.05)';
  rr(g, -190, dY, 380, 80, 14);
  g.fill();

  g.font = '700 14px Inter, sans-serif';
  g.fillStyle = mainColor;
  g.fillText(detail1, 0, dY + 30);
  g.font = '600 13px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.fillText(detail2, 0, dY + 56);

  // Live Carrier Sync Status
  pill(g, -125, dY + 95, "● LIVE CARRIER CONNECTED · 0.08s", {
    color: '#A3E635', bg: 'rgba(163, 230, 53, 0.15)', px: 12
  });

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. THE MULTI-SECTOR WHATSAPP PUSH (47.2s – 52.8s)
// ─────────────────────────────────────────────────────────────────────────────
export function drawMultiSectorWhatsApp(g, cx, cy, t) {
  g.save();
  g.translate(cx, cy);

  const cardW = 460, cardH = 340;
  g.fillStyle = '#005D4B'; // WhatsApp Header
  rr(g, -cardW / 2, -160, cardW, 60, 20);
  g.fill();

  g.font = '700 17px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'left';
  g.fillText("💬 WhatsApp · CLOSER AI Verified", -cardW / 2 + 25, -125);

  // Chat body
  g.fillStyle = '#0B141A'; // WhatsApp dark chat bg
  rr(g, -cardW / 2, -100, cardW, 280, 20);
  g.fill();

  // 3 Multi-Sector Attachments dropped dynamically
  const docs = [
    { icon: "📄", title: "ECR_Villa_FloorPlan.pdf", tag: "REAL ESTATE · RERA APPROVED" },
    { icon: "🩺", title: "Dr_Implant_Pass_Tomorrow.pkpass", tag: "HEALTHCARE · VIP CLINIC SLOT" },
    { icon: "⚡", title: "5kW_Solar_Subsidy_Quote.pdf", tag: "SOLAR · 3D AUDIT QUOTATION" }
  ];

  docs.forEach((d, idx) => {
    const dy = -85 + idx * 82;
    g.fillStyle = '#1F2C34';
    rr(g, -cardW / 2 + 20, dy, cardW - 40, 70, 12);
    g.fill();
    g.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    g.lineWidth = 1;
    g.stroke();

    g.font = '28px sans-serif';
    g.textAlign = 'left';
    g.fillText(d.icon, -cardW / 2 + 35, dy + 45);

    g.font = '700 13px Inter, sans-serif';
    g.fillStyle = '#FFFFFF';
    g.fillText(d.title, -cardW / 2 + 80, dy + 32);

    g.font = '600 10px JBMono, monospace';
    g.fillStyle = '#A3E635';
    g.fillText(d.tag, -cardW / 2 + 80, dy + 52);

    g.font = '600 10px JBMono, monospace';
    g.fillStyle = '#38BDF8';
    g.textAlign = 'right';
    g.fillText("✓✓ DELIVERED", cardW / 2 - 35, dy + 42);
  });

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. ALEX HORMOZI KARAOKE WORD-BY-WORD ANIMATED SUBTITLES
// ─────────────────────────────────────────────────────────────────────────────
export const HORMOZI_TRACKS = [
  {
    t0: 0.4, t1: 7.6, emoji: "📊",
    words: [
      { w: "In", dt: 0.0 },
      { w: "India,", dt: 0.3 },
      { w: "every", dt: 0.8 },
      { w: "business", dt: 1.2, e: "🏢" },
      { w: "hires", dt: 1.8 },
      { w: "an", dt: 2.1 },
      { w: "AGENCY.", dt: 2.4, e: "💼" },
      { w: "You", dt: 3.2 },
      { w: "spend", dt: 3.5 },
      { w: "LAKHS,", dt: 3.9, e: "💸" },
      { w: "they", dt: 4.8 },
      { w: "give", dt: 5.1 },
      { w: "an", dt: 5.4 },
      { w: "EXCEL", dt: 5.7, e: "📊" },
      { w: "sheet.", dt: 6.3 }
    ]
  },
  {
    t0: 7.8, t1: 13.8, emoji: "😡",
    words: [
      { w: "Sales", dt: 0.0 },
      { w: "calls", dt: 0.4, e: "📞" },
      { w: "hours", dt: 0.9 },
      { w: "later.", dt: 1.3 },
      { w: "Customer:", dt: 2.0 },
      { w: '"WHO', dt: 2.7, e: "❓" },
      { w: "ARE", dt: 3.1 },
      { w: 'YOU?!"', dt: 3.5, e: "😡" },
      { w: "And", dt: 4.3 },
      { w: "HANGS", dt: 4.7, e: "❌" },
      { w: "UP.", dt: 5.2 }
    ]
  },
  {
    t0: 14.0, t1: 19.6, emoji: "⏱️",
    words: [
      { w: "After", dt: 0.0 },
      { w: "5", dt: 0.4, e: "⏱️" },
      { w: "MINUTES,", dt: 0.8 },
      { w: "intent", dt: 1.6 },
      { w: "DROPS", dt: 2.1, e: "📉" },
      { w: "off", dt: 2.7 },
      { w: "a", dt: 3.0 },
      { w: "cliff.", dt: 3.3 },
      { w: "Ad", dt: 4.0 },
      { w: "spend", dt: 4.3 },
      { w: "is", dt: 4.7 },
      { w: "DEAD.", dt: 5.0, e: "💀" }
    ]
  },
  {
    t0: 19.8, t1: 26.4, emoji: "🤖",
    words: [
      { w: "Meet", dt: 0.0 },
      { w: "CLOSER", dt: 0.4, e: "⚡" },
      { w: "AI.", dt: 0.8 },
      { w: "Dials", dt: 1.5, e: "📞" },
      { w: "the", dt: 2.0 },
      { w: "lead", dt: 2.3 },
      { w: "in", dt: 2.7 },
      { w: "0.08", dt: 3.1, e: "🚀" },
      { w: "SECONDS.", dt: 3.8 }
    ]
  },
  {
    t0: 26.5, t1: 34.5, emoji: "🏖️",
    words: [
      { w: "Maya:", dt: 0.0, e: "🎙️" },
      { w: '"Villa', dt: 0.7, e: "🏖️" },
      { w: "brochure", dt: 1.3 },
      { w: "in", dt: 1.8 },
      { w: "WhatsApp.", dt: 2.2, e: "💬" },
      { w: "Sunday", dt: 3.4, e: "🗓️" },
      { w: "11", dt: 4.1 },
      { w: "AM", dt: 4.5 },
      { w: "is", dt: 5.0 },
      { w: 'LOCKED."', dt: 5.4, e: "🔒" }
    ]
  },
  {
    t0: 34.7, t1: 41.0, emoji: "🩺",
    words: [
      { w: "Pallavi:", dt: 0.0, e: "🎙️" },
      { w: "டென்டல்", dt: 0.8, e: "🦷" },
      { w: "இம்ப்ளான்ட்", dt: 1.5 },
      { w: "அப்பாயின்மென்ட்", dt: 2.2 },
      { w: "நாளை", dt: 3.2, e: "🗓️" },
      { w: "மாலை", dt: 3.8 },
      { w: "5", dt: 4.2 },
      { w: "மணிக்கு", dt: 4.6 },
      { w: "கன்பார்ம்.", dt: 5.2, e: "✅" }
    ]
  },
  {
    t0: 41.1, t1: 47.1, emoji: "☀️",
    words: [
      { w: "Swati:", dt: 0.0, e: "🎙️" },
      { w: "रूफटॉप", dt: 0.7, e: "☀️" },
      { w: "सोलर", dt: 1.2, e: "⚡" },
      { w: "कोटेशन", dt: 1.8 },
      { w: "व्हाट्सएप", dt: 2.6, e: "💬" },
      { w: "पर", dt: 3.2 },
      { w: "भेज", dt: 3.6 },
      { w: "दिया", dt: 4.0 },
      { w: "है।", dt: 4.4 }
    ]
  },
  {
    t0: 47.2, t1: 52.8, emoji: "💬",
    words: [
      { w: "Drops", dt: 0.0 },
      { w: "quote,", dt: 0.4, e: "📄" },
      { w: "clinic", dt: 1.0, e: "🩺" },
      { w: "pass,", dt: 1.5 },
      { w: "or", dt: 2.0 },
      { w: "floor", dt: 2.3 },
      { w: "plan", dt: 2.7 },
      { w: "in", dt: 3.1 },
      { w: "WHATSAPP.", dt: 3.5, e: "💬" }
    ]
  },
  {
    t0: 53.0, t1: 59.1, emoji: "💰",
    words: [
      { w: "Human:", dt: 0.0 },
      { w: "₹220.", dt: 0.5, e: "❌" },
      { w: "CLOSER", dt: 1.6 },
      { w: "AI:", dt: 2.1 },
      { w: "₹1.55", dt: 2.7, e: "⚡" },
      { w: "per", dt: 3.7 },
      { w: "call.", dt: 4.2 }
    ]
  },
  {
    t0: 59.2, t1: 67.0, emoji: "✍️",
    words: [
      { w: "Comment", dt: 0.0, e: "💬" },
      { w: '"CLOSER"', dt: 0.7, e: "🔥" },
      { w: "below", dt: 1.4, e: "👇" },
      { w: "for", dt: 1.9 },
      { w: "the", dt: 2.3 },
      { w: "multi-sector", dt: 2.7 },
      { w: "prompt", dt: 3.5 },
      { w: "stack!", dt: 4.0, e: "🚀" }
    ]
  }
];

export function renderHormoziCaptions(g, t, W, H) {
  const track = HORMOZI_TRACKS.find(tr => t >= tr.t0 && t <= tr.t1);
  if (!track) return;

  const relT = t - track.t0;
  const py = 1530; // Instagram Safe Zone

  g.save();
  g.textAlign = 'center';
  g.textBaseline = 'middle';

  let activeIdx = 0;
  for (let i = 0; i < track.words.length; i++) {
    if (relT >= track.words[i].dt) {
      activeIdx = i;
    }
  }

  const fullText = track.words.map(w => w.w).join(' ');
  g.font = '800 44px InterTight, sans-serif';
  const totalW = Math.min(W - 80, g.measureText(fullText).width + 80);
  const totalH = 80;

  g.fillStyle = 'rgba(4, 7, 14, 0.95)';
  g.shadowColor = 'rgba(0, 0, 0, 0.85)';
  g.shadowBlur = 32;
  g.shadowOffsetY = 12;
  rr(g, W / 2 - totalW / 2, py - totalH / 2, totalW, totalH, totalH / 2);
  g.fill();
  g.shadowColor = 'transparent';

  g.strokeStyle = 'rgba(255, 255, 255, 0.22)';
  g.lineWidth = 1.5;
  rr(g, W / 2 - totalW / 2 + 0.5, py - totalH / 2 + 0.5, totalW - 1, totalH - 1, totalH / 2);
  g.stroke();

  const spaceW = g.measureText(' ').width;
  let wordWidths = track.words.map(w => g.measureText(w.w).width);
  let totalWordsW = wordWidths.reduce((a, b) => a + b, 0) + spaceW * (track.words.length - 1);
  let startX = W / 2 - totalWordsW / 2;

  let curX = startX;
  for (let i = 0; i < track.words.length; i++) {
    const item = track.words[i];
    const wWidth = wordWidths[i];
    const wordCenter = curX + wWidth / 2;
    const isActive = (i === activeIdx);

    g.save();
    if (isActive) {
      const wordT = relT - item.dt;
      const bounceScale = (wordT < 0.18) ? (1.0 + Math.sin(wordT / 0.18 * Math.PI) * 0.25) : 1.05;

      g.translate(wordCenter, py);
      g.scale(bounceScale, bounceScale);

      if (item.e) {
        g.font = '32px sans-serif';
        g.fillText(item.e, 0, -48);
      }

      g.font = '900 45px InterTight, sans-serif';
      g.shadowColor = 'rgba(250, 204, 21, 0.85)';
      g.shadowBlur = 18;
      g.fillStyle = '#FACC15';
      g.fillText(item.w, 0, 0);
    } else {
      g.translate(wordCenter, py);
      g.font = '700 42px InterTight, sans-serif';
      g.fillStyle = (i < activeIdx) ? '#FFFFFF' : 'rgba(255, 255, 255, 0.45)';
      g.fillText(item.w, 0, 0);
    }
    g.restore();

    curX += wWidth + spaceW;
  }

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. CINEMATIC GLITCH & SCANLINES
// ─────────────────────────────────────────────────────────────────────────────
export function drawCutTransition(g, t, cutTimes = [], W, H) {
  for (const ct of cutTimes) {
    const dt = t - ct;
    if (dt >= 0 && dt <= 0.16) {
      const alpha = (1.0 - dt / 0.16) * 0.45;
      g.save();
      g.globalCompositeOperation = 'screen';
      g.fillStyle = `rgba(0, 229, 255, ${alpha})`;
      g.fillRect(-10, 0, W + 20, H);
      g.fillStyle = `rgba(239, 68, 68, ${alpha})`;
      g.fillRect(10, 0, W + 20, H);
      g.restore();
      break;
    }
  }
}

export function drawScanlines(g, W, H) {
  g.save();
  g.fillStyle = 'rgba(0, 0, 0, 0.05)';
  for (let y = 0; y < H; y += 4) {
    g.fillRect(0, y, W, 1.5);
  }
  g.restore();
}
