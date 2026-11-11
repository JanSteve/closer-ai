// engine.js — CLOSER AI Award-Winning Keynote & Motion Visual Engine
// Higgsfield / Apple Keynote / Linear / Teenage Engineering standard.
// Features: 2.5D Virtual Camera, Strip Perspective 3D, Anamorphic Flares,
// Dual-Layer Bokeh Particles, Scrambled Digit Locks, Kinetic Dials, Waveforms.

import { clamp, lerp, seg, ss, eo, ei, eio, back, spring, mulberry, hash, TAU } from '/core/lib.js';
export { clamp, lerp, seg, ss, eo, ei, eio, back, spring, mulberry, hash, TAU };

export const W = 1920, H = 1080;

export const PAL = {
  bg0: '#030508',
  bg1: '#090E18',
  surf: '#0E1422',
  surf2: '#141D30',
  surf3: '#1B263E',
  line: 'rgba(255, 255, 255, 0.08)',
  lineHi: 'rgba(0, 229, 255, 0.40)',
  text: '#F8FAFC',
  dim: '#94A3B8',
  mute: '#64748B',
  accent: '#00E5FF',  // Electric Cyan (Hero Closer)
  lime: '#B7F34A',    // Luminous Lime (Unit Economics)
  red: '#FF4545',     // Crimson Alert (The Midnight Crisis)
  emerald: '#10B981', // Emerald (Tamil Desk - Pallavi)
  purple: '#C084FC',  // Violet (Hindi Desk - Swati)
  gold: '#FBBF24',
  white: '#FFFFFF'
};

export const FONT = { ui: 'Inter', disp: 'InterTight', mono: 'JBMono' };
export const font = (px, wt = 500, fam = 'ui') => `${wt} ${px}px ${FONT[fam] || fam}`;

export function rgba(hex, a) {
  if (hex.startsWith('rgba')) return hex;
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`;
}

// ───────────────────────── Offscreen Canvas Buffer Pool ─────────────────────────
const _pool = {};
export function buf(name, w = W, h = H) {
  let c = _pool[name];
  if (!c || c.width !== w || c.height !== h) {
    c = _pool[name] = document.createElement('canvas');
    c.width = w;
    c.height = h;
  }
  const g = c.getContext('2d');
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalAlpha = 1;
  g.globalCompositeOperation = 'source-over';
  g.filter = 'none';
  g.clearRect(0, 0, w, h);
  return [c, g];
}

// ───────────────────────── Rounded Rect Helper ─────────────────────────
export function rr(g, x, y, w, h, r) {
  g.beginPath();
  g.roundRect(x, y, w, h, Math.max(0, Math.min(r, w / 2, h / 2)));
}

// ───────────────────────── Radial Glow ─────────────────────────
export function glow(g, x, y, r, color, a) {
  if (a <= 0 || r <= 0) return;
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, rgba(color, a));
  gr.addColorStop(0.4, rgba(color, a * 0.35));
  gr.addColorStop(1, rgba(color, 0));
  g.fillStyle = gr;
  g.fillRect(x - r, y - r, r * 2, r * 2);
}

// ───────────────────────── Background & Multi-Color Volumetric Stage ─────────────────────────
export function bg(g, o = {}) {
  const { lift = 1, cyanGlow = 1, t = 0, cx = W * 0.5, cy = H * 0.38, tint = null } = o;
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.fillStyle = PAL.bg0;
  g.fillRect(0, 0, W, H);

  // Dynamic sweeping stage spotlight with organic drift
  const spotX = cx + Math.sin(t * 0.7) * 70;
  const spotY = cy + Math.cos(t * 0.5) * 45;
  let gr = g.createRadialGradient(spotX, spotY, 0, spotX, spotY, W * 0.85);
  gr.addColorStop(0, rgba(PAL.bg1, 0.98 * lift));
  gr.addColorStop(1, rgba(PAL.bg0, 0));
  g.fillStyle = gr;
  g.fillRect(0, 0, W, H);

  if (cyanGlow > 0) {
    glow(g, spotX, spotY, 920, tint || PAL.accent, 0.07 * cyanGlow);
  }
  g.restore();
}

// ───────────────────────── Dual-Layer Bokeh Particle System ─────────────────────────
// Higgsfield style: Out-of-focus soft foreground bokeh + sharp midground dust motes
export function cinematicBokeh(g, t, count = 42) {
  g.save();
  // 1. Out-of-focus Foreground Bokeh (large, soft, fast drifting)
  for (let i = 0; i < 8; i++) {
    const seed = i * 491.7;
    const speed = 0.04 + hash(seed) * 0.05;
    const x = ((hash(seed + 1) * W + t * speed * 70) % (W + 200)) - 100;
    const y = ((hash(seed + 2) * H + Math.sin(t * 0.4 + i) * 80) % (H + 200)) - 100;
    const r = 18 + hash(seed + 3) * 26;
    const alpha = 0.035 + 0.03 * Math.sin(t * 1.5 + i);
    const color = i % 2 === 0 ? PAL.accent : PAL.lime;
    
    glow(g, x, y, r * 2.5, color, alpha);
  }

  // 2. Midground Floating Dust Motes (sharp, gentle floating)
  for (let i = 0; i < count; i++) {
    const seed = i * 173.3 + 99;
    const speed = 0.06 + hash(seed) * 0.10;
    const x = ((hash(seed + 1) * W + t * speed * 35) % (W + 60)) - 30;
    const y = ((hash(seed + 2) * H + Math.sin(t * speed + i * 1.2) * 25) % (H + 60)) - 30;
    const r = 1.0 + hash(seed + 3) * 1.8;
    const alpha = 0.12 + 0.22 * Math.sin(t * 2.4 + i);
    const color = (i % 3 === 0) ? PAL.accent : (i % 3 === 1 ? PAL.lime : '#FFFFFF');

    g.fillStyle = rgba(color, alpha);
    g.beginPath();
    g.arc(x, y, r, 0, TAU);
    g.fill();
  }
  g.restore();
}

// ───────────────────────── Hairline Precision Grid ─────────────────────────
export function grid(g, o = {}) {
  const { ox = 0, oy = 0, scale = 1, module = 48, alpha = 1, rect = [0, 0, W, H] } = o;
  const step = module * scale;
  if (step < 4 || alpha <= 0) return;
  const [rx, ry, rw, rh] = rect;
  g.save();
  g.beginPath();
  g.rect(rx, ry, rw, rh);
  g.clip();
  g.lineWidth = 1;
  const i0 = Math.floor((rx - ox) / step), i1 = Math.ceil((rx + rw - ox) / step);
  const j0 = Math.floor((ry - oy) / step), j1 = Math.ceil((ry + rh - oy) / step);

  g.strokeStyle = `rgba(255, 255, 255, ${0.036 * alpha})`;
  g.beginPath();
  for (let i = i0; i <= i1; i++) {
    const x = Math.round(ox + i * step) + 0.5;
    g.moveTo(x, ry); g.lineTo(x, ry + rh);
  }
  for (let j = j0; j <= j1; j++) {
    const y = Math.round(oy + j * step) + 0.5;
    g.moveTo(rx, y); g.lineTo(rx + rw, y);
  }
  g.stroke();
  g.restore();
}

// ───────────────────────── Anamorphic Lens Flare ─────────────────────────
// Horizontal optical streak characteristic of Hollywood anamorphic lenses and Higgsfield renders
export function anamorphicFlare(g, cx, cy, len = 900, color = PAL.accent, intensity = 1.0) {
  if (intensity <= 0) return;
  g.save();
  g.globalCompositeOperation = 'lighter';

  // Core brilliant center hot spot
  glow(g, cx, cy, 70, '#FFFFFF', 0.45 * intensity);
  glow(g, cx, cy, 140, color, 0.6 * intensity);

  // Horizontal primary streak
  const streakH = 4;
  const gr = g.createLinearGradient(cx - len / 2, cy, cx + len / 2, cy);
  gr.addColorStop(0, 'rgba(0,0,0,0)');
  gr.addColorStop(0.3, rgba(color, 0.18 * intensity));
  gr.addColorStop(0.5, rgba('#FFFFFF', 0.95 * intensity));
  gr.addColorStop(0.7, rgba(color, 0.18 * intensity));
  gr.addColorStop(1, 'rgba(0,0,0,0)');

  g.fillStyle = gr;
  g.fillRect(cx - len / 2, cy - streakH / 2, len, streakH);

  // Soft secondary horizontal bloom
  const haloH = 22;
  const grHalo = g.createLinearGradient(cx - len * 0.4, cy, cx + len * 0.4, cy);
  grHalo.addColorStop(0, 'rgba(0,0,0,0)');
  grHalo.addColorStop(0.5, rgba(color, 0.25 * intensity));
  grHalo.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = grHalo;
  g.fillRect(cx - len * 0.4, cy - haloH / 2, len * 0.8, haloH);

  g.restore();
}

// ───────────────────────── 2.5D Virtual Camera ─────────────────────────
export function camera(c) {
  const { x = W / 2, y = H / 2, zoom = 1, rot = 0, sx = 0, sy = 0 } = c;
  const inv = 1 / Math.max(zoom, 0.01);

  const proj = (px, py, z = 0) => {
    const d = inv - z;
    if (d <= 0.02) return null;
    const s = 1 / d;
    let X = (px - x) * s, Y = (py - y) * s;
    const cr = Math.cos(rot), sr = Math.sin(rot);
    return { x: W / 2 + X * cr - Y * sr + sx, y: H / 2 + X * sr + Y * cr + sy, s };
  };

  const apply = (g, z = 0) => {
    const d = inv - z, s = 1 / Math.max(d, 0.02);
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.translate(W / 2 + sx, H / 2 + sy);
    g.rotate(rot);
    g.scale(s, s);
    g.translate(-x, -y);
    return s;
  };

  return { x, y, zoom, rot, sx, sy, proj, apply };
}

// ───────────────────────── Strip Perspective 3D Slicing ─────────────────────────
// Renders an offscreen canvas in true 3D perspective with Y-axis yaw (rotY in radians)
export function perspective3D(g, src, cx, cy, w, h, rotY, o = {}) {
  const { slices = 96, dist = 2.4, alpha = 1, shadow = true } = o;
  if (Math.abs(rotY) < 0.001) {
    g.save();
    g.globalAlpha *= alpha;
    if (shadow) {
      g.shadowColor = 'rgba(0,0,0,0.6)';
      g.shadowBlur = 40;
      g.shadowOffsetY = 16;
    }
    g.drawImage(src, cx - w / 2, cy - h / 2, w, h);
    g.restore();
    return;
  }

  const D = dist * w;
  const cs = Math.cos(rotY), sn = Math.sin(rotY);
  const map = (u, v) => {
    const X = (u - 0.5) * w;
    const Z = X * sn;
    const f = D / (D + Z);
    return [cx + X * cs * f, cy + (v - 0.5) * h * f];
  };

  g.save();
  g.globalAlpha *= alpha;

  if (shadow) {
    g.save();
    g.fillStyle = 'rgba(0,0,0,0.55)';
    g.beginPath();
    const p0 = map(0, 1), p1 = map(1, 1);
    g.ellipse((p0[0] + p1[0]) / 2, Math.max(p0[1], p1[1]) + 20, (Math.abs(p1[0] - p0[0])) * 0.55, 18, 0, 0, TAU);
    g.fill();
    g.restore();
  }

  const sw = src.width / slices;
  for (let i = 0; i < slices; i++) {
    const u0 = i / slices, u1 = (i + 1) / slices;
    const [x0] = map(u0, 0.5), [x1] = map(u1, 0.5);
    const X = ((u0 + u1) / 2 - 0.5) * w;
    const f = D / (D + X * sn);
    const hh = h * f;
    const segW = Math.abs(x1 - x0) + 0.8;
    g.drawImage(src, i * sw, 0, sw, src.height, Math.min(x0, x1) - 0.4, cy - hh / 2, segW, hh);
  }
  g.restore();
}

// ───────────────────────── 3D Tilt Panel with Dynamic Specular Edge ─────────────────────────
export function panel3D(g, x, y, w, h, o = {}) {
  const { r = 20, fill = PAL.surf, stroke = PAL.line, shadow = 1, alpha = 1, lightTop = true } = o;
  g.save();
  g.globalAlpha *= alpha;

  if (shadow > 0) {
    g.shadowColor = 'rgba(0, 0, 0, 0.72)';
    g.shadowBlur = Math.min(95, 24 + h * 0.16);
    g.shadowOffsetY = Math.min(42, 10 + h * 0.07);
    g.fillStyle = fill;
    rr(g, x, y, w, h, r);
    g.fill();
    g.shadowColor = 'transparent';
  }

  // Linear dark glass gradient
  const gr = g.createLinearGradient(0, y, 0, y + h);
  gr.addColorStop(0, '#192338');
  gr.addColorStop(0.25, fill);
  gr.addColorStop(1, fill);
  g.fillStyle = gr;
  rr(g, x, y, w, h, r);
  g.fill();

  // 1px hairline border
  g.lineWidth = 1;
  g.strokeStyle = stroke;
  rr(g, x + 0.5, y + 0.5, w - 1, h - 1, r);
  g.stroke();

  // Specular top highlight
  if (lightTop) {
    g.strokeStyle = 'rgba(255, 255, 255, 0.20)';
    g.beginPath();
    g.moveTo(x + r, y + 1.5);
    g.lineTo(x + w - r, y + 1.5);
    g.stroke();
  }

  g.restore();
}

// ───────────────────────── Status Pill Badge ─────────────────────────
export function pill(g, x, y, text, o = {}) {
  const { color = PAL.accent, bg = PAL.surf3, px = 13, icon = '', stroke = null } = o;
  g.save();
  g.font = font(px, 600, 'mono');
  const fullText = (icon ? icon + '  ' : '') + text;
  const tw = g.measureText(fullText).width;
  const pw = tw + 26, ph = px * 1.9;
  panel3D(g, x, y - ph / 2, pw, ph, { r: ph / 2, fill: bg, stroke: stroke || rgba(color, 0.35), shadow: 0 });
  g.fillStyle = color;
  g.textBaseline = 'middle';
  g.fillText(fullText, x + 13, y);
  g.restore();
  return pw;
}

// ───────────────────────── Circular Precision Latency Dial ─────────────────────────
export function drawRadialDial(g, cx, cy, r, progress, valueStr, labelStr, color = PAL.accent) {
  g.save();
  // Background track
  g.beginPath();
  g.arc(cx, cy, r, Math.PI * 0.75, Math.PI * 2.25);
  g.lineWidth = 8;
  g.strokeStyle = 'rgba(255, 255, 255, 0.08)';
  g.lineCap = 'round';
  g.stroke();

  // Active progress arc with spring glow
  const angle = Math.PI * 0.75 + progress * (Math.PI * 1.5);
  g.beginPath();
  g.arc(cx, cy, r, Math.PI * 0.75, angle);
  g.lineWidth = 9;
  g.strokeStyle = color;
  g.shadowColor = rgba(color, 0.85);
  g.shadowBlur = 20;
  g.stroke();
  g.shadowColor = 'transparent';

  // Center Value
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.font = font(52, 700, 'disp');
  g.fillStyle = '#FFFFFF';
  g.fillText(valueStr, cx, cy - 8);

  g.font = font(14, 600, 'mono');
  g.fillStyle = color;
  g.fillText(labelStr, cx, cy + 34);

  g.restore();
}

// ───────────────────────── Mirrored Organic Waveform Ribbons ─────────────────────────
export function drawWaveform(g, cx, cy, w, h, t, o = {}) {
  const { bars = 52, color = PAL.accent, active = true, alpha = 1, energy = 1.0 } = o;
  g.save();
  g.globalAlpha *= alpha;
  const step = w / bars;
  const barW = Math.max(3.5, step * 0.58);

  for (let i = 0; i < bars; i++) {
    const x = cx - w / 2 + i * step + step / 2;
    const normI = (i - bars / 2) / (bars / 2);
    const envelope = Math.cos(normI * Math.PI * 0.48); // cosine taper at ends

    let amp = 0.14;
    if (active) {
      const f1 = Math.sin(t * 14 + i * 0.65);
      const f2 = Math.cos(t * 22 - i * 0.42);
      const f3 = Math.sin(t * 8 + i * 1.1);
      amp = Math.abs(f1 * 0.45 + f2 * 0.35 + f3 * 0.2) * envelope * energy;
      amp = Math.max(0.12, Math.min(1.0, amp));
    }
    const bh = Math.max(6, h * amp);

    if (active && amp > 0.42) {
      glow(g, x, cy, bh * 0.8, color, 0.18 * amp);
    }

    g.fillStyle = active ? (amp > 0.65 ? '#FFFFFF' : (amp > 0.38 ? color : rgba(color, 0.85))) : PAL.mute;
    rr(g, x - barW / 2, cy - bh / 2, barW, bh, barW / 2);
    g.fill();
  }
  g.restore();
}

// ───────────────────────── Mechanical Rolling Scrambled Digits ─────────────────────────
const GLYPHS = '0123456789%₹$.,<>';
export function rollingNumber(targetStr, progress, seed = 42) {
  if (progress >= 1) return targetStr;
  let out = '';
  for (let i = 0; i < targetStr.length; i++) {
    const char = targetStr[i];
    if (char === '.' || char === ',' || char === ' ' || char === '₹' || char === '$' || char === '%') {
      out += char;
      continue;
    }
    const charProgress = clamp((progress - (i * 0.08)) / 0.5);
    if (charProgress >= 1) {
      out += char;
    } else {
      const rndIndex = Math.floor(hash(seed + i * 17 + Math.floor(progress * 42)) * GLYPHS.length);
      out += GLYPHS[rndIndex];
    }
  }
  return out;
}

// ───────────────────────── Light Sweep Band ─────────────────────────
export function lightSweep(g, x, y, w, h, progress, color = 'rgba(255,255,255,0.30)') {
  if (progress < 0 || progress > 1) return;
  g.save();
  g.beginPath();
  g.rect(x, y, w, h);
  g.clip();
  const d = Math.hypot(w, h);
  const sx = x - d * 0.3 + progress * d * 1.6;
  const gr = g.createLinearGradient(sx - 160, y, sx + 160, y + h * 0.4);
  gr.addColorStop(0, 'rgba(255,255,255,0)');
  gr.addColorStop(0.5, color);
  gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.globalCompositeOperation = 'lighter';
  g.fillStyle = gr;
  g.fillRect(x, y, w, h);
  g.restore();
}

// ───────────────────────── Cinematic Corner Vignette ─────────────────────────
export function vignette(g, a = 0.55) {
  const gr = g.createRadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 1.05);
  gr.addColorStop(0, 'rgba(0,0,0,0)');
  gr.addColorStop(1, `rgba(0,0,0,${a})`);
  g.fillStyle = gr;
  g.fillRect(0, 0, W, H);
}
