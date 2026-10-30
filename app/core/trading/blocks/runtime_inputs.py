"""Explicit runtime input bindings for session profiles and instruments.

Binds session-derived profiles, instrument tick sizes, and evaluation-time
decision prices into BarData auxiliary inputs so that indicator compositions and
specialized signals execute with explicit configuration and zero silent guessing.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np

from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.include.blocks.indicators.volume.tpo_profile import TPOProfile
from app.include.blocks.indicators.volume.volume_profile import VolumeProfile


def resolve_decision_price(
    bars: BarData,
    *,
    decides_on_bar_close: bool = True,
    bid: float | Sequence[float] | np.ndarray[Any, Any] | None = None,
    ask: float | Sequence[float] | np.ndarray[Any, Any] | None = None,
) -> np.ndarray[Any, Any]:
    """Resolve the decision price series for strategy evaluation.

    If decides_on_bar_close is True, the decision price is the completed bar close.
    If False, an explicit bid (or ask) quote series or scalar must be supplied.
    """
    count = len(bars.prices)
    if decides_on_bar_close:
        bars.require_inputs(("close",))
        return np.asarray(bars.close, dtype=np.float64)

    quote = bid if bid is not None else ask
    if quote is None:
        raise ValueError(
            "Intra-bar decision price requires an explicitly supplied bid or ask quote"
        )

    if isinstance(quote, (int, float)):
        if not math.isfinite(quote) or quote <= 0:
            raise ValueError("Quote price must be finite and positive")
        return np.full(count, float(quote), dtype=np.float64)

    arr = np.asarray(quote, dtype=np.float64)
    if arr.ndim != 1 or len(arr) != count:
        raise ValueError(
            f"Quote series length ({len(arr)}) must match bar count ({count})"
        )
    return arr


def bind_profile_signals(
    bars: BarData,
    *,
    volume_profile: VolumeProfile | None = None,
    tpo_profile: TPOProfile | None = None,
    threshold: float = 0.0,
) -> BarData:
    """Calculate session profiles and bind all expected feeds into BarData.auxiliary.

    Maps all Point of Control, Value Area High/Low, Bull/Bear POCs, and delta
    series directly to the canonical external field names expected by catalog signals.
    """
    auxiliary = dict(bars.auxiliary)

    if volume_profile is not None:
        vp_result = volume_profile.calculate(bars)
        for port in (
            "poc",
            "vah",
            "val",
            "bull_poc",
            "bear_poc",
            "delta",
            "poc_pct_down",
            "poc_pct_up",
        ):
            auxiliary[f"vp_{port}"] = vp_result[port].values
        auxiliary["vp_session_vah"] = vp_result["vah"].values
        auxiliary["vp_session_val"] = vp_result["val"].values
        auxiliary["vp_session_open_prices"] = np.asarray(bars.open, dtype=np.float64)
        auxiliary["vp_session_poc_pct_down"] = vp_result["poc_pct_down"].values
        auxiliary["vp_session_poc_pct_up"] = vp_result["poc_pct_up"].values
        auxiliary["vp_session_threshold"] = np.full(
            len(bars.prices), float(threshold), dtype=np.float64
        )

        for session in ("london", "new_york", "sydney", "tokyo"):
            for port in ("poc", "vah", "val"):
                name = f"{session}_{port}"
                if name in vp_result:
                    auxiliary[f"vp_{name}"] = vp_result[name].values

    if tpo_profile is not None:
        tpo_result = tpo_profile.calculate(bars)
        for port in (
            "poc",
            "vah",
            "val",
            "single_prints",
            "poor_high",
            "poor_low",
        ):
            auxiliary[f"tpo_{port}"] = tpo_result[port].values

    return _reconstruct_bars(bars, auxiliary)


def _reconstruct_bars(
    bars: BarData, auxiliary: dict[str, np.ndarray[Any, Any]]
) -> BarData:
    avail = (
        bars.available_inputs
        if bars.available_inputs is not None
        else {"open", "high", "low", "close", "volume"}
    )
    return BarData(
        prices=bars.prices,
        timestamps=bars.timestamps,
        symbol=bars.symbol,
        timeframe=bars.timeframe,
        dataset_revision=bars.dataset_revision,
        auxiliary=auxiliary,
        available_inputs=frozenset(avail | auxiliary.keys()),
    )


def _build_profile_instances(
    volume_profile: VolumeProfile | Mapping[str, Any] | None,
    tpo_profile: TPOProfile | Mapping[str, Any] | None,
    tick_size: float | None,
    timezone: str | None,
) -> tuple[VolumeProfile | None, TPOProfile | None]:
    vp: VolumeProfile | None = None
    if isinstance(volume_profile, VolumeProfile):
        vp = volume_profile
    elif isinstance(volume_profile, Mapping):
        cfg = dict(volume_profile)
        if tick_size is not None and "tick_size" not in cfg:
            cfg["tick_size"] = tick_size
        if timezone is not None and "timezone" not in cfg:
            cfg["timezone"] = timezone
        vp = VolumeProfile(**cfg)

    tpo: TPOProfile | None = None
    if isinstance(tpo_profile, TPOProfile):
        tpo = tpo_profile
    elif isinstance(tpo_profile, Mapping):
        cfg = dict(tpo_profile)
        if tick_size is not None and "tick_size" not in cfg:
            cfg["tick_size"] = tick_size
        if timezone is not None and "timezone" not in cfg:
            cfg["timezone"] = timezone
        tpo = TPOProfile(**cfg)

    return vp, tpo


def bind_runtime_inputs(
    bars: BarData,
    *,
    decides_on_bar_close: bool = True,
    bid: float | Sequence[float] | np.ndarray[Any, Any] | None = None,
    ask: float | Sequence[float] | np.ndarray[Any, Any] | None = None,
    tick_size: float | None = None,
    timezone: str | None = None,
    volume_profile: VolumeProfile | Mapping[str, Any] | None = None,
    tpo_profile: TPOProfile | Mapping[str, Any] | None = None,
    threshold: float = 0.0,
    extra_feeds: Mapping[str, Sequence[float] | np.ndarray[Any, Any]] | None = None,
) -> BarData:
    """Produce fully bound BarData with decision prices, profiles, and extra feeds."""
    decision_price = resolve_decision_price(
        bars,
        decides_on_bar_close=decides_on_bar_close,
        bid=bid,
        ask=ask,
    )
    aux = dict(bars.auxiliary)
    aux["decision_price"] = decision_price

    if extra_feeds:
        for name, values in extra_feeds.items():
            arr = np.asarray(values, dtype=np.float64)
            if len(arr) != len(bars.prices):
                raise ValueError(
                    f"Extra feed '{name}' length ({len(arr)}) must match bar count"
                )
            aux[name] = arr

    working_bars = _reconstruct_bars(bars, aux)
    vp_inst, tpo_inst = _build_profile_instances(
        volume_profile, tpo_profile, tick_size, timezone
    )

    if vp_inst is not None or tpo_inst is not None:
        working_bars = bind_profile_signals(
            working_bars,
            volume_profile=vp_inst,
            tpo_profile=tpo_inst,
            threshold=threshold,
        )

    return working_bars


def execute_bound_signal(
    descriptor: Any,
    bars: BarData,
    **kwargs: Any,
) -> Any:
    """Execute a catalog signal descriptor against bound BarData."""
    if descriptor.input_bindings:
        args: dict[str, Any] = {}
        for param_name, b_info in descriptor.input_bindings.items():
            field_name = b_info["field"]
            raw_data = (
                bars.input(field_name, required=True)
                if b_info.get("kind") == "external"
                else getattr(bars, field_name)
            )
            if raw_data is None:
                raise ValueError(f"Missing input feed: {field_name}")
            series_data = np.asarray(raw_data, dtype=np.float64)
            args[param_name] = (
                IndicatorSeries(series_data, name=field_name)
                if not isinstance(raw_data, IndicatorSeries)
                else raw_data
            )
        target_fn = descriptor.instantiate(**kwargs)
        return target_fn(**args)
    return descriptor.target(bars, **kwargs)


def schedule_calendar_session(
    epoch_ms: int,
    session_type: int,
    timezone: str = "UTC",
    custom: tuple[int, int] | None = None,
) -> tuple[datetime, datetime]:
    """Calculate session start and end datetimes in chart timezone."""
    from app.include.calculators.profile_sessions import session_bounds

    zone = ZoneInfo(timezone)
    kind = (session_type - 1) % 4 + 1
    start_ms, end_ms = session_bounds(epoch_ms, kind, zone, custom)
    start_dt = datetime.fromtimestamp(start_ms / 1000, UTC).astimezone(zone)
    end_dt = datetime.fromtimestamp(end_ms / 1000, UTC).astimezone(zone)
    return start_dt, end_dt


__all__ = [
    "bind_profile_signals",
    "bind_runtime_inputs",
    "execute_bound_signal",
    "resolve_decision_price",
    "schedule_calendar_session",
]
