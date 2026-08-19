"""Canonical one-tick-at-a-time simulated execution engine."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, cast

from app.services.simulator.accounting import AccountLedger, LedgerFill
from app.services.simulator.errors import (
    SimulationError,
    operation_guard,
    unwrap_simulation_response,
)
from app.services.simulator.execution.lifecycle import (
    build_lifecycle_deal,
    deterministic_lifecycle_ticket,
)
from app.services.simulator.execution.matching import (
    evaluate_protective_exit,
    match_order,
)
from app.services.simulator.execution.provider_semantics import (
    is_provider_session_open,
    select_provider_revision,
    validate_provider_order,
)
from app.services.simulator.reporting.contracts import ClosedTradeRecord
from app.services.simulator.timeline import Tick, validate_intent_timing
from app.services.trading import create_execution_receipt
from app.utils import canonical_json, get_logger

RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

ExecutionReceipt = Any
OrderIntent = Any

if TYPE_CHECKING:
    from app.services.simulator.execution.matching import MatchResult
    from app.services.simulator.execution.pricing import ExecutionProfile
    from app.services.simulator.journal import JournalWriter

type ReceiptStatus = Literal[
    "accepted", "rejected", "partial", "filled", "cancelled", "unknown_outcome"
]


def _week_second(tick: Tick) -> int:
    """Calculate one tick's second offset within its UTC week.

    Args:
        tick: Canonical UTC tick.

    Returns:
        Integer UTC week offset.
    """
    logger.debug("Calculating Simulation UTC week offset")
    timestamp = tick.timestamp
    return (
        timestamp.weekday() * 86_400
        + timestamp.hour * 3_600
        + timestamp.minute * 60
        + timestamp.second
    )


def _receipt_id(intent: OrderIntent, status: str, sequence: int) -> str:
    """Derive a stable simulated receipt identity.

    Args:
        intent: Source order intent.
        status: Receipt status.
        sequence: Current tick sequence.

    Returns:
        Stable secret-free receipt identifier.
    """
    logger.debug("Deriving Simulation execution receipt identity")
    material = canonical_json(
        {
            "intent_id": intent.client_order_id,
            "status": status,
            "sequence": sequence,
        }
    )
    return f"sim-receipt-{sha256(material.encode('utf-8')).hexdigest()}"


def _deal_authority_snapshot(
    *,
    position_id: str,
    symbol: str,
    side: str,
    quantity: Decimal,
    source_sequence: int,
    account: Mapping[str, object],
) -> tuple[Mapping[str, object], str]:
    """Build complete post-event position/account and ledger identity evidence.

    Args:
        position_id: Exact affected position identity.
        symbol: Canonical position symbol.
        side: Provider BUY/SELL position side.
        quantity: Post-event open quantity, including zero after full close.
        source_sequence: Authority source sequence.
        account: Complete post-event account ledger snapshot.

    Returns:
        Immutable-compatible authority snapshot and stable ledger reference.
    """
    snapshot: Mapping[str, object] = {
        "position": {
            "position_id": position_id,
            "symbol": symbol,
            "side": "LONG" if side == "BUY" else "SHORT",
            "state": "FLAT" if quantity == 0 else "OPEN",
            "quantity": quantity,
            "source_sequence": source_sequence,
        },
        "account": dict(account),
    }
    reference = f"ledger-{sha256(canonical_json(account).encode()).hexdigest()}"
    return snapshot, reference


class EventDrivenExecutionEngine:
    """Own pending orders, fills, positions, excursions, and current tick."""

    def __init__(
        self,
        ledger: AccountLedger,
        journal_writer: JournalWriter,
        execution_profile: ExecutionProfile,
        engine_version: str,
        provider_revisions: Sequence[Mapping[str, object]],
    ) -> None:
        """Initialize one isolated execution engine.

        Args:
            ledger: Authoritative account ledger.
            journal_writer: Durable event writer.
            execution_profile: Explicit matching and pricing policy.
            engine_version: Stable implementation identity.
            provider_revisions: Complete Data-returned effective revision history.

        Raises:
            SimulationError: If engine identity is invalid.
        """
        logger.info("Initializing EventDrivenExecutionEngine %s", engine_version)
        if not engine_version or engine_version != engine_version.strip():
            raise SimulationError("SIM_INVALID_CONFIG", "Engine version is invalid")
        if not provider_revisions:
            raise SimulationError(
                "SIM_INVALID_CONFIG", "Provider revision evidence is required"
            )
        self._ledger = ledger
        self._journal = journal_writer
        self._profile = execution_profile
        self._engine_version = engine_version
        self._provider_revisions = tuple(provider_revisions)
        self._pending: dict[str, tuple[OrderIntent, bool]] = {}
        self._orders: dict[str, ExecutionReceipt] = {}
        self._deals: list[object] = []
        self._positions: dict[str, dict[str, object]] = {}
        self._closed_trades: list[ClosedTradeRecord] = []
        self._equity_observations: list[tuple[datetime, Decimal]] = []
        self._current_tick: Tick | None = None
        self._last_seen: Tick | None = None

    def _effective_provider_revision(self, at: datetime) -> Mapping[str, object]:
        """Select provider evidence for a canonical authority instant.

        Args:
            at: Current authority timestamp.

        Returns:
            Effective provider revision.

        Raises:
            SimulationError: If canonical revision coverage is invalid.
        """
        try:
            return select_provider_revision(self._provider_revisions, at=at)
        except (TypeError, ValueError) as error:
            raise SimulationError(
                "SIM_INVALID_CONFIG", f"Provider revision coverage failed: {error}"
            ) from error

    def _validate_pending_provider_order(
        self, intent: OrderIntent, tick: Tick, revision: Mapping[str, object]
    ) -> None:
        """Enforce effective provider order semantics before matching.

        Args:
            intent: Pending Trading-owned order intent.
            tick: Current authority quote.
            revision: Unique Data-returned effective provider revision.

        Raises:
            SimulationError: If any effective provider rule rejects the order.
        """
        payload = revision.get("payload")
        if not isinstance(payload, Mapping):
            raise SimulationError(
                "SIM_INVALID_CONFIG", "Provider revision payload is missing"
            )
        side = str(intent.side)
        position_volume = sum(
            (
                Decimal(str(position["volume"]))
                for position in self._positions.values()
                if position.get("side") == side
            ),
            Decimal(0),
        )
        pending_volume = sum(
            (
                Decimal(str(other.approved_volume))
                for other, _armed in self._pending.values()
                if other.client_order_id != intent.client_order_id
                and str(other.side) == side
            ),
            Decimal(0),
        )
        fill_policy = getattr(intent, "fill_policy", None) or getattr(
            intent, "time_in_force", None
        )
        reference_price = tick.ask if side == "BUY" else tick.bid
        try:
            for stop_price in (intent.stop_loss, intent.take_profit):
                validate_provider_order(
                    revision,
                    at=tick.timestamp,
                    action="OPEN",
                    fill_policy=str(fill_policy),
                    execution_mode=str(payload.get("execution_mode")),
                    requested_volume=Decimal(str(intent.approved_volume)),
                    same_direction_position_volume=position_volume,
                    same_direction_pending_volume=pending_volume,
                    reference_price=reference_price,
                    stop_price=stop_price,
                )
        except (TypeError, ValueError) as error:
            raise SimulationError(
                "SIM_INVALID_CONFIG",
                f"Provider order semantics rejected intent: {error}",
            ) from error

    def _provider_allows_tick(self, tick: Tick, revision: Mapping[str, object]) -> bool:
        """Return whether effective provider session evidence admits a tick.

        Args:
            tick: Current authority tick.
            revision: Effective provider revision.

        Returns:
            Whether provider-session processing may continue.

        Raises:
            SimulationError: If the provider session evidence is invalid.
        """
        try:
            return is_provider_session_open(revision, at=tick.timestamp)
        except (TypeError, ValueError) as error:
            raise SimulationError(
                "SIM_INVALID_CONFIG", f"Provider session evidence failed: {error}"
            ) from error

    @property
    def closed_trades(self) -> tuple[ClosedTradeRecord, ...]:
        """Return the ordered closed-trade ledger observed during this run.

        Returns:
            Immutable ordered closed-trade records.
        """
        logger.debug("Reading the Simulation closed-trade ledger")
        return tuple(self._closed_trades)

    @property
    def equity_observations(self) -> tuple[tuple[datetime, Decimal], ...]:
        """Return end-of-tick mark-to-market equity observations.

        Returns:
            Immutable ordered UTC timestamp and equity pairs.
        """
        logger.debug("Reading Simulation mark-to-market equity observations")
        return tuple(self._equity_observations)

    def _receipt(
        self,
        intent: OrderIntent,
        status: ReceiptStatus,
        filled: Decimal,
        price: Decimal | None,
        tick: Tick,
    ) -> ExecutionReceipt:
        """Construct one Trading-owned immutable execution receipt.

        Args:
            intent: Source order intent.
            status: Trading receipt status.
            filled: Exact filled quantity.
            price: Exact average price when filled.
            tick: Authority tick.

        Returns:
            Trading-owned execution receipt.
        """
        logger.debug("Constructing Simulation receipt with status %s", status)
        deal_ids = (
            (str(cast("Mapping[str, object]", self._deals[-1])["deal_id"]),)
            if filled > 0
            else ()
        )
        return create_execution_receipt(
            receipt_id=_receipt_id(intent, status, tick.sequence),
            intent_id=intent.source_intent_id,
            client_order_id=intent.client_order_id,
            route=intent.route,
            authority="simulation",
            provider_order_id=f"sim-order-{intent.client_order_id}",
            provider_deal_ids=deal_ids,
            status=status,
            requested_quantity=intent.approved_volume,
            filled_quantity=filled,
            average_price=price,
            authority_timestamp=tick.timestamp,
            received_at=tick.timestamp,
            response_classification=f"simulation_{status}",
            retry_safe=status in {"rejected", "cancelled"},
            reconciliation_required=False,
            request_id=intent.request_id,
            correlation_id=intent.correlation_id,
        )

    @operation_guard(
        operation="simulation.execution.event_driven_execution_engine.submit_order",
        risk_level="medium",
        read_only=False,
    )
    def submit_order(self, intent: OrderIntent) -> ExecutionReceipt:
        """Accept one validated sim-route intent into pending engine state.

        Args:
            intent: Trading-owned approved intent.

        Returns:
            Immediate accepted receipt.

        Raises:
            SimulationError: If route, volume, or identity is invalid.
        """
        logger.info("Submitting order %s to Simulation engine", intent.client_order_id)
        if str(intent.route) != "sim":
            raise SimulationError(
                "SIM_INVALID_CONFIG", "Only sim-route intents are accepted"
            )
        if (
            intent.client_order_id in self._pending
            or intent.client_order_id in self._orders
        ):
            raise SimulationError(
                "SIM_RUN_ID_CONFLICT", "Order identity is already present"
            )
        authority_tick = self._current_tick
        authority_time = (
            intent.created_at if authority_tick is None else authority_tick.timestamp
        )
        authority_sequence = 0 if authority_tick is None else authority_tick.sequence
        receipt = create_execution_receipt(
            receipt_id=_receipt_id(intent, "accepted", authority_sequence),
            intent_id=intent.source_intent_id,
            client_order_id=intent.client_order_id,
            route=intent.route,
            authority="simulation",
            provider_order_id=f"sim-order-{intent.client_order_id}",
            provider_deal_ids=(),
            status="accepted",
            requested_quantity=intent.approved_volume,
            filled_quantity=Decimal(0),
            average_price=None,
            authority_timestamp=authority_time,
            received_at=authority_time,
            response_classification="simulation_accepted",
            retry_safe=False,
            reconciliation_required=False,
            request_id=intent.request_id,
            correlation_id=intent.correlation_id,
        )
        unwrap_simulation_response(
            self._journal.append(
                "order_accepted",
                {
                    "client_order_id": intent.client_order_id,
                    "approved_volume": intent.approved_volume,
                },
                authority_time,
                intent.source_intent_id,
            ),
            operation="simulation.execution.event_driven_execution_engine.submit_order",
        )
        self._pending[intent.client_order_id] = (intent, False)
        self._orders[intent.client_order_id] = receipt
        return receipt

    def _apply_match(
        self, intent: OrderIntent, match: MatchResult, tick: Tick
    ) -> ExecutionReceipt:
        """Journal and apply one terminal or partial match.

        Args:
            intent: Source intent.
            match: Pure matching outcome.
            tick: Current authority tick.

        Returns:
            Trading-owned outcome receipt.

        Raises:
            SimulationError: If a non-terminal match reaches state mutation.
        """
        logger.info("Applying Simulation match %s", match.status)
        if match.status == "pending":
            raise SimulationError(
                "SIM_ACCOUNT_INVARIANT_BROKEN",
                "Pending match cannot be applied as a fill",
            )
        if match.filled_quantity > 0 and match.execution_price is not None:
            self._journal.append(
                "fill_proposed",
                {
                    "client_order_id": intent.client_order_id,
                    "quantity": match.filled_quantity,
                    "price": match.execution_price,
                },
                tick.timestamp,
                intent.source_intent_id,
            )
            costs = self._ledger.apply_fill_internal(
                LedgerFill(
                    action="OPEN",
                    side=intent.side,
                    volume=match.filled_quantity,
                    price=match.execution_price,
                )
            )
            position_id = f"sim-position-{intent.client_order_id}"
            self._positions[position_id] = {
                "position_id": position_id,
                "account_id": intent.account_id,
                "ticket": position_id,
                "symbol": intent.symbol,
                "side": intent.side,
                "volume": match.filled_quantity,
                "entry_price": match.execution_price,
                "entry_time": tick.timestamp,
                "stop_loss": intent.stop_loss,
                "take_profit": intent.take_profit,
                "magic": intent.strategy_id,
                "comment": intent.client_order_id,
                "commission": costs["commission"],
                "swap": costs["swap"],
                "mae": Decimal(0),
                "mfe": Decimal(0),
            }
            account_after = self._ledger.snapshot_internal()
            authority_sequence = len(self._deals)
            authority_snapshot, ledger_reference = _deal_authority_snapshot(
                position_id=position_id,
                symbol=intent.symbol,
                side=str(intent.side),
                quantity=match.filled_quantity,
                source_sequence=authority_sequence,
                account=account_after,
            )
            deal = build_lifecycle_deal(
                order_id=f"sim-order-{intent.client_order_id}",
                account_id=intent.account_id,
                position_id=position_id,
                side=str(intent.side),
                quantity=match.filled_quantity,
                price=match.execution_price,
                entry="DEAL_ENTRY_IN",
                reason="EXPERT",
                occurred_at=tick.timestamp,
                economic_at=tick.timestamp,
                available_at=tick.timestamp,
                source_sequence=authority_sequence,
                fee_evidence=costs,
                authority_snapshot=authority_snapshot,
                ledger_reference=ledger_reference,
            )
            self._deals.append(MappingProxyType(dict(deal)))
        receipt_status: ReceiptStatus = match.status
        receipt = self._receipt(
            intent,
            receipt_status,
            match.filled_quantity,
            match.execution_price,
            tick,
        )
        unwrap_simulation_response(
            self._journal.append(
                "order_outcome",
                receipt.model_dump(mode="python", warnings=False),
                tick.timestamp,
                intent.source_intent_id,
            ),
            operation="simulation.execution.event_driven_execution_engine._apply_match",
        )
        self._orders[intent.client_order_id] = receipt
        return receipt

    def _observe_excursions(self, tick: Tick) -> None:
        """Update open-position MAE and MFE and mark the account to market.

        Args:
            tick: Current canonical tick.
        """
        logger.debug("Observing Simulation position excursions")
        unrealized = Decimal(0)
        for position in self._positions.values():
            entry = Decimal(str(position["entry_price"]))
            volume = Decimal(str(position["volume"]))
            side = str(position["side"])
            movement = self._ledger.calculate_profit(
                side="BUY" if side == "BUY" else "SELL",
                volume=volume,
                entry_price=entry,
                exit_price=tick.bid if side == "BUY" else tick.ask,
            )
            position["mae"] = min(Decimal(str(position["mae"])), movement)
            position["mfe"] = max(Decimal(str(position["mfe"])), movement)
            unrealized += movement
        self._ledger.mark_to_market_internal(unrealized)

    def _close(
        self,
        position_id: str,
        quantity: Decimal,
        tick: Tick,
        exit_reason: str,
    ) -> Mapping[str, object]:
        """Close all or part of one position and record terminal evidence.

        Args:
            position_id: Existing simulated position identity.
            quantity: Approved closing quantity.
            tick: Authority tick supplying the exit price.
            exit_reason: Journalled cause of the close.

        Returns:
            Immutable close evidence.

        Raises:
            SimulationError: If position or quantity evidence is invalid.
        """
        logger.info("Closing Simulation position %s by %s", position_id, exit_reason)
        position = self._positions.get(position_id)
        if position is None:
            raise SimulationError("SIM_POSITION_NOT_FOUND", "Position does not exist")
        current_volume = Decimal(str(position["volume"]))
        if not quantity.is_finite() or quantity <= 0 or quantity > current_volume:
            raise SimulationError("SIM_INVALID_VOLUME", "Close quantity is invalid")
        side = str(position["side"])
        exit_price = tick.bid if side == "BUY" else tick.ask
        entry_price = Decimal(str(position["entry_price"]))
        gross_profit = self._ledger.calculate_profit(
            side="BUY" if side == "BUY" else "SELL",
            volume=quantity,
            entry_price=entry_price,
            exit_price=exit_price,
        )
        account = self._ledger.snapshot_internal()
        used_margin = Decimal(str(account["used_margin"]))
        margin_released = used_margin * quantity / current_volume
        unwrap_simulation_response(
            self._journal.append(
                "position_close_proposed",
                {
                    "position_id": position_id,
                    "quantity": quantity,
                    "price": exit_price,
                    "exit_reason": exit_reason,
                },
                tick.timestamp,
                position_id,
            ),
            operation="simulation.execution.event_driven_execution_engine._close",
        )
        costs = self._ledger.apply_fill_internal(
            LedgerFill(
                action="CLOSE",
                side="BUY" if side == "BUY" else "SELL",
                volume=quantity,
                price=exit_price,
                gross_profit=gross_profit,
                margin_released=margin_released,
            )
        )
        share = quantity / current_volume
        self._closed_trades.append(
            ClosedTradeRecord(
                ticket=str(position["ticket"]),
                symbol=str(position["symbol"]),
                type="BUY" if side == "BUY" else "SELL",
                volume=quantity,
                entry_time=position["entry_time"],  # type: ignore[arg-type]
                entry_price=entry_price,
                stop_loss=position["stop_loss"],  # type: ignore[arg-type]
                take_profit=position["take_profit"],  # type: ignore[arg-type]
                exit_time=tick.timestamp,
                exit_price=exit_price,
                comment=str(position["comment"]),
                commission=Decimal(str(position["commission"])) * share
                + costs["commission"],
                swap=Decimal(str(position["swap"])) * share + costs["swap"],
                profit=gross_profit,
                magic=str(position["magic"]),
                mae=Decimal(str(position["mae"])) * share,
                mfe=Decimal(str(position["mfe"])) * share,
            )
        )
        remaining = current_volume - quantity
        if remaining == 0:
            del self._positions[position_id]
        else:
            position["volume"] = remaining
        account_after = self._ledger.snapshot_internal()
        authority_sequence = len(self._deals)
        authority_snapshot, ledger_reference = _deal_authority_snapshot(
            position_id=position_id,
            symbol=str(position["symbol"]),
            side=side,
            quantity=remaining,
            source_sequence=authority_sequence,
            account=account_after,
        )
        close_order_id = deterministic_lifecycle_ticket(
            "order",
            {
                "position_id": position_id,
                "quantity": quantity,
                "source_sequence": tick.sequence,
                "reason": exit_reason,
            },
        )
        lifecycle_deal = build_lifecycle_deal(
            order_id=close_order_id,
            account_id=str(position["account_id"]),
            position_id=position_id,
            side="SELL" if side == "BUY" else "BUY",
            quantity=quantity,
            price=exit_price,
            entry="DEAL_ENTRY_OUT",
            reason=exit_reason,
            occurred_at=tick.timestamp,
            economic_at=tick.timestamp,
            available_at=tick.timestamp,
            source_sequence=authority_sequence,
            fee_evidence={
                **costs,
                "gross_profit": gross_profit,
            },
            authority_snapshot=authority_snapshot,
            ledger_reference=ledger_reference,
        )
        deal = MappingProxyType(dict(lifecycle_deal))
        self._deals.append(deal)
        unwrap_simulation_response(
            self._journal.append(
                "authority_deal",
                dict(deal),
                tick.timestamp,
                position_id,
            ),
            operation="simulation.execution.event_driven_execution_engine._close",
        )
        return deal

    def _apply_protective_exits(self, tick: Tick) -> None:
        """Close every open position whose stop or target crossed this tick.

        Args:
            tick: Current canonical tick.

        Raises:
            SimulationError: If a close cannot be applied deterministically.
        """
        logger.debug("Applying Simulation protective exits")
        for position_id, position in tuple(self._positions.items()):
            exit_reason = evaluate_protective_exit(position, tick)
            if exit_reason is None:
                continue
            unwrap_simulation_response(
                self._journal.append(
                    "protection_trigger",
                    {
                        "position_id": position_id,
                        "trigger": exit_reason,
                        "source_sequence": tick.sequence,
                    },
                    tick.timestamp,
                    position_id,
                ),
                operation="simulation.execution.event_driven_execution_engine._apply_protective_exits",
            )
            self._close(
                position_id,
                Decimal(str(position["volume"])),
                tick,
                exit_reason,
            )

    @operation_guard(
        operation="simulation.execution.event_driven_execution_engine.execute_tick",
        risk_level="medium",
        read_only=False,
    )
    def execute_tick(self, tick: Tick) -> tuple[ExecutionReceipt, ...]:
        """Advance exactly one tick and process all pending orders.

        Args:
            tick: Next canonical tick.

        A tick outside every configured UTC session is journalled and skipped
        rather than aborting the run, because Data may legitimately supply
        closed-market ticks inside a requested range.

        Returns:
            Immutable terminal/partial receipts produced at this tick, or an
            empty tuple when the tick falls outside every configured session.

        Raises:
            SimulationError: If timing, matching, or accounting fails.
        """
        return self.execute_tick_internal(tick)

    def execute_tick_internal(self, tick: Tick) -> tuple[ExecutionReceipt, ...]:
        """Execute one validated canonical tick inside the trusted run loop.

        Args:
            tick: Next canonical ordered tick.

        Returns:
            Terminal or partial receipts produced by this tick.

        Raises:
            SimulationError: If timing, matching, or accounting fails.
        """
        if self._last_seen is not None and (
            tick.timestamp <= self._last_seen.timestamp
            or tick.sequence <= self._last_seen.sequence
        ):
            raise SimulationError(
                "SIM_DATA_NON_MONOTONIC", "Execution tick is not strictly ordered"
            )
        self._last_seen = tick
        revision = self._effective_provider_revision(tick.timestamp)
        if not self._provider_allows_tick(tick, revision):
            unwrap_simulation_response(
                self._journal.append(
                    "tick_outside_provider_session",
                    {"sequence": tick.sequence, "symbol": tick.symbol},
                    tick.timestamp,
                ),
                operation="simulation.execution.event_driven_execution_engine.execute_tick",
            )
            return ()
        week_second = _week_second(tick)
        if not any(
            session.start_week_second <= week_second < session.end_week_second
            for session in self._profile.sessions
        ):
            logger.info("Skipping Simulation tick outside configured sessions")
            unwrap_simulation_response(
                self._journal.append(
                    "tick_outside_session",
                    {"sequence": tick.sequence, "symbol": tick.symbol},
                    tick.timestamp,
                ),
                operation="simulation.execution.event_driven_execution_engine.execute_tick",
            )
            return ()
        self._current_tick = tick
        self._observe_excursions(tick)
        self._apply_protective_exits(tick)
        outcomes: list[ExecutionReceipt] = []
        for order_id, (intent, armed) in tuple(self._pending.items()):
            if order_id not in self._orders:
                raise SimulationError(
                    "SIM_ORDER_NOT_FOUND", "Pending order state is inconsistent"
                )
            validate_intent_timing(intent.created_at, tick.timestamp)
            self._validate_pending_provider_order(intent, tick, revision)
            if tick.timestamp >= intent.valid_until:
                receipt = self._receipt(intent, "cancelled", Decimal(0), None, tick)
                self._orders[order_id] = receipt
                del self._pending[order_id]
                outcomes.append(receipt)
                continue
            match = match_order(intent, tick, self._profile, stop_limit_armed=armed)
            if match.status == "pending":
                self._pending[order_id] = (intent, match.stop_limit_armed)
                continue
            outcomes.append(self._apply_match(intent, match, tick))
            if match.remainder_quantity > 0:
                residual = intent.model_copy(
                    update={
                        "approved_volume": match.remainder_quantity,
                        "risk_approved_volume": match.remainder_quantity,
                    }
                )
                self._pending[order_id] = (residual, match.stop_limit_armed)
            else:
                del self._pending[order_id]
        self._observe_excursions(tick)
        account = self._ledger.snapshot_internal()
        self._equity_observations.append(
            (tick.timestamp, Decimal(str(account["equity"])))
        )
        return tuple(outcomes)

    @operation_guard(
        operation="simulation.execution.event_driven_execution_engine.close_position",
        risk_level="medium",
        read_only=False,
    )
    def close_position(
        self, position_id: str, quantity: Decimal
    ) -> Mapping[str, object]:
        """Close an existing position using the current canonical tick.

        Args:
            position_id: Existing simulated position identity.
            quantity: Approved closing quantity.

        Returns:
            Immutable close evidence.

        Raises:
            SimulationError: If position, tick, or quantity is unavailable.
        """
        logger.info("Closing Simulation position %s on request", position_id)
        if self._current_tick is None:
            raise SimulationError("SIM_INVALID_CONFIG", "No current tick is available")
        return self._close(position_id, quantity, self._current_tick, "REQUESTED")

    @operation_guard(
        operation=(
            "simulation.execution.event_driven_execution_engine.cancel_pending_order"
        ),
        risk_level="medium",
        read_only=False,
    )
    def cancel_pending_order(self, client_order_id: str) -> ExecutionReceipt:
        """Cancel one pending order that has not matched.

        Cancellation removes the resting order and records a cancelled receipt.
        It never produces a fill: an order that already matched is no longer
        pending and cannot be cancelled.

        Args:
            client_order_id: Trading-owned resting order identity.

        Returns:
            Trading-owned cancelled receipt.

        Raises:
            SimulationError: `SIM_ORDER_NOT_FOUND` when no such order rests.
        """
        logger.info("Cancelling pending Simulation order %s", client_order_id)
        resting = self._pending.pop(client_order_id, None)
        if resting is None:
            raise SimulationError(
                "SIM_ORDER_NOT_FOUND", "No pending order matches that identity"
            )
        intent, _armed = resting
        authority_tick = self._current_tick
        authority_time = (
            intent.created_at if authority_tick is None else authority_tick.timestamp
        )
        authority_sequence = 0 if authority_tick is None else authority_tick.sequence
        unwrap_simulation_response(
            self._journal.append(
                "order_cancelled",
                {"client_order_id": intent.client_order_id},
                authority_time,
                intent.source_intent_id,
            ),
            operation=(
                "simulation.execution.event_driven_execution_engine"
                ".cancel_pending_order"
            ),
        )
        receipt = create_execution_receipt(
            receipt_id=_receipt_id(intent, "cancelled", authority_sequence),
            intent_id=intent.source_intent_id,
            client_order_id=intent.client_order_id,
            route=intent.route,
            authority="simulation",
            provider_order_id=f"sim-order-{intent.client_order_id}",
            provider_deal_ids=(),
            status="cancelled",
            requested_quantity=intent.approved_volume,
            filled_quantity=Decimal(0),
            average_price=None,
            authority_timestamp=authority_time,
            received_at=authority_time,
            response_classification="simulation_cancelled",
            retry_safe=True,
            reconciliation_required=False,
            request_id=intent.request_id,
            correlation_id=intent.correlation_id,
        )
        self._orders[intent.client_order_id] = receipt
        return receipt

    @operation_guard(
        operation=(
            "simulation.execution.event_driven_execution_engine.modify_pending_order"
        ),
        risk_level="medium",
        read_only=False,
    )
    def modify_pending_order(
        self,
        client_order_id: str,
        *,
        price: Decimal | None = None,
        stop_loss: Decimal | None = None,
        take_profit: Decimal | None = None,
    ) -> ExecutionReceipt:
        """Revise the levels of one resting order without refilling it.

        Only price and protective levels change. Volume is Risk-approved and is
        never re-sized here, and the revision produces an accepted receipt with
        no filled quantity: a modification is not a fill.

        Args:
            client_order_id: Trading-owned resting order identity.
            price: Replacement limit or stop trigger price.
            stop_loss: Replacement protective stop level.
            take_profit: Replacement protective target level.

        Returns:
            Trading-owned accepted receipt for the revised order.

        Raises:
            SimulationError: `SIM_ORDER_NOT_FOUND` when no such order rests, or
                `SIM_INVALID_CONFIG` when no level was supplied.
        """
        logger.info("Modifying pending Simulation order %s", client_order_id)
        resting = self._pending.get(client_order_id)
        if resting is None:
            raise SimulationError(
                "SIM_ORDER_NOT_FOUND", "No pending order matches that identity"
            )
        if price is None and stop_loss is None and take_profit is None:
            raise SimulationError(
                "SIM_INVALID_CONFIG", "A modification must supply at least one level"
            )
        intent, armed = resting
        updates: dict[str, object] = {}
        if price is not None:
            updates["price"] = price
        if stop_loss is not None:
            updates["stop_loss"] = stop_loss
        if take_profit is not None:
            updates["take_profit"] = take_profit
        revised = intent.model_copy(update=updates)
        authority_tick = self._current_tick
        authority_time = (
            intent.created_at if authority_tick is None else authority_tick.timestamp
        )
        authority_sequence = 0 if authority_tick is None else authority_tick.sequence
        unwrap_simulation_response(
            self._journal.append(
                "order_modified",
                {
                    "client_order_id": intent.client_order_id,
                    "modified_fields": tuple(sorted(updates)),
                },
                authority_time,
                intent.source_intent_id,
            ),
            operation=(
                "simulation.execution.event_driven_execution_engine"
                ".modify_pending_order"
            ),
        )
        self._pending[client_order_id] = (revised, armed)
        receipt = create_execution_receipt(
            receipt_id=_receipt_id(revised, "accepted", authority_sequence + 1),
            intent_id=revised.source_intent_id,
            client_order_id=revised.client_order_id,
            route=revised.route,
            authority="simulation",
            provider_order_id=f"sim-order-{revised.client_order_id}",
            provider_deal_ids=(),
            status="accepted",
            requested_quantity=revised.approved_volume,
            filled_quantity=Decimal(0),
            average_price=None,
            authority_timestamp=authority_time,
            received_at=authority_time,
            response_classification="simulation_modified",
            retry_safe=False,
            reconciliation_required=False,
            request_id=revised.request_id,
            correlation_id=revised.correlation_id,
        )
        self._orders[revised.client_order_id] = receipt
        return receipt

    @operation_guard(
        operation="simulation.execution.event_driven_execution_engine.snapshot",
        risk_level="medium",
        read_only=True,
    )
    def snapshot(self) -> Mapping[str, object]:
        """Return immutable engine and account state.

        Returns:
            Deeply immutable state projection.
        """
        return self.snapshot_internal()

    def snapshot_internal(self) -> Mapping[str, object]:
        """Return the trusted internal immutable engine projection.

        Returns:
            Immutable engine and account state.
        """
        positions = tuple(
            MappingProxyType(dict(row)) for row in self._positions.values()
        )
        return MappingProxyType(
            {
                "engine_version": self._engine_version,
                "orders": tuple(self._orders.values()),
                "positions": positions,
                "pending_orders": tuple(row[0] for row in self._pending.values()),
                "deals": tuple(self._deals),
                "closed_trades": tuple(self._closed_trades),
                "account": self._ledger.snapshot_internal(),
            }
        )


__all__ = ["EventDrivenExecutionEngine"]
