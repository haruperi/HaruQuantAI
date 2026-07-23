"""Golden-schema guard for the five owned cross-domain Data contracts.

These contracts are consumed by Indicators, Risk, Strategy, Simulation, Trading,
Portfolio, Optimization, Research, and UI/API. The ``CAP-DATA-026`` restructure
moves them between modules; it must not change their shape. Each test compares the
contract's generated JSON schema against a fixture captured from the pre-restructure
implementation.

A failure here means a field, type, default, requirement, or constraint changed. That
is a contract break for nine consuming domains, not a test that needs updating.
Regenerate a fixture only when a deliberate, versioned contract change is approved.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from app.services.data.audit.contracts import AuditEventPage, AuditEventQuery
from app.services.data.contracts import MarketDataset
from app.services.data.evidence.account_contracts import AccountStateSnapshot
from app.services.data.evidence.fx_contracts import FXConversionEvidence
from app.services.data.evidence.market_context_contracts import MarketContextEvidence

GOLDEN_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "golden" / "contracts"

OWNED_CONTRACTS: dict[str, type] = {
    "market_dataset": MarketDataset,
    "account_state_snapshot": AccountStateSnapshot,
    "market_context_evidence": MarketContextEvidence,
    "fx_conversion_evidence": FXConversionEvidence,
    "audit_event_query": AuditEventQuery,
    "audit_event_page": AuditEventPage,
}


def _schema(model: type) -> dict[str, Any]:
    """Return the deterministic JSON schema for one contract model.

    Args:
        model: Pydantic contract class to describe.

    Returns:
        The generated JSON schema as a plain dictionary.
    """
    return dict(model.model_json_schema())


def _canonical(payload: dict[str, Any]) -> str:
    """Serialize a schema deterministically for comparison.

    Args:
        payload: JSON schema dictionary.

    Returns:
        Sorted-key JSON text with stable indentation.
    """
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


@pytest.mark.parametrize("name", sorted(OWNED_CONTRACTS))
def test_owned_contract_schema_is_unchanged(name: str) -> None:
    """Assert one owned contract's schema still matches its golden fixture.

    Args:
        name: Fixture stem for the contract under test.

    Raises:
        AssertionError: If the generated schema differs from the fixture.
    """
    fixture = GOLDEN_DIR / f"{name}.json"
    assert fixture.is_file(), (
        f"Missing golden fixture {fixture}. The snapshot must be captured from a "
        "verified implementation before any restructure phase moves the contract."
    )
    expected = fixture.read_text(encoding="utf-8")
    actual = _canonical(_schema(OWNED_CONTRACTS[name]))
    assert actual == expected, (
        f"Contract schema for {name} changed. This is a cross-domain contract break, "
        "not a fixture that needs refreshing. Revert the change or version the "
        "contract explicitly."
    )


def test_every_owned_contract_has_a_fixture() -> None:
    """Assert no owned contract silently loses its golden fixture.

    Raises:
        AssertionError: If the fixture set and the owned contract set diverge.
    """
    captured = {path.stem for path in GOLDEN_DIR.glob("*.json")}
    assert captured == set(OWNED_CONTRACTS), (
        "Golden fixture set does not match the owned contract set: "
        f"missing={set(OWNED_CONTRACTS) - captured}, "
        f"unexpected={captured - set(OWNED_CONTRACTS)}"
    )


def test_schema_identifiers_are_stable() -> None:
    """Assert the published schema identifiers keep their v1 values.

    Raises:
        AssertionError: If a schema identifier constant changed.
    """
    from app.services.data.contracts import MARKET_DATASET_SCHEMA, NORMALIZATION_VERSION
    from app.services.data.evidence.account_contracts import ACCOUNT_SNAPSHOT_SCHEMA
    from app.services.data.evidence.fx_contracts import (
        FX_CONVERSION_EVIDENCE_SCHEMA,
    )
    from app.services.data.evidence.market_context_contracts import (
        MARKET_CONTEXT_SCHEMA,
    )

    assert MARKET_DATASET_SCHEMA == "data.market_dataset.v1"
    assert ACCOUNT_SNAPSHOT_SCHEMA == "data.account_state_snapshot.v1"
    assert MARKET_CONTEXT_SCHEMA == "data.market_context_evidence.v1"
    assert FX_CONVERSION_EVIDENCE_SCHEMA == "data.fx_conversion_evidence.v1"
    assert NORMALIZATION_VERSION == "v1"
