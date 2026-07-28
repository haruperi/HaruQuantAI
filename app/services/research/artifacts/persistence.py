"""Safe masked and atomic Research artifact persistence."""

from __future__ import annotations

import hashlib
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from app.services.research.contracts import (
    ArtifactReference,
    ArtifactWriteConfig,
    ResearchProfileSnapshot,
    ResearchReport,
)
from app.services.research.leakage import mask_research_artifact
from app.services.research.profiles import render_research_report
from app.utils import (
    SecurityError,
    ValidationError,
    canonical_json,
    create_audit_event,
    generate_id,
    get_logger,
)

type AuthContext = Any

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.research.contracts import ResearchResourceLimits
    from app.services.research.leakage.masking import JSONValue as LeakageJSONValue

ArtifactT = ResearchReport | ResearchProfileSnapshot


def _serialize_artifact(artifact: ArtifactT, *, config: ArtifactWriteConfig) -> bytes:
    """Mask and serialize one approved artifact to bytes.

    Args:
        artifact: Report or snapshot to persist.
        config: Approved write policy.

    Returns:
        UTF-8 encoded masked artifact bytes.

    Raises:
        ValidationError: If serialization fails.
    """
    logger.debug("Serializing Research artifact")
    if config.format == "markdown":
        if isinstance(artifact, ResearchReport):
            rendered = render_research_report(artifact, format="markdown")
            if not isinstance(rendered, str):
                raise ValidationError("RES_INPUT_INVALID", "MARKDOWN_RENDER_FAILED")
            return rendered.encode("utf-8")
        raise ValidationError("RES_INPUT_INVALID", "MARKDOWN_REQUIRES_REPORT")
    if isinstance(artifact, ResearchReport):
        payload = {
            "schema_id": artifact.schema_id,
            "report_id": artifact.report_id,
            "hypothesis": artifact.hypothesis,
            "evidence": dict(artifact.evidence),
            "advisory_only": artifact.advisory_only,
        }
    else:
        payload = {
            "schema_version": artifact.schema_version,
            "stages": dict(artifact.stages),
            "advisory_only": artifact.advisory_only,
        }
    masked = mask_research_artifact(cast("LeakageJSONValue", payload))
    return canonical_json(masked).encode("utf-8")


def _validate_destination(destination: Path, *, config: ArtifactWriteConfig) -> Path:
    """Validate that the destination is under the approved root.

    Args:
        destination: Target file path.
        config: Approved write policy.

    Returns:
        The resolved destination.

    Raises:
        SecurityError: If the path escapes the allowed root.
        ValidationError: If the path is invalid.
    """
    logger.debug("Validating Research artifact destination")
    if not destination.is_absolute():
        raise ValidationError("RES_INPUT_INVALID", "DESTINATION_NOT_ABSOLUTE")
    resolved = destination.resolve()
    root = config.allowed_root.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise SecurityError(
            "RES_SENSITIVE_OUTPUT_REJECTED", "ARTIFACT_PATH_TRAVERSAL"
        ) from exc
    return resolved


def _emit_audit_event(
    *, auth: AuthContext, relative_path: Path, size_bytes: int, sha256: str
) -> str:
    """Build and return one redacted artifact-write audit event id.

    Args:
        auth: Authenticated principal context.
        relative_path: Safe relative artifact path.
        size_bytes: Written artifact size.
        sha256: Written content digest.

    Returns:
        The canonical audit event identifier.
    """
    logger.info("Emitting Research artifact audit event")
    event_id = generate_id("evt")
    payload: dict[str, str | int] = {
        "relative_path": relative_path.as_posix(),
        "size_bytes": size_bytes,
        "sha256_prefix": sha256[:16],
    }
    event = create_audit_event(
        contract_version="v1",
        schema_id="utils.audit_event.v1",
        event_id=event_id,
        timestamp=datetime.now(UTC),
        domain="research",
        action="artifact.write",
        principal_id=auth.principal_id,
        request_id=auth.request_id,
        correlation_id=auth.correlation_id,
        causation_id=None,
        payload=payload,
    )
    return event.event_id


def write_research_artifact(
    artifact: ArtifactT,
    destination: Path,
    *,
    config: ArtifactWriteConfig,
    auth: AuthContext,
    limits: ResearchResourceLimits,
) -> ArtifactReference:
    """Mask, validate, and atomically persist one approved Research artifact.

    Args:
        artifact: Report or snapshot to persist.
        destination: Absolute target file path under the approved root.
        config: Approved write policy.
        auth: Authenticated principal context for audit.
        limits: Approved resource ceilings.

    Returns:
        Safe ``ArtifactReference`` with hash, size, and audit identity.

    Raises:
        SecurityError: If the path escapes the allowed root.
        ValidationError: If overwrite, size, atomicity, or serialization fail.
    """
    logger.info("Writing Research artifact")
    data = _serialize_artifact(artifact, config=config)
    if len(data) > limits.max_artifact_bytes:
        raise ValidationError("RES_RESOURCE_LIMIT_EXCEEDED", "ARTIFACT_SIZE_EXCEEDED")
    resolved = _validate_destination(destination, config=config)
    if resolved.exists() and not config.overwrite:
        raise ValidationError("RES_INPUT_INVALID", "ARTIFACT_CONFLICT")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    atomic = config.require_atomic
    if atomic:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(resolved.parent), prefix=".research_", suffix=".tmp"
        )
        os.close(fd)
        try:
            with Path(tmp_path).open("wb") as handle:
                handle.write(data)
            Path(tmp_path).replace(resolved)
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise
    else:
        with Path(resolved).open("wb") as handle:
            handle.write(data)
    sha256 = hashlib.sha256(data).hexdigest()
    relative = resolved.relative_to(config.allowed_root.resolve())
    audit_event_id = _emit_audit_event(
        auth=auth, relative_path=relative, size_bytes=len(data), sha256=sha256
    )
    return ArtifactReference(
        relative_path=relative,
        format=config.format,
        size_bytes=len(data),
        sha256=sha256,
        atomic=atomic,
        schema_version="v1",
        audit_event_id=audit_event_id,
    )


__all__ = ("write_research_artifact",)
