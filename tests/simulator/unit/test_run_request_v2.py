"""Unit evidence for Simulation backtest request V2 identity."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path

import pytest
from app.services.simulator import (
    calculate_simulation_backtest_v2_config_hash,
    create_simulation_value,
    dump_simulation_value,
    run_backtest,
    run_backtest_async,
    unwrap_simulation_response,
)

from tests.simulator.component.test_orchestrator import (
    FakeDependencies,
    _auth,
    _dataset,
    _request,
)


def _payload() -> dict[str, object]:
    """Return one valid bounded V2 request payload."""
    dataset = _dataset("req-55555555-5555-4555-8555-555555555555")
    payload = dict(_request(dataset).model_dump(mode="python", warnings=False))
    payload.pop("contract_version")
    payload.pop("schema_id")
    payload.pop("config_hash")
    payload.update(
        {
            "execution_model_ref": "execution-model-v1",
            "execution_model_hash": "e" * 64,
            "source_lineage_hash": "f" * 64,
            "tick_lineage_hash": "1" * 64,
            "market_evidence_class": "genuine_bid_ask_ticks",
            "decision_instant_policy": "point_in_time_available_at",
            "provider_specification_revisions": (
                {
                    "revision_id": "revision-1",
                    "checksum": "2" * 64,
                    "provider": "mt5",
                    "server": "demo-server",
                    "environment": "demo",
                    "account_digest": "3" * 64,
                    "symbol": "EURUSD",
                    "observed_at": dataset.start,
                    "effective_from": dataset.start,
                    "effective_to": None,
                    "historical_provenance": None,
                },
            ),
            "initial_authority_state_hash": "4" * 64,
            "certification_target": "demo",
            "close_open_positions_at_end": True,
        }
    )
    payload["config_hash"] = unwrap_simulation_response(
        calculate_simulation_backtest_v2_config_hash(payload),
        operation="test.request_v2.calculate_hash",
    )
    return payload


def _build(payload: dict[str, object] | None = None) -> object:
    """Build one opaque V2 request."""
    return create_simulation_value(
        "SimulationBacktestRequestV2", **(payload or _payload())
    )


def _rehash(payload: dict[str, object]) -> None:
    """Replace a payload's V2 configuration hash in place."""
    payload["config_hash"] = unwrap_simulation_response(
        calculate_simulation_backtest_v2_config_hash(payload),
        operation="test.request_v2.calculate_hash",
    )


def test_fr_sim_196_v2_binds_complete_execution_identity() -> None:
    """FR-SIM-196: V2 exposes all registered execution-identity fields."""
    result = dump_simulation_value(_build())
    assert result["contract_version"] == "v2"
    assert result["schema_id"] == "simulation.backtest_request.v2"
    assert result["decision_instant_policy"] == "point_in_time_available_at"


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("execution_model_ref", "execution-model-v2"),
        ("execution_model_hash", "5" * 64),
        ("source_lineage_hash", "6" * 64),
        ("tick_lineage_hash", "7" * 64),
        ("market_evidence_class", "depth_supported_ticks"),
        ("initial_authority_state_hash", "8" * 64),
        ("close_open_positions_at_end", False),
    ],
)
def test_fr_sim_232_233_234_execution_fields_change_hash(
    field: str, replacement: object
) -> None:
    """FR-SIM-232-234: every changed execution field changes the hash."""
    baseline = _payload()
    changed = dict(baseline)
    changed[field] = replacement
    _rehash(changed)
    assert changed["config_hash"] != baseline["config_hash"]
    _build(changed)


@pytest.mark.parametrize("field", ["request_id", "workflow_id", "correlation_id"])
def test_fr_sim_231_trace_identity_does_not_change_config_hash(field: str) -> None:
    """FR-SIM-231: trace fields remain outside configuration identity."""
    baseline = _payload()
    changed = dict(baseline)
    changed[field] = f"{field}-changed"
    _rehash(changed)
    assert changed["config_hash"] == baseline["config_hash"]


def test_fr_sim_234_demo_evidence_cannot_claim_live_target() -> None:
    """FR-SIM-234: demo revision evidence cannot be relabelled live."""
    payload = _payload()
    payload["certification_target"] = "live"
    _rehash(payload)
    with pytest.raises(Exception, match="relabelled"):
        _build(payload)


def test_fr_sim_231_policy_and_revision_material_change_hash() -> None:
    """FR-SIM-231: policy and provider revision material are hash-bound."""
    baseline = _payload()
    policy = dict(baseline)
    policy["decision_instant_policy"] = "future_visibility_forbidden"
    _rehash(policy)
    assert policy["config_hash"] != baseline["config_hash"]
    with pytest.raises(Exception, match="decision_instant_policy"):
        _build(policy)

    revision_changed = dict(baseline)
    revision = dict(baseline["provider_specification_revisions"][0])  # type: ignore[index]
    revision["checksum"] = "9" * 64
    revision_changed["provider_specification_revisions"] = (revision,)
    _rehash(revision_changed)
    assert revision_changed["config_hash"] != baseline["config_hash"]
    _build(revision_changed)


def test_fr_sim_232_missing_initial_authority_hash_fails_closed() -> None:
    """FR-SIM-232: missing complete initial-state identity is rejected."""
    payload = _payload()
    payload.pop("initial_authority_state_hash")
    _rehash(payload)
    with pytest.raises(Exception, match="initial_authority_state_hash"):
        _build(payload)


def test_fr_sim_231_revision_gap_and_retroactive_claim_fail_closed() -> None:
    """FR-SIM-231: revision gaps and unproved backdating are rejected."""
    payload = _payload()
    revision = dict(payload["provider_specification_revisions"][0])  # type: ignore[index]
    revision["effective_from"] = revision["observed_at"] - timedelta(seconds=1)  # type: ignore[operator]
    payload["provider_specification_revisions"] = (revision,)
    _rehash(payload)
    with pytest.raises(Exception, match="historical provider revision"):
        _build(payload)


def test_fr_sim_235_async_success_and_running_loop_sync_failure(
    tmp_path: Path,
) -> None:
    """FR-SIM-235: async succeeds and sync fails inside a running loop."""
    dataset = _dataset("req-55555555-5555-4555-8555-555555555555")
    request = _build()
    dependencies = FakeDependencies(tmp_path, dataset)

    async def exercise() -> None:
        response = await run_backtest_async(request, _auth(request), dependencies)
        unwrap_simulation_response(response, operation="test.request_v2.async")
        sync_response = run_backtest(request, _auth(request), dependencies)
        with pytest.raises(Exception, match="active event loop"):
            unwrap_simulation_response(sync_response, operation="test.request_v2.sync")

    asyncio.run(exercise())


def test_fr_sim_196_cold_v2_identity_is_stable() -> None:
    """FR-SIM-196: fresh V2 construction produces identical identity."""
    first = dump_simulation_value(_build())
    second = dump_simulation_value(_build())
    assert first["config_hash"] == second["config_hash"]
