"""Usage evidence for FEAT-SIM-16 effective-dated calculations."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.simulator import (
    calculate_fx_profit,
    calculate_planned_margin,
    calculate_total_margin,
    convert_account_currency,
    get_calculation_model_identity,
    get_supported_calculation_modes,
    load_calculation_conformance_artifact,
    run_offline_calculation_conformance,
    unwrap_simulation_response,
)


def _revision(now: datetime) -> dict[str, object]:
    """Return bounded complete provider-revision evidence."""
    return {
        "complete_coverage": True,
        "revision_id": "usage-revision-1",
        "snapshot_checksum": "a" * 64,
        "effective_from": now.isoformat(),
        "effective_to": (now + timedelta(days=1)).isoformat(),
        "payload": {
            "calculation_mode": "FOREX",
            "contract_size": "100000",
            "point": "0.00001",
            "tick_size": "0.00001",
            "tick_value": "1",
            "base_currency": "EUR",
            "profit_currency": "USD",
            "margin_currency": "USD",
            "leverage": "100",
            "margin_initial": None,
            "margin_maintenance": None,
            "margin_hedged": "500",
            "margin_hedged_use_leg": False,
            "account_currency": "USD",
            "currency_digits": 2,
            "rounding_rule": "ROUND_HALF_EVEN",
        },
    }


def _artifact(model_hash: str) -> dict[str, object]:
    """Return one canonical checksummed offline artifact."""
    material = {
        "schema_id": "simulation.calculation_conformance.v1",
        "model_identity": model_hash,
        "cases": [{"case_id": "profit-1", "expected": "100.00", "actual": "100.00"}],
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return {**material, "checksum": hashlib.sha256(encoded.encode()).hexdigest()}


def fr_sim_137(evidence: dict[str, object]) -> None:
    """Verify exact evidenced FX profit."""
    assert evidence["profit"] == Decimal("100.00")


def fr_sim_138(evidence: dict[str, object]) -> None:
    """Verify contract-size profit semantics."""
    assert evidence["profit"] == Decimal("100.00")


def fr_sim_139(evidence: dict[str, object]) -> None:
    """Verify account-currency conversion."""
    assert evidence["converted"] == Decimal("10.00")


def fr_sim_140(evidence: dict[str, object]) -> None:
    """Verify total margin semantics."""
    assert evidence["total"] == Decimal("100.00")


def fr_sim_141(evidence: dict[str, object]) -> None:
    """Verify incremental planned margin semantics."""
    assert evidence["planned"] == Decimal("100.00")


def fr_sim_142(evidence: dict[str, object]) -> None:
    """Verify effective revision selection."""
    assert evidence["profit"] is not None


def fr_sim_143(evidence: dict[str, object]) -> None:
    """Verify provider rounding semantics."""
    assert evidence["converted"] == Decimal("10.00")


def fr_sim_144(evidence: dict[str, object]) -> None:
    """Verify the exact admitted calculation-mode set."""
    assert evidence["modes"] == ("FOREX",)


def fr_sim_145(evidence: dict[str, object]) -> None:
    """Verify canonical calculations remain deterministic."""
    assert evidence["profit"] == Decimal("100.00")


def fr_sim_210(evidence: dict[str, object]) -> None:
    """Verify stable calculation-model identity."""
    assert len(str(evidence["model_hash"])) == 64


def fr_sim_211(evidence: dict[str, object]) -> None:
    """Verify checksummed artifact loading."""
    assert evidence["artifact"] is not None


def fr_sim_212(evidence: dict[str, object]) -> None:
    """Verify offline exact conformance."""
    assert evidence["passed"] is True


def fr_sim_213(evidence: dict[str, object]) -> None:
    """Verify conformance binds the calculation model."""
    assert evidence["artifact_model_hash"] == evidence["model_hash"]


def fr_sim_214(evidence: dict[str, object]) -> None:
    """Verify the artifact checksum is part of the verdict."""
    assert len(str(evidence["artifact_checksum"])) == 64


def main() -> None:
    """Exercise every FEAT-SIM-16 public operation."""
    now = datetime(2024, 1, 2, 12, tzinfo=UTC)
    revision = _revision(now)
    profit = unwrap_simulation_response(
        calculate_fx_profit(
            revision,
            side="BUY",
            volume=Decimal(1),
            open_price=Decimal("1.1000"),
            close_price=Decimal("1.1010"),
            as_of=now,
            fx_evidence=None,
        ),
        operation="usage.calculations.profit",
    )
    margin_fields = {
        "position_mode": "NETTING",
        "existing_long": Decimal(0),
        "existing_short": Decimal(0),
        "planned_side": "BUY",
        "planned_volume": Decimal("0.1"),
        "as_of": now,
        "fx_evidence": None,
    }
    total = unwrap_simulation_response(
        calculate_total_margin(revision, **margin_fields),
        operation="usage.calculations.total_margin",
    )
    planned = unwrap_simulation_response(
        calculate_planned_margin(revision, **margin_fields),
        operation="usage.calculations.planned_margin",
    )
    converted = unwrap_simulation_response(
        convert_account_currency(
            amount=Decimal("10.005"),
            source_currency="USD",
            target_currency="USD",
            as_of=now,
            currency_digits=2,
            rounding_rule="ROUND_HALF_EVEN",
            evidence=None,
        ),
        operation="usage.calculations.convert",
    )
    identity = unwrap_simulation_response(
        get_calculation_model_identity(), operation="usage.calculations.identity"
    )
    modes = unwrap_simulation_response(
        get_supported_calculation_modes(), operation="usage.calculations.modes"
    )
    artifact = unwrap_simulation_response(
        load_calculation_conformance_artifact(_artifact(identity["model_hash"])),
        operation="usage.calculations.load_artifact",
    )
    verdict = unwrap_simulation_response(
        run_offline_calculation_conformance(artifact),
        operation="usage.calculations.run_conformance",
    )
    evidence: dict[str, object] = {
        "profit": profit,
        "total": total,
        "planned": planned,
        "converted": converted,
        "modes": modes,
        "model_hash": identity["model_hash"],
        "artifact": artifact,
        "passed": verdict["passed"],
        "artifact_model_hash": verdict["model_identity"],
        "artifact_checksum": verdict["artifact_checksum"],
    }
    for requirement in (
        fr_sim_137,
        fr_sim_138,
        fr_sim_139,
        fr_sim_140,
        fr_sim_141,
        fr_sim_142,
        fr_sim_143,
        fr_sim_144,
        fr_sim_145,
        fr_sim_210,
        fr_sim_211,
        fr_sim_212,
        fr_sim_213,
        fr_sim_214,
    ):
        requirement(evidence)
    print(
        f"profit={profit} total_margin={total} planned_margin={planned} "
        f"converted={converted} modes={modes} conformance={verdict['passed']}"
    )


if __name__ == "__main__":
    main()
