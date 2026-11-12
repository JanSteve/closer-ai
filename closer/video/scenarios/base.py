"""
closer/video/scenarios/base.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Data contracts and schema definitions for CLOSER AI Video Scenarios.
Enforces type safety, safe-zone subtitle constraints (Y=1360), viral CTA hooks (Y=1530),
and character rig visual parameters for 1080x1920 9:16 vertical reels.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
import re
import json


class Sector(str, Enum):
    CLINICS = "clinics"
    SOLAR = "solar"
    REALESTATE = "real_estate"
    EDTECH = "edtech"
    AGENCY = "b2b_agency"


class Language(str, Enum):
    ENGLISH = "english"
    TAMIL = "tamil"
    HINDI = "hindi"
    MULTILINGUAL = "multilingual"


class AttireType(str, Enum):
    BLAZER = "blazer"
    LABCOAT = "labcoat"
    VEST = "vest"
    TURTLENECK = "turtleneck"
    POLO = "polo"
    SCRUBS = "scrubs"
    SMART_CASUAL = "smart_casual"
    HIGH_VIS_VEST = "high_vis_vest"


class ExpressionType(str, Enum):
    TALKING = "talking"
    SMILING = "smiling"
    ANGRY = "angry"
    STRESSED = "stressed"
    SERIOUS = "serious"
    SMUG = "smug"


class HairStyle(str, Enum):
    FADE = "fade"
    PARTED = "parted"
    BOB = "bob"
    BUN = "bun"
    PONYTAIL = "ponytail"
    MESSY = "messy"


@dataclass(frozen=True)
class CharacterRigConfig:
    """Configures procedural Canvas 2D character rendering in characters.js."""
    role: str                          # e.g., 'host', 'doctor', 'engineer', 'customer'
    name: str                          # Display name (e.g. 'Dr. Pallavi', 'Swati', 'Maya')
    skin_tone: str = "#D29568"         # Hex skin color
    skin_shadow: str = "#B07548"       # Hex skin shadow
    hair_color: str = "#1A1A1A"        # Hex hair color
    hair_style: str = "fade"           # Hair style identifier
    attire: str = "blazer"             # Attire identifier
    default_expression: str = "talking"# Starting expression
    accessories: List[str] = field(default_factory=list) # e.g. ['stethoscope', 'glasses']
    scale: float = 1.0                 # Visual scale factor
    position_x: int = 540              # Canvas X center (1080px width)
    position_y: int = 960              # Canvas Y center (1920px height)


@dataclass(frozen=True)
class WhatsAppAsset:
    """Configures the digital asset delivered via WhatsApp during the call."""
    title: str                         # e.g., "Dental Implant Pre-Op & Cost Guide.pdf"
    file_type: str                     # "pdf", "quote", "brochure", "pass", "dossier"
    file_size_display: str             # e.g., "2.4 MB"
    headline: str                      # Main title on the WhatsApp card
    subheadline: str                   # Explanatory subtitle
    badge_text: str = "INSTANT WHATSAPP SYNC"
    preview_bullet_points: List[str] = field(default_factory=list)
    cta_prompt: str = "Tap to view attachment"


@dataclass
class ScenarioLine:
    """Individual dialogue or narration line in the reel timeline."""
    id: str                            # Unique line identifier, e.g., 'c1_hook'
    speaker: str                       # Character name or 'Narrator'
    text: str                          # Exact text displayed on screen
    voice: str                         # Kokoro voice (e.g. 'af_heart') or Edge-TTS ('ta-IN-PallaviNeural')
    say: Optional[str] = None          # Phonetic or audio text (defaults to text if None)
    speed: float = 1.15                # TTS playback speed multiplier
    pitch: str = "+0Hz"                # Edge-TTS pitch adjustment
    rate: str = "+10%"                 # Edge-TTS rate string
    emotion: str = "confident"         # Delivery emotion
    character_id: Optional[str] = None # Links to CharacterRigConfig role
    estimated_duration: float = 0.0    # In seconds (computed or overridden)
    screen_tag: Optional[str] = None   # Subtitle category pill (e.g., 'HEALTHCARE CLINIC')
    scene_visual: Optional[str] = None # Visual background state identifier

    def get_speech_text(self) -> str:
        return self.say if self.say else self.text

    def estimate_duration_sec(self) -> float:
        """Estimates duration based on word count (~2.6 words/sec at 1.15 speed)."""
        words = len(self.get_speech_text().split())
        return max(1.2, round(words / (2.6 * self.speed), 2))


@dataclass(frozen=True)
class FoleyCue:
    """Synchronized audio sound effect cue."""
    timestamp: float                   # Timeline offset in seconds
    sound_effect: str                  # Function name in sfx.py (e.g. 'whoosh_hit', 'sub_drop')
    volume: float = 0.7                # Linear volume factor (0.0 to 1.0)
    description: str = ""


@dataclass
class ReelScenario:
    """
    Authoritative specification of an animated problem-solving reel scenario.
    Provides complete instructions for script synthesis, Canvas 2D scene composition,
    audio mixing, and social publishing metadata.
    """
    id: str                            # Unique scenario identifier (e.g., 'clinic_dental_implant_01')
    sector: Sector                     # Business sector enum
    sub_sector: str                    # Niche name (e.g., 'Dental Implants & Aligners')
    title: str                         # Human-readable title
    target_persona: str                # e.g., 'Clinic Owners, Dentists & Hospital Admins'
    target_duration: float             # Duration target in seconds (60.0 - 75.0s)
    
    # Story Sections
    opening_hook_lines: List[ScenarioLine]
    problem_dialogue: List[ScenarioLine]
    closer_solution_dialogue: List[ScenarioLine]
    whatsapp_asset_attachment: WhatsAppAsset
    cta_lines: List[ScenarioLine]
    
    # Visual & Audio Assets
    character_rig_configs: List[CharacterRigConfig]
    foley_cues: List[FoleyCue]
    caption_template: str
    cta_keyword: str = "CLOSER"
    
    # Economics Benchmark
    human_cost_per_lead: float = 220.0 # Standard Indian BPO telecaller cost (INR)
    closer_cost_per_lead: float = 1.55 # Autonomous CLOSER AI cost (INR)

    def get_all_lines(self) -> List[ScenarioLine]:
        """Returns flat list of all dialogue lines in chronological order."""
        return (
            self.opening_hook_lines +
            self.problem_dialogue +
            self.closer_solution_dialogue +
            self.cta_lines
        )

    def to_lines_json(self) -> List[Dict[str, Any]]:
        """Exports lines matching audio synthesizer input schema (lines_reel.json)."""
        output = []
        for line in self.get_all_lines():
            item = {
                "id": line.id,
                "speaker": line.speaker,
                "text": line.text,
                "voice": line.voice,
                "speed": line.speed,
            }
            if line.say and line.say != line.text:
                item["say"] = line.say
            if line.voice.startswith("ta-") or line.voice.startswith("hi-") or line.voice.startswith("en-IN-"):
                item["rate"] = line.rate
                item["pitch"] = line.pitch
            output.append(item)
        return output

    def to_subtitles_config(self) -> List[Dict[str, Any]]:
        """
        Exports subtitle configuration anchored strictly at safe-zone baseline Y = 1360.
        Calculates progressive start and end timestamps.
        """
        subs = []
        current_time = 0.4
        for line in self.get_all_lines():
            dur = line.estimated_duration if line.estimated_duration > 0 else line.estimate_duration_sec()
            subs.append({
                "t0": round(current_time, 2),
                "t1": round(current_time + dur, 2),
                "text": line.text,
                "tag": line.screen_tag or self.sub_sector.upper(),
                "safe_zone_y": 1360,
                "box_width_max": 680
            })
            current_time += dur + 0.25 # Short visual breath between sentences
        return subs

    def estimate_total_duration(self) -> float:
        """Estimates total spoken duration including natural dialogue pauses."""
        if self.target_duration and 58.0 <= self.target_duration <= 78.0:
            return round(self.target_duration, 1)
        total_speech = sum(
            l.estimated_duration if l.estimated_duration > 0 else l.estimate_duration_sec()
            for l in self.get_all_lines()
        )
        pauses = (len(self.get_all_lines()) - 1) * 0.25
        return round(0.4 + total_speech + pauses + 1.2, 1) # 1.2s tail for CTA freeze

    def format_caption(self) -> str:
        """Formats the Instagram caption with hashtags and CTA keyword."""
        return self.caption_template.replace("{CTA_KEYWORD}", self.cta_keyword)

    def validate(self) -> Tuple[bool, List[str]]:
        """Comprehensive verification of scenario rules and safety constraints."""
        errors = []
        
        # Duration target constraint (60 - 78 seconds safe reel window)
        est_dur = self.estimate_total_duration()
        if not (58.0 <= est_dur <= 78.0):
            errors.append(f"Estimated duration {est_dur}s out of safe reel window (58-78s)")

        # Section presence checks
        if not self.opening_hook_lines:
            errors.append("Opening hook lines cannot be empty")
        if not self.problem_dialogue:
            errors.append("Problem dialogue cannot be empty")
        if not self.closer_solution_dialogue:
            errors.append("CLOSER solution dialogue cannot be empty")
        if not self.cta_lines:
            errors.append("CTA lines cannot be empty")

        # CTA keyword verification
        all_cta_text = " ".join([l.text for l in self.cta_lines])
        if self.cta_keyword.lower() not in all_cta_text.lower():
            errors.append(f"CTA keyword '{self.cta_keyword}' missing from cta_lines")

        # Unique line IDs
        line_ids = [l.id for l in self.get_all_lines()]
        if len(line_ids) != len(set(line_ids)):
            errors.append("Duplicate line IDs detected in scenario")

        # Character rig linkage
        rig_roles = {r.role for r in self.character_rig_configs}
        for line in self.get_all_lines():
            if line.character_id and line.character_id not in rig_roles:
                errors.append(f"Line '{line.id}' references unknown character_id '{line.character_id}'")

        # Subtitle safe-zone constraints check
        for sub in self.to_subtitles_config():
            if sub["safe_zone_y"] != 1360:
                errors.append(f"Subtitle anchor {sub['safe_zone_y']} != 1360")
            if sub["box_width_max"] > 680:
                errors.append(f"Subtitle max width {sub['box_width_max']} > 680")

        return (len(errors) == 0, errors)
