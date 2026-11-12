"""closer.video.audio.sfx — Procedural Foley & Sound Effects Engine.

Procedural sound synthesis and DSP primitives for CLOSER AI video reels.
Zero external asset dependency: generates telephone, UI, notification,
and cinematic retention SFX using pure NumPy and SciPy.
Sample rate: 48,000 Hz broadcast standard.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple, Union
import numpy as np
from scipy.signal import butter, sosfilt

SR: int = 48000
_rng = np.random.default_rng(2026)


def set_seed(seed: int = 2026) -> None:
    """Reset the deterministic random number generator."""
    global _rng
    _rng = np.random.default_rng(seed)


# ─────────────────────────────────────────────────────────────────────────────
# Core DSP Primitives
# ─────────────────────────────────────────────────────────────────────────────

def t_(d: float) -> np.ndarray:
    """Generate time vector for duration d in seconds at SR."""
    return np.arange(int(round(d * SR)), dtype=np.float32) / SR


def env_exp(d: float, tau: float) -> np.ndarray:
    """Exponential decay envelope: exp(-t / tau)."""
    return np.exp(-t_(d) / tau).astype(np.float32)


def env_adsr(
    d: float,
    attack: float = 0.01,
    decay: float = 0.05,
    sustain: float = 0.7,
    release: float = 0.05,
) -> np.ndarray:
    """ADSR envelope normalized to length of duration d."""
    total_n = int(round(d * SR))
    att_n = int(round(attack * SR))
    dec_n = int(round(decay * SR))
    rel_n = int(round(release * SR))
    sus_n = max(0, total_n - att_n - dec_n - rel_n)

    parts: List[np.ndarray] = []
    if att_n > 0:
        parts.append(np.linspace(0.0, 1.0, att_n, dtype=np.float32))
    if dec_n > 0:
        parts.append(np.linspace(1.0, sustain, dec_n, dtype=np.float32))
    if sus_n > 0:
        parts.append(np.full(sus_n, sustain, dtype=np.float32))
    if rel_n > 0:
        parts.append(np.linspace(sustain, 0.0, rel_n, dtype=np.float32))

    env = np.concatenate(parts) if parts else np.ones(total_n, dtype=np.float32)
    if len(env) < total_n:
        env = np.pad(env, (0, total_n - len(env)))
    return env[:total_n]


def bp(x: np.ndarray, lo: float, hi: float, o: int = 2) -> np.ndarray:
    """Bandpass Butterworth filter."""
    sos = butter(o, [lo, hi], "band", fs=SR, output="sos")
    return sosfilt(sos, x).astype(np.float32)


def lp(x: np.ndarray, f: float, o: int = 2) -> np.ndarray:
    """Lowpass Butterworth filter."""
    sos = butter(o, f, "low", fs=SR, output="sos")
    return sosfilt(sos, x).astype(np.float32)


def hp(x: np.ndarray, f: float, o: int = 2) -> np.ndarray:
    """Highpass Butterworth filter."""
    sos = butter(o, f, "high", fs=SR, output="sos")
    return sosfilt(sos, x).astype(np.float32)


def noise(d: float) -> np.ndarray:
    """White Gaussian noise of duration d."""
    return _rng.standard_normal(int(round(d * SR))).astype(np.float32)


def brown(d: float) -> np.ndarray:
    """Brown noise (integrated white noise, highpassed at 20Hz)."""
    w = np.cumsum(noise(d))
    w -= np.linspace(w[0], w[-1], len(w))
    return norm(hp(w, 20.0))


def norm(x: np.ndarray, peak: float = 1.0) -> np.ndarray:
    """Normalize array peak to peak amplitude."""
    m = float(np.max(np.abs(x))) if len(x) > 0 else 0.0
    return (x * (peak / m)).astype(np.float32) if m > 0.0 else x.astype(np.float32)


def sine(f: float, d: float, tau: float, ph: float = 0.0) -> np.ndarray:
    """Decaying sine wave at frequency f Hz with decay tau."""
    return (np.sin(2 * np.pi * f * t_(d) + ph) * env_exp(d, tau)).astype(np.float32)


def compress(
    x: np.ndarray,
    thr: float = 0.25,
    ratio: float = 3.5,
    att: float = 0.004,
    rel: float = 0.08,
) -> np.ndarray:
    """Dynamic range compressor (feed-forward peak detector)."""
    env = np.zeros_like(x, dtype=np.float32)
    a = float(np.exp(-1.0 / (att * SR)))
    r = float(np.exp(-1.0 / (rel * SR)))
    cur = 0.0
    abs_x = np.abs(x)
    for i in range(len(x)):
        v = abs_x[i]
        cur = a * cur + (1.0 - a) * v if v > cur else r * cur + (1.0 - r) * v
        env[i] = cur

    gain = np.ones_like(x, dtype=np.float32)
    over = env > thr
    if np.any(over):
        env_over = env[over]
        gain[over] = (thr + (env_over - thr) / ratio) / (env_over + 1e-9)
    return (x * gain).astype(np.float32)


def limit(x: np.ndarray, ceiling: float = 0.891, knee_db: float = 2.0) -> np.ndarray:
    """Soft-knee peak limiter enforcing strict ceiling without hard-clipping distortion."""
    peak = float(np.max(np.abs(x))) if len(x) > 0 else 0.0
    if peak <= ceiling:
        return x
    knee = 10.0 ** (-knee_db / 20.0)
    thresh = ceiling * knee
    out = np.copy(x)
    above = np.abs(out) > thresh
    if np.any(above):
        sgn = np.sign(out[above])
        mag = np.abs(out[above])
        compressed = thresh + (ceiling - thresh) * np.tanh((mag - thresh) / (ceiling - thresh + 1e-9))
        out[above] = sgn * compressed
    return np.clip(out, -ceiling, ceiling).astype(np.float32)


def add(
    target: np.ndarray,
    src: np.ndarray,
    t_sec: float = 0.0,
    gain: float = 1.0,
    pan: float = 0.0,
    at_time: Optional[float] = None,
) -> np.ndarray:
    """Add a sound source into a target canvas at t_sec with gain and stereo pan."""
    if at_time is not None:
        t_sec = at_time
    idx = int(round(t_sec * SR))
    if idx >= len(target):
        return target
    chunk_n = min(len(src), len(target) - idx)
    if chunk_n <= 0:
        return target

    src_chunk = src[:chunk_n] * gain
    if target.ndim == 1:
        if src_chunk.ndim == 1:
            target[idx:idx + chunk_n] += src_chunk
        else:
            target[idx:idx + chunk_n] += src_chunk.mean(axis=1)
    else:
        # Stereo target: pan in [-1.0 (left), 1.0 (right)]
        theta = (np.clip(pan, -1.0, 1.0) + 1.0) * (np.pi / 4.0)
        gain_l = float(np.cos(theta))
        gain_r = float(np.sin(theta))
        if src_chunk.ndim == 1:
            target[idx:idx + chunk_n, 0] += src_chunk * gain_l
            target[idx:idx + chunk_n, 1] += src_chunk * gain_r
        else:
            target[idx:idx + chunk_n, 0] += src_chunk[:, 0] * gain_l
            target[idx:idx + chunk_n, 1] += src_chunk[:, 1] * gain_r
    return target


def stereo(mono: np.ndarray, width: float = 0.25) -> np.ndarray:
    """Create pseudo-stereo field from mono source via micro-delay Haas effect."""
    n_delay = int(round(0.0006 * SR))  # 0.6ms Haas delay
    l_chan = mono
    r_chan = np.roll(mono, n_delay)
    r_chan[:n_delay] = 0.0
    out = np.column_stack([l_chan, r_chan])
    return (out * (1.0 - width) + np.column_stack([mono, mono]) * width).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# 1-14: Core Telephony, Notification & UI Sound Effects
# ─────────────────────────────────────────────────────────────────────────────

def telephone_ring(cadence: str = "india", gain: float = 0.75) -> np.ndarray:
    """Authentic telephone ring cadence."""
    if cadence == "india":
        # Dual-pulse ring: 0.4s ring, 0.2s pause, 0.4s ring, 2.0s silence
        d = 3.0
        tt = t_(d)
        tone = (np.sin(2 * np.pi * 400.0 * tt) + np.sin(2 * np.pi * 425.0 * tt)) * 0.5
        pulse1 = (tt >= 0.0) & (tt < 0.40)
        pulse2 = (tt >= 0.60) & (tt < 1.00)
        gate = (pulse1 | pulse2).astype(np.float32)
        env = bp(gate, 10.0, 1200.0)
        return norm(tone * env, gain)
    elif cadence == "us":
        # US/North America cadence: 2.0s ring, 4.0s silence
        d = 6.0
        tt = t_(d)
        tone = (np.sin(2 * np.pi * 440.0 * tt) + np.sin(2 * np.pi * 480.0 * tt)) * 0.5
        gate = ((tt >= 0.0) & (tt < 2.0)).astype(np.float32)
        return norm(tone * gate, gain)
    else:
        d = 1.0
        tt = t_(d)
        tone = (np.sin(2 * np.pi * 400.0 * tt) + np.sin(2 * np.pi * 450.0 * tt)) * 0.5
        return norm(tone * env_adsr(d, 0.05, 0.1, 0.8, 0.1), gain)


def pickup_click(gain: float = 0.80) -> np.ndarray:
    """Mechanical telephone handset cradle pickup click and line connect hiss."""
    d = 0.09
    click = hp(noise(d), 2800.0) * env_exp(d, 0.005)
    body = bp(noise(d), 450.0, 1800.0) * env_exp(d, 0.018)
    line_hum = np.sin(2 * np.pi * 60.0 * t_(d)) * 0.05
    return norm(click * 1.2 + body * 0.8 + line_hum, gain)


def hangup_click(gain: float = 0.85) -> np.ndarray:
    """Decisive phone slam hangup click with transient pop and chassis resonance."""
    d = 0.16
    pop = hp(noise(d), 2200.0) * env_exp(d, 0.004)
    thud = bp(noise(d), 120.0, 600.0) * env_exp(d, 0.035)
    cradle = sine(480.0, d, 0.02) + sine(320.0, d, 0.04)
    return norm(pop * 1.5 + thud * 1.0 + cradle * 0.4, gain)


def busy_tone(bursts: int = 3, gain: float = 0.70) -> np.ndarray:
    """PSTN telephone busy/disconnect tone."""
    total_d = bursts * 0.75
    tt = t_(total_d)
    tone = (np.sin(2 * np.pi * 480.0 * tt) + np.sin(2 * np.pi * 620.0 * tt)) * 0.5
    gate = (np.sin(2 * np.pi * (1.0 / 0.75) * tt) > 0.0).astype(np.float32)
    return norm(tone * gate, gain)


def whatsapp_ping(gain: float = 0.85) -> np.ndarray:
    """WhatsApp signature two-tone pop (C6 1046.5Hz + G6 1567.98Hz)."""
    d = 0.38
    t1 = sine(1046.5, d, 0.08)  # C6
    t2 = sine(1567.98, d, 0.12) # G6
    delay = int(round(0.055 * SR))
    comb = np.zeros(int(round(d * SR)), dtype=np.float32)
    comb[:len(t1)] += t1 * 0.7
    if delay < len(comb):
        chunk = min(len(t2), len(comb) - delay)
        comb[delay:delay + chunk] += t2[:chunk] * 0.9
    return norm(comb, gain)


def alert_ping(gain: float = 0.80) -> np.ndarray:
    """High-tech lead alert notification ping (1200Hz + 1800Hz bell chime)."""
    d = 0.40
    tone = sine(1200.0, d, 0.05) + 0.6 * sine(1800.0, d, 0.03)
    trans = hp(noise(d), 3000.0) * env_exp(d, 0.008) * 0.25
    return norm(tone + trans, gain)


def comment_chime(gain: float = 0.85, duration: float = 0.80) -> np.ndarray:
    """Celestial sparkle retention chord for 'Comment CLOSER' CTA (A6, E7, A7)."""
    d = duration
    chord = (
        sine(1760.0, d, 0.14) +
        0.60 * sine(2637.0, d, 0.18) +
        0.35 * sine(3520.0, d, 0.11)
    )
    sparkle = bp(noise(d), 4500.0, 11000.0) * env_exp(d, 0.02) * 0.15
    return norm(chord + sparkle, gain)


def sub_drop(gain: float = 0.95, duration: float = 2.2) -> np.ndarray:
    """Cinematic keynote sub-bass drop (70Hz swept to 36Hz with low-pass punch)."""
    d = duration
    tt = t_(d)
    freq = 70.0 * np.exp(-tt / 0.42) + 36.0
    phase = 2.0 * np.pi * np.cumsum(freq) / SR
    sub = np.sin(phase) * env_exp(d, 0.65)
    punch = lp(noise(d), 380.0) * env_exp(d, 0.02) * 0.80
    return norm(sub + punch, gain)


def whoosh_hit(gain: float = 0.85, duration: float = 0.45) -> np.ndarray:
    """High-velocity camera cut whoosh hit with low punch."""
    d = duration
    tt = t_(d)
    w = bp(noise(d), 200.0, 3500.0) * np.sin(np.pi * (tt / d)) ** 1.8
    punch = sine(95.0, d, 0.08)
    return norm(w * 0.80 + punch * 0.60, gain)


def light_sweep(duration: float = 1.5, gain: float = 0.80) -> np.ndarray:
    """Electric cyan shimmer sweep."""
    d = duration
    n = noise(d)
    tt = t_(d)
    sw = bp(n, 1200.0, 7000.0) * np.sin(np.pi * tt / d) ** 1.8
    ting = sine(2400.0, d, 0.20) * 0.30 + sine(3600.0, d, 0.15) * 0.20
    return norm(sw + ting, gain)


def digit_tick(gain: float = 0.50) -> np.ndarray:
    """Precision click for scrambled digit lock or phone dial."""
    d = 0.028
    return norm(bp(noise(d), 3000.0, 8000.0) * env_exp(d, 0.003) + sine(2800.0, d, 0.004) * 0.5, gain)


def coin_clink(gain: float = 0.50) -> np.ndarray:
    """High-frequency coin jackpot clink for ₹1.55 economics."""
    d = 0.25
    x = sine(2400.0, d, 0.03) + sine(3200.0, d, 0.02) + sine(4800.0, d, 0.015)
    return norm(x, gain)


def clinic_chime(gain: float = 0.60) -> np.ndarray:
    """Medical clean harmonic chime (C6, E6, C7)."""
    d = 0.55
    return norm(sine(1046.5, d, 0.06) + sine(1318.5, d, 0.08) + sine(2093.0, d, 0.05), gain)


def solar_whoosh(gain: float = 0.60) -> np.ndarray:
    """Airy solar energy whoosh (bandpassed noise 800-2400Hz)."""
    d = 0.50
    return norm(bp(noise(d), 800.0, 2400.0) * env_exp(d, 0.08), gain)


# ─────────────────────────────────────────────────────────────────────────────
# 15-24: Additional Procedural UI & Retention Foley Cues
# ─────────────────────────────────────────────────────────────────────────────

def door_chime(gain: float = 0.75) -> np.ndarray:
    """Classic two-tone receptionist door chime (Ding-Dong: E5 659Hz + C5 523Hz)."""
    d = 1.2
    d1 = sine(659.25, d, 0.35)
    d2 = sine(523.25, d, 0.45)
    delay = int(round(0.28 * SR))
    comb = np.zeros(int(round(d * SR)), dtype=np.float32)
    comb[:len(d1)] += d1 * 0.7
    if delay < len(comb):
        chunk = min(len(d2), len(comb) - delay)
        comb[delay:delay + chunk] += d2[:chunk] * 0.8
    return norm(comb, gain)


def camera_shutter(gain: float = 0.70) -> np.ndarray:
    """Mechanical camera shutter click & flash whirr."""
    d = 0.22
    click1 = hp(noise(d), 3500.0) * env_exp(d, 0.005)
    click2 = bp(noise(d), 1200.0, 4000.0) * env_exp(d, 0.015)
    delay = int(round(0.045 * SR))
    comb = np.zeros(int(round(d * SR)), dtype=np.float32)
    comb[:len(click1)] += click1
    if delay < len(comb):
        chunk = min(len(click2), len(comb) - delay)
        comb[delay:delay + chunk] += click2[:chunk] * 0.8
    return norm(comb, gain)


def card_swipe(gain: float = 0.65) -> np.ndarray:
    """Friction swipe sound for document card presentation."""
    d = 0.18
    sw = bp(noise(d), 1500.0, 5500.0) * env_adsr(d, 0.02, 0.05, 0.5, 0.04)
    return norm(sw, gain)


def bubble_pop(gain: float = 0.60) -> np.ndarray:
    """Playful liquid bubble pop for WhatsApp asset badge."""
    d = 0.08
    freq = np.linspace(400.0, 1600.0, int(round(d * SR)))
    pop = np.sin(2 * np.pi * np.cumsum(freq) / SR) * env_exp(d, 0.015)
    return norm(pop, gain)


def notification_gentle(gain: float = 0.70) -> np.ndarray:
    """Soft three-note marimba chime (F5, A5, C6)."""
    d = 0.65
    n1 = sine(698.46, d, 0.12)
    n2 = sine(880.00, d, 0.14)
    n3 = sine(1046.50, d, 0.16)
    comb = np.zeros(int(round(d * SR)), dtype=np.float32)
    d1 = int(round(0.06 * SR))
    d2 = int(round(0.12 * SR))
    comb[:len(n1)] += n1 * 0.5
    if d1 < len(comb):
        chunk = min(len(n2), len(comb) - d1)
        comb[d1:d1 + chunk] += n2[:chunk] * 0.6
    if d2 < len(comb):
        chunk = min(len(n3), len(comb) - d2)
        comb[d2:d2 + chunk] += n3[:chunk] * 0.7
    return norm(comb, gain)


def error_buzz(gain: float = 0.65) -> np.ndarray:
    """Low harsh rejection buzz for client churn / lead drop alerts."""
    d = 0.35
    tt = t_(d)
    saw = (2.0 * (tt * 140.0 - np.floor(tt * 140.0 + 0.5))) * env_exp(d, 0.10)
    filtered = lp(saw, 800.0)
    return norm(filtered, gain)


def keyboard_type(gain: float = 0.55) -> np.ndarray:
    """Rapid mechanical keyboard keystroke burst."""
    d = 0.12
    n = noise(d)
    click = hp(n, 2500.0) * env_exp(d, 0.003)
    clack = bp(n, 800.0, 2200.0) * env_exp(d, 0.012)
    return norm(click * 0.7 + clack * 0.8, gain)


def sparkle_riser(duration: float = 1.0, gain: float = 0.75) -> np.ndarray:
    """Ascending cosmic pitch riser."""
    d = duration
    tt = t_(d)
    freq = np.linspace(800.0, 4200.0, len(tt))
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR) * (tt / d) ** 1.5
    shimmer = bp(noise(d), 3000.0, 8000.0) * (tt / d) ** 2.0 * 0.25
    return norm(tone + shimmer, gain)


def heartbeat(gain: float = 0.85) -> np.ndarray:
    """Low frequency physiological heartbeat pulse (lub-dub)."""
    d = 0.60
    t1 = sine(55.0, d, 0.05) + sine(80.0, d, 0.03)
    t2 = sine(50.0, d, 0.06) + sine(75.0, d, 0.04)
    comb = np.zeros(int(round(d * SR)), dtype=np.float32)
    delay = int(round(0.14 * SR))
    comb[:len(t1)] += t1 * 0.8
    if delay < len(comb):
        chunk = min(len(t2), len(comb) - delay)
        comb[delay:delay + chunk] += t2[:chunk] * 0.9
    return norm(comb, gain)


def ambient_bed(duration: float = 2.0, gain: float = 0.40) -> np.ndarray:
    """Warm analog synth drone bed for scene depth."""
    d = duration
    tt = t_(d)
    pad = (
        np.sin(2 * np.pi * 110.0 * tt) * 0.4 +
        np.sin(2 * np.pi * 220.0 * tt) * 0.3 +
        np.sin(2 * np.pi * 330.0 * tt) * 0.2
    )
    filtered = lp(pad, 450.0)
    return norm(filtered * env_adsr(d, 0.2, 0.1, 0.8, 0.2), gain)


# ─────────────────────────────────────────────────────────────────────────────
# 24 SFX Registry & Factory
# ─────────────────────────────────────────────────────────────────────────────

SFX_REGISTRY: Dict[str, Callable[..., np.ndarray]] = {
    # 1-14 Core
    "telephone_ring": telephone_ring,
    "ring": telephone_ring,
    "pickup_click": pickup_click,
    "pickup": pickup_click,
    "hangup_click": hangup_click,
    "hangup": hangup_click,
    "busy_tone": busy_tone,
    "busy": busy_tone,
    "whatsapp_ping": whatsapp_ping,
    "whatsapp": whatsapp_ping,
    "alert_ping": alert_ping,
    "alert": alert_ping,
    "comment_chime": comment_chime,
    "chime": comment_chime,
    "sub_drop": sub_drop,
    "whoosh_hit": whoosh_hit,
    "whoosh": whoosh_hit,
    "light_sweep": light_sweep,
    "digit_tick": digit_tick,
    "tick": digit_tick,
    "coin_clink": coin_clink,
    "coin": coin_clink,
    "clinic_chime": clinic_chime,
    "solar_whoosh": solar_whoosh,
    # 15-24 Additional
    "door_chime": door_chime,
    "camera_shutter": camera_shutter,
    "card_swipe": card_swipe,
    "bubble_pop": bubble_pop,
    "notification_gentle": notification_gentle,
    "error_buzz": error_buzz,
    "keyboard_type": keyboard_type,
    "sparkle_riser": sparkle_riser,
    "heartbeat": heartbeat,
    "ambient_bed": ambient_bed,
}


def generate_sfx(name: str, **kwargs) -> np.ndarray:
    """Generate a sound effect by name from the registry."""
    clean_name = name.lower().strip()
    if clean_name not in SFX_REGISTRY:
        raise KeyError(f"Unknown SFX '{name}'. Available: {list(SFX_REGISTRY.keys())}")
    return SFX_REGISTRY[clean_name](**kwargs)
