"""Golden package-root API coverage for the Data domain."""

from __future__ import annotations

import inspect

from app.services import data


def test_package_root_exports_only_standalone_functions() -> None:
    """Every symbol re-exported in data.__all__ is a callable standalone function."""
    assert len(data.__all__) > 0
    assert len(data.__all__) == len(set(data.__all__))

    for name in data.__all__:
        assert hasattr(data, name), f"Missing public symbol {name}"
        obj = getattr(data, name)
        assert callable(obj), f"Symbol {name} is not callable"
        assert inspect.isfunction(obj), f"Symbol {name} is not a standalone function"
        assert not name.startswith("_"), f"Private symbol {name} exported in __all__"
