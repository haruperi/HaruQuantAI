"""Unit tests for runtime-store codec governance."""

import json
from types import SimpleNamespace

import pytest
from app.kernel.identity import generate_id
from app.services.data import (
    build_agentic_runtime_store,
    execute_runtime_store_operation,
    execute_runtime_store_transition,
)
from app.services.data.persistence.contracts import TransactionResult
from app.services.data.runtime_stores import codecs


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


def test_runtime_store_operation_matrix(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise every governed operation without database I/O."""
    store = build_agentic_runtime_store({"record": (_encode, json.loads)})
    rows: list[dict[str, object]] = []

    monkeypatch.setattr(codecs, "_read_rows", lambda *_args, **_kwargs: tuple(rows))
    monkeypatch.setattr(codecs, "create_runtime_append_record", lambda *_a, **_k: None)
    monkeypatch.setattr(
        codecs, "create_runtime_put_once_record", lambda *_a, **_k: None
    )
    monkeypatch.setattr(codecs, "update_runtime_upsert_record", lambda *_a, **_k: None)
    monkeypatch.setattr(
        codecs,
        "update_runtime_compare_and_swap_record",
        lambda *_a, **_k: SimpleNamespace(affected_rows=1),
    )

    assert (
        execute_runtime_store_operation(
            store, "get", collection="records", key="record-1"
        )
        is None
    )
    rows[:] = [{"codec_kind": "record", "payload_json": '{"a": 1}', "revision": 2}]
    assert execute_runtime_store_operation(
        store, "get_with_revision", collection="records", key="record-1"
    ) == ({"a": 1}, 2)
    assert execute_runtime_store_operation(
        store, "list", collection="records", partition="root", limit=1
    ) == ({"a": 1},)
    assert execute_runtime_store_operation(
        store, "list_all_partitions", collection="records", limit=1
    ) == ({"a": 1},)
    assert (
        execute_runtime_store_operation(
            store,
            "append",
            collection="records",
            key="record-1",
            partition="root",
            sequence=1,
            kind="record",
            value={"a": 1},
        )
        == 1
    )
    assert (
        execute_runtime_store_operation(
            store,
            "put_once",
            collection="records",
            key="record-1",
            kind="record",
            value={"a": 1},
        )
        == 2
    )
    assert (
        execute_runtime_store_operation(
            store,
            "upsert",
            collection="records",
            key="record-1",
            kind="record",
            value={"a": 1},
        )
        == 2
    )
    assert (
        execute_runtime_store_operation(
            store,
            "compare_and_swap",
            collection="records",
            key="record-1",
            kind="record",
            value={"a": 2},
            expected_revision=2,
        )
        == 3
    )


def test_runtime_store_transition_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cover create and compare-and-swap atomic transition paths."""
    store = build_agentic_runtime_store({"record": (_encode, json.loads)})
    monkeypatch.setattr(
        codecs,
        "update_runtime_transition_records",
        lambda *_a, **_k: SimpleNamespace(affected_rows=2),
    )
    common = {
        "state_collection": "states",
        "state_key": "state-1",
        "state_kind": "record",
        "state_value": {"state": "ready"},
        "event_collection": "events",
        "event_key": "event-1",
        "event_partition": "root",
        "event_sequence": 1,
        "event_kind": "record",
        "event_value": {"event": "ready"},
    }
    assert execute_runtime_store_transition(store, expected_revision=0, **common)
    assert execute_runtime_store_transition(store, expected_revision=1, **common)


def test_runtime_store_read_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Route exact-key, partition, and cross-partition reads explicitly."""
    store = codecs._require_store(
        build_agentic_runtime_store({"record": (_encode, json.loads)})
    )
    calls: list[str] = []

    def result(label: str) -> TransactionResult:
        calls.append(label)
        return TransactionResult(
            rows=({"codec_kind": "record", "payload_json": "{}", "revision": 1},),
            affected_rows=0,
            committed=True,
            request_id=generate_id("req"),
        )

    monkeypatch.setattr(codecs, "read_runtime_record", lambda *_a, **_k: result("key"))
    monkeypatch.setattr(
        codecs,
        "read_runtime_partition_records",
        lambda *_a, **_k: result("partition"),
    )
    monkeypatch.setattr(
        codecs,
        "read_runtime_collection_records",
        lambda *_a, **_k: result("all"),
    )
    assert codecs._read_rows(store, "records", key="one")
    assert codecs._read_rows(store, "records", partition="root")
    assert codecs._read_rows(store, "records", all_partitions=True)
    assert calls == ["key", "partition", "all"]


@pytest.mark.parametrize(
    ("operation", "kwargs", "message"),
    [
        ("list", {"limit": 0}, "outside"),
        ("append", {"sequence": 0, "kind": "record", "value": {}}, "positive"),
        ("upsert", {}, "requires kind"),
        (
            "compare_and_swap",
            {"kind": "record", "value": {}, "expected_revision": 0},
            "positive",
        ),
    ],
)
def test_runtime_store_rejects_invalid_operations(
    operation: str, kwargs: dict[str, object], message: str
) -> None:
    """Cover bounded operation validation failures."""
    store = build_agentic_runtime_store({"record": (_encode, json.loads)})
    with pytest.raises(ValueError, match=message):
        execute_runtime_store_operation(
            store,
            operation,  # type: ignore[arg-type]
            collection="records",
            key="record-1",
            **kwargs,
        )
