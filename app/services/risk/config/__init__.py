"""Configuration profiles and hashing module for Risk Governance.

Exposes the validation schema, built-in profiles registry, loader utility, and
stable hash generator.
"""

from __future__ import annotations

from app.services.risk.config.hashing import (
    ConfigHashComparison,
    canonicalize_risk_config_for_hash,
    compare_risk_config_hashes,
    hash_risk_config,
    validate_risk_config_hash,
)
from app.services.risk.config.loader import (
    APPROVED_OVERRIDE_KEYS,
    RiskConfigHash,
    RiskConfigLoader,
    RiskProfileRegistry,
    _registry,
    load_risk_config,
)
from app.services.risk.config.profiles import (
    build_live_conservative_profile,
    build_paper_profile,
    build_prop_firm_default_profile,
    build_safe_default_profile,
    get_builtin_risk_profile,
    list_builtin_risk_profiles,
)
from app.services.risk.config.schema import (
    MAX_DAILY_LOSS_PCT,
    MAX_EFFECTIVE_LEVERAGE,
    MAX_MARGIN_UTILIZATION_PCT,
    MAX_RISK_PER_TRADE,
    MAX_TOTAL_LOSS_PCT,
    validate_risk_config,
)

__all__ = [
    "APPROVED_OVERRIDE_KEYS",
    "MAX_DAILY_LOSS_PCT",
    "MAX_EFFECTIVE_LEVERAGE",
    "MAX_MARGIN_UTILIZATION_PCT",
    "MAX_RISK_PER_TRADE",
    "MAX_TOTAL_LOSS_PCT",
    "ConfigHashComparison",
    "RiskConfigHash",
    "RiskConfigLoader",
    "RiskProfileRegistry",
    "_registry",
    "build_live_conservative_profile",
    "build_paper_profile",
    "build_prop_firm_default_profile",
    "build_safe_default_profile",
    "canonicalize_risk_config_for_hash",
    "compare_risk_config_hashes",
    "get_builtin_risk_profile",
    "hash_risk_config",
    "list_builtin_risk_profiles",
    "load_risk_config",
    "validate_risk_config",
    "validate_risk_config_hash",
]
