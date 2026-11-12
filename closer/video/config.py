"""
closer.video.config
~~~~~~~~~~~~~~~~~~~
Configuration parameters, safe zone coordinates, audio/video specifications,
and Indian sector presets for the CLOSER AI video rendering pipeline.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# 1. CANVAS 2D STAGE & SAFE ZONE GEOMETRY
# ─────────────────────────────────────────────────────────────────────────────
CANVAS_WIDTH: int = 1080
CANVAS_HEIGHT: int = 1920
ASPECT_RATIO: str = "9:16"
DEFAULT_FPS: int = 30
DEFAULT_WORKERS: int = 4

# Instagram Reels Occlusion Boundaries (1080x1920 viewport)
# - Top 220px: Stories/Reel header, sound label, back buttons
# - Bottom 370px (1550-1920): Account handle, captions, audio track pill, bottom navigation
# - Right 160px (920-1080): Like, comment, share, remix, audio disc icon stack
OCCLUSION_TOP_Y: int = 220
OCCLUSION_BOTTOM_Y: int = 1550
OCCLUSION_RIGHT_X: int = 920

# Safe Zone Subtitle Positioning
# Hormozi karaoke subtitle baseline anchored strictly at subY = 1360
SAFE_ZONE_SUBTITLE_Y: int = 1360
SAFE_ZONE_SUBTITLE_MAX_W: int = 680
SAFE_ZONE_SUBTITLE_BOX_H: int = 68
SAFE_ZONE_SUBTITLE_FONT_SIZE: int = 38
SAFE_ZONE_TAG_OFFSET_Y: int = 68  # subY - 68

# Safe Zone Viral CTA Banner Positioning
# Anchored strictly at Y = 1530 (in the safe pocket above Instagram bottom controls)
SAFE_ZONE_CTA_Y: int = 1530
SAFE_ZONE_CTA_WIDTH: int = 960  # W - 120
SAFE_ZONE_CTA_HEIGHT: int = 74
SAFE_ZONE_CTA_KEYWORD: str = "CLOSER"
SAFE_ZONE_CTA_DEFAULT_TEXT: str = "💬 COMMENT 'CLOSER' FOR YOUR BUSINESS PLAYBOOK ➔"

# ─────────────────────────────────────────────────────────────────────────────
# 2. AUDIO & LOUDNESS MASTERING SPECIFICATIONS
# ─────────────────────────────────────────────────────────────────────────────
AUDIO_SAMPLE_RATE: int = 48000  # Broadcast standard for MP4 / Instagram
AUDIO_CHANNELS: int = 2         # Stereo
AUDIO_BITRATE: str = "192k"
AUDIO_MASTER_MP3_BITRATE: str = "320k"

# EBU R128 Loudness Normalization
TARGET_LOUDNESS_LUFS: float = -14.0
TARGET_TRUE_PEAK_DBTP: float = -1.2
TARGET_LOUDNESS_RANGE_LRA: float = 11.0

# Dynamic Voice Ducking
VOICE_DUCKING_DB: float = -8.5   # Duck musical score by -8.5 dB during speech
FOLEY_DUCKING_DB: float = -3.0   # Duck foley by -3.0 dB during speech
CONVERSATIONAL_PAUSE_MIN: float = 0.25
CONVERSATIONAL_PAUSE_MAX: float = 0.45

# ─────────────────────────────────────────────────────────────────────────────
# 3. VIDEO EXPORT VARIANTS & FFMPEG ENCODING PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class VideoFormatSpec:
    name: str
    width: int
    height: int
    codec_v: str
    crf: int
    preset: str
    profile_v: str
    pix_fmt: str
    faststart: bool
    scale_filter: str = ""
    crop_filter: str = ""

# Master Instagram Reel (1080x1920 MP4)
MASTER_REEL_SPEC = VideoFormatSpec(
    name="master_1080p",
    width=1080,
    height=1920,
    codec_v="libx264",
    crf=16,
    preset="medium",
    profile_v="high",
    pix_fmt="yuv420p",
    faststart=True
)

# 720p Mobile Preview (720x1280 MP4)
PREVIEW_720P_SPEC = VideoFormatSpec(
    name="preview_720p",
    width=720,
    height=1280,
    codec_v="libx264",
    crf=20,
    preset="fast",
    profile_v="high",
    pix_fmt="yuv420p",
    faststart=True,
    scale_filter="scale=720:1280:flags=lanczos"
)

# 1:1 Square Feed Cut (1080x1080 MP4)
SQUARE_FEED_SPEC = VideoFormatSpec(
    name="square_1080p",
    width=1080,
    height=1080,
    codec_v="libx264",
    crf=18,
    preset="fast",
    profile_v="high",
    pix_fmt="yuv420p",
    faststart=True,
    crop_filter="crop=1080:1080:0:420"
)

EXPORT_FORMAT_SPECS: Dict[str, VideoFormatSpec] = {
    "master_1080p": MASTER_REEL_SPEC,
    "preview_720p": PREVIEW_720P_SPEC,
    "square_1080p": SQUARE_FEED_SPEC,
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. INDIAN SMB SECTORS & PRESETS
# ─────────────────────────────────────────────────────────────────────────────
SECTORS: List[str] = [
    "clinics",
    "solar",
    "real_estate",
    "edtech",
    "b2b_agency"
]

SECTOR_ALIASES: Dict[str, str] = {
    "realestate": "real_estate",
    "real_estate": "real_estate",
    "agency": "b2b_agency",
    "b2b_agency": "b2b_agency",
    "b2b": "b2b_agency",
    "clinics": "clinics",
    "clinic": "clinics",
    "solar": "solar",
    "edtech": "edtech",
}

SECTOR_PRESETS: Dict[str, Dict] = {
    "clinics": {
        "title": "Dental & Hair Clinic Lead Drop-off Solution",
        "industry": "clinics",
        "sub_sector": "Dental Implants & Hair Restoration",
        "language": "tamil",
        "target_persona": "Clinic Owners, Dentists, Trichologists & Hospital Admins",
        "persona_host": "Dr. Pallavi",
        "persona_attire": "labcoat",
        "voice_id": "ta-IN-PallaviNeural",
        "hook": "Doctor: why does your front desk miss 40% of leads while in surgery?",
        "whatsapp_asset": "VIP_Clinic_Consultation_Pass.pkpass",
        "cta": "👇 COMMENT 'CLOSER' BELOW 👇 for the Dental & Hair Clinic Automated Lead Qualification Protocol"
    },
    "solar": {
        "title": "Rooftop Solar PM Surya Ghar Subsidy Closer",
        "industry": "solar",
        "sub_sector": "Residential & Commercial Rooftop Solar EPC",
        "language": "hindi",
        "target_persona": "Rooftop Solar EPC Contractors, Renewable Energy Founders",
        "persona_host": "Swati",
        "persona_attire": "high_vis_vest",
        "voice_id": "hi-IN-SwaraNeural",
        "hook": "₹78,000 PM Surya Ghar rooftop solar subsidy inquiries are freezing in your CRM.",
        "whatsapp_asset": "5kW_Solar_PM_Surya_Ghar_Quotation.pdf",
        "cta": "👇 COMMENT 'CLOSER' BELOW 👇 for the PM Surya Ghar 5kW Subsidy Prompt & Calculator"
    },
    "real_estate": {
        "title": "Luxury Real Estate & Villa NRI Buyer Closer",
        "industry": "real_estate",
        "sub_sector": "Luxury Coastal Villas & High-Rise Apartments",
        "language": "english",
        "target_persona": "Luxury Property Developers, Real Estate Brokers, Channel Partners",
        "persona_host": "Maya",
        "persona_attire": "blazer",
        "voice_id": "af_bella",
        "hook": "When a ₹2.85 Cr lead arrives from Dubai at 11:42 PM, your sales floor is asleep.",
        "whatsapp_asset": "ECR_Sea_Facing_Penthouse_Brochure.pdf",
        "cta": "👇 COMMENT 'CLOSER' BELOW 👇 for the Luxury Real Estate Inbound Closing Engine"
    },
    "edtech": {
        "title": "EdTech & Career Bootcamp Lead Speed to Enroll",
        "industry": "edtech",
        "sub_sector": "Executive AI Bootcamps & Admissions",
        "language": "multilingual",
        "target_persona": "EdTech Founders, Admissions Heads, Bootcamp Growth Leaders",
        "persona_host": "Rohan",
        "persona_attire": "polo",
        "voice_id": "en-IN-PrabhatNeural",
        "hook": "EdTech Founders: why are your prospective students blocking your telecallers?",
        "whatsapp_asset": "AI_Executive_Bootcamp_Curriculum_EMI.pdf",
        "cta": "👇 COMMENT 'CLOSER' BELOW 👇 for the EdTech Inbound Enrollment Playbook"
    },
    "b2b_agency": {
        "title": "B2B Performance Agency Client Retention Weapon",
        "industry": "b2b_agency",
        "sub_sector": "Meta Ads Lead Gen & High-Ticket B2B",
        "language": "english",
        "target_persona": "Agency Owners, Performance Marketers, Media Buyers",
        "persona_host": "Kabir",
        "persona_attire": "turtleneck",
        "voice_id": "af_heart",
        "hook": "Agency owners: how many high-paying clients did you lose last month because 'the leads were dead'?",
        "whatsapp_asset": "Performance_Agency_Client_Retention_Kit.pdf",
        "cta": "👇 COMMENT 'CLOSER' BELOW 👇 for the Agency Client Retention Automation Playbook"
    }
}
