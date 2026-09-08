"""Bounded offline usage scenarios for FEAT-WS-MANAGE_ACCOUNTS."""

from __future__ import annotations

import asyncio
import tempfile
from collections.abc import Callable
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast
from uuid import uuid7

from app.contracts.workspace.capabilities import (
    MANAGE_ACCOUNTS_CAPABILITY,
    PERSISTENCE_CAPABILITY,
)
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.manage_accounts import (
    ManageAccountsRequest,
    ManageAccountsSuccess,
)
from app.kernel.context import DefaultFeatureContext, FeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.manage_accounts.feature import feature

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey
    from app.kernel.feature import FeatureSpec
    from app.services.workspace.manage_accounts.accounts import AccountService

_USAGE_PASSWORD = "usage-only-password"  # noqa: S105  # pragma: allowlist secret


class _MountableFeature(Protocol):
    """Minimal public lifecycle shape used by the usage composition."""

    spec: FeatureSpec

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount into the supplied scoped context."""
        ...


async def _mount(
    instance: _MountableFeature,
    registry: ServiceRegistry,
    scope: FeatureScope,
    config: object,
) -> None:
    """Mount one discovered feature into a bounded local registry."""

    def register(
        capability: CapabilityKey[Any],
        implementation: object,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            implementation,
            owner_id=instance.spec.feature_id,
            scope=owner_scope,
        )

    context = DefaultFeatureContext(
        spec=instance.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )
    await instance.mount(context, config)


def _request(operation: str, **values: object) -> ManageAccountsRequest:
    """Build one bounded usage request.

    Returns:
        Validated account operation request.
    """
    return ManageAccountsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        account_id="usage-account",
        workspace_id="usage-workspace",
        **values,  # type: ignore[arg-type]
    )


async def _run_usage_example() -> None:  # noqa: PLR0915
    """Exercise scoped identity, denial, revalidation, retention, and cleanup.

    Raises:
        RuntimeError: If any expected scenario outcome is not observed.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / "workspace"
        registry = ServiceRegistry()

        candidates = entry_points(group="haruquantai.features")
        provider_entry = next(
            entry
            for entry in candidates
            if entry.name == "workspace-execute-persistence"
        )
        provider_factory = cast(
            "Callable[[], _MountableFeature]",
            provider_entry.load(),
        )
        persistence_feature = provider_factory()
        persistence_scope = FeatureScope(owner_id=persistence_feature.spec.feature_id)
        await _mount(persistence_feature, registry, persistence_scope, {})
        if registry.resolve(PERSISTENCE_CAPABILITY) is None:
            raise RuntimeError("usage persistence capability was not published")

        account_feature = feature()
        account_scope = FeatureScope(owner_id=account_feature.spec.feature_id)
        await _mount(
            account_feature,
            registry,
            account_scope,
            {"database_path": workspace},
        )
        provider = registry.require(MANAGE_ACCOUNTS_CAPABILITY)

        print("Executing Manage Accounts (_usage) scenarios...")
        print("[1/4] Registering user with scrypt password hashing...")
        registered = await provider.manage_accounts(
            _request(
                "REGISTER",
                username="usage_user",
                password=_USAGE_PASSWORD,
            )
        )
        if not isinstance(registered, ManageAccountsSuccess) or registered.user is None:
            raise RuntimeError("usage registration did not succeed")
        session_token = registered.session_token
        captured = registered.user
        print(f"      Registered user: {captured.username} (ID: {captured.user_id})")

        print("[2/4] Validating active session claims via ME...")
        current = await provider.manage_accounts(
            _request("ME", session_token=session_token)
        )
        if not isinstance(current, ManageAccountsSuccess) or current.user != captured:
            raise RuntimeError("usage current-scope verification failed")
        print(
            f"      Session valid for: {current.user.username}, "
            f"expires: {current.user.expires_at}"
        )

        print("[3/4] Enforcing scope isolation (mismatched account/workspace)...")
        wrong_scope = await provider.manage_accounts(
            ManageAccountsRequest(
                request_id=str(uuid7()),
                capability_snapshot_id=str(uuid7()),
                operation="ME",
                account_id="different-account",
                workspace_id="usage-workspace",
                session_token=session_token,
            )
        )
        if not isinstance(wrong_scope, WorkspaceFailure):
            raise RuntimeError(  # noqa: TRY004 - verifies a domain result.
                "usage wrong-account verification did not fail"
            )
        print("      Mismatched scope access denied successfully.")

        print("[4/4] Revoking session via LOGOUT and asserting revalidation denial...")
        await provider.manage_accounts(_request("LOGOUT", session_token=session_token))
        revalidated = await provider.manage_accounts(
            _request("ME", session_token=session_token)
        )
        if not isinstance(revalidated, WorkspaceFailure):
            raise RuntimeError(  # noqa: TRY004 - verifies a domain result.
                "usage revoked snapshot was trusted"
            )
        print("      Revoked session token denied on subsequent ME revalidation.")

        service = cast("AccountService", provider)
        audit_rows = service.safe_session_audit_records(
            request_id=str(uuid7()),
            account_id="usage-account",
        )
        if not audit_rows or (
            audit_rows[0].authentication_audit_ref != captured.authentication_audit_ref
        ):
            raise RuntimeError("usage safe audit reference was not retained")

        await account_scope.close()
        if registry.resolve(MANAGE_ACCOUNTS_CAPABILITY) is not None:
            raise RuntimeError("usage account capability survived scope disposal")
        if registry.resolve(PERSISTENCE_CAPABILITY) is None:
            raise RuntimeError("usage account disposal closed shared persistence")

        replacement = feature()
        replacement_scope = FeatureScope(owner_id=replacement.spec.feature_id)
        await _mount(
            replacement,
            registry,
            replacement_scope,
            {"database_path": workspace},
        )
        retained_provider = registry.require(MANAGE_ACCOUNTS_CAPABILITY)
        retained_login = await retained_provider.manage_accounts(
            _request(
                "LOGIN",
                username="usage_user",
                password=_USAGE_PASSWORD,
            )
        )
        if not isinstance(retained_login, ManageAccountsSuccess):
            raise RuntimeError(  # noqa: TRY004 - verifies a domain result.
                "usage retained account was unavailable after remount"
            )

        await replacement_scope.close()
        await persistence_scope.close()
        print("[SUCCESS] Manage Accounts usage: all scenarios passed.")


def main() -> None:
    """Run the bounded offline usage example."""
    asyncio.run(_run_usage_example())


if __name__ == "__main__":
    main()
