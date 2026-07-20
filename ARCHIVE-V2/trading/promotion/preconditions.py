"""Pre-activation conditions and simulation route metadata lookup validations.

This module implements pre-activation checks for live mutation routes (TRD-FR-185)
and enforces restrictions on simulation route broker metadata lookups (TRD-FR-186).
"""

from __future__ import annotations

from app.services.trading.contracts import PromotionStage, TradingRoute
from app.services.trading.security.error_mapping import (
    TradingMappedError,
    TradingValidationError,
)
from app.utils.logger import logger


def validate_preactivation_conditions(
    *,
    route: TradingRoute,
    stage: PromotionStage,
    active_kill_switches: bool,
    reconciliation_blocked: bool,
    context_is_stale: bool,
    security_profile_missing: bool,
) -> None:
    """Validate pre-activation conditions for live routes (TRD-FR-185).

    Production live mutation (live route in micro_live or full_live stage) remains
    hard-blocked if active kill switches, unresolved reconciliation state,
    stale context, or missing security profiles exist.

    Args:
        route: Requested trading route.
        stage: Requested promotion stage.
        active_kill_switches: True if any global/strategy/symbol kill switch is active.
        reconciliation_blocked: True if reconciliation state is unresolved.
        context_is_stale: True if clock drift is too high or quote snapshot is stale.
        security_profile_missing: True if credentials or security profiles are missing.

    Raises:
        TradingMappedError: If any safety check fails for live mutation.
    """
    logger.info(
        "Validating preactivation conditions for route={}, stage={}.",
        route.value,
        stage.value,
    )

    is_live_mutation = route is TradingRoute.LIVE and stage in (
        PromotionStage.MICRO_LIVE,
        PromotionStage.FULL_LIVE,
    )

    if not is_live_mutation:
        logger.debug("Route/stage combination does not require live mutation checks.")
        return

    if active_kill_switches:
        logger.error("Live mutation blocked: active kill switch exists.")
        raise TradingMappedError(
            "Production live mutation is blocked by an active kill switch.",
            code="LIVE_KILL_SWITCH_ACTIVE",
        )

    if reconciliation_blocked:
        logger.error("Live mutation blocked: unresolved reconciliation state.")
        raise TradingMappedError(
            "Production live mutation is blocked: reconciliation state is unresolved.",
            code="LIVE_RECONCILIATION_REQUIRED",
        )

    if context_is_stale:
        logger.error("Live mutation blocked: stale context.")
        raise TradingMappedError(
            "Production live mutation is blocked: system context or quotes are stale.",
            code="LIVE_STALE_CONTEXT",
        )

    if security_profile_missing:
        logger.error("Live mutation blocked: missing security profile.")
        msg = (
            "Production live mutation is blocked: missing security credentials profile."
        )
        raise TradingMappedError(
            msg,
            code="CREDENTIALS_MISSING",
        )

    logger.info("Preactivation condition checks passed.")


def validate_sim_metadata_lookup(
    *,
    mode: str,
    has_captured_snapshot: bool,
) -> None:
    """Validate broker metadata lookups in the simulation route (TRD-FR-186).

    The simulation route may perform broker read-only metadata lookups only
    during configuration, calibration, explicitly enabled live-metadata simulation
    mode, or during a historical backtest that uses a captured metadata snapshot.

    Args:
        mode: The simulation execution context mode (e.g. 'configuration',
            'calibration', 'live_metadata_simulation', 'historical_backtest').
        has_captured_snapshot: True if a local, reproducible metadata snapshot
            is present.

    Raises:
        TradingValidationError: If the lookup is performed in an invalid context
            or violates backtest reproducibility rules.
    """
    logger.info(
        "Validating simulation metadata lookup context: mode={}, has_snapshot={}.",
        mode,
        has_captured_snapshot,
    )

    allowed_live_lookup_modes = (
        "configuration",
        "calibration",
        "live_metadata_simulation",
    )

    if mode == "historical_backtest":
        if not has_captured_snapshot:
            logger.error(
                "Historical backtest attempted metadata lookup "
                "without captured snapshot."
            )
            raise TradingValidationError(
                "Deterministic historical backtests must use captured metadata "
                "snapshots to preserve reproducibility."
            )
        logger.debug(
            "Metadata lookup allowed for historical backtest via captured snapshot."
        )
        return

    if mode not in allowed_live_lookup_modes:
        logger.error("Metadata lookup blocked: invalid context mode '{}'.", mode)
        msg = (
            f"Broker metadata lookup not permitted in simulation mode '{mode}'. "
            "Must be configuration, calibration, live_metadata_simulation, or "
            "historical_backtest with a valid snapshot."
        )
        raise TradingValidationError(msg)

    logger.info("Simulation metadata lookup validation passed.")
