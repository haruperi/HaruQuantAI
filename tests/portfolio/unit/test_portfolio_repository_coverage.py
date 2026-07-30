"""Coverage expansion tests for Portfolio repository operations."""

from unittest.mock import MagicMock

import pytest
from app.services.portfolio.contracts.errors import PortfolioError
from app.services.portfolio.state.repository import (
    PortfolioRepository,
    PortfolioStateStore,
    scope_key,
)


class DummyStore(PortfolioStateStore):
    """Implementation of PortfolioStateStore for testing default base methods."""


def test_scope_key_empty_raises_portfolio_error() -> None:
    """Verify scope_key raises PortfolioError when given empty scope dict."""
    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        scope_key({})


def test_portfolio_repository_init_validation() -> None:
    """Verify PortfolioRepository rejects invalid non-store instances."""
    with pytest.raises(PortfolioError, match="PORT_UNSAFE_OBJECT"):
        PortfolioRepository("not-a-store")  # type: ignore[arg-type]


def test_portfolio_repository_activate_revision_validation() -> None:
    """Verify activate rejects negative expected_revision."""
    mock_store = MagicMock(spec=PortfolioStateStore)
    repo = PortfolioRepository(mock_store)
    mock_alloc = MagicMock(canonical_hash="hash-123")

    with pytest.raises(PortfolioError, match="PORT_INVALID_INPUT"):
        repo.activate(
            mock_alloc,
            expected_predecessor=None,
            expected_revision=-1,
            audit_record={},
        )


def test_portfolio_repository_persistence_failures() -> None:
    """
    Verify repository catches unexpected exceptions and maps them to PORT_PERSISTENCE_FAILED.
    """
    mock_store = MagicMock(spec=PortfolioStateStore)
    mock_store.save_construction.side_effect = RuntimeError("DB write error")
    mock_store.activate_allocation.side_effect = RuntimeError("CAS error")
    mock_store.save_plan.side_effect = RuntimeError("Plan error")
    mock_store.load_allocation.return_value = None
    mock_store.load_plan.return_value = None

    repo = PortfolioRepository(mock_store)
    mock_alloc = MagicMock(canonical_hash="hash-123")

    # save_construction failure
    with pytest.raises(PortfolioError, match="PORT_PERSISTENCE_FAILED"):
        repo.save_construction(MagicMock(), {})

    # activate failure
    with pytest.raises(PortfolioError, match="PORT_PERSISTENCE_FAILED"):
        repo.activate(
            mock_alloc, expected_predecessor=None, expected_revision=0, audit_record={}
        )

    # save_plan failure
    with pytest.raises(PortfolioError, match="PORT_PERSISTENCE_FAILED"):
        repo.save_plan(MagicMock(), {})

    # missing allocation -> PORT_NOT_FOUND
    with pytest.raises(PortfolioError, match="PORT_NOT_FOUND"):
        repo.allocation("port-1", "v1")

    # missing plan -> PORT_NOT_FOUND
    with pytest.raises(PortfolioError, match="PORT_NOT_FOUND"):
        repo.plan("plan-1")


def test_portfolio_state_store_protocol_defaults() -> None:
    """
    Verify base PortfolioStateStore methods raise NotImplementedError when un-overridden.
    """
    store = DummyStore()

    with pytest.raises(NotImplementedError):
        store.save_construction(MagicMock(), {})

    with pytest.raises(NotImplementedError):
        store.activate_allocation(MagicMock(), None, 0, "hash", {})

    with pytest.raises(NotImplementedError):
        store.save_plan(MagicMock(), {})

    with pytest.raises(NotImplementedError):
        store.load_active("port-1", "scope")

    with pytest.raises(NotImplementedError):
        store.load_allocation("port-1", "v1")

    with pytest.raises(NotImplementedError):
        store.load_history("port-1")

    with pytest.raises(NotImplementedError):
        store.load_plan("plan-1", None)
