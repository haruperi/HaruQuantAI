"""Schema-level evidence for the private Analytics persistence package.

Analytics persistence is internal support, not a registered feature, so this
evidence lives in pytest rather than in a numbered usage program. Analytics
stores only derived values, and each test below asserts a property that keeps a
derived value honest about what produced it.
"""

import sqlite3
from decimal import Decimal

import pytest
from app.services.analytics.migrations.definitions import (
    _ANALYTICS_SCHEMA_STATEMENTS,
)

_NOW = "2026-08-03T00:00:00.000Z"

_INSERT_VALUE = (
    "INSERT INTO analytics_metric_values (value_id, metric_id, scope_level, "
    "scope_key, period_kind, period_start_utc, period_end_utc, value_decimal, "
    "sample_size, insufficient_sample, source_hash, computed_at, created_at) "
    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
)

_INSERT_TRADE = (
    "INSERT INTO analytics_trade_analysis (trade_id, source_kind, run_id, "
    "position_id, account_id, symbol_id, strategy_version_id, direction, "
    "entry_price_decimal, exit_price_decimal, quantity_decimal, "
    "gross_pnl_decimal, net_pnl_decimal, commission_decimal, swap_decimal, "
    "slippage_decimal, r_multiple_decimal, mae_decimal, mfe_decimal, "
    "holding_seconds, bars_held, exit_reason, regime_id, entry_at, exit_at, "
    "source_hash, created_at) "
    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
)


@pytest.fixture
def connection():
    """Yield an in-memory database carrying the Analytics schema."""
    con = sqlite3.connect(":memory:")
    for statement in _ANALYTICS_SCHEMA_STATEMENTS:
        con.execute(statement)
    con.execute(
        "INSERT INTO analytics_metric_definitions (metric_id, metric_code, "
        "version, category, formula_hash, min_sample_size, requires_benchmark, "
        "higher_is_better, unit, definition_json, state, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "m-sharpe",
            "sharpe",
            "v1",
            "ratio",
            "formula-hash-sharpe",
            30,
            0,
            1,
            "ratio",
            "{}",
            "active",
            _NOW,
            _NOW,
        ),
    )
    yield con
    con.close()


def test_a_null_value_must_declare_an_insufficient_sample(connection):
    """Make a null measurement presented as a real one unrepresentable."""
    with pytest.raises(sqlite3.IntegrityError, match="insufficient_sample"):
        connection.execute(
            _INSERT_VALUE,
            (
                "v-bad",
                "m-sharpe",
                "strategy",
                "strat-1",
                "all_time",
                1_700_000_000,
                1_702_591_999,
                None,
                9,
                0,
                "src-hash-v1",
                _NOW,
                _NOW,
            ),
        )


def test_an_undersized_sample_is_recordable_as_such(connection):
    """Accept a null value once it declares the sample was too small."""
    connection.execute(
        _INSERT_VALUE,
        (
            "v-honest",
            "m-sharpe",
            "strategy",
            "strat-1",
            "all_time",
            1_700_000_000,
            1_702_591_999,
            None,
            9,
            1,
            "src-hash-v1",
            _NOW,
            _NOW,
        ),
    )
    row = connection.execute(
        "SELECT sample_size, insufficient_sample FROM analytics_metric_values "
        "WHERE value_id = ?",
        ("v-honest",),
    ).fetchone()
    assert row == (9, 1)


def test_excursion_distinguishes_two_identical_winners(connection):
    """Keep a trade that ran against the position distinct from one that did not."""
    for trade_id, mae in (("t-calm", "0"), ("t-rough", "-310")):
        connection.execute(
            _INSERT_TRADE,
            (
                trade_id,
                "live",
                None,
                f"pos-{trade_id}",
                "acct-1",
                "EURUSD",
                "sv-1",
                "long",
                "1.0800",
                "1.0812",
                "1.0",
                "120",
                "118",
                "2",
                "0",
                "0",
                "1.2",
                mae,
                "120",
                3_600,
                60,
                "take_profit",
                None,
                _NOW,
                _NOW,
                "src-hash-v1",
                _NOW,
            ),
        )
    rows = connection.execute(
        "SELECT net_pnl_decimal, mae_decimal FROM analytics_trade_analysis "
        "ORDER BY trade_id"
    ).fetchall()
    assert len({row[0] for row in rows}) == 1
    assert len({row[1] for row in rows}) == 2


def test_attribution_factors_are_unique_per_scope_and_period(connection):
    """Reject a second contribution for one factor in one window."""
    row = (
        "attr-1",
        "strategy",
        "strat-1",
        1_700_000_000,
        1_702_591_999,
        "commission",
        "-4",
        "0",
        2,
        "src-hash-v1",
        _NOW,
        _NOW,
    )
    statement = (
        "INSERT INTO analytics_pnl_attribution (attribution_id, scope_level, "
        "scope_key, period_start_utc, period_end_utc, factor, "
        "contribution_decimal, contribution_percent_decimal, trade_count, "
        "source_hash, computed_at, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"
    )
    connection.execute(statement, row)
    with pytest.raises(sqlite3.IntegrityError, match="factor"):
        connection.execute(statement, ("attr-2", *row[1:]))
    total = sum(
        Decimal(value)
        for (value,) in connection.execute(
            "SELECT contribution_decimal FROM analytics_pnl_attribution"
        )
    )
    assert total == Decimal(-4)


def test_superseded_inputs_mark_a_curve_stale_rather_than_delete_it(connection):
    """Preserve what was reported when a decision was made."""
    connection.execute(
        "INSERT INTO analytics_equity_curves (curve_id, scope_level, scope_key, "
        "dataset_id, period_start_utc, period_end_utc, point_count, "
        "start_equity_decimal, end_equity_decimal, peak_equity_decimal, "
        "trough_equity_decimal, max_drawdown_decimal, "
        "max_drawdown_percent_decimal, max_drawdown_start_utc, "
        "max_drawdown_end_utc, recovery_ts_utc, source_hash, state, "
        "computed_at, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "curve-1",
            "strategy",
            "strat-1",
            "ds-equity-strat-1",
            1_700_000_000,
            1_702_591_999,
            43_200,
            "10000",
            "10118",
            "10240",
            "9820",
            "420",
            "4.1",
            1_700_500_000,
            1_701_000_000,
            None,
            "src-hash-v1",
            "ready",
            _NOW,
            _NOW,
            _NOW,
        ),
    )
    connection.execute(
        "UPDATE analytics_equity_curves SET state = 'stale', updated_at = ? "
        "WHERE scope_level = ? AND scope_key = ? AND source_hash <> ?",
        (_NOW, "strategy", "strat-1", "src-hash-v2"),
    )
    row = connection.execute(
        "SELECT state, recovery_ts_utc FROM analytics_equity_curves WHERE curve_id = ?",
        ("curve-1",),
    ).fetchone()
    assert row == ("stale", None)
