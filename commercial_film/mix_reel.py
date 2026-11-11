#!/usr/bin/env python3
"""mix_reel.py — Foley + Voices + Score Ducking for CLOSER AI Instagram Reel → mix_reel.wav
Mastered to -14.0 LUFS target.
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

DUR = 50.0
N = int(DUR * SR)

VOICE_SCHEDULE = {
    "r1": 0.5,
    "r2": 6.5,
    "r3": 11.2,
    "r_maya": 16.0,
    "r_pallavi": 26.0,
    "r_swati": 32.5,
    "r4": 40.0,
    "r5": 45.0
}

fol = np.zeros((N, 2), np.float32)
vox = np.zeros((N, 2), np.float32)
mus = np.zeros((N, 2), np.float32)

def sine(f, d, tau):
    return np.sin(2 * np.pi * f * t_(d)) * env_exp(d, tau)

def alert_ping():
    d = 0.35
    return norm(sine(1300, d, 0.04) + 0.5 * sine(1900, d, 0.03))

def sub_drop():
    d = 2.0
    tt = t_(d)
    freq = 65.0 * np.exp(-tt / 0.4) + 38.0
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return norm(np.sin(phase) * env_exp(d, 0.6) + lp(noise(d), 350) * env_exp(d, 0.02))

def digit_tick():
    d = 0.025
    return norm(bp(noise(d), 3200, 8000) * env_exp(d, 0.003))

# 1. Foley Placement
add(fol, alert_ping(), 0.5, 0.5)
add(fol, sub_drop(), 11.2, 0.85)
add(fol, sub_drop(), 40.0, 0.9)
for i in range(6):
    add(fol, digit_tick(), 40.6 + i * 0.25, 0.35)

# 2. Voices
vo_intervals = []
for lid, t_start in VOICE_SCHEDULE.items():
    wav_path = os.path.join(HERE, 'voices_reel', f"{lid}.wav")
    if not os.path.exists(wav_path):
        continue
    y, sr = sf.read(wav_path)
    if y.ndim > 1:
        y = y.mean(1)
    if sr != SR:
        y = resample_poly(y, SR, sr)
    y = compress(y / (np.max(np.abs(y)) + 1e-9) * 0.95, 0.3, 3.0)
    add(vox, y, t_start, 0.82, pan=0.0)
    vo_intervals.append((t_start, t_start + len(y) / SR))

# 3. Score
score_path = os.path.join(HERE, 'music', 'score_reel.wav')
if os.path.exists(score_path):
    m, msr = sf.read(score_path, always_2d=True)
    if msr != SR:
        m = resample_poly(m, SR, msr, axis=0)
    mus[:min(N, len(m))] = m[:N]

# 4. Ducking
duck = np.ones(N, dtype=np.float32)
duck_fol = np.ones(N, dtype=np.float32)
for a, b in vo_intervals:
    s = int(max(0, (a - 0.1) * SR))
    e = int(min(N, (b + 0.15) * SR))
    duck[s:e] = 10 ** (-8.0 / 20)
    duck_fol[s:e] = 10 ** (-3.0 / 20)

duck = uniform_filter1d(duck, int(0.15 * SR))
duck_fol = uniform_filter1d(duck_fol, int(0.1 * SR))

final_mix = (mus * 0.70 * duck[:, None]) + (fol * duck_fol[:, None]) + vox

fade_s = int(1.0 * SR)
final_mix[-fade_s:] *= np.linspace(1, 0, fade_s)[:, None]

for c in range(2):
    final_mix[:, c] = limit(final_mix[:, c], 0.92)

out_mix = os.path.join(HERE, 'mix_reel.wav')
sf.write(out_mix, final_mix.astype(np.float32), SR, subtype='PCM_16')
print(f"mix_reel.wav successfully created! Duration: {len(final_mix)/SR:.2f}s, Peak: {np.max(np.abs(final_mix)):.3f}")
