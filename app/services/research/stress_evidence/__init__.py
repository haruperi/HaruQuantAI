"""FEAT-RES-16 stress-scenario evidence."""

from app.services.research.stress_evidence.contracts import (
    build_stress_scenario_evidence,
    parse_stress_scenario_evidence,
    validate_shock_basis,
)
from app.services.research.stress_evidence.derivation import (
    build_reasoned_stress_shock,
    derive_historical_stress_shock,
)
from app.services.research.stress_evidence.persistence import (
    load_latest_stress_scenario_evidence,
    persist_stress_scenario_evidence,
)
from app.services.research.stress_evidence.providers import (
    build_stress_calibration_provider,
)
from app.services.research.stress_evidence.scenarios import (
    build_registered_stress_scenario,
    get_stress_scenario_catalog,
)

__all__ = (
    "build_reasoned_stress_shock",
    "build_registered_stress_scenario",
    "build_stress_calibration_provider",
    "build_stress_scenario_evidence",
    "derive_historical_stress_shock",
    "get_stress_scenario_catalog",
    "load_latest_stress_scenario_evidence",
    "parse_stress_scenario_evidence",
    "persist_stress_scenario_evidence",
    "validate_shock_basis",
)
