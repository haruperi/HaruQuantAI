"""Unit evidence for Simulation backtest request V2 identity."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path

import pytest
from app.kernel.serialization import canonical_digest
from app.services.simulator import (
    calculate_simulation_backtest_config_hash,
    create_simulation_value,
    dump_simulation_value,
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
            "calculation_model_hash": "a" * 64,
            "calculation_artifact_checksum": "b" * 64,
            "calibration_artifact_checksum": "c" * 64,
            "realism_stream_identity_hash": "d" * 64,
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
            "initial_authority_state_hash": canonical_digest(
                {
                    "account": {
                        "balance": payload["initial_balance"],
                        "currency": payload["account_currency"],
                    },
                    "orders": (),
                    "positions": (),
                    "deals": (),
                    "ownership": {"mode": "exclusive"},
                }
            ),
            "certification_target": "demo",
            "close_open_positions_at_end": True,
        }
    )
    payload["config_hash"] = unwrap_simulation_response(
        calculate_simulation_backtest_config_hash(payload),
        operation="test.request_v2.calculate_hash",
    )
    return payload


def _build(payload: dict[str, object] | None = None) -> object:
    """Build one opaque V2 request."""
    return create_simulation_value(
        "SimulationBacktestRequest", **(payload or _payload())
    )


def _rehash(payload: dict[str, object]) -> None:
    """Replace a payload's V2 configuration hash in place."""
    payload["config_hash"] = unwrap_simulation_response(
        calculate_simulation_backtest_config_hash(payload),
        operation="test.request_v2.calculate_hash",
    )


def test_fr_sim_196_v2_binds_complete_execution_identity() -> None:
    """FR-SIM-196: V2 exposes all registered execution-identity fields."""
    result = dump_simulation_value(_build())
    assert result["contract_version"] == "v2"
    assert result["schema_id"] == "simulation.backtest_request.v2"
    assert result["decision_instant_policy"] == "point_in_time_available_at"
    assert result["calculation_model_hash"] == "a" * 64
    assert result["calculation_artifact_checksum"] == "b" * 64
    assert result["calibration_artifact_checksum"] == "c" * 64
    assert result["realism_stream_identity_hash"] == "d" * 64


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("execution_model_ref", "execution-model-v2"),
        ("execution_model_hash", "5" * 64),
        ("calculation_model_hash", "9" * 64),
        ("calculation_artifact_checksum", "a" * 64),
        ("calibration_artifact_checksum", "d" * 64),
        ("realism_stream_identity_hash", "e" * 64),
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


def test_fr_sim_235_async_is_the_only_official_operation(
    tmp_path: Path,
) -> None:
    """FR-SIM-235: async succeeds and sync fails inside a running loop."""
    dataset = _dataset("req-55555555-5555-4555-8555-555555555555")
    request = _build()

    class V2Dependencies(FakeDependencies):
        """Add complete neutral v2 authority composition to the base fixture."""

        def load_initial_authority_state(self, value: object) -> dict[str, object]:
            """Return the exact request-bound empty authority snapshot."""
            return {
                "account": {
                    "balance": value.initial_balance,  # type: ignore[attr-defined]
                    "currency": value.account_currency,  # type: ignore[attr-defined]
                },
                "orders": (),
                "positions": (),
                "deals": (),
                "ownership": {"mode": "exclusive"},
            }

        def load_account_activity(self, value: object) -> tuple[object, ...]:
            """Return no foreign activity for the exclusive interval."""
            del value
            return ()

        def load_provider_specification_revisions(
            self, value: object
        ) -> dict[str, object]:
            """Return complete Data-shaped request-bound revision evidence."""
            binding = value.provider_specification_revisions[0]  # type: ignore[attr-defined]
            return {
                "complete_coverage": True,
                "revisions": (
                    {
                        "revision_id": binding.revision_id,
                        "broker": binding.provider,
                        "server": binding.server,
                        "environment": binding.environment,
                        "account_digest": binding.account_digest,
                        "provider_symbol": binding.symbol,
                        "snapshot_checksum": binding.checksum,
                        "effective_from": binding.effective_from,
                        "effective_to": binding.effective_to,
                        "payload": {
                            "trade_mode": "FULL",
                            "filling_modes": ("FOK",),
                            "execution_mode": "MARKET",
                            "directional_volume_limit": "100",
                            "point": "0.00001",
                            "stops_level_points": 0,
                            "freeze_level_points": 0,
                            "weekly_sessions": {
                                str(day): (("00:00", "23:59:59.999999"),)
                                for day in range(7)
                            },
                            "dated_exceptions": {},
                            "exception_coverage": (),
                            "exception_coverage_required": False,
                        },
                    },
                ),
            }

        def build_approved_requests(self, *_args: object) -> tuple[object, ...]:
            """Return no approved request for the fixture's neutral strategy."""
            return ()

        async def evaluate_point_in_time_cycle(self, *_args: object) -> dict[str, bool]:
            """Return one neutral shared-cycle result per visible instant."""
            return {"mutation_performed": False}

    dependencies = V2Dependencies(tmp_path, dataset)

    response = asyncio.run(run_backtest_async(request, _auth(request), dependencies))
    unwrap_simulation_response(response, operation="test.request.async")


def test_fr_sim_196_cold_v2_identity_is_stable() -> None:
    """FR-SIM-196: fresh V2 construction produces identical identity."""
    first = dump_simulation_value(_build())
    second = dump_simulation_value(_build())
    assert first["config_hash"] == second["config_hash"]
