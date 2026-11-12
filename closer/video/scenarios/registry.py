"""
closer.video.scenarios.registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Central catalog, dynamic registry, and round-robin scenario dispatcher.
Ensures equal rotation across the 5 Indian SMB sectors (clinics, solar, real estate, edtech, agency)
to feed the 14-slot weekly master posting timetable.
"""

from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import json
import os

from closer.video.scenarios.base import ReelScenario, Sector, Language
from closer.video.scenarios.clinics import get_dental_implant_scenario, get_hair_clinic_scenario
from closer.video.scenarios.solar import get_rooftop_solar_scenario, get_commercial_solar_scenario
from closer.video.scenarios.realestate import get_luxury_villa_scenario, get_apartments_scenario
from closer.video.scenarios.edtech import get_ai_bootcamp_scenario, get_study_abroad_scenario
from closer.video.scenarios.agency import get_meta_ads_lead_trap_scenario, get_b2b_appointments_scenario


# In-memory scenario catalog
_SCENARIO_CATALOG: Dict[str, ReelScenario] = {}

# Default round-robin state path
DEFAULT_ROUND_ROBIN_STATE = Path(__file__).resolve().parent / "round_robin_state.json"

# Sector rotation order for the 14 weekly posting slots
SECTOR_ROTATION_ORDER = [
    Sector.CLINICS,
    Sector.SOLAR,
    Sector.REALESTATE,
    Sector.EDTECH,
    Sector.AGENCY
]


def _normalize_sector(sec: Union[Sector, str]) -> Sector:
    """Normalize string or Sector enum to canonical Sector enum."""
    if isinstance(sec, Sector):
        return sec
    s = str(sec).lower().strip()
    if s in ("clinics", "clinic"):
        return Sector.CLINICS
    if s in ("solar", "solar_epc"):
        return Sector.SOLAR
    if s in ("realestate", "real_estate", "realty"):
        return Sector.REALESTATE
    if s in ("edtech", "education"):
        return Sector.EDTECH
    if s in ("agency", "b2b_agency", "b2b"):
        return Sector.AGENCY
    return Sector(s)


def register_scenario(scenario: ReelScenario) -> None:
    """Registers a scenario into the global catalog after validation."""
    valid, errors = scenario.validate()
    if not valid:
        raise ValueError(f"Cannot register invalid scenario '{scenario.id}': {', '.join(errors)}")
    _SCENARIO_CATALOG[scenario.id] = scenario


def get_scenario(scenario_id: str) -> Optional[ReelScenario]:
    """Retrieves a scenario by its unique ID."""
    _ensure_scenarios_loaded()
    return _SCENARIO_CATALOG.get(scenario_id)


def list_scenarios(
    sector: Optional[Union[Sector, str]] = None,
    language: Optional[Union[Language, str]] = None
) -> List[ReelScenario]:
    """Lists scenarios with optional sector and language filtering."""
    _ensure_scenarios_loaded()
    scenarios = list(_SCENARIO_CATALOG.values())
    if sector is not None:
        norm_sec = _normalize_sector(sector)
        scenarios = [s for s in scenarios if s.sector == norm_sec]
    return scenarios


def list_sectors() -> List[str]:
    """Returns all supported sector identifiers."""
    return [s.value for s in Sector]


def get_round_robin_scenario(state_path: Optional[Union[str, Path]] = None) -> ReelScenario:
    """
    Selects the next scenario in sequence across sectors.
    Maintains a persistent JSON state file to ensure balanced rotation across all 5 sectors.
    """
    _ensure_scenarios_loaded()
    path = Path(state_path) if state_path else DEFAULT_ROUND_ROBIN_STATE
    
    last_sector_idx = -1
    last_scenario_ids = {}
    
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
                last_sector_idx = state.get("last_sector_index", -1)
                last_scenario_ids = state.get("last_scenario_by_sector", {})
        except Exception:
            pass

    # Advance to next sector in rotation
    next_sector_idx = (last_sector_idx + 1) % len(SECTOR_ROTATION_ORDER)
    target_sector = SECTOR_ROTATION_ORDER[next_sector_idx]
    
    sector_scenarios = list_scenarios(sector=target_sector)
    if not sector_scenarios:
        raise RuntimeError(f"No scenarios registered for sector: {target_sector}")

    # Pick next scenario in this sector
    last_id = last_scenario_ids.get(target_sector.value)
    selected_scenario = sector_scenarios[0]
    if last_id:
        for idx, s in enumerate(sector_scenarios):
            if s.id == last_id:
                selected_scenario = sector_scenarios[(idx + 1) % len(sector_scenarios)]
                break

    # Persist updated state
    last_scenario_ids[target_sector.value] = selected_scenario.id
    new_state = {
        "last_sector_index": next_sector_idx,
        "last_sector": target_sector.value,
        "selected_scenario_id": selected_scenario.id,
        "last_scenario_by_sector": last_scenario_ids
    }
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(new_state, f, indent=2)
    except Exception:
        pass

    return selected_scenario


def validate_all_scenarios() -> Dict[str, List[str]]:
    """Runs safety and layout validation across all registered presets."""
    _ensure_scenarios_loaded()
    results = {}
    for sid, scenario in _SCENARIO_CATALOG.items():
        valid, errors = scenario.validate()
        if not valid:
            results[sid] = errors
    return results


def _ensure_scenarios_loaded() -> None:
    """Idempotently loads all 10 core presets into the catalog."""
    if len(_SCENARIO_CATALOG) >= 10:
        return

    presets = [
        get_dental_implant_scenario(),
        get_hair_clinic_scenario(),
        get_rooftop_solar_scenario(),
        get_commercial_solar_scenario(),
        get_luxury_villa_scenario(),
        get_apartments_scenario(),
        get_ai_bootcamp_scenario(),
        get_study_abroad_scenario(),
        get_meta_ads_lead_trap_scenario(),
        get_b2b_appointments_scenario(),
    ]
    for p in presets:
        _SCENARIO_CATALOG[p.id] = p
