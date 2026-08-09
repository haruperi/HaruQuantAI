"""Unit evidence for FEAT-SIM-12 execution realism."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.simulator import (
    build_fill_model_provider,
    build_latency_profile,
    build_queue_model,
    price_realistic_execution,
    project_execution_views,
    project_latency_timestamps,
    resolve_cancel_replace_race,
    simulate_queue_fill,
)


def test_latency_queue_and_price_models_are_deterministic() -> None:
    """Project causal latency, queue position, and adverse execution price."""
    latency = build_latency_profile(network_ms=Decimal(2), venue_ms=Decimal(3))
    now = datetime.now(UTC)
    projected = project_latency_timestamps(now, latency)
    assert projected["venue"] > projected["market"]
    queue = build_queue_model(
        price=Decimal("1.1000"),
        order_quantity=Decimal(2),
        quantity_ahead=Decimal(1),
        cancellation_rate=Decimal(0),
        maximum_fill_probability=Decimal(1),
    )
    fill = simulate_queue_fill(queue, traded_volume=Decimal(2))
    assert fill.filled_quantity == Decimal(1)
    result = price_realistic_execution(
        side="BUY",
        base_price=Decimal("1.1000"),
        quantity=Decimal(2),
        point_value=Decimal("0.0001"),
        price_quantum=Decimal("0.00001"),
        fixed_slippage_points=Decimal(1),
        impact_points_per_unit=Decimal("0.5"),
        maximum_total_points=Decimal(3),
        latency=latency,
    )
    assert result.execution_price == Decimal("1.10020")


def test_race_and_view_projection_prevent_future_leakage() -> None:
    """Prefer a simultaneous fill and hide unperceived venue events."""
    now = datetime.now(UTC)
    race = resolve_cancel_replace_race(fill_at=now, cancel_at=now, replace_at=None)
    assert race["winner"] == "FILL"
    views = project_execution_views(
        (
            {
                "event_id": "e",
                "venue_at": now,
                "perceived_at": now + timedelta(seconds=1),
            },
        ),
        as_of=now,
    )
    assert len(views["venue"]) == 1
    assert views["player"] == ()


def test_fill_provider_requires_exact_market_evidence() -> None:
    """Return calibration only for the declared data reference."""
    provider = build_fill_model_provider(
        {"EURUSD": {"market_data_ref": "dataset-1", "latency_ms": 4}}
    )
    assert (
        provider.fill_model_calibration(
            market_data_ref="dataset-1", instrument="EURUSD"
        )["status"]
        == "CALIBRATED"
    )
    assert (
        provider.fill_model_calibration(market_data_ref="other", instrument="EURUSD")[
            "status"
        ]
        == "NOT_CALIBRATED"
    )
