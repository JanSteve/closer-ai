import { renderFilm, setLines, subs, DUR } from './film.js';
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

window.DUR = DUR;
window.SUBS = subs();

const Q = new URLSearchParams(location.search);
const scene = Q.get('scene');
window.render = scene ? (t => frames[scene](g, t)) : (t => renderFilm(g, t, { nosub: Q.has('nosub') }));
window.READY = true;
