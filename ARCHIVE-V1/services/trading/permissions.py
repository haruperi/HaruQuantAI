"""Runtime permission checks for strategy lifecycle state.

Purpose:
    Runtime permission checks for strategy lifecycle state.

Classes:
    StrategyPermissionError: Public class defined by this module.
    StrategyRuntimePermissionService: Public class defined by this module.

Functions:
    assert_strategy_allowed: Public function defined by this module.

Notes:
    External-facing exports are collected in package __init__.py files;
    private underscore helpers remain implementation details.
"""

from __future__ import annotations

from typing import Literal

from app.services.utils.logger import logger
from data.database import GovernanceRepository
from data.database.sqlite.database_operations import DatabaseManager

StrategyRuntimeContext = Literal[
    "backtest", "optimization", "paper", "live", "live_production"
]

_ALLOWED_STATES: dict[StrategyRuntimeContext, set[str]] = {
    "backtest": {
        "RESEARCH",
        "BACKTEST_QUALIFIED",
        "ROBUSTNESS_QUALIFIED",
        "PAPER_APPROVED",
        "LIVE_LIMITED",
        "LIVE_PRODUCTION",
    },
    "optimization": {
        "RESEARCH",
        "BACKTEST_QUALIFIED",
        "ROBUSTNESS_QUALIFIED",
        "PAPER_APPROVED",
        "LIVE_LIMITED",
        "LIVE_PRODUCTION",
    },
    "paper": {"PAPER_APPROVED", "LIVE_LIMITED", "LIVE_PRODUCTION"},
    "live": {"LIVE_LIMITED", "LIVE_PRODUCTION"},
    "live_production": {"LIVE_PRODUCTION"},
}


def _governance_strategy_id(user_id: int, strategy_id: int) -> str:
    """Build the canonical governance strategy identifier.

    Args:
        user_id: Owning user identifier.
        strategy_id: Local strategy identifier.

    Returns:
        str: Namespaced governance strategy identifier.
    """
    return f"strategy:{user_id}:{strategy_id}"


class StrategyPermissionError(PermissionError):
    """Raised when a strategy lifecycle state does not permit a runtime context."""


class StrategyRuntimePermissionService:
    """Authorize strategy execution contexts from governance lifecycle state."""

    def __init__(
        self,
        db_manager: DatabaseManager | None = None,
        governance_repository: GovernanceRepository | None = None,
    ) -> None:
        """Initialize the service with database and governance dependencies.

        Args:
            db_manager: Optional database manager; a default is created if None.
            governance_repository: Optional governance repository; a default
                bound to the database path is created if None.
        """
        self.db = db_manager or DatabaseManager()
        self.governance = governance_repository or GovernanceRepository(self.db.db_path)

    def assert_strategy_allowed(
        self,
        *,
        strategy_id: int,
        context: StrategyRuntimeContext,
    ) -> None:
        """Assert a strategy may run in the requested runtime context.

        Args:
            strategy_id: Local strategy identifier to authorize.
            context: Requested runtime context (e.g. 'live', 'paper').

        Raises:
            LookupError: If the strategy is not found.
            StrategyPermissionError: If the strategy has no governance
                registration or its lifecycle state does not permit the
                requested context.
        """
        logger.debug("Authorizing strategy %s for context '%s'.", strategy_id, context)
        strategy = self.db.get_strategy(strategy_id)
        if strategy is None:
            logger.error("Strategy %s not found during authorization.", strategy_id)
            raise LookupError(f"Strategy {strategy_id} not found")
        gov_id = strategy.get("governance_strategy_id") or _governance_strategy_id(
            int(strategy["user_id"]),
            strategy_id,
        )
        record = self.governance.get_strategy(str(gov_id))
        if record is None:
            logger.error(
                "Strategy %s has no governance registration for context '%s'.",
                strategy_id,
                context,
            )
            raise StrategyPermissionError(
                f"Strategy {strategy_id} has no governance registration and cannot run in {context}."
            )

        state = record.current_lifecycle_state.upper()
        allowed = _ALLOWED_STATES[context]
        if state not in allowed:
            required = ", ".join(sorted(allowed))
            logger.warning(
                "Strategy %s blocked: state '%s' not allowed for context '%s'.",
                strategy_id,
                state,
                context,
            )
            raise StrategyPermissionError(
                f"Strategy {strategy_id} is in lifecycle state '{state}'. "
                f"Context '{context}' requires one of: {required}."
            )
        logger.info(
            "Strategy %s authorized for context '%s' (state '%s').",
            strategy_id,
            context,
            state,
        )


def assert_strategy_allowed(
    strategy_id: int,
    context: StrategyRuntimeContext,
    *,
    db_manager: DatabaseManager | None = None,
    governance_repository: GovernanceRepository | None = None,
) -> None:
    """Convenience wrapper for one-off runtime permission checks.

    Args:
        strategy_id: Local strategy identifier to authorize.
        context: Requested runtime context (e.g. 'live', 'paper').
        db_manager: Optional database manager dependency.
        governance_repository: Optional governance repository dependency.

    Raises:
        LookupError: If the strategy is not found.
        StrategyPermissionError: If the strategy is not permitted to run.
    """
    StrategyRuntimePermissionService(
        db_manager=db_manager,
        governance_repository=governance_repository,
    ).assert_strategy_allowed(strategy_id=strategy_id, context=context)
    logger.debug("Implemented one-off strategy runtime permission check.")
