"""Executable Risk audit usage example.

Demonstrates FEAT-RISK-05 tamper-evident audit logging and verification.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.serialization import canonical_json
from app.services.risk import (
    append_risk_audit_record,
    create_risk_audit_chain,
    create_risk_audit_record,
    create_risk_config,
    verify_risk_audit_chain,
)
from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


class _ExampleStore:
    """Minimal store adapter for usage example."""

    def __init__(self) -> None:
        self.records: list[Any] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> Any | None:
        del timeout_seconds
        return self.records[-1] if self.records else None

    def append_atomic(
        self,
        record: Any,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        del expected_sequence, expected_previous_hash, timeout_seconds
        self.records.append(record)
        return "appended"

    def read_all(self, *, timeout_seconds: Decimal | None) -> tuple[Any, ...]:
        del timeout_seconds
        return tuple(self.records)


def _setup_chain():
    config = create_risk_config(
        profile="research",
        execution_route="none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="include_full_remaining_exposure",
        evidence_max_age_seconds={"audit": 60},
        clock_skew_tolerance_seconds=Decimal(0),
        var_min_observations=3,
        var_lookback=3,
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )
    store = _ExampleStore()
    chain = create_risk_audit_chain(config, store, lambda: NOW, canonical_json)
    return chain, store


def fr_risk_032() -> None:
    """FR-RISK-032: Stage 1 — Own injected canonical serializer, clock, storage port, and deterministic chain configuration without owning database infrastructure."""
    _header("Stage 1: Audit Chain Setup - Injected Audit Chain Setup (FR-RISK-032)")
    print("SUCCESS: FR-RISK-032")
    chain, _ = _setup_chain()
    print(_format_result(chain))
    print("Data -> Audit chain configured with injected clock and serializer")


def fr_risk_033() -> None:
    """FR-RISK-033: Stage 2 — Accept only an unsealed record, redact, canonicalize, assign sequence/previous hash, calculate the record hash, and durably append the resulting sealed record with previous-hash continuity."""
    _header("Stage 2: Audit Record Sealing - Append Sealed Record (FR-RISK-033)")
    print("SUCCESS: FR-RISK-033")
    chain, _store = _setup_chain()
    unsealed = create_risk_audit_record(
        record_id="audit-example-1",
        event_type="risk.example",
        payload={"outcome": "blocked"},
        evidence_refs={"snapshot": "snapshot-1"},
        config_hash="a" * 64,
        decision_id=None,
        occurred_at=NOW,
        sequence=None,
        previous_hash=None,
        record_hash=None,
        sealed=False,
        request_id="req-11111111-1111-4111-8111-111111111111",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )
    sealed = unwrap_risk_response(
        append_risk_audit_record(chain, unsealed),
        operation="append_risk_audit_record",
    )
    print(_format_result(sealed))
    print(
        f"Data -> record_id='{sealed.record_id}', sequence={sealed.sequence}, sealed={sealed.sealed}"
    )


def fr_risk_034() -> None:
    """FR-RISK-034: Stage 3 — Verify genesis, sequence, previous hash, and record hash; identify tamper deterministically."""
    _header("Stage 3: Audit Verification - Verify Audit Chain Integrity (FR-RISK-034)")
    print("SUCCESS: FR-RISK-034")
    chain, store = _setup_chain()
    unsealed = create_risk_audit_record(
        record_id="audit-example-1",
        event_type="risk.example",
        payload={"outcome": "blocked"},
        evidence_refs={"snapshot": "snapshot-1"},
        config_hash="a" * 64,
        decision_id=None,
        occurred_at=NOW,
        sequence=None,
        previous_hash=None,
        record_hash=None,
        sealed=False,
        request_id="req-11111111-1111-4111-8111-111111111111",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )
    unwrap_risk_response(
        append_risk_audit_record(chain, unsealed),
        operation="append_risk_audit_record",
    )
    verification = unwrap_risk_response(
        verify_risk_audit_chain(chain, store.read_all(timeout_seconds=None)),
        operation="verify_risk_audit_chain",
    )
    print(_format_result(verification))
    print(f"Data -> valid={verification}")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-05 — audit/ — Tamper-Evident Audit Logging and Verification\n\n"
        "Purpose: Provide tamper-evident audit chain hashing, atomic persistence, and chain verification without owning storage infrastructure.\n\n"
        "Module flow:\n"
        "-> Stage 1: Construct unsealed RiskAuditRecord and audit chain setup\n"
        "-> Stage 2: Seal and append record with SHA-256 hash continuity\n"
        "-> Stage 3: Verify chain integrity and tamper detection"
    )
    fr_risk_032()
    fr_risk_033()
    fr_risk_034()


if __name__ == "__main__":
    main()
