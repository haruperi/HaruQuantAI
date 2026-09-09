"""Bounded offline usage scenarios for FEAT-WS-MANAGE_ARTIFACTS.

Scenario map (FR → demonstrated behavior):
    FR-TRC-WS-MANAGE_ARTIFACTS-001 — publish fixture with verified
    receipt/checksum, idempotent replay, and typed invalid-hash refusal.
    FR-TRC-WS-MANAGE_ARTIFACTS-002 — bounded grant authorization and
    checksum-verified resolution.
    FR-TRC-WS-MANAGE_ARTIFACTS-003 — reference removal while another
    reference remains retains the artifact bytes.
    NFR-TRC-WS-MANAGE_ARTIFACTS-001 — scope close withdraws only
    ``workspace.artifacts@1`` and retains committed custody state.
"""

from __future__ import annotations

import asyncio
import hashlib
import tempfile
from collections.abc import Callable
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast
from uuid import uuid7

from app.contracts.orchestration.capabilities import RESERVE_RESOURCES_CAPABILITY
from app.contracts.workspace.artifacts import (
    AddReferenceRequest,
    ArtifactPublication,
    ArtifactReference,
    ArtifactValidationError,
    AuthorizeDownloadRequest,
    DownloadGrant,
    InspectArtifactRequest,
    PublishArtifactRequest,
    RemoveReferenceRequest,
    ResolveDownloadRequest,
)
from app.contracts.workspace.capabilities import (
    MANAGE_ARTIFACTS_CAPABILITY,
    PERSISTENCE_CAPABILITY,
)
from app.kernel.context import DefaultFeatureContext, FeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.orchestration.reserve_resources._persistence import (
    ResourceReservationStore,
)
from app.services.orchestration.reserve_resources.reserve_resources import (
    ReserveResourcesService,
)
from app.services.workspace.manage_artifacts.feature import feature

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey
    from app.kernel.feature import FeatureSpec
    from app.services.workspace.manage_artifacts.manage_artifacts import (
        ManageArtifactsService,
    )

_FIXTURE = b"haruquantai artifact custody usage fixture\n" * 4
_FIXTURE_HASH = f"sha256:{hashlib.sha256(_FIXTURE).hexdigest()}"
_WORKSPACE_ID = "usage-workspace"
_ACCOUNT_ID = "usage-account"
_PRINCIPAL_ID = "usage-principal"
_ARTIFACT_ID = "usage-artifact-001"
_EXPECTED_REFERENCE_COUNT = 2


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


def _load_entry(name: str) -> _MountableFeature:
    """Load one registered feature factory from the entry-point group.

    Returns:
        Fresh provider feature instance.
    """
    candidates = entry_points(group="haruquantai.features")
    entry = next(entry for entry in candidates if entry.name == name)
    factory = cast("Callable[[], _MountableFeature]", entry.load())
    return factory()


def _publication(
    artifact_id: str,
    *,
    content_hash: str | None = None,
) -> ArtifactPublication:
    """Build one bounded usage publication declaration.

    Returns:
        Configured publication declaration.
    """
    return ArtifactPublication(
        artifact_id=artifact_id,
        workspace_id=_WORKSPACE_ID,
        account_id=_ACCOUNT_ID,
        schema_declaration="application/octet-stream",
        byte_count=len(_FIXTURE),
        content_hash=content_hash or _FIXTURE_HASH,
        idempotency_key=f"usage-key-{artifact_id}",
        source_reference="usage-run-0001",
    )


def _publish_request(publication: ArtifactPublication) -> PublishArtifactRequest:
    """Build one bounded usage publication request.

    Returns:
        Configured publication request.
    """
    return PublishArtifactRequest(
        request_id=str(uuid7()),
        actor_id=_PRINCIPAL_ID,
        publication=publication,
        payload=_FIXTURE,
    )


def _inspect_request() -> InspectArtifactRequest:
    """Build one bounded usage inspection request.

    Returns:
        Configured inspect request.
    """
    return InspectArtifactRequest(
        request_id=str(uuid7()),
        actor_id=_PRINCIPAL_ID,
        artifact_id=_ARTIFACT_ID,
        workspace_id=_WORKSPACE_ID,
        account_id=_ACCOUNT_ID,
    )


def _authorize_request() -> AuthorizeDownloadRequest:
    """Build one bounded usage grant-authorization request.

    Returns:
        Configured authorize-download request.
    """
    return AuthorizeDownloadRequest(
        request_id=str(uuid7()),
        actor_id=_PRINCIPAL_ID,
        artifact_id=_ARTIFACT_ID,
        workspace_id=_WORKSPACE_ID,
        account_id=_ACCOUNT_ID,
        principal_id=_PRINCIPAL_ID,
        ttl_seconds=60,
    )


def _resolve_request(grant: DownloadGrant) -> ResolveDownloadRequest:
    """Build one bounded usage grant-resolution request.

    Returns:
        Configured resolve-download request.
    """
    return ResolveDownloadRequest(
        request_id=str(uuid7()),
        grant=grant,
        workspace_id=_WORKSPACE_ID,
        account_id=_ACCOUNT_ID,
        principal_id=_PRINCIPAL_ID,
    )


def _reference(reference_id: str, owner_namespace: str) -> ArtifactReference:
    """Build one bounded usage semantic reference.

    Returns:
        Configured artifact reference.
    """
    return ArtifactReference(
        reference_id=reference_id,
        artifact_id=_ARTIFACT_ID,
        owner_namespace=owner_namespace,
        owner_record_id="record-0001",
        created_at="",
    )


def _add_reference(reference: ArtifactReference) -> AddReferenceRequest:
    """Build one bounded usage add-reference request.

    Returns:
        Configured add-reference request.
    """
    return AddReferenceRequest(
        request_id=str(uuid7()),
        actor_id=_PRINCIPAL_ID,
        workspace_id=_WORKSPACE_ID,
        reference=reference,
    )


async def _run_usage_example() -> None:  # noqa: C901, PLR0912, PLR0915
    """Exercise publication, authorization, retention, and cleanup.

    Raises:
        RuntimeError: If any expected scenario outcome is not observed.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / "workspace"
        registry = ServiceRegistry()

        persistence_feature = _load_entry("workspace-execute-persistence")
        persistence_scope = FeatureScope(owner_id=persistence_feature.spec.feature_id)
        await _mount(persistence_feature, registry, persistence_scope, {})
        if registry.resolve(PERSISTENCE_CAPABILITY) is None:
            raise RuntimeError("usage persistence capability was not published")

        # Deterministic offline admission: the production provider
        # constructed with synthetic host capacity, because the mounted
        # provider reads the real host disk and a nearly-full host
        # legitimately refuses all disk-writing work.
        admission_service = ReserveResourcesService(
            store=ResourceReservationStore(),
            total_disk_bytes=100 * 1024**3,
            free_disk_bytes=50 * 1024**3,
        )
        admission_scope = FeatureScope(owner_id="FEAT-ORCH-RESERVE_RESOURCES")
        registry.register(
            RESERVE_RESOURCES_CAPABILITY,
            admission_service,
            owner_id="FEAT-ORCH-RESERVE_RESOURCES",
            scope=admission_scope,
        )
        if registry.resolve(RESERVE_RESOURCES_CAPABILITY) is None:
            raise RuntimeError("usage admission capability was not published")

        artifacts_feature = feature()
        artifacts_scope = FeatureScope(owner_id=artifacts_feature.spec.feature_id)
        await _mount(
            artifacts_feature,
            registry,
            artifacts_scope,
            {"database_path": workspace},
        )
        provider = cast(
            "ManageArtifactsService",
            registry.require(MANAGE_ARTIFACTS_CAPABILITY),
        )

        print("Executing Manage Artifacts (_usage) scenarios...")
        print("[1/7] Publishing bounded fixture with verified custody receipt...")
        publication_request = _publish_request(_publication(_ARTIFACT_ID))
        receipt = await provider.publish_artifact(publication_request)
        if receipt.content_hash != _FIXTURE_HASH or receipt.byte_count != len(_FIXTURE):
            raise RuntimeError("usage custody receipt did not verify")
        print(
            f"      Published artifact {receipt.artifact_id} "
            f"({receipt.byte_count} bytes, revision {receipt.storage_revision})"
        )

        print("[2/7] Replaying identical publication (idempotency)...")
        replay = await provider.publish_artifact(publication_request)
        if (
            replay.artifact_id,
            replay.idempotency_key,
            replay.content_hash,
            replay.storage_revision,
        ) != (
            receipt.artifact_id,
            receipt.idempotency_key,
            receipt.content_hash,
            receipt.storage_revision,
        ):
            raise RuntimeError(
                "usage replay did not return the original custody result"
            )
        print("      Replay returned the original custody receipt.")

        print("[3/7] Refusing publication with an invalid content hash...")
        invalid = _publish_request(
            _publication("usage-artifact-invalid", content_hash=f"sha256:{'0' * 64}")
        )
        try:
            await provider.publish_artifact(invalid)
        except ArtifactValidationError:
            print("      Invalid hash rejected before any publication effect.")
        else:
            raise RuntimeError("usage invalid-hash publication was accepted")

        print("[4/7] Authorizing a bounded download grant...")
        grant = await provider.authorize_download(_authorize_request())
        print(f"      Grant issued, expires at {grant.expires_at}")

        print("[5/7] Resolving authorized bytes and verifying checksum...")
        resolved = await provider.resolve_download(_resolve_request(grant))
        if resolved.payload != _FIXTURE or (
            hashlib.sha256(resolved.payload).hexdigest()
            != receipt.content_hash.removeprefix("sha256:")
        ):
            raise RuntimeError("usage resolved bytes did not match the stored checksum")
        print("      Resolved bytes hash to the immutable stored checksum.")

        print("[6/7] Removing one reference while another remains...")
        await provider.add_reference(
            _add_reference(_reference("usage-ref-result", "simulation.result"))
        )
        await provider.add_reference(
            _add_reference(_reference("usage-ref-databank", "databank.membership"))
        )
        inspected = await provider.inspect_artifact(_inspect_request())
        if inspected.reference_count != _EXPECTED_REFERENCE_COUNT:
            raise RuntimeError("usage reference registration did not verify")
        await provider.remove_reference(
            RemoveReferenceRequest(
                request_id=str(uuid7()),
                actor_id=_PRINCIPAL_ID,
                reference_id="usage-ref-result",
                expected_revision=inspected.storage_revision,
            )
        )
        retained = await provider.inspect_artifact(_inspect_request())
        if retained.reference_count != 1:
            raise RuntimeError("usage remaining reference was not retained")
        print("      One reference removed; artifact bytes remain retained.")

        print("[7/7] Closing scope: withdrawal and retained custody...")
        await artifacts_scope.close()
        if registry.resolve(MANAGE_ARTIFACTS_CAPABILITY) is not None:
            raise RuntimeError("usage artifact capability survived scope disposal")
        if registry.resolve(PERSISTENCE_CAPABILITY) is None:
            raise RuntimeError("usage disposal closed shared persistence")
        if registry.resolve(RESERVE_RESOURCES_CAPABILITY) is None:
            raise RuntimeError("usage disposal closed shared admission")

        replacement = feature()
        replacement_scope = FeatureScope(owner_id=replacement.spec.feature_id)
        await _mount(
            replacement,
            registry,
            replacement_scope,
            {"database_path": workspace},
        )
        retained_provider = cast(
            "ManageArtifactsService",
            registry.require(MANAGE_ARTIFACTS_CAPABILITY),
        )
        committed = await retained_provider.inspect_artifact(_inspect_request())
        if committed.content_hash != _FIXTURE_HASH or committed.reference_count != 1:
            raise RuntimeError("usage committed artifact was not retained")

        await replacement_scope.close()
        await admission_scope.close()
        await persistence_scope.close()
        print("[SUCCESS] Manage Artifacts usage: all scenarios passed.")


def main() -> None:
    """Run the bounded offline usage example."""
    asyncio.run(_run_usage_example())


if __name__ == "__main__":
    main()
