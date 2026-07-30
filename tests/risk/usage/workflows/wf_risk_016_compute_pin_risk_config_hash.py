"""WF-RISK-016: load and pin a canonical Risk configuration hash."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.risk import (
    append_risk_audit_record,
    compute_config_hash,
    create_risk_audit_chain,
    create_risk_audit_record,
    load_risk_config,
)
from app.utils import canonical_json
from tests.risk.integration.test_strategy_admission import _AuditStore
from tests.risk.usage.workflows._support import examples, unwrap_risk_response

WORKFLOW_ID = "WF-RISK-016"
STAGES = (
    "Load the selected bounded Risk profile.",
    "Resolve the mandate-bound policy context.",
    "Canonicalize the exact loaded configuration.",
    "Compute the stable pinned Risk configuration hash.",
    "Bind the hash into one sealed audit record.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the complete configuration-hash pinning workflow."""
    source = examples._config()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "simulation.yaml").write_text(
            yaml.safe_dump(source.model_dump(warnings=False, mode="json")),
            encoding="utf-8",
        )
        # Stage 1 — INPUT BOUNDARY: Load the exact selected YAML profile.
        _stage(1)
        config = unwrap_risk_response(
            load_risk_config("simulation", root),
            operation="load_risk_config",
        )
        print("Loaded profile:", config.model_dump(warnings=False, mode="json"))

    # Stage 2: Resolve the loaded policy context.
    _stage(2)
    print("Policy context:", config.profile, config.policy_version)
    # Stage 3: Canonicalize the complete configuration.
    _stage(3)
    canonical = canonical_json(config.model_dump(warnings=False, mode="json"))
    print("Canonical configuration:", canonical)
    # Stage 4: Compute the stable configuration hash.
    _stage(4)
    config_hash = unwrap_risk_response(
        compute_config_hash(config),
        operation="compute_config_hash",
    )
    print("Pinned hash:", config_hash)

    # Stage 5 — OUTPUT BOUNDARY: Seal the pinned hash into audit evidence.
    _stage(5)
    store = _AuditStore()
    chain = create_risk_audit_chain(config, store, lambda: examples.NOW, canonical_json)
    record = create_risk_audit_record(
        record_id="risk-config-pin-1",
        event_type="risk.config.pinned",
        payload={"profile": config.profile, "policy_version": config.policy_version},
        occurred_at=examples.NOW,
        config_hash=config_hash,
        evidence_refs={"config": config_hash},
        decision_id=None,
        sequence=None,
        previous_hash=None,
        record_hash=None,
        sealed=False,
        request_id=examples.REQUEST_ID,
        correlation_id=examples.CORRELATION_ID,
    )
    sealed = unwrap_risk_response(
        append_risk_audit_record(chain, record),
        operation="append_risk_audit_record",
    )
    print("Sealed audit record:", sealed.model_dump(warnings=False, mode="json"))


if __name__ == "__main__":
    main()
