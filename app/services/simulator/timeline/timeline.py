"""Construction and no-lookahead validation for the Simulation tick clock."""

from __future__ import annotations

from datetime import datetime

from app.services.data.contracts import (
    MarketDataset,
    TickRecord,
)
from app.services.simulator.errors import SimulationError
from app.services.simulator.timeline.contracts import Tick
from app.utils import logger

APPROVED_TICK_MODELS = ("real", "trading_bar", "ohlc_m1", "generated")


def build_tick_timeline(tick_dataset: MarketDataset) -> tuple[Tick, ...]:
    """Convert Data-owned tick evidence into the immutable execution clock.

    Args:
        tick_dataset: Dataset returned by Data ``generate_tick_series``.

    Returns:
        Strictly ordered immutable ticks.

    Raises:
        SimulationError: If the dataset is not approved tick evidence.
    """
    logger.info("Building Simulation tick timeline for %s", tick_dataset.symbol)
    model = tick_dataset.source_metadata.get("tick_generation_model")
    if tick_dataset.data_kind != "ticks" or model not in APPROVED_TICK_MODELS:
        raise SimulationError(
            "SIM_UNSUPPORTED_TICK_MODEL",
            "Dataset was not produced by an approved Data tick model",
            request_id=tick_dataset.request_id,
        )
    timeline: list[Tick] = []
    for sequence, record in enumerate(tick_dataset.records):
        if not isinstance(record, TickRecord):
            raise SimulationError(
                "SIM_DATA_SCHEMA_INVALID",
                "Tick dataset contains a non-tick record",
                request_id=tick_dataset.request_id,
            )
        if record.bid is None or record.ask is None:
            raise SimulationError(
                "SIM_SPREAD_MISSING",
                "Official execution requires genuine bid and ask",
                request_id=tick_dataset.request_id,
            )
        if model != "real" and (
            record.source_bar_time is None
            or record.tick_index_in_bar is None
            or record.bar_phase is None
        ):
            raise SimulationError(
                "SIM_DATA_SCHEMA_INVALID",
                "Derived tick is missing intra-bar evidence",
                request_id=tick_dataset.request_id,
            )
        try:
            tick = Tick(
                symbol=tick_dataset.symbol,
                timestamp=record.timestamp,
                bid=record.bid,
                ask=record.ask,
                source_id=record.source,
                sequence=sequence,
                available_at=record.available_at,
                volume=record.volume,
                volume_unit=record.volume_unit,
                source_bar_time=record.source_bar_time,
                tick_index_in_bar=record.tick_index_in_bar,
                bar_phase=record.bar_phase,
            )
        except ValueError as error:
            logger.warning("Simulation rejected invalid tick %s", sequence)
            raise SimulationError(
                "SIM_INVALID_PRICE",
                "Tick price evidence is invalid",
                request_id=tick_dataset.request_id,
            ) from error
        timeline.append(tick)
    timestamps = tuple(tick.timestamp for tick in timeline)
    if timestamps != tuple(sorted(timestamps)):
        raise SimulationError(
            "SIM_DATA_NON_MONOTONIC",
            "Tick timeline is not monotonic",
            request_id=tick_dataset.request_id,
        )
    if len(set(timestamps)) != len(timestamps):
        raise SimulationError(
            "SIM_DATA_DUPLICATE_TIMESTAMP",
            "Tick timeline timestamps are not unique",
            request_id=tick_dataset.request_id,
        )
    return tuple(timeline)


def validate_intent_timing(
    intent_available_at: datetime,
    execution_time: datetime,
) -> None:
    """Reject intent evidence unavailable at the execution timestamp.

    Args:
        intent_available_at: UTC time all strategy evidence became available.
        execution_time: UTC tick time considered for execution.

    Raises:
        SimulationError: If either time is invalid or evidence looks ahead.
    """
    logger.debug("Validating Simulation intent timing")
    for value in (intent_available_at, execution_time):
        if value.tzinfo is None or value.utcoffset() is None:
            raise SimulationError(
                "SIM_INVALID_CONFIG", "Intent timing must be aware UTC"
            )
    if intent_available_at > execution_time:
        raise SimulationError(
            "SIM_FEATURE_LOOKAHEAD_DETECTED",
            "Strategy feature evidence was unavailable at execution time",
        )


__all__ = ["APPROVED_TICK_MODELS", "build_tick_timeline", "validate_intent_timing"]
