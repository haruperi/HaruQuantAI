"""Tests for DomainError and JSONValue handling."""

from typing import Any

import pytest
from app.core.lib.errors import DomainError, copy_json


def test_error_defaults() -> None:
    err = DomainError(code="NOT_FOUND", message="missing")
    assert err.to_dict() == {"code": "NOT_FOUND", "message": "missing", "details": {}}
    assert str(err) == "missing"
    assert err.code == "NOT_FOUND"
    assert err.message == "missing"


def test_error_rejects_invalid_json() -> None:
    for invalid in [float("nan"), float("inf"), (1, 2), {1: "x"}]:
        invalid_details: Any = {"key": invalid}
        with pytest.raises(ValueError, match="value must contain finite JSON values"):
            DomainError(code="ERR", message="msg", details=invalid_details)
        with pytest.raises(ValueError, match="value must contain finite JSON values"):
            copy_json(invalid)  # type: ignore[arg-type]

    cyclic: list[Any] = []
    cyclic.append(cyclic)
    cyclic_details: Any = {"c": cyclic}
    with pytest.raises(ValueError, match="value must not contain cycles"):
        DomainError(code="ERR", message="msg", details=cyclic_details)
    with pytest.raises(ValueError, match="value must not contain cycles"):
        copy_json(cyclic)


def test_error_is_detached() -> None:
    source: dict[str, Any] = {"ids": ["a"]}
    err = DomainError(code="ERR", message="msg", details=source)
    source["ids"].append("b")
    assert err.details == {"ids": ["a"]}
    assert err.to_dict()["details"] == {"ids": ["a"]}

    d1 = err.to_dict()
    assert isinstance(d1["details"], dict)
    assert isinstance(d1["details"]["ids"], list)
    d1["details"]["ids"].append("c")
    d2 = err.to_dict()
    assert d2["details"] == {"ids": ["a"]}
