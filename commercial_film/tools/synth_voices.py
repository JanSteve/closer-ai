#!/usr/bin/env python3
"""Synthesize all film voiceover lines using Microsoft neural voices via edge-tts.
Outputs 24kHz mono WAV files to voices/<id>.wav and computes voices/dur.json.
"""
import os, sys, json, asyncio, subprocess, tempfile
import numpy as np
import soundfile as sf
import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
FILM_DIR = os.path.dirname(HERE)
LINES_PATH = os.path.join(FILM_DIR, 'lines.json')
VOICES_DIR = os.path.join(FILM_DIR, 'voices')
DUR_PATH = os.path.join(VOICES_DIR, 'dur.json')
SR = 24000

os.makedirs(VOICES_DIR, exist_ok=True)

def trim_silence(y, top_db=32):
    """Trim leading and trailing silence from audio array."""
    if len(y) == 0:
        return y
    peak = np.max(np.abs(y))
    if peak == 0:
        return y
    threshold = peak * (10 ** (-top_db / 20))
    active = np.where(np.abs(y) >= threshold)[0]
    if len(active) == 0:
        return y
    start = max(0, active[0] - int(SR * 0.05)) # keep 50ms padding
    end = min(len(y), active[-1] + int(SR * 0.05))
    return y[start:end]

async def synth_line(item):
    line_id = item['id']
    text = item.get('say', item['text'])
    voice = item.get('voice', 'en-US-ChristopherNeural')
    rate = item.get('rate', '+0%')
    pitch = item.get('pitch', '+0Hz')
    wav_path = os.path.join(VOICES_DIR, f"{line_id}.wav")

    print(f"Synthesizing [{line_id}] using {voice}...")
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_mp3:
        mp3_name = tmp_mp3.name

    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(mp3_name)

        # Convert to 24kHz mono WAV with ffmpeg
        tmp_wav = mp3_name + '.wav'
        cmd = [
            'ffmpeg', '-y', '-v', 'error',
            '-i', mp3_name,
            '-ar', str(SR),
            '-ac', '1',
            tmp_wav
        ]
        subprocess.run(cmd, check=True)

        samples, sr = sf.read(tmp_wav, dtype='float32')
        samples = trim_silence(samples)

        # Normalize to -1.5 dB peak
        pk = np.max(np.abs(samples))
        if pk > 0:
            samples = samples / pk * (10 ** (-1.5 / 20))

        sf.write(wav_path, samples, SR, subtype='PCM_16')
        dur = len(samples) / SR
        print(f" -> Saved {wav_path} ({dur:.2f}s)")
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)
        return line_id, dur
    finally:
        if os.path.exists(mp3_name):
            os.remove(mp3_name)

async def main():
    with open(LINES_PATH, 'r', encoding='utf-8') as f:
        lines = json.load(f)

    durs = {}
    for item in lines:
        lid, dur = await synth_line(item)
        durs[lid] = round(dur, 3)

    with open(DUR_PATH, 'w', encoding='utf-8') as f:
        json.dump(durs, f, indent=2)
    print(f"\nAll voice lines rendered successfully! Durations saved to {DUR_PATH}")

if __name__ == '__main__':
    asyncio.run(main())
