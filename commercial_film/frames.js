// frames.js — Style frames and poster for CLOSER AI film & reel
import * as E from './engine.js';
import { renderFilm } from './film.js';
import { renderReel } from './reel.js';

export function poster(g) {
  renderFilm(g, 54.5, { nosub: true });
}

export function poster_reel(g) {
  renderReel(g, 42.0);
}
