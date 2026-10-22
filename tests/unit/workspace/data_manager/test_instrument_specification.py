"""Verify private instrument storage mappings and unchanged public values."""

from __future__ import annotations

import json
from typing import Any

import pytest
from app.workspace.data_manager.instruments import (
    _FLAT_DEFAULTS,
    _GROUPS,
    _pack,
    _unpack,
)


@pytest.mark.parametrize("mode", range(9))
def test_swap_storage_is_text_but_public_values_remain_numeric(mode: int) -> None:
    row = _pack(
        {
            "symbol": "EURUSD",
            "swap_mode": mode,
            "swap_long": -3.2,
            "swap_short": 1.24,
            "swap_3day_day": 3,
        }
    )
    stored = json.loads(row["swap"])
    assert stored["day3x"] == "Wednesday"
    assert stored["long"] == -3.2
    assert stored["short"] == 1.24
    assert isinstance(stored["mode"], str)
    restored = _unpack(row)
    assert restored["swap_mode"] == mode
    assert restored["swap_3day_day"] == 3
    assert restored["swap_long"] == -3.2
    assert "swap_mode" not in row
    assert "swap_long" not in row


def test_every_existing_flat_field_round_trips_with_its_original_type() -> None:
    flat = {
        **_FLAT_DEFAULTS,
        "symbol": "TEST",
        "decimals": 0,
        "volume": 0,
        "margin_rate": 0,
        "swap_3day_day": 0,
        "filling_mode": 7,
        "order_mode": 127,
        "expiration_mode": 15,
        "commissions": '{ "version": 1, "settings": {"value": 3} }',
        "swap_settings": {"use": True, "long": 0, "short": -2},
    }
    recovered = _unpack(_pack(flat))
    assert recovered == flat
    assert isinstance(recovered["filling_mode"], int)
    assert isinstance(recovered["commissions"], str)
    assert not (set(_GROUPS) - {"volume", "commissions", "spread"}) & set(recovered)


def test_flags_store_labels_and_unknown_codes_round_trip_without_guessing() -> None:
    stored = _pack({"symbol": "TEST", "chart_mode": 0, "filling_mode": 3})
    assert json.loads(stored["price"])["chart_mode"] == "Bid"
    assert json.loads(stored["trade"])["filling"] == [
        "Fill or Kill",
        "Immediate or Cancel",
    ]
    unknown = _pack({"symbol": "TEST", "chart_mode": 999, "order_mode": 128})
    assert json.loads(unknown["price"])["chart_mode"] is None
    restored = _unpack(unknown)
    assert restored["chart_mode"] == 999
    assert restored["order_mode"] == 128


@pytest.mark.parametrize(
    "patch",
    [
        {"price": {"digits": 2}},
        {"swap": {"long": 1}},
        {"tick_size": float("nan")},
        {"volume": {"min": 0.01}},
        {"swap_settings": []},
    ],
)
def test_storage_boundary_rejects_grouped_public_inputs_and_nonfinite_values(
    patch: dict[str, Any],
) -> None:
    with pytest.raises((ValueError, TypeError)):
        _pack({"symbol": "TEST", **patch})


def test_boolean_storage_retains_numeric_public_columns() -> None:
    stored = _pack({"symbol": "TEST", "spread_float": 1, "custom": 0, "select": 1})
    assert json.loads(stored["spread"])["floating"] is True
    assert json.loads(stored["symbol_state"])["custom"] is False
    flat = _unpack(stored)
    assert type(flat["spread_float"]) is int
    assert flat["spread_float"] == 1


@pytest.mark.parametrize(
    "status,rules", [("not_retrieved", None), ("unavailable", None), ("available", [])]
)
def test_commission_statuses_round_trip_without_zero_defaults(
    status: str, rules: Any
) -> None:
    document = {"version": 2, "source": "mt5", "status": status, "rules": rules}
    row = _pack({"symbol": "TEST", "commissions": json.dumps(document)})
    assert json.loads(row["commissions"]) == document
    assert json.loads(_unpack(row)["commissions"]) == document


@pytest.mark.parametrize(
    "document",
    [
        {"version": 2, "source": "mt5", "status": "available", "rules": None},
        {"version": 2, "source": "mt5", "status": "unavailable", "rules": []},
        {"version": 2, "source": "mt5", "status": "bad", "rules": None},
        {"version": 2, "source": "other", "status": "available", "rules": []},
        {"version": 2, "source": "mt5", "status": "available", "rules": [{}]},
        {
            "version": 2,
            "source": "mt5",
            "status": "available",
            "rules": [],
            "settings": {"model": "Per trade", "value": "bad"},
        },
    ],
)
def test_invalid_broker_commission_payload_is_rejected(
    document: dict[str, Any],
) -> None:
    with pytest.raises((ValueError, TypeError)):
        _pack({"symbol": "TEST", "commissions": json.dumps(document)})


@pytest.mark.parametrize(
    "change",
    [
        {"value": True},
        {"value": float("inf")},
        {"min": None},
        {"mode": 1},
        {"volume_type": 1},
    ],
)
def test_invalid_commission_tier_values_are_rejected(change: dict[str, Any]) -> None:
    tier = {
        "mode": "money specified",
        "volume_type": "volume type volume",
        "currency": "USD",
        "effective_currency": "USD",
        "value": 3.5,
        "min": 0.01,
        "max": 0,
        "from": 0,
        "to": 1e9,
        **change,
    }
    rule = {
        "currency": "USD",
        "range": "range volume",
        "charge": "charge instant",
        "entry": "entry inout",
        "direction": "direction both",
        "profit": "profit all",
        "tiers": [tier],
    }
    payload = json.dumps(
        {"version": 2, "source": "mt5", "status": "available", "rules": [rule]}
    )
    with pytest.raises((ValueError, TypeError)):
        _pack({"symbol": "TEST", "commissions": payload})


def test_broker_rule_and_tier_counts_are_bounded() -> None:
    rule = {
        "currency": "USD",
        "range": "range volume",
        "charge": "charge instant",
        "entry": "entry inout",
        "direction": "direction both",
        "profit": "profit all",
        "tiers": [],
    }
    for rules in ([rule] * 257, [{**rule, "tiers": [{}] * 1025}]):
        payload = json.dumps(
            {"version": 2, "source": "mt5", "status": "available", "rules": rules}
        )
        with pytest.raises(ValueError):
            _pack({"symbol": "TEST", "commissions": payload})
