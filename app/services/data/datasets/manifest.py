"""Dataset-manifest verification boundary."""

from typing import TYPE_CHECKING

from app.services.data.datasets.contracts import ManifestCompatibility
from app.services.data.persistence.dataset_writer import _load_dataset_raw

if TYPE_CHECKING:
    from app.services.data.contracts import MarketDataset
    from app.services.data.datasets.contracts import DatasetLoadRequest
    from app.services.data.persistence.contracts import StorageManifest


def verify_dataset_manifest(request: DatasetLoadRequest) -> MarketDataset:
    """Verify a dataset manifest and return its canonical dataset.

    Args:
        request: The ``request`` argument.

    Returns:
        The result produced by the operation.
    """
    return _load_dataset_raw(request)


def verify_manifest_compatibility(
    manifest: StorageManifest,
    *,
    expected_schema_version: str,
    expected_normalization_version: str,
) -> ManifestCompatibility:
    """Verify a manifest's schema and normalization version compatibility.

    application Phase 0 reconciliation (`feature`): compatibility
    is checked against caller-declared expectations only; it is never
    inferred or defaulted to compatible.

    Args:
        manifest: Previously written storage manifest to verify.
        expected_schema_version: Schema version the caller currently requires.
        expected_normalization_version: Normalization version the caller
            currently requires.

    Returns:
        Bounded compatibility verdict with a reason per mismatch.
    """
    reasons: list[str] = []
    if manifest.schema_version != expected_schema_version:
        reasons.append(
            f"schema_version mismatch: manifest={manifest.schema_version} "
            f"expected={expected_schema_version}"
        )
    if manifest.normalization_version != expected_normalization_version:
        reasons.append(
            "normalization_version mismatch: "
            f"manifest={manifest.normalization_version} "
            f"expected={expected_normalization_version}"
        )
    return ManifestCompatibility(compatible=not reasons, reasons=tuple(reasons))


__all__ = ["verify_dataset_manifest", "verify_manifest_compatibility"]
