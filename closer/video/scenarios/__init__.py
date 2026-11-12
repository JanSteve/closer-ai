"""
closer.video.scenarios
~~~~~~~~~~~~~~~~~~~~~~
Sector scenario presets, data models, validation, and round-robin scheduler.
Supports 5 Indian business domains: Clinics, Solar EPC, Real Estate, EdTech, and B2B Agency.
"""

from closer.video.scenarios.base import (
    Sector,
    Language,
    AttireType,
    ExpressionType,
    HairStyle,
    CharacterRigConfig,
    WhatsAppAsset,
    ScenarioLine,
    FoleyCue,
    ReelScenario,
)
from closer.video.scenarios.registry import (
    get_scenario,
    list_scenarios,
    list_sectors,
    get_round_robin_scenario,
    validate_all_scenarios,
    register_scenario,
)

__all__ = [
    "Sector",
    "Language",
    "AttireType",
    "ExpressionType",
    "HairStyle",
    "CharacterRigConfig",
    "WhatsAppAsset",
    "ScenarioLine",
    "FoleyCue",
    "ReelScenario",
    "get_scenario",
    "list_scenarios",
    "list_sectors",
    "get_round_robin_scenario",
    "validate_all_scenarios",
    "register_scenario",
]
