"""CRUD execution evidence for the private Indicators persistence package.

Indicators persistence is internal support, not a registered feature (see
``docs/CHANGELOG.md``, "Withdraw feature status from the four persistence
packages"), so this evidence lives in pytest rather than a numbered usage
program. Each test runs the real CRUD functions against one scratch database
created through the production migration runner, so the shipped statements are
exercised exactly as a governed caller would execute them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
    unwrap_data_response,
)
from app.services.indicators import run_indicators_migrations
from app.services.indicators.persistence import (
    create_indicator_definition_record,
    create_indicator_materialization_record,
    create_indicator_param_set_record,
    delete_indicator_materialization_record,
    delete_stale_indicator_materializations,
    invalidate_indicator_materializations_for_source,
    read_indicator_definition,
    read_indicator_materialization,
    read_stale_indicator_materializations,
    update_indicator_materialization_state,
)
from app.utils import generate_id

_NOW = "2026-08-04T00:00:00.000Z"
_LATER = "2026-08-04T01:00:00.000Z"

_DEFINITION_PARAMETERS: tuple[Any, ...] = (
    "def-rsi-v2",
    "RSI",
    "v2",
    "momentum",
    "formula-hash-aaa",
    '{"period": {"type": "integer"}}',
    '["value"]',
    14,
    1,
    "active",
    "req-seed",
    "corr-seed",
    _NOW,
    _NOW,
)

_PARAM_SET_PARAMETERS: tuple[Any, ...] = (
    "ps-rsi-14",
    "def-rsi-v2",
    '{"period": 14, "source": "close"}',
    "params-hash-14",
    "standard",
    _NOW,
    _NOW,
)


def _configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Configure one isolated scratch database for persistence runs.

    Args:
        monkeypatch: Environment mutator scoped to the current test.
        tmp_path: Unique per-test directory hosting the scratch database.
    """
    monkeypatch.setenv("DATABASE_URL", "sqlite:///indicators_persistence.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")


def _status(response: Any) -> str:
    """Read the envelope status of one standard response.

    Args:
        response: Standard response returned by a persistence operation.

    Returns:
        The response status string.
    """
    return str(response.status)


def _rows(response: Any, request_id: str) -> list[dict[str, Any]]:
    """Unwrap one Data-owned transaction response into its row list.

    Args:
        response: Standard response wrapping a transaction result.
        request_id: Caller trace identity for the unwrap operation.

    Returns:
        The transaction result rows as dictionaries.
    """
    result = unwrap_data_response(
        response,
        operation="indicators.persistence.test",
        request_id=request_id,
    )
    return list(result.rows)


def _materialization_parameters(
    materialization_id: str, *, state: str, covered_to_utc: int, timeframe: str = "M1"
) -> tuple[Any, ...]:
    """Build one ordered ``indicator_materializations`` column tuple.

    Args:
        materialization_id: Materialisation identity.
        state: Lifecycle state to record.
        covered_to_utc: Inclusive covered-range end.
        timeframe: Bar timeframe, part of the series uniqueness key.

    Returns:
        Ordered column values matching the shipped INSERT statement.
    """
    return (
        materialization_id,
        "def-rsi-v2",
        "ps-rsi-14",
        "EURUSD",
        timeframe,
        f"ds-{materialization_id}",
        "ds-eurusd-m1",
        "source-hash-v1",
        "formula-hash-aaa",
        1_700_000_000,
        covered_to_utc,
        43_200,
        state,
        None,
        "req-seed",
        "corr-seed",
        _NOW,
        _NOW,
    )


def _seed_schema(request_id: str) -> None:
    """Apply the Indicators manifest through the production runner.

    Args:
        request_id: Caller trace identity.
    """
    assert _status(run_indicators_migrations(request_id)) == "success"


def _seed_definition(request_id: str) -> None:
    """Create the shared definition and parameter set.

    Args:
        request_id: Caller trace identity.
    """
    created = create_indicator_definition_record(
        _DEFINITION_PARAMETERS, request_id=request_id
    )
    assert _status(created) == "success"
    param_set = create_indicator_param_set_record(
        _PARAM_SET_PARAMETERS, request_id=request_id
    )
    assert _status(param_set) == "success"


def _create_materialization(
    materialization_id: str,
    *,
    state: str,
    covered_to_utc: int,
    request_id: str,
    timeframe: str = "M1",
) -> None:
    """Insert one materialisation reference.

    Args:
        materialization_id: Materialisation identity.
        state: Lifecycle state to record.
        covered_to_utc: Inclusive covered-range end.
        request_id: Caller trace identity.
        timeframe: Bar timeframe, part of the series uniqueness key.
    """
    created = create_indicator_materialization_record(
        _materialization_parameters(
            materialization_id,
            state=state,
            covered_to_utc=covered_to_utc,
            timeframe=timeframe,
        ),
        request_id=request_id,
    )
    assert _status(created) == "success"


def test_migrations_runner_creates_support_tables_idempotently(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The production runner applies the schema and skips on rerun."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    _seed_schema(request_id)
    rows = _rows(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(
                        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
                    ),
                    parameter_sets=((),),
                    max_rows=50,
                ),
                request_id=request_id,
            )
        ),
        request_id,
    )
    table_names = {row["name"] for row in rows}
    assert {
        "indicator_definitions",
        "indicator_param_sets",
        "indicator_materializations",
    } <= table_names
    assert _status(run_indicators_migrations(request_id)) == "success"


def test_definition_round_trip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A created definition is readable by code and version."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    _seed_schema(request_id)
    created = create_indicator_definition_record(
        _DEFINITION_PARAMETERS, request_id=request_id
    )
    assert _status(created) == "success"
    rows = _rows(
        read_indicator_definition("RSI", "v2", request_id=request_id), request_id
    )
    assert len(rows) == 1
    assert rows[0]["definition_id"] == "def-rsi-v2"
    assert rows[0]["is_causal"] == 1
    assert rows[0]["state"] == "active"
    missing = _rows(
        read_indicator_definition("RSI", "v9", request_id=request_id), request_id
    )
    assert missing == []


def _read_mat(request_id: str, timeframe: str = "M1") -> list[dict[str, Any]]:
    """Read back one EURUSD materialisation row by its series key.

    Args:
        request_id: Caller trace identity.
        timeframe: Bar timeframe, part of the series uniqueness key.

    Returns:
        Rows for the shared definition, parameter set, symbol, and timeframe.
    """
    return _rows(
        read_indicator_materialization(
            "def-rsi-v2", "ps-rsi-14", "EURUSD", timeframe, request_id=request_id
        ),
        request_id,
    )


def test_param_set_and_materialization_round_trip(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Parameter sets and materialisation references survive a round trip."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    _seed_schema(request_id)
    _seed_definition(request_id)
    _create_materialization(
        "mat-1", state="building", covered_to_utc=1_702_000_000, request_id=request_id
    )
    rows = _read_mat(request_id)
    assert len(rows) == 1
    assert rows[0]["materialization_id"] == "mat-1"
    assert rows[0]["state"] == "building"
    assert rows[0]["dataset_id"] == "ds-mat-1"


def test_state_update_and_source_invalidation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Lifecycle updates advance state; changed sources invalidate derivations."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    _seed_schema(request_id)
    _seed_definition(request_id)
    _create_materialization(
        "mat-1", state="building", covered_to_utc=1_702_000_000, request_id=request_id
    )
    updated = update_indicator_materialization_state(
        ("ready", _LATER, 43_200, _LATER, "mat-1"), request_id=request_id
    )
    assert _status(updated) == "success"
    assert _read_mat(request_id)[0]["state"] == "ready"

    invalidated = invalidate_indicator_materializations_for_source(
        _LATER, "ds-eurusd-m1", "source-hash-v2", request_id=request_id
    )
    assert _status(invalidated) == "success"
    stale = _rows(
        read_stale_indicator_materializations(request_id=request_id, limit=10),
        request_id,
    )
    assert [row["materialization_id"] for row in stale] == ["mat-1"]

    # A matching source hash leaves the invalidated row untouched.
    unchanged = invalidate_indicator_materializations_for_source(
        _LATER, "ds-eurusd-m1", "source-hash-v1", request_id=request_id
    )
    assert _status(unchanged) == "success"
    stale_again = _rows(
        read_stale_indicator_materializations(request_id=request_id, limit=10),
        request_id,
    )
    assert len(stale_again) == 1


def test_delete_one_and_purge_stale(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Deletion purges only recomputable rows selected by state and range."""
    _configure(monkeypatch, tmp_path)
    request_id = generate_id("req")
    _seed_schema(request_id)
    _seed_definition(request_id)
    # The two rows use distinct series keys because the schema enforces
    # UNIQUE (definition_id, param_set_id, symbol_id, timeframe).
    _create_materialization(
        "mat-stale", state="stale", covered_to_utc=1_700_500_000, request_id=request_id
    )
    _create_materialization(
        "mat-ready",
        state="ready",
        covered_to_utc=1_702_000_000,
        request_id=request_id,
        timeframe="M5",
    )

    purged = delete_stale_indicator_materializations(
        1_701_000_000, request_id=request_id
    )
    assert _status(purged) == "success"
    remaining = _rows(
        read_stale_indicator_materializations(request_id=request_id, limit=10),
        request_id,
    )
    assert remaining == []
    assert _read_mat(request_id) == []
    assert _read_mat(request_id, timeframe="M5")[0]["materialization_id"] == "mat-ready"

    deleted = delete_indicator_materialization_record(
        "mat-ready", request_id=request_id
    )
    assert _status(deleted) == "success"
    assert _read_mat(request_id, timeframe="M5") == []
