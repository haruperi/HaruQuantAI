"""Executable Risk audit usage example.

Demonstrates creating and appending records to RiskAuditChain.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.risk.audit import RiskAuditChain
from app.services.risk.config import RiskConfig
from app.services.risk.contracts import RiskAuditRecord
from app.utils import canonical_json

NOW = datetime(2026, 7, 19, tzinfo=UTC)


class _ExampleStore:
    """Minimal store for example."""

    def __init__(self) -> None:
        self.records: list[RiskAuditRecord] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> RiskAuditRecord | None:
        del timeout_seconds
        return self.records[-1] if self.records else None

    def append_atomic(
        self,
        record: RiskAuditRecord,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        del expected_sequence, expected_previous_hash, timeout_seconds
        self.records.append(record)
        return "appended"

    def read_all(
        self, *, timeout_seconds: Decimal | None
    ) -> tuple[RiskAuditRecord, ...]:
        del timeout_seconds
        return tuple(self.records)


def example_audit() -> None:
    """Demonstrate Risk audit chain hashing and appending."""
    print("=" * 80)
    print("Risk Example 6: Tamper-Evident Audit Chain")
    print("=" * 80)

    config = RiskConfig(
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
    chain = RiskAuditChain(config, store, lambda: NOW, canonical_json)

    record = RiskAuditRecord(
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
        request_id="req-1",
        correlation_id="cor-1",
    )

    sealed = chain.append(record)
    print(
        f"Sealed Audit Record sequence: {sealed.sequence}, hash: {sealed.record_hash}"
    )


def main() -> None:
    """Run Risk audit usage example."""
    example_audit()


if __name__ == "__main__":
    main()
