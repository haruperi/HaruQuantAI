"""Standalone usage evidence for Account Watchlists (FEAT-API-11)."""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.api import (
    create_account_watchlist,
    delete_account_watchlist,
    get_account_watchlist,
    get_default_watchlist_symbols,
    list_account_watchlists,
    register_api_user,
    rename_account_watchlist,
    replace_account_watchlist_items,
    run_api_migrations,
    set_default_account_watchlist,
)
from app.services.data import build_data_settings, data_settings_context
from app.utils import generate_id


def main() -> None:
    """Exercise every public watchlist operation without broker transport."""
    with TemporaryDirectory() as directory:
        settings = build_data_settings(
            database_url="sqlite:///api-watchlists-usage.db",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(Path(),),
        )
        with data_settings_context(settings):
            run_api_migrations(generate_id("req"))
            account = register_api_user(
                username="watchlists-usage",
                password="bounded usage password",  # pragma: allowlist secret
                request_id=generate_id("req"),
                tenant_or_environment="development",
                runtime_profile="simulation",
            )
            initial = list_account_watchlists(
                account.user_id,
                source_id="mt5",
                request_id=generate_id("req"),
            )
            assert len(initial[0].items) == len(get_default_watchlist_symbols())
            created = create_account_watchlist(
                account.user_id, "Research", request_id=generate_id("req")
            )
            populated = replace_account_watchlist_items(
                created.watchlist_id,
                account.user_id,
                ("EURUSD", "GBPUSD"),
                source_id="mt5",
                request_id=generate_id("req"),
            )
            renamed = rename_account_watchlist(
                populated.watchlist_id,
                account.user_id,
                "Priority",
                request_id=generate_id("req"),
            )
            fetched = get_account_watchlist(
                renamed.watchlist_id,
                account.user_id,
                request_id=generate_id("req"),
            )
            set_default_account_watchlist(
                fetched.watchlist_id,
                account.user_id,
                request_id=generate_id("req"),
            )
            delete_account_watchlist(
                initial[0].watchlist_id,
                account.user_id,
                request_id=generate_id("req"),
            )
            final = list_account_watchlists(
                account.user_id,
                source_id="mt5",
                request_id=generate_id("req"),
            )
            print({"watchlist_count": len(final), "default": final[0].name})


if __name__ == "__main__":
    main()
