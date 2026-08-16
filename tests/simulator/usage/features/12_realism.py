"""Standalone usage for FEAT-SIM-12 execution realism."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    admit_calibrated_realism,
    build_fill_model_provider,
    build_latency_profile,
    build_queue_model,
    build_seeded_fault_event,
    create_realism_stream,
    dump_calibration_artifact,
    fit_execution_calibration,
    fit_spread_calibration,
    get_realism_performance_budgets,
    get_realism_stream_identity,
    partition_calibration_evidence,
    price_realistic_execution,
    project_execution_views,
    project_latency_timestamps,
    resolve_cancel_replace_race,
    sample_calibrated_realism,
    simulate_queue_fill,
)

_NOW = datetime(2025, 1, 10, tzinfo=UTC)
_SOURCE = "a" * 64
_COMPONENTS = (
    "spread",
    "latency",
    "slippage",
    "queue_position",
    "partial_fill",
    "requote",
)


def _calibration(component: str) -> dict[str, object]:
    """Build one bounded checksummed demo calibration artifact."""
    evidence = []
    for index in range(600):
        observed_component = _COMPONENTS[index % len(_COMPONENTS)]
        instant = _NOW - timedelta(days=2, seconds=index)
        evidence.append(
            {
                "evidence_id": f"usage-realism-{index:04d}",
                "component": observed_component,
                "value": Decimal(index % 9 + 1) / Decimal(10),
                "unit": "probability"
                if observed_component in {"partial_fill", "requote"}
                else "points",
                "economic_at": instant,
                "available_at": instant,
                "ingested_at": instant,
                "source_checksum": _SOURCE,
                "broker": "mt5",
                "server": "demo-server",
                "account_digest": "b" * 64,
                "environment": "demo",
                "symbol": "EURUSD",
                "regime": "scheduled_event" if index % 5 == 0 else "ordinary",
            }
        )
    partitions = partition_calibration_evidence(
        evidence, evaluation_start=_NOW, source_identity=_SOURCE
    )
    identity = {
        "artifact_id": "usage-realism-v1",
        "broker": "mt5",
        "server": "demo-server",
        "account_digest": "b" * 64,
        "environment": "demo",
        "symbol": "EURUSD",
        "source_identity": _SOURCE,
        "source_available_at": _NOW,
        "ingested_at": _NOW,
        "calibrated_at": _NOW,
    }
    policy = {
        "effective_from": _NOW,
        "effective_to": _NOW + timedelta(days=30),
        "valid_until": _NOW + timedelta(days=30),
        "minimum_samples": 3,
        "minimum_coverage": Decimal("0.95"),
        "observed_coverage": Decimal(1),
        "threshold_metric": "mean_absolute_error",
        "threshold_unit": "points",
        "threshold_test": "mae_lte",
        "threshold_tolerance": Decimal(10),
        "confidence": Decimal("0.95"),
        "economic_error_budget": Decimal(10),
    }
    artifact = (
        fit_spread_calibration(partitions, identity=identity, policy=policy)
        if component == "spread"
        else fit_execution_calibration(
            partitions,
            components=_COMPONENTS[1:],
            identity=identity,
            policy=policy,
        )
    )
    return dump_calibration_artifact(artifact)


def _sample(component: str) -> object:
    """Sample one admitted component through package-root APIs."""
    admission = admit_calibrated_realism(
        _calibration(component),
        component=component,
        environment="demo",
        symbol="EURUSD",
        as_of=_NOW,
        canonical=True,
    )
    stream = create_realism_stream({"seed": 17, "symbol": "EURUSD"}, component)
    return sample_calibrated_realism(admission, stream)


def _latency() -> object:
    """Build one bounded latency profile."""
    return build_latency_profile(network_ms=Decimal(2), venue_ms=Decimal(3))


def fr_sim_118() -> None:
    """FR-SIM-118: Simulator shall validate non-negative deterministic market, client, network, broker, venue, report, and processing latency and project their complete causal timestamp chain."""
    projected = project_latency_timestamps(datetime.now(UTC), _latency())
    print(f"SUCCESS: FR-SIM-118 latency projected; Data -> {tuple(projected)}")


def fr_sim_119() -> None:
    """FR-SIM-119: Simulator shall model price level, order quantity, quantity ahead, cancellation rate, traded volume, remaining queue position, and bounded fill probability."""
    queue = build_queue_model(
        price=Decimal("1.1"),
        order_quantity=Decimal(2),
        quantity_ahead=Decimal(1),
        cancellation_rate=Decimal(0),
        maximum_fill_probability=Decimal(1),
    )
    result = simulate_queue_fill(queue, traded_volume=Decimal(2))
    print(f"SUCCESS: FR-SIM-119 queue modeled; Data -> fill={result.filled_quantity}")


def fr_sim_120() -> None:
    """FR-SIM-120: Simulator shall calculate finite Decimal adverse slippage and linear market impact within an explicit maximum movement ceiling."""
    result = price_realistic_execution(
        side="BUY",
        base_price=Decimal("1.1"),
        quantity=Decimal(2),
        point_value=Decimal("0.0001"),
        price_quantum=Decimal("0.00001"),
        fixed_slippage_points=Decimal(1),
        impact_points_per_unit=Decimal("0.5"),
        maximum_total_points=Decimal(3),
        latency=_latency(),
    )
    print(f"SUCCESS: FR-SIM-120 price modeled; Data -> {result.execution_price}")


def fr_sim_121() -> None:
    """FR-SIM-121: Simulator shall resolve cancel, replace, and fill races by aware venue timestamps with an explicit fill-before-cancel-before-replace tie priority."""
    now = datetime.now(UTC)
    result = resolve_cancel_replace_race(fill_at=now, cancel_at=now, replace_at=None)
    print(f"SUCCESS: FR-SIM-121 race resolved; Data -> {result['winner']}")


def fr_sim_122() -> None:
    """FR-SIM-122: Simulator shall separate venue-effective state from player-perceived state and expose no event before its perception timestamp."""
    now = datetime.now(UTC)
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
    print(
        f"SUCCESS: FR-SIM-122 views separated; Data -> venue={len(views['venue'])}, player={len(views['player'])}"
    )


def fr_sim_123() -> None:
    """FR-SIM-123: Simulator shall provide explicit instrument and market-data-bound fill-model calibration evidence to Optimization without inferred defaults."""
    provider = build_fill_model_provider(
        {"EURUSD": {"market_data_ref": "dataset-usage", "latency_ms": 5}}
    )
    evidence = provider.fill_model_calibration(
        market_data_ref="dataset-usage", instrument="EURUSD"
    )
    print(f"SUCCESS: FR-SIM-123 provider built; Data -> {evidence['status']}")


def fr_sim_171() -> None:
    """FR-SIM-171: sample calibrated latency."""
    print(f"SUCCESS: FR-SIM-171 Data -> {_sample('latency')}")


def fr_sim_172() -> None:
    """FR-SIM-172: sample calibrated spread."""
    print(f"SUCCESS: FR-SIM-172 Data -> {_sample('spread')}")


def fr_sim_173() -> None:
    """FR-SIM-173: sample calibrated slippage."""
    print(f"SUCCESS: FR-SIM-173 Data -> {_sample('slippage')}")


def fr_sim_174() -> None:
    """FR-SIM-174: sample trace-calibrated queue and partial-fill outcomes."""
    print(
        "SUCCESS: FR-SIM-174 Data ->",
        _sample("queue_position"),
        _sample("partial_fill"),
    )


def fr_sim_175() -> None:
    """FR-SIM-175: sample calibrated requote behavior."""
    print(f"SUCCESS: FR-SIM-175 Data -> {_sample('requote')}")


def fr_sim_176() -> None:
    """FR-SIM-176: publish pinned concern-stream identity."""
    print(f"SUCCESS: FR-SIM-176 Data -> {get_realism_stream_identity()}")


def fr_sim_177() -> None:
    """FR-SIM-177: retain exact point-in-time canonical applicability."""
    print(f"SUCCESS: FR-SIM-177 canonical={_sample('latency')['canonical']}")  # type: ignore[index]


def fr_sim_178() -> None:
    """FR-SIM-178: disclose artifact, stream draw, and journal event identity."""
    print(f"SUCCESS: FR-SIM-178 Data -> {_sample('spread')}")


def fr_sim_228() -> None:
    """FR-SIM-228: admit only applicable calibrated canonical realism."""
    print(f"SUCCESS: FR-SIM-228 Data -> {_sample('latency')}")


def fr_sim_229() -> None:
    """FR-SIM-229: create seeded faults only through the scenario engine."""
    event = build_seeded_fault_event(
        stream=create_realism_stream({"seed": 17}, "fault"),
        fault_type="timeout",
        probability=Decimal(1),
        occurred_at=_NOW,
        artifact_checksum="a" * 64,
    )
    print(
        f"SUCCESS: FR-SIM-229 Data -> {event.event_type if event else 'not_triggered'}"
    )


def fr_sim_241() -> None:
    """FR-SIM-241: publish the enforced annual and multi-symbol budgets."""
    print(f"SUCCESS: FR-SIM-241 Data -> {get_realism_performance_budgets()}")


def main() -> None:
    """Run every FEAT-SIM-12 requirement demonstration."""
    print("FEATURE: FEAT-SIM-12 — Execution Realism Models")
    fr_sim_118()
    fr_sim_119()
    fr_sim_120()
    fr_sim_121()
    fr_sim_122()
    fr_sim_123()
    fr_sim_171()
    fr_sim_172()
    fr_sim_173()
    fr_sim_174()
    fr_sim_175()
    fr_sim_176()
    fr_sim_177()
    fr_sim_178()
    fr_sim_228()
    fr_sim_229()
    fr_sim_241()


if __name__ == "__main__":
    main()
