"""Regenerate the frozen UI/API OpenAPI contract snapshot.

The snapshot at ``tests/api/contracts/snapshots/openapi.v1.json`` pins the
canonical operation count and a SHA-256 digest of the deterministic OpenAPI
document so that an unreviewed boundary change fails CI. Whenever a route is
deliberately added, removed, or re-shaped, run this script once and commit the
regenerated snapshot alongside the route change.

Usage:
    uv run python scripts/refresh_openapi_snapshot.py

The script refuses to run if the registered route-contract registry and the
generated OpenAPI document disagree, because that mismatch is exactly the drift
the snapshot exists to catch.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.services.api import create_api_app, get_canonical_route_contract_registry

_SNAPSHOT = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "api"
    / "contracts"
    / "snapshots"
    / "openapi.v1.json"
)


def main() -> int:
    """Regenerate and write the OpenAPI snapshot.

    Returns:
        Process exit code: ``0`` on success, ``1`` on registry drift.
    """
    schema = create_api_app().openapi()
    encoded = json.dumps(schema, sort_keys=True, separators=(",", ":")).encode()
    operation_count = sum(len(path_item) for path_item in schema["paths"].values())
    registry_size = get_canonical_route_contract_registry().size

    if operation_count != registry_size:
        print(
            "Refusing to refresh: OpenAPI exposes "
            f"{operation_count} operations but the route contract registry "
            f"declares {registry_size}. Register every route contract first."
        )
        return 1

    previous = (
        json.loads(_SNAPSHOT.read_text(encoding="utf-8")) if _SNAPSHOT.exists() else {}
    )
    payload = {
        **previous,
        "operation_count": operation_count,
        "sha256_bytes": list(hashlib.sha256(encoded).digest()),
    }
    _SNAPSHOT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"Refreshed {_SNAPSHOT.relative_to(Path(__file__).resolve().parents[1])}: "
        f"{previous.get('operation_count', 'none')} -> {operation_count} operations."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
