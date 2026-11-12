"""
closer.video.audio
~~~~~~~~~~~~~~~~~~
Speech synthesis, procedural Foley sound effects, and dynamic audio mixer.
Includes Kokoro ONNX + Edge-TTS unified engine, 24 procedural SFX cues,
dynamic speech ducking (-8.5 dB), and EBU R128 (-14.0 LUFS) master limiter.
"""

from closer.video.audio.sfx import (
    SR,
    generate_sfx,
    SFX_REGISTRY,
    telephone_ring,
    pickup_click,
    hangup_click,
    busy_tone,
    whatsapp_ping,
    alert_ping,
    comment_chime,
    sub_drop,
    whoosh_hit,
    light_sweep,
    digit_tick,
    coin_clink,
    clinic_chime,
    solar_whoosh,
)
try:
    from closer.video.audio.synthesizer import (
        VoiceSynthesizer,
        DialogueLine,
        SynthesisResult,
    )
except ImportError:
    VoiceSynthesizer = None
    DialogueLine = None
    SynthesisResult = None

try:
    from closer.video.audio.mixer import (
        AudioMixer,
        AudioMixResult,
        FoleyCue,
    )
except ImportError:
    AudioMixer = None
    AudioMixResult = None
    FoleyCue = None

__all__ = [
    "SR",
    "generate_sfx",
    "SFX_REGISTRY",
    "telephone_ring",
    "pickup_click",
    "hangup_click",
    "busy_tone",
    "whatsapp_ping",
    "alert_ping",
    "comment_chime",
    "sub_drop",
    "whoosh_hit",
    "light_sweep",
    "digit_tick",
    "coin_clink",
    "clinic_chime",
    "solar_whoosh",
    "VoiceSynthesizer",
    "DialogueLine",
    "SynthesisResult",
    "AudioMixer",
    "AudioMixResult",
    "FoleyCue",
]
