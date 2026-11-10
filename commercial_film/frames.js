// frames.js — Style frames and poster for CLOSER AI film
import * as E from './engine.js';
import { renderFilm } from './film.js';

export function poster(g) {
  // Render Shot 9 at t=54.5s
  renderFilm(g, 54.5, { nosub: true });
}
