"""Bounded executable usage demonstration for the watchlist gateway.

The usage harness composes the gateway with a real Workspace watchlist
store; usage modules are the documented exception to the feature-import
boundary so the demonstration exercises the true provider path.
"""

from __future__ import annotations

import asyncio
from uuid import uuid7

from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    OperateWatchlistsRequest,
    OperateWatchlistsSuccess,
)
from app.services.interfaces.operate_watchlists.config import OperateWatchlistsConfig
from app.services.interfaces.operate_watchlists.gateway import WatchlistGateway
from app.services.workspace.manage_watchlists.config import ManageWatchlistsConfig
from app.services.workspace.manage_watchlists.manage_watchlists import WatchlistService

_EXPECTED_SEED_ITEMS = 4


def _request(operation: str, **overrides: object) -> OperateWatchlistsRequest:
    """Build one demonstration gateway request.

    Args:
        operation: Gateway operation discriminator.
        overrides: Optional operation fields.

    Returns:
        Operation-discriminated gateway request.
    """
    return OperateWatchlistsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **overrides,  # type: ignore[arg-type]
    )


async def _run_usage_example() -> None:
    """Run the bounded public usage demonstration.

    Raises:
        RuntimeError: If any verified behavior differs from the contract.
        TypeError: If a verification result has an unexpected type.
    """
    provider = WatchlistService(ManageWatchlistsConfig())
    gateway = WatchlistGateway(provider, OperateWatchlistsConfig())

    listing = await gateway.operate_watchlists(_request("LIST"))
    if not isinstance(listing, OperateWatchlistsSuccess) or not listing.watchlists:
        raise TypeError("usage verification: gateway LIST failed")
    seeded = listing.watchlists[0]
    if not seeded.is_default or len(seeded.items) != _EXPECTED_SEED_ITEMS:
        raise RuntimeError("usage verification: seeding not projected")

    created = await gateway.operate_watchlists(_request("CREATE", name="Usage"))
    if not isinstance(created, OperateWatchlistsSuccess) or created.watchlist is None:
        raise TypeError("usage verification: CREATE failed")

    duplicate = await gateway.operate_watchlists(_request("CREATE", name="Usage"))
    if not isinstance(duplicate, InterfaceFailure):
        raise TypeError("usage verification: collision not mapped")

    gateway.close()
    closed = await gateway.operate_watchlists(_request("LIST"))
    if not isinstance(closed, InterfaceFailure):
        raise TypeError("usage verification: disposal did not fail closed")
    provider.close()
    print(
        "Usage verification passed: "
        f"seeded_items={len(seeded.items)} "
        f"collision_code={duplicate.code} "
        f"closed_code={closed.code}"
    )


if __name__ == "__main__":
    asyncio.run(_run_usage_example())
