"""Production reachability evidence for the Brokers symbol-map table."""

from __future__ import annotations

from typing import Any

import pytest
from app.services.brokers import persistence
from app.services.brokers.instrument_profiles import mappings as symbol_map

_RESULT = {"status": "success"}


def test_register_mapping_validates_and_reaches_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reach the insert executor through the production profile operation."""
    captured: dict[str, Any] = {}

    def create(parameters: tuple[object, ...], *, request_id: str) -> object:
        captured["parameters"] = parameters
        captured["request_id"] = request_id
        return _RESULT

    monkeypatch.setattr(persistence, "create_symbol_map_record", create)

    result = symbol_map.register_broker_symbol_mapping(
        "mt5",
        "EURUSD",
        "EURUSD.r",
        request_id="req-symbol",
        effective_from="2026-01-01T00:00:00+00:00",
        contract_size="100000",
        digits_override=5,
    )

    parameters = captured["parameters"]
    assert parameters[1:7] == ("mt5", "EURUSD", "EURUSD.r", "100000", 5, 1)
    assert captured["request_id"] == "req-symbol"
    assert result is _RESULT


@pytest.mark.parametrize("contract_size", ["0", "NaN", "invalid"])
def test_register_mapping_rejects_invalid_contract_size(contract_size: str) -> None:
    """Reject invalid contract size before persistence is reached."""
    with pytest.raises(ValueError, match="contract_size"):
        symbol_map.register_broker_symbol_mapping(
            "mt5",
            "EURUSD",
            "EURUSD.r",
            request_id="req-symbol",
            effective_from="2026-01-01T00:00:00+00:00",
            contract_size=contract_size,
        )


def test_all_administrative_update_operations_reach_their_crud_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Trace close and disable administration to persistence."""
    calls: list[tuple[str, tuple[object, ...], str]] = []

    def capture(name: str):
        def operation(*args: object, request_id: str) -> object:
            calls.append((name, args, request_id))
            return _RESULT

        return operation

    monkeypatch.setattr(persistence, "close_symbol_mapping", capture("close"))
    monkeypatch.setattr(persistence, "disable_symbol_mapping", capture("disable"))

    symbol_map.close_broker_symbol_mapping(
        "mt5", "EURUSD", "2025-01-01", request_id="req-4"
    )
    symbol_map.disable_broker_symbol_mapping("brkmap-1", request_id="req-5")

    assert [call[0] for call in calls] == [
        "close",
        "disable",
    ]
    assert [call[2] for call in calls] == [
        "req-4",
        "req-5",
    ]


def test_symbol_map_administration_rejects_empty_identifiers() -> None:
    """Reject empty administrative identifiers before database execution."""
    with pytest.raises(ValueError, match="provider_code"):
        symbol_map.register_broker_symbol_mapping(
            " ",
            "EURUSD",
            "EURUSD.r",
            request_id="req-symbol",
            effective_from="2026-01-01T00:00:00+00:00",
        )
