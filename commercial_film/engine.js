// engine.js — CLOSER AI Award-Winning Keynote Visual Engine (Apple / Linear / Teenage Engineering standard)
import { clamp, lerp, seg, ss, eo, ei, eio, back, spring, mulberry, hash, TAU } from '/core/lib.js';
export { clamp, lerp, seg, ss, eo, ei, eio, back, spring, mulberry, hash, TAU };

export const W = 1920, H = 1080;

export const PAL = {
  bg0: '#030508',
  bg1: '#0A0E17',
  surf: '#0F1522',
  surf2: '#151D2E',
  surf3: '#1C273E',
  line: 'rgba(255, 255, 255, 0.08)',
  lineHi: 'rgba(0, 229, 255, 0.35)',
  text: '#F8FAFC',
  dim: '#94A3B8',
  mute: '#64748B',
  accent: '#00E5FF',  // Electric Cyan
  lime: '#B7F34A',    // Luminous Lime
  red: '#FF4545',     // Crimson Alert
  emerald: '#10B981', // Native Emerald
  purple: '#C084FC',  // Violet Accent
  gold: '#FBBF24'
};

export const FONT = { ui: 'Inter', disp: 'InterTight', mono: 'JBMono' };
export const font = (px, wt = 500, fam = 'ui') => `${wt} ${px}px ${FONT[fam] || fam}`;

export function rgba(hex, a) {
  if (hex.startsWith('rgba')) return hex;
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`;
}

export function rr(g, x, y, w, h, r) {
  g.beginPath();
  g.roundRect(x, y, w, h, Math.max(0, Math.min(r, w / 2, h / 2)));
}

export function glow(g, x, y, r, color, a) {
  if (a <= 0 || r <= 0) return;
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, rgba(color, a));
  gr.addColorStop(0.4, rgba(color, a * 0.4));
  gr.addColorStop(1, rgba(color, 0));
  g.fillStyle = gr;
  g.fillRect(x - r, y - r, r * 2, r * 2);
}

// Stage background with moving spotlight and vignette
export function bg(g, o = {}) {
  const { lift = 1, cyanGlow = 1, t = 0, cx = W * 0.5, cy = H * 0.36 } = o;
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.fillStyle = PAL.bg0;
  g.fillRect(0, 0, W, H);
  
  // Dynamic subtle drifting stage spotlight
  const spotX = cx + Math.sin(t * 0.8) * 60;
  const spotY = cy + Math.cos(t * 0.6) * 40;
  let gr = g.createRadialGradient(spotX, spotY, 0, spotX, spotY, W * 0.8);
  gr.addColorStop(0, rgba(PAL.bg1, 0.98 * lift));
  gr.addColorStop(1, rgba(PAL.bg0, 0));
  g.fillStyle = gr;
  g.fillRect(0, 0, W, H);

  if (cyanGlow > 0) {
    glow(g, spotX, spotY, 850, PAL.accent, 0.06 * cyanGlow);
  }
  g.restore();
}

// Drifting micro-particles for depth
export function particles(g, t, count = 35) {
  g.save();
  for (let i = 0; i < count; i++) {
    const seed = i * 133.7;
    const speed = 0.08 + (hash(seed) * 0.12);
    const x = ((hash(seed + 1) * W + t * speed * 40) % (W + 80)) - 40;
    const y = ((hash(seed + 2) * H + Math.sin(t * speed + i) * 30) % (H + 80)) - 40;
    const r = 1.0 + hash(seed + 3) * 2.0;
    const alpha = 0.15 + 0.25 * Math.sin(t * 2 + i);

    g.fillStyle = i % 2 === 0 ? rgba(PAL.accent, alpha) : rgba(PAL.lime, alpha * 0.8);
    g.beginPath();
    g.arc(x, y, r, 0, TAU);
    g.fill();
  }
  g.restore();
}

// Hairline precision grid
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
  
  g.strokeStyle = `rgba(255, 255, 255, ${0.038 * alpha})`;
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

export function vignette(g, a = 0.55) {
  const gr = g.createRadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 1.05);
  gr.addColorStop(0, 'rgba(0,0,0,0)');
  gr.addColorStop(1, `rgba(0,0,0,${a})`);
  g.fillStyle = gr;
  g.fillRect(0, 0, W, H);
}

// 3D Tilt Panel with dynamic edge lighting
export function panel3D(g, x, y, w, h, o = {}) {
  const { r = 20, fill = PAL.surf, stroke = PAL.line, shadow = 1, alpha = 1, tilt = 0 } = o;
  g.save();
  g.globalAlpha *= alpha;

  if (shadow > 0) {
    g.shadowColor = 'rgba(0, 0, 0, 0.7)';
    g.shadowBlur = Math.min(90, 24 + h * 0.16);
    g.shadowOffsetY = Math.min(36, 10 + h * 0.06);
    g.fillStyle = fill;
    rr(g, x, y, w, h, r);
    g.fill();
    g.shadowColor = 'transparent';
  }
  
  // Linear glass gradient fill
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

  // High-spec top edge light
  g.strokeStyle = 'rgba(255, 255, 255, 0.18)';
  g.beginPath();
  g.moveTo(x + r, y + 1.5);
  g.lineTo(x + w - r, y + 1.5);
  g.stroke();

  g.restore();
}

export function pill(g, x, y, text, o = {}) {
  const { color = PAL.accent, bg = PAL.surf3, px = 13, icon = '' } = o;
  g.save();
  g.font = font(px, 600, 'mono');
  const fullText = (icon ? icon + '  ' : '') + text;
  const tw = g.measureText(fullText).width;
  const pw = tw + 26, ph = px * 1.9;
  panel3D(g, x, y - ph / 2, pw, ph, { r: ph / 2, fill: bg, stroke: rgba(color, 0.35), shadow: 0 });
  g.fillStyle = color;
  g.textBaseline = 'middle';
  g.fillText(fullText, x + 13, y);
  g.restore();
  return pw;
}

// Circular Precision Latency Dial
export function drawRadialDial(g, cx, cy, r, progress, valueStr, labelStr, color = PAL.accent) {
  g.save();
  // Background track
  g.beginPath();
  g.arc(cx, cy, r, Math.PI * 0.75, Math.PI * 2.25);
  g.lineWidth = 8;
  g.strokeStyle = 'rgba(255, 255, 255, 0.08)';
  g.lineCap = 'round';
  g.stroke();

  // Active progress arc
  const angle = Math.PI * 0.75 + progress * (Math.PI * 1.5);
  g.beginPath();
  g.arc(cx, cy, r, Math.PI * 0.75, angle);
  g.lineWidth = 9;
  g.strokeStyle = color;
  g.shadowColor = rgba(color, 0.8);
  g.shadowBlur = 18;
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
  g.fillText(labelStr, cx, cy + 32);

  g.restore();
}

// Mirrored Organic Waveform Ribbons
export function drawWaveform(g, cx, cy, w, h, t, o = {}) {
  const { bars = 48, color = PAL.accent, active = true, alpha = 1, energy = 1.0 } = o;
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
    
    if (active && amp > 0.45) {
      glow(g, x, cy, bh * 0.75, color, 0.16 * amp);
    }
    
    // Gradient coloring on high bars
    g.fillStyle = active ? (amp > 0.65 ? '#FFFFFF' : (amp > 0.4 ? color : rgba(color, 0.8))) : PAL.mute;
    rr(g, x - barW / 2, cy - bh / 2, barW, bh, barW / 2);
    g.fill();
  }
  g.restore();
}

// Rolling scrambled numbers
export function rollingNumber(targetStr, progress, seed = 42) {
  if (progress >= 1) return targetStr;
  const glyphs = '0123456789%₹$.,<>';
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
      const rndIndex = Math.floor(hash(seed + i * 17 + Math.floor(progress * 40)) * glyphs.length);
      out += glyphs[rndIndex];
    }
  }
  return out;
}

// Light sweep band
export function lightSweep(g, x, y, w, h, progress, color = 'rgba(255,255,255,0.25)') {
  if (progress < 0 || progress > 1) return;
  g.save();
  g.beginPath();
  g.rect(x, y, w, h);
  g.clip();
  const d = Math.hypot(w, h);
  const sx = x - d * 0.3 + progress * d * 1.6;
  const gr = g.createLinearGradient(sx - 150, y, sx + 150, y + h * 0.4);
  gr.addColorStop(0, 'rgba(255,255,255,0)');
  gr.addColorStop(0.5, color);
  gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.globalCompositeOperation = 'lighter';
  g.fillStyle = gr;
  g.fillRect(x, y, w, h);
  g.restore();
}
