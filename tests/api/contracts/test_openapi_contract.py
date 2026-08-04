"""Deterministic OpenAPI contract baseline for typed frontend generation."""

import hashlib
import json
from pathlib import Path

from app.services.api import create_api_app, get_canonical_route_contract_registry

_SNAPSHOT = Path(__file__).with_name("snapshots") / "openapi.v1.json"


def test_openapi_v1_matches_registered_contract_snapshot() -> None:
    """The canonical schema and operation inventory must change together."""
    schema = create_api_app().openapi()
    encoded = json.dumps(schema, sort_keys=True, separators=(",", ":")).encode()
    expected = json.loads(_SNAPSHOT.read_text(encoding="utf-8"))
    operation_count = sum(len(path_item) for path_item in schema["paths"].values())
    assert operation_count == expected["operation_count"]
    assert operation_count == get_canonical_route_contract_registry().size
    assert hashlib.sha256(encoded).digest() == bytes(expected["sha256_bytes"])


def test_openapi_v1_contains_no_excluded_routes() -> None:
    """Unsupported backend-v1 workflow families remain absent."""
    paths = tuple(create_api_app().openapi()["paths"])
    assert not any("/imports" in path for path in paths)
    assert not any("/docs/" in path for path in paths)
    assert not any("/simulation/sessions" in path for path in paths)
    assert not any("/backtest/" in path for path in paths)
    assert "/api/v1/risk/kill-switch" in paths
    assert "/api/v1/trading/session" in paths
    assert not any("/optimization/" in path for path in paths)
    assert not any("/portfolio/" in path for path in paths)
    assert not any("/agentic/" in path for path in paths)
