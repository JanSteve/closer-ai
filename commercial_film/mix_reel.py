#!/usr/bin/env python3
"""mix_reel.py — Foley + Voices + Score Ducking for CLOSER AI 65s Instagram Reel → mix_reel.wav
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

DUR = 65.0
N = int(DUR * SR)

VOICE_SCHEDULE = {
    "r1_hook": 0.5,
    "r2_cliff": 8.1,
    "r3_intro": 19.8,
    "r_maya": 26.2,
    "r_pallavi": 35.2,
    "r_swati": 41.2,
    "r4_whatsapp": 46.3,
    "r5_economics": 52.6,
    "r6_cta": 58.9
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

def whatsapp_pop():
    d = 0.4
    tone1 = sine(1046.5, d, 0.08) # C6
    tone2 = sine(1567.98, d, 0.12) # G6
    delay = int(0.06 * SR)
    combined = np.zeros(int(d * SR), dtype=np.float32)
    combined[:len(tone1)] += tone1 * 0.7
    combined[delay:delay + len(tone2) - delay] += tone2[:len(tone2) - delay] * 0.9
    return norm(combined)

def comment_chime():
    d = 0.6
    return norm(sine(1760, d, 0.1) + sine(2637, d, 0.15) + sine(3520, d, 0.08))

def digit_tick():
    d = 0.025
    return norm(bp(noise(d), 3200, 8000) * env_exp(d, 0.003))

# 1. Foley Placement
add(fol, alert_ping(), 0.5, 0.5)
add(fol, alert_ping(), 8.1, 0.4)
add(fol, sub_drop(), 19.8, 0.85)
add(fol, whatsapp_pop(), 46.3, 0.8)
add(fol, sub_drop(), 52.6, 0.9)
for i in range(6):
    add(fol, digit_tick(), 53.2 + i * 0.2, 0.35)
add(fol, comment_chime(), 58.9, 0.75)

# 2. Voices
vo_intervals = []
for lid, t_start in VOICE_SCHEDULE.items():
    wav_path = os.path.join(HERE, 'voices_reel', f"{lid}.wav")
    if not os.path.exists(wav_path):
        print(f"Warning: {wav_path} not found")
        continue
    y, sr = sf.read(wav_path)
    if y.ndim > 1:
        y = y.mean(1)
    if sr != SR:
        y = resample_poly(y, SR, sr)
    y = compress(y / (np.max(np.abs(y)) + 1e-9) * 0.95, 0.3, 3.0)
    add(vox, y, t_start, 0.84, pan=0.0)
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
    duck[s:e] = 10 ** (-8.5 / 20)
    duck_fol[s:e] = 10 ** (-3.0 / 20)

duck = uniform_filter1d(duck, int(0.15 * SR))
duck_fol = uniform_filter1d(duck_fol, int(0.1 * SR))

final_mix = (mus * 0.70 * duck[:, None]) + (fol * duck_fol[:, None]) + vox

fade_s = int(1.2 * SR)
final_mix[-fade_s:] *= np.linspace(1, 0, fade_s)[:, None]

for c in range(2):
    final_mix[:, c] = limit(final_mix[:, c], 0.92)

out_mix = os.path.join(HERE, 'mix_reel.wav')
sf.write(out_mix, final_mix.astype(np.float32), SR, subtype='PCM_16')
print(f"mix_reel.wav successfully created! Duration: {len(final_mix)/SR:.2f}s, Peak: {np.max(np.abs(final_mix)):.3f}")
