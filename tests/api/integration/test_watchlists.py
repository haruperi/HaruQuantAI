"""Integration evidence for UI/API-owned watchlist persistence and business logic."""

from pathlib import Path

import pytest
from app.services.api import (
    create_account_watchlist,
    delete_account_watchlist,
    get_api_identity_error_type,
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


def _isolated_settings(tmp_path: Path, db_name: str) -> object:
    """Build isolated DATA settings pointing at a fresh temp-path database.

    Returns:
        Validated DATA settings for the isolated test database.
    """
    return build_data_settings(
        database_url=f"sqlite:///{db_name}",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _register(username: str) -> str:
    """Register one bounded test account and return its account id.

    Returns:
        Registered account's stable user id.
    """
    user = register_api_user(
        username=username,
        password="bounded integration password",  # pragma: allowlist secret
        request_id=generate_id("req"),
        tenant_or_environment="development",
        runtime_profile="simulation",
    )
    return user.user_id


def test_list_watchlists_seeds_default_on_first_read(tmp_path: Path) -> None:
    """A brand-new account gets exactly one seeded default watchlist."""
    with data_settings_context(_isolated_settings(tmp_path, "wl-seed.db")):
        migration = run_api_migrations(generate_id("req"))
        assert migration.status == "success"
        account_id = _register("wl-seed-user")

        watchlists = list_account_watchlists(
            account_id, source_id="mt5", request_id=generate_id("req")
        )

        assert len(watchlists) == 1
        assert watchlists[0].name == "default"
        assert watchlists[0].is_default
        assert [item.symbol for item in watchlists[0].items] == list(
            get_default_watchlist_symbols()
        )
        assert all(item.source_id == "mt5" for item in watchlists[0].items)

        # Re-listing must not duplicate the seed.
        again = list_account_watchlists(
            account_id, source_id="mt5", request_id=generate_id("req")
        )
        assert len(again) == 1
        assert again[0].watchlist_id == watchlists[0].watchlist_id


def test_watchlist_crud_lifecycle(tmp_path: Path) -> None:
    """Create, replace items, rename, promote to default, then delete."""
    with data_settings_context(_isolated_settings(tmp_path, "wl-crud.db")):
        migration = run_api_migrations(generate_id("req"))
        assert migration.status == "success"
        account_id = _register("wl-crud-user")
        list_account_watchlists(
            account_id, source_id="mt5", request_id=generate_id("req")
        )

        created = create_account_watchlist(
            account_id, "My Custom", request_id=generate_id("req")
        )
        assert created.name == "My Custom"
        assert not created.is_default
        assert created.items == ()

        updated = replace_account_watchlist_items(
            created.watchlist_id,
            account_id,
            ("EURUSD", "GBPUSD", "XAUUSD"),
            source_id="mt5",
            request_id=generate_id("req"),
        )
        assert [item.symbol for item in updated.items] == [
            "EURUSD",
            "GBPUSD",
            "XAUUSD",
        ]

        renamed = rename_account_watchlist(
            created.watchlist_id,
            account_id,
            "Renamed List",
            request_id=generate_id("req"),
        )
        assert renamed.name == "Renamed List"
        assert [item.symbol for item in renamed.items] == [
            "EURUSD",
            "GBPUSD",
            "XAUUSD",
        ]

        promoted = set_default_account_watchlist(
            created.watchlist_id, account_id, request_id=generate_id("req")
        )
        assert promoted.is_default

        watchlists = list_account_watchlists(
            account_id, source_id="mt5", request_id=generate_id("req")
        )
        defaults = [item for item in watchlists if item.is_default]
        assert len(defaults) == 1
        assert defaults[0].watchlist_id == created.watchlist_id

        old_default = next(
            item for item in watchlists if item.watchlist_id != created.watchlist_id
        )
        assert not old_default.is_default
        delete_account_watchlist(
            old_default.watchlist_id, account_id, request_id=generate_id("req")
        )

        remaining = list_account_watchlists(
            account_id, source_id="mt5", request_id=generate_id("req")
        )
        assert [item.watchlist_id for item in remaining] == [created.watchlist_id]


def test_cannot_delete_the_default_watchlist(tmp_path: Path) -> None:
    """Deleting the current default watchlist is rejected."""
    with data_settings_context(_isolated_settings(tmp_path, "wl-default-guard.db")):
        migration = run_api_migrations(generate_id("req"))
        assert migration.status == "success"
        account_id = _register("wl-guard-user")
        watchlists = list_account_watchlists(
            account_id, source_id="mt5", request_id=generate_id("req")
        )

        with pytest.raises(
            get_api_identity_error_type(), match="WATCHLIST_DEFAULT_UNDELETABLE"
        ):
            delete_account_watchlist(
                watchlists[0].watchlist_id, account_id, request_id=generate_id("req")
            )


def test_watchlist_name_conflict_and_ownership_isolation(tmp_path: Path) -> None:
    """Duplicate names within an account fail; other accounts cannot see it."""
    with data_settings_context(_isolated_settings(tmp_path, "wl-conflict.db")):
        migration = run_api_migrations(generate_id("req"))
        assert migration.status == "success"
        owner_id = _register("wl-owner")
        other_id = _register("wl-stranger")
        list_account_watchlists(
            owner_id, source_id="mt5", request_id=generate_id("req")
        )

        create_account_watchlist(owner_id, "Duplicate", request_id=generate_id("req"))
        with pytest.raises(
            get_api_identity_error_type(), match="WATCHLIST_NAME_CONFLICT"
        ):
            create_account_watchlist(
                owner_id, "Duplicate", request_id=generate_id("req")
            )

        owner_watchlists = list_account_watchlists(
            owner_id, source_id="mt5", request_id=generate_id("req")
        )
        target = next(item for item in owner_watchlists if item.name == "Duplicate")

        with pytest.raises(get_api_identity_error_type(), match="WATCHLIST_NOT_FOUND"):
            rename_account_watchlist(
                target.watchlist_id,
                other_id,
                "Stolen",
                request_id=generate_id("req"),
            )
        with pytest.raises(get_api_identity_error_type(), match="WATCHLIST_NOT_FOUND"):
            delete_account_watchlist(
                target.watchlist_id, other_id, request_id=generate_id("req")
            )
