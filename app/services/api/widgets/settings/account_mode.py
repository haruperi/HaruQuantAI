"""Application-wide account-mode resolution for the composed API process.

The operator selects one account mode - ``sim``, ``demo``, or ``live`` - and
that selection is the authoritative application context for execution routing
and runtime-profile marking. Price data is deliberately not mode-dependent:
quotes always come from the configured ``RUNTIME_BROKER``. What follows the
mode is account state - positions, margin, exposure - which follows the route.

Mode semantics (``docs/PROJECT.md`` runtime-profile and execution-route
compatibility):

* ``sim`` executes virtually against the Simulator; nothing reaches a broker.
* ``demo`` and ``live`` share one execution path into the connected MT5
  terminal and differ only by the credentials the operator supplies. The
  distinction the application owns is registry marking, not a technical gate:
  every routed order, thread, and persisted row is stamped with the selected
  profile so demo and live activity can never be confused after the fact.

The persisted ``ACCOUNT_MODE`` system setting is authoritative. Bootstrap
``EXECUTION_ROUTE`` supplies only the default used before an operator has ever
chosen, and an absent or unreadable selection falls back to ``sim`` so the
unresolved state can never move real money.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final, Literal, cast

from app.services.api.identity import get_system_settings
from app.services.api.widgets.settings.bootstrap import get_api_settings
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

type AccountMode = Literal["sim", "demo", "live"]
type ExecutionRoute = Literal["sim", "demo", "live"]
type RuntimeProfile = Literal["simulation", "demo", "live"]

_SETTING_KEY: Final = "ACCOUNT_MODE"
# Selecting an account mode selects its route: the two are the same decision
# expressed in the vocabulary of two boundaries.
_ROUTE_BY_MODE: Final = MappingProxyType({"sim": "sim", "demo": "demo", "live": "live"})
# Trading persists ``simulation`` where the route is named ``sim``; demo and
# live keep their own names precisely so the registry marking survives.
_PROFILE_BY_MODE: Final = MappingProxyType(
    {"sim": "simulation", "demo": "demo", "live": "live"}
)
# Bootstrap ``EXECUTION_ROUTE`` seeds the mode until an operator chooses one.
# A research deployment declares route ``none``; it has no execution authority,
# so it seeds the virtual mode rather than any broker-bound one.
_MODE_BY_BOOTSTRAP_ROUTE: Final = MappingProxyType(
    {"none": "sim", "sim": "sim", "demo": "demo", "live": "live"}
)
_FALLBACK_MODE: Final[AccountMode] = "sim"


def _bootstrap_mode() -> AccountMode:
    """Return the account mode implied by bootstrap execution configuration.

    Returns:
        Account mode seeded from ``EXECUTION_ROUTE``, or the virtual fallback
        when the configured route has no account-mode equivalent.
    """
    route = get_api_settings().execution_route
    mode = _MODE_BY_BOOTSTRAP_ROUTE.get(route)
    if mode is None:
        logger.warning("Bootstrap execution route has no account mode equivalent")
        return _FALLBACK_MODE
    return cast("AccountMode", mode)


def resolve_account_mode(*, request_id: str | None = None) -> AccountMode:
    """Resolve the authoritative application-wide account mode.

    Args:
        request_id: Canonical request identifier for the settings read.

    Returns:
        The operator-selected account mode, the bootstrap-seeded mode when no
        selection is persisted, or ``sim`` when neither resolves.
    """
    trace_id = request_id if request_id is not None else generate_id("req")
    selected = str(
        get_system_settings(request_id=trace_id).settings.get(_SETTING_KEY, "")
    ).strip()
    if not selected:
        return _bootstrap_mode()
    if selected not in _ROUTE_BY_MODE:
        # The manifest constrains writes, so an unknown value means the record
        # predates or bypassed validation. Refuse to guess a broker-bound mode.
        logger.error("Persisted account mode is not a recognized mode")
        return _FALLBACK_MODE
    return cast("AccountMode", selected)


def resolve_execution_route(*, request_id: str | None = None) -> ExecutionRoute:
    """Resolve the execution route the application is currently configured for.

    Args:
        request_id: Canonical request identifier for the settings read.

    Returns:
        Trading execution route matching the active account mode.
    """
    mode = resolve_account_mode(request_id=request_id)
    return cast("ExecutionRoute", _ROUTE_BY_MODE[mode])


def resolve_runtime_profile(*, request_id: str | None = None) -> RuntimeProfile:
    """Resolve the runtime profile that marks activity for the active mode.

    Args:
        request_id: Canonical request identifier for the settings read.

    Returns:
        Runtime profile stamped onto routed orders and persisted rows.
    """
    mode = resolve_account_mode(request_id=request_id)
    return cast("RuntimeProfile", _PROFILE_BY_MODE[mode])


__all__ = (
    "resolve_account_mode",
    "resolve_execution_route",
    "resolve_runtime_profile",
)
