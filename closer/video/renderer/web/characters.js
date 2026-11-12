// closer/video/renderer/web/characters.js
// Procedural 2D Indian Character Rigs, Expressions, Attire & Sector Visual Engine

import { clamp, lerp, TAU, rgba, rr, pill, font, FONT, PAL } from './engine.js';

// ─────────────────────────────────────────────────────────────────────────────
// 1. PROCEDURAL INDIAN CHARACTER RIG SYSTEM
// ─────────────────────────────────────────────────────────────────────────────
export function drawHumanRig(g, opts) {
  const {
    cx = 0, cy = 0,
    scale = 1.0,
    skin = '#D29568',          // Realistic Indian wheatish/bronze skin
    skinShadow = '#B07548',
    hairColor = '#1A1A1A',
    hairStyle = 'fade',        // 'fade', 'parted', 'bob', 'bun', 'ponytail', 'messy'
    attire = 'blazer',         // 'blazer', 'turtleneck', 'polo', 'labcoat', 'vest'
    expression = 'talking',    // 'talking', 'angry', 'smug', 'stressed', 'smiling'
    isTalking = true,
    talkingRate = 12,
    blink = false,
    accessories = [],          // 'glasses', 'headset', 'stethoscope', 'phone-right', 'sweat', 'anger-vein', 'steam'
    t = 0
  } = opts;

  g.save();
  g.translate(cx, cy);
  g.scale(scale, scale);

  // Subtle natural breathing bob & micro head tilt
  const breathY = Math.sin(t * 3.5) * 2.5;
  const headBob = Math.sin(t * 4.0) * 1.5;
  const headTilt = Math.sin(t * 2.2) * 0.03;

  // ─── 1. TORSO / BODY & SECTOR ATTIRE ───
  g.save();
  g.translate(0, breathY);
  const shoulderW = 190;

  if (attire === 'blazer') {
    // Luxury Real Estate / Corporate: Dark Navy Blazer + White Shirt + Burgundy Tie
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
    // Agency Founder: Charcoal Ribbed Turtleneck + Chic Jacket + Gold Chain
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

    // Stylish Gold Chain Necklace
    g.strokeStyle = '#F59E0B';
    g.lineWidth = 2.5;
    g.beginPath();
    g.arc(0, 72, 22, 0.2, Math.PI - 0.2);
    g.stroke();

  } else if (attire === 'polo') {
    // EdTech / Tech Founder: Casual Coral/Orange Polo
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
    // Clinic Doctor: White Medical Lab Coat over Cyan Medical Scrubs
    g.fillStyle = '#0E7490';
    g.beginPath();
    g.moveTo(-shoulderW / 2, 70);
    g.lineTo(shoulderW / 2, 70);
    g.lineTo(shoulderW / 2 + 15, 220);
    g.lineTo(-shoulderW / 2 - 15, 220);
    g.closePath();
    g.fill();

    // V-Neck Medical Scrubs
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
    // Rooftop Solar EPC: Technical High-Vis Safety Vest + Reflective Stripe
    g.fillStyle = '#14532D';
    g.beginPath();
    g.moveTo(-shoulderW / 2, 70);
    g.lineTo(shoulderW / 2, 70);
    g.lineTo(shoulderW / 2 + 15, 220);
    g.lineTo(-shoulderW / 2 - 15, 220);
    g.closePath();
    g.fill();

    // High-Vis Green/Lime Technical Vest
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

    // Reflective Silver Safety Stripe
    g.fillStyle = '#E2E8F0';
    g.fillRect(-shoulderW / 2 + 10, 160, shoulderW - 20, 12);
  }

  // Accessory: Stethoscope
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

  // ─── 2. NECK & HEAD CONTOUR ───
  g.save();
  g.translate(0, headBob);
  g.rotate(headTilt);

  // Neck
  g.fillStyle = skinShadow;
  g.fillRect(-18, 25, 36, 45);

  // Head Base
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

  // Cheek Glow / Soft Blush
  g.fillStyle = 'rgba(239, 68, 68, 0.08)';
  g.beginPath();
  g.arc(-26, 12, 12, 0, TAU);
  g.arc(26, 12, 12, 0, TAU);
  g.fill();

  // ─── 3. HAIR STYLES ───
  g.fillStyle = hairColor;

  if (hairStyle === 'fade') {
    // Clean Modern Indian Fade
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
    // Professional Side-Parted Hair
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
    // Sleek Bob with Chic Highlights
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

  } else if (hairStyle === 'bun') {
    // Doctor / Executive Top Bun
    g.beginPath();
    g.arc(0, -16, 55, Math.PI, 0);
    g.lineTo(53, 20);
    g.lineTo(-53, 20);
    g.closePath();
    g.fill();
    g.beginPath();
    g.arc(0, -68, 24, 0, TAU);
    g.fill();

  } else if (hairStyle === 'ponytail') {
    // Energetic Clean-Energy Ponytail
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
    // Customer Frustrated / Disheveled Hair
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

  // ─── 4. EYES & EYEBROWS (EXPRESSIONS) ───
  const eyeY = -4;
  const isBlinking = blink || ((t * 1.5) % 3.0 > 2.85);

  g.strokeStyle = hairColor;
  g.lineWidth = 3.5;
  g.lineCap = 'round';

  if (expression === 'angry') {
    // Aggressive V-Shaped Eyebrows
    g.beginPath();
    g.moveTo(-36, eyeY - 18);
    g.lineTo(-10, eyeY - 8);
    g.moveTo(36, eyeY - 18);
    g.lineTo(10, eyeY - 8);
    g.stroke();
  } else if (expression === 'stressed') {
    // Inward-Slanting Furrowed Eyebrows
    g.beginPath();
    g.moveTo(-36, eyeY - 12);
    g.lineTo(-12, eyeY - 18);
    g.moveTo(36, eyeY - 12);
    g.lineTo(12, eyeY - 18);
    g.stroke();
  } else if (expression === 'smug') {
    // Raised Asymmetrical Eyebrows
    g.beginPath();
    g.moveTo(-36, eyeY - 20);
    g.lineTo(-10, eyeY - 16);
    g.moveTo(36, eyeY - 12);
    g.lineTo(10, eyeY - 10);
    g.stroke();
  } else if (expression === 'smiling') {
    // High Arched Warm Eyebrows
    g.beginPath();
    g.arc(-22, eyeY - 16, 16, Math.PI * 1.15, Math.PI * 1.85);
    g.moveTo(10, eyeY - 16);
    g.arc(22, eyeY - 16, 16, Math.PI * 1.15, Math.PI * 1.85);
    g.stroke();
  } else {
    // Standard Neutral Talking Eyebrows
    g.beginPath();
    g.arc(-22, eyeY - 14, 15, Math.PI * 1.15, Math.PI * 1.85);
    g.moveTo(10, eyeY - 14);
    g.arc(22, eyeY - 14, 15, Math.PI * 1.15, Math.PI * 1.85);
    g.stroke();
  }

  // Eyes
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
      g.fillStyle = '#1E1B18'; // Deep brown / black Indian iris
      g.beginPath();
      g.arc(ex + irisShift, eyeY, 5, 0, TAU);
      g.fill();

      // Specular eye gleam
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

  // ─── 6. MOUTH & PHONEME LIP-SYNC ───
  const mouthY = eyeY + 30;

  if (expression === 'angry') {
    // Wide shouting mouth with red tongue
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
    // Dynamic Phoneme Mouth Flapping
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
    // Half-Smirk Curve
    g.strokeStyle = skinShadow;
    g.lineWidth = 3;
    g.beginPath();
    g.moveTo(-12, mouthY);
    g.quadraticCurveTo(0, mouthY + 2, 16, mouthY - 5);
    g.stroke();

  } else if (expression === 'stressed') {
    // Tremoring Wavy Mouth
    g.strokeStyle = skinShadow;
    g.lineWidth = 2.5;
    g.beginPath();
    g.moveTo(-16, mouthY);
    g.quadraticCurveTo(-8, mouthY - 3, 0, mouthY);
    g.quadraticCurveTo(8, mouthY + 3, 16, mouthY);
    g.stroke();

  } else if (expression === 'smiling') {
    // Warm Smile
    g.strokeStyle = skinShadow;
    g.lineWidth = 2.5;
    g.beginPath();
    g.arc(0, mouthY - 4, 15, 0.2, Math.PI - 0.2);
    g.stroke();
  } else {
    // Relaxed Closed Mouth
    g.strokeStyle = skinShadow;
    g.lineWidth = 2.5;
    g.beginPath();
    g.moveTo(-10, mouthY);
    g.lineTo(10, mouthY);
    g.stroke();
  }

  // ─── 7. ACCESSORIES & EMOTION EFFECTS ───
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
    g.strokeStyle = PAL.accent;
    g.lineWidth = 4;
    g.beginPath();
    g.arc(0, -18, 54, Math.PI * 1.15, Math.PI * 1.85);
    g.stroke();
    g.fillStyle = '#083344';
    g.strokeStyle = PAL.accent;
    g.lineWidth = 2;
    rr(g, 46, -10, 14, 26, 6);
    g.fill();
    g.stroke();
    g.strokeStyle = PAL.accent;
    g.lineWidth = 2.5;
    g.beginPath();
    g.moveTo(52, 6);
    g.quadraticCurveTo(45, mouthY + 5, 20, mouthY + 2);
    g.stroke();
    g.fillStyle = ((t * 4) % 1.0 > 0.3) ? PAL.lime : PAL.accent;
    g.beginPath();
    g.arc(19, mouthY + 2, 4, 0, TAU);
    g.fill();
  }

  if (accessories.includes('anger-vein')) {
    g.save();
    g.translate(32, -34);
    g.strokeStyle = PAL.red;
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
    g.strokeStyle = PAL.accent;
    g.lineWidth = 1.5;
    g.stroke();

    g.fillStyle = PAL.red;
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
