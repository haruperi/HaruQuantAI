"""Published resources retain custody and access without installed producers."""

import json

import pytest
from app.persistence.resources import ResourceRef, ResourceStore


def publish(
    store: ResourceStore,
    content: bytes = b"market data",
    *,
    readers: tuple[str, ...] = (),
    previous: ResourceRef | None = None,
) -> ResourceRef:
    return store.publish(
        "test.producer",
        "1.0.0",
        content,
        schema_id="test.market",
        schema_version="1.0.0",
        schema_json='{"type":"string"}',
        media_type="text/plain",
        readers=readers,
        previous=previous,
    )


def test_producer_absence_and_access_control(tmp_path):
    store = ResourceStore(tmp_path / "resources")
    assert not store.root.exists()
    assert store.list("test.consumer") == ()
    public = publish(store, readers=("*",))
    private = publish(store, b"private")
    # Restart with no producer code/context/registration, only the custody root.
    independent = ResourceStore(store.root)
    assert independent.list("test.consumer") == (public,)
    assert independent.read("test.consumer", public)[0] == b"market data"
    with pytest.raises(PermissionError):
        independent.read("test.consumer", private)


def test_revisions_and_stale_write_keep_history(tmp_path):
    store = ResourceStore(tmp_path)
    first = publish(store)
    second = publish(store, b"next", previous=first)
    assert second.id == first.id and second.revision == 2
    with pytest.raises(ValueError, match="Stale"):
        publish(store, b"lost update", previous=first)
    assert store.read("test.producer", first)[0] == b"market data"
    assert store.read("test.producer", second)[0] == b"next"
    assert not (tmp_path / ".publication.lock").exists()


def test_corruption_and_abandoned_writer_fail_closed(tmp_path):
    store = ResourceStore(tmp_path)
    ref = publish(store, readers=("*",))
    path = tmp_path / f"{ref.id}.1.json"
    record = json.loads(path.read_text())
    record["content_base64"] = "b3RoZXI="
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="checksum"):
        store.read("any", ref)
    (tmp_path / ".publication.lock").write_text("interrupted publisher")
    with pytest.raises(FileExistsError):
        publish(store)


def test_limits_and_schema(tmp_path):
    store = ResourceStore(tmp_path)
    with pytest.raises(ValueError, match="limit"):
        publish(store, b"x" * (16 * 1024 * 1024 + 1))
    with pytest.raises(TypeError, match="JSON object"):
        store.publish(
            "p",
            "1.0.0",
            b"a",
            schema_id="x",
            schema_version="1.0.0",
            schema_json="[]",
            media_type="text/plain",
        )
