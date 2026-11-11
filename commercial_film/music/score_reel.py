#!/usr/bin/env python3
"""68-second high-energy kinetic documentary score for CLOSER AI Multi-Sector Instagram Reel.
Uses VCSL + VSCO2CE samples via core.audio.sampler.
"""
import os, sys
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
FILM_DIR = os.path.dirname(HERE)
LEMO_ROOT = '/Users/janstevedaniel/lemo-opuscar'
sys.path.insert(0, LEMO_ROOT)
from core.audio import sampler as S
from core.audio.sfx import SR, t_, env_exp, bp, lp, hp, noise, norm

DUR = 68.0
N = int(DUR * SR)
BEAT = 0.5  # 120 BPM
S16 = 0.125 # sixteenth note

STEMS = ['marimba', 'vibes', 'glock', 'pad', 'perc', 'riser']
BUF = {s: np.zeros((N, 2), np.float32) for s in STEMS}

S.seed(20261111)

def put(stem, x, t, gain=1.0, pan=0.0):
    s = int(round(t * SR))
    if s < 0:
        x = x[-s:]
        s = 0
    e = min(N, s + len(x))
    if e <= s:
        return
    l = np.cos((pan + 1) * np.pi / 4) * 1.414
    r = np.sin((pan + 1) * np.pi / 4) * 1.414
    if x.ndim == 1:
        BUF[stem][s:e, 0] += x[:e - s] * gain * l
        BUF[stem][s:e, 1] += x[:e - s] * gain * r
    else:
        BUF[stem][s:e, 0] += x[:e - s, 0] * gain * l
        BUF[stem][s:e, 1] += x[:e - s, 1] * gain * r

def play(stem, inst, t, midi_pitch, dur, vel=0.6, pan=0.0, gain=1.0, **kw):
    try:
        x = S.note(inst, midi_pitch, dur, vel, **kw)
        if x.ndim > 1:
            x = x.mean(1)
        put(stem, x, t, gain=gain, pan=pan)
    except Exception as ex:
        pass

def play_hit(stem, inst, t, vel=0.6, pan=0.0, gain=1.0, **kw):
    try:
        x = S.hit(inst, vel=vel, **kw)
        if x.ndim > 1:
            x = x.mean(1)
        put(stem, x, t, gain=gain, pan=pan)
    except Exception as ex:
        pass

def make_pad(d, f_hz):
    tt = t_(d)
    x = np.sin(2 * np.pi * f_hz * tt) + 0.5 * np.sin(2 * np.pi * (f_hz * 1.004) * tt)
    env = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 0.8
    return lp(x * env, 800)

# 1. Tension Section (0.0s – 19.5s) — The Agency Nightmare & 5-Minute Collapse
for t in np.arange(0.4, 19.5, 0.5):
    play_hit('perc', 'woodblock', t, vel=0.35, pan=-0.2)
    if int(t * 2) % 4 == 0:
        play_hit('perc', 'toms', t, vel=0.45, pan=0.1)

put('pad', make_pad(19.0, 65.4), 0.4, gain=0.35, pan=0.0)

# 2. The Breakthrough Drop at 19.8s (CLOSER AI Sub-45s Callback)
play_hit('perc', 'sus_cymbal', 19.8, vel=0.75)
play_hit('perc', 'gran_cassa', 19.8, vel=0.95)
play('vibes', 'vibraphone_hard', 19.8, 60, 3.0, vel=0.85)
play('vibes', 'vibraphone_hard', 19.8, 63, 3.0, vel=0.75)
play('vibes', 'vibraphone_hard', 19.8, 67, 3.0, vel=0.75)

# 3. Kinetic Grooves across Multi-Sector Demos, WhatsApp, Economics & CTA (20.0s – 66.5s)
c_notes = [60, 63, 67, 70, 74, 70, 67, 63]
t_step = 20.0
idx = 0
while t_step < 66.5:
    m_note = c_notes[idx % len(c_notes)]
    vel = 0.52 if idx % 4 == 0 else 0.38
    pan = ((idx % 4) - 1.5) * 0.2
    play('marimba', 'marimba', t_step, m_note, 0.35, vel=vel, pan=pan)
    if idx % 2 == 0:
        play_hit('perc', 'shaker', t_step, vel=0.25, pan=0.3)
    if idx % 8 == 0:
        play('glock', 'glockenspiel', t_step, m_note + 12, 0.8, vel=0.45, pan=-0.2)
    t_step += S16
    idx += 1

# Outro Final Hit at 66.8s
play_hit('perc', 'gran_cassa', 66.8, vel=0.8)
play('vibes', 'vibraphone_hard', 66.8, 60, 1.5, vel=0.7)

out_score = np.zeros((N, 2), np.float32)
for s in STEMS:
    out_score += BUF[s]

pk = np.max(np.abs(out_score))
if pk > 0:
    out_score = out_score / pk * 0.88

dst = os.path.join(HERE, 'score_reel.wav')
sf.write(dst, out_score, SR, subtype='PCM_16')
print(f"Reel score rendered: {DUR:.2f}s, peak {np.max(np.abs(out_score)):.3f} -> {dst}")
