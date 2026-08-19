"""Export-only public boundary for the Indicators domain."""

import typing

# Explicit imports keep type checking exact; runtime stays lazy.
if typing.TYPE_CHECKING:
    from app.services.indicators.core.closed_input import assert_closed_input
    from app.services.indicators.core.contracts import build_indicator_config
    from app.services.indicators.core.registry import (
        get_capability_matrix,
        get_indicator,
        list_indicators,
    )
    from app.services.indicators.core.results import (
        get_indicator_result_metadata,
        get_indicator_result_values,
        join_indicator_result,
    )
    from app.services.indicators.core.validation import (
        get_warmup_requirement,
        validate_indicator,
    )
    from app.services.indicators.liquidity.amihud_illiquidity import amihud_illiquidity
    from app.services.indicators.market_speed.composite_market_speed_gauge import (
        composite_market_speed_gauge,
    )
    from app.services.indicators.market_speed.market_event_arrival_rate import (
        market_event_arrival_rate,
    )
    from app.services.indicators.market_speed.momentum_acceleration import (
        momentum_acceleration,
    )
    from app.services.indicators.market_speed.price_velocity import price_velocity
    from app.services.indicators.market_speed.volatility_expansion_rate import (
        volatility_expansion_rate,
    )
    from app.services.indicators.market_speed.volume_acceleration import (
        volume_acceleration,
    )
    from app.services.indicators.migrations.definitions import run_indicators_migrations
    from app.services.indicators.momentum.rsi import rsi
    from app.services.indicators.momentum.williams_r import williams_r
    from app.services.indicators.order_flow.aggressive_trade_imbalance import (
        aggressive_trade_imbalance,
    )
    from app.services.indicators.order_flow.cumulative_volume_delta import (
        cumulative_volume_delta,
    )
    from app.services.indicators.patterns.breakout_retest import breakout_retest
    from app.services.indicators.patterns.doji import doji
    from app.services.indicators.patterns.double_top_bottom import double_top_bottom
    from app.services.indicators.patterns.engulfing import engulfing
    from app.services.indicators.patterns.evidence import build_chart_pattern_evidence
    from app.services.indicators.patterns.flag_pennant import flag_pennant
    from app.services.indicators.patterns.head_and_shoulders import head_and_shoulders
    from app.services.indicators.patterns.inside_bar import inside_bar
    from app.services.indicators.patterns.pinbar import pinbar
    from app.services.indicators.patterns.rectangle import rectangle
    from app.services.indicators.patterns.three_bar_reversal import three_bar_reversal
    from app.services.indicators.patterns.triangle import triangle
    from app.services.indicators.patterns.wedge import wedge
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
    from app.services.indicators.snapshots import (
        build_indicator_snapshot,
        parse_indicator_snapshot,
    )
    from app.services.indicators.structure.anchored_vwap import anchored_vwap
    from app.services.indicators.structure.donchian_channels import donchian_channels
    from app.services.indicators.structure.gaps import gaps
    from app.services.indicators.structure.level_clustering import level_clustering
    from app.services.indicators.structure.pivot_points import pivot_points
    from app.services.indicators.structure.pivots import pivots
    from app.services.indicators.structure.volume_profile import volume_profile
    from app.services.indicators.trend.aroon import aroon
    from app.services.indicators.trend.bollinger_bands import bollinger_bands
    from app.services.indicators.trend.directional import adx
    from app.services.indicators.trend.ema import ema
    from app.services.indicators.trend.ema_slope import ema_slope
    from app.services.indicators.trend.hull_ma import hull_ma
    from app.services.indicators.trend.linear_regression_trend import (
        linear_regression_trend,
    )
    from app.services.indicators.trend.macd import macd
    from app.services.indicators.trend.sma import sma
    from app.services.indicators.trend.strength import measure_trend_strength
    from app.services.indicators.trend.structural_levels import (
        project_structural_levels,
    )
    from app.services.indicators.trend.supertrend import supertrend
    from app.services.indicators.trend.wma import wma
    from app.services.indicators.trend.zigzag import zigzag
    from app.services.indicators.volatility.adr import adr
    from app.services.indicators.volatility.atr import atr
    from app.services.indicators.volatility.atr_percent import atr_percent
    from app.services.indicators.volatility.bollinger_bandwidth import (
        bollinger_bandwidth,
    )
    from app.services.indicators.volatility.envelope import measure_volatility_envelope
    from app.services.indicators.volatility.ewma_volatility import ewma_volatility
    from app.services.indicators.volatility.garman_klass_volatility import (
        garman_klass_volatility,
    )
    from app.services.indicators.volatility.market_projection import (
        project_market_overlay,
    )
    from app.services.indicators.volatility.market_speed import measure_market_speed
    from app.services.indicators.volatility.parkinson_volatility import (
        parkinson_volatility,
    )
    from app.services.indicators.volatility.rogers_satchell_volatility import (
        rogers_satchell_volatility,
    )
    from app.services.indicators.volatility.rolling_volatility import rolling_volatility
    from app.services.indicators.volatility.standard_deviation import standard_deviation
    from app.services.indicators.volatility.volatility_of_volatility import (
        volatility_of_volatility,
    )
    from app.services.indicators.volatility.volatility_percentile import (
        volatility_percentile,
    )
    from app.services.indicators.volume.cmf import cmf
    from app.services.indicators.volume.liquidity_snapshot import (
        build_liquidity_snapshot,
        parse_liquidity_snapshot,
    )
    from app.services.indicators.volume.mfi import mfi
    from app.services.indicators.volume.obv import obv
    from app.services.indicators.volume.order_flow import measure_order_flow
    from app.services.indicators.volume.price_volume_distribution import (
        price_volume_distribution,
    )

# Public export name to the module and attribute that owns it. Resolved on
# first access so importing this boundary never loads every feature.
_EXPORTS: dict[str, tuple[str, str]] = {
    "adr": ("app.services.indicators.volatility.adr", "adr"),
    "adx": ("app.services.indicators.trend.directional", "adx"),
    "adx_dmi_regime": (
        "app.services.indicators.regime.adx_dmi_regime",
        "adx_dmi_regime",
    ),
    "aggressive_trade_imbalance": (
        "app.services.indicators.order_flow.aggressive_trade_imbalance",
        "aggressive_trade_imbalance",
    ),
    "amihud_illiquidity": (
        "app.services.indicators.liquidity.amihud_illiquidity",
        "amihud_illiquidity",
    ),
    "anchored_vwap": (
        "app.services.indicators.structure.anchored_vwap",
        "anchored_vwap",
    ),
    "aroon": ("app.services.indicators.trend.aroon", "aroon"),
    "assert_closed_input": (
        "app.services.indicators.core.closed_input",
        "assert_closed_input",
    ),
    "atr": ("app.services.indicators.volatility.atr", "atr"),
    "atr_percent": ("app.services.indicators.volatility.atr_percent", "atr_percent"),
    "bollinger_bands": (
        "app.services.indicators.trend.bollinger_bands",
        "bollinger_bands",
    ),
    "bollinger_bandwidth": (
        "app.services.indicators.volatility.bollinger_bandwidth",
        "bollinger_bandwidth",
    ),
    "breakout_retest": (
        "app.services.indicators.patterns.breakout_retest",
        "breakout_retest",
    ),
    "build_chart_pattern_evidence": (
        "app.services.indicators.patterns.evidence",
        "build_chart_pattern_evidence",
    ),
    "build_indicator_config": (
        "app.services.indicators.core.contracts",
        "build_indicator_config",
    ),
    "build_indicator_snapshot": (
        "app.services.indicators.snapshots",
        "build_indicator_snapshot",
    ),
    "build_liquidity_snapshot": (
        "app.services.indicators.volume.liquidity_snapshot",
        "build_liquidity_snapshot",
    ),
    "choppiness_regime": (
        "app.services.indicators.regime.choppiness_regime",
        "choppiness_regime",
    ),
    "cmf": ("app.services.indicators.volume.cmf", "cmf"),
    "composite_market_speed_gauge": (
        "app.services.indicators.market_speed.composite_market_speed_gauge",
        "composite_market_speed_gauge",
    ),
    "cumulative_volume_delta": (
        "app.services.indicators.order_flow.cumulative_volume_delta",
        "cumulative_volume_delta",
    ),
    "doji": ("app.services.indicators.patterns.doji", "doji"),
    "donchian_breakout_regime": (
        "app.services.indicators.regime.donchian_breakout_regime",
        "donchian_breakout_regime",
    ),
    "donchian_channels": (
        "app.services.indicators.structure.donchian_channels",
        "donchian_channels",
    ),
    "double_top_bottom": (
        "app.services.indicators.patterns.double_top_bottom",
        "double_top_bottom",
    ),
    "ema": ("app.services.indicators.trend.ema", "ema"),
    "ema_slope": ("app.services.indicators.trend.ema_slope", "ema_slope"),
    "engulfing": ("app.services.indicators.patterns.engulfing", "engulfing"),
    "ewma_volatility": (
        "app.services.indicators.volatility.ewma_volatility",
        "ewma_volatility",
    ),
    "final_regime_resolver": (
        "app.services.indicators.regime.final_regime_resolver",
        "final_regime_resolver",
    ),
    "flag_pennant": ("app.services.indicators.patterns.flag_pennant", "flag_pennant"),
    "gaps": ("app.services.indicators.structure.gaps", "gaps"),
    "garman_klass_volatility": (
        "app.services.indicators.volatility.garman_klass_volatility",
        "garman_klass_volatility",
    ),
    "get_capability_matrix": (
        "app.services.indicators.core.registry",
        "get_capability_matrix",
    ),
    "get_indicator": ("app.services.indicators.core.registry", "get_indicator"),
    "get_indicator_result_metadata": (
        "app.services.indicators.core.results",
        "get_indicator_result_metadata",
    ),
    "get_indicator_result_values": (
        "app.services.indicators.core.results",
        "get_indicator_result_values",
    ),
    "get_warmup_requirement": (
        "app.services.indicators.core.validation",
        "get_warmup_requirement",
    ),
    "head_and_shoulders": (
        "app.services.indicators.patterns.head_and_shoulders",
        "head_and_shoulders",
    ),
    "hull_ma": ("app.services.indicators.trend.hull_ma", "hull_ma"),
    "hurst_regime": ("app.services.indicators.regime.hurst_regime", "hurst_regime"),
    "inside_bar": ("app.services.indicators.patterns.inside_bar", "inside_bar"),
    "join_indicator_result": (
        "app.services.indicators.core.results",
        "join_indicator_result",
    ),
    "level_clustering": (
        "app.services.indicators.structure.level_clustering",
        "level_clustering",
    ),
    "linear_regression_trend": (
        "app.services.indicators.trend.linear_regression_trend",
        "linear_regression_trend",
    ),
    "list_indicators": ("app.services.indicators.core.registry", "list_indicators"),
    "macd": ("app.services.indicators.trend.macd", "macd"),
    "market_event_arrival_rate": (
        "app.services.indicators.market_speed.market_event_arrival_rate",
        "market_event_arrival_rate",
    ),
    "measure_market_speed": (
        "app.services.indicators.volatility.market_speed",
        "measure_market_speed",
    ),
    "measure_order_flow": (
        "app.services.indicators.volume.order_flow",
        "measure_order_flow",
    ),
    "measure_trend_strength": (
        "app.services.indicators.trend.strength",
        "measure_trend_strength",
    ),
    "measure_volatility_envelope": (
        "app.services.indicators.volatility.envelope",
        "measure_volatility_envelope",
    ),
    "mfi": ("app.services.indicators.volume.mfi", "mfi"),
    "momentum_acceleration": (
        "app.services.indicators.market_speed.momentum_acceleration",
        "momentum_acceleration",
    ),
    "obv": ("app.services.indicators.volume.obv", "obv"),
    "parkinson_volatility": (
        "app.services.indicators.volatility.parkinson_volatility",
        "parkinson_volatility",
    ),
    "parse_indicator_snapshot": (
        "app.services.indicators.snapshots",
        "parse_indicator_snapshot",
    ),
    "parse_liquidity_snapshot": (
        "app.services.indicators.volume.liquidity_snapshot",
        "parse_liquidity_snapshot",
    ),
    "pinbar": ("app.services.indicators.patterns.pinbar", "pinbar"),
    "pivot_points": ("app.services.indicators.structure.pivot_points", "pivot_points"),
    "pivots": ("app.services.indicators.structure.pivots", "pivots"),
    "price_velocity": (
        "app.services.indicators.market_speed.price_velocity",
        "price_velocity",
    ),
    "price_volume_distribution": (
        "app.services.indicators.volume.price_volume_distribution",
        "price_volume_distribution",
    ),
    "project_market_overlay": (
        "app.services.indicators.volatility.market_projection",
        "project_market_overlay",
    ),
    "project_structural_levels": (
        "app.services.indicators.trend.structural_levels",
        "project_structural_levels",
    ),
    "rectangle": ("app.services.indicators.patterns.rectangle", "rectangle"),
    "rogers_satchell_volatility": (
        "app.services.indicators.volatility.rogers_satchell_volatility",
        "rogers_satchell_volatility",
    ),
    "rolling_volatility": (
        "app.services.indicators.volatility.rolling_volatility",
        "rolling_volatility",
    ),
    "rsi": ("app.services.indicators.momentum.rsi", "rsi"),
    "run_indicators_migrations": (
        "app.services.indicators.migrations.definitions",
        "run_indicators_migrations",
    ),
    "sma": ("app.services.indicators.trend.sma", "sma"),
    "standard_deviation": (
        "app.services.indicators.volatility.standard_deviation",
        "standard_deviation",
    ),
    "supertrend": ("app.services.indicators.trend.supertrend", "supertrend"),
    "three_bar_reversal": (
        "app.services.indicators.patterns.three_bar_reversal",
        "three_bar_reversal",
    ),
    "triangle": ("app.services.indicators.patterns.triangle", "triangle"),
    "validate_indicator": (
        "app.services.indicators.core.validation",
        "validate_indicator",
    ),
    "volatility_expansion_rate": (
        "app.services.indicators.market_speed.volatility_expansion_rate",
        "volatility_expansion_rate",
    ),
    "volatility_liquidity_stress_regime": (
        "app.services.indicators.regime.volatility_liquidity_stress_regime",
        "volatility_liquidity_stress_regime",
    ),
    "volatility_of_volatility": (
        "app.services.indicators.volatility.volatility_of_volatility",
        "volatility_of_volatility",
    ),
    "volatility_percentile": (
        "app.services.indicators.volatility.volatility_percentile",
        "volatility_percentile",
    ),
    "volume_acceleration": (
        "app.services.indicators.market_speed.volume_acceleration",
        "volume_acceleration",
    ),
    "volume_profile": (
        "app.services.indicators.structure.volume_profile",
        "volume_profile",
    ),
    "wedge": ("app.services.indicators.patterns.wedge", "wedge"),
    "williams_r": ("app.services.indicators.momentum.williams_r", "williams_r"),
    "wma": ("app.services.indicators.trend.wma", "wma"),
    "zigzag": ("app.services.indicators.trend.zigzag", "zigzag"),
}


def __getattr__(name: str) -> object:
    """Resolve one public export on first access.

    Args:
        name: Public export name.

    Returns:
        The resolved public function.

    Raises:
        AttributeError: If the name is not part of the public boundary.
    """
    target = _EXPORTS.get(name)
    if target is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    from importlib import import_module

    return getattr(import_module(target[0]), target[1])


def __dir__() -> list[str]:
    """List the public export surface.

    Returns:
        Sorted public export names.
    """
    return sorted(_EXPORTS)


__all__ = (
    "adr",
    "adx",
    "adx_dmi_regime",
    "aggressive_trade_imbalance",
    "amihud_illiquidity",
    "anchored_vwap",
    "aroon",
    "assert_closed_input",
    "atr",
    "atr_percent",
    "bollinger_bands",
    "bollinger_bandwidth",
    "breakout_retest",
    "build_chart_pattern_evidence",
    "build_indicator_config",
    "build_indicator_snapshot",
    "build_liquidity_snapshot",
    "choppiness_regime",
    "cmf",
    "composite_market_speed_gauge",
    "cumulative_volume_delta",
    "doji",
    "donchian_breakout_regime",
    "donchian_channels",
    "double_top_bottom",
    "ema",
    "ema_slope",
    "engulfing",
    "ewma_volatility",
    "final_regime_resolver",
    "flag_pennant",
    "gaps",
    "garman_klass_volatility",
    "get_capability_matrix",
    "get_indicator",
    "get_indicator_result_metadata",
    "get_indicator_result_values",
    "get_warmup_requirement",
    "head_and_shoulders",
    "hull_ma",
    "hurst_regime",
    "inside_bar",
    "join_indicator_result",
    "level_clustering",
    "linear_regression_trend",
    "list_indicators",
    "macd",
    "market_event_arrival_rate",
    "measure_market_speed",
    "measure_order_flow",
    "measure_trend_strength",
    "measure_volatility_envelope",
    "mfi",
    "momentum_acceleration",
    "obv",
    "parkinson_volatility",
    "parse_indicator_snapshot",
    "parse_liquidity_snapshot",
    "pinbar",
    "pivot_points",
    "pivots",
    "price_velocity",
    "price_volume_distribution",
    "project_market_overlay",
    "project_structural_levels",
    "rectangle",
    "rogers_satchell_volatility",
    "rolling_volatility",
    "rsi",
    "run_indicators_migrations",
    "sma",
    "standard_deviation",
    "supertrend",
    "three_bar_reversal",
    "triangle",
    "validate_indicator",
    "volatility_expansion_rate",
    "volatility_liquidity_stress_regime",
    "volatility_of_volatility",
    "volatility_percentile",
    "volume_acceleration",
    "volume_profile",
    "wedge",
    "williams_r",
    "wma",
    "zigzag",
)
