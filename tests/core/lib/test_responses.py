"""Tests for StandardResponse envelope."""

from typing import Any

import pytest
from app.core.lib.responses import StandardResponse


def test_empty_response() -> None:
    payload: dict[str, list[Any]] = {"items": []}
    resp = StandardResponse(request_id="req-001", data=payload)
    assert (
        resp.to_json()
        == b'{"request_id":"req-001","data":{"items":[]},"revision":null}'
    )


def test_response_revision() -> None:
    resp = StandardResponse(request_id="req-002", data=False, revision=0)
    assert resp.data is False
    assert resp.revision == 0
    assert resp.to_dict() == {
        "request_id": "req-002",
        "data": False,
        "revision": 0,
    }

    for invalid_rev in [True, -1, "1"]:
        with pytest.raises(
            ValueError, match="revision must be a non-negative integer or None"
        ):
            StandardResponse(request_id="req-002", data=False, revision=invalid_rev)  # type: ignore[arg-type]


def test_response_detached_and_unicode() -> None:
    source: dict[str, Any] = {"items": ["a"]}
    resp = StandardResponse(request_id="req-003", data=source)
    source["items"].append("b")
    assert resp.to_dict()["data"] == {"items": ["a"]}

    d = resp.to_dict()
    assert isinstance(d["data"], dict)
    assert isinstance(d["data"]["items"], list)
    d["data"]["items"].append("c")
    assert resp.to_dict()["data"] == {"items": ["a"]}
    assert (
        resp.to_json()
        == b'{"request_id":"req-003","data":{"items":["a"]},"revision":null}'
    )

    unicode_resp = StandardResponse(request_id="req-u", data="\ud83d")
    assert (
        unicode_resp.to_json()
        == b'{"request_id":"req-u","data":"\\ud83d","revision":null}'
    )

    with pytest.raises(ValueError, match="value must contain finite JSON values"):
        StandardResponse(request_id="req-nan", data=float("nan"))
