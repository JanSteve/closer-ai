#!/usr/bin/env python3
"""Score for CLOSER AI Commercial Film — "The 11:42 PM Lead".
Minimalist polyrhythmic keynote score in C minor / Eb major at 120 BPM.
Uses Versilian Community Sample Library via core.audio.sampler + synthetic numpy pads.
"""
import os, sys, json
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
FILM_DIR = os.path.dirname(HERE)
LEMO_ROOT = '/Users/janstevedaniel/lemo-opuscar'
sys.path.insert(0, LEMO_ROOT)
from core.audio import sampler as S
from core.audio.sfx import SR, t_, env_exp, bp, lp, hp, noise, norm

DUR = 60.0
N = int(DUR * SR)
BEAT = 0.5  # 120 BPM
S16 = 0.125 # sixteenth note

STEMS = ['marimba', 'vibes', 'glock', 'bass', 'pad', 'perc', 'riser']
BUF = {s: np.zeros((N, 2), np.float32) for s in STEMS}

S.seed(20261110)
rng = np.random.default_rng(2026)

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
        print(f"Warning: could not play {inst} ({ex})")

def play_hit(stem, inst, t, vel=0.6, pan=0.0, gain=1.0, **kw):
    try:
        x = S.hit(inst, vel=vel, **kw)
        if x.ndim > 1:
            x = x.mean(1)
        put(stem, x, t, gain=gain, pan=pan)
    except Exception as ex:
        if inst == 'claves':
            try:
                x = S.hit('woodblock', vel=vel, **kw)
                if x.ndim > 1:
                    x = x.mean(1)
                put(stem, x, t, gain=gain, pan=pan)
                return
            except Exception:
                pass
        elif inst == 'bass_drum':
            try:
                x = S.hit('gran_cassa', vel=vel, **kw)
                if x.ndim > 1:
                    x = x.mean(1)
                put(stem, x, t, gain=gain, pan=pan)
                return
            except Exception:
                pass
        print(f"Warning: could not hit {inst} ({ex})")

# 1. Pad generator (detuned supersaw/triangle warmly lowpassed)
def make_pad(d, f_hz, tau=0.5):
    tt = t_(d)
    x = np.sin(2 * np.pi * f_hz * tt) + 0.5 * np.sin(2 * np.pi * (f_hz * 1.004) * tt) + 0.5 * np.sin(2 * np.pi * (f_hz * 0.996) * tt)
    env = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 0.8
    return lp(x * env, 800)

# 2. Riser generator
def make_riser(d, f0=80, f1=1800):
    tt = t_(d)
    freq = f0 * (f1 / f0) ** (tt / d)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    sweep = np.sin(phase) * (tt / d) ** 2
    n = bp(noise(d), 200, 4000) * (tt / d) ** 1.8
    return norm(sweep * 0.4 + n * 0.6)

# ————— BUILD THE SCORE —————

# SECTION 1: 0.0s – 9.5s (The Nocturnal Cold Crisis)
# Low sub tension (C1/Eb1)
for t in np.arange(0.5, 9.0, 1.0):
    # Clock tick heartbeat
    play_hit('perc', 'claves', t, vel=0.25, pan=-0.2)
    # Low subtle tom pulse
    if int(t) % 2 == 0:
        play_hit('perc', 'toms', t, vel=0.35, pan=0.1)

# Tension chord pad
p1 = make_pad(8.5, 65.4) # C2 (65.4 Hz)
put('pad', p1, 0.5, gain=0.3, pan=-0.1)
p2 = make_pad(8.5, 77.8) # Eb2 (77.8 Hz)
put('pad', p2, 1.0, gain=0.2, pan=0.2)

# Riser into the drop
riser = make_riser(2.5, f0=60, f1=1200)
put('riser', riser, 7.0, gain=0.45, pan=0.0)

# SECTION 2: 9.8s – 22.0s (Autonomous Awakening & Keynote Shift)
# Climax drop at 9.8s
play_hit('perc', 'sus_cymbal', 9.8, vel=0.7)
play_hit('perc', 'bass_drum', 9.8, vel=0.85)
play('vibes', 'vibraphone_hard', 9.8, 60, 3.5, vel=0.8, pan=0.0) # C4
play('vibes', 'vibraphone_hard', 9.8, 63, 3.5, vel=0.7, pan=0.3) # Eb4
play('vibes', 'vibraphone_hard', 9.8, 67, 3.5, vel=0.7, pan=-0.3) # G4
play('vibes', 'vibraphone_hard', 9.8, 70, 3.5, vel=0.6, pan=0.2) # Bb4

# Kinetic marimba groove in sixteenths from 10.5s to 21.5s
# Pattern: C4, Eb4, G4, Bb4, D5, Bb4, G4, Eb4
c_min_notes = [60, 63, 67, 70, 74, 70, 67, 63]
t_step = 10.5
idx = 0
while t_step < 21.5:
    m_note = c_min_notes[idx % len(c_min_notes)]
    vel = 0.55 if idx % 4 == 0 else 0.42
    pan = ((idx % 4) - 1.5) * 0.2
    play('marimba', 'marimba', t_step, m_note, 0.35, vel=vel, pan=pan)
    if idx % 2 == 0:
        play_hit('perc', 'shaker', t_step, vel=0.22, pan=0.3)
    t_step += S16
    idx += 1

# Pad supporting Section 2
pad_sec2 = make_pad(11.0, 130.8) # C3
put('pad', pad_sec2, 10.5, gain=0.35, pan=0.0)

# SECTION 3: 22.0s – 44.5s (Tri-Lingual Showcase: Maya, Pallavi, Swati)
# Voice 1: Maya (22.0s – 30.0s) — Sophisticated Eb Major
eb_notes = [63, 67, 70, 74, 75, 74, 70, 67]
t_step = 22.0
idx = 0
while t_step < 29.5:
    m_note = eb_notes[idx % len(eb_notes)]
    vel = 0.48 if idx % 4 == 0 else 0.36
    play('marimba', 'marimba', t_step, m_note, 0.4, vel=vel, pan=-0.15)
    if idx % 4 == 0:
        play('vibes', 'vibraphone', t_step, m_note + 12, 1.2, vel=0.4, pan=0.25)
    t_step += S16
    idx += 1

# Transition at 29.8s
play_hit('perc', 'triangle', 29.8, vel=0.5)
play_hit('perc', 'toms', 29.8, vel=0.5)

# Voice 2: Pallavi (30.0s – 36.5s) — Coastal / Tamil dynamic cadence (Ab - Bb)
ab_notes = [68, 70, 72, 75, 72, 70, 68, 65]
t_step = 30.0
idx = 0
while t_step < 36.3:
    m_note = ab_notes[idx % len(ab_notes)]
    vel = 0.52 if idx % 4 == 0 else 0.38
    play('marimba', 'marimba', t_step, m_note, 0.35, vel=vel, pan=0.2)
    if idx % 8 == 0:
        play('glock', 'glockenspiel', t_step, m_note + 12, 0.8, vel=0.45, pan=-0.2)
    t_step += S16
    idx += 1

# Transition at 36.5s
play_hit('perc', 'claves', 36.5, vel=0.6)
play_hit('perc', 'bass_drum', 36.6, vel=0.6)

# Voice 3: Swati (36.8s – 44.5s) — Warm G-minor to C-minor resolution
gm_notes = [67, 70, 72, 74, 77, 74, 72, 70]
t_step = 36.8
idx = 0
while t_step < 44.2:
    m_note = gm_notes[idx % len(gm_notes)]
    vel = 0.52 if idx % 4 == 0 else 0.40
    play('marimba', 'marimba', t_step, m_note, 0.35, vel=vel, pan=-0.1)
    if idx % 4 == 0:
        play('vibes', 'vibraphone', t_step, m_note + 12, 1.2, vel=0.42, pan=0.15)
    t_step += S16
    idx += 1

# Pre-drop riser into The Big Number
riser2 = make_riser(1.8, f0=100, f1=2200)
put('riser', riser2, 42.8, gain=0.45, pan=0.0)

# SECTION 4: 44.8s – 52.0s (The Giant Number: ₹1.55 / 99.3%)
# Huge downbeat impact at 44.8s
play_hit('perc', 'sus_cymbal', 44.8, vel=0.8)
play_hit('perc', 'bass_drum', 44.8, vel=0.9)
play('vibes', 'vibraphone_hard', 44.8, 60, 4.0, vel=0.85, pan=0.0) # C4
play('vibes', 'vibraphone_hard', 44.8, 72, 4.0, vel=0.8, pan=0.2) # C5
play('marimba', 'marimba', 44.8, 36, 4.0, vel=0.9, pan=-0.1) # C2
play('marimba', 'marimba', 44.8, 48, 4.0, vel=0.85, pan=0.1) # C3

# Digit lock ticks (45.8, 46.4, 47.0, 47.6, 48.2)
lock_pitches = [72, 74, 76, 79, 84] # C5, D5, E5, G5, C6
for i, lp_note in enumerate(lock_pitches):
    t_lock = 45.6 + i * 0.5
    play('glock', 'glockenspiel', t_lock, lp_note, 1.2, vel=0.65, pan=0.1 * (i - 2))
    play('marimba', 'marimba', t_lock, lp_note - 12, 0.5, vel=0.7, pan=0.0)

# SECTION 5: 52.0s – 60.0s (Hero Climax & Launching Soon)
# Majestic resolving chord at 52.4s (C Major 9)
cmaj9 = [48, 55, 60, 64, 71, 74] # C3, G3, C4, E4, B4, D5
play_hit('perc', 'sus_cymbal', 52.4, vel=0.7)
for j, chord_note in enumerate(cmaj9):
    pan = ((j / len(cmaj9)) - 0.5) * 0.8
    play('vibes', 'vibraphone', 52.4, chord_note, 5.0, vel=0.65, pan=pan)
    play('marimba', 'marimba', 52.4, chord_note - 12, 5.0, vel=0.6, pan=pan)

pad_final = make_pad(6.0, 130.8) # C3
put('pad', pad_final, 52.4, gain=0.4, pan=0.0)

# Soft glockenspiel twinkle on "Launching Soon" at 55.5s
play('glock', 'glockenspiel', 55.5, 84, 2.0, vel=0.45, pan=0.2) # C6
play('glock', 'glockenspiel', 56.0, 88, 2.0, vel=0.45, pan=-0.2) # E6
play('glock', 'glockenspiel', 56.5, 91, 2.5, vel=0.5, pan=0.0) # G6

# REVERB & MIXDOWN
ROOM = {'marimba': (0.35, 0.18), 'vibes': (0.45, 0.22), 'glock': (0.55, 0.25), 'bass': (0.2, 0.1), 'pad': (0.4, 0.15), 'perc': (0.3, 0.14), 'riser': (0.4, 0.15)}
GAIN = {'marimba': 0.9, 'vibes': 0.85, 'glock': 0.75, 'bass': 0.8, 'pad': 0.45, 'perc': 0.85, 'riser': 0.6}

stems = {}
for s in STEMS:
    x = BUF[s]
    if x.any() and ROOM[s]:
        x = S.room(x, size=ROOM[s][0], mix=ROOM[s][1])
    stems[s] = x * GAIN[s]

full_mix = sum(stems.values())
# Fade out last 1.5 seconds smoothly to zero
fade_len = int(1.5 * SR)
full_mix[-fade_len:] *= np.linspace(1, 0, fade_len)[:, None]

peak = np.abs(full_mix).max()
if peak > 0:
    g = (10 ** (-1.0 / 20)) / peak
    full_mix = (full_mix * g).astype(np.float32)

score_out = os.path.join(HERE, 'score.wav')
sf.write(score_out, full_mix, SR, subtype='PCM_24')
print(f"score.wav rendered successfully: {len(full_mix)/SR:.2f}s, peak {np.abs(full_mix).max():.3f} -> {score_out}")
