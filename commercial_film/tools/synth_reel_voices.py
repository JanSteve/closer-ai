#!/usr/bin/env python3
"""Synthesize voice lines for the 38-second Instagram Reel.
Uses Kokoro TTS (af_heart) for narrator, (af_bella) for Maya, and Edge-TTS for Tamil/Hindi.
"""
import os, sys, json, asyncio, subprocess, tempfile
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
FILM_DIR = os.path.dirname(HERE)
LEMO_ROOT = '/Users/janstevedaniel/lemo-opuscar'
sys.path.insert(0, LEMO_ROOT)

LINES_PATH = os.path.join(FILM_DIR, 'lines_reel.json')
VOICES_DIR = os.path.join(FILM_DIR, 'voices_reel')
DUR_PATH = os.path.join(VOICES_DIR, 'dur.json')
SR = 24000

os.makedirs(VOICES_DIR, exist_ok=True)

from kokoro_onnx import Kokoro
kokoro = Kokoro(
    os.path.join(LEMO_ROOT, 'core/tts/kokoro-v1.0.onnx'),
    os.path.join(LEMO_ROOT, 'core/tts/voices-v1.0.bin')
)

def trim_silence(y, top_db=32):
    if len(y) == 0:
        return y
    peak = np.max(np.abs(y))
    if peak == 0:
        return y
    threshold = peak * (10 ** (-top_db / 20))
    active = np.where(np.abs(y) >= threshold)[0]
    if len(active) == 0:
        return y
    start = max(0, active[0] - int(SR * 0.05))
    end = min(len(y), active[-1] + int(SR * 0.05))
    return y[start:end]

async def synth_edgetts(text, voice, rate="+0%", pitch="+0Hz"):
    import edge_tts
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_mp3:
        mp3_name = tmp_mp3.name

    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(mp3_name)

        tmp_wav = mp3_name + '.wav'
        cmd = ['ffmpeg', '-y', '-v', 'error', '-i', mp3_name, '-ar', str(SR), '-ac', '1', tmp_wav]
        subprocess.run(cmd, check=True)

        samples, _ = sf.read(tmp_wav, dtype='float32')
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)
        return samples
    finally:
        if os.path.exists(mp3_name):
            os.remove(mp3_name)

async def synth_line(item):
    line_id = item['id']
    text = item.get('say', item['text'])
    voice = item.get('voice', 'af_heart')
    speed = float(item.get('speed', 1.0))
    wav_path = os.path.join(VOICES_DIR, f"{line_id}.wav")

    print(f"Synthesizing Reel [{line_id}] using {voice}...")

    if voice.startswith('af_') or voice.startswith('bf_'):
        samples, _ = kokoro.create(text, voice=voice, speed=speed, lang='en-us')
        samples = np.array(samples, dtype=np.float32)
    else:
        rate_str = item.get('rate', '+0%')
        pitch_str = item.get('pitch', '+0Hz')
        samples = await synth_edgetts(text, voice, rate=rate_str, pitch=pitch_str)

    samples = trim_silence(samples)
    pk = np.max(np.abs(samples))
    if pk > 0:
        samples = samples / pk * (10 ** (-1.2 / 20))

    sf.write(wav_path, samples, SR, subtype='PCM_16')
    dur = len(samples) / SR
    print(f" -> Saved {wav_path} ({dur:.2f}s)")
    return line_id, dur

async def main():
    with open(LINES_PATH, 'r', encoding='utf-8') as f:
        lines = json.load(f)

    durs = {}
    for item in lines:
        lid, dur = await synth_line(item)
        durs[lid] = round(dur, 3)

    with open(DUR_PATH, 'w', encoding='utf-8') as f:
        json.dump(durs, f, indent=2)
    print(f"\nAll Reel voice lines synthesized: {DUR_PATH}")

if __name__ == '__main__':
    asyncio.run(main())
