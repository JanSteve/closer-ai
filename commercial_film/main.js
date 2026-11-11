import { renderFilm, setLines, subs, DUR } from './film.js';
import { renderReel, reelSubs, DUR as REEL_DUR } from './reel.js';
import * as frames from './frames.js';

const cv = document.getElementById('c');
const g = cv.getContext('2d');

await Promise.all([300, 400, 500, 600, 700].flatMap(w => [
  `${w} 40px Inter`,
  `${w} 40px InterTight`,
  `${w} 40px JBMono`
]).map(f => document.fonts.load(f).catch(() => {})));

const get = async (u, d) => {
  try {
    const r = await fetch(u);
    return r.ok ? await r.json() : d;
  } catch {
    return d;
  }
};

const lines = await get('lines.json', []);
const durs = await get('voices/dur.json', {});
setLines(lines, durs);

const Q = new URLSearchParams(location.search);
const isReel = Q.get('format') === 'reel' || Q.get('scene') === 'reel';

if (isReel) {
  cv.width = 1080;
  cv.height = 1920;
  window.DUR = REEL_DUR;
  window.SUBS = reelSubs();
  window.render = (t) => renderReel(g, t);
} else {
  cv.width = 1920;
  cv.height = 1080;
  window.DUR = DUR;
  window.SUBS = subs();
  const scene = Q.get('scene');
  window.render = scene ? (t => frames[scene](g, t)) : (t => renderFilm(g, t, { nosub: Q.has('nosub') }));
}

window.READY = true;
