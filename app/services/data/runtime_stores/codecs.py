"""Allowlisted codecs and transactional runtime-record storage."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast

from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
    TransactionResult,
)
from app.services.data.persistence.transactions import execute_transaction
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

type _Codec = tuple[Callable[[object], str], Callable[[str], object]]
type _Operation = Literal[
    "append",
    "compare_and_swap",
    "get",
    "get_with_revision",
    "list",
    "list_all_partitions",
    "put_once",
    "upsert",
]

_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,127}$")
_MAX_PAYLOAD_BYTES = 1_048_576
_MAX_LIST_ITEMS = 1_000
_CODEC_PARTS = 2
_ATOMIC_TRANSITION_WRITE_COUNT = 2
_SENSITIVE_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "client_secret",
        "credential",
        "password",
        "refresh_token",
        "secret",
        "token",
    }
)


@dataclass(frozen=True, slots=True)
class _RuntimeStore:
    """Opaque namespaced runtime store with an allowlisted codec registry."""

    namespace: str
    codecs: Mapping[str, _Codec]


def _name(value: object, field: str) -> str:
    """Validate a bounded storage identifier.

    Returns:
        Validated identifier.

    Raises:
        ValueError: If the identifier is malformed.
    """
    if not isinstance(value, str) or _NAME_PATTERN.fullmatch(value) is None:
        message = f"{field} must match {_NAME_PATTERN.pattern}"
        raise ValueError(message)
    return value


def _contains_sensitive_key(value: object) -> bool:
    """Return whether decoded JSON contains a prohibited field name.

    Returns:
        True when a prohibited field is present.
    """
    if isinstance(value, dict):
        return any(
            str(key).lower() in _SENSITIVE_KEYS or _contains_sensitive_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def _validate_payload(payload: str) -> str:
    """Validate bounded secret-safe JSON emitted by an owner codec.

    Returns:
        Validated JSON payload.

    Raises:
        TypeError: If the codec did not return text.
        ValueError: If the payload is invalid, unsafe, or unbounded.
    """
    if not isinstance(payload, str):
        raise TypeError("runtime codec must return JSON text")
    if len(payload.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
        raise ValueError("runtime payload exceeds the storage bound")
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ValueError("runtime codec must return valid JSON") from error
    if _contains_sensitive_key(decoded):
        raise ValueError("runtime payload contains a prohibited sensitive field")
    return payload


def build_runtime_store(
    namespace: str,
    codecs: Mapping[str, _Codec],
) -> object:
    """Construct one opaque durable runtime-store handle.

    Args:
        namespace: Stable owner namespace.
        codecs: Explicit kind-to-encoder/decoder registry.

    Returns:
        Opaque runtime-store handle.

    Raises:
        TypeError: If a codec entry is not callable.
        ValueError: If the namespace or registry is invalid.
    """
    safe_namespace = _name(namespace, "namespace")
    if not codecs:
        raise ValueError("runtime codec registry must not be empty")
    validated: dict[str, _Codec] = {}
    for kind, codec in codecs.items():
        safe_kind = _name(kind, "codec kind")
        if (
            not isinstance(codec, tuple)
            or len(codec) != _CODEC_PARTS
            or not all(callable(item) for item in codec)
        ):
            raise TypeError("each runtime codec must be an encoder/decoder tuple")
        validated[safe_kind] = codec
    return _RuntimeStore(namespace=safe_namespace, codecs=validated)


def _require_store(value: object) -> _RuntimeStore:
    """Validate an opaque runtime-store handle.

    Returns:
        Internal runtime-store value.

    Raises:
        TypeError: If the handle did not originate from this feature.
    """
    if not isinstance(value, _RuntimeStore):
        raise TypeError("invalid runtime-store handle")
    return value


def _transaction(
    statements: tuple[str, ...],
    parameter_sets: tuple[tuple[object, ...], ...],
    *,
    max_rows: int = 1,
) -> TransactionResult:
    """Execute one bounded Data-owned runtime transaction.

    Returns:
        Data transaction result.
    """
    request_id = generate_id("req")
    request = TransactionRequest(
        plan=StatementPlan(
            statements=statements,
            parameter_sets=cast("Any", parameter_sets),
            max_rows=max_rows,
        ),
        request_id=request_id,
    )
    return unwrap_data_response(
        execute_transaction(request),
        operation="data.runtime_stores.transaction",
        request_id=request_id,
    )


def _encode(store: _RuntimeStore, kind: str, value: object) -> str:
    """Encode one allowlisted owner value.

    Returns:
        Validated JSON text.

    Raises:
        ValueError: If the kind is unregistered.
    """
    codec = store.codecs.get(_name(kind, "codec kind"))
    if codec is None:
        raise ValueError("runtime codec kind is not registered")
    return _validate_payload(codec[0](value))


def _decode(store: _RuntimeStore, kind: str, payload: object) -> object:
    """Decode one stored value through its registered owner codec.

    Returns:
        Decoded owner value.

    Raises:
        TypeError: If stored payload data is malformed.
        ValueError: If the stored kind is no longer registered.
    """
    codec = store.codecs.get(kind)
    if codec is None:
        raise ValueError("stored runtime codec kind is not registered")
    if not isinstance(payload, str):
        raise TypeError("stored runtime payload is not text")
    return codec[1](_validate_payload(payload))


def _read_rows(
    store: _RuntimeStore,
    collection: str,
    *,
    key: str | None = None,
    partition: str | None = None,
    limit: int = 1,
    all_partitions: bool = False,
) -> tuple[Mapping[str, object], ...]:
    """Read bounded runtime rows by exact key or ordered partition.

    Returns:
        Detached normalized row mappings.
    """
    if key is not None:
        sql = (
            "SELECT codec_kind, payload_json, revision FROM hq_runtime_records "
            "WHERE namespace = ? AND collection_name = ? AND record_key = ?"
        )
        params: tuple[object, ...] = (store.namespace, collection, key)
    elif all_partitions:
        sql = (
            "SELECT codec_kind, payload_json, revision FROM hq_runtime_records "
            "WHERE namespace = ? AND collection_name = ? "
            "ORDER BY sequence_number ASC, partition_key ASC LIMIT ?"
        )
        params = (store.namespace, collection, limit)
    else:
        sql = (
            "SELECT codec_kind, payload_json, revision FROM hq_runtime_records "
            "WHERE namespace = ? AND collection_name = ? AND partition_key = ? "
            "ORDER BY sequence_number ASC LIMIT ?"
        )
        params = (store.namespace, collection, partition or "", limit)
    result = _transaction((sql,), (params,), max_rows=limit)
    return cast("tuple[Mapping[str, object], ...]", result.rows)


def execute_runtime_store_operation(  # noqa: C901, PLR0911, PLR0912, PLR0915
    handle: object,
    operation: _Operation,
    *,
    collection: str,
    key: str | None = None,
    partition: str = "root",
    sequence: int = 0,
    kind: str | None = None,
    value: object | None = None,
    expected_revision: int | None = None,
    limit: int = 100,
) -> object:
    """Execute one allowlisted atomic runtime-record operation.

    Returns:
        Decoded value, ordered value tuple, or committed revision.

    Raises:
        ValueError: If inputs are invalid or an atomic guard fails.
    """
    store = _require_store(handle)
    safe_collection = _name(collection, "collection")
    safe_partition = _name(partition, "partition")
    if operation in {"list", "list_all_partitions"}:
        if isinstance(limit, bool) or not 1 <= limit <= _MAX_LIST_ITEMS:
            raise ValueError("runtime list limit is outside the approved bound")
        rows = _read_rows(
            store,
            safe_collection,
            partition=safe_partition,
            limit=limit,
            all_partitions=operation == "list_all_partitions",
        )
        return tuple(
            _decode(store, str(row["codec_kind"]), row["payload_json"]) for row in rows
        )
    safe_key = _name(key, "record key")
    if operation in {"get", "get_with_revision"}:
        rows = _read_rows(store, safe_collection, key=safe_key)
        if not rows:
            return None
        row = rows[0]
        decoded = _decode(store, str(row["codec_kind"]), row["payload_json"])
        if operation == "get_with_revision":
            revision = row["revision"]
            if not isinstance(revision, int):
                raise TypeError("stored runtime revision is not an integer")
            return decoded, revision
        return decoded
    if kind is None or value is None:
        raise ValueError("runtime write requires kind and value")
    safe_kind = _name(kind, "codec kind")
    payload = _encode(store, safe_kind, value)
    if operation == "append":
        if isinstance(sequence, bool) or sequence <= 0:
            raise ValueError("append sequence must be positive")
        sql = (
            "INSERT INTO hq_runtime_records "
            "(namespace, collection_name, record_key, partition_key, sequence_number, "
            "codec_kind, payload_json, revision) VALUES (?, ?, ?, ?, ?, ?, ?, 1)"
        )
        _transaction(
            (sql,),
            (
                (
                    store.namespace,
                    safe_collection,
                    safe_key,
                    safe_partition,
                    sequence,
                    safe_kind,
                    payload,
                ),
            ),
        )
        return 1
    if operation == "put_once":
        sql = (
            "INSERT OR IGNORE INTO hq_runtime_records "
            "(namespace, collection_name, record_key, partition_key, sequence_number, "
            "codec_kind, payload_json, revision) VALUES (?, ?, ?, '', 0, ?, ?, 1)"
        )
        _transaction(
            (sql,),
            ((store.namespace, safe_collection, safe_key, safe_kind, payload),),
        )
        rows = _read_rows(store, safe_collection, key=safe_key)
        if (
            not rows
            or rows[0]["codec_kind"] != safe_kind
            or rows[0]["payload_json"] != payload
        ):
            raise ValueError("runtime put-once key conflicts with stored material")
        revision = rows[0]["revision"]
        if not isinstance(revision, int):
            raise TypeError("stored runtime revision is not an integer")
        return revision
    if operation == "upsert":
        sql = (
            "INSERT INTO hq_runtime_records "
            "(namespace, collection_name, record_key, partition_key, sequence_number, "
            "codec_kind, payload_json, revision) VALUES (?, ?, ?, '', 0, ?, ?, 1) "
            "ON CONFLICT(namespace, collection_name, record_key) DO UPDATE SET "
            "codec_kind = excluded.codec_kind, payload_json = excluded.payload_json, "
            "revision = hq_runtime_records.revision + 1"
        )
        _transaction(
            (sql,),
            ((store.namespace, safe_collection, safe_key, safe_kind, payload),),
        )
        rows = _read_rows(store, safe_collection, key=safe_key)
        revision = rows[0]["revision"]
        if not isinstance(revision, int):
            raise TypeError("stored runtime revision is not an integer")
        return revision
    if operation != "compare_and_swap" or expected_revision is None:
        raise ValueError("unsupported runtime-store operation or missing revision")
    if isinstance(expected_revision, bool) or expected_revision < 1:
        raise ValueError("expected revision must be positive")
    sql = (
        "UPDATE hq_runtime_records SET codec_kind = ?, payload_json = ?, "
        "revision = revision + 1 WHERE namespace = ? AND collection_name = ? "
        "AND record_key = ? AND revision = ?"
    )
    result = _transaction(
        (sql,),
        (
            (
                safe_kind,
                payload,
                store.namespace,
                safe_collection,
                safe_key,
                expected_revision,
            ),
        ),
    )
    if result.affected_rows != 1:
        raise ValueError("runtime compare-and-swap revision conflict")
    return expected_revision + 1


def execute_runtime_store_transition(
    handle: object,
    *,
    state_collection: str,
    state_key: str,
    state_kind: str,
    state_value: object,
    expected_revision: int,
    event_collection: str,
    event_key: str,
    event_partition: str,
    event_sequence: int,
    event_kind: str,
    event_value: object,
) -> bool:
    """Atomically compare-and-swap state and append its exact evidence event.

    Returns:
        True when both writes commit; false on a state revision conflict.

    Raises:
        ValueError: If identifiers, revisions, or codec output are invalid.
    """
    store = _require_store(handle)
    state_collection = _name(state_collection, "state collection")
    state_key = _name(state_key, "state key")
    event_collection = _name(event_collection, "event collection")
    event_key = _name(event_key, "event key")
    event_partition = _name(event_partition, "event partition")
    if expected_revision < 0 or event_sequence <= 0:
        raise ValueError("runtime transition revisions must be non-negative")
    state_kind = _name(state_kind, "state kind")
    event_kind = _name(event_kind, "event kind")
    state_payload = _encode(store, state_kind, state_value)
    event_payload = _encode(store, event_kind, event_value)
    if expected_revision == 0:
        state_sql = (
            "INSERT OR IGNORE INTO hq_runtime_records "
            "(namespace, collection_name, record_key, partition_key, sequence_number, "
            "codec_kind, payload_json, revision) VALUES (?, ?, ?, '', 0, ?, ?, 1)"
        )
        state_params: tuple[object, ...] = (
            store.namespace,
            state_collection,
            state_key,
            state_kind,
            state_payload,
        )
    else:
        state_sql = (
            "UPDATE hq_runtime_records SET codec_kind = ?, payload_json = ?, "
            "revision = revision + 1 WHERE namespace = ? AND collection_name = ? "
            "AND record_key = ? AND revision = ?"
        )
        state_params = (
            state_kind,
            state_payload,
            store.namespace,
            state_collection,
            state_key,
            expected_revision,
        )
    event_sql = (
        "INSERT INTO hq_runtime_records "
        "(namespace, collection_name, record_key, partition_key, sequence_number, "
        "codec_kind, payload_json, revision) "
        "SELECT ?, ?, ?, ?, ?, ?, ?, 1 WHERE changes() = 1"
    )
    result = _transaction(
        (state_sql, event_sql),
        (
            state_params,
            (
                store.namespace,
                event_collection,
                event_key,
                event_partition,
                event_sequence,
                event_kind,
                event_payload,
            ),
        ),
    )
    return result.affected_rows == _ATOMIC_TRANSITION_WRITE_COUNT


__all__ = (
    "build_runtime_store",
    "execute_runtime_store_operation",
    "execute_runtime_store_transition",
)
