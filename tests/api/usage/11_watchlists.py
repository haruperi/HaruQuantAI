"""Standalone usage evidence for Account Watchlists (FEAT-API-11)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.kernel.identity import generate_id
from app.services.api import (
    get_default_watchlist_symbols,
    list_account_watchlists,
    run_api_migrations,
)
from app.services.api.identity.persistence.read import read_account_record


def main() -> None:
    """Exercise public watchlist operations against the application database."""
    req_id = generate_id("req")
    run_api_migrations(req_id)

    target_user = "haruquantai"
    rows = read_account_record(target_user, request_id=generate_id("req"))
    if not rows:
        print(f"User '{target_user}' not found in database.")
        return

    account_id = str(rows[0]["user_id"])
    watchlists = list_account_watchlists(
        account_id,
        source_id="mt5",
        request_id=generate_id("req"),
    )

    print(f"\n=== Account Watchlists for '{target_user}' (App Database) ===")
    for wl in watchlists:
        symbol_classes = [
            (item.symbol, item.asset_class) for item in getattr(wl, "items", ())
        ]
        print(
            f"Watchlist: {getattr(wl, 'name', '')} | "
            f"Default: {getattr(wl, 'is_default', False)} | "
            f"Total Symbols ({len(symbol_classes)}):"
        )
        print(f"Symbol Classes: {symbol_classes}\n")

    default_wl = next(
        (w for w in watchlists if w.is_default), watchlists[0] if watchlists else None
    )
    print(
        "Summary:",
        {
            "user": target_user,
            "watchlist_count": len(watchlists),
            "default_watchlist": default_wl.name if default_wl else None,
            "default_watchlist_symbols_count": len(default_wl.items)
            if default_wl
            else 0,
            "system_default_seed_count": len(get_default_watchlist_symbols()),
        },
    )


if __name__ == "__main__":
    main()
