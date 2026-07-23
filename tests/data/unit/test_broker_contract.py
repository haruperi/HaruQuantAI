"""Guards for the runtime read-only broker contract.

``NFR-DATA-006`` says Data never invokes a broker mutation. Before Phase 9 that held by
convention and by the Brokers catalogue excluding write capabilities — both real, both
enforced outside Data. ``wrap_broker_client`` makes it a local property.

Two failure modes matter equally and pull in opposite directions:

* **Too permissive** — a mutation reaches the broker. That is the catastrophic one.
* **Too restrictive** — a legitimate read is blocked. That reads as an outage, and it
  is what would have happened had the README's four-name allow-list been applied
  literally: ``get_bars`` is not a real method, and nine reads Data actually makes were
  missing from it.

So these tests assert both directions: every real read passes, and mutations fail even
when the adapter implements them.
"""

from __future__ import annotations

import pytest
from app.services.data.contracts import DataError
from app.services.data.sources.read_only import (
    READ_ONLY_BROKER_METHODS,
    ReadOnlyBrokerProxy,
    verify_read_only_call,
    wrap_broker_client,
)


def test_sources_surface_has_no_account_state_bypass() -> None:
    """Account evidence is reachable only through its read-only evidence owner."""
    from app.services.data import sources

    assert not hasattr(sources, "get_account_state_snapshot")


# Mutation names a broker SDK plausibly exposes. None is in the allow-list, and the
# proxy must refuse all of them even though the stub below implements every one.
MUTATION_METHODS = (
    "trade",
    "place_order",
    "modify_order",
    "cancel_order",
    "close_position",
    "update_account",
    "submit_order",
    "set_leverage",
    "withdraw",
)


class _FullyCapableAdapter:
    """A stub that implements every read *and* every mutation.

    Deliberately more capable than any real read-only adapter: if the proxy relied on
    the underlying object simply lacking mutations, this stub would defeat it. It exists
    to prove the proxy refuses on its own authority.
    """

    def __getattr__(self, name: str) -> object:
        """Return a callable for any attribute at all.

        Args:
            name: Attribute being requested.

        Returns:
            A callable reporting which method was reached.
        """
        return lambda *_args, **_kwargs: f"called:{name}"


@pytest.mark.parametrize("method", sorted(READ_ONLY_BROKER_METHODS))
def test_every_permitted_read_passes_through(method: str) -> None:
    """Assert each allow-listed read reaches the underlying adapter.

    Args:
        method: Permitted method name under test.

    Raises:
        AssertionError: If a legitimate read is blocked.
    """
    proxy = wrap_broker_client(_FullyCapableAdapter())
    assert getattr(proxy, method)() == f"called:{method}"


@pytest.mark.parametrize("method", MUTATION_METHODS)
def test_every_mutation_is_refused(method: str) -> None:
    """Assert a mutation is refused even though the adapter implements it.

    Args:
        method: Mutation method name under test.

    Raises:
        AssertionError: If a mutation reaches the adapter.
    """
    proxy = wrap_broker_client(_FullyCapableAdapter())
    with pytest.raises(DataError) as excinfo:
        getattr(proxy, method)
    assert excinfo.value.code == "PERMISSION_DENIED"


def test_an_unknown_future_method_is_refused() -> None:
    """Assert the allow-list is closed rather than a deny-list.

    A broker SDK adding a method in a minor release must not become reachable from Data
    without an explicit decision. This is the property a deny-list could not provide.

    Raises:
        AssertionError: If an unrecognized method is permitted.
    """
    proxy = wrap_broker_client(_FullyCapableAdapter())
    with pytest.raises(DataError) as excinfo:
        proxy.submit_order_v2_experimental  # noqa: B018
    assert excinfo.value.code == "PERMISSION_DENIED"


def test_the_wrapped_client_cannot_be_reached_through_the_proxy() -> None:
    """Assert private access does not offer an escape hatch.

    If ``_client`` were reachable, a caller could unwrap the adapter and call anything,
    making the proxy decorative.

    Raises:
        AssertionError: If the wrapped client is accessible by attribute.
    """
    proxy = wrap_broker_client(_FullyCapableAdapter())
    with pytest.raises(DataError):
        proxy._client  # noqa: B018


def test_the_proxy_cannot_be_mutated() -> None:
    """Assert attribute assignment on the proxy is refused.

    Raises:
        AssertionError: If the proxy accepts an assignment.
    """
    proxy = wrap_broker_client(_FullyCapableAdapter())
    with pytest.raises(DataError) as excinfo:
        proxy.get_ticks = lambda: "replaced"
    assert excinfo.value.code == "PERMISSION_DENIED"


def test_wrapping_twice_returns_the_same_proxy() -> None:
    """Assert repeated wrapping along a call path is harmless.

    Raises:
        AssertionError: If double wrapping nests proxies.
    """
    once = wrap_broker_client(_FullyCapableAdapter())
    twice = wrap_broker_client(once)
    assert twice is once


def test_verify_raises_rather_than_returning_false() -> None:
    """Assert the check fails loudly for a denied method.

    Returning ``False`` would let a caller that ignored the result proceed to make the
    very call the check exists to prevent.

    Raises:
        AssertionError: If a denied method returns instead of raising.
    """
    assert verify_read_only_call("get_ticks") is True
    with pytest.raises(DataError):
        verify_read_only_call("place_order")


def test_the_allow_list_contains_no_mutation_names() -> None:
    """Assert no mutation name crept into the allow-list.

    Raises:
        AssertionError: If a mutation name is permitted.
    """
    assert not READ_ONLY_BROKER_METHODS & set(MUTATION_METHODS)
    for name in READ_ONLY_BROKER_METHODS:
        assert name.startswith(("get_", "is_")) or name == "connect", (
            f"{name!r} is in the read-only allow-list but does not read like a read."
        )


def test_the_allow_list_covers_every_adapter_call_data_makes() -> None:
    """Assert no adapter method Data actually calls is missing from the allow-list.

    This is the guard against the too-restrictive failure mode. A read that Data makes
    but the list omits would fail closed in production while every unit test using a
    stub adapter kept passing.

    Raises:
        AssertionError: If Data calls an adapter method that is not permitted.
    """
    import re
    from pathlib import Path

    data_root = Path("app/services/data").resolve()
    called: set[str] = set()
    for path in data_root.rglob("*.py"):
        if "__pycache__" in path.parts or path.name == "broker_contract.py":
            continue
        called |= set(re.findall(r"\badapter\.(\w+)", path.read_text(encoding="utf-8")))

    missing = called - READ_ONLY_BROKER_METHODS
    assert not missing, (
        f"Data calls adapter methods that the read-only allow-list omits: "
        f"{sorted(missing)}. Either they are legitimate reads and belong in the list, "
        "or they are mutations and the call site is a boundary violation."
    )


def test_repr_does_not_expose_the_wrapped_client() -> None:
    """Assert the proxy's representation leaks nothing.

    A repr that rendered the adapter could surface credentials or connection detail in
    a log line, which ``NFR-DATA-005`` forbids.

    Raises:
        AssertionError: If the repr exposes the wrapped object.
    """
    proxy = ReadOnlyBrokerProxy(_FullyCapableAdapter())
    assert repr(proxy) == "<ReadOnlyBrokerProxy>"
