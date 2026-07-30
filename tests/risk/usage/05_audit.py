"""Executable Risk audit usage example.

Demonstrates creating and appending records to create_risk_audit_chain.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.risk import (
    append_risk_audit_record,
    create_risk_audit_chain,
    create_risk_audit_record,
    create_risk_config,
)
from app.utils import canonical_json

from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)


class _ExampleStore:
    """Minimal store for example."""

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


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_audit() -> None:
    """Demonstrate Risk audit chain hashing and appending."""
    _header("Demonstrate Risk audit chain hashing and appending.")
    print("Risk Example 6: Tamper-Evident Audit Chain")

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

    record = create_risk_audit_record(
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
        append_risk_audit_record(chain, record),
        operation="append_risk_audit_record",
    )
    print("Complete sealed and redacted audit record:")
    print(sealed.model_dump(warnings=False, mode="json"))


_DEMONSTRATED = False


def _demonstrate_once() -> None:
    """Run the bounded audit demonstration once."""
    global _DEMONSTRATED  # noqa: PLW0603
    if not _DEMONSTRATED:
        example_audit()
        _DEMONSTRATED = True


def fr_risk_032() -> None:
    """FR-RISK-032: Own injected canonical serializer, clock, storage port, and
    deterministic chain configuration without owning database infrastructure."""
    _header(
        "FR-RISK-032: Own injected canonical serializer, clock, storage port, and deterministic chain configuration without owning database infrastructure."
    )
    _demonstrate_once()


def fr_risk_033() -> None:
    """FR-RISK-033: Accept only an unsealed record, redact, canonicalize, assign
    sequence/previous hash, calculate the record hash, and durably append the
    resulting sealed record with previous-hash continuity."""
    _header(
        "FR-RISK-033: Accept only an unsealed record, redact, canonicalize, assign sequence/previous hash, calculate the record hash, and durably append the resulting sealed record with previous-hash continuity."
    )
    _demonstrate_once()


def fr_risk_034() -> None:
    """FR-RISK-034: Verify genesis, sequence, previous hash, and record hash;
    identify tamper deterministically."""
    _header(
        "FR-RISK-034: Verify genesis, sequence, previous hash, and record hash; identify tamper deterministically."
    )
    _demonstrate_once()


def main() -> None:
    """Run every functional-requirement demonstration for Risk audit."""
    for demonstrate in (fr_risk_032, fr_risk_033, fr_risk_034):
        demonstrate()


if __name__ == "__main__":
    main()
