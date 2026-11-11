// characters.js — CLOSER AI High-Fidelity Character Animation & Visual Story Engine
// Fully animated 2D procedural characters with expressive faces, phoneme mouth flaps,
// hair styles, attire, gesturing hands, accessories, and cinematic visual props.
// Story: The Performance Agency Trap -> Angry Customer Hangup -> 5-Min Freeze ->
// Maya (Real Estate) -> Dr. Pallavi (Healthcare) -> Swati (Solar) -> WhatsApp Lock -> Viral CTA.

import { clamp, lerp, TAU, rgba } from './engine.js';

export function rr(g, x, y, w, h, r) {
  g.beginPath();
  g.roundRect(x, y, w, h, Math.max(0, Math.min(r, w / 2, h / 2)));
}

export function pill(g, x, y, text, opts = {}) {
  const { color = '#00E5FF', bg = 'rgba(0,229,255,0.15)', px = 14 } = opts;
  g.save();
  g.font = '700 13px JBMono, monospace';
  const tw = g.measureText(text).width;
  const pw = tw + px * 2, ph = 30;
  g.fillStyle = bg;
  rr(g, x, y, pw, ph, ph / 2);
  g.fill();
  g.strokeStyle = color;
  g.lineWidth = 1.2;
  rr(g, x + 0.5, y + 0.5, pw - 1, ph - 1, ph / 2);
  g.stroke();
  g.fillStyle = color;
  g.textAlign = 'left';
  g.textBaseline = 'middle';
  g.fillText(text, x + px, y + ph / 2);
  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// CORE PROCEDURAL HUMAN RIG SYSTEM
// ─────────────────────────────────────────────────────────────────────────────

export function drawHumanRig(g, opts) {
  const {
    cx = 0, cy = 0,
    scale = 1.0,
    skin = '#D29568',
    skinShadow = '#B07548',
    hairColor = '#1A1A1A',
    hairStyle = 'fade', // 'fade', 'parted', 'bob', 'bun', 'ponytail', 'messy'
    attire = 'blazer',   // 'blazer', 'turtleneck', 'polo', 'labcoat', 'vest'
    expression = 'talking', // 'talking', 'angry', 'smug', 'stressed', 'smiling'
    isTalking = true,
    talkingRate = 12,
    blink = false,
    accessories = [],   // 'glasses', 'headset', 'stethoscope', 'phone-right', 'sweat', 'anger-vein', 'steam'
    t = 0
  } = opts;

  g.save();
  g.translate(cx, cy);
  g.scale(scale, scale);

  // Subtle breathing bob
  const breathY = Math.sin(t * 3.5) * 2.5;
  const headBob = Math.sin(t * 4.0) * 1.5;
  const headTilt = Math.sin(t * 2.2) * 0.03;

  // ─── 1. TORSO / BODY & CLOTHING ───
  g.save();
  g.translate(0, breathY);

  const shoulderW = 190;
  
  if (attire === 'blazer') {
    // Dark Navy Blazer with White Dress Shirt & Burgundy Tie
    g.fillStyle = '#0F172A';
    g.beginPath();
    g.moveTo(-shoulderW / 2, 70);
    g.lineTo(shoulderW / 2, 70);
    g.lineTo(shoulderW / 2 + 15, 220);
    g.lineTo(-shoulderW / 2 - 15, 220);
    g.closePath();
    g.fill();

    // White Shirt V-Neck
    g.fillStyle = '#F8FAFC';
    g.beginPath();
    g.moveTo(-28, 65);
    g.lineTo(28, 65);
    g.lineTo(14, 150);
    g.lineTo(-14, 150);
    g.closePath();
    g.fill();

    // Burgundy Tie
    g.fillStyle = '#991B1B';
    g.beginPath();
    g.moveTo(-8, 80);
    g.lineTo(8, 80);
    g.lineTo(12, 175);
    g.lineTo(0, 195);
    g.lineTo(-12, 175);
    g.closePath();
    g.fill();

    // Blazer Lapels
    g.fillStyle = '#1E293B';
    g.beginPath();
    g.moveTo(-shoulderW / 2 + 10, 80);
    g.lineTo(-14, 155);
    g.lineTo(-38, 160);
    g.lineTo(-shoulderW / 2 - 5, 220);
    g.lineTo(-shoulderW / 2 - 15, 80);
    g.closePath();
    g.fill();
    g.beginPath();
    g.moveTo(shoulderW / 2 - 10, 80);
    g.lineTo(14, 155);
    g.lineTo(38, 160);
    g.lineTo(shoulderW / 2 + 5, 220);
    g.lineTo(shoulderW / 2 + 15, 80);
    g.closePath();
    g.fill();

  } else if (attire === 'turtleneck') {
    // Modern Agency Charcoal Turtleneck with Chic Jacket
    g.fillStyle = '#1E293B';
    g.beginPath();
    g.moveTo(-shoulderW / 2, 75);
    g.lineTo(shoulderW / 2, 75);
    g.lineTo(shoulderW / 2 + 15, 220);
    g.lineTo(-shoulderW / 2 - 15, 220);
    g.closePath();
    g.fill();

    // Dark Ribbed Turtleneck Collar
    g.fillStyle = '#090D16';
    rr(g, -32, 50, 64, 42, 12);
    g.fill();
    g.strokeStyle = '#273549';
    g.lineWidth = 1;
    g.stroke();

    // Stylish gold chain necklace
    g.strokeStyle = '#F59E0B';
    g.lineWidth = 2.5;
    g.beginPath();
    g.arc(0, 72, 22, 0.2, Math.PI - 0.2);
    g.stroke();

  } else if (attire === 'polo') {
    // Casual Orange/Coral Polo
    g.fillStyle = '#C2410C';
    g.beginPath();
    g.moveTo(-shoulderW / 2, 75);
    g.lineTo(shoulderW / 2, 75);
    g.lineTo(shoulderW / 2 + 15, 220);
    g.lineTo(-shoulderW / 2 - 15, 220);
    g.closePath();
    g.fill();

    // Polo Collar
    g.fillStyle = '#EA580C';
    g.beginPath();
    g.moveTo(-36, 68);
    g.lineTo(0, 115);
    g.lineTo(36, 68);
    g.lineTo(24, 60);
    g.lineTo(-24, 60);
    g.closePath();
    g.fill();

  } else if (attire === 'labcoat') {
    // Doctor White Lab Coat over Cyan Medical Scrubs
    g.fillStyle = '#0E7490';
    g.beginPath();
    g.moveTo(-shoulderW / 2, 70);
    g.lineTo(shoulderW / 2, 70);
    g.lineTo(shoulderW / 2 + 15, 220);
    g.lineTo(-shoulderW / 2 - 15, 220);
    g.closePath();
    g.fill();

    // V-neck scrubs
    g.fillStyle = '#06B6D4';
    g.beginPath();
    g.moveTo(-25, 65);
    g.lineTo(25, 65);
    g.lineTo(0, 125);
    g.closePath();
    g.fill();

    // Crisp White Coat Panels
    g.fillStyle = '#F8FAFC';
    g.beginPath();
    g.moveTo(-shoulderW / 2 - 5, 75);
    g.lineTo(-20, 120);
    g.lineTo(-30, 220);
    g.lineTo(-shoulderW / 2 - 20, 220);
    g.closePath();
    g.fill();
    g.beginPath();
    g.moveTo(shoulderW / 2 + 5, 75);
    g.lineTo(20, 120);
    g.lineTo(30, 220);
    g.lineTo(shoulderW / 2 + 20, 220);
    g.closePath();
    g.fill();

    g.strokeStyle = '#CBD5E1';
    g.lineWidth = 2;
    g.stroke();

  } else if (attire === 'vest') {
    // Solar Engineer High-Tech Vest
    g.fillStyle = '#14532D';
    g.beginPath();
    g.moveTo(-shoulderW / 2, 70);
    g.lineTo(shoulderW / 2, 70);
    g.lineTo(shoulderW / 2 + 15, 220);
    g.lineTo(-shoulderW / 2 - 15, 220);
    g.closePath();
    g.fill();

    // High-Vis Technical Vest
    g.fillStyle = '#16A34A';
    g.beginPath();
    g.moveTo(-shoulderW / 2 + 15, 75);
    g.lineTo(-12, 130);
    g.lineTo(-12, 220);
    g.lineTo(-shoulderW / 2, 220);
    g.closePath();
    g.fill();
    g.beginPath();
    g.moveTo(shoulderW / 2 - 15, 75);
    g.lineTo(12, 130);
    g.lineTo(12, 220);
    g.lineTo(shoulderW / 2, 220);
    g.closePath();
    g.fill();

    // Reflective Silver Stripe
    g.fillStyle = '#E2E8F0';
    g.fillRect(-shoulderW / 2 + 10, 160, shoulderW - 20, 12);
  }

  // Accessories: Stethoscope
  if (accessories.includes('stethoscope')) {
    g.strokeStyle = '#475569';
    g.lineWidth = 5;
    g.beginPath();
    g.moveTo(-32, 75);
    g.bezierCurveTo(-45, 140, -25, 170, 0, 175);
    g.bezierCurveTo(25, 170, 45, 140, 32, 75);
    g.stroke();

    g.fillStyle = '#94A3B8';
    g.beginPath();
    g.arc(0, 185, 12, 0, TAU);
    g.fill();
    g.fillStyle = '#06B6D4';
    g.beginPath();
    g.arc(0, 185, 6, 0, TAU);
    g.fill();
  }

  g.restore(); // end torso

  // ─── 2. NECK & HEAD ───
  g.save();
  g.translate(0, headBob);
  g.rotate(headTilt);

  // Neck
  g.fillStyle = skinShadow;
  g.fillRect(-18, 25, 36, 45);

  // Head Base Contour
  g.fillStyle = skin;
  g.beginPath();
  g.ellipse(0, 0, 52, 60, 0, 0, TAU);
  g.fill();

  // Ears
  g.fillStyle = skin;
  g.beginPath();
  g.ellipse(-52, 2, 10, 16, 0, 0, TAU);
  g.fill();
  g.beginPath();
  g.ellipse(52, 2, 10, 16, 0, 0, TAU);
  g.fill();
  g.fillStyle = skinShadow;
  g.beginPath();
  g.arc(-52, 2, 5, 0, TAU);
  g.fill();
  g.beginPath();
  g.arc(52, 2, 5, 0, TAU);
  g.fill();

  // Cheek glow / Soft blush
  g.fillStyle = 'rgba(239, 68, 68, 0.08)';
  g.beginPath();
  g.arc(-26, 12, 12, 0, TAU);
  g.arc(26, 12, 12, 0, TAU);
  g.fill();

  // ─── 3. HAIR STYLES ───
  g.fillStyle = hairColor;

  if (hairStyle === 'fade') {
    // Agency Modern Fade with textured top
    g.beginPath();
    g.arc(0, -18, 54, Math.PI, 0);
    g.lineTo(54, 5);
    g.lineTo(46, -10);
    g.lineTo(-46, -10);
    g.lineTo(-54, 5);
    g.closePath();
    g.fill();
    g.beginPath();
    g.ellipse(0, -56, 46, 22, -0.05, 0, TAU);
    g.fill();

  } else if (hairStyle === 'parted') {
    // Stressed Founder Parted Hair
    g.beginPath();
    g.arc(0, -15, 55, Math.PI * 0.95, 0.05);
    g.bezierCurveTo(45, -45, 0, -65, -50, -25);
    g.fill();
    g.strokeStyle = hairColor;
    g.lineWidth = 3.5;
    g.beginPath();
    g.moveTo(-15, -45);
    g.quadraticCurveTo(-22, -20, -12, -8);
    g.stroke();

  } else if (hairStyle === 'bob') {
    // Maya Sleek Chic Bob with highlights
    g.beginPath();
    g.arc(0, -20, 56, Math.PI * 0.9, 0.1);
    g.lineTo(56, 32);
    g.lineTo(42, 38);
    g.lineTo(40, -10);
    g.lineTo(-40, -10);
    g.lineTo(-42, 38);
    g.lineTo(-56, 32);
    g.closePath();
    g.fill();
    g.strokeStyle = '#D97706';
    g.lineWidth = 2.5;
    g.beginPath();
    g.arc(0, -42, 40, Math.PI * 1.15, Math.PI * 1.85);
    g.stroke();

  } else if (hairStyle === 'bun') {
    // Dr. Pallavi Professional Hair with Bun
    g.beginPath();
    g.arc(0, -16, 55, Math.PI, 0);
    g.lineTo(53, 20);
    g.lineTo(-53, 20);
    g.closePath();
    g.fill();
    g.beginPath();
    g.arc(0, -68, 24, 0, TAU);
    g.fill();
    g.strokeStyle = '#FBBF24';
    g.lineWidth = 3;
    g.beginPath();
    g.moveTo(-20, -65);
    g.lineTo(20, -71);
    g.stroke();

  } else if (hairStyle === 'ponytail') {
    // Swati Energetic Engineer Ponytail
    g.beginPath();
    g.arc(0, -18, 54, Math.PI, 0);
    g.lineTo(53, 10);
    g.lineTo(-53, 10);
    g.closePath();
    g.fill();
    g.beginPath();
    g.moveTo(42, -28);
    g.bezierCurveTo(75, -20, 85, 30, 68, 70);
    g.bezierCurveTo(58, 45, 60, 0, 36, -18);
    g.closePath();
    g.fill();

  } else if (hairStyle === 'messy') {
    // Customer Frustrated Messy Hair
    g.beginPath();
    g.arc(0, -15, 55, Math.PI, 0);
    g.lineTo(53, 10);
    g.lineTo(-53, 10);
    g.closePath();
    g.fill();
    g.beginPath();
    g.moveTo(-45, -45); g.lineTo(-60, -65); g.lineTo(-30, -55);
    g.moveTo(-15, -55); g.lineTo(0, -78); g.lineTo(20, -55);
    g.moveTo(30, -52); g.lineTo(58, -68); g.lineTo(46, -42);
    g.fill();
  }

  // ─── 4. EYES & EYEBROWS ───
  const eyeY = -4;
  const isBlinking = blink || ((t * 1.5) % 3.0 > 2.85);

  g.strokeStyle = hairColor;
  g.lineWidth = 3.5;
  g.lineCap = 'round';

  if (expression === 'angry') {
    g.beginPath();
    g.moveTo(-36, eyeY - 18);
    g.lineTo(-10, eyeY - 8);
    g.moveTo(36, eyeY - 18);
    g.lineTo(10, eyeY - 8);
    g.stroke();
  } else if (expression === 'stressed') {
    g.beginPath();
    g.moveTo(-36, eyeY - 12);
    g.lineTo(-12, eyeY - 18);
    g.moveTo(36, eyeY - 12);
    g.lineTo(12, eyeY - 18);
    g.stroke();
  } else if (expression === 'smug') {
    g.beginPath();
    g.moveTo(-36, eyeY - 20);
    g.lineTo(-10, eyeY - 16);
    g.moveTo(36, eyeY - 12);
    g.lineTo(10, eyeY - 10);
    g.stroke();
  } else {
    g.beginPath();
    g.arc(-22, eyeY - 14, 15, Math.PI * 1.15, Math.PI * 1.85);
    g.moveTo(10, eyeY - 16);
    g.arc(22, eyeY - 14, 15, Math.PI * 1.15, Math.PI * 1.85);
    g.stroke();
  }

  if (isBlinking) {
    g.strokeStyle = skinShadow;
    g.lineWidth = 2.5;
    g.beginPath();
    g.arc(-22, eyeY, 10, 0.2, Math.PI - 0.2);
    g.moveTo(12, eyeY);
    g.arc(22, eyeY, 10, 0.2, Math.PI - 0.2);
    g.stroke();
  } else {
    [-22, 22].forEach(ex => {
      g.fillStyle = '#FFFFFF';
      g.beginPath();
      g.ellipse(ex, eyeY, 10, 8, 0, 0, TAU);
      g.fill();
      g.strokeStyle = 'rgba(0,0,0,0.15)';
      g.lineWidth = 1;
      g.stroke();

      const irisShift = (expression === 'angry') ? (ex < 0 ? 2 : -2) : 0;
      g.fillStyle = '#1E1B18';
      g.beginPath();
      g.arc(ex + irisShift, eyeY, 5, 0, TAU);
      g.fill();

      g.fillStyle = '#FFFFFF';
      g.beginPath();
      g.arc(ex + irisShift - 2, eyeY - 2, 2, 0, TAU);
      g.fill();
    });
  }

  // ─── 5. NOSE ───
  g.strokeStyle = skinShadow;
  g.lineWidth = 2;
  g.beginPath();
  g.moveTo(0, eyeY + 4);
  g.lineTo(4, eyeY + 16);
  g.lineTo(-2, eyeY + 18);
  g.stroke();

  // ─── 6. MOUTH WITH PHONEME LIP-SYNC ───
  const mouthY = eyeY + 30;

  if (expression === 'angry') {
    const openAmount = 14 + Math.sin(t * 16) * 5;
    g.fillStyle = '#450A0A';
    g.beginPath();
    g.ellipse(0, mouthY, 22, openAmount, 0, 0, TAU);
    g.fill();
    g.strokeStyle = '#991B1B';
    g.lineWidth = 2;
    g.stroke();

    g.fillStyle = '#FFFFFF';
    g.fillRect(-14, mouthY - openAmount, 28, 6);
    g.fillStyle = '#F87171';
    g.beginPath();
    g.ellipse(0, mouthY + openAmount * 0.4, 12, 6, 0, 0, TAU);
    g.fill();

  } else if (isTalking) {
    const flap = Math.abs(Math.sin(t * talkingRate));
    const mouthW = 16 + flap * 8;
    const mouthH = 3 + flap * 12;

    g.fillStyle = '#450A0A';
    g.beginPath();
    g.ellipse(0, mouthY, mouthW / 2, mouthH / 2, 0, 0, TAU);
    g.fill();
    g.strokeStyle = skinShadow;
    g.lineWidth = 1.5;
    g.stroke();

    if (mouthH > 7) {
      g.fillStyle = '#FFFFFF';
      g.fillRect(-mouthW / 3, mouthY - mouthH / 2, (mouthW * 2) / 3, 3.5);
    }
  } else if (expression === 'smug') {
    g.strokeStyle = skinShadow;
    g.lineWidth = 3;
    g.beginPath();
    g.moveTo(-12, mouthY);
    g.quadraticCurveTo(0, mouthY + 2, 16, mouthY - 5);
    g.stroke();
  } else if (expression === 'stressed') {
    g.strokeStyle = skinShadow;
    g.lineWidth = 2.5;
    g.beginPath();
    g.moveTo(-16, mouthY);
    g.quadraticCurveTo(-8, mouthY - 3, 0, mouthY);
    g.quadraticCurveTo(8, mouthY + 3, 16, mouthY);
    g.stroke();
  } else {
    g.strokeStyle = skinShadow;
    g.lineWidth = 2.5;
    g.beginPath();
    g.arc(0, mouthY - 5, 14, 0.2, Math.PI - 0.2);
    g.stroke();
  }

  // ─── 7. ACCESSORIES ───
  if (accessories.includes('glasses')) {
    g.strokeStyle = '#F59E0B';
    g.lineWidth = 2.5;
    g.fillStyle = 'rgba(255, 255, 255, 0.12)';
    g.beginPath();
    g.arc(-22, eyeY, 14, 0, TAU);
    g.fill();
    g.stroke();
    g.beginPath();
    g.arc(22, eyeY, 14, 0, TAU);
    g.fill();
    g.stroke();
    g.beginPath();
    g.moveTo(-8, eyeY);
    g.lineTo(8, eyeY);
    g.stroke();
  }

  if (accessories.includes('headset')) {
    g.strokeStyle = '#00E5FF';
    g.lineWidth = 4;
    g.beginPath();
    g.arc(0, -18, 54, Math.PI * 1.15, Math.PI * 1.85);
    g.stroke();
    g.fillStyle = '#083344';
    g.strokeStyle = '#00E5FF';
    g.lineWidth = 2;
    rr(g, 46, -10, 14, 26, 6);
    g.fill();
    g.stroke();
    g.strokeStyle = '#00E5FF';
    g.lineWidth = 2.5;
    g.beginPath();
    g.moveTo(52, 6);
    g.quadraticCurveTo(45, mouthY + 5, 20, mouthY + 2);
    g.stroke();
    g.fillStyle = ((t * 4) % 1.0 > 0.3) ? '#10B981' : '#00E5FF';
    g.beginPath();
    g.arc(19, mouthY + 2, 4, 0, TAU);
    g.fill();
  }

  if (accessories.includes('anger-vein')) {
    g.save();
    g.translate(32, -34);
    g.strokeStyle = '#EF4444';
    g.lineWidth = 3;
    g.beginPath();
    g.moveTo(-8, -8); g.lineTo(8, 8);
    g.moveTo(8, -8); g.lineTo(-8, 8);
    g.stroke();
    g.restore();
  }

  if (accessories.includes('steam')) {
    const puff1 = (t * 2.5) % 1.0;
    const puff2 = (t * 2.5 + 0.5) % 1.0;
    g.fillStyle = `rgba(255, 255, 255, ${0.8 - puff1 * 0.8})`;
    g.beginPath();
    g.arc(-62 - puff1 * 25, 0 - puff1 * 20, 10 + puff1 * 12, 0, TAU);
    g.fill();
    g.fillStyle = `rgba(255, 255, 255, ${0.8 - puff2 * 0.8})`;
    g.beginPath();
    g.arc(62 + puff2 * 25, 0 - puff2 * 20, 10 + puff2 * 12, 0, TAU);
    g.fill();
  }

  if (accessories.includes('sweat')) {
    const dropProg = (t * 1.8) % 1.0;
    const dy = -24 + dropProg * 45;
    g.fillStyle = '#38BDF8';
    g.beginPath();
    g.arc(38, dy, 5, 0, TAU);
    g.fill();
  }

  if (accessories.includes('phone-right')) {
    g.save();
    g.fillStyle = skin;
    g.beginPath();
    g.moveTo(shoulderW / 2 - 20, 140);
    g.lineTo(shoulderW / 2 + 15, 120);
    g.lineTo(60, 20);
    g.lineTo(40, 25);
    g.closePath();
    g.fill();

    g.fillStyle = '#020617';
    rr(g, 44, -20, 24, 48, 6);
    g.fill();
    g.strokeStyle = '#00E5FF';
    g.lineWidth = 1.5;
    g.stroke();

    g.fillStyle = '#EF4444';
    g.fillRect(47, -16, 18, 40);

    g.fillStyle = skin;
    for (let f = 0; f < 3; f++) {
      g.beginPath();
      g.ellipse(44, -10 + f * 10, 5, 4, 0, 0, TAU);
      g.fill();
    }
    g.restore();
  }

  g.restore(); // end head
  g.restore(); // end character root
}

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 1: THE AGENCY INVOICE & EXCEL NIGHTMARE (0.0s – 7.8s)
// Features: Rohan (Agency Marketer) smirking + Rahul (Stressed Founder)
// ─────────────────────────────────────────────────────────────────────────────
export function drawAgencyExcelScene(g, cx, cy, t) {
  g.save();
  g.translate(cx, cy);

  // Background Studio Desk Glow
  const gr = g.createRadialGradient(0, 0, 20, 0, 0, 360);
  gr.addColorStop(0, 'rgba(251, 191, 36, 0.12)');
  gr.addColorStop(1, 'rgba(0, 0, 0, 0)');
  g.fillStyle = gr;
  g.fillRect(-450, -250, 900, 500);

  // CHARACTER 1: ROHAN (Slick Agency Marketer - Left)
  drawHumanRig(g, {
    cx: -180, cy: 30,
    scale: 0.95,
    skin: '#E0A97E',
    hairColor: '#0F172A',
    hairStyle: 'fade',
    attire: 'turtleneck',
    expression: 'smug',
    isTalking: (t < 4.0),
    accessories: ['glasses'],
    t
  });

  // Agency Guy Speech Bubble
  if (t < 4.2) {
    g.fillStyle = '#1E293B';
    rr(g, -260, -140, 180, 55, 14);
    g.fill();
    g.strokeStyle = '#F59E0B';
    g.lineWidth = 2;
    g.stroke();
    g.fillStyle = '#FFFFFF';
    g.font = '700 13px Inter, sans-serif';
    g.textAlign = 'center';
    g.fillText('"Bro, 500 leads!"', -170, -118);
    g.font = '600 11px JBMono, monospace';
    g.fillStyle = '#FBBF24';
    g.fillText('"All high intent! 🔥"', -170, -100);
  }

  // CHARACTER 2: RAHUL (Frustrated Founder - Right)
  drawHumanRig(g, {
    cx: 180, cy: 30,
    scale: 0.95,
    skin: '#C68A5E',
    hairColor: '#171717',
    hairStyle: 'parted',
    attire: 'blazer',
    expression: 'stressed',
    isTalking: (t >= 4.0),
    accessories: ['sweat'],
    t
  });

  // Founder Thought Bubble
  if (t >= 4.0) {
    g.fillStyle = '#17060A';
    rr(g, 90, -145, 190, 60, 14);
    g.fill();
    g.strokeStyle = '#EF4444';
    g.lineWidth = 2;
    g.stroke();
    g.fillStyle = '#FFFFFF';
    g.font = '700 13px Inter, sans-serif';
    g.textAlign = 'center';
    g.fillText('"I paid ₹2,50,000..."', 185, -122);
    g.font = '600 11px JBMono, monospace';
    g.fillStyle = '#F87171';
    g.fillText('"for an Excel sheet?! 📉"', 185, -102);
  }

  // Center Prop: The Giant Floating Excel Sheet & Invoice
  const xlY = 90;
  g.fillStyle = '#064E3B';
  rr(g, -150, xlY, 300, 120, 16);
  g.fill();
  g.strokeStyle = '#10B981';
  g.lineWidth = 2;
  g.stroke();

  g.fillStyle = '#10B981';
  rr(g, -135, xlY + 14, 32, 32, 8);
  g.fill();
  g.font = '900 18px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'center';
  g.fillText("X", -119, xlY + 36);

  g.textAlign = 'left';
  g.font = '700 14px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.fillText("leads_sheet_may2026.xlsx", -95, xlY + 28);
  g.font = '700 11px JBMono, monospace';
  g.fillStyle = '#86EFAC';
  g.fillText("500 RAW LEADS DELIVERED", -95, xlY + 44);

  // Floating Rupee Bills flying away
  for (let i = 0; i < 4; i++) {
    const pProg = ((t * 1.5 + i * 0.25) % 1.0);
    const fx = -90 + i * 60 + Math.sin(t * 5 + i) * 15;
    const fy = xlY - 20 - pProg * 110;
    const fa = (1.0 - pProg) * 0.9;
    g.font = '800 18px Inter, sans-serif';
    g.fillStyle = `rgba(239, 68, 68, ${fa})`;
    g.fillText("💸 ₹", fx, fy);
  }

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 2: THE YELLING CUSTOMER HANGUP SCENE (7.8s – 14.0s)
// Features: Vikram (Angry Customer) holding phone + slam shockwaves
// ─────────────────────────────────────────────────────────────────────────────
export function drawYellingCustomerScene(g, cx, cy, t) {
  g.save();
  g.translate(cx, cy);

  const gr = g.createRadialGradient(0, 0, 30, 0, 0, 380);
  gr.addColorStop(0, 'rgba(239, 68, 68, 0.22)');
  gr.addColorStop(1, 'rgba(0, 0, 0, 0)');
  g.fillStyle = gr;
  g.fillRect(-450, -300, 900, 600);

  const isSlam = (t > 12.2);
  const shakeX = isSlam ? (Math.random() - 0.5) * 8 : (Math.sin(t * 24) * 3);
  const shakeY = isSlam ? (Math.random() - 0.5) * 6 : 0;

  drawHumanRig(g, {
    cx: shakeX, cy: shakeY + 20,
    scale: 1.25,
    skin: '#D29568',
    hairColor: '#0A0A0A',
    hairStyle: 'messy',
    attire: 'polo',
    expression: isSlam ? 'angry' : 'angry',
    isTalking: !isSlam,
    accessories: ['anger-vein', 'steam', 'phone-right'],
    t
  });

  if (!isSlam) {
    for (let w = 1; w <= 3; w++) {
      const ringProg = ((t * 3.5 + w * 0.3) % 1.0);
      const rw = 40 + ringProg * 110;
      const rh = 25 + ringProg * 75;
      const ra = (1.0 - ringProg) * 0.7;
      g.strokeStyle = `rgba(239, 68, 68, ${ra})`;
      g.lineWidth = 3;
      g.beginPath();
      g.ellipse(-40 - ringProg * 40, 20, rw / 2, rh / 2, -0.2, 0, TAU);
      g.stroke();
    }
  }

  if (!isSlam) {
    g.fillStyle = '#EF4444';
    rr(g, -260, -180, 520, 85, 20);
    g.fill();
    g.strokeStyle = '#FFFFFF';
    g.lineWidth = 3;
    g.stroke();

    g.font = '900 24px InterTight, sans-serif';
    g.fillStyle = '#FFFFFF';
    g.textAlign = 'center';
    g.fillText('"WHO ARE YOU?! 😡"', 0, -145);
    g.font = '700 16px Inter, sans-serif';
    g.fillStyle = '#FEF08A';
    g.fillText('I NEVER FILLED ANY FORM! DON\'T CALL ME!', 0, -115);
  } else {
    g.fillStyle = '#020617';
    rr(g, -220, -170, 440, 95, 22);
    g.fill();
    g.strokeStyle = '#EF4444';
    g.lineWidth = 3;
    g.stroke();

    g.font = '900 28px InterTight, sans-serif';
    g.fillStyle = '#EF4444';
    g.textAlign = 'center';
    g.fillText('💥 CALL TERMINATED', 0, -132);
    g.font = '700 13px JBMono, monospace';
    g.fillStyle = '#94A3B8';
    g.fillText('PROSPECT HUNG UP · LEAD BURNED', 0, -100);
  }

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 3: THE 5-MINUTE BRAIN FREEZE (14.0s – 19.8s)
// Features: Customer physically freezing into ice as intent collapses
// ─────────────────────────────────────────────────────────────────────────────
export function drawBrainFreezeScene(g, cx, cy, t) {
  g.save();
  g.translate(cx, cy);

  const prog = clamp((t - 14.0) / 5.2, 0, 1);
  const isFrozen = (prog > 0.6);

  const gr = g.createRadialGradient(0, 0, 20, 0, 0, 360);
  gr.addColorStop(0, `rgba(56, 189, 248, ${0.1 + prog * 0.25})`);
  gr.addColorStop(1, 'rgba(0, 0, 0, 0)');
  g.fillStyle = gr;
  g.fillRect(-450, -300, 900, 600);

  const skinColor = isFrozen ? '#94A3B8' : '#D29568';
  drawHumanRig(g, {
    cx: 0, cy: 30,
    scale: 1.15,
    skin: skinColor,
    hairColor: isFrozen ? '#475569' : '#0F172A',
    hairStyle: 'messy',
    attire: 'polo',
    expression: isFrozen ? 'stressed' : 'talking',
    isTalking: !isFrozen,
    accessories: [],
    t
  });

  if (isFrozen) {
    g.strokeStyle = '#38BDF8';
    g.lineWidth = 2.5;
    [-40, 0, 40].forEach((ix, idx) => {
      const iy = 20 + idx * 25;
      g.beginPath();
      g.moveTo(ix - 12, iy); g.lineTo(ix + 12, iy);
      g.moveTo(ix, iy - 12); g.lineTo(ix, iy + 12);
      g.moveTo(ix - 8, iy - 8); g.lineTo(ix + 8, iy + 8);
      g.moveTo(ix + 8, iy - 8); g.lineTo(ix - 8, iy + 8);
      g.stroke();
    });
  }

  const clockY = -150;
  g.fillStyle = '#0B132B';
  rr(g, -230, clockY, 460, 90, 20);
  g.fill();
  g.strokeStyle = '#38BDF8';
  g.lineWidth = 2;
  g.stroke();

  const secCount = Math.min(5, Math.floor(prog * 5));
  g.font = '900 36px JBMono, monospace';
  g.fillStyle = (secCount >= 5) ? '#EF4444' : '#00E5FF';
  g.textAlign = 'center';
  g.fillText(`00:0${secCount} MIN`, 0, clockY + 45);

  g.font = '700 13px Inter, sans-serif';
  g.fillStyle = '#EF4444';
  g.fillText('📉 BUYING INTENT COLLAPSES: -391%', 0, clockY + 72);

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 5A: MAYA — LUXURY REAL ESTATE AI CLOSER (26.5s – 34.7s)
// Features: Maya speaking English, beachfront villa blueprint, WhatsApp drop
// ─────────────────────────────────────────────────────────────────────────────
export function drawMayaRealEstateScene(g, cx, cy, t) {
  g.save();
  g.translate(cx, cy);

  const gr = g.createRadialGradient(0, -20, 20, 0, -20, 380);
  gr.addColorStop(0, 'rgba(16, 185, 129, 0.18)');
  gr.addColorStop(1, 'rgba(0, 0, 0, 0)');
  g.fillStyle = gr;
  g.fillRect(-450, -320, 900, 640);

  drawHumanRig(g, {
    cx: -100, cy: 30,
    scale: 1.2,
    skin: '#E2A77A',
    hairColor: '#2E1810',
    hairStyle: 'bob',
    attire: 'blazer',
    expression: 'smiling',
    isTalking: (t >= 26.5 && t <= 34.7),
    accessories: ['headset'],
    t
  });

  const cardX = 140, cardY = -30;
  g.fillStyle = '#062822';
  rr(g, cardX - 120, cardY - 110, 240, 220, 20);
  g.fill();
  g.strokeStyle = '#10B981';
  g.lineWidth = 2;
  g.stroke();

  pill(g, cardX - 105, cardY - 95, "🏖️ REAL ESTATE", {
    color: '#34D399', bg: 'rgba(52, 211, 153, 0.2)', px: 10
  });

  g.font = '800 20px InterTight, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'left';
  g.fillText("ECR Sea Villa", cardX - 105, cardY - 35);
  g.font = '700 15px JBMono, monospace';
  g.fillStyle = '#34D399';
  g.fillText("₹15.5 Crore", cardX - 105, cardY - 12);

  g.strokeStyle = 'rgba(52, 211, 153, 0.4)';
  g.lineWidth = 1.5;
  g.strokeRect(cardX - 105, cardY + 8, 210, 75);
  g.fillStyle = 'rgba(52, 211, 153, 0.1)';
  g.fillRect(cardX - 105, cardY + 8, 210, 75);

  g.font = '600 11px JBMono, monospace';
  g.fillStyle = '#A7F3D0';
  g.fillText("RERA APPROVED · POOL · 5BHK", cardX - 95, cardY + 38);
  g.fillText("✓ BROCHURE SENT VIA WHATSAPP", cardX - 95, cardY + 58);

  g.fillStyle = '#041F1A';
  rr(g, -240, -170, 480, 50, 15);
  g.fill();
  g.strokeStyle = '#34D399';
  g.lineWidth = 1.5;
  g.stroke();
  g.font = '700 13px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'center';
  g.fillText('Maya: "Good evening Mr. Sharma! Villa brochure sent. Sunday 11 AM locked."', 0, -140);

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 5B: DR. PALLAVI — HEALTHCARE & CLINIC AI CLOSER (34.7s – 41.1s)
// Features: Dr. Pallavi speaking Tamil, dental/hair clinic pass, consultation locked
// ─────────────────────────────────────────────────────────────────────────────
export function drawPallaviClinicScene(g, cx, cy, t) {
  g.save();
  g.translate(cx, cy);

  const gr = g.createRadialGradient(0, -20, 20, 0, -20, 380);
  gr.addColorStop(0, 'rgba(6, 182, 212, 0.20)');
  gr.addColorStop(1, 'rgba(0, 0, 0, 0)');
  g.fillStyle = gr;
  g.fillRect(-450, -320, 900, 640);

  drawHumanRig(g, {
    cx: -100, cy: 30,
    scale: 1.2,
    skin: '#C68652',
    hairColor: '#171717',
    hairStyle: 'bun',
    attire: 'labcoat',
    expression: 'smiling',
    isTalking: (t >= 34.7 && t <= 41.1),
    accessories: ['stethoscope', 'headset'],
    t
  });

  const cardX = 140, cardY = -30;
  g.fillStyle = '#082F3B';
  rr(g, cardX - 120, cardY - 110, 240, 220, 20);
  g.fill();
  g.strokeStyle = '#06B6D4';
  g.lineWidth = 2;
  g.stroke();

  pill(g, cardX - 105, cardY - 95, "🩺 CLINICS & HEALTHCARE", {
    color: '#22D3EE', bg: 'rgba(34, 211, 238, 0.2)', px: 10
  });

  g.font = '800 18px InterTight, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'left';
  g.fillText("Dental & Hair VIP Pass", cardX - 105, cardY - 35);
  g.font = '700 14px JBMono, monospace';
  g.fillStyle = '#22D3EE';
  g.fillText("Chennai Aesthetic Clinic", cardX - 105, cardY - 12);

  g.fillStyle = 'rgba(6, 182, 212, 0.15)';
  rr(g, cardX - 105, cardY + 10, 210, 75, 12);
  g.fill();
  g.font = '700 12px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.fillText("Dr. Consultation Confirmed", cardX - 95, cardY + 35);
  g.font = '700 11px JBMono, monospace';
  g.fillStyle = '#67E8F9';
  g.fillText("🗓️ Tomorrow 5:00 PM Locked", cardX - 95, cardY + 55);
  g.fillText("✓ Token: VIP-CH-942", cardX - 95, cardY + 72);

  g.fillStyle = '#06202A';
  rr(g, -240, -170, 480, 50, 15);
  g.fill();
  g.strokeStyle = '#22D3EE';
  g.lineWidth = 1.5;
  g.stroke();
  g.font = '700 13px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'center';
  g.fillText('Pallavi: "வணக்கம்! உங்கள் அப்பாயின்மென்ட் நாளை மாலை 5 மணிக்கு கன்பார்ம்."', 0, -140);

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 5C: SWATI — SOLAR & HOME RENOVATION AI CLOSER (41.1s – 47.2s)
// Features: Swati speaking Hindi, 5kW Solar panel, 40% government subsidy quote
// ─────────────────────────────────────────────────────────────────────────────
export function drawSwatiSolarScene(g, cx, cy, t) {
  g.save();
  g.translate(cx, cy);

  const gr = g.createRadialGradient(0, -20, 20, 0, -20, 380);
  gr.addColorStop(0, 'rgba(234, 179, 8, 0.18)');
  gr.addColorStop(1, 'rgba(0, 0, 0, 0)');
  g.fillStyle = gr;
  g.fillRect(-450, -320, 900, 640);

  drawHumanRig(g, {
    cx: -100, cy: 30,
    scale: 1.2,
    skin: '#DE9E6E',
    hairColor: '#171717',
    hairStyle: 'ponytail',
    attire: 'vest',
    expression: 'smiling',
    isTalking: (t >= 41.1 && t <= 47.2),
    accessories: ['headset'],
    t
  });

  const cardX = 140, cardY = -30;
  g.fillStyle = '#261C02';
  rr(g, cardX - 120, cardY - 110, 240, 220, 20);
  g.fill();
  g.strokeStyle = '#EAB308';
  g.lineWidth = 2;
  g.stroke();

  pill(g, cardX - 105, cardY - 95, "☀️ SOLAR & HOME RENO", {
    color: '#FACC15', bg: 'rgba(250, 204, 21, 0.2)', px: 10
  });

  g.font = '800 20px InterTight, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'left';
  g.fillText("5kW Rooftop Solar", cardX - 105, cardY - 35);
  g.font = '700 14px JBMono, monospace';
  g.fillStyle = '#FACC15';
  g.fillText("Delhi NCR Homeowner", cardX - 105, cardY - 12);

  g.fillStyle = 'rgba(234, 179, 8, 0.15)';
  rr(g, cardX - 105, cardY + 10, 210, 75, 12);
  g.fill();
  g.font = '700 12px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.fillText("40% PM Surya Ghar Subsidy", cardX - 95, cardY + 34);
  g.font = '700 11px JBMono, monospace';
  g.fillStyle = '#FEF08A';
  g.fillText("⚡ ₹78,000 Direct Subsidy", cardX - 95, cardY + 54);
  g.fillText("✓ Quotation Sent to WhatsApp", cardX - 95, cardY + 72);

  g.fillStyle = '#1A1402';
  rr(g, -240, -170, 480, 50, 15);
  g.fill();
  g.strokeStyle = '#FACC15';
  g.lineWidth = 1.5;
  g.stroke();
  g.font = '700 13px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'center';
  g.fillText('Swati: "नमस्ते सर! आपके 5kW रूफटॉप सोलर का कोटेशन हमने व्हाट्सएप पर भेज दिया है।"', 0, -140);

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 5 MASTER DISPATCHER: Renders Maya, Pallavi, or Swati seamlessly!
// ─────────────────────────────────────────────────────────────────────────────
export function drawMultiSectorScene(g, cx, cy, t) {
  if (t < 34.7) {
    drawMayaRealEstateScene(g, cx, cy, t);
  } else if (t < 41.1) {
    drawPallaviClinicScene(g, cx, cy, t);
  } else {
    drawSwatiSolarScene(g, cx, cy, t);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 6: MULTI-SECTOR WHATSAPP ENGINE (47.2s – 53.0s)
// ─────────────────────────────────────────────────────────────────────────────
export function drawMultiSectorWhatsApp(g, cx, cy, t) {
  g.save();
  g.translate(cx, cy);

  const pw = 420, ph = 340;
  g.fillStyle = '#075E54';
  rr(g, -pw / 2, -160, pw, 50, 16);
  g.fill();

  g.fillStyle = '#111B21';
  rr(g, -pw / 2, -115, pw, ph - 45, 16);
  g.fill();
  g.strokeStyle = '#25D366';
  g.lineWidth = 2;
  rr(g, -pw / 2, -160, pw, ph, 16);
  g.stroke();

  g.font = '700 15px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'left';
  g.fillText("💬 CLOSER AI Verified Dispatch", -pw / 2 + 20, -130);

  const attachments = [
    { title: "📄 ECR_Villa_RERA_Brochure.pdf", meta: "3.2 MB · Real Estate", color: "#10B981" },
    { title: "🩺 VIP_Clinic_Consultation_Pass.pkpass", meta: "Apple Wallet · Clinic", color: "#06B6D4" },
    { title: "☀️ 5kW_Solar_Subsidy_Breakdown.pdf", meta: "₹78,000 Subsidy · Solar", color: "#FACC15" }
  ];

  attachments.forEach((att, idx) => {
    const ay = -90 + idx * 75;
    g.fillStyle = '#202C33';
    rr(g, -pw / 2 + 15, ay, pw - 30, 62, 12);
    g.fill();
    g.strokeStyle = att.color;
    g.lineWidth = 1.2;
    g.stroke();

    g.font = '700 13px Inter, sans-serif';
    g.fillStyle = '#FFFFFF';
    g.fillText(att.title, -pw / 2 + 30, ay + 26);
    g.font = '600 11px JBMono, monospace';
    g.fillStyle = att.color;
    g.fillText(att.meta, -pw / 2 + 30, ay + 46);

    g.font = '700 12px Inter, sans-serif';
    g.fillStyle = '#53BDEB';
    g.textAlign = 'right';
    g.fillText("✓✓ Sent", pw / 2 - 25, ay + 46);
    g.textAlign = 'left';
  });

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// SCENE 7: VIRAL COMMENT MAGNET & CALL TO ACTION (59.2s – 68.0s)
// Features: The Host pointing down with arrows towards the comment section!
// ─────────────────────────────────────────────────────────────────────────────
export function drawCommentCtaScene(g, cx, cy, t) {
  g.save();
  g.translate(cx, cy);

  const gr = g.createRadialGradient(0, 0, 20, 0, 0, 360);
  gr.addColorStop(0, 'rgba(251, 191, 36, 0.22)');
  gr.addColorStop(1, 'rgba(0, 0, 0, 0)');
  g.fillStyle = gr;
  g.fillRect(-450, -300, 900, 600);

  drawHumanRig(g, {
    cx: 0, cy: -20,
    scale: 1.15,
    skin: '#D29568',
    hairColor: '#0A0A0A',
    hairStyle: 'fade',
    attire: 'blazer',
    expression: 'smiling',
    isTalking: (t < 66.5),
    accessories: ['headset'],
    t
  });

  const bounceY = Math.sin(t * 8) * 8;
  const boxY = 120 + bounceY;

  g.fillStyle = '#1E1402';
  rr(g, -210, boxY, 420, 85, 20);
  g.fill();
  g.strokeStyle = '#FBBF24';
  g.lineWidth = 3;
  g.stroke();

  g.font = '900 24px InterTight, sans-serif';
  g.fillStyle = '#FBBF24';
  g.textAlign = 'center';
  g.fillText('COMMENT "CLOSER" BELOW 👇', 0, boxY + 38);

  g.font = '700 12px JBMono, monospace';
  g.fillStyle = '#FFFFFF';
  g.fillText('FOR THE MULTI-SECTOR PROMPT STACK', 0, boxY + 62);

  [-170, 170].forEach(ax => {
    const arrowBounce = Math.sin(t * 10) * 10;
    g.font = '900 28px Inter, sans-serif';
    g.fillStyle = '#FBBF24';
    g.fillText('👇', ax, boxY + 45 + arrowBounce);
  });

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// HORMOZI HIGH-RETENTION KARAOKE SUBTITLES
// ─────────────────────────────────────────────────────────────────────────────
const DEFAULT_REEL_SUBS = [
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

export function renderHormoziCaptions(g, t, W, H, lines = DEFAULT_REEL_SUBS) {
  const active = lines.find(l => t >= l.t0 && t <= l.t1);
  if (!active) return;

  const prog = clamp((t - active.t0) / (active.t1 - active.t0), 0, 1);
  const words = active.text.split(' ');
  const activeWordIdx = Math.min(words.length - 1, Math.floor(prog * words.length));

  const subY = H - 240;
  g.save();

  g.font = '900 36px InterTight, sans-serif';
  const fullTw = g.measureText(active.text).width;
  g.fillStyle = 'rgba(0, 0, 0, 0.78)';
  rr(g, W / 2 - fullTw / 2 - 25, subY - 45, fullTw + 50, 65, 20);
  g.fill();
  g.strokeStyle = 'rgba(255, 255, 255, 0.15)';
  g.lineWidth = 1;
  g.stroke();

  let curX = W / 2 - fullTw / 2;
  words.forEach((w, idx) => {
    const isCur = (idx === activeWordIdx);
    const wordWidth = g.measureText(w + ' ').width;

    if (isCur) {
      const bounce = Math.sin(prog * words.length * Math.PI) * 4;
      g.save();
      g.translate(curX + wordWidth / 2, subY - bounce);
      g.scale(1.15, 1.15);
      g.fillStyle = '#FACC15';
      g.shadowColor = 'rgba(250, 204, 21, 0.8)';
      g.shadowBlur = 18;
      g.textAlign = 'center';
      g.fillText(w, 0, 0);
      g.restore();
    } else {
      g.fillStyle = '#FFFFFF';
      g.shadowColor = 'transparent';
      g.textAlign = 'left';
      g.fillText(w, curX, subY);
    }
    curX += wordWidth;
  });

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// TRANSITIONS & VISUAL EFFECTS
// ─────────────────────────────────────────────────────────────────────────────
const DEFAULT_CUT_TIMES = [0.0, 7.8, 14.0, 19.8, 26.5, 34.7, 41.1, 47.2, 53.0, 59.2];

export function drawCutTransition(g, t, cutTimes = DEFAULT_CUT_TIMES, W = 1080, H = 1920) {
  const cuts = Array.isArray(cutTimes) ? cutTimes : DEFAULT_CUT_TIMES;
  for (const ct of cuts) {
    const dt = t - ct;
    if (dt >= 0 && dt < 0.18) {
      const alpha = (1.0 - dt / 0.18);
      g.fillStyle = `rgba(0, 229, 255, ${alpha * 0.35})`;
      g.fillRect(0, 0, W, H);
      g.fillStyle = `rgba(239, 68, 68, ${alpha * 0.25})`;
      g.fillRect(0, 0, W, H);
      g.fillStyle = `rgba(255, 255, 255, ${alpha * 0.45})`;
      g.fillRect(0, 0, W, H);
      break;
    }
  }
}

export function drawScanlines(g, W, H) {
  g.save();
  g.fillStyle = 'rgba(0, 0, 0, 0.08)';
  for (let y = 0; y < H; y += 4) {
    g.fillRect(0, y, W, 1.5);
  }
  g.restore();
}
