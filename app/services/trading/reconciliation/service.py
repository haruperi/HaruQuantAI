"""Reconciliation service for orchestrating state syncs and authority policies."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, cast

from app.services.trading.contracts import (
    TradingContract,
    TradingRoute,
)
from app.services.trading.execution.reporting import (
    ReconciliationDiscrepancyEntry,  # noqa: TC001
)
from app.services.trading.execution.state_machine import LifecycleKind
from app.services.trading.info._common import broker_call, iter_or_empty, safe_attr
from app.services.trading.info.account import AccountInfo
from app.services.trading.reconciliation.snapshots_and_compare import (
    compare_snapshots,
)
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.trading.config.models import TradingRuntimeConfig
    from app.services.trading.contracts import JsonObject
    from app.services.trading.reconciliation.authority_and_retry_guard import (
        AuthorityAndRetryGuard,
    )
    from app.services.trading.state.event_journal import AppendOnlyEventJournal
    from app.services.trading.state.ports import Clock, TradeStore, TradingStateStore


class ReconciliationReport(TradingContract):
    """Report summarizing the outcome of a reconciliation run.

    Attributes:
        run_id: Unique run identifier.
        run_type: Reconciliation trigger type.
        account_id: Account identifier.
        route: Active trading route.
        timestamp: ISO format run timestamp.
        discrepancies: Detected discrepancies.
        status: Run status ("success" or "mismatch").
    """

    run_id: str
    run_type: str
    account_id: str
    route: TradingRoute
    timestamp: str
    discrepancies: tuple[ReconciliationDiscrepancyEntry, ...]
    status: str


class ReconciliationService:
    """Coordinates startup, pre-trade, periodic, and shutdown reconciliation runs."""

    def __init__(
        self,
        *,
        trade_store: TradeStore,
        state_store: TradingStateStore,
        journal: AppendOnlyEventJournal,
        authority_guard: AuthorityAndRetryGuard,
        clock: Clock,
        config: TradingRuntimeConfig,
    ) -> None:
        """Initialize the reconciliation service.

        Args:
            trade_store: Injected TradeStore.
            state_store: Injected state store snapshot manager.
            journal: Append-only event journal.
            authority_guard: Mutation block manager.
            clock: Injected clock.
            config: Runtime configuration settings.
        """
        logger.info("Initializing ReconciliationService.")
        self._trade_store = trade_store
        self._state_store = state_store
        self._journal = journal
        self._authority_guard = authority_guard
        self._clock = clock
        self._config = config

    def run_reconciliation(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        account_id: str,
        run_type: str,
    ) -> ReconciliationReport:
        """Execute a state reconciliation check.

        Args:
            route: Active trading route.
            tenant_id: Tenant or session namespace.
            account_id: Account identifier.
            run_type: The trigger/context of this run (e.g. "startup",
                "periodic", "pre_trade", "post_unknown_outcome", "shutdown").

        Returns:
            ReconciliationReport: The reconciliation run report.
        """
        logger.info(
            "Running reconciliation (type={}, route={}) for account {}.",
            run_type,
            route.value,
            account_id,
        )
        timestamp = self._clock.now_utc().isoformat()
        run_id = f"recon-{run_type}-{self._clock.monotonic():.3f}"

        # 1. Retrieve broker snapshots using facades & direct helpers
        raw_orders = iter_or_empty(broker_call("get_order_info"))
        broker_orders = [self._extract_broker_order(o) for o in raw_orders]

        raw_positions = iter_or_empty(broker_call("get_position_info"))
        broker_positions = [self._extract_broker_position(p) for p in raw_positions]

        account_facade = AccountInfo()
        broker_balance = Decimal(str(account_facade.balance()))
        broker_margin = Decimal(str(account_facade.margin()))

        # 2. Retrieve local projections from stores
        local_orders = self._trade_store.list_order_states(
            route=route, tenant_id=tenant_id
        )
        local_positions = self._trade_store.list_position_states(
            route=route, tenant_id=tenant_id
        )

        latest_snapshot = self._state_store.load_state(
            route=route, tenant_id=tenant_id, snapshot_id="latest"
        )
        if latest_snapshot is not None:
            local_balance = Decimal(str(latest_snapshot.get("balance", broker_balance)))
            local_margin = Decimal(str(latest_snapshot.get("margin", broker_margin)))
        else:
            local_balance = broker_balance
            local_margin = broker_margin

        # 3. Compare states
        discrepancies = compare_snapshots(
            local_orders=local_orders,
            broker_orders=broker_orders,
            local_positions=local_positions,
            broker_positions=broker_positions,
            local_balance=local_balance,
            broker_balance=broker_balance,
            local_margin=local_margin,
            broker_margin=broker_margin,
            price_drift_threshold=self._config.reconciliation.price_drift_threshold,
            volume_drift_threshold=self._config.reconciliation.volume_drift_threshold,
            balance_drift_threshold=self._config.reconciliation.balance_drift_threshold,
            margin_drift_threshold=self._config.reconciliation.margin_drift_threshold,
            clock=self._clock,
        )

        # 4. Handle mismatches & apply policies
        self._handle_discrepancies(
            route=route,
            tenant_id=tenant_id,
            account_id=account_id,
            run_type=run_type,
            discrepancies=discrepancies,
            broker_positions=broker_positions,
        )

        status = "mismatch" if discrepancies else "success"

        # 5. Journal reconciliation resolution
        self._journal.append_event(
            event_type="ReconciliationResolutionEvent",
            request_id=run_id,
            correlation_id=run_id,
            route=route,
            account_id=account_id,
            symbol="*",
            actor="reconciliation_service",
            payload={
                "run_id": run_id,
                "run_type": run_type,
                "status": status,
                "discrepancies": [d.model_dump() for d in discrepancies],
            },
        )

        return ReconciliationReport(
            run_id=run_id,
            run_type=run_type,
            account_id=account_id,
            route=route,
            timestamp=timestamp,
            discrepancies=tuple(discrepancies),
            status=status,
        )

    def _handle_discrepancies(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        account_id: str,
        run_type: str,
        discrepancies: list[ReconciliationDiscrepancyEntry],
        broker_positions: list[JsonObject],
    ) -> None:
        """Handle detected discrepancies, applying startup and orphan policies.

        Args:
            route: Active trading route.
            tenant_id: Tenant namespace.
            account_id: Account identifier.
            run_type: reconciliation run type context.
            discrepancies: List of detected discrepancies.
            broker_positions: Positions from the broker.
        """
        if not discrepancies:
            return

        logger.warning("Reconciliation found {} discrepancies.", len(discrepancies))

        # Raise alerts and apply startup/orphan policies
        if run_type == "startup":
            logger.critical("Startup reconciliation mismatch! Blocking mutations.")
            self._authority_guard.transition_to_unresolved(
                account_id, "*", "STARTUP_MISMATCH"
            )

        # Evaluate orphan deals policy
        policy = self._config.reconciliation.orphan_deal_policy
        for disc in discrepancies:
            if disc.discrepancy_type == "missing_locally":
                self._handle_missing_locally(
                    route=route,
                    tenant_id=tenant_id,
                    account_id=account_id,
                    policy=policy,
                    disc=disc,
                    broker_positions=broker_positions,
                )

    def _handle_missing_locally(
        self,
        *,
        route: TradingRoute,
        tenant_id: str,
        account_id: str,
        policy: str,
        disc: ReconciliationDiscrepancyEntry,
        broker_positions: list[JsonObject],
    ) -> None:
        """Handle a missing locally (orphan) discrepancy.

        Args:
            route: Active trading route.
            tenant_id: Tenant namespace.
            account_id: Account identifier.
            policy: Orphan deal policy from configuration.
            disc: The missing locally discrepancy entry.
            broker_positions: Positions from the broker.
        """
        symbol = "*"
        if disc.kind == LifecycleKind.POSITION:
            broker_p = next(
                (
                    p
                    for p in broker_positions
                    if str(p.get("position_id")) == disc.entity_id
                ),
                None,
            )
            if broker_p:
                symbol = str(broker_p.get("symbol", "*"))

        if policy == "block":
            logger.critical(
                "Orphan deal detected for symbol {}. Blocking mutations.",
                symbol,
            )
            self._authority_guard.transition_to_unresolved(
                account_id, symbol, "ORPHAN_DEAL_BLOCK"
            )
        elif policy == "adopt-quarantine" and disc.kind == LifecycleKind.POSITION:
            logger.info(
                "Orphan deal quarantined for position {} symbol {}.",
                disc.entity_id,
                symbol,
            )
            broker_p = next(
                (
                    p
                    for p in broker_positions
                    if str(p.get("position_id")) == disc.entity_id
                ),
                None,
            )
            if broker_p:
                quarantined_p = {
                    "position_id": disc.entity_id,
                    "symbol": broker_p.get("symbol", ""),
                    "state": "OPEN",
                    "volume": str(broker_p.get("volume", 0.0)),
                    "vwap": str(broker_p.get("price_open", 0.0)),
                    "regulatory_tags": {
                        "tags": {
                            "owner": "external",
                            "quarantine": "true",
                        }
                    },
                }
                self._trade_store.save_position_state(
                    route=route,
                    tenant_id=tenant_id,
                    position_state=cast("JsonObject", quarantined_p),
                    expected_version=None,
                )

    def _extract_broker_order(self, raw_order: object) -> JsonObject:
        """Map raw broker order attributes to JSON-safe dictionary fields.

        Args:
            raw_order: Broker order record.

        Returns:
            JsonObject: Standardized order dictionary.
        """
        logger.debug("Extracting broker order details.")
        return {
            "ticket": str(
                safe_attr(raw_order, "ticket", 0, int)
                or safe_attr(raw_order, "order_id", "", str)
            ),
            "symbol": safe_attr(raw_order, "symbol", "", str),
            "volume_current": float(safe_attr(raw_order, "volume_current", 0.0, float)),
            "price": float(safe_attr(raw_order, "price", 0.0, float)),
            "state": safe_attr(raw_order, "state", 0, int),
            "comment": safe_attr(raw_order, "comment", "", str),
            "magic": int(safe_attr(raw_order, "magic", 0, int)),
        }

    def _extract_broker_position(self, raw_position: object) -> JsonObject:
        """Map raw broker position attributes to JSON-safe dictionary fields.

        Args:
            raw_position: Broker position record.

        Returns:
            JsonObject: Standardized position dictionary.
        """
        logger.debug("Extracting broker position details.")
        return {
            "position_id": str(
                safe_attr(raw_position, "position_id", "", str)
                or safe_attr(raw_position, "ticket", 0, int)
            ),
            "symbol": safe_attr(raw_position, "symbol", "", str),
            "volume": float(safe_attr(raw_position, "volume", 0.0, float)),
            "price_open": float(safe_attr(raw_position, "price_open", 0.0, float)),
            "comment": safe_attr(raw_position, "comment", "", str),
            "magic": int(safe_attr(raw_position, "magic", 0, int)),
        }
