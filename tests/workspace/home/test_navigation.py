"""Tests for HomeNavigation metadata."""

from app.workspace.home.navigation import HomeNavigation


def test_navigation_entry() -> None:
    nav = HomeNavigation()
    resp = nav.get(request_id="req-home")
    assert resp.to_dict() == {
        "request_id": "req-home",
        "data": {
            "app_code": "HOME",
            "title": "Getting started",
            "order": 0,
            "section": 0,
            "icon": "home",
        },
        "revision": None,
    }


def test_navigation_is_detached() -> None:
    nav = HomeNavigation()
    resp1 = nav.get(request_id="req-1")
    data_dict = resp1.to_dict()["data"]
    assert isinstance(data_dict, dict)
    data_dict["title"] = "changed"

    resp2 = nav.get(request_id="req-2")
    assert resp2.to_dict()["data"] == {
        "app_code": "HOME",
        "title": "Getting started",
        "order": 0,
        "section": 0,
        "icon": "home",
    }
