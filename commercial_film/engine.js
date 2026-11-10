// engine.js — CLOSER AI Dark Tech Keynote Visual Engine
import { clamp, lerp, seg, ss, eo, ei, eio, back, spring, mulberry, hash, TAU } from '/core/lib.js';
export { clamp, lerp, seg, ss, eo, ei, eio, back, spring, mulberry, hash, TAU };

export const W = 1920, H = 1080;

export const PAL = {
  bg0: '#04060A',
  bg1: '#0B0F17',
  surf: '#111622',
  surf2: '#161E2E',
  surf3: '#1E283D',
  line: 'rgba(255, 255, 255, 0.07)',
  hi: 'rgba(255, 255, 255, 0.12)',
  text: '#F8FAFC',
  dim: '#94A3B8',
  mute: '#64748B',
  accent: '#00E5FF',  // Electric Cyan
  lime: '#B7F34A',    // Luminous Lime
  red: '#EF4444',     // Crimson
  emerald: '#10B981', // Success Emerald
  purple: '#A855F7'
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
  gr.addColorStop(0.45, rgba(color, a * 0.35));
  gr.addColorStop(1, rgba(color, 0));
  g.fillStyle = gr;
  g.fillRect(x - r, y - r, r * 2, r * 2);
}

export function bg(g, o = {}) {
  const { lift = 1, cyanGlow = 1, cx = W * 0.5, cy = H * 0.38 } = o;
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.fillStyle = PAL.bg0;
  g.fillRect(0, 0, W, H);
  
  // Subtle radial stage light
  let gr = g.createRadialGradient(cx, cy, 0, cx, cy, W * 0.75);
  gr.addColorStop(0, rgba(PAL.bg1, 0.95 * lift));
  gr.addColorStop(1, rgba(PAL.bg0, 0));
  g.fillStyle = gr;
  g.fillRect(0, 0, W, H);

  if (cyanGlow > 0) {
    glow(g, W * 0.5, H * 0.32, 750, PAL.accent, 0.05 * cyanGlow);
  }
  g.restore();
}

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
  
  g.strokeStyle = `rgba(255, 255, 255, ${0.035 * alpha})`;
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

export function panel(g, x, y, w, h, o = {}) {
  const { r = 16, fill = PAL.surf, stroke = PAL.line, shadow = 1, alpha = 1, borderHighlight = true } = o;
  g.save();
  g.globalAlpha *= alpha;
  if (shadow > 0) {
    g.shadowColor = 'rgba(0, 0, 0, 0.6)';
    g.shadowBlur = Math.min(80, 20 + h * 0.15);
    g.shadowOffsetY = Math.min(30, 8 + h * 0.05);
    g.fillStyle = fill;
    rr(g, x, y, w, h, r);
    g.fill();
    g.shadowColor = 'transparent';
  }
  
  // Top-lit gradient fill
  const gr = g.createLinearGradient(0, y, 0, y + h);
  gr.addColorStop(0, '#1A2133');
  gr.addColorStop(0.3, fill);
  gr.addColorStop(1, fill);
  g.fillStyle = gr;
  rr(g, x, y, w, h, r);
  g.fill();

  // 1px Hairline border
  g.lineWidth = 1;
  g.strokeStyle = stroke;
  rr(g, x + 0.5, y + 0.5, w - 1, h - 1, r);
  g.stroke();

  // Top edge reflection highlight
  if (borderHighlight) {
    g.strokeStyle = 'rgba(255, 255, 255, 0.14)';
    g.beginPath();
    g.moveTo(x + r, y + 1.5);
    g.lineTo(x + w - r, y + 1.5);
    g.stroke();
  }
  g.restore();
}

export function pill(g, x, y, text, o = {}) {
  const { color = PAL.accent, bg = PAL.surf3, px = 14, icon = '' } = o;
  g.save();
  g.font = font(px, 600, 'mono');
  const fullText = (icon ? icon + '  ' : '') + text;
  const tw = g.measureText(fullText).width;
  const pw = tw + 24, ph = px * 1.8;
  panel(g, x, y - ph / 2, pw, ph, { r: ph / 2, fill: bg, stroke: rgba(color, 0.3), shadow: 0 });
  g.fillStyle = color;
  g.textBaseline = 'middle';
  g.fillText(fullText, x + 12, y);
  g.restore();
  return pw;
}

// Live interactive audio waveform bars
export function drawWaveform(g, cx, cy, w, h, t, o = {}) {
  const { bars = 36, color = PAL.accent, active = true, alpha = 1 } = o;
  g.save();
  g.globalAlpha *= alpha;
  const step = w / bars;
  const barW = Math.max(3, step * 0.55);

  for (let i = 0; i < bars; i++) {
    const x = cx - w / 2 + i * step + step / 2;
    const normI = (i - bars / 2) / (bars / 2);
    const envelope = Math.cos(normI * Math.PI * 0.45); // curve down at edges
    
    let amp = 0.15;
    if (active) {
      const f1 = Math.sin(t * 12 + i * 0.7);
      const f2 = Math.cos(t * 18 - i * 0.4);
      const f3 = Math.sin(t * 7 + i * 1.2);
      amp = Math.abs(f1 * 0.45 + f2 * 0.35 + f3 * 0.2) * envelope;
      amp = Math.max(0.12, Math.min(1.0, amp));
    }
    const bh = Math.max(6, h * amp);
    
    // Bar glow
    if (active && amp > 0.4) {
      glow(g, x, cy, bh * 0.8, color, 0.12 * amp);
    }
    
    g.fillStyle = active ? (amp > 0.6 ? '#FFFFFF' : color) : PAL.mute;
    rr(g, x - barW / 2, cy - bh / 2, barW, bh, barW / 2);
    g.fill();
  }
  g.restore();
}

// Scrambled / rolling counter digits
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

// Light sweep highlight across cards or hero text
export function lightSweep(g, x, y, w, h, progress, color = 'rgba(255,255,255,0.22)') {
  if (progress < 0 || progress > 1) return;
  g.save();
  g.beginPath();
  g.rect(x, y, w, h);
  g.clip();
  const d = Math.hypot(w, h);
  const sx = x - d * 0.3 + progress * d * 1.6;
  const gr = g.createLinearGradient(sx - 140, y, sx + 140, y + h * 0.4);
  gr.addColorStop(0, 'rgba(255,255,255,0)');
  gr.addColorStop(0.5, color);
  gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.globalCompositeOperation = 'lighter';
  g.fillStyle = gr;
  g.fillRect(x, y, w, h);
  g.restore();
}
