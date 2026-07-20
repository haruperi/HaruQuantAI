"""Pydantic models for simulator API routes.

Purpose:
    Pydantic models for simulator API routes.

Classes:
    SimulationStartRequest: Public class defined by this module.
    SimulationUpdateRequest: Public class defined by this module.
    ManualTradeRequest: Public class defined by this module.
    PendingOrderRequest: Public class defined by this module.
    PositionModifyRequest: Public class defined by this module.
    OrderModifyRequest: Public class defined by this module.
    SeekRequest: Public class defined by this module.
    AdvanceRequest: Public class defined by this module.
    WhatIfActionRequest: Public class defined by this module.
    WhatIfRequest: Public class defined by this module.
    SeekTradeRequest: Public class defined by this module.

Functions:
    None.

Notes:
    External-facing exports are collected in the owning package __init__.py.
    private underscore helpers remain implementation details unless preserved for API compatibility.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SimulationStartRequest(BaseModel):
    """Request to start a simulation session."""

    session_name: str | None = None
    symbol: str
    timeframe: str = "M1"
    range_by: str | None = "bars"
    start_time: str | None = None
    end_time: str | None = None
    number_of_bars: int | None = None
    warmup_by: str | None = "date"
    warmup_start_date: str | None = None
    warmup_bars: int | None = None
    initial_balance: float = 10000.0
    speed_multiplier: float = 1.0
    commission: float = 7.0
    leverage: int = 400
    slippage_type: str = "fixed"
    slippage: float = 0.0
    slippage_min: float = 0.0
    slippage_max: float = 10.0
    spread_type: str = "use-broker"
    spread: float = 20.0
    spread_min: float = 10.0
    spread_max: float = 50.0
    data_source: str | None = "mt5"
    data_resolution: str = "trading_timeframe"
    position_sizing_method: str | None = "fixed_lot"
    lot_size: float = 0.1
    risk_percent: float = 1.0
    base_lot_size: float = 0.1
    milestone_amount: float = 3000.0
    lot_increment: float = 0.2
    kelly_fraction_limit: float = 0.25
    fraction: float = 2.0
    fractional_factor: float = 2.0
    use_dynamic_stop_loss: bool = False
    atr_multiplier: float = 2.0
    win_rate: float = 0.55
    avg_win: float = 150.0
    avg_loss: float = 100.0
    risk_confidence_level: float = 0.95
    risk_horizon_unit: str = "days"
    risk_horizon_value: int = 1
    risk_vol_lookback: int = 20
    risk_corr_lookback: int = 60
    risk_var_cap_frac: float = 0.10
    risk_es_cap_frac: float = 0.15
    risk_delta_var_cap_frac: float = 0.02
    risk_delta_es_cap_frac: float = 0.03
    risk_max_margin_used_frac: float = 0.50
    risk_max_currency_exposure_frac: float = 0.20
    risk_max_single_rc_frac: float = 0.10
    risk_warning_utilization_frac: float = 0.90
    risk_limits_enforced: bool = True
    mode: str = Field(default="manual", description="manual | strategy | replay")
    strategy_id: int | None = None
    strategy_version_id: int | None = None
    strategy_params: dict[str, Any] | None = None
    replay_source: str | None = None
    replay_backtest_id: int | None = None
    replay_file_name: str | None = None
    alias: str | None = None
    description: str | None = None
    sma_period: int | None = 14
    ema_period: int | None = 14
    rsi_period: int | None = 14
    indicators_enabled: bool = False
    indicator_sma_enabled: bool = False
    indicator_ema_enabled: bool = False
    indicator_rsi_enabled: bool = False


class SimulationUpdateRequest(BaseModel):
    """Request to update a simulation session."""

    speed_multiplier: float | None = None
    paused: bool | None = None
    indicators_enabled: bool | None = None
    indicator_sma_enabled: bool | None = None
    indicator_ema_enabled: bool | None = None
    indicator_rsi_enabled: bool | None = None


class ManualTradeRequest(BaseModel):
    """Request to execute a manual trade."""

    symbol: str | None = None
    side: str = Field(..., description="buy | sell")
    volume: float = 0.1
    price: float | None = None
    sl: float | None = None
    tp: float | None = None
    comment: str | None = None
    manual_review_accepted: bool = False


class PendingOrderRequest(BaseModel):
    """Request to place a pending order."""

    symbol: str | None = None
    type: str = Field(
        ...,
        description="buy_limit | sell_limit | buy_stop | sell_stop | buy_stop_limit | sell_stop_limit",
    )
    volume: float
    price: float
    sl: float | None = None
    tp: float | None = None
    comment: str | None = None
    expiry_date: str | None = None
    expiration_mode: str | None = "gtc"


class PositionModifyRequest(BaseModel):
    """Request to modify a position."""

    sl: float | None = None
    tp: float | None = None


class OrderModifyRequest(BaseModel):
    """Request to modify a pending order."""

    volume: float | None = None
    price: float | None = None
    sl: float | None = None
    tp: float | None = None


class SeekRequest(BaseModel):
    """Request to seek to a bar index."""

    bar_index: int | None = None
    target_time: str | None = None


class AdvanceRequest(BaseModel):
    """Request to advance by N synchronized simulator frames."""

    count: int = 1


class WhatIfActionRequest(BaseModel):
    """One hypothetical non-mutating portfolio action."""

    action_type: str
    symbol: str
    delta_lots: float | None = None
    target_lots: float | None = None
    rationale: str | None = None


class WhatIfRequest(BaseModel):
    """Request to evaluate a what-if scenario against the current simulator state."""

    actions: list[WhatIfActionRequest] = Field(default_factory=list)
    leverage_override: int | None = None


class SeekTradeRequest(BaseModel):
    """Request to seek to a specific trade index in replay mode."""

    trade_index: int
