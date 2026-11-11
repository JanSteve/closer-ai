// characters.js — CLOSER AI Animated Character Rig & Visual FX Engine
// Procedural Canvas 2D character animation for ultra-high retention short-form video.
// Characters: Frustrated Builder, Nocturnal Luxury Buyer, Sleeping Telecaller,
// Holographic AI Closer Avatars (Maya, Pallavi, Swati), WhatsApp Sync, Viral Comment Magnet.

import { clamp, lerp, TAU, rgba } from './engine.js';

// Helper: Rounded rectangle
function rr(g, x, y, w, h, r) {
  g.beginPath();
  g.roundRect(x, y, w, h, Math.max(0, Math.min(r, w / 2, h / 2)));
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. THE FRUSTRATED LUXURY BUILDER (Mr. Rajesh)
// Stressed builder watching stacks of ₹500 notes burst into flames & dissolve
// ─────────────────────────────────────────────────────────────────────────────
export function drawBuilderCharacter(g, cx, cy, t, opts = {}) {
  g.save();
  const breathe = Math.sin(t * 6) * 4;
  const panicShake = (Math.sin(t * 24) * 2.5);

  g.translate(cx + panicShake, cy + breathe);

  // 1. Shoulders & Navy Suit
  g.fillStyle = '#0F1E36';
  g.beginPath();
  g.ellipse(0, 140, 110, 75, 0, 0, TAU);
  g.fill();

  // White shirt collar
  g.fillStyle = '#FFFFFF';
  g.beginPath();
  g.moveTo(-35, 95);
  g.lineTo(0, 140);
  g.lineTo(35, 95);
  g.closePath();
  g.fill();

  // Red Tie
  g.fillStyle = '#EF4444';
  g.beginPath();
  g.moveTo(-12, 120);
  g.lineTo(12, 120);
  g.lineTo(8, 190);
  g.lineTo(0, 205);
  g.lineTo(-8, 190);
  g.closePath();
  g.fill();

  // 2. Neck
  g.fillStyle = '#D97746';
  rr(g, -24, 75, 48, 40, 10);
  g.fill();

  // 3. Head & Face
  g.fillStyle = '#F59E0B'; // warm skin
  g.beginPath();
  g.ellipse(0, 30, 68, 78, 0, 0, TAU);
  g.fill();

  // Hair
  g.fillStyle = '#1E293B';
  g.beginPath();
  g.arc(0, 10, 72, Math.PI, 0);
  g.fill();
  // Sideburns
  rr(g, -72, 10, 14, 40, 6);
  g.fill();
  rr(g, 58, 10, 14, 40, 6);
  g.fill();

  // 4. Stressed Eyes (Wide, shaking pupils)
  const eyeBlink = (t % 3.2 < 0.12) ? 0.1 : 1.0;
  // Left eye white
  g.fillStyle = '#FFFFFF';
  g.beginPath();
  g.ellipse(-26, 22, 18, 20 * eyeBlink, 0, 0, TAU);
  g.fill();
  // Right eye white
  g.beginPath();
  g.ellipse(26, 22, 18, 20 * eyeBlink, 0, 0, TAU);
  g.fill();

  if (eyeBlink > 0.3) {
    // Shaking dark pupils
    const px = Math.sin(t * 18) * 3;
    g.fillStyle = '#0F172A';
    g.beginPath();
    g.arc(-26 + px, 22, 8, 0, TAU);
    g.fill();
    g.beginPath();
    g.arc(26 + px, 22, 8, 0, TAU);
    g.fill();

    // Catchlight sparkles
    g.fillStyle = '#FFFFFF';
    g.beginPath();
    g.arc(-29 + px, 18, 3, 0, TAU);
    g.fill();
    g.beginPath();
    g.arc(23 + px, 18, 3, 0, TAU);
    g.fill();
  }

  // Furrowed Eyebrows (angled in intense stress)
  g.strokeStyle = '#1E293B';
  g.lineWidth = 5;
  g.lineCap = 'round';
  g.beginPath();
  g.moveTo(-45, 0);
  g.lineTo(-12, 12);
  g.stroke();

  g.beginPath();
  g.moveTo(45, 0);
  g.lineTo(12, 12);
  g.stroke();

  // 5. Open Gasping Mouth (Shocked 'O')
  const mouthWarp = Math.sin(t * 12) * 3;
  g.fillStyle = '#7F1D1D';
  g.beginPath();
  g.ellipse(0, 68, 18 + mouthWarp, 22, 0, 0, TAU);
  g.fill();
  // Teeth
  g.fillStyle = '#FFFFFF';
  rr(g, -10, 52, 20, 8, 3);
  g.fill();

  // 6. Giant Sweat Droplets popping from temples
  const sweatProg = (t * 4) % 1.0;
  const sweatY = -10 + sweatProg * 50;
  const sweatA = clamp(1.0 - sweatProg);
  g.fillStyle = `rgba(56, 189, 248, ${sweatA * 0.9})`;
  g.beginPath();
  g.arc(68, sweatY, 9, 0, TAU);
  g.fill();
  g.beginPath();
  g.moveTo(68, sweatY - 14);
  g.lineTo(60, sweatY);
  g.lineTo(76, sweatY);
  g.closePath();
  g.fill();

  // 7. Hands holding burning money notes
  g.fillStyle = '#F59E0B';
  // Hands
  g.beginPath();
  g.arc(-80, 110, 22, 0, TAU);
  g.fill();
  g.beginPath();
  g.arc(80, 110, 22, 0, TAU);
  g.fill();

  // Burning Cash Stacks (₹500 banknotes)
  const cashW = 140, cashH = 70;
  g.fillStyle = '#15803D'; // Indian ₹500 Green
  rr(g, -cashW / 2, 70, cashW, cashH, 8);
  g.fill();
  g.strokeStyle = 'rgba(255,255,255,0.4)';
  g.lineWidth = 2;
  g.stroke();

  g.font = '800 24px InterTight, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'center';
  g.fillText("₹5,00,000", 0, 112);

  // 8. Animated Fire & Smoke Particles rising from the money
  for (let i = 0; i < 9; i++) {
    const pProg = ((t * 2.8 + i * 0.14) % 1.0);
    const fx = -50 + i * 13 + Math.sin(t * 8 + i) * 8;
    const fy = 70 - pProg * 85;
    const fSize = (1.0 - pProg) * 22;

    // Fire Gradient
    const grFire = g.createRadialGradient(fx, fy, 0, fx, fy, fSize);
    grFire.addColorStop(0, '#FFFFFF');
    grFire.addColorStop(0.3, '#F59E0B');
    grFire.addColorStop(0.7, '#EF4444');
    grFire.addColorStop(1, 'rgba(239, 68, 68, 0)');
    g.fillStyle = grFire;
    g.beginPath();
    g.arc(fx, fy, fSize, 0, TAU);
    g.fill();
  }

  // Smoke Puffs
  for (let s = 0; s < 5; s++) {
    const sProg = ((t * 1.5 + s * 0.22) % 1.0);
    const sx = -40 + s * 22 + Math.sin(t * 4 + s) * 16;
    const sy = 30 - sProg * 110;
    const sSize = 14 + sProg * 28;
    const sAlpha = (1.0 - sProg) * 0.45;
    g.fillStyle = `rgba(148, 163, 184, ${sAlpha})`;
    g.beginPath();
    g.arc(sx, sy, sSize, 0, TAU);
    g.fill();
  }

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. THE NOCTURNAL LUXURY BUYER (Dr. Daniels at 11:42 PM)
// Luxury NRI buyer in bed, illuminated by intense glowing smartphone screen
// ─────────────────────────────────────────────────────────────────────────────
export function drawBuyerCharacter(g, cx, cy, t, opts = {}) {
  g.save();
  g.translate(cx, cy);

  // Background Bedroom Ambience (Moody midnight blue)
  const bgGr = g.createRadialGradient(0, 0, 40, 0, 0, 320);
  bgGr.addColorStop(0, 'rgba(15, 23, 42, 0.9)');
  bgGr.addColorStop(1, 'rgba(3, 7, 18, 0.95)');
  g.fillStyle = bgGr;
  rr(g, -260, -180, 520, 380, 32);
  g.fill();

  // Floating Digital Wall Clock: 11:42 PM
  const colonBlink = (Math.sin(t * 4) > 0) ? ":" : " ";
  g.font = '700 28px JBMono, monospace';
  g.fillStyle = 'rgba(239, 68, 68, 0.85)';
  g.textAlign = 'center';
  g.fillText(`11${colonBlink}42 PM`, 0, -130);

  g.font = '600 13px Inter, sans-serif';
  g.fillStyle = 'rgba(148, 163, 184, 0.8)';
  g.fillText("NOCTURNAL HIGH-TICKET INQUIRY", 0, -105);

  // Pillows & Headrest
  g.fillStyle = '#1E293B';
  g.beginPath();
  g.ellipse(0, -10, 160, 70, 0, 0, TAU);
  g.fill();

  // Buyer Head
  g.fillStyle = '#C28258';
  g.beginPath();
  g.ellipse(0, 10, 55, 62, 0, 0, TAU);
  g.fill();

  // Dark hair
  g.fillStyle = '#0F172A';
  g.beginPath();
  g.arc(0, -6, 58, Math.PI * 0.9, Math.PI * 2.1);
  g.fill();

  // Closed relaxed eyebrows & eyes glancing down at phone
  g.strokeStyle = '#0F172A';
  g.lineWidth = 3.5;
  g.beginPath();
  g.arc(-22, 12, 10, 0.1, Math.PI * 0.9);
  g.stroke();
  g.beginPath();
  g.arc(22, 12, 10, 0.1, Math.PI * 0.9);
  g.stroke();

  // Subtle satisfied smile
  g.beginPath();
  g.arc(0, 36, 12, 0.2, Math.PI * 0.8);
  g.stroke();

  // Smart Phone held in hands
  const phoneY = 85 + Math.sin(t * 3) * 3;
  g.fillStyle = '#020617';
  rr(g, -55, phoneY, 110, 160, 18);
  g.fill();
  g.strokeStyle = 'rgba(0, 229, 255, 0.6)';
  g.lineWidth = 2;
  g.stroke();

  // Intense Screen Glow illuminating Buyer's face
  const screenGlow = g.createRadialGradient(0, phoneY + 50, 10, 0, phoneY - 40, 190);
  screenGlow.addColorStop(0, 'rgba(0, 229, 255, 0.45)');
  screenGlow.addColorStop(0.5, 'rgba(0, 229, 255, 0.18)');
  screenGlow.addColorStop(1, 'rgba(0, 229, 255, 0)');
  g.fillStyle = screenGlow;
  g.fillRect(-180, -80, 360, 280);

  // Inside phone screen: Submit Inquiry Button with Pulsing Tap Ripple
  g.fillStyle = '#0F172A';
  rr(g, -46, phoneY + 12, 92, 136, 12);
  g.fill();

  // Property thumbnail on phone
  g.fillStyle = 'rgba(0, 229, 255, 0.25)';
  rr(g, -40, phoneY + 22, 80, 42, 6);
  g.fill();
  g.font = '700 9px Inter, sans-serif';
  g.fillStyle = '#38BDF8';
  g.fillText("ECR VILLA", 0, phoneY + 46);

  // Submit button
  const tapPulse = (t * 3) % 1.0;
  g.fillStyle = '#10B981';
  rr(g, -38, phoneY + 80, 76, 26, 8);
  g.fill();
  g.font = '700 10px Inter, sans-serif';
  g.fillStyle = '#FFFFFF';
  g.fillText("SUBMIT", 0, phoneY + 97);

  // Expanding Tap Ripple
  g.beginPath();
  g.arc(0, phoneY + 93, tapPulse * 28, 0, TAU);
  g.strokeStyle = `rgba(16, 185, 129, ${(1.0 - tapPulse) * 0.9})`;
  g.lineWidth = 2.5;
  g.stroke();

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. THE SLEEPING TELECALLER (Human Sales Desk Failure)
// Human caller asleep at desk, face on keyboard, loud "Zzz" snore bubbles, phone off hook
// ─────────────────────────────────────────────────────────────────────────────
export function drawSleepingCallerCharacter(g, cx, cy, t, opts = {}) {
  g.save();
  g.translate(cx, cy);

  // Desk Surface
  g.fillStyle = '#1E293B';
  rr(g, -240, 70, 480, 140, 16);
  g.fill();
  g.strokeStyle = 'rgba(255, 255, 255, 0.08)';
  g.lineWidth = 2;
  g.stroke();

  // Sleeping Telecaller Body (Slumped forward over desk)
  const snoreBreathe = Math.sin(t * 3.5) * 6;
  g.fillStyle = '#334155';
  g.beginPath();
  g.ellipse(20, 75 + snoreBreathe, 110, 65, 0, 0, TAU);
  g.fill();

  // Head resting face-down on keyboard
  g.fillStyle = '#F59E0B';
  g.beginPath();
  g.ellipse(-10, 55 + snoreBreathe, 52, 44, -0.2, 0, TAU);
  g.fill();

  // Messy hair
  g.fillStyle = '#0F172A';
  g.beginPath();
  g.arc(-15, 38 + snoreBreathe, 48, Math.PI * 0.8, Math.PI * 2.2);
  g.fill();

  // Cold coffee mug with cobweb
  g.fillStyle = '#64748B';
  rr(g, 150, 40, 40, 45, 6);
  g.fill();
  g.font = '600 11px Inter, sans-serif';
  g.fillStyle = '#94A3B8';
  g.textAlign = 'center';
  g.fillText("COLD", 170, 68);

  // Desk Phone Unanswered (Flashing red LED & vibrating)
  const phoneShake = Math.sin(t * 30) * 4;
  g.fillStyle = '#0F172A';
  rr(g, -190 + phoneShake, 20, 65, 60, 12);
  g.fill();
  // Flashing Red Alert Light
  const alertBlink = (Math.sin(t * 12) > 0) ? '#EF4444' : '#7F1D1D';
  g.fillStyle = alertBlink;
  g.beginPath();
  g.arc(-160 + phoneShake, 35, 8, 0, TAU);
  g.fill();

  g.font = '700 11px JBMono, monospace';
  g.fillStyle = '#EF4444';
  g.fillText("RINGING", -160 + phoneShake, 64);

  // Animated Floating Snore "Zzz" Bubbles
  for (let z = 0; z < 3; z++) {
    const zProg = ((t * 0.8 + z * 0.33) % 1.0);
    const zx = -10 + zProg * 65 + Math.sin(t * 3 + z) * 15;
    const zy = 10 - zProg * 140;
    const zSize = 16 + zProg * 26;
    const zAlpha = (1.0 - zProg);

    g.font = `800 ${zSize}px InterTight, sans-serif`;
    g.fillStyle = `rgba(148, 163, 184, ${zAlpha * 0.9})`;
    g.fillText("Z", zx, zy);
  }

  // Warning Badge
  pill(g, -110, -100, "⚠️ HUMAN DESK: 4-6 HR DELAY", {
    color: '#EF4444', bg: 'rgba(239, 68, 68, 0.15)', px: 13
  });

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. HOLOGRAPHIC AI CLOSER AVATARS (Maya, Pallavi, Swati)
// Animated avatars with dynamic lip sync, glowing headsets, and certification stamps
// ─────────────────────────────────────────────────────────────────────────────
export function drawAICloserAvatar(g, cx, cy, t, persona = 'maya', opts = {}) {
  g.save();
  g.translate(cx, cy);

  let mainColor = '#00E5FF';
  let badgeText = "MAYA (ENGLISH NRI DESK)";
  let accentTag = "8.4% YIELD CERTIFIED";

  if (persona === 'pallavi') {
    mainColor = '#10B981';
    badgeText = "PALLAVI (CHENNAI & ECR DESK)";
    accentTag = "TN-RERA APPROVED";
  } else if (persona === 'swati') {
    mainColor = '#C084FC';
    badgeText = "SWATI (DELHI NCR DESK)";
    accentTag = "DLF PENTHOUSE VIP VISIT";
  }

  // Holographic Aura Rings
  for (let r = 1; r <= 3; r++) {
    const rSize = 130 + ((t * 30 + r * 35) % 80);
    const rAlpha = clamp(1.0 - (rSize - 130) / 80) * 0.35;
    g.strokeStyle = rgba(mainColor, rAlpha);
    g.lineWidth = 2;
    g.beginPath();
    g.arc(0, 0, rSize, 0, TAU);
    g.stroke();
  }

  // Cybernetic Glowing Collar & Shoulders
  g.fillStyle = '#0A1324';
  g.beginPath();
  g.ellipse(0, 135, 120, 70, 0, 0, TAU);
  g.fill();
  g.strokeStyle = rgba(mainColor, 0.5);
  g.lineWidth = 2.5;
  g.stroke();

  // Head
  g.fillStyle = (persona === 'maya') ? '#F2C6A0' : (persona === 'pallavi') ? '#B47854' : '#E2A980';
  g.beginPath();
  g.ellipse(0, 15, 62, 72, 0, 0, TAU);
  g.fill();

  // Stylized Hair
  g.fillStyle = '#1A1D28';
  g.beginPath();
  g.arc(0, -6, 68, Math.PI * 0.85, Math.PI * 2.15);
  g.fill();
  // Side locks
  rr(g, -66, -6, 16, 85, 8);
  g.fill();
  rr(g, 50, -6, 16, 85, 8);
  g.fill();

  // Eyes with blinking
  const eyeBlink = (t % 3.6 < 0.12) ? 0.08 : 1.0;
  g.fillStyle = '#FFFFFF';
  g.beginPath();
  g.ellipse(-24, 15, 16, 18 * eyeBlink, 0, 0, TAU);
  g.fill();
  g.beginPath();
  g.ellipse(24, 15, 16, 18 * eyeBlink, 0, 0, TAU);
  g.fill();

  if (eyeBlink > 0.3) {
    g.fillStyle = '#0F172A';
    g.beginPath();
    g.arc(-24, 15, 7.5, 0, TAU);
    g.fill();
    g.beginPath();
    g.arc(24, 15, 7.5, 0, TAU);
    g.fill();
    // Catchlight
    g.fillStyle = '#FFFFFF';
    g.beginPath();
    g.arc(-26, 12, 3, 0, TAU);
    g.fill();
    g.beginPath();
    g.arc(22, 12, 3, 0, TAU);
    g.fill();
  }

  // Dynamic Lip Sync Mouth (moves with speech wave)
  const mouthOpen = Math.abs(Math.sin(t * 14)) * 14;
  g.fillStyle = '#831843';
  g.beginPath();
  g.ellipse(0, 54, 15, 6 + mouthOpen, 0, 0, TAU);
  g.fill();
  g.fillStyle = '#FFFFFF';
  rr(g, -8, 48, 16, 4, 2);
  g.fill();

  // Glowing High-Tech Headset with Microphone Diode
  g.strokeStyle = mainColor;
  g.lineWidth = 4;
  g.beginPath();
  g.arc(0, 0, 72, Math.PI * 0.95, Math.PI * 1.8);
  g.stroke();

  // Headset Earcup
  g.fillStyle = '#0F172A';
  g.beginPath();
  g.arc(66, 15, 16, 0, TAU);
  g.fill();
  g.strokeStyle = mainColor;
  g.lineWidth = 2.5;
  g.stroke();

  // Mic Boom extending to mouth
  g.beginPath();
  g.moveTo(66, 22);
  g.lineTo(35, 52);
  g.stroke();

  // Mic Tip with Audio Pulsing Diode
  const micPulse = (Math.sin(t * 16) + 1) * 0.5;
  g.fillStyle = mainColor;
  g.shadowColor = mainColor;
  g.shadowBlur = 14;
  g.beginPath();
  g.arc(32, 53, 5 + micPulse * 2, 0, TAU);
  g.fill();
  g.shadowColor = 'transparent';

  // Persona Pill Header
  pill(g, -135, -115, badgeText, {
    color: mainColor, bg: 'rgba(15, 23, 42, 0.9)', px: 12
  });

  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. KARAOKE-STYLE WORD-BY-WORD ANIMATED SUBTITLES (Alex Hormozi Style)
// Active word pops with spring bounce, glowing yellow/lime highlight, and emojis!
// ─────────────────────────────────────────────────────────────────────────────
export const HORMOZI_TRACKS = [
  {
    t0: 0.5, t1: 4.2, emoji: "💸",
    words: [
      { w: "Builders", dt: 0.0, e: "👷‍♂️" },
      { w: "spend", dt: 0.4 },
      { w: "LAKHS", dt: 0.9, e: "💰" },
      { w: "on", dt: 1.5 },
      { w: "Meta", dt: 1.9 },
      { w: "&", dt: 2.4 },
      { w: "Google", dt: 2.7 },
      { w: "ads.", dt: 3.2, e: "📊" }
    ]
  },
  {
    t0: 4.3, t1: 7.9, emoji: "📉",
    words: [
      { w: "70%", dt: 0.0, e: "⚠️" },
      { w: "of", dt: 0.5 },
      { w: "luxury", dt: 0.9 },
      { w: "leads", dt: 1.4 },
      { w: "EVAPORATE", dt: 1.9, e: "💨" },
      { w: "into", dt: 2.5 },
      { w: "thin", dt: 2.9 },
      { w: "air.", dt: 3.3 }
    ]
  },
  {
    t0: 8.1, t1: 13.5, emoji: "🌙",
    words: [
      { w: "At", dt: 0.0 },
      { w: "JSM", dt: 0.4, e: "📍" },
      { w: "in", dt: 0.8 },
      { w: "Chennai,", dt: 1.1 },
      { w: "inquiries", dt: 1.6 },
      { w: "arrive", dt: 2.2 },
      { w: "at", dt: 2.6 },
      { w: "11:42", dt: 3.0, e: "🌙" },
      { w: "PM.", dt: 3.7 }
    ]
  },
  {
    t0: 13.6, t1: 19.6, emoji: "🧗",
    words: [
      { w: "Sales", dt: 0.0 },
      { w: "teams", dt: 0.4 },
      { w: "are", dt: 0.7 },
      { w: "ASLEEP.", dt: 1.0, e: "😴" },
      { w: "After", dt: 1.7 },
      { w: "5", dt: 2.2, e: "⏱️" },
      { w: "minutes,", dt: 2.6 },
      { w: "intent", dt: 3.3 },
      { w: "DROPS", dt: 3.8, e: "📉" },
      { w: "off", dt: 4.4 },
      { w: "a", dt: 4.7 },
      { w: "cliff.", dt: 5.0 }
    ]
  },
  {
    t0: 19.8, t1: 25.9, emoji: "🤖",
    words: [
      { w: "CLOSER", dt: 0.0, e: "⚡" },
      { w: "AI", dt: 0.5 },
      { w: "dials", dt: 0.9, e: "📞" },
      { w: "the", dt: 1.4 },
      { w: "lead", dt: 1.8 },
      { w: "in", dt: 2.2 },
      { w: "0.08", dt: 2.6, e: "🚀" },
      { w: "SECONDS.", dt: 3.3 }
    ]
  },
  {
    t0: 26.2, t1: 35.0, emoji: "🏢",
    words: [
      { w: "Maya:", dt: 0.0, e: "🎙️" },
      { w: '"Rental', dt: 0.8 },
      { w: "yield", dt: 1.4 },
      { w: "is", dt: 1.8 },
      { w: "8.4%.", dt: 2.2, e: "📈" },
      { w: "Sunday", dt: 3.5, e: "🗓️" },
      { w: "11", dt: 4.2 },
      { w: "AM", dt: 4.6 },
      { w: "is", dt: 5.1 },
      { w: 'reserved."', dt: 5.6 }
    ]
  },
  {
    t0: 35.2, t1: 41.0, emoji: "🏖️",
    words: [
      { w: "Pallavi:", dt: 0.0, e: "🎙️" },
      { w: "சென்னை", dt: 0.7 },
      { w: "ECR", dt: 1.4, e: "🏖️" },
      { w: "வில்லா", dt: 2.0 },
      { w: "RERA", dt: 2.8, e: "🛡️" },
      { w: "விவரங்கள்", dt: 3.4 },
      { w: "தயார்.", dt: 4.2 }
    ]
  },
  {
    t0: 41.2, t1: 46.0, emoji: "🏙️",
    words: [
      { w: "Swati:", dt: 0.0, e: "🎙️" },
      { w: "गोल्फ", dt: 0.6 },
      { w: "कोर्स", dt: 1.0 },
      { w: "पेंटहाउस", dt: 1.5, e: "🏢" },
      { w: "विज़िट", dt: 2.2, e: "🗓️" },
      { w: "बुक", dt: 2.8 },
      { w: "कर", dt: 3.3 },
      { w: "दी।", dt: 3.7 }
    ]
  },
  {
    t0: 46.3, t1: 52.4, emoji: "💬",
    words: [
      { w: "Live", dt: 0.0 },
      { w: "WhatsApp", dt: 0.4, e: "💬" },
      { w: "push:", dt: 1.0 },
      { w: "RERA", dt: 1.6, e: "📄" },
      { w: "floor", dt: 2.1 },
      { w: "plans", dt: 2.5 },
      { w: "&", dt: 2.9 },
      { w: "VIP", dt: 3.2, e: "🎟️" },
      { w: "pass.", dt: 3.8 }
    ]
  },
  {
    t0: 52.6, t1: 58.7, emoji: "💰",
    words: [
      { w: "Human:", dt: 0.0 },
      { w: "₹220.", dt: 0.5, e: "❌" },
      { w: "CLOSER", dt: 1.5 },
      { w: "AI:", dt: 2.0 },
      { w: "₹1.55", dt: 2.6, e: "⚡" },
      { w: "per", dt: 3.5 },
      { w: "call.", dt: 4.0 }
    ]
  },
  {
    t0: 58.9, t1: 64.6, emoji: "✍️",
    words: [
      { w: "Comment", dt: 0.0, e: "💬" },
      { w: '"CLOSER"', dt: 0.6, e: "🔥" },
      { w: "below", dt: 1.3, e: "👇" },
      { w: "for", dt: 1.8 },
      { w: "the", dt: 2.2 },
      { w: "free", dt: 2.6 },
      { w: "AI", dt: 3.1 },
      { w: "blueprint!", dt: 3.5, e: "🚀" }
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

  // Find currently spoken word index
  let activeIdx = 0;
  for (let i = 0; i < track.words.length; i++) {
    if (relT >= track.words[i].dt) {
      activeIdx = i;
    }
  }

  // Render container banner with dark glass backdrop
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

  // Specular Border
  g.strokeStyle = 'rgba(255, 255, 255, 0.22)';
  g.lineWidth = 1.5;
  rr(g, W / 2 - totalW / 2 + 0.5, py - totalH / 2 + 0.5, totalW - 1, totalH - 1, totalH / 2);
  g.stroke();

  // Measure word positions
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
      // Alex Hormozi Bouncing Pop
      const wordT = relT - item.dt;
      const bounceScale = (wordT < 0.18) ? (1.0 + Math.sin(wordT / 0.18 * Math.PI) * 0.25) : 1.05;

      g.translate(wordCenter, py);
      g.scale(bounceScale, bounceScale);

      // Contextual Emoji Popup above active word
      if (item.e) {
        g.font = '32px sans-serif';
        g.fillText(item.e, 0, -48);
      }

      // Glowing Neon Yellow Text
      g.font = '900 45px InterTight, sans-serif';
      g.shadowColor = 'rgba(250, 204, 21, 0.85)';
      g.shadowBlur = 18;
      g.fillStyle = '#FACC15'; // Neon Gold/Yellow
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
// 6. CINEMATIC GLITCH & RETENTION TRANSITIONS
// ─────────────────────────────────────────────────────────────────────────────
export function drawCutTransition(g, t, cutTimes = [], W, H) {
  for (const ct of cutTimes) {
    const dt = t - ct;
    if (dt >= 0 && dt <= 0.16) {
      // Chromatic Glitch Flash
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

// Subtle CRT Scanlines
export function drawScanlines(g, W, H) {
  g.save();
  g.fillStyle = 'rgba(0, 0, 0, 0.05)';
  for (let y = 0; y < H; y += 4) {
    g.fillRect(0, y, W, 1.5);
  }
  g.restore();
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
