"""Unit tests for the exact import-safe Data contract surface."""

from types import ModuleType

from app.services.data import contracts


def test_contract_exports_are_exact_and_import_safe() -> None:
    """Exports are public, provider-neutral, and contain no runtime handle."""
    assert set(contracts.__all__) == {
        name
        for name, value in vars(contracts).items()
        if not name.startswith("_") and not isinstance(value, ModuleType)
    }
    forbidden = {"BrokerAdapter", "Connection", "DataFrame", "Session", "Timer"}
    assert forbidden.isdisjoint(contracts.__all__)
