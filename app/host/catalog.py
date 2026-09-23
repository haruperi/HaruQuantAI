"""Self-describing domain discovery and route mounting.

Backend domain pairs (workspaces, plugins) describe themselves with a
``manifest.json`` in their folder — a JSON object with ``id``, ``kind``
(``workspace`` | ``plugin``), ``route_base`` (absolute path), ``version``,
``capabilities``, and an optional dotted ``module`` naming a package whose
``create_routes()`` returns Starlette routes.

The host discovers domains by scanning the configured roots (defaults
``app/workspace`` and ``app/plugins``); it never knows a domain by name
(Law 5: catalogs are built from self-description, never a central list).
Discovery fails closed per domain: an invalid, unreadable, or oversized
manifest is skipped and reported as a structured issue instead of crashing
the host, and the catalog endpoint serves both the valid manifests and the
skip reasons. Route mounting is lazy and additive — only manifests that
declare a module are mounted, under their own declared route base.
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import BaseRoute, Mount

from app.host.envelope import ValidationIssue, success_payload
from app.host.http import envelope_response, request_id_of

MANIFEST_FILENAME = "manifest.json"
DOMAIN_KINDS = ("workspace", "plugin")
MAX_MANIFEST_BYTES = 64 * 1024


@dataclass(frozen=True)
class DomainManifest:
    """One discovered backend domain's self-description.

    Attributes:
        domain_id: Stable unique identifier (the manifest ``id``).
        kind: Domain family: ``workspace`` or ``plugin``.
        route_base: Absolute path prefix the domain owns, for example
            ``/api/v1/builder``.
        version: Domain's own version string.
        capabilities: Declared capability tokens other components may
            require (Law 3 typed capability slots).
        module: Dotted module path exposing ``create_routes()``, or
            ``None`` for manifest-only domains.
    """

    domain_id: str
    kind: str
    route_base: str
    version: str
    capabilities: tuple[str, ...]
    module: str | None

    def to_json(self) -> dict[str, Any]:
        """Return the wire representation of this manifest.

        Mirrors the ``manifest.json`` field names (``id`` for
        ``domain_id``); ``module`` is omitted when unset.
        """
        payload: dict[str, Any] = {
            "id": self.domain_id,
            "kind": self.kind,
            "route_base": self.route_base,
            "version": self.version,
            "capabilities": list(self.capabilities),
        }
        if self.module is not None:
            payload["module"] = self.module
        return payload


def validate_manifest(raw: dict[str, Any]) -> list[ValidationIssue]:
    """Return the list of problems that make ``raw`` an invalid manifest.

    Checks every required field (``id``, ``kind``, ``route_base``,
    ``version``), the optional ``capabilities`` list and ``module`` string,
    and reports each problem separately so a fixer can address them all at
    once. An empty result means the manifest is valid.
    """
    issues: list[ValidationIssue] = []

    domain_id = raw.get("id")
    if not isinstance(domain_id, str) or not domain_id.strip():
        issues.append(
            ValidationIssue(
                path="id", code="required", message="id must be a non-empty string"
            )
        )

    kind = raw.get("kind")
    if kind not in DOMAIN_KINDS:
        issues.append(
            ValidationIssue(
                path="kind",
                code="invalid",
                message=f"kind must be one of {DOMAIN_KINDS}",
            )
        )

    route_base = raw.get("route_base")
    if not isinstance(route_base, str) or not route_base.startswith("/"):
        issues.append(
            ValidationIssue(
                path="route_base",
                code="invalid",
                message="route_base must be an absolute path starting with '/'",
            )
        )

    version = raw.get("version")
    if not isinstance(version, str) or not version.strip():
        issues.append(
            ValidationIssue(
                path="version",
                code="required",
                message="version must be a non-empty string",
            )
        )

    capabilities = raw.get("capabilities", [])
    if not isinstance(capabilities, list) or not all(
        isinstance(item, str) for item in capabilities
    ):
        issues.append(
            ValidationIssue(
                path="capabilities",
                code="invalid",
                message="capabilities must be a list of strings",
            )
        )

    module = raw.get("module")
    if module is not None and (not isinstance(module, str) or not module.strip()):
        issues.append(
            ValidationIssue(
                path="module",
                code="invalid",
                message="module must be a dotted module path",
            )
        )

    return issues


def parse_manifest(raw: dict[str, Any]) -> DomainManifest:
    """Build a ``DomainManifest`` from already-JSON ``raw`` data.

    Raises:
        CatalogError: When validation issues exist.
    """
    issues = validate_manifest(raw)
    if issues:
        raise CatalogError(issues)
    module = raw.get("module")
    return DomainManifest(
        domain_id=str(raw["id"]),
        kind=str(raw["kind"]),
        route_base=str(raw["route_base"]),
        version=str(raw["version"]),
        capabilities=tuple(str(item) for item in raw.get("capabilities", [])),
        module=str(module) if module is not None else None,
    )


class CatalogError(Exception):
    """Raised when a manifest is invalid; carries structured issues.

    Attributes:
        issues: Every validation problem found, each with the offending
            field as its path.
    """

    def __init__(self, issues: list[ValidationIssue]) -> None:
        """Store ``issues`` on the exception for envelope conversion."""
        super().__init__("Invalid domain manifest")
        self.issues = issues


@dataclass(frozen=True)
class CatalogView:
    """The result of a domain scan: valid manifests plus skip reasons.

    Attributes:
        domains: Every valid manifest found, in sorted folder order.
        issues: One structured issue per skipped or invalid manifest, with
            the manifest path (and field) as its location.
    """

    domains: tuple[DomainManifest, ...]
    issues: tuple[ValidationIssue, ...]


def _read_and_parse_manifest(
    manifest_path: Path,
) -> tuple[DomainManifest | None, list[ValidationIssue]]:
    """Read and validate a single manifest file.

    Returns:
        A tuple of (parsed manifest or None, list of validation issues).
    """
    try:
        if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
            raise CatalogError(
                [
                    ValidationIssue(
                        path=str(manifest_path),
                        code="too_large",
                        message="Manifest exceeds the size limit",
                    )
                ]
            )
        raw: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as err:
        return None, [
            ValidationIssue(
                path=str(manifest_path), code="unreadable", message=str(err)
            )
        ]

    if not isinstance(raw, dict):
        return None, [
            ValidationIssue(
                path=str(manifest_path),
                code="invalid",
                message="Manifest must be a JSON object",
            )
        ]

    try:
        return parse_manifest(raw), []
    except CatalogError as err:
        return None, [
            ValidationIssue(
                path=f"{manifest_path}:{issue.path}",
                code=issue.code,
                message=issue.message,
            )
            for issue in err.issues
        ]


def scan_domains(roots: Sequence[Path]) -> CatalogView:
    """Scan ``roots`` for domain folders carrying a ``manifest.json``.

    Missing roots are skipped silently (a configured root may legitimately
    not exist yet); directories without a manifest are ignored. Invalid,
    unreadable, or oversized manifests are skipped and reported as issues —
    fail closed per domain, never fatal to the host.

    Args:
        roots: Candidate parent directories of domain folders.

    Returns:
        The valid manifests plus the structured skip reasons.
    """
    domains: list[DomainManifest] = []
    issues: list[ValidationIssue] = []
    seen_ids: dict[str, Path] = {}
    seen_routes: dict[str, Path] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            manifest_path = child / MANIFEST_FILENAME
            if not manifest_path.is_file():
                continue

            manifest, parse_issues = _read_and_parse_manifest(manifest_path)
            if parse_issues:
                issues.extend(parse_issues)
                continue
            if manifest is None:
                continue

            if manifest.domain_id in seen_ids:
                issues.append(
                    ValidationIssue(
                        path=f"{manifest_path}:id",
                        code="duplicate",
                        message=(
                            f"Duplicate domain id '{manifest.domain_id}' already "
                            f"declared at {seen_ids[manifest.domain_id]}"
                        ),
                    )
                )
                continue

            if manifest.route_base in seen_routes:
                issues.append(
                    ValidationIssue(
                        path=f"{manifest_path}:route_base",
                        code="duplicate",
                        message=(
                            f"Duplicate route_base '{manifest.route_base}' already "
                            f"declared at {seen_routes[manifest.route_base]}"
                        ),
                    )
                )
                continue

            seen_ids[manifest.domain_id] = manifest_path
            seen_routes[manifest.route_base] = manifest_path
            domains.append(manifest)
    return CatalogView(domains=tuple(domains), issues=tuple(issues))


def domain_routes(manifest: DomainManifest) -> Mount:
    """Import a manifest's module and mount its ``create_routes()``.

    The returned :class:`~starlette.routing.Mount` binds the module's routes
    under the manifest's declared ``route_base`` — the single mounting
    mechanism by which domain pairs plug into the host.

    Args:
        manifest: A manifest with a non-``None`` ``module``.

    Returns:
        The mount ready to append to the application's route table.

    Raises:
        CatalogError: When the manifest declares no module, the module
            cannot be imported, or it exposes no callable
            ``create_routes()``.
    """
    if manifest.module is None:
        raise CatalogError(
            [
                ValidationIssue(
                    path="module",
                    code="required",
                    message="Manifest declares no module",
                )
            ]
        )
    try:
        module = importlib.import_module(manifest.module)
    except ImportError as err:
        raise CatalogError(
            [ValidationIssue(path="module", code="import_failed", message=str(err))]
        ) from err
    factory = getattr(module, "create_routes", None)
    if not callable(factory):
        raise CatalogError(
            [
                ValidationIssue(
                    path="module",
                    code="invalid",
                    message="Module must expose create_routes()",
                )
            ]
        )
    routes: Sequence[BaseRoute] = factory()
    return Mount(manifest.route_base, routes=list(routes))


class CatalogService:
    """Scans roots once per refresh and serves the catalog.

    The application mounts routes from the scan taken at construction;
    :meth:`refresh` rescans for the catalog endpoint's view (new domains
    appear in the catalog immediately, while route mounting still requires
    an application rebuild — deliberate, since mounting is a structural
    change).
    """

    def __init__(self, roots: Sequence[Path]) -> None:
        """Scan ``roots`` once at construction.

        Args:
            roots: Candidate parent directories of domain folders.
        """
        self._roots = list(roots)
        self._view = scan_domains(self._roots)

    def refresh(self) -> CatalogView:
        """Rescan the configured roots and return the fresh view."""
        self._view = scan_domains(self._roots)
        return self._view

    @property
    def view(self) -> CatalogView:
        """Return the most recent scan result."""
        return self._view


async def catalog_endpoint(request: Request) -> JSONResponse:
    """Handle ``GET /api/v1/catalog``.

    Serves the immutable view captured when this app mounted its routes.
    """
    request_id = request_id_of(request)
    view: CatalogView = request.app.state.catalog_view
    data = {
        "domains": [
            {**manifest.to_json(), "mounted": manifest.module is not None}
            for manifest in view.domains
        ],
        "issues": [issue.to_json() for issue in view.issues],
    }
    return envelope_response(request_id, success_payload(request_id, data))
