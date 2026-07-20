# ruff: noqa: PLR2004
"""Drawdown governor engine.

Calculates total, daily, and strategy-level drawdowns, manages state transitions,
persists throttling states, and checks for revenge/catch-up risk behavior. Also
exposes a pure, canonically-typed V2 calculation surface
(:func:`determine_drawdown_state`, :func:`calculate_drawdown_multiplier`) and a
dual-dispatch :func:`apply_drawdown_throttle` that accepts either the original
V1 ``PortfolioState``/``market_context`` calling convention or the canonical
V2 ``size``/``DrawdownState``/``EffectiveRiskPolicy`` convention.
"""

from __future__ import annotations

import json
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any, overload

from app.services.risk.errors import RiskValidationError as ValidationError
from app.services.risk.limits import LimitResult
from app.services.risk.models import (
    DrawdownState,
    PortfolioRiskSnapshot,
    PortfolioState,
    ProposedTrade,
    RiskConfig,
    RiskDecisionStatus,
    RiskReasonCode,
    RiskSeverity,
)
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.risk.policy.contracts import EffectiveRiskPolicy


class RiskStepDownState(StrEnum):
    """Drawdown-based throttling categories/states."""

    NORMAL = "normal"
    CAUTION = "caution"
    DEFENSIVE = "defensive"
    RECOVERY_ONLY = "recovery_only"
    HALTED = "halted"


DrawdownThrottlingState = RiskStepDownState


def calculate_daily_drawdown(
    portfolio_state: PortfolioState, daily_start_balance: Decimal
) -> Decimal:
    """Calculate daily drawdown percentage.

    Based on daily starting balance and current equity.

    Args:
        portfolio_state: Current portfolio state.
        daily_start_balance: Portfolio balance at the start of the day.

    Returns:
        Decimal daily drawdown percentage.
    """
    if daily_start_balance <= Decimal("0.0"):
        logger.debug("Daily start balance is non-positive; daily drawdown is 0.")
        return Decimal("0.0")
    drawdown = max(
        Decimal("0.0"),
        (daily_start_balance - portfolio_state.equity) / daily_start_balance,
    )
    logger.info(f"Calculated daily drawdown: {drawdown:.4f}.")
    return drawdown


def calculate_total_drawdown(
    portfolio_state: PortfolioState, peak_balance: Decimal
) -> Decimal:
    """Calculate total account drawdown percentage from lifetime peak balance.

    Args:
        portfolio_state: Current portfolio state.
        peak_balance: Historic maximum balance/equity peak.

    Returns:
        Decimal total drawdown percentage.
    """
    if peak_balance <= Decimal("0.0"):
        logger.debug("Peak balance is non-positive; total drawdown is 0.")
        return Decimal("0.0")
    drawdown = max(
        Decimal("0.0"), (peak_balance - portfolio_state.equity) / peak_balance
    )
    logger.info(f"Calculated total drawdown: {drawdown:.4f}.")
    return drawdown


def calculate_strategy_drawdown(
    strategy_id: str,
    portfolio_state: PortfolioState,
    strategy_peak_equity: Decimal,
) -> Decimal:
    """Calculate drawdown for a specific strategy's allocated capital.

    Args:
        strategy_id: Identifier of the strategy.
        portfolio_state: Current portfolio state.
        strategy_peak_equity: Peak equity allocated or realized by this strategy.

    Returns:
        Decimal strategy drawdown percentage.
    """
    allocation = portfolio_state.strategy_allocations.get(strategy_id, Decimal("0.0"))
    strat_pnl = sum(
        pos.floating_pnl
        for pos in portfolio_state.positions
        if pos.strategy_id == strategy_id
    )
    current_strat_equity = allocation + strat_pnl

    if strategy_peak_equity <= Decimal("0.0"):
        logger.debug(f"Strategy '{strategy_id}' peak equity is non-positive.")
        return Decimal("0.0")
    drawdown = max(
        Decimal("0.0"),
        (strategy_peak_equity - current_strat_equity) / strategy_peak_equity,
    )
    logger.info(f"Calculated strategy '{strategy_id}' drawdown: {drawdown:.4f}.")
    return drawdown


def determine_drawdown_throttling(
    drawdown: Decimal, soft_limit: Decimal, hard_limit: Decimal
) -> tuple[DrawdownThrottlingState, Decimal]:
    """Map a drawdown level to a throttling category and risk scale multiplier.

    Args:
        drawdown: Current drawdown percentage.
        soft_limit: Soft drawdown advisory threshold.
        hard_limit: Hard drawdown halt threshold.

    Returns:
        tuple containing (DrawdownThrottlingState, multiplier)
    """
    if drawdown >= hard_limit:
        logger.info(f"Drawdown {drawdown:.4f} halted (>= hard limit {hard_limit}).")
        return DrawdownThrottlingState.HALTED, Decimal("0.0")

    if drawdown >= hard_limit * Decimal("0.8"):
        logger.info(f"Drawdown {drawdown:.4f} in recovery-only state.")
        return DrawdownThrottlingState.RECOVERY_ONLY, Decimal("0.2")

    if drawdown >= soft_limit:
        logger.info(f"Drawdown {drawdown:.4f} in defensive state.")
        return DrawdownThrottlingState.DEFENSIVE, Decimal("0.5")

    if drawdown >= soft_limit * Decimal("0.5"):
        logger.info(f"Drawdown {drawdown:.4f} in caution state.")
        return DrawdownThrottlingState.CAUTION, Decimal("0.8")

    logger.info(f"Drawdown {drawdown:.4f} is normal.")
    return DrawdownThrottlingState.NORMAL, Decimal("1.0")


def persist_drawdown_state(state: DrawdownState, file_path: str | Path) -> None:
    """Serialize and write DrawdownState to a JSON file.

    Args:
        state: Active DrawdownState model.
        file_path: Output target path.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(state.to_json())
    logger.info(f"Persisted drawdown state to {path}.")


def restore_drawdown_state(file_path: str | Path) -> DrawdownState | None:
    """Restore and deserialize DrawdownState from a JSON file.

    Handles missing files and data corruption by returning None.

    Args:
        file_path: Input source path.

    Returns:
        DrawdownState or None if file does not exist or is corrupt.
    """
    path = Path(file_path)
    if not path.exists():
        logger.debug(f"Drawdown state file does not exist: {path}.")
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        required_keys = {"current_drawdown", "soft_limit", "hard_limit", "multiplier"}
        if not required_keys.issubset(data.keys()):
            logger.warning(
                "Corrupt drawdown state file: missing keys "
                f"{required_keys - data.keys()}"
            )
            return None

        state = DrawdownState(
            current_drawdown=Decimal(str(data["current_drawdown"])),
            soft_limit=Decimal(str(data["soft_limit"])),
            hard_limit=Decimal(str(data["hard_limit"])),
            multiplier=Decimal(str(data["multiplier"])),
        )
        logger.info(f"Restored drawdown state from {path}.")
        return state
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Failed to restore drawdown state from {file_path}: {e}")
        return None


def check_revenge_trading(
    proposed_trade: ProposedTrade | None,
    drawdown_state: DrawdownState,
    market_context: dict[str, Any],
    config: RiskConfig | None = None,
) -> tuple[bool, str]:
    """Check if the proposed trade constitutes catch-up or revenge risk behavior.

    Rejects proposed trades with lot volumes exceeding scaled average baseline
    when the portfolio is in a drawdown throttling state (multiplier < 1.0).

    Args:
        proposed_trade: Candidate proposed trade.
        drawdown_state: Active DrawdownState.
        market_context: Context containing historical volume metadata.
        config: Optional active risk config profile.

    Returns:
        tuple (revenge_detected: bool, reason_message: str)
    """
    if proposed_trade is None:
        logger.debug("No proposed trade; revenge trading check skipped.")
        return False, ""

    is_simulation = (
        market_context.get("mode") == "simulation"
        or market_context.get("environment") == "simulation"
    )
    allow_revenge = market_context.get("allow_revenge_trading") is True or (
        config is not None
        and config.experimental_features.get("allow_revenge_trading") is True
    )
    if is_simulation and allow_revenge:
        logger.debug("Revenge trading check bypassed under simulation policy.")
        return False, ""

    if drawdown_state.multiplier >= Decimal("1.0"):
        return False, ""

    symbol = proposed_trade.symbol
    avg_vol_raw = market_context.get(
        f"{symbol}_historical_avg_volume"
    ) or market_context.get("historical_avg_volume")
    if avg_vol_raw is None:
        logger.debug(f"No historical average volume metadata for {symbol}.")
        return False, ""

    avg_vol = Decimal(str(avg_vol_raw))
    max_allowed_vol = avg_vol * drawdown_state.multiplier

    if proposed_trade.volume > max_allowed_vol:
        msg = (
            f"Revenge trading detected: proposed volume {proposed_trade.volume} lots "
            f"exceeds maximum allowed drawdown-scaled volume of {max_allowed_vol} lots "
            f"(historical average: {avg_vol} lots, "
            f"multiplier: {drawdown_state.multiplier})."
        )
        logger.info(msg)
        return True, msg
    return False, ""


def _check_reset_approval(market_context: dict[str, Any]) -> LimitResult | None:
    """Check if drawdown reset is requested and operator token is valid."""
    is_reset = (
        market_context.get("reset_drawdown") is True
        or market_context.get("reset_drawdown_state") is True
    )
    if is_reset and not (
        market_context.get("approval_token_valid")
        or market_context.get("approval_token")
    ):
        logger.info("Drawdown reset requested without a valid approval token.")
        return LimitResult(
            limit_name="max_drawdown_limit",
            status=RiskDecisionStatus.BLOCK,
            reason_code=RiskReasonCode.APPROVAL_REQUIRED,
            message="Drawdown reset requires operator approval token.",
            severity=RiskSeverity.HARD_BREACH,
            breached=True,
        )
    return None


def _check_daily_loss(
    portfolio_state: PortfolioState,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult | None:
    """Check if daily drawdown limit is reached."""
    daily_start_raw = market_context.get("daily_start_balance")
    if daily_start_raw is not None:
        daily_start_balance = Decimal(str(daily_start_raw))
        daily_dd = calculate_daily_drawdown(portfolio_state, daily_start_balance)
        if daily_dd >= config.max_daily_loss_pct:
            logger.info(f"Daily hard loss limit breached: {daily_dd:.2%}.")
            return LimitResult(
                limit_name="max_drawdown_limit",
                status=RiskDecisionStatus.BLOCK,
                reason_code=RiskReasonCode.DAILY_LOSS_BREACH,
                message=(
                    f"Daily hard loss limit breached: {daily_dd:.2%} >= "
                    f"{config.max_daily_loss_pct:.2%}."
                ),
                severity=RiskSeverity.CRITICAL_BREACH,
                breached=True,
            )
    return None


def _check_strategy_loss(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult | None:
    """Check if strategy-level drawdown limit is reached."""
    if proposed_trade is None:
        return None

    strategy_id = proposed_trade.strategy_id
    strat_peak_raw = market_context.get(f"{strategy_id}_peak_equity")
    if strat_peak_raw is not None:
        strat_peak = Decimal(str(strat_peak_raw))
    else:
        strat_peak = portfolio_state.strategy_allocations.get(
            strategy_id, Decimal("0.0")
        )

    max_strat_loss = Decimal(
        str(
            market_context.get("max_strategy_loss_pct")
            or config.experimental_features.get("max_strategy_loss_pct")
            or "0.04"
        )
    )
    if strat_peak > 0:
        strat_dd = calculate_strategy_drawdown(strategy_id, portfolio_state, strat_peak)
        if strat_dd >= max_strat_loss:
            logger.info(
                f"Strategy loss limit breached for '{strategy_id}': {strat_dd:.2%}."
            )
            return LimitResult(
                limit_name="max_drawdown_limit",
                status=RiskDecisionStatus.REJECT,
                reason_code=RiskReasonCode.DRAWDOWN_BREACH,
                message=(
                    f"Strategy loss limit breached for strategy '{strategy_id}': "
                    f"{strat_dd:.2%} >= {max_strat_loss:.2%}."
                ),
                severity=RiskSeverity.HARD_BREACH,
                breached=True,
            )
    return None


def _apply_drawdown_throttle_v1(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult:
    """Implement drawdown-aware risk throttling before hard loss limits are hit.

    Applies risk step-down multipliers as drawdown increases, checks
    strategy-level limits, daily hard loss limits, revenge trading
    behaviors, and reset approval requirements.
    """
    result = _check_reset_approval(market_context)

    if result is None:
        result = _check_daily_loss(portfolio_state, market_context, config)

    if result is None:
        result = _check_strategy_loss(
            portfolio_state, proposed_trade, market_context, config
        )

    if result is None:
        peak_balance_raw = market_context.get("peak_balance")
        if peak_balance_raw is None:
            peak_balance = portfolio_state.balance
        else:
            peak_balance = Decimal(str(peak_balance_raw))

        drawdown = calculate_total_drawdown(portfolio_state, peak_balance)
        soft_limit = config.max_total_loss_pct_advisory
        hard_limit = config.max_total_loss_pct

        throttling_state, multiplier = determine_drawdown_throttling(
            drawdown, soft_limit, hard_limit
        )

        state = DrawdownState(
            current_drawdown=drawdown,
            soft_limit=soft_limit,
            hard_limit=hard_limit,
            multiplier=multiplier,
        )

        if throttling_state == DrawdownThrottlingState.HALTED:
            logger.info(f"Total drawdown halt threshold breached: {drawdown:.2%}.")
            result = LimitResult(
                limit_name="max_drawdown_limit",
                status=RiskDecisionStatus.BLOCK,
                reason_code=RiskReasonCode.DRAWDOWN_BREACH,
                message=(
                    f"Total drawdown halt threshold breached: {drawdown:.2%} >= "
                    f"{hard_limit:.2%}."
                ),
                severity=RiskSeverity.CRITICAL_BREACH,
                breached=True,
                details=state.model_dump(),
            )
        else:
            is_revenge, revenge_msg = check_revenge_trading(
                proposed_trade, state, market_context, config
            )
            if is_revenge:
                result = LimitResult(
                    limit_name="max_drawdown_limit",
                    status=RiskDecisionStatus.REJECT,
                    reason_code=RiskReasonCode.DRAWDOWN_BREACH,
                    message=revenge_msg,
                    severity=RiskSeverity.HARD_BREACH,
                    breached=True,
                    details=state.model_dump(),
                )
            elif throttling_state in {
                DrawdownThrottlingState.CAUTION,
                DrawdownThrottlingState.DEFENSIVE,
                DrawdownThrottlingState.RECOVERY_ONLY,
            }:
                logger.info(
                    f"Drawdown throttling active ({throttling_state.value}): "
                    f"multiplier {multiplier}."
                )
                result = LimitResult(
                    limit_name="max_drawdown_limit",
                    status=RiskDecisionStatus.REDUCE_SIZE,
                    reason_code=RiskReasonCode.DRAWDOWN_BREACH,
                    message=(
                        f"Drawdown throttling active ({throttling_state.value}): "
                        f"risk sizing multiplier of {multiplier} enforced."
                    ),
                    severity=RiskSeverity.SOFT_BREACH,
                    breached=False,
                    details=state.model_dump(),
                )
            else:
                result = LimitResult(
                    limit_name="max_drawdown_limit",
                    status=RiskDecisionStatus.APPROVE,
                    reason_code=RiskReasonCode.OK,
                    message="Total drawdown is within safe limits.",
                    severity=RiskSeverity.INFO,
                    breached=False,
                    details=state.model_dump(),
                )

    return result


def verify_drawdown_limits(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult:
    """Enforce total drawdown limits and check for revenge trading behavior.

    Delegates check sequence directly to apply_drawdown_throttle.

    Args:
        portfolio_state: Current portfolio snapshot.
        proposed_trade: Optional candidate proposed trade.
        market_context: Market details.
        config: Active risk configuration.

    Returns:
        LimitResult: Outcome of the drawdown-aware throttling sequence.
    """
    logger.info("Verifying drawdown limits via throttle sequence.")
    return _apply_drawdown_throttle_v1(
        portfolio_state, proposed_trade, market_context, config
    )


def determine_drawdown_state(
    snapshot: PortfolioRiskSnapshot,
    prior: DrawdownState | None,
    policy: EffectiveRiskPolicy,
) -> DrawdownState:
    """Classify normal/caution/defensive/recovery/halted drawdown state.

    Args:
        snapshot: Canonical portfolio-level risk snapshot carrying the
            current drawdown percentage.
        prior: Optional previously persisted drawdown state (unused for
            classification, retained for auditability of state transitions).
        policy: Resolved effective risk policy providing soft/hard limits.

    Returns:
        DrawdownState: Classified drawdown state with applied multiplier.
    """
    logger.info("Determining canonical drawdown state from portfolio snapshot.")
    config = policy.resolved_config
    soft_limit = config.max_total_loss_pct_advisory
    hard_limit = config.max_total_loss_pct
    drawdown = snapshot.drawdown

    _, multiplier = determine_drawdown_throttling(drawdown, soft_limit, hard_limit)
    logger.debug(
        f"Canonical drawdown state resolved: drawdown={drawdown}, "
        f"multiplier={multiplier}, prior_present={prior is not None}."
    )

    return DrawdownState(
        current_drawdown=drawdown,
        soft_limit=soft_limit,
        hard_limit=hard_limit,
        multiplier=multiplier,
    )


def calculate_drawdown_multiplier(
    state: DrawdownState, policy: EffectiveRiskPolicy
) -> Decimal:
    """Return the approved risk step-down multiplier for a drawdown state.

    Args:
        state: Classified drawdown state.
        policy: Resolved effective risk policy (retained for interface
            symmetry; the multiplier is already embedded in `state`).

    Returns:
        Decimal: The risk-scaling multiplier to apply to proposed sizing.
    """
    logger.info(f"Resolving drawdown multiplier: {state.multiplier}.")
    _ = policy
    return state.multiplier


@overload
def apply_drawdown_throttle(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
) -> LimitResult: ...


@overload
def apply_drawdown_throttle(
    size: Decimal,
    state: DrawdownState,
    policy: EffectiveRiskPolicy,
) -> Decimal: ...


def apply_drawdown_throttle(*args: Any, **kwargs: Any) -> Any:
    """Apply drawdown-aware risk throttling, supporting V1 and V2 signatures.

    Args:
        *args: Positional arguments. For V2, the arguments are
            (size: Decimal, state: DrawdownState, policy: EffectiveRiskPolicy).
            For V1, the arguments are
            (portfolio_state: PortfolioState, proposed_trade: ProposedTrade | None,
            market_context: dict[str, Any], config: RiskConfig).
        **kwargs: Keyword arguments mirroring the positional forms above.

    Returns:
        Decimal | LimitResult: For V2, the throttled size. For V1, the
            aggregated LimitResult of the throttling sequence.
    """
    logger.info("apply_drawdown_throttle entry.")

    is_v2 = ("size" in kwargs and isinstance(kwargs["size"], Decimal)) or (
        len(args) > 0 and isinstance(args[0], Decimal)
    )

    if is_v2:
        size: Any = kwargs.get("size", args[0] if len(args) > 0 else None)
        state: Any = kwargs.get("state", args[1] if len(args) > 1 else None)
        policy: Any = kwargs.get("policy", args[2] if len(args) > 2 else None)
        max_size_cap = policy.resolved_config.max_risk_per_trade
        reduced = size * state.multiplier
        if max_size_cap > Decimal("0.0"):
            reduced = min(reduced, size)
        logger.debug(
            f"V2 drawdown throttle applied: size={size}, "
            f"multiplier={state.multiplier} -> {reduced}."
        )
        return reduced

    portfolio_state: Any = kwargs.get(
        "portfolio_state", args[0] if len(args) > 0 else None
    )
    proposed_trade: Any = kwargs.get(
        "proposed_trade", args[1] if len(args) > 1 else None
    )
    market_context: Any = kwargs.get(
        "market_context", args[2] if len(args) > 2 else None
    )
    config: Any = kwargs.get("config", args[3] if len(args) > 3 else None)

    return _apply_drawdown_throttle_v1(
        portfolio_state, proposed_trade, market_context, config
    )


class DrawdownGovernor:
    """Orchestrator for managing portfolio and strategy drawdowns.

    Throttles risk based on step-down thresholds and multipliers.
    """

    def __init__(self, config: RiskConfig | None = None) -> None:
        """Initialize with optional active configuration profile.

        Args:
            config: Optional active risk config profile.
        """
        self.config = config
        logger.debug("DrawdownGovernor initialized.")

    def calculate_daily_drawdown(
        self, portfolio_state: PortfolioState, daily_start_balance: Decimal
    ) -> Decimal:
        """Calculate daily drawdown percentage."""
        return calculate_daily_drawdown(portfolio_state, daily_start_balance)

    def calculate_total_drawdown(
        self, portfolio_state: PortfolioState, peak_balance: Decimal
    ) -> Decimal:
        """Calculate total account drawdown percentage."""
        return calculate_total_drawdown(portfolio_state, peak_balance)

    def calculate_strategy_drawdown(
        self,
        strategy_id: str,
        portfolio_state: PortfolioState,
        strategy_peak_equity: Decimal,
    ) -> Decimal:
        """Calculate drawdown for a specific strategy's allocated capital."""
        return calculate_strategy_drawdown(
            strategy_id, portfolio_state, strategy_peak_equity
        )

    def determine_drawdown_throttling(
        self, drawdown: Decimal, soft_limit: Decimal, hard_limit: Decimal
    ) -> tuple[RiskStepDownState, Decimal]:
        """Map a drawdown level to a throttling category and multiplier."""
        return determine_drawdown_throttling(drawdown, soft_limit, hard_limit)

    def apply_drawdown_throttle(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        market_context: dict[str, Any],
        config: RiskConfig | None = None,
    ) -> LimitResult:
        """Implement drawdown-aware risk throttling before hard loss limits are hit."""
        active_config = config or self.config
        if active_config is None:
            msg = "DrawdownGovernor requires a RiskConfig to apply throttling."
            logger.error(msg)
            raise ValidationError(msg)
        return _apply_drawdown_throttle_v1(
            portfolio_state, proposed_trade, market_context, active_config
        )

    def persist_state(self, state: DrawdownState, file_path: str | Path) -> None:
        """Serialize and write DrawdownState to a JSON file."""
        persist_drawdown_state(state, file_path)

    def restore_state(self, file_path: str | Path) -> DrawdownState | None:
        """Restore and deserialize DrawdownState from a JSON file."""
        return restore_drawdown_state(file_path)
