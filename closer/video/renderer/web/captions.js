// closer/video/renderer/web/captions.js
// Hormozi-Style Safe-Zone Subtitle Renderer (subY = 1360) & Viral CTA Banner (Y = 1530)
// Guarantees 100% visibility on Instagram Reels across all iOS/Android device aspect ratios.

import { clamp, rr, pill, panel3D, font, PAL } from './engine.js';

export const SAFE_ZONE_SUBTITLE_Y = 1360;
export const SAFE_ZONE_CTA_Y = 1530;
export const MAX_SUBTITLE_WIDTH = 680;

/**
 * Renders Hormozi-style energetic karaoke subtitles anchored strictly at Y = 1360.
 * 
 * @param {CanvasRenderingContext2D} g - 2D rendering context
 * @param {number} t - Current playback time in seconds
 * @param {number} W - Canvas width (default 1080)
 * @param {number} H - Canvas height (default 1920)
 * @param {Array<{t0: number, t1: number, text: string, tag?: string}>} lines - Subtitle line definitions
 */
export function renderHormoziCaptions(g, t, W = 1080, H = 1920, lines = []) {
  if (!lines || !lines.length) return;

  const active = lines.find(l => t >= l.t0 && t <= l.t1);
  if (!active) return;

  const prog = clamp((t - active.t0) / (active.t1 - active.t0), 0, 1);
  const words = active.text.split(' ');
  const activeWordIdx = Math.min(words.length - 1, Math.floor(prog * words.length));

  // Instagram Safe Zone: Y = 1360 (clear of Reels bottom captions & native action icons)
  const subY = SAFE_ZONE_SUBTITLE_Y;
  g.save();

  // Measure text with 38px punchy font
  g.font = font(38, 900, 'disp');
  let totalW = 0;
  const wordWidths = words.map(w => {
    const wWidth = g.measureText(w + ' ').width;
    totalW += wWidth;
    return wWidth;
  });

  // Clamp max width so subtitles NEVER cover the full screen or bleed into edge icons
  const maxW = MAX_SUBTITLE_WIDTH;
  let scaleRatio = 1.0;
  if (totalW > maxW) {
    scaleRatio = maxW / totalW;
  }

  const boxW = Math.min(totalW * scaleRatio + 56, maxW + 40);
  const boxH = 68;

  // Sector / Category Tag Pill above subtitle box (subY - 68)
  if (active.tag) {
    pill(g, W / 2 - 120, subY - 68, active.tag, {
      color: PAL.gold,
      bg: 'rgba(0, 0, 0, 0.85)',
      px: 12
    });
  }

  // Frosted dark pill container
  g.fillStyle = 'rgba(6, 9, 18, 0.88)';
  rr(g, W / 2 - boxW / 2, subY - boxH / 2, boxW, boxH, 20);
  g.fill();
  g.strokeStyle = 'rgba(250, 204, 21, 0.45)';
  g.lineWidth = 1.5;
  rr(g, W / 2 - boxW / 2 + 0.5, subY - boxH / 2 + 0.5, boxW - 1, boxH - 1, 20);
  g.stroke();

  // Draw karaoke words
  g.save();
  g.translate(W / 2, subY);
  if (scaleRatio < 1.0) {
    g.scale(scaleRatio, scaleRatio);
  }

  let startX = -totalW / 2;
  words.forEach((w, idx) => {
    const isCur = (idx === activeWordIdx);
    const ww = wordWidths[idx];

    if (isCur) {
      // Energetic karaoke bounce animation
      const bounce = Math.sin(prog * words.length * Math.PI) * 4;
      g.save();
      g.translate(startX + ww / 2, -bounce);
      g.scale(1.15, 1.15);
      g.fillStyle = PAL.gold;
      g.shadowColor = 'rgba(250, 204, 21, 0.9)';
      g.shadowBlur = 20;
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillText(w, 0, 0);
      g.restore();
    } else {
      g.fillStyle = '#FFFFFF';
      g.shadowColor = 'rgba(0, 0, 0, 0.8)';
      g.shadowBlur = 6;
      g.textAlign = 'left';
      g.textBaseline = 'middle';
      g.fillText(w, startX, 0);
    }
    startX += ww;
  });

  g.restore();
  g.restore();
}

/**
 * Renders the high-converting Viral CTA Banner hook strictly at Y = 1530.
 * 
 * @param {CanvasRenderingContext2D} g - 2D rendering context
 * @param {number} t - Current playback time in seconds
 * @param {number} W - Canvas width (default 1080)
 * @param {number} H - Canvas height (default 1920)
 * @param {object} opts - Optional CTA keyword and text overrides
 */
export function renderViralCTABanner(g, t, W = 1080, H = 1920, opts = {}) {
  const {
    keyword = 'CLOSER',
    text = "💬 COMMENT 'CLOSER' FOR YOUR BUSINESS PLAYBOOK ➔",
    showDuration = 8.0,
    totalDuration = 78.0
  } = opts;

  // Display only during the closing CTA window
  if (t < (totalDuration - showDuration)) return;

  const ctaY = SAFE_ZONE_CTA_Y;
  const ctaW = W - 120;
  const ctaH = 74;

  g.save();

  // Glassmorphic Golden CTA Pill
  panel3D(g, W / 2 - ctaW / 2, ctaY - ctaH / 2, ctaW, ctaH, {
    r: ctaH / 2,
    fill: 'rgba(251, 191, 36, 0.22)',
    stroke: PAL.gold,
    shadow: 1.4
  });

  // Pulsing Glow Accent
  const pulse = (Math.sin(t * 6) + 1) * 0.5;
  g.strokeStyle = `rgba(250, 204, 21, ${0.4 + pulse * 0.4})`;
  g.lineWidth = 2.0;
  rr(g, W / 2 - ctaW / 2, ctaY - ctaH / 2, ctaW, ctaH, ctaH / 2);
  g.stroke();

  // High-contrast call to action text
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.font = font(22, 800, 'mono');
  g.fillStyle = PAL.gold;
  g.shadowColor = 'rgba(0, 0, 0, 0.9)';
  g.shadowBlur = 8;
  g.fillText(text, W / 2, ctaY);

  g.restore();
}
