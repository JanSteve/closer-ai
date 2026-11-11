// reel.js — CLOSER AI Official Instagram Reel Engine (9:16 Vertical 1080x1920)
// Optimized for Instagram Reels, TikTok, and YouTube Shorts.
// Features: 3D Floating iPhone Mockup, Dynamic Island, Tri-Lingual Carousels,
// Kinetic Typography in Safe Zone, Rolling Number Mechanics, Anamorphic Flares.

import * as E from './engine.js';
const { PAL, clamp, lerp, seg, ss, eo, ei, eio, back, spring, font, rr, glow,
        panel3D, pill, drawWaveform, drawRadialDial, rollingNumber, lightSweep,
        vignette, cinematicBokeh, anamorphicFlare, perspective3D, buf, TAU, rgba } = E;

export const W = 1080, H = 1920;
export const DUR = 50.0;

// Subtitles timed for Instagram Reel (38-50s)
export function reelSubs() {
  return [
    { t0: 0.5, t1: 6.3, text: "At 11:42 PM, you're asleep.", highlight: "11:42 PM" },
    { t0: 6.5, t1: 11.0, text: "Your sales team is offline. Commission evaporates.", highlight: "Commission evaporates" },
    { t0: 11.2, t1: 15.8, text: "CLOSER AI calls the lead in 0.08 seconds.", highlight: "0.08 seconds" },
    { t0: 16.0, t1: 25.5, text: 'Maya: "Projected rental yield is 8.4%. Sunday visit reserved."', highlight: "8.4% yield" },
    { t0: 26.0, t1: 32.0, text: 'Pallavi: "சென்னை ECR வில்லாவின் RERA அப்ரூவல் விவரங்கள் தயார்."', highlight: "ECR வில்லா" },
    { t0: 32.5, t1: 39.5, text: 'Swati: "गोल्फ कोर्स रोड पेंटहाउस के लिए आपकी विज़िट बुक कर दी है।"', highlight: "विज़िट बुक" },
    { t0: 40.0, t1: 44.8, text: "₹1.55 per call. 99.3% cost reduction.", highlight: "₹1.55" },
    { t0: 45.0, t1: 49.5, text: "CLOSER AI. Tap link in bio to test live.", highlight: "Link in bio" }
  ];
}

// ───────────────────────── Instagram Safe-Zone Captions ─────────────────────────
function renderReelCaptions(g, t) {
  const current = reelSubs().find(s => t >= s.t0 && t <= s.t1);
  if (!current) return;

  const fadeIn = clamp((t - current.t0) / 0.18);
  const fadeOut = clamp((current.t1 - t) / 0.18);
  const alpha = Math.min(fadeIn, fadeOut);
  if (alpha <= 0) return;

  g.save();
  g.globalAlpha = alpha;

  const py = 1520; // Safe zone above Instagram bottom overlay
  g.font = font(42, 800, 'disp');
  g.textAlign = 'center';
  g.textBaseline = 'middle';

  // Backdrop pill
  const tw = g.measureText(current.text).width;
  const pw = Math.min(W - 80, tw + 60), ph = 74;
  g.fillStyle = 'rgba(6, 9, 16, 0.92)';
  g.shadowColor = 'rgba(0, 0, 0, 0.7)';
  g.shadowBlur = 28;
  g.shadowOffsetY = 10;
  rr(g, W / 2 - pw / 2, py - ph / 2, pw, ph, ph / 2);
  g.fill();
  g.shadowColor = 'transparent';

  // Border
  g.strokeStyle = 'rgba(255, 255, 255, 0.18)';
  g.lineWidth = 1.5;
  rr(g, W / 2 - pw / 2 + 0.5, py - ph / 2 + 0.5, pw - 1, ph - 1, ph / 2);
  g.stroke();

  // Highlight word in luminous lime/cyan
  g.fillStyle = '#FFFFFF';
  g.fillText(current.text, W / 2, py);

  g.restore();
}

// ───────────────────────── Floating 3D iPhone Mockup ─────────────────────────
function drawPhoneFrame(g, cx, cy, w, h, t) {
  const r = 56;
  // Exterior titanium drop shadow
  g.save();
  g.shadowColor = 'rgba(0, 0, 0, 0.85)';
  g.shadowBlur = 60;
  g.shadowOffsetY = 28;
  g.fillStyle = '#080C14';
  rr(g, cx - w / 2, cy - h / 2, w, h, r);
  g.fill();
  g.shadowColor = 'transparent';

  // Titanium Bezel
  const grBezel = g.createLinearGradient(0, cy - h / 2, 0, cy + h / 2);
  grBezel.addColorStop(0, '#263147');
  grBezel.addColorStop(0.5, '#121824');
  grBezel.addColorStop(1, '#1A2234');
  g.fillStyle = grBezel;
  rr(g, cx - w / 2, cy - h / 2, w, h, r);
  g.fill();

  // Outer 1px specular line
  g.strokeStyle = 'rgba(255, 255, 255, 0.25)';
  g.lineWidth = 1.5;
  rr(g, cx - w / 2 + 0.5, cy - h / 2 + 0.5, w - 1, h - 1, r);
  g.stroke();

  // Inner OLED Glass Screen
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
  g.strokeStyle = 'rgba(255, 255, 255, 0.1)';
  g.lineWidth = 1;
  rr(g, diX + 0.5, diY + 0.5, diW - 1, diH - 1, diH / 2);
  g.stroke();

  // Dynamic Island Cyan Mic Indicator
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

  // Multi-harmonic sine orb
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
  E.bg(g, { lift: 1.1, cyanGlow: 2.2, t, cx: W / 2, cy: H * 0.45 });
  E.grid(g, { ox: W / 2, oy: H / 2, alpha: 0.65 });
  cinematicBokeh(g, t, 36);

  // TOP SAFE BRAND HEADER
  const topY = 250;
  g.textAlign = 'center';
  pill(g, W / 2 - 160, topY - 40, "🔴 LIVE LEAD INBOUND · 11:42 PM", {
    color: PAL.red, bg: 'rgba(255, 69, 69, 0.15)', px: 13
  });

  g.font = font(42, 800, 'disp');
  g.fillStyle = '#FFFFFF';
  g.fillText("CLOSER AI", W / 2, topY + 25);

  g.font = font(14, 700, 'mono');
  g.fillStyle = PAL.accent;
  g.fillText("AUTONOMOUS VOICE CLOSING ENGINE", W / 2, topY + 55);

  // CENTER 3D IPHONE MOCKUP
  const phoneW = 760, phoneH = 1050;
  const phoneX = W / 2, phoneY = H / 2 - 40;
  const [sx, sy, sw, sh] = drawPhoneFrame(g, phoneX, phoneY, phoneW, phoneH, t);

  // IN-SCREEN PHONE CONTENT BASED ON TIME
  g.save();
  g.beginPath();
  rr(g, sx, sy, sw, sh, 42);
  g.clip();

  if (t < 6.5) {
    // SHOT 1: The 11:42 PM Lead Alert
    const cardY = sy + 180;
    glow(g, phoneX, cardY + 120, 280, PAL.red, 0.3);

    panel3D(g, sx + 40, cardY, sw - 80, 480, { r: 24, fill: PAL.surf, stroke: PAL.red, shadow: 1.4 });

    pill(g, sx + 70, cardY + 50, "● INBOUND WEB INQUIRY", { color: PAL.red, bg: 'rgba(255,69,69,0.15)', px: 12 });

    g.font = font(34, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.textAlign = 'left';
    g.fillText("₹15.5 Cr ($1.85M)", sx + 70, cardY + 130);
    g.fillText("Sea-Facing Penthouse", sx + 70, cardY + 175);

    g.font = font(16, 500, 'ui');
    g.fillStyle = PAL.dim;
    g.fillText("High-Intent NRI Buyer · Web Lead", sx + 70, cardY + 225);

    // Alert rows
    const rows = [
      { l: "HUMAN DESK", v: "OFFLINE / ASLEEP", c: PAL.red },
      { l: "CONVERSION RISK", v: "-391% DROP IN 5 MIN", c: PAL.red },
      { l: "TIME TO HUMAN SHIFT", v: "08h 17m DEAD AIR", c: '#F59E0B' }
    ];
    rows.forEach((r, idx) => {
      const ry = cardY + 280 + idx * 58;
      g.font = font(12, 700, 'mono');
      g.fillStyle = PAL.mute;
      g.fillText(r.l, sx + 70, ry);
      g.font = font(14, 700, 'mono');
      g.fillStyle = r.c;
      g.textAlign = 'right';
      g.fillText(r.v, sx + sw - 70, ry);
      g.textAlign = 'left';
    });

  } else if (t < 11.2) {
    // SHOT 2: Commission Evaporation
    const localT = t - 6.5;
    const cardY = sy + 200;
    glow(g, phoneX, cardY + 140, 320, PAL.red, 0.4);

    panel3D(g, sx + 40, cardY, sw - 80, 420, { r: 24, fill: '#140609', stroke: PAL.red, shadow: 1.5 });

    g.textAlign = 'center';
    g.font = font(15, 700, 'mono');
    g.fillStyle = PAL.red;
    g.fillText("⚠️ TRADITIONAL CALL CENTER FAILURE", phoneX, cardY + 70);

    g.font = font(34, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("While They Sleep,", phoneX, cardY + 135);
    g.fillText("Commission Evaporates.", phoneX, cardY + 180);

    const lostVal = Math.min(1420000, Math.floor(localT * 380000));
    g.font = font(14, 600, 'mono');
    g.fillStyle = PAL.dim;
    g.fillText("PIPELINE LOST TO NOCTURNAL SILENCE", phoneX, cardY + 250);

    g.font = font(56, 800, 'disp');
    g.fillStyle = PAL.red;
    g.fillText(`₹${lostVal.toLocaleString('en-IN')}`, phoneX, cardY + 330);

  } else if (t < 16.0) {
    // SHOT 3: Autonomous Neural Dial in 0.08s
    const localT = t - 11.2;
    const cardY = sy + 160;
    glow(g, phoneX, cardY + 220, 350, PAL.accent, 0.45);

    // Neural Orb Pulsing in Center
    drawNeuralOrb(g, phoneX, cardY + 160, 85, t, PAL.accent);

    g.textAlign = 'center';
    pill(g, phoneX - 165, cardY + 280, "● OUTBOUND DIAL IN 0.08 SECONDS", {
      color: PAL.accent, bg: 'rgba(0, 229, 255, 0.15)', px: 12
    });

    g.font = font(32, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("Carrier SIP Connected", phoneX, cardY + 345);

    g.font = font(14, 600, 'mono');
    g.fillStyle = PAL.lime;
    g.fillText("OPUS-HD 48kHz · LATENCY: 238ms · 200 OK", phoneX, cardY + 385);

    drawWaveform(g, phoneX, cardY + 450, sw - 120, 50, t, { active: true, color: PAL.accent, energy: 1.3 });

  } else if (t < 26.0) {
    // SHOT 4: Maya (English NRI Closer)
    const cardY = sy + 140;
    drawNeuralOrb(g, phoneX, cardY + 130, 80, t, PAL.accent);

    g.textAlign = 'center';
    pill(g, phoneX - 145, cardY + 240, "NEURAL CLOSER: MAYA (ENGLISH)", {
      color: PAL.accent, bg: PAL.surf2, px: 12
    });

    g.font = font(28, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("Sea-Facing Penthouse Desk", phoneX, cardY + 295);

    // Live call transcript box
    panel3D(g, sx + 40, cardY + 330, sw - 80, 160, { r: 18, fill: PAL.surf2, stroke: 'rgba(0, 229, 255, 0.3)' });
    g.font = font(12, 700, 'mono');
    g.fillStyle = PAL.accent;
    g.fillText("LIVE VOICE TRANSCRIPT", phoneX, cardY + 365);

    g.font = font(19, 500, 'ui');
    g.fillStyle = '#FFFFFF';
    g.fillText('"Projected rental yield is 8.4%.', phoneX, cardY + 405);
    g.fillText('Sunday 11 AM is reserved for your visit."', phoneX, cardY + 440);

    drawWaveform(g, phoneX, cardY + 540, sw - 120, 48, t, { active: true, color: PAL.accent, energy: 1.2 });

  } else if (t < 32.5) {
    // SHOT 5: Pallavi (Tamil Closer)
    const cardY = sy + 140;
    drawNeuralOrb(g, phoneX, cardY + 130, 80, t, PAL.emerald);

    g.textAlign = 'center';
    pill(g, phoneX - 150, cardY + 240, "NEURAL CLOSER: PALLAVI (TAMIL)", {
      color: PAL.emerald, bg: PAL.surf2, px: 12
    });

    g.font = font(28, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("Chennai & ECR Luxury Desk", phoneX, cardY + 295);

    panel3D(g, sx + 40, cardY + 330, sw - 80, 160, { r: 18, fill: PAL.surf2, stroke: 'rgba(16, 185, 129, 0.3)' });
    g.font = font(12, 700, 'mono');
    g.fillStyle = PAL.emerald;
    g.fillText("நேரடி அழைப்பு (LIVE TAMIL CALL)", phoneX, cardY + 365);

    g.font = font(18, 500, 'ui');
    g.fillStyle = '#FFFFFF';
    g.fillText('"வணக்கம் சார், சென்னை ECR வில்லாவின்', phoneX, cardY + 405);
    g.fillText('RERA அப்ரூவல் விவரங்கள் தயார்."', phoneX, cardY + 440);

    drawWaveform(g, phoneX, cardY + 540, sw - 120, 48, t, { active: true, color: PAL.emerald, energy: 1.2 });

  } else if (t < 40.0) {
    // SHOT 6: Swati (Hindi Closer)
    const cardY = sy + 140;
    drawNeuralOrb(g, phoneX, cardY + 130, 80, t, PAL.purple);

    g.textAlign = 'center';
    pill(g, phoneX - 145, cardY + 240, "NEURAL CLOSER: SWATI (HINDI)", {
      color: PAL.purple, bg: PAL.surf2, px: 12
    });

    g.font = font(28, 700, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("Delhi NCR Luxury Desk", phoneX, cardY + 295);

    panel3D(g, sx + 40, cardY + 330, sw - 80, 160, { r: 18, fill: PAL.surf2, stroke: 'rgba(192, 132, 252, 0.3)' });
    g.font = font(12, 700, 'mono');
    g.fillStyle = PAL.purple;
    g.fillText("लाइव कॉल (LIVE HINDI CALL)", phoneX, cardY + 365);

    g.font = font(18, 500, 'ui');
    g.fillStyle = '#FFFFFF';
    g.fillText('"नमस्ते सर, गोल्फ कोर्स रोड पेंटहाउस के लिए', phoneX, cardY + 405);
    g.fillText('आपकी फैमिली विज़िट बुक कर दी है।"', phoneX, cardY + 440);

    drawWaveform(g, phoneX, cardY + 540, sw - 120, 48, t, { active: true, color: PAL.purple, energy: 1.2 });

  } else if (t < 45.0) {
    // SHOT 7: Monumental Unit Economics (₹1.55)
    const localT = t - 40.0;
    const cardY = sy + 150;
    glow(g, phoneX, cardY + 180, 360, PAL.lime, 0.4);

    const prog = clamp(localT / 0.85);
    const numStr = rollingNumber("₹1.55", prog, 77);

    g.textAlign = 'center';
    g.font = font(15, 700, 'mono');
    g.fillStyle = PAL.dim;
    g.fillText("UNIT ECONOMICS PER CALL", phoneX, cardY + 60);

    g.font = font(110, 800, 'disp');
    g.fillStyle = PAL.lime;
    g.shadowColor = rgba(PAL.lime, 0.7);
    g.shadowBlur = 30;
    g.fillText(numStr, phoneX, cardY + 180);
    g.shadowColor = 'transparent';

    // Showdown Box
    panel3D(g, sx + 40, cardY + 240, sw - 80, 150, { r: 20, fill: PAL.surf, stroke: PAL.line });
    g.font = font(16, 700, 'mono');
    g.fillStyle = PAL.red;
    g.fillText("HUMAN CALLER: ₹220", phoneX, cardY + 290);
    g.fillStyle = PAL.mute;
    g.fillText("vs", phoneX, cardY + 325);
    g.font = font(20, 800, 'mono');
    g.fillStyle = PAL.lime;
    g.fillText("CLOSER AI: ₹1.55 (-99.3%)", phoneX, cardY + 360);

  } else {
    // SHOT 8: Hero Brand Lock & Launching Soon
    const localT = t - 45.0;
    const cardY = sy + 180;
    glow(g, phoneX, cardY + 160, 380, PAL.accent, 0.45);

    // 3D Hexagon/Cube Logo
    panel3D(g, phoneX - 55, cardY + 20, 110, 110, { r: 30, fill: PAL.surf2, stroke: PAL.accent, shadow: 1.5 });
    g.font = font(54, 800, 'disp');
    g.fillStyle = PAL.accent;
    g.textAlign = 'center';
    g.fillText("C", phoneX, cardY + 95);

    g.font = font(52, 800, 'disp');
    g.fillStyle = '#FFFFFF';
    g.fillText("CLOSER AI", phoneX, cardY + 200);

    g.font = font(16, 700, 'mono');
    g.fillStyle = PAL.accent;
    g.fillText("INTELLIGENCE DESIGNED TO EVOLVE", phoneX, cardY + 245);

    pill(g, phoneX - 160, cardY + 300, "● LAUNCHING SOON · USA & INDIA", {
      color: PAL.lime, bg: PAL.surf2, px: 13
    });
  }

  g.restore(); // end phone clip

  // BOTTOM SAFE CTA BANNER (Instagram Conversion Engine)
  const ctaY = 1680;
  const ctaW = W - 120, ctaH = 76;
  panel3D(g, W / 2 - ctaW / 2, ctaY - ctaH / 2, ctaW, ctaH, {
    r: ctaH / 2, fill: 'rgba(0, 229, 255, 0.14)', stroke: PAL.accent, shadow: 1.2
  });

  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.font = font(24, 800, 'mono');
  g.fillStyle = PAL.lime;
  g.fillText("🔥 TEST LIVE AI CLOSER ➔ LINK IN BIO", W / 2, ctaY);

  // Subtitle Captions
  renderReelCaptions(g, t);

  vignette(g, 0.45);
  g.restore();
}
