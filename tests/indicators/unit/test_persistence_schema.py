"""Schema-level evidence for the private Indicators persistence package.

Indicators persistence is internal support, not a registered feature, so this
evidence lives in pytest rather than in a numbered usage program. Each test
asserts an invariant the database enforces, because an invariant enforced only
by convention is not enforced.
"""

import sqlite3

import pytest
from app.services.indicators.migrations.definitions import (
    _INDICATOR_SCHEMA_STATEMENTS,
)

_NOW = "2026-08-03T00:00:00.000Z"

_INSERT_DEFINITION = (
    "INSERT INTO indicator_definitions (definition_id, indicator_code, "
    "version, category, formula_hash, param_schema_json, output_names_json, "
    "lookback_bars, is_causal, state, request_id, correlation_id, "
    "created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
)

_INSERT_MATERIALIZATION = (
    "INSERT INTO indicator_materializations (materialization_id, "
    "definition_id, param_set_id, symbol_id, timeframe, dataset_id, "
    "source_dataset_id, source_data_hash, formula_hash, covered_from_utc, "
    "covered_to_utc, row_count, state, built_at, request_id, correlation_id, "
    "created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
)


@pytest.fixture
def connection():
    """Yield an in-memory database carrying the Indicators schema."""
    con = sqlite3.connect(":memory:")
    for statement in _INDICATOR_SCHEMA_STATEMENTS:
        con.execute(statement)
    con.execute(
        _INSERT_DEFINITION,
        (
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
            "req-1",
            "corr-1",
            _NOW,
            _NOW,
        ),
    )
    con.execute(
        "INSERT INTO indicator_param_sets (param_set_id, definition_id, "
        "params_json, params_hash, label, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (
            "ps-rsi-14",
            "def-rsi-v2",
            '{"period": 14, "source": "close"}',
            "params-hash-14",
            "standard",
            _NOW,
            _NOW,
        ),
    )
    yield con
    con.close()


def test_one_formula_version_cannot_be_registered_twice(connection):
    """Reject a second definition sharing a code and version."""
    with pytest.raises(sqlite3.IntegrityError, match="indicator_code"):
        connection.execute(
            _INSERT_DEFINITION,
            (
                "def-rsi-dup",
                "RSI",
                "v2",
                "momentum",
                "formula-hash-bbb",
                "{}",
                '["value"]',
                14,
                1,
                "active",
                "req-2",
                "corr-2",
                _NOW,
                _NOW,
            ),
        )


def test_non_causal_indicators_are_separately_selectable(connection):
    """Isolate lookahead indicators so a live signal path can exclude them."""
    connection.execute(
        _INSERT_DEFINITION,
        (
            "def-zigzag-v1",
            "ZIGZAG",
            "v1",
            "trend",
            "formula-hash-ccc",
            "{}",
            '["pivot"]',
            0,
            0,
            "active",
            "req-1",
            "corr-1",
            _NOW,
            _NOW,
        ),
    )
    lookahead = connection.execute(
        "SELECT indicator_code FROM indicator_definitions WHERE is_causal = 0"
    ).fetchall()
    assert lookahead == [("ZIGZAG",)]


def test_generated_columns_expose_json_parameters(connection):
    """Filter on a JSON parameter without json_extract at read time."""
    row = connection.execute(
        "SELECT period, source_field FROM indicator_param_sets "
        "WHERE definition_id = ? AND period = ?",
        ("def-rsi-v2", 14),
    ).fetchone()
    assert row == (14, "close")


def test_changed_source_bytes_invalidate_a_materialization(connection):
    """Make a derivation from superseded bars provably stale."""
    connection.execute(
        _INSERT_MATERIALIZATION,
        (
            "mat-1",
            "def-rsi-v2",
            "ps-rsi-14",
            "EURUSD",
            "M1",
            "ds-rsi-eurusd-m1",
            "ds-eurusd-m1",
            "source-hash-v1",
            "formula-hash-aaa",
            1_700_000_000,
            1_702_591_999,
            43_200,
            "ready",
            _NOW,
            "req-1",
            "corr-1",
            _NOW,
            _NOW,
        ),
    )
    connection.execute(
        "UPDATE indicator_materializations SET state = 'invalidated', "
        "updated_at = ? WHERE source_dataset_id = ? AND source_data_hash <> ?",
        (_NOW, "ds-eurusd-m1", "source-hash-v2"),
    )
    state = connection.execute(
        "SELECT state FROM indicator_materializations WHERE materialization_id = ?",
        ("mat-1",),
    ).fetchone()[0]
    assert state == "invalidated"


def test_purging_a_materialization_retains_its_definition(connection):
    """Permit deleting a recomputable series while keeping its provenance."""
    connection.execute(
        _INSERT_MATERIALIZATION,
        (
            "mat-1",
            "def-rsi-v2",
            "ps-rsi-14",
            "EURUSD",
            "M1",
            "ds-rsi-eurusd-m1",
            "ds-eurusd-m1",
            "source-hash-v1",
            "formula-hash-aaa",
            1_700_000_000,
            1_702_591_999,
            43_200,
            "ready",
            _NOW,
            "req-1",
            "corr-1",
            _NOW,
            _NOW,
        ),
    )
    connection.execute("DELETE FROM indicator_materializations")
    assert (
        connection.execute(
            "SELECT COUNT(*) FROM indicator_materializations"
        ).fetchone()[0]
        == 0
    )
    assert (
        connection.execute("SELECT COUNT(*) FROM indicator_definitions").fetchone()[0]
        == 1
    )
