"""Approved public regime-indicator API.

All six spec ``IND-RG-*`` indicators are registered here, per the plan's
scope for this domain: ``adx_dmi_regime`` (``IND-RG-01``),
``choppiness_regime`` (``IND-RG-02``), ``hurst_regime`` (``IND-RG-03``),
``donchian_breakout_regime`` (``IND-RG-04``),
``volatility_liquidity_stress_regime`` (``IND-RG-05``, a documented
reduced-input variant — see its module docstring), and
``final_regime_resolver`` (``IND-RG-06``).
"""

from app.services.indicators.regime.adx_dmi_regime import adx_dmi_regime
from app.services.indicators.regime.choppiness_regime import choppiness_regime
from app.services.indicators.regime.donchian_breakout_regime import (
    donchian_breakout_regime,
)
from app.services.indicators.regime.final_regime_resolver import (
    final_regime_resolver,
)
from app.services.indicators.regime.hurst_regime import hurst_regime
from app.services.indicators.regime.volatility_liquidity_stress_regime import (
    volatility_liquidity_stress_regime,
)

__all__ = [
    "adx_dmi_regime",
    "choppiness_regime",
    "donchian_breakout_regime",
    "final_regime_resolver",
    "hurst_regime",
    "volatility_liquidity_stress_regime",
]
