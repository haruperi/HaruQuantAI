"""Schema-level evidence for the private Brokers symbol-map persistence.

Brokers persists one table and nothing else. Symbol mapping is internal support
rather than a registered feature, so this evidence lives in pytest. A mis-mapped
symbol routes an order to the wrong instrument, which is why the uniqueness and
point-in-time properties below are enforced by the database.
"""

import sqlite3

import pytest
from app.services.brokers.migrations.definitions import _BROKER_SCHEMA_STATEMENTS

_NOW = "2026-08-03T00:00:00.000Z"

_INSERT = (
    "INSERT INTO broker_symbol_map (map_id, provider_code, symbol_id, "
    "provider_symbol, contract_size_decimal, digits_override, enabled, "
    "effective_from, effective_to, request_id, correlation_id, created_at, "
    "updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
)


def _row(map_id, provider_symbol, effective_from, effective_to=None):
    """Return one mapping row for the tests below."""
    return (
        map_id,
        "mt5",
        "EURUSD",
        provider_symbol,
        "100000",
        None,
        1,
        effective_from,
        effective_to,
        "req-1",
        "corr-1",
        _NOW,
        _NOW,
    )


@pytest.fixture
def connection():
    """Yield an in-memory database holding one active EURUSD mapping."""
    con = sqlite3.connect(":memory:")
    for statement in _BROKER_SCHEMA_STATEMENTS:
        con.execute(statement)
    con.execute(_INSERT, _row("map-1", "EURUSD.r", "2019-01-01"))
    yield con
    con.close()


def test_an_instrument_cannot_hold_two_active_mappings(connection):
    """Reject the duplicate that would route an order to the wrong instrument."""
    with pytest.raises(sqlite3.IntegrityError, match="symbol_id"):
        connection.execute(_INSERT, _row("map-2", "EURUSD.pro", "2024-01-01"))


def test_a_provider_symbol_cannot_map_to_two_instruments(connection):
    """Reject an active reverse-direction duplicate."""
    with pytest.raises(sqlite3.IntegrityError, match="provider_symbol"):
        connection.execute(
            _INSERT,
            (
                "map-3",
                "mt5",
                "GBPUSD",
                "EURUSD.r",
                "100000",
                None,
                1,
                "2024-01-01",
                None,
                "req-1",
                "corr-1",
                _NOW,
                _NOW,
            ),
        )


def test_a_rename_closes_the_old_mapping_and_opens_a_successor(connection):
    """Keep both rows so a historical resolution stays answerable."""
    connection.execute(
        "UPDATE broker_symbol_map SET effective_to = ?, updated_at = ? "
        "WHERE provider_code = ? AND symbol_id = ? AND effective_to IS NULL",
        ("2024-01-01", _NOW, "mt5", "EURUSD"),
    )
    connection.execute(_INSERT, _row("map-2", "EURUSD.pro", "2024-01-01"))
    rows = connection.execute(
        "SELECT provider_symbol, effective_to FROM broker_symbol_map "
        "ORDER BY effective_from"
    ).fetchall()
    assert rows == [("EURUSD.r", "2024-01-01"), ("EURUSD.pro", None)]


def test_an_as_of_read_returns_the_mapping_that_applied_then(connection):
    """Resolve a past bar to the instrument that was actually traded."""
    connection.execute(
        "UPDATE broker_symbol_map SET effective_to = ?, updated_at = ? "
        "WHERE effective_to IS NULL",
        ("2024-01-01", _NOW),
    )
    connection.execute(_INSERT, _row("map-2", "EURUSD.pro", "2024-01-01"))
    as_of = "2020-06-01"
    historical = connection.execute(
        "SELECT provider_symbol FROM broker_symbol_map "
        "WHERE provider_code = ? AND symbol_id = ? AND effective_from <= ? "
        "AND (effective_to IS NULL OR effective_to > ?) "
        "ORDER BY effective_from DESC",
        ("mt5", "EURUSD", as_of, as_of),
    ).fetchone()[0]
    current = connection.execute(
        "SELECT provider_symbol FROM broker_symbol_map "
        "WHERE provider_code = ? AND symbol_id = ? AND enabled = 1 "
        "AND effective_to IS NULL",
        ("mt5", "EURUSD"),
    ).fetchone()[0]
    assert historical == "EURUSD.r"
    assert current == "EURUSD.pro"


def test_a_provider_symbol_resolves_back_to_its_instrument(connection):
    """Resolve in the reverse direction for an inbound broker message."""
    canonical = connection.execute(
        "SELECT symbol_id FROM broker_symbol_map "
        "WHERE provider_code = ? AND provider_symbol = ? AND enabled = 1 "
        "AND effective_to IS NULL",
        ("mt5", "EURUSD.r"),
    ).fetchone()[0]
    assert canonical == "EURUSD"
