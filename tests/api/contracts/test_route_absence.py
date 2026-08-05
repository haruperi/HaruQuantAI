"""Authoritative exclusions enforced as route absence.

Every family asserted absent here is excluded for a recorded reason, not
because it is unfinished work:

* Documentation file I/O is withdrawn scope (`NFR-API-015` and `CAP-UI-019`
  retired under `API-CLOSE-002`); the gateway must still own no file I/O.
* Production-capital execution is no longer excluded: live reuses the single
  Trading surface and is gated by deployment settings, not by route absence.
  What stays enforced here is that no *parallel* live route family appears.

If any assertion here starts failing, a boundary grew without the
corresponding decision being revisited.
"""

from app.services.api import create_api_app


def _paths() -> tuple[str, ...]:
    """Return the canonical OpenAPI path inventory.

    Returns:
        Every registered path in the canonical application.
    """
    return tuple(create_api_app().openapi()["paths"])


def test_gateway_owns_no_documentation_file_io() -> None:
    """The gateway never grows a documentation file surface.

    This is a boundary invariant, not a pending exclusion. `NFR-API-015` and
    `CAP-UI-019` were retired as withdrawn scope under `API-CLOSE-002`: no
    domain owns documentation persistence, and UI/API's "Does not own" section
    forbids the gateway from owning file I/O. If a documentation capability is
    ever wanted, it needs an owning domain first — not a route here.
    """
    paths = _paths()
    assert not any("/docs/" in path for path in paths)
    assert not any("/documentation" in path for path in paths)


def test_live_what_if_reuses_the_session_surface() -> None:
    """Live what-if is exposed as sessions, not as ad-hoc mutation routes.

    `WF-API-008` closed under `API-CLOSE-002` once the Simulator gained a
    resumable engine. What stays enforced is the shape: branching is a session
    operation with recorded lineage, so no route may mutate a completed run in
    place.
    """
    paths = _paths()
    assert "/api/v1/simulation/live-sessions" in paths
    assert "/api/v1/simulation/live-sessions/{session_id}/branch" in paths
    # Completed-run playback remains a separate read-only surface.
    assert "/api/v1/simulation/sessions" in paths
    assert "/api/v1/simulation/sessions/{session_id}/frames" in paths
    # No route mutates a completed run in place.
    assert not any(path.endswith("/results/{run_id}/mutate") for path in paths)


def test_no_separate_live_execution_surface_exists() -> None:
    """Live execution reuses the one Trading surface rather than adding another.

    Paper and live differ only by the credentials in the composed
    `BrokerConnectionConfig`, so there is deliberately no parallel live route
    family. Reachability is a deployment-settings question, enforced in
    `routes/trading.py::_governed_preflight` and covered by
    `tests/api/unit/test_trading_routes.py`, not a routing question.
    """
    paths = _paths()
    assert not any("/live/" in path for path in paths)
    assert not any(path.endswith("/execute-live") for path in paths)
    assert "/api/v1/trading/orders" in paths
    assert "/api/v1/trading/session" in paths


def test_rejected_operator_surfaces_are_absent() -> None:
    """Rejected duplicate surfaces stay absent.

    These are rejected and resolved, not outstanding scope. Each would be a
    second path to a capability the boundary already exposes exactly once, so
    reintroducing one would make the surface ambiguous rather than more
    capable. The assertions below pair each rejected path with the approved one
    it would have duplicated.
    """
    paths = _paths()
    assert "/api/v1/operator/kill-switch" not in paths
    assert "/api/v1/risk/kill-switch" in paths
    assert "/api/v1/operator/readiness" not in paths
    assert "/api/v1/health/readiness" in paths
