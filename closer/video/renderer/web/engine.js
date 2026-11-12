// closer/video/renderer/web/engine.js
// High-Fidelity Canvas 2D Motion Graphics, 2.5D Camera & Device Frame Engine
// Optimized for 1080x1920 9:16 Vertical Video Production.

export const W = 1080, H = 1920;
export const TAU = Math.PI * 2;

// ─────────────────────────────────────────────────────────────────────────────
// 1. MATHEMATICAL & EASING HELPERS
// ─────────────────────────────────────────────────────────────────────────────
export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const seg = (t, a, b) => clamp((t - a) / (b - a));
export const ss = t => { t = clamp(t); return t * t * (3 - 2 * t); };
export const eio = t => { t = clamp(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
export const eo = t => 1 - Math.pow(1 - clamp(t), 3);
export const ei = t => Math.pow(clamp(t), 3);
export const back = (t, s = 1.8) => { t = clamp(t) - 1; return 1 + t * t * ((s + 1) * t + s); };
export const spring = (t, k = 7, z = 0.35) => {
  t = Math.max(0, t);
  return 1 - Math.exp(-z * k * t) * Math.cos(k * Math.sqrt(1 - z * z) * t * 1.6);
};
export const hash = n => {
  n = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return n - Math.floor(n);
};

export function mulberry(seed) {
  return function () {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. COLOR PALETTE & TYPOGRAPHY
// ─────────────────────────────────────────────────────────────────────────────
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
  accent: '#00E5FF',  // Electric Cyan (CLOSER AI Core)
  lime: '#B7F34A',    // Luminous Lime (Unit Economics & Proof)
  red: '#EF4444',     // Crimson Alert (The Lead Drop Crisis)
  emerald: '#10B981', // Emerald Green (WhatsApp Instant Sync)
  purple: '#C084FC',  // Violet (Hindi / Clean Energy Desk)
  gold: '#FACC15',    // Gold (Hormozi Karaoke & Viral CTA)
  amber: '#F59E0B',
  white: '#FFFFFF'
};

export function rgba(hex, a) {
  if (!hex) return `rgba(255,255,255,${a})`;
  if (hex.startsWith('rgba')) return hex;
  const clean = hex.replace('#', '');
  const n = parseInt(clean, 16);
  if (clean.length === 6) {
    return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`;
  }
  return hex;
}

export const FONT = {
  ui: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  disp: 'InterTight, "Inter", sans-serif',
  mono: 'JBMono, "JetBrains Mono", monospace'
};

export const font = (px, wt = 500, fam = 'ui') => `${wt} ${px}px ${FONT[fam] || fam}`;

// ─────────────────────────────────────────────────────────────────────────────
// 3. CANVAS BUFFER POOL
// ─────────────────────────────────────────────────────────────────────────────
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

// ─────────────────────────────────────────────────────────────────────────────
// 4. GEOMETRY PRIMITIVES & PILLS
// ─────────────────────────────────────────────────────────────────────────────
export function rr(g, x, y, w, h, r) {
  g.beginPath();
  g.roundRect(x, y, w, h, Math.max(0, Math.min(r, w / 2, h / 2)));
}

export function glow(g, x, y, r, color, a) {
  if (a <= 0 || r <= 0) return;
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, rgba(color, a));
  gr.addColorStop(0.4, rgba(color, a * 0.35));
  gr.addColorStop(1, rgba(color, 0));
  g.fillStyle = gr;
  g.fillRect(x - r, y - r, r * 2, r * 2);
}

export function pill(g, x, y, text, opts = {}) {
  const { color = PAL.accent, bg = 'rgba(0,229,255,0.15)', px = 14, py = 6, fontSize = 13 } = opts;
  g.save();
  g.font = `700 ${fontSize}px ${FONT.mono}`;
  const tw = g.measureText(text).width;
  const pw = tw + px * 2;
  const ph = fontSize + py * 2;
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
  return pw;
}

export function panel3D(g, x, y, w, h, opts = {}) {
  const { r = 20, fill = PAL.surf, stroke = PAL.line, shadow = 1.0 } = opts;
  g.save();
  if (shadow > 0) {
    g.shadowColor = 'rgba(0, 0, 0, 0.75)';
    g.shadowBlur = 40 * shadow;
    g.shadowOffsetY = 18 * shadow;
  }
  g.fillStyle = fill;
  rr(g, x, y, w, h, r);
  g.fill();
  g.shadowColor = 'transparent';

  // Specular top edge sheen
  const grSheen = g.createLinearGradient(x, y, x, y + 60);
  grSheen.addColorStop(0, 'rgba(255, 255, 255, 0.12)');
  grSheen.addColorStop(1, 'rgba(255, 255, 255, 0.0)');
  g.fillStyle = grSheen;
  rr(g, x, y, w, 60, r);
  g.fill();

  if (stroke) {
    g.strokeStyle = stroke;
    g.lineWidth = 1.5;
    rr(g, x + 0.5, y + 0.5, w - 1, h - 1, r);
    g.stroke();
  }
  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. VOLUMETRIC STAGE BACKGROUND & PARTICLES
// ─────────────────────────────────────────────────────────────────────────────
export function bg(g, o = {}) {
  const { lift = 1, cyanGlow = 1, t = 0, cx = W * 0.5, cy = H * 0.38, tint = null } = o;
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.fillStyle = PAL.bg0;
  g.fillRect(0, 0, W, H);

  // Dynamic sweeping stage spotlight with organic drift
  const spotX = cx + Math.sin(t * 0.7) * 70;
  const spotY = cy + Math.cos(t * 0.5) * 45;
  const gr = g.createRadialGradient(spotX, spotY, 0, spotX, spotY, W * 0.85);
  gr.addColorStop(0, rgba(PAL.bg1, 0.98 * lift));
  gr.addColorStop(1, rgba(PAL.bg0, 0));
  g.fillStyle = gr;
  g.fillRect(0, 0, W, H);

  if (cyanGlow > 0) {
    glow(g, spotX, spotY, 920, tint || PAL.accent, 0.08 * cyanGlow);
  }
  g.restore();
}

export function cinematicBokeh(g, t, count = 36) {
  g.save();
  const rand = mulberry(1337);
  for (let i = 0; i < count; i++) {
    const baseX = rand() * W;
    const baseY = rand() * H;
    const speed = 0.2 + rand() * 0.6;
    const size = 3 + rand() * 14;
    const phase = rand() * TAU;
    const x = baseX + Math.sin(t * speed + phase) * 40;
    const y = ((baseY - t * speed * 30) % H + H) % H;
    const alpha = 0.04 + Math.sin(t * 2 + phase) * 0.03;

    g.fillStyle = rgba(PAL.accent, Math.max(0, alpha));
    g.beginPath();
    g.arc(x, y, size, 0, TAU);
    g.fill();
  }
  g.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. DYNAMIC 3D DEVICE FRAME (iPhone 16 Pro + Dynamic Island Telemetry)
// ─────────────────────────────────────────────────────────────────────────────
export function drawPhoneFrame(g, cx, cy, w, h, t, opts = {}) {
  const { callActive = true, waveLevel = 0.8 } = opts;
  const r = 56;
  g.save();

  // Outer volumetric ambient shadow
  g.shadowColor = 'rgba(0, 0, 0, 0.92)';
  g.shadowBlur = 75;
  g.shadowOffsetY = 34;
  g.fillStyle = '#080C14';
  rr(g, cx - w / 2, cy - h / 2, w, h, r);
  g.fill();
  g.shadowColor = 'transparent';

  // Titanium Bezel gradient
  const grBezel = g.createLinearGradient(0, cy - h / 2, 0, cy + h / 2);
  grBezel.addColorStop(0, '#263147');
  grBezel.addColorStop(0.5, '#121824');
  grBezel.addColorStop(1, '#1A2234');
  g.fillStyle = grBezel;
  rr(g, cx - w / 2, cy - h / 2, w, h, r);
  g.fill();

  // Specular edge highlights
  g.strokeStyle = 'rgba(255, 255, 255, 0.28)';
  g.lineWidth = 1.5;
  rr(g, cx - w / 2 + 0.5, cy - h / 2 + 0.5, w - 1, h - 1, r);
  g.stroke();

  // OLED Screen Inner Area
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
  g.strokeStyle = 'rgba(255, 255, 255, 0.12)';
  g.lineWidth = 1;
  rr(g, diX + 0.5, diY + 0.5, diW - 1, diH - 1, diH / 2);
  g.stroke();

  // Dynamic Island Telemetry: Mic Pulse / Waveform
  if (callActive) {
    const micPulse = (Math.sin(t * 8) + 1) * 0.5;
    g.fillStyle = PAL.accent;
    g.shadowColor = rgba(PAL.accent, 0.8);
    g.shadowBlur = 8;
    g.beginPath();
    g.arc(diX + diW - 22, diY + diH / 2, 3.5 + micPulse * 1.5, 0, TAU);
    g.fill();
    g.shadowColor = 'transparent';

    // Mini waveform bars inside Dynamic Island
    for (let b = 0; b < 4; b++) {
      const bh = 6 + Math.abs(Math.sin(t * 12 + b * 1.2)) * 14 * waveLevel;
      const bx = diX + diW - 55 + b * 6;
      g.fillStyle = PAL.accent;
      rr(g, bx, diY + diH / 2 - bh / 2, 3, bh, 1.5);
      g.fill();
    }
  }

  // Status Bar Telemetry
  g.font = font(16, 600, 'mono');
  g.fillStyle = '#FFFFFF';
  g.textAlign = 'left';
  g.textBaseline = 'middle';
  g.fillText("11:42", sx + 32, diY + diH / 2);

  g.textAlign = 'right';
  g.fillText("5G ▮▮▮ 98%", sx + sw - 32, diY + diH / 2);

  g.restore();
  return [sx, sy, sw, sh];
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. AUDIO WAVEFORMS, CUTS & SCANLINES
// ─────────────────────────────────────────────────────────────────────────────
export function drawWaveform(g, cx, cy, w, h, t, level = 1.0) {
  g.save();
  const bars = 28;
  const barW = (w / bars) * 0.6;
  const gap = w / bars;
  const startX = cx - w / 2;

  for (let i = 0; i < bars; i++) {
    const wave = Math.abs(Math.sin(t * 10 + i * 0.4)) * 0.7 + Math.abs(Math.cos(t * 14 + i * 0.8)) * 0.3;
    const barH = Math.max(6, wave * h * level);
    const x = startX + i * gap;
    const y = cy - barH / 2;

    const gr = g.createLinearGradient(0, y, 0, y + barH);
    gr.addColorStop(0, PAL.accent);
    gr.addColorStop(1, PAL.lime);
    g.fillStyle = gr;
    rr(g, x, y, barW, barH, barW / 2);
    g.fill();
  }
  g.restore();
}

export function drawCutTransition(g, t, cutTimes = [], W = 1080, H = 1920) {
  for (const ct of cutTimes) {
    const dt = t - ct;
    if (dt >= 0 && dt < 0.18) {
      const alpha = (1.0 - dt / 0.18);
      g.save();
      g.fillStyle = `rgba(0, 229, 255, ${alpha * 0.35})`;
      g.fillRect(0, 0, W, H);
      g.fillStyle = `rgba(239, 68, 68, ${alpha * 0.25})`;
      g.fillRect(0, 0, W, H);
      g.fillStyle = `rgba(255, 255, 255, ${alpha * 0.45})`;
      g.fillRect(0, 0, W, H);
      g.restore();
      break;
    }
  }
}

export function drawScanlines(g, W = 1080, H = 1920) {
  g.save();
  g.fillStyle = 'rgba(0, 0, 0, 0.08)';
  for (let y = 0; y < H; y += 4) {
    g.fillRect(0, y, W, 1.5);
  }
  g.restore();
}

export function vignette(g, amount = 0.45, W = 1080, H = 1920) {
  g.save();
  const gr = g.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.75);
  gr.addColorStop(0, 'rgba(0, 0, 0, 0)');
  gr.addColorStop(1, `rgba(0, 0, 0, ${amount})`);
  g.fillStyle = gr;
  g.fillRect(0, 0, W, H);
  g.restore();
}
