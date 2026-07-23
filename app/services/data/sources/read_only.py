"""Runtime enforcement of Data's read-only broker contract.

``NFR-DATA-006`` states that all Data broker access is read-only and that Data never
invokes a mutation. Until now that was guaranteed by convention plus the Brokers
capability catalogue excluding every ``_WRITE`` capability. Both are sound, but both
enforce the rule *somewhere else*: nothing in Data itself would stop a mutation call if
one were written.

This module makes the guarantee local. ``wrap_broker_client`` returns a proxy that
refuses any method outside a closed allow-list, so a mutation fails at the Data boundary
even when the injected adapter implements it. "Data cannot place a trade" becomes a
property the code asserts rather than a property the code relies on others to maintain.

**The allow-list is closed, not a deny-list.** Denying known-bad names would permit any
mutation nobody thought to list — and a broker SDK adding ``submit_order_v2`` in a minor
release should not silently become reachable. Anything not named here is refused,
including methods that do not exist yet.

Read-only is a Data constraint, not a claim about the adapter. Trading obtains mutation
capability directly from Brokers; nothing here restricts that path.
"""

from __future__ import annotations

from typing import Final, override

from app.services.data.contracts import DataError
from app.utils import logger

__all__ = [
    "READ_ONLY_BROKER_METHODS",
    "ReadOnlyBrokerProxy",
    "verify_read_only_call",
    "wrap_broker_client",
]

# The complete set of broker operations Data may invoke, derived from the call sites
# that exist rather than from the specification.
#
# The Data README proposed a four-name list — `get_bars`, `get_ticks`, `is_connected`,
# `connect`. Applying it literally would have broken two working capabilities:
# `get_bars` is not a real method (`get_historical_bars` is), and account snapshots plus
# symbol discovery call nine further reads that the list omitted. An allow-list built
# from a specification that disagrees with the code is worse than none: it fails closed
# on legitimate reads, which reads as an outage rather than as a policy.
#
# Every name here was verified against an actual call site. `connect` and `is_connected`
# are included because establishing and observing a session is not a market mutation.
# Everything that changes broker-side state is absent by construction.
READ_ONLY_BROKER_METHODS: Final[frozenset[str]] = frozenset(
    {
        # Session lifecycle.
        "connect",
        "is_connected",
        # Market data reads.
        "get_historical_bars",
        "get_ticks",
        "get_spread",
        # Reference reads.
        "get_symbols",
        "get_symbol_info",
        "get_trading_sessions",
        # Account evidence reads.
        "get_account_info",
        "get_balances",
        "get_positions",
        "get_orders",
        "get_permissions",
    }
)


def verify_read_only_call(method_name: str) -> bool:
    """Confirm that one broker method name is permitted for Data.

    Args:
        method_name: Attribute name Data intends to invoke.

    Returns:
        ``True`` when the method is in the closed allow-list.

    Raises:
        DataError: With code ``PERMISSION_DENIED`` when it is not. This raises rather
            than returning ``False`` because a caller that ignored a falsy return would
            proceed to make the very call the check exists to prevent.
    """
    logger.debug("Verifying read-only broker method %s", method_name)
    if method_name not in READ_ONLY_BROKER_METHODS:
        raise DataError(
            "PERMISSION_DENIED",
            safe_details={"method": method_name, "reason": "not_read_only"},
        )
    return True


class ReadOnlyBrokerProxy:
    """A broker adapter facade that exposes only Data's permitted read operations.

    Attribute access is intercepted, so the restriction holds for any call route —
    including a method looked up dynamically by name. Private and dunder attributes are
    refused too: allowing them would let a caller reach the wrapped adapter and bypass
    the proxy entirely.
    """

    __slots__ = ("_client",)

    def __init__(self, client: object) -> None:
        """Wrap one caller-owned broker client.

        Args:
            client: Connected broker adapter owned by the caller. Data neither creates
                nor closes it.
        """
        object.__setattr__(self, "_client", client)

    @override
    def __getattribute__(self, name: str) -> object:
        """Return a permitted broker method, or refuse.

        Args:
            name: Attribute being accessed.

        Returns:
            The underlying bound method when permitted.

        Raises:
            DataError: With code ``PERMISSION_DENIED`` when the name is not in the
                allow-list, including for private and dunder attributes.
        """
        if name in ("__class__", "__repr__", "__doc__", "__slots__"):
            return object.__getattribute__(self, name)
        verify_read_only_call(name)
        return getattr(object.__getattribute__(self, "_client"), name)

    @override
    def __setattr__(self, name: str, value: object) -> None:
        """Refuse every attribute assignment.

        Mutating the proxy — or through it, the wrapped client — would defeat the
        contract this class exists to enforce.

        Args:
            name: Attribute name.
            value: Proposed value.

        Raises:
            DataError: With code ``PERMISSION_DENIED`` always.
        """
        raise DataError(
            "PERMISSION_DENIED",
            safe_details={"attribute": name, "reason": "read_only_proxy_is_immutable"},
        )

    @override
    def __repr__(self) -> str:
        """Return a representation that does not expose the wrapped client.

        Returns:
            A short, secret-safe description.
        """
        return "<ReadOnlyBrokerProxy>"


def wrap_broker_client(client: object) -> ReadOnlyBrokerProxy:
    """Wrap a caller-owned broker client so only read operations are reachable.

    Args:
        client: Connected broker adapter owned by the caller.

    Returns:
        A proxy exposing only the operations in ``READ_ONLY_BROKER_METHODS``. Wrapping
        an already-wrapped client returns it unchanged, so repeated wrapping along a
        call path is harmless.
    """
    if isinstance(client, ReadOnlyBrokerProxy):
        return client
    logger.debug("Wrapping a broker client in the read-only proxy")
    return ReadOnlyBrokerProxy(client)
