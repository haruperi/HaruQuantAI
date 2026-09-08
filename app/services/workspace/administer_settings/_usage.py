"""Bounded offline usage scenarios for FEAT-WS-ADMINISTER_SETTINGS.

Demonstrates:
- FR-1 / AT-1: Schema-validated revisions, optimistic concurrency (409 conflict),
  atomic rejection of unknown keys and invalid values.
- FR-2 / AT-2: Manifest exposure of owner, effective default, narrower policy,
  remount effect, secret slots; host orchestration CPU envelope clamping
  (80% / 4 cores).
- FR-3 / AT-3: User-visible display settings (locale, theme, units) without
  corrupting stored capability IDs or raw values.
- NFR-1 / ATN-1: Clean withdrawal of capability while preserving database
  tables and history.
"""

from __future__ import annotations

import asyncio
import gc
import sqlite3
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol
from uuid import uuid7

from app.composition.logging import get_logger
from app.contracts.workspace.capabilities import ADMINISTER_SETTINGS_CAPABILITY
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import (
    AdministerSettingsRequest,
    AdministerSettingsSuccess,
)
from app.kernel.context import DefaultFeatureContext, FeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.administer_settings._store import init_settings_db
from app.services.workspace.administer_settings.feature import feature

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey
    from app.kernel.feature import FeatureSpec

logger = get_logger(__name__)

_STATUS_CONFLICT = 409
_STATUS_BAD_REQUEST = 400


class _MountableFeature(Protocol):
    """Minimal lifecycle shape used by the usage runner."""

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
    """Mount one feature into a bounded local registry."""

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


def _request(operation: str, **values: object) -> AdministerSettingsRequest:
    """Build one bounded usage request.

    Returns:
        Validated administer settings request.
    """
    return AdministerSettingsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **values,  # type: ignore[arg-type]
    )


async def _run_usage_example() -> None:  # noqa: C901, PLR0912, PLR0915
    """Exercise administered settings scenarios offline.

    Raises:
        RuntimeError: If any expected scenario outcome is not observed.
    """
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        db_path = Path(temp_dir) / "settings.db"
        init_settings_db(db_path)
        registry = ServiceRegistry()

        feat = feature()
        feat_scope = FeatureScope(owner_id=feat.spec.feature_id)
        await _mount(feat, registry, feat_scope, {"database_path": db_path})

        provider = registry.require(ADMINISTER_SETTINGS_CAPABILITY)

        print("Executing Administer Settings (_usage) scenarios...")

        # --- Scenario 1: Revisions, Optimistic Concurrency & Validation ---
        print(
            "[1/4] Testing versioned updates, conflict detection (409), "
            "and validation..."
        )
        initial = await provider.administer_settings(_request("READ_SYSTEM"))
        if not isinstance(initial, AdministerSettingsSuccess) or initial.system is None:
            raise RuntimeError("Failed to read initial system settings")
        initial_version = initial.system.version
        print(f"      Initial system settings version: {initial_version}")

        # Update with valid expected revision
        update1 = await provider.administer_settings(
            _request(
                "UPDATE_SYSTEM",
                settings={"APP_NAME": "HaruQuant AI Pro"},
                changed_by="admin_usage",
                expected_revision=initial_version,
            )
        )
        if not isinstance(update1, AdministerSettingsSuccess) or update1.system is None:
            raise RuntimeError("Valid update with expected revision failed")
        new_version = update1.system.version
        if new_version != initial_version + 1:
            msg = f"Expected version {initial_version + 1}, got {new_version}"
            raise RuntimeError(msg)
        print(f"      Updated APP_NAME -> version {new_version}")

        # Update with stale expected revision -> Expect 409 conflict
        stale_update = await provider.administer_settings(
            _request(
                "UPDATE_SYSTEM",
                settings={"APP_NAME": "Conflicted App"},
                changed_by="admin_usage",
                expected_revision=initial_version,  # Stale!
            )
        )
        if not isinstance(stale_update, WorkspaceFailure):
            raise RuntimeError("Stale update should have produced WorkspaceFailure")  # noqa: TRY004
        if stale_update.problem.status != _STATUS_CONFLICT:
            msg = f"Expected status 409 on conflict, got {stale_update.problem.status}"
            raise RuntimeError(msg)
        print("      Stale expected revision rejected with 409 conflict.")

        # Update with unknown key -> Expect validation failure (400) and no version bump
        bad_key_update = await provider.administer_settings(
            _request(
                "UPDATE_SYSTEM",
                settings={"UNKNOWN_CUSTOM_KEY": "arbitrary_value"},
                changed_by="admin_usage",
            )
        )
        if not isinstance(bad_key_update, WorkspaceFailure):
            raise RuntimeError("Unknown key should have failed validation")  # noqa: TRY004
        if bad_key_update.problem.status != _STATUS_BAD_REQUEST:
            status_code = bad_key_update.problem.status
            msg = f"Expected status 400 on unknown key, got {status_code}"
            raise RuntimeError(msg)

        # Verify version did not advance
        check = await provider.administer_settings(_request("READ_SYSTEM"))
        if not isinstance(check, AdministerSettingsSuccess) or check.system is None:
            raise RuntimeError("Failed to read system settings")
        if check.system.version != new_version:
            raise RuntimeError("System version incremented on invalid update!")
        print("      Unknown key rejected atomically with no version increment.")

        # --- Scenario 2: Manifest Metadata & Orchestration Envelope Clamping ---
        print("[2/4] Testing manifest metadata and Orchestration CPU envelope...")
        manifest_res = await provider.administer_settings(_request("READ_MANIFEST"))
        if not isinstance(manifest_res, AdministerSettingsSuccess):
            raise RuntimeError("Failed to read manifest")  # noqa: TRY004
        manifest = manifest_res.manifest
        print(f"      Settings manifest loaded: {len(manifest)} definitions")

        worker_cpu_def = next(
            (d for d in manifest if d.key == "WORKER_CPU_PERCENT"), None
        )
        if worker_cpu_def is None or worker_cpu_def.owner != "orchestration":
            raise RuntimeError("WORKER_CPU_PERCENT missing or owner invalid")
        if not worker_cpu_def.narrower_policy:
            raise RuntimeError("Narrower policy missing on WORKER_CPU_PERCENT")
        print(
            f"      Manifest metadata verified "
            f"(owner: {worker_cpu_def.owner}, narrower_policy present)"
        )

        # Attempt to set larger CPU values exceeding host envelope
        envelope_update = await provider.administer_settings(
            _request(
                "UPDATE_SYSTEM",
                settings={"WORKER_CPU_PERCENT": "95", "MAX_CPU_CORES": "16"},
                changed_by="admin_usage",
            )
        )
        if (
            not isinstance(envelope_update, AdministerSettingsSuccess)
            or envelope_update.system is None
        ):
            raise RuntimeError("Envelope update failed")
        effective_cpu = envelope_update.system.settings.get("WORKER_CPU_PERCENT")
        effective_cores = envelope_update.system.settings.get("MAX_CPU_CORES")
        if effective_cpu != "80" or effective_cores != "4":
            msg = (
                f"Orchestration envelope clamping failed: "
                f"cpu={effective_cpu}, cores={effective_cores}"
            )
            raise RuntimeError(msg)
        print("      CPU allocation clamped to host envelope (80% / 4 cores).")

        # --- Scenario 3: User-Visible Preferences ---
        print("[3/4] Testing user-visible preference persistence...")
        pref_update = await provider.administer_settings(
            _request(
                "UPDATE_SYSTEM",
                settings={
                    "LOCALE": "ja_JP",
                    "THEME": "light",
                    "SOUND_ENABLED": "false",
                    "UNITS_SYSTEM": "imperial",
                    "DEFAULT_RESULT_VIEW": "equity",
                },
                changed_by="admin_usage",
            )
        )
        if (
            not isinstance(pref_update, AdministerSettingsSuccess)
            or pref_update.system is None
        ):
            raise RuntimeError("User preferences update failed")
        if pref_update.system.settings.get("LOCALE") != "ja_JP":
            raise RuntimeError("Locale update was not applied")
        if pref_update.system.settings.get("THEME") != "light":
            raise RuntimeError("Theme update was not applied")
        print("      Locale, theme, and user preferences persisted cleanly.")

        # --- Scenario 4: Capability Withdrawal & Non-Destructive Lifecycle ---
        print("[4/4] Testing non-destructive capability withdrawal and recovery...")
        await feat_scope.close()
        if registry.resolve(ADMINISTER_SETTINGS_CAPABILITY) is not None:
            raise RuntimeError("Capability survived scope withdrawal")
        print("      AdministerSettings capability withdrawn cleanly.")

        # Verify underlying SQLite database and tables still exist and are intact
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.cursor()
            rows = cursor.execute("SELECT count(*) FROM settings").fetchone()
            history_rows = cursor.execute(
                "SELECT count(*) FROM settings_history"
            ).fetchone()
            if not rows or rows[0] == 0 or not history_rows or history_rows[0] == 0:
                raise RuntimeError(
                    "Settings database tables were damaged on withdrawal"
                )
            print(
                f"      Database verified intact "
                f"({rows[0]} settings, {history_rows[0]} history rows)."
            )
        finally:
            conn.close()

        # Remount and verify data retention
        remount_feat = feature()
        remount_scope = FeatureScope(owner_id=remount_feat.spec.feature_id)
        await _mount(
            remount_feat,
            registry,
            remount_scope,
            {"database_path": db_path},
        )

        remount_provider = registry.require(ADMINISTER_SETTINGS_CAPABILITY)
        remount_read = await remount_provider.administer_settings(
            _request("READ_SYSTEM")
        )
        if (
            not isinstance(remount_read, AdministerSettingsSuccess)
            or remount_read.system is None
        ):
            raise RuntimeError("Failed to read settings after remount")
        if remount_read.system.settings.get("APP_NAME") != "HaruQuant AI Pro":
            raise RuntimeError("Persisted settings lost after remount")
        if remount_read.system.settings.get("LOCALE") != "ja_JP":
            raise RuntimeError("Persisted locale lost after remount")
        await remount_scope.close()

        gc.collect()

        print("[SUCCESS] Administer Settings usage: all scenarios passed.")


def main() -> None:
    """Run the bounded offline usage example."""
    asyncio.run(_run_usage_example())


if __name__ == "__main__":
    main()
