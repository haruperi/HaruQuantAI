"""Host settings REST API endpoints and payload projection.

Description:
    Exposes FastAPI routes for host settings management, including reading the
    public settings snapshot, executing atomic preference updates with revision
    guards, projecting the safe settings catalogue, and updating write-only
    secrets without echoing sensitive material. Acts as the dedicated API
    bridge between browser UI components and the pure business logic in
    HostSettings.

Purpose:
    FEAT-API-SETTINGS: Dedicated REST API routing and payload projection for
    host configuration settings.

Key Capabilities:
    - FR-API-SETTINGS-READ: Project public settings snapshot over HTTP.
      Associated: `get_settings_endpoint()`
      Logging: DEBUG reads with query telemetry.
    - FR-API-SETTINGS-UPDATE: Atomically update settings with revision checks.
      Associated: `put_settings_endpoint()`
      Logging: INFO revision on completion; ERROR failed post-commit notification.
    - FR-API-SETTINGS-CATALOGUE: Read field catalogue without exposing secrets.
      Associated: `get_catalogue_endpoint()`
      Logging: DEBUG catalogue query telemetry.
    - FR-API-SETTINGS-SECRETS: Update write-only secrets without echoing stored data.
      Associated: `replace_secrets_endpoint()`
      Logging: INFO revision on completion; WARNING rejected validation.

Python API Usage:
    ```python
    from app.api.settings import create_settings_router
    from app.host.settings import settings

    router = create_settings_router(settings)
    ```

CLI Usage:
    Settings REST endpoints are mounted by the host bootstrap runtime:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.host.logging import get_logger
from app.host.persistence import (
    PersistenceError,
    RevisionConflictError,
    ValidationError,
)
from app.host.settings import (
    SETTINGS_FIELDS,
    SETTINGS_GROUPS,
    HostSettings,
    HostSettingsSnapshot,
    _field_value,
    _is_secret,
    _set_field,
    _validate_catalogue_field,
    effective_settings_values,
    settings_catalogue,
)
from app.host.settings import (
    settings as default_settings,
)

__all__ = [
    "create_settings_router",
]

logger = get_logger(__name__)

_MISSING = object()


def _public_settings_snapshot(snapshot: HostSettingsSnapshot) -> dict[str, Any]:
    """Exclude account credentials from browser-facing settings projections."""
    values = effective_settings_values(snapshot.values)
    public: dict[str, dict[str, Any]] = {}
    for scope, group in SETTINGS_GROUPS.items():
        row = values.get(scope, {})
        safe: dict[str, Any] = {}
        for field in SETTINGS_FIELDS.get(group, {}):
            if not _is_secret(field) and group != "user_access":
                value = _field_value(row, field, _MISSING)
                if value is not _MISSING:
                    _set_field(safe, field, value)
        public[scope] = safe
    return {"revision": snapshot.revision, "values": public}


def _extract_put_payload(body: Any) -> tuple[int, dict[str, dict[str, Any]]]:
    """Validate and extract expected revision and changes from PUT body."""
    if not isinstance(body, dict):
        raise ValidationError("Request body must be a JSON object")
    expected_rev = body.get("expected_revision")
    if not isinstance(expected_rev, int) or expected_rev < 0:
        raise ValidationError("expected_revision must be a non-negative integer")
    changes = body.get("changes")
    if not isinstance(changes, dict):
        raise ValidationError("changes must be a dictionary of scoped settings")
    for scope, fields in changes.items():
        if scope == "user_access" or scope not in SETTINGS_GROUPS:
            raise ValidationError("Unsupported or protected settings scope.")
        if not isinstance(fields, dict):
            raise ValidationError("Setting changes must be objects.")
        group = SETTINGS_GROUPS[scope]
        for field, value in fields.items():
            _validate_catalogue_field(group, field, value, secrets=False)
    if isinstance(expected_rev, bool):
        raise ValidationError("expected_revision must be an integer")
    return expected_rev, changes


def _extract_secret_payload(body: Any) -> tuple[int, dict[str, dict[str, Any]]]:
    """Validate an atomic mixed preference/secret update without echoing values."""
    if not isinstance(body, dict) or type(body.get("expected_revision")) is not int:
        raise ValidationError("Expected revision is required.")
    changes = body.get("changes")
    if not isinstance(changes, dict):
        raise ValidationError("Secret changes must be scoped objects.")
    for scope, fields in changes.items():
        group = SETTINGS_GROUPS.get(scope)
        if group is None or not isinstance(fields, dict):
            raise ValidationError("Unsupported secret scope.")
        for field, value in fields.items():
            _validate_catalogue_field(group, field, value, secrets=_is_secret(field))
    return body["expected_revision"], changes


def _create_catalogue_router(
    target_settings: HostSettings, on_updated: Callable[[int], None] | None
) -> APIRouter:
    """Compose settings catalogue and write-only secret projection routes."""
    router = APIRouter()

    @router.get("/settings/catalogue")
    async def get_catalogue_endpoint() -> JSONResponse:
        """Read known fields without returning secret values or unknown payloads."""
        logger.debug(
            "FR-API-SETTINGS-CATALOGUE: Settings catalogue projected.",
            extra={"fr_id": "FR-API-SETTINGS-CATALOGUE"},
        )
        return JSONResponse(
            content={
                "status": "success",
                "data": settings_catalogue(target_settings.get_snapshot()),
            }
        )

    @router.put("/settings/secrets")
    async def replace_secrets_endpoint(request: Request) -> JSONResponse:
        """Replace/explicitly clear secret leaves without returning stored material."""
        try:
            body = await request.json()
            expected_revision, changes = _extract_secret_payload(body)
            snapshot = target_settings.update(
                changes, expected_revision=expected_revision
            )
            if on_updated is not None and any(changes.values()):
                try:
                    on_updated(snapshot.revision)
                except Exception:  # noqa: BLE001 - A hint failure cannot undo a committed save.
                    logger.error(  # noqa: TRY400 - Never log secret-bearing callback errors.
                        "Settings notification failed",
                        extra={"fr_id": "FR-API-SETTINGS-SECRETS"},
                    )
            logger.info(
                "FR-API-SETTINGS-SECRETS: Updated secret settings to revision %d.",
                snapshot.revision,
                extra={
                    "fr_id": "FR-API-SETTINGS-SECRETS",
                    "revision": snapshot.revision,
                },
            )
            return JSONResponse(
                content={"status": "success", "data": settings_catalogue(snapshot)}
            )
        except RevisionConflictError:
            return JSONResponse(
                status_code=409,
                content={
                    "status": "error",
                    "error": {
                        "code": "SETTINGS_CONFLICT",
                        "message": "Settings changed. Reopen and retry.",
                    },
                },
            )
        except ValueError, TypeError, ValidationError:
            logger.warning(
                "Secret settings update rejected",
                extra={"fr_id": "FR-API-SETTINGS-SECRETS"},
            )
            return JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "error": {
                        "code": "INVALID_SETTINGS",
                        "message": "Invalid secret settings request.",
                    },
                },
            )
        except PersistenceError:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "error": {
                        "code": "UNAVAILABLE",
                        "message": "Settings store unavailable.",
                    },
                },
            )

    return router


def create_settings_router(
    settings_instance: HostSettings | None = None,
    *,
    require_session: Callable[[Request], None] | None = None,
    on_updated: Callable[[int], None] | None = None,
) -> APIRouter:
    """Create FastAPI APIRouter exposing host settings REST projections.

    Args:
        settings_instance: HostSettings instance to expose. Defaults to
            global singleton.
        require_session: Optional session access dependency supplied by bootstrap.
        on_updated: Optional committed-revision notification supplied by bootstrap.

    Returns:
        Configured FastAPI APIRouter.
    """
    router = APIRouter(
        dependencies=[Depends(require_session)] if require_session is not None else []
    )
    target_settings = (
        settings_instance if settings_instance is not None else default_settings
    )

    router.include_router(_create_catalogue_router(target_settings, on_updated))

    @router.get("/settings")
    async def get_settings_endpoint() -> JSONResponse:
        """Retrieve current shell settings and preferences snapshot."""
        logger.debug(
            "FR-API-SETTINGS-READ: Handling GET /settings query.",
            extra={"fr_id": "FR-API-SETTINGS-READ"},
        )
        snapshot = target_settings.get_snapshot()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "data": _public_settings_snapshot(snapshot)},
        )

    @router.put("/settings")
    async def put_settings_endpoint(request: Request) -> JSONResponse:
        """Atomically update host settings with revision check."""
        try:
            body = await request.json()
        except ValueError, TypeError, json.JSONDecodeError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "error": {
                        "code": "INVALID_JSON",
                        "message": "Malformed JSON payload in request body",
                    },
                },
            )

        try:
            expected_rev, changes = _extract_put_payload(body)
            snapshot = target_settings.update(changes, expected_revision=expected_rev)
            if on_updated is not None and any(changes.values()):
                try:
                    on_updated(snapshot.revision)
                except Exception:  # noqa: BLE001 - A refresh hint must not undo a save.
                    logger.error(  # noqa: TRY400 - Never log callback exception secrets.
                        "Settings committed but revision notification failed",
                        extra={
                            "fr_id": "FR-API-SETTINGS-UPDATE",
                            "revision": snapshot.revision,
                        },
                    )
            logger.info(
                "FR-API-SETTINGS-UPDATE: Updated settings to revision %d.",
                snapshot.revision,
                extra={
                    "fr_id": "FR-API-SETTINGS-UPDATE",
                    "revision": snapshot.revision,
                },
            )
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "data": _public_settings_snapshot(snapshot),
                },
            )
        except RevisionConflictError as exc:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "status": "error",
                    "error": {
                        "code": "REVISION_CONFLICT",
                        "message": str(exc),
                        "current_revision": target_settings.revision,
                    },
                },
            )
        except ValidationError as exc:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content={
                    "status": "error",
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": str(exc),
                    },
                },
            )

    return router
