"""State snapshot comparison logic for trading reconciliation.

Compares local TradeStore state projections (orders, positions, balance, margin)
against broker snapshots using dynamically configured drift thresholds.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.trading.execution.reporting import ReconciliationDiscrepancyEntry
from app.services.trading.execution.state_machine import LifecycleKind
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.trading.contracts import JsonObject
    from app.services.trading.state.ports import Clock

_STATE_STR_MAP = {
    "NEW": "NEW",
    "SUBMITTED": "NEW",
    "STARTED": "NEW",
    "PLACED": "NEW",
    "REQUEST SENT": "NEW",
    "PARTIAL": "PARTIALLY_FILLED",
    "PARTIALLY_FILLED": "PARTIALLY_FILLED",
    "FILLED": "FILLED",
    "CANCELED": "CANCELLED",
    "CANCELLED": "CANCELLED",
    "REQUEST CANCELLED": "CANCELLED",
    "REJECTED": "REJECTED",
    "EXPIRED": "EXPIRED",
}

_STATE_INT_MAP = {
    0: "NEW",  # Started
    1: "NEW",  # Placed
    7: "NEW",  # Request Sent
    3: "PARTIALLY_FILLED",  # Partial
    4: "FILLED",  # Filled
    2: "CANCELLED",  # Canceled
    8: "CANCELLED",  # Request Cancelled
    5: "REJECTED",  # Rejected
    6: "EXPIRED",  # Expired
}


def _map_broker_order_state(state_val: object) -> str:
    """Map broker order state values to canonical FixExecutionState strings.

    Args:
        state_val: Raw broker order state.

    Returns:
        str: Mapped canonical state name.
    """
    if isinstance(state_val, str):
        return _STATE_STR_MAP.get(state_val.upper(), "UNKNOWN")
    if isinstance(state_val, (int, float)):
        return _STATE_INT_MAP.get(int(state_val), "UNKNOWN")
    return "UNKNOWN"


def _compare_balance(
    *,
    local_balance: Decimal,
    broker_balance: Decimal,
    balance_drift_threshold: Decimal,
    detected_at: str,
) -> ReconciliationDiscrepancyEntry | None:
    """Compare local vs broker balance.

    Args:
        local_balance: Local balance.
        broker_balance: Broker balance.
        balance_drift_threshold: Threshold.
        detected_at: Timestamp.

    Returns:
        ReconciliationDiscrepancyEntry | None: Discrepancy if detected.
    """
    balance_drift = abs(local_balance - broker_balance)
    if balance_drift > balance_drift_threshold:
        logger.warning(
            "Balance mismatch: local={}, broker={}, drift={}.",
            local_balance,
            broker_balance,
            balance_drift,
        )
        return ReconciliationDiscrepancyEntry(
            entity_id="balance",
            kind=LifecycleKind.POSITION,
            discrepancy_type="balance_mismatch",
            local_value=str(local_balance),
            broker_value=str(broker_balance),
            detected_at=detected_at,
        )
    return None


def _compare_margin(
    *,
    local_margin: Decimal,
    broker_margin: Decimal,
    margin_drift_threshold: Decimal,
    detected_at: str,
) -> ReconciliationDiscrepancyEntry | None:
    """Compare local vs broker margin.

    Args:
        local_margin: Local margin.
        broker_margin: Broker margin.
        margin_drift_threshold: Threshold.
        detected_at: Timestamp.

    Returns:
        ReconciliationDiscrepancyEntry | None: Discrepancy if detected.
    """
    margin_drift = abs(local_margin - broker_margin)
    if margin_drift > margin_drift_threshold:
        logger.warning(
            "Margin mismatch: local={}, broker={}, drift={}.",
            local_margin,
            broker_margin,
            margin_drift,
        )
        return ReconciliationDiscrepancyEntry(
            entity_id="margin",
            kind=LifecycleKind.POSITION,
            discrepancy_type="margin_mismatch",
            local_value=str(local_margin),
            broker_value=str(broker_margin),
            detected_at=detected_at,
        )
    return None


def _compare_single_order(
    order_id: str,
    local_o: JsonObject,
    broker_o: JsonObject,
    price_drift_threshold: Decimal,
    volume_drift_threshold: Decimal,
    detected_at: str,
) -> list[ReconciliationDiscrepancyEntry]:
    """Compare a matched order's properties.

    Args:
        order_id: Local order ID.
        local_o: Local order state.
        broker_o: Broker order state.
        price_drift_threshold: Price threshold.
        volume_drift_threshold: Volume threshold.
        detected_at: Timestamp.

    Returns:
        list[ReconciliationDiscrepancyEntry]: Detected discrepancies.
    """
    order_discrepancies: list[ReconciliationDiscrepancyEntry] = []

    # Compare remaining volume
    local_vol = Decimal(
        str(local_o.get("remaining_volume", local_o.get("volume_current", 0.0)))
    )
    broker_vol = Decimal(
        str(
            broker_o.get(
                "volume_current",
                broker_o.get("volume_initial", broker_o.get("volume", 0.0)),
            )
        )
    )
    if abs(local_vol - broker_vol) > volume_drift_threshold:
        order_discrepancies.append(
            ReconciliationDiscrepancyEntry(
                entity_id=order_id,
                kind=LifecycleKind.ORDER,
                discrepancy_type="volume_mismatch",
                local_value=str(local_vol),
                broker_value=str(broker_vol),
                detected_at=detected_at,
            )
        )

    # Compare price/VWAP
    local_price_val = local_o.get("vwap") or local_o.get("price")
    local_price = (
        Decimal(str(local_price_val)) if local_price_val is not None else Decimal(0)
    )
    broker_price_val = broker_o.get("price") or broker_o.get("price_open")
    broker_price = (
        Decimal(str(broker_price_val)) if broker_price_val is not None else Decimal(0)
    )

    if (
        local_price_val is not None
        and broker_price_val is not None
        and abs(local_price - broker_price) > price_drift_threshold
    ):
        order_discrepancies.append(
            ReconciliationDiscrepancyEntry(
                entity_id=order_id,
                kind=LifecycleKind.ORDER,
                discrepancy_type="price_mismatch",
                local_value=str(local_price),
                broker_value=str(broker_price),
                detected_at=detected_at,
            )
        )

    # Compare state
    local_state = str(local_o.get("state", "")).upper()
    broker_state_raw = broker_o.get("state", "")
    broker_state = _map_broker_order_state(broker_state_raw)
    if local_state != broker_state:
        order_discrepancies.append(
            ReconciliationDiscrepancyEntry(
                entity_id=order_id,
                kind=LifecycleKind.ORDER,
                discrepancy_type="state_mismatch",
                local_value=local_state,
                broker_value=broker_state,
                detected_at=detected_at,
            )
        )

    return order_discrepancies


def _compare_orders(
    local_orders: list[JsonObject],
    broker_orders: list[JsonObject],
    price_drift_threshold: Decimal,
    volume_drift_threshold: Decimal,
    detected_at: str,
) -> list[ReconciliationDiscrepancyEntry]:
    """Compare all orders between local projections and broker snapshots.

    Args:
        local_orders: Local orders.
        broker_orders: Broker orders.
        price_drift_threshold: Price threshold.
        volume_drift_threshold: Volume threshold.
        detected_at: Timestamp.

    Returns:
        list[ReconciliationDiscrepancyEntry]: Detected discrepancies.
    """
    order_discrepancies: list[ReconciliationDiscrepancyEntry] = []

    broker_orders_by_id: dict[str, JsonObject] = {}
    for o in broker_orders:
        ticket = str(o.get("ticket", ""))
        if ticket:
            broker_orders_by_id[ticket] = o

    local_orders_by_id: dict[str, JsonObject] = {}
    for o in local_orders:
        order_id = str(o.get("order_id", o.get("ticket", "")))
        if order_id:
            local_orders_by_id[order_id] = o

    for order_id, local_o in local_orders_by_id.items():
        state_str = str(local_o.get("state", "")).upper()
        if state_str in ("FILLED", "CANCELLED", "REJECTED", "EXPIRED"):
            continue

        if order_id not in broker_orders_by_id:
            logger.warning("Order {} missing at broker.", order_id)
            order_discrepancies.append(
                ReconciliationDiscrepancyEntry(
                    entity_id=order_id,
                    kind=LifecycleKind.ORDER,
                    discrepancy_type="missing_at_broker",
                    local_value=str(local_o),
                    broker_value="",
                    detected_at=detected_at,
                )
            )
        else:
            broker_o = broker_orders_by_id[order_id]
            order_discrepancies.extend(
                _compare_single_order(
                    order_id,
                    local_o,
                    broker_o,
                    price_drift_threshold,
                    volume_drift_threshold,
                    detected_at,
                )
            )

    for ticket, broker_o in broker_orders_by_id.items():
        if ticket not in local_orders_by_id:
            logger.warning("Broker order {} missing locally.", ticket)
            order_discrepancies.append(
                ReconciliationDiscrepancyEntry(
                    entity_id=ticket,
                    kind=LifecycleKind.ORDER,
                    discrepancy_type="missing_locally",
                    local_value="",
                    broker_value=str(broker_o),
                    detected_at=detected_at,
                )
            )

    return order_discrepancies


def _compare_single_position(
    pos_id: str,
    local_p: JsonObject,
    broker_p: JsonObject,
    price_drift_threshold: Decimal,
    volume_drift_threshold: Decimal,
    detected_at: str,
) -> list[ReconciliationDiscrepancyEntry]:
    """Compare properties of a matched position.

    Args:
        pos_id: Position ID.
        local_p: Local position state.
        broker_p: Broker position state.
        price_drift_threshold: Price threshold.
        volume_drift_threshold: Volume threshold.
        detected_at: Timestamp.

    Returns:
        list[ReconciliationDiscrepancyEntry]: Detected discrepancies.
    """
    pos_discrepancies: list[ReconciliationDiscrepancyEntry] = []

    # Compare volume
    local_vol = Decimal(str(local_p.get("volume", 0.0)))
    broker_vol = Decimal(str(broker_p.get("volume", 0.0)))
    if abs(local_vol - broker_vol) > volume_drift_threshold:
        pos_discrepancies.append(
            ReconciliationDiscrepancyEntry(
                entity_id=pos_id,
                kind=LifecycleKind.POSITION,
                discrepancy_type="volume_mismatch",
                local_value=str(local_vol),
                broker_value=str(broker_vol),
                detected_at=detected_at,
            )
        )

    # Compare VWAP / entry price
    local_vwap_val = local_p.get("vwap") or local_p.get("price_open")
    local_vwap = (
        Decimal(str(local_vwap_val)) if local_vwap_val is not None else Decimal(0)
    )
    broker_vwap_val = broker_p.get("vwap") or broker_p.get("price_open")
    broker_vwap = (
        Decimal(str(broker_vwap_val)) if broker_vwap_val is not None else Decimal(0)
    )

    if (
        local_vwap_val is not None
        and broker_vwap_val is not None
        and abs(local_vwap - broker_vwap) > price_drift_threshold
    ):
        pos_discrepancies.append(
            ReconciliationDiscrepancyEntry(
                entity_id=pos_id,
                kind=LifecycleKind.POSITION,
                discrepancy_type="vwap_mismatch",
                local_value=str(local_vwap),
                broker_value=str(broker_vwap),
                detected_at=detected_at,
            )
        )

    return pos_discrepancies


def _compare_positions(
    local_positions: list[JsonObject],
    broker_positions: list[JsonObject],
    price_drift_threshold: Decimal,
    volume_drift_threshold: Decimal,
    detected_at: str,
) -> list[ReconciliationDiscrepancyEntry]:
    """Compare all positions between local projections and broker snapshots.

    Args:
        local_positions: Local positions.
        broker_positions: Broker positions.
        price_drift_threshold: Price threshold.
        volume_drift_threshold: Volume threshold.
        detected_at: Timestamp.

    Returns:
        list[ReconciliationDiscrepancyEntry]: Detected discrepancies.
    """
    pos_discrepancies: list[ReconciliationDiscrepancyEntry] = []

    broker_positions_by_id: dict[str, JsonObject] = {}
    for p in broker_positions:
        pos_id = str(p.get("position_id", p.get("ticket", p.get("symbol", ""))))
        if pos_id:
            broker_positions_by_id[pos_id] = p

    local_positions_by_id: dict[str, JsonObject] = {}
    for p in local_positions:
        pos_id = str(p.get("position_id", p.get("ticket", p.get("symbol", ""))))
        if pos_id:
            local_positions_by_id[pos_id] = p

    for pos_id, local_p in local_positions_by_id.items():
        if pos_id not in broker_positions_by_id:
            logger.warning("Position {} missing at broker.", pos_id)
            pos_discrepancies.append(
                ReconciliationDiscrepancyEntry(
                    entity_id=pos_id,
                    kind=LifecycleKind.POSITION,
                    discrepancy_type="missing_at_broker",
                    local_value=str(local_p),
                    broker_value="",
                    detected_at=detected_at,
                )
            )
        else:
            broker_p = broker_positions_by_id[pos_id]
            pos_discrepancies.extend(
                _compare_single_position(
                    pos_id,
                    local_p,
                    broker_p,
                    price_drift_threshold,
                    volume_drift_threshold,
                    detected_at,
                )
            )

    for pos_id, broker_p in broker_positions_by_id.items():
        if pos_id not in local_positions_by_id:
            logger.warning("Broker position {} missing locally.", pos_id)
            pos_discrepancies.append(
                ReconciliationDiscrepancyEntry(
                    entity_id=pos_id,
                    kind=LifecycleKind.POSITION,
                    discrepancy_type="missing_locally",
                    local_value="",
                    broker_value=str(broker_p),
                    detected_at=detected_at,
                )
            )

    return pos_discrepancies


def compare_snapshots(
    *,
    local_orders: list[JsonObject],
    broker_orders: list[JsonObject],
    local_positions: list[JsonObject],
    broker_positions: list[JsonObject],
    local_balance: Decimal,
    broker_balance: Decimal,
    local_margin: Decimal,
    broker_margin: Decimal,
    price_drift_threshold: Decimal,
    volume_drift_threshold: Decimal,
    balance_drift_threshold: Decimal,
    margin_drift_threshold: Decimal,
    clock: Clock,
) -> list[ReconciliationDiscrepancyEntry]:
    """Compare local states against broker snapshots.

    Args:
        local_orders: Local order state projections.
        broker_orders: Broker active orders.
        local_positions: Local position state projections.
        broker_positions: Broker open positions.
        local_balance: Local account balance.
        broker_balance: Broker account balance.
        local_margin: Local account margin.
        broker_margin: Broker account margin.
        price_drift_threshold: Absolute price/VWAP drift threshold.
        volume_drift_threshold: Absolute volume drift threshold.
        balance_drift_threshold: Absolute balance drift threshold.
        margin_drift_threshold: Absolute margin drift threshold.
        clock: Injected clock.

    Returns:
        list[ReconciliationDiscrepancyEntry]: Detected discrepancies.
    """
    logger.info("Comparing local state against broker snapshots.")
    discrepancies: list[ReconciliationDiscrepancyEntry] = []
    detected_at = clock.now_utc().isoformat()

    # 1. Compare balance
    bal_disc = _compare_balance(
        local_balance=local_balance,
        broker_balance=broker_balance,
        balance_drift_threshold=balance_drift_threshold,
        detected_at=detected_at,
    )
    if bal_disc is not None:
        discrepancies.append(bal_disc)

    # 2. Compare margin
    mar_disc = _compare_margin(
        local_margin=local_margin,
        broker_margin=broker_margin,
        margin_drift_threshold=margin_drift_threshold,
        detected_at=detected_at,
    )
    if mar_disc is not None:
        discrepancies.append(mar_disc)

    # 3. Compare orders
    order_discs = _compare_orders(
        local_orders=local_orders,
        broker_orders=broker_orders,
        price_drift_threshold=price_drift_threshold,
        volume_drift_threshold=volume_drift_threshold,
        detected_at=detected_at,
    )
    discrepancies.extend(order_discs)

    # 4. Compare positions
    pos_discs = _compare_positions(
        local_positions=local_positions,
        broker_positions=broker_positions,
        price_drift_threshold=price_drift_threshold,
        volume_drift_threshold=volume_drift_threshold,
        detected_at=detected_at,
    )
    discrepancies.extend(pos_discs)

    return discrepancies
