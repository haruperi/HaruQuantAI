"""Calibration admission and component sampling evidence."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.simulator import (
    admit_calibrated_realism,
    create_realism_stream,
    create_simulation_scheduler,
    dump_calibration_artifact,
    fit_execution_calibration,
    fit_spread_calibration,
    get_simulation_scheduler_state,
    partition_calibration_evidence,
    sample_calibrated_realism,
    schedule_calibrated_realism_event,
)

NOW = datetime(2025, 1, 10, tzinfo=UTC)
SOURCE = "a" * 64
COMPONENTS = (
    "spread",
    "latency",
    "slippage",
    "queue_position",
    "partial_fill",
    "requote",
)


def _evidence() -> list[dict[str, object]]:
    """Return sufficient trace evidence for every admitted test component."""
    result: list[dict[str, object]] = []
    for index in range(600):
        component = COMPONENTS[index % len(COMPONENTS)]
        instant = NOW - timedelta(days=2, seconds=index)
        result.append(
            {
                "evidence_id": f"realism-{index:04d}",
                "component": component,
                "value": Decimal(index % 9 + 1) / Decimal(10),
                "unit": "probability"
                if component in {"partial_fill", "requote"}
                else "points",
                "economic_at": instant,
                "available_at": instant,
                "ingested_at": instant,
                "source_checksum": SOURCE,
                "broker": "mt5",
                "server": "demo-server",
                "account_digest": "b" * 64,
                "environment": "demo",
                "symbol": "EURUSD",
                "regime": "scheduled_event" if index % 5 == 0 else "ordinary",
            }
        )
    return result


def _identity() -> dict[str, object]:
    """Return matching sanitized calibration identity."""
    return {
        "artifact_id": "realism-components-v1",
        "broker": "mt5",
        "server": "demo-server",
        "account_digest": "b" * 64,
        "environment": "demo",
        "symbol": "EURUSD",
        "source_identity": SOURCE,
        "source_available_at": NOW,
        "ingested_at": NOW,
        "calibrated_at": NOW,
    }


def _policy() -> dict[str, object]:
    """Return predeclared component conformance policy."""
    return {
        "effective_from": NOW,
        "effective_to": NOW + timedelta(days=30),
        "valid_until": NOW + timedelta(days=30),
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


def _artifacts() -> tuple[dict[str, object], dict[str, object]]:
    """Return spread and execution artifacts over one locked partition."""
    partitions = partition_calibration_evidence(
        _evidence(), evaluation_start=NOW, source_identity=SOURCE
    )
    spread = fit_spread_calibration(partitions, identity=_identity(), policy=_policy())
    execution = fit_execution_calibration(
        partitions,
        components=COMPONENTS[1:],
        identity=_identity(),
        policy=_policy(),
    )
    return dump_calibration_artifact(spread), dump_calibration_artifact(execution)


def test_all_evidenced_components_sample_with_artifact_and_stream_identity() -> None:
    """FR-SIM-171-175/178/228: admit and journal calibrated components only."""
    spread, execution = _artifacts()
    for component in COMPONENTS:
        artifact = spread if component == "spread" else execution
        admission = admit_calibrated_realism(
            artifact,
            component=component,
            environment="demo",
            symbol="EURUSD",
            as_of=NOW,
            canonical=True,
        )
        stream = create_realism_stream({"seed": 4, "symbol": "EURUSD"}, component)
        sampled = sample_calibrated_realism(admission, stream)
        assert sampled["component"] == component
        assert sampled["artifact_checksum"] == artifact["checksum"]
        assert sampled["journal_event_type"] == "calibrated_realism_sample"


def test_uncalibrated_pathwise_queue_and_exploratory_prior_fail_canonical() -> None:
    """FR-SIM-174/177/228: forbidden queue and priors fail canonical admission."""
    _spread, execution = _artifacts()
    with pytest.raises(ValueError, match="Level-2"):
        admit_calibrated_realism(
            execution,
            component="queue_position_pathwise",
            environment="demo",
            symbol="EURUSD",
            as_of=NOW,
            canonical=True,
        )
    tampered = dict(execution)
    applicability = dict(tampered["applicability"])  # type: ignore[arg-type]
    applicability["canonical_eligible"] = "false"
    tampered["applicability"] = applicability
    with pytest.raises(ValueError, match="checksum mismatch"):
        admit_calibrated_realism(
            tampered,
            component="latency",
            environment="demo",
            symbol="EURUSD",
            as_of=NOW,
            canonical=True,
        )


def test_calibrated_sample_is_scheduled_with_complete_evidence() -> None:
    """FR-SIM-171-178: calibrated samples enter deterministic scheduler order."""
    spread, _execution = _artifacts()
    admission = admit_calibrated_realism(
        spread,
        component="spread",
        environment="demo",
        symbol="EURUSD",
        as_of=NOW,
        canonical=True,
    )
    stream = create_realism_stream({"seed": 4, "symbol": "EURUSD"}, "spread")
    sampled = sample_calibrated_realism(admission, stream)
    scheduler = create_simulation_scheduler(NOW, {"realism": lambda value: value})
    event_id = schedule_calibrated_realism_event(
        scheduler,
        sampled=sampled,
        scheduled_at=NOW,
        canonical_symbol="EURUSD",
        source_sequence=1,
        handler_id="realism",
    )
    state = get_simulation_scheduler_state(scheduler)
    event = state["events"][0]  # type: ignore[index]
    assert event["event_id"] == event_id
    assert event["priority"] == "match_evaluation"
    assert event["payload"]["artifact_checksum"] == spread["checksum"]
