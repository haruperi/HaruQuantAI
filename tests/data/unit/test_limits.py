"""Guards for the centralised DATA limits manifest.

``limits/manifest.py`` is the only genuinely new production code in ``CAP-DATA-026``
Phase 1, which makes it the phase's main behaviour risk: a wrong default would change a
bound that a legacy module constant governs today.

The manifest cannot import those legacy constants without inverting the dependency
graph, so equality is proven here instead.
``test_manifest_matches_every_legacy_constant`` imports both sides and asserts they
agree. It is the drift guard for as long as both definitions coexist, and is deleted
with the legacy constants in Phase 11.
"""

from __future__ import annotations

import pytest
from app.services.data._limits import (
    DEFAULT_LIMITS,
    WORKFLOW_CONTEXTS,
    apply_workflow_override,
    get_limit,
)
from app.services.data.contracts import DataError


def test_manifest_matches_every_legacy_constant() -> None:
    """Assert each published limit equals the legacy constant it replaces.

    Raises:
        AssertionError: If the manifest and the owning module have drifted.
    """
    from app.services.data.audit.contracts import AUDIT_QUERY_HARD_MAX_LIMIT
    from app.services.data.contracts import QUALITY_SAMPLE_LIMIT
    from app.services.data.contracts.errors import (
        ERROR_SAFE_DETAILS_MAX_BYTES,
        ERROR_SAFE_DETAILS_MAX_ITEMS,
    )
    from app.services.data.data_jobs import backfill
    from app.services.data.data_jobs import job as scheduler
    from app.services.data.market_data import pipeline as historical
    from app.services.data.market_data import symbol_discovery as reference
    from app.services.data.persistence.contracts import (
        CACHE_CLEAR_MAX_ENTRIES,
        CACHE_TTL_MAX_SECONDS,
    )
    from app.services.data.synthetic_data import gbm as synthetic
    from app.services.data.tick_derivation import generator as ticks

    expected = {
        "TICK_MAX_LIMIT": historical.TICK_MAX_LIMIT,
        "SPREAD_MAX_LIMIT": historical.SPREAD_MAX_LIMIT,
        "CACHE_TTL_MAX_SECONDS": historical.CACHE_TTL_MAX_SECONDS,
        "CACHE_TTL_DAILY_SECONDS": historical.CACHE_TTL_DAILY_SECONDS,
        "CACHE_TTL_INTRADAY_SECONDS": historical.CACHE_TTL_INTRADAY_SECONDS,
        "CACHE_TTL_TICK_SECONDS": historical.CACHE_TTL_TICK_SECONDS,
        "SYMBOL_LIST_DEFAULT_LIMIT": reference.SYMBOL_LIST_DEFAULT_LIMIT,
        "SYMBOL_LIST_MAX_LIMIT": reference.SYMBOL_LIST_MAX_LIMIT,
        "AVAILABILITY_SCAN_MAX_RECORDS": reference.AVAILABILITY_SCAN_MAX_RECORDS,
        "SYNTHETIC_BAR_MAX_RECORDS": synthetic.SYNTHETIC_BAR_MAX_RECORDS,
        "SYNTHETIC_TICK_MAX_RECORDS": synthetic.SYNTHETIC_TICK_MAX_RECORDS,
        "GENERATED_TICKS_MIN_PER_BAR": ticks.GENERATED_TICKS_MIN_PER_BAR,
        "BACKFILL_MAX_RECORDS_PER_CHUNK": backfill.BACKFILL_MAX_RECORDS_PER_CHUNK,
        "JOB_LEASE_TIMEOUT_SECONDS": backfill.JOB_LEASE_TIMEOUT_SECONDS,
        "JOB_MAX_SYMBOLS": scheduler.JOB_MAX_SYMBOLS,
        "JOB_MAX_TIMEFRAMES": scheduler.JOB_MAX_TIMEFRAMES,
        "JOB_MIN_INTERVAL_SECONDS": scheduler.JOB_MIN_INTERVAL_SECONDS,
        "CACHE_TTL_MAX_SECONDS_CONTRACT": CACHE_TTL_MAX_SECONDS,
        "CACHE_CLEAR_MAX_ENTRIES": CACHE_CLEAR_MAX_ENTRIES,
        "QUALITY_SAMPLE_LIMIT": QUALITY_SAMPLE_LIMIT,
        "AUDIT_QUERY_HARD_MAX_LIMIT": AUDIT_QUERY_HARD_MAX_LIMIT,
        "ERROR_SAFE_DETAILS_MAX_ITEMS": ERROR_SAFE_DETAILS_MAX_ITEMS,
        "ERROR_SAFE_DETAILS_MAX_BYTES": ERROR_SAFE_DETAILS_MAX_BYTES,
    }
    # The contract-side cache ceiling must agree with the retrieval-side one.
    assert (
        expected.pop("CACHE_TTL_MAX_SECONDS_CONTRACT")
        == (expected["CACHE_TTL_MAX_SECONDS"])
    )

    mismatched = {
        name: (value, DEFAULT_LIMITS[name])
        for name, value in expected.items()
        if DEFAULT_LIMITS[name] != value
    }
    assert not mismatched, (
        f"Limits manifest drifted from its legacy constants: {mismatched}. "
        "The manifest must publish the value the owning module enforces today."
    )


def test_backfill_chunk_size_matches_its_record_bound() -> None:
    """Assert the two published names for the backfill chunk bound agree.

    Raises:
        AssertionError: If the aliases diverge.
    """
    assert get_limit("BACKFILL_CHUNK_SIZE") == get_limit(
        "BACKFILL_MAX_RECORDS_PER_CHUNK"
    )


def test_removed_ohlcv_limit_fails_closed() -> None:
    """Assert the retired OHLCV ceiling is no longer published.

    Raises:
        AssertionError: If the retired limit is still accepted.
    """
    with pytest.raises(DataError) as excinfo:
        get_limit("OHLCV_MAX_LIMIT")
    assert excinfo.value.code == "INVALID_INPUT"


def test_unknown_limit_fails_rather_than_defaulting() -> None:
    """Assert a typo cannot silently remove a bound.

    Raises:
        AssertionError: If an unknown limit returns a permissive value.
    """
    with pytest.raises(DataError) as excinfo:
        get_limit("NOT_A_REAL_LIMIT")
    assert excinfo.value.code == "INVALID_INPUT"


def test_unknown_workflow_is_rejected() -> None:
    """Assert an unrecognized workflow context fails closed.

    Raises:
        AssertionError: If an unknown workflow is accepted.
    """
    with pytest.raises(DataError):
        get_limit("TICK_MAX_LIMIT", "not_a_workflow")
    with pytest.raises(DataError):
        apply_workflow_override("not_a_workflow", {})


def test_research_may_raise_a_limit() -> None:
    """Assert the research context may loosen a bound.

    Raises:
        AssertionError: If research cannot raise a limit.
    """
    resolved = apply_workflow_override("research", {"TICK_MAX_LIMIT": 300_000})
    assert resolved["TICK_MAX_LIMIT"] == 300_000


@pytest.mark.parametrize(
    "workflow", ["backtest", "validation", "risk", "execution_bound"]
)
def test_governed_workflows_may_not_raise_a_limit(workflow: str) -> None:
    """Assert a governed workflow cannot loosen a bound.

    Args:
        workflow: Governed workflow context under test.

    Raises:
        AssertionError: If a governed context is allowed to raise a limit.
    """
    with pytest.raises(DataError) as excinfo:
        apply_workflow_override(workflow, {"TICK_MAX_LIMIT": 300_000})
    assert excinfo.value.code == "POLICY_BLOCKED"


@pytest.mark.parametrize(
    "workflow", ["backtest", "validation", "risk", "execution_bound"]
)
def test_governed_workflows_may_tighten_a_limit(workflow: str) -> None:
    """Assert tightening is permitted in every workflow context.

    Args:
        workflow: Governed workflow context under test.

    Raises:
        AssertionError: If a governed context cannot tighten a limit.
    """
    resolved = apply_workflow_override(workflow, {"TICK_MAX_LIMIT": 100})
    assert resolved["TICK_MAX_LIMIT"] == 100


@pytest.mark.parametrize("value", [0, -1, True, "1000"])
def test_non_positive_or_non_integer_overrides_are_rejected(value: object) -> None:
    """Assert an override must be a positive integer.

    Args:
        value: Invalid override value under test.

    Raises:
        AssertionError: If an invalid value is accepted.
    """
    with pytest.raises(DataError):
        apply_workflow_override("research", {"TICK_MAX_LIMIT": value})


def test_override_result_is_immutable_and_complete() -> None:
    """Assert overrides return every published limit and cannot be mutated.

    Raises:
        AssertionError: If the result is partial or mutable.
    """
    resolved = apply_workflow_override("research", {"TICK_MAX_LIMIT": 300_000})
    assert set(resolved) == set(DEFAULT_LIMITS)
    with pytest.raises(TypeError):
        resolved["TICK_MAX_LIMIT"] = 1  # type: ignore[index]


def test_workflow_contexts_match_the_contract_vocabulary() -> None:
    """Assert the manifest and the dataset contracts publish the same contexts.

    Raises:
        AssertionError: If the two vocabularies diverge.
    """
    from app.services.data.contracts.dataset import (
        WORKFLOW_CONTEXTS as CONTRACT_CONTEXTS,
    )

    assert set(WORKFLOW_CONTEXTS) == set(CONTRACT_CONTEXTS)
