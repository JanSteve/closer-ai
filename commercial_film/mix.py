#!/usr/bin/env python3
"""mix.py — Foley + Female Voice + Music Ducking for CLOSER AI Commercial Film → mix.wav
Follows DIRECTOR.md and STYLE.md standards for the Dark Tech Keynote style.
Mastered to -14 LUFS target.
"""
import os, sys, json
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from scipy.ndimage import uniform_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
LEMO_ROOT = '/Users/janstevedaniel/lemo-opuscar'
sys.path.insert(0, LEMO_ROOT)
from core.audio.sfx import SR, t_, env_exp, bp, lp, hp, noise, norm, add, compress, limit

DUR = 60.0
N = int(DUR * SR)

VOICE_SCHEDULE = {
    "l1": 0.5,
    "l2": 5.4,
    "l3": 9.8,
    "l4": 14.0,
    "v_maya": 20.8,
    "v_pallavi": 28.8,
    "v_swati": 35.4,
    "l5": 43.5,
    "l6": 50.5
}

fol = np.zeros((N, 2), np.float32)
vox = np.zeros((N, 2), np.float32)
mus = np.zeros((N, 2), np.float32)

rng = np.random.default_rng(2026)

# ————— Bespoke Synthesizers for Foley —————
def sine(f, d, tau, ph=0):
    return np.sin(2 * np.pi * f * t_(d) + ph) * env_exp(d, tau)

def alert_ping(v=1.0):
    """Crisp high-tech alert for the 11:42 PM lead."""
    d = 0.4
    x = sine(1200, d, 0.05) + 0.6 * sine(1800, d, 0.03) + 0.3 * bp(noise(d), 2000, 6000) * env_exp(d, 0.01)
    return norm(x) * v

def sub_drop(v=1.0):
    """Heavy cinematic keynote sub drop (9.8s)."""
    d = 2.2
    tt = t_(d)
    freq = 68.0 * np.exp(-tt / 0.45) + 38.0
    phase = 2 * np.pi * np.cumsum(freq) / SR
    sub = np.sin(phase) * env_exp(d, 0.7)
    punch = lp(noise(d), 400) * env_exp(d, 0.02) * 0.8
    return norm(sub + punch) * v

def light_sweep(d=1.5, v=1.0):
    """Whoosh shimmer for electric cyan light sweep."""
    n = noise(d)
    tt = t_(d)
    f = 400.0 * (8000.0 / 400.0) ** (tt / d)
    sw = bp(n, 1200, 7000) * np.sin(np.pi * tt / d) ** 1.8
    ting = sine(2400, d, 0.2) * 0.3 + sine(3600, d, 0.15) * 0.2
    return norm(sw + ting) * v

def digit_tick(v=1.0):
    """Precision click for scrambled digit lock."""
    d = 0.03
    return norm(bp(noise(d), 3000, 8000) * env_exp(d, 0.003) + sine(2800, d, 0.004) * 0.5) * v

def glass_chime(f, v=1.0, d=0.6):
    """Elegant glass chime for voice card appearance."""
    x = sine(f, d, d * 0.35) + 0.4 * sine(f * 2, d, d * 0.2) + 0.2 * bp(noise(d), 4000, 9000) * env_exp(d, 0.01)
    return norm(x) * v

# 1. Foley Placement
print("Generating Foley and UI audio cues...")
# 0.5s: Lead alert
add(fol, alert_ping(0.7), 0.5, 0.4, pan=0.0)
add(fol, alert_ping(0.5), 0.7, 0.3, pan=0.1)

# 9.6s: Autonomous turn / Keynote shockwave & sweep
add(fol, light_sweep(1.8, 0.85), 9.2, 0.6, pan=-0.2)
add(fol, sub_drop(0.95), 9.6, 0.85, pan=0.0)

# 14.0s: SIP activation clicks
for i in range(4):
    add(fol, digit_tick(0.4), 13.8 + i * 0.12, 0.25, pan=((i - 1.5) * 0.3))

# 20.8s: Maya card
add(fol, glass_chime(1320, 0.6), 20.8, 0.35, pan=-0.2)

# 28.8s: Pallavi card
add(fol, glass_chime(1480, 0.6), 28.8, 0.35, pan=0.2)

# 35.4s: Swati card
add(fol, glass_chime(1650, 0.6), 35.4, 0.35, pan=0.0)

# 43.0s: Big number impact
add(fol, sub_drop(1.0), 43.0, 0.9, pan=0.0)
add(fol, light_sweep(1.2, 0.7), 42.8, 0.5, pan=0.0)

# Digit ticks during 43.8s to 46.5s
for i in range(8):
    add(fol, digit_tick(0.5), 43.8 + i * 0.3, 0.3, pan=0.1 * (i % 3 - 1))

# 50.5s: Hero logo reveal
add(fol, light_sweep(2.0, 0.8), 50.0, 0.6, pan=0.0)
add(fol, glass_chime(1760, 0.7, 1.2), 50.5, 0.4, pan=0.0)

# 2. Voice Assembly & Ducking intervals
print("Assembling Voice Lines...")
vo_intervals = []
for lid, t_start in VOICE_SCHEDULE.items():
    wav_path = os.path.join(HERE, 'voices', f"{lid}.wav")
    if not os.path.exists(wav_path):
        print(f"Warning: {wav_path} not found!")
        continue
    y, sr = sf.read(wav_path)
    if y.ndim > 1:
        y = y.mean(1)
    if sr != SR:
        y = resample_poly(y, SR, sr)
    # Broadcast voice compression
    y = compress(y / (np.max(np.abs(y)) + 1e-9) * 0.95, 0.3, 3.0)
    add(vox, y, t_start, 0.80, pan=0.0)
    vo_intervals.append((t_start, t_start + len(y) / SR))

# 3. Score Loading & Voice-Ducking
score_path = os.path.join(HERE, 'music', 'score.wav')
if os.path.exists(score_path):
    print("Loading musical score...")
    m, msr = sf.read(score_path, always_2d=True)
    if msr != SR:
        m = resample_poly(m, SR, msr, axis=0)
    mus[:min(N, len(m))] = m[:N]
else:
    print("Warning: score.wav not found, running dry mix.")

# Ducking curve: smoothly attenuate music during speech
duck = np.ones(N, dtype=np.float32)
duck_fol = np.ones(N, dtype=np.float32)
for a, b in vo_intervals:
    s = int(max(0, (a - 0.12) * SR))
    e = int(min(N, (b + 0.18) * SR))
    duck[s:e] = 10 ** (-8.5 / 20)      # -8.5 dB music duck
    duck_fol[s:e] = 10 ** (-3.0 / 20)  # -3.0 dB foley duck

# Smooth ducking edges
duck = uniform_filter1d(duck, int(0.18 * SR))
duck_fol = uniform_filter1d(duck_fol, int(0.12 * SR))

MUSIC_GAIN = 0.72
final_mix = (mus * MUSIC_GAIN * duck[:, None]) + (fol * duck_fol[:, None]) + vox

# Ensure clean tail fade
fade_s = int(1.2 * SR)
final_mix[-fade_s:] *= np.linspace(1, 0, fade_s)[:, None]

# Soft limiting and normalization
for c in range(2):
    final_mix[:, c] = limit(final_mix[:, c], 0.92)

out_mix = os.path.join(HERE, 'mix.wav')
sf.write(out_mix, final_mix.astype(np.float32), SR, subtype='PCM_16')
print(f"mix.wav successfully created! Duration: {len(final_mix)/SR:.2f}s, Peak: {np.max(np.abs(final_mix)):.3f}")
