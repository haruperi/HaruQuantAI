"""CRUD and invariant tests for the manage-watchlists feature."""

from __future__ import annotations

from uuid import uuid7

import pytest
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import (
    ManageWatchlistsRequest,
    ManageWatchlistsSuccess,
)
from app.services.workspace.manage_watchlists.config import ManageWatchlistsConfig
from app.services.workspace.manage_watchlists.manage_watchlists import WatchlistService
from app.services.workspace.manage_watchlists.manifest import SPEC

ACCOUNT = "acct-1"


def _request(
    operation: str,
    **overrides: object,
) -> ManageWatchlistsRequest:
    """Build one operation request."""
    return ManageWatchlistsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        account_id=ACCOUNT,
        operation=operation,  # type: ignore[arg-type]
        **overrides,  # type: ignore[arg-type]
    )


def _success(result: object) -> ManageWatchlistsSuccess:
    """Narrow a successful result."""
    assert isinstance(result, ManageWatchlistsSuccess)
    return result


def test_manifest_spec() -> None:
    """Verify feature specification and declared durable state."""
    assert SPEC.feature_id == "FEAT-WS-MANAGE_WATCHLISTS"
    (provided,) = SPEC.provides
    assert provided.identifier == "workspace.manage-watchlists@1"
    assert SPEC.state is not None
    assert SPEC.state.namespace == "workspace.manage_watchlists"
    SPEC.validate()


@pytest.mark.asyncio
async def test_first_list_seeds_curated_default() -> None:
    """Verify per-account seeding with exactly one default."""
    service = WatchlistService(ManageWatchlistsConfig())
    listing = _success(await service.manage_watchlists(_request("LIST")))

    assert len(listing.watchlists) == 1
    seeded = listing.watchlists[0]
    assert seeded.is_default is True
    assert seeded.name == "Default"
    assert [item.symbol for item in seeded.items] == [
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "XAUUSD",
    ]
    service.close()


@pytest.mark.asyncio
async def test_create_rename_and_uniqueness() -> None:
    """Verify create, rename, and unique (account, name)."""
    service = WatchlistService(ManageWatchlistsConfig())
    created = _success(
        await service.manage_watchlists(_request("CREATE", name="Scalping"))
    )
    assert created.watchlist is not None
    watchlist_id = created.watchlist.watchlist_id

    duplicate = await service.manage_watchlists(_request("CREATE", name="Scalping"))
    assert isinstance(duplicate, WorkspaceFailure)
    assert duplicate.code == "WORKSPACE_VALIDATION_FAILED"

    renamed = _success(
        await service.manage_watchlists(
            _request("UPDATE", watchlist_id=watchlist_id, name="Swing")
        )
    )
    assert renamed.watchlist is not None
    assert renamed.watchlist.name == "Swing"

    default = _success(await service.manage_watchlists(_request("CREATE", name="Temp")))
    assert default.watchlist is not None
    clash = await service.manage_watchlists(
        _request("UPDATE", watchlist_id=default.watchlist.watchlist_id, name="Swing")
    )
    assert isinstance(clash, WorkspaceFailure)
    service.close()


@pytest.mark.asyncio
async def test_default_promote_exactly_one_and_delete_guard() -> None:
    """Verify exactly-one-default promotion and default deletion guard."""
    service = WatchlistService(ManageWatchlistsConfig())
    listing = _success(await service.manage_watchlists(_request("LIST")))
    seeded = listing.watchlists[0]
    created = _success(
        await service.manage_watchlists(_request("CREATE", name="Second"))
    )
    assert created.watchlist is not None

    promoted = _success(
        await service.manage_watchlists(
            _request(
                "UPDATE", watchlist_id=created.watchlist.watchlist_id, is_default=True
            )
        )
    )
    assert promoted.watchlist is not None
    assert promoted.watchlist.is_default is True

    after = _success(await service.manage_watchlists(_request("LIST")))
    defaults = [item for item in after.watchlists if item.is_default]
    assert len(defaults) == 1
    assert defaults[0].watchlist_id == created.watchlist.watchlist_id

    blocked = await service.manage_watchlists(
        _request("DELETE", watchlist_id=created.watchlist.watchlist_id)
    )
    assert isinstance(blocked, WorkspaceFailure)

    demote = await service.manage_watchlists(
        _request(
            "UPDATE", watchlist_id=created.watchlist.watchlist_id, is_default=False
        )
    )
    assert isinstance(demote, WorkspaceFailure)

    deleted = _success(
        await service.manage_watchlists(
            _request("DELETE", watchlist_id=seeded.watchlist_id)
        )
    )
    assert deleted.deleted is True
    service.close()


@pytest.mark.asyncio
async def test_item_replacement_preserves_known_asset_classes() -> None:
    """Verify complete ordered item replacement."""
    service = WatchlistService(ManageWatchlistsConfig())
    listing = _success(await service.manage_watchlists(_request("LIST")))
    seeded = listing.watchlists[0]

    updated = _success(
        await service.manage_watchlists(
            _request(
                "UPDATE",
                watchlist_id=seeded.watchlist_id,
                symbols=("EURUSD", "USDCHF"),
            )
        )
    )
    assert updated.watchlist is not None
    assert [item.symbol for item in updated.watchlist.items] == ["EURUSD", "USDCHF"]
    assert updated.watchlist.items[0].asset_class == "Forex"
    assert updated.watchlist.items[1].asset_class == ""

    missing = await service.manage_watchlists(
        _request("DELETE", watchlist_id=str(uuid7()))
    )
    assert isinstance(missing, WorkspaceFailure)
    assert missing.code == "WORKSPACE_NOT_FOUND"
    service.close()


@pytest.mark.asyncio
async def test_accounts_are_isolated() -> None:
    """Verify per-account scoping and seeding."""
    service = WatchlistService(ManageWatchlistsConfig())
    other = _success(
        await service.manage_watchlists(
            ManageWatchlistsRequest(
                request_id=str(uuid7()),
                capability_snapshot_id=str(uuid7()),
                account_id="acct-2",
                operation="LIST",
            )
        )
    )
    assert len(other.watchlists) == 1
    assert other.watchlists[0].account_id == "acct-2"

    first = _success(await service.manage_watchlists(_request("LIST")))
    assert first.watchlists[0].account_id == ACCOUNT
    service.close()
