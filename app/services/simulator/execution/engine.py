"""Canonical one-tick-at-a-time simulated execution engine."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from hashlib import sha256
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from app.services.simulator.accounting import AccountLedger, LedgerFill
from app.services.simulator.errors import SimulationError
from app.services.simulator.execution.matching import (
    evaluate_protective_exit,
    match_order,
)
from app.services.simulator.reporting.contracts import ClosedTradeRecord
from app.services.simulator.timeline import Tick, validate_intent_timing
from app.services.trading import ExecutionReceipt, OrderIntent
from app.utils import canonical_json, logger

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


class EventDrivenExecutionEngine:
    """Own pending orders, fills, positions, excursions, and current tick."""

    def __init__(
        self,
        ledger: AccountLedger,
        journal_writer: JournalWriter,
        execution_profile: ExecutionProfile,
        engine_version: str,
    ) -> None:
        """Initialize one isolated execution engine.

        Args:
            ledger: Authoritative account ledger.
            journal_writer: Durable event writer.
            execution_profile: Explicit matching and pricing policy.
            engine_version: Stable implementation identity.

        Raises:
            SimulationError: If engine identity is invalid.
        """
        logger.info("Initializing EventDrivenExecutionEngine %s", engine_version)
        if not engine_version or engine_version != engine_version.strip():
            raise SimulationError("SIM_INVALID_CONFIG", "Engine version is invalid")
        self._ledger = ledger
        self._journal = journal_writer
        self._profile = execution_profile
        self._engine_version = engine_version
        self._pending: dict[str, tuple[OrderIntent, bool]] = {}
        self._orders: dict[str, ExecutionReceipt] = {}
        self._deals: list[ExecutionReceipt] = []
        self._positions: dict[str, dict[str, object]] = {}
        self._closed_trades: list[ClosedTradeRecord] = []
        self._current_tick: Tick | None = None
        self._last_seen: Tick | None = None

    @property
    def closed_trades(self) -> tuple[ClosedTradeRecord, ...]:
        """Return the ordered closed-trade ledger observed during this run.

        Returns:
            Immutable ordered closed-trade records.
        """
        logger.debug("Reading the Simulation closed-trade ledger")
        return tuple(self._closed_trades)

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
            (f"sim-deal-{intent.client_order_id}-{tick.sequence}",)
            if filled > 0
            else ()
        )
        return ExecutionReceipt(
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
        receipt = ExecutionReceipt(
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
        self._journal.append(
            "order_accepted",
            {
                "client_order_id": intent.client_order_id,
                "approved_volume": intent.approved_volume,
            },
            authority_time,
            intent.source_intent_id,
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
            costs = self._ledger.apply_fill(
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
        receipt_status: ReceiptStatus = match.status
        receipt = self._receipt(
            intent,
            receipt_status,
            match.filled_quantity,
            match.execution_price,
            tick,
        )
        self._journal.append(
            "order_outcome",
            receipt.model_dump(mode="python", warnings=False),
            tick.timestamp,
            intent.source_intent_id,
        )
        self._orders[intent.client_order_id] = receipt
        self._deals.append(receipt)
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
            movement = (
                tick.bid - entry if side == "BUY" else entry - tick.ask
            ) * volume
            position["mae"] = min(Decimal(str(position["mae"])), movement)
            position["mfe"] = max(Decimal(str(position["mfe"])), movement)
            unrealized += movement
        self._ledger.mark_to_market(unrealized)

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
        gross_profit = (
            exit_price - entry_price if side == "BUY" else entry_price - exit_price
        ) * quantity
        account = self._ledger.snapshot()
        used_margin = Decimal(str(account["used_margin"]))
        margin_released = used_margin * quantity / current_volume
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
        )
        costs = self._ledger.apply_fill(
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
        return MappingProxyType(
            {
                "position_id": position_id,
                "quantity": quantity,
                "exit_price": exit_price,
                "gross_profit": gross_profit,
                "exit_reason": exit_reason,
                "closed_at": tick.timestamp,
            }
        )

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
            self._close(
                position_id,
                Decimal(str(position["volume"])),
                tick,
                exit_reason,
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
        logger.info("Executing Simulation tick %s", tick.sequence)
        if self._last_seen is not None and (
            tick.timestamp <= self._last_seen.timestamp
            or tick.sequence <= self._last_seen.sequence
        ):
            raise SimulationError(
                "SIM_DATA_NON_MONOTONIC", "Execution tick is not strictly ordered"
            )
        self._last_seen = tick
        week_second = _week_second(tick)
        if not any(
            session.start_week_second <= week_second < session.end_week_second
            for session in self._profile.sessions
        ):
            logger.info("Skipping Simulation tick outside configured sessions")
            self._journal.append(
                "tick_outside_session",
                {"sequence": tick.sequence, "symbol": tick.symbol},
                tick.timestamp,
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
            del self._pending[order_id]
        return tuple(outcomes)

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

    def snapshot(self) -> Mapping[str, object]:
        """Return immutable engine and account state.

        Returns:
            Deeply immutable state projection.
        """
        logger.debug("Creating immutable Simulation engine snapshot")
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
                "account": self._ledger.snapshot(),
            }
        )


__all__ = ["EventDrivenExecutionEngine"]
