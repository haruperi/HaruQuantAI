"""Application-wide account-mode resolution tests.

The account mode is the single decision that determines which execution route
the application runs on and which runtime profile every routed order and
persisted row is stamped with, so these tests pin both the happy path and the
fail-closed behaviour on unreadable or unrecognized state.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.services.api.widgets.settings import account_mode


def _stored(monkeypatch: pytest.MonkeyPatch, value: str | None) -> None:
    """Pin the persisted system-settings document the resolver reads.

    Args:
        monkeypatch: Test patcher.
        value: Persisted ACCOUNT_MODE value, or None for an absent setting.
    """
    settings = {} if value is None else {"ACCOUNT_MODE": value}
    monkeypatch.setattr(
        account_mode,
        "get_system_settings",
        lambda **_: SimpleNamespace(settings=settings),
    )


def _bootstrap(monkeypatch: pytest.MonkeyPatch, execution_route: str) -> None:
    """Pin the bootstrap execution route used before any selection exists.

    Args:
        monkeypatch: Test patcher.
        execution_route: Bootstrap EXECUTION_ROUTE value.
    """
    monkeypatch.setattr(
        account_mode,
        "get_api_settings",
        lambda: SimpleNamespace(execution_route=execution_route),
    )


@pytest.mark.parametrize(
    ("mode", "route", "profile"),
    [
        ("sim", "sim", "simulation"),
        ("demo", "demo", "demo"),
        ("live", "live", "live"),
    ],
)
def test_selected_mode_drives_route_and_profile(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    route: str,
    profile: str,
) -> None:
    """The operator's selection is the authority for both boundaries.

    Trading names the virtual profile ``simulation`` where the route names it
    ``sim``; demo and live keep their own names so the registry marking that
    separates them survives into persisted rows.
    """
    _stored(monkeypatch, mode)
    assert account_mode.resolve_account_mode() == mode
    assert account_mode.resolve_execution_route() == route
    assert account_mode.resolve_runtime_profile() == profile


def test_live_is_reachable_purely_by_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Selecting live routes to live even from a demo bootstrap.

    This is the point of the setting: the operator elects the mode at runtime,
    and the deployment's boot configuration does not veto it.
    """
    _bootstrap(monkeypatch, "demo")
    _stored(monkeypatch, "live")
    assert account_mode.resolve_execution_route() == "live"


@pytest.mark.parametrize(
    ("bootstrap_route", "expected"),
    [("sim", "sim"), ("demo", "demo"), ("live", "live"), ("none", "sim")],
)
def test_bootstrap_seeds_the_mode_before_any_selection(
    monkeypatch: pytest.MonkeyPatch,
    bootstrap_route: str,
    expected: str,
) -> None:
    """With nothing persisted the boot route seeds the mode.

    A research deployment declares route ``none`` and has no execution
    authority at all, so it seeds the virtual mode rather than a broker-bound
    one.
    """
    _stored(monkeypatch, None)
    _bootstrap(monkeypatch, bootstrap_route)
    assert account_mode.resolve_account_mode() == expected


def test_an_unrecognized_stored_mode_fails_closed_to_sim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A value that bypassed the manifest never resolves to a broker route.

    The manifest constrains writes, so this state should be unreachable; if it
    is ever reached the resolver refuses to guess a mode that could move real
    money.
    """
    _stored(monkeypatch, "paper")
    assert account_mode.resolve_account_mode() == "sim"
    assert account_mode.resolve_execution_route() == "sim"


def test_an_unusable_bootstrap_route_fails_closed_to_sim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unmappable boot route seeds the virtual mode rather than failing."""
    _stored(monkeypatch, None)
    _bootstrap(monkeypatch, "not-a-route")
    assert account_mode.resolve_account_mode() == "sim"
