"""Unit tests for runtime-store codec governance."""

import json

import pytest
from app.services.data import build_agentic_runtime_store


def _encode(value: object) -> str:
    """Encode one JSON-compatible test value.

    Returns:
        JSON text.
    """
    return json.dumps(value, sort_keys=True)


def test_runtime_store_rejects_invalid_codec_registry() -> None:
    """Construction fails closed for unsafe or incomplete codecs."""
    with pytest.raises(ValueError, match="must not be empty"):
        build_agentic_runtime_store({})
    with pytest.raises(TypeError, match="encoder/decoder"):
        build_agentic_runtime_store({"record": (_encode,)})  # type: ignore[dict-item]


def test_runtime_store_rejects_secret_bearing_payload_before_sql() -> None:
    """Codec output cannot persist a prohibited credential-shaped field."""
    from app.services.data import execute_runtime_store_operation

    store = build_agentic_runtime_store({"record": (_encode, json.loads)})

    with pytest.raises(ValueError, match="sensitive field"):
        execute_runtime_store_operation(
            store,
            "put_once",
            collection="records",
            key="record-1",
            kind="record",
            value={"api_key": "not-persisted"},  # pragma: allowlist secret
        )
