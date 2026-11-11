#!/usr/bin/env python3
"""mix_reel.py — Foley + Voices + Score Ducking for CLOSER AI 68s Multi-Sector Instagram Reel
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

DUR = 68.0
N = int(DUR * SR)

VOICE_SCHEDULE = {
    "r1_agency": 0.4,
    "r2_hangup": 7.8,
    "r3_harvard": 14.0,
    "r4_closer": 19.8,
    "r_maya": 26.5,
    "r_pallavi": 34.7,
    "r_swati": 41.1,
    "r5_whatsapp": 47.2,
    "r6_economics": 53.0,
    "r7_cta": 59.2
}

fol = np.zeros((N, 2), np.float32)
vox = np.zeros((N, 2), np.float32)
mus = np.zeros((N, 2), np.float32)

def sine(f, d, tau):
    return np.sin(2 * np.pi * f * t_(d)) * env_exp(d, tau)

def whoosh_hit():
    d = 0.45
    tt = t_(d)
    w = bp(noise(d), 200, 3500) * np.sin(np.pi * (tt / d)) ** 1.8
    punch = sine(95, d, 0.08)
    return norm(w * 0.8 + punch * 0.6)

def alert_ping():
    d = 0.35
    return norm(sine(1300, d, 0.04) + 0.5 * sine(1900, d, 0.03))

def sub_drop():
    d = 2.0
    tt = t_(d)
    freq = 70.0 * np.exp(-tt / 0.38) + 36.0
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return norm(np.sin(phase) * env_exp(d, 0.6) + lp(noise(d), 350) * env_exp(d, 0.02))

def hangup_click():
    d = 0.3
    tt = t_(d)
    click = hp(noise(d), 4000) * env_exp(d, 0.005)
    busy = np.sin(2 * np.pi * 480 * tt) * env_exp(d, 0.05)
    return norm(click * 0.8 + busy * 0.4)

def clinic_chime():
    d = 0.5
    return norm(sine(1046.5, d, 0.06) + sine(1318.5, d, 0.08) + sine(2093, d, 0.05))

def solar_whoosh():
    d = 0.5
    return norm(bp(noise(d), 800, 2400) * env_exp(d, 0.08))

def whatsapp_pop():
    d = 0.4
    tone1 = sine(1046.5, d, 0.08) # C6
    tone2 = sine(1567.98, d, 0.12) # G6
    delay = int(0.06 * SR)
    combined = np.zeros(int(d * SR), dtype=np.float32)
    combined[:len(tone1)] += tone1 * 0.7
    combined[delay:delay + len(tone2) - delay] += tone2[:len(tone2) - delay] * 0.9
    return norm(combined)

def coin_clink():
    d = 0.25
    return norm(sine(2400, d, 0.03) + sine(3200, d, 0.02) + sine(4800, d, 0.015))

def comment_chime():
    d = 0.7
    return norm(sine(1760, d, 0.12) + sine(2637, d, 0.16) + sine(3520, d, 0.09))

def digit_tick():
    d = 0.025
    return norm(bp(noise(d), 3200, 8000) * env_exp(d, 0.003))

# ──────────────── Foley Placement on Key Retention Cuts ────────────────
add(fol, whoosh_hit(), 0.0, 0.85)     # 0.0s AGENCY INVOICE EXPLOSION
add(fol, alert_ping(), 0.4, 0.5)      # 0.4s Invoice ding
add(fol, whoosh_hit(), 7.8, 0.65)     # 7.8s CUT TO CUSTOMER HANGUP
add(fol, hangup_click(), 11.2, 0.85)  # 11.2s PHONE HANGUP CLICK & BUSY TONE
add(fol, whoosh_hit(), 14.0, 0.6)     # 14.0s 5-MIN BRAIN FREEZE COUNTDOWN
add(fol, alert_ping(), 14.1, 0.4)     # 14.1s Timer countdown ping
add(fol, whoosh_hit(), 19.8, 0.7)     # 19.8s CUT TO CLOSER AI HERO
add(fol, sub_drop(), 19.8, 0.95)      # 19.8s SUB BASS DROP
add(fol, alert_ping(), 26.5, 0.35)    # 26.5s Maya English Luxury Villa
add(fol, clinic_chime(), 34.7, 0.55)  # 34.7s Pallavi Tamil Clinic Medical Chime
add(fol, solar_whoosh(), 41.1, 0.5)   # 41.1s Swati Hindi Solar Whoosh
add(fol, whatsapp_pop(), 47.2, 0.85)  # 47.2s WHATSAPP 3-SECTOR PUSH
add(fol, whoosh_hit(), 53.0, 0.65)    # 53.0s UNIT ECONOMICS CUT
add(fol, sub_drop(), 53.0, 0.9)       # 53.0s BASS DROP ON ₹1.55
for i in range(6):
    add(fol, digit_tick(), 53.4 + i * 0.18, 0.35)
    add(fol, coin_clink(), 53.6 + i * 0.22, 0.4) # Coin jackpot clinking!
add(fol, comment_chime(), 59.2, 0.85) # 59.2s COMMENT CLOSER SPARKLE
add(fol, whoosh_hit(), 59.2, 0.5)     # 59.2s Arrow whoosh

# ──────────────── Voices Placement ────────────────
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

# ──────────────── Score Placement ────────────────
score_path = os.path.join(HERE, 'music', 'score_reel.wav')
if os.path.exists(score_path):
    m, msr = sf.read(score_path, always_2d=True)
    if msr != SR:
        m = resample_poly(m, SR, msr, axis=0)
    mus[:min(N, len(m))] = m[:N]

# ──────────────── Dynamic Ducking ────────────────
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
