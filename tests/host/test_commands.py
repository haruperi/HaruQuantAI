"""Tests for OS-mediation commands and the sandboxed file exchange."""

from pathlib import Path

import pytest
from app.host.transport import CommandError, ExchangeFiles, copy_text, open_link
from starlette.testclient import TestClient


@pytest.mark.parametrize(
    "url",
    ["http://example.com/docs", "https://example.com/docs?a=1"],
)
def test_open_link_accepts_http_links(url: str) -> None:
    assert open_link(url) == url


@pytest.mark.parametrize(
    "url",
    ["ftp://example.com", "javascript:alert(1)", "file:///etc/passwd", "http://"],
)
def test_open_link_rejects_other_schemes(url: str) -> None:
    with pytest.raises(CommandError):
        open_link(url)


def test_copy_text_enforces_byte_cap() -> None:
    assert copy_text("hello") == "hello"
    with pytest.raises(CommandError):
        copy_text("x" * (8 * 1024 + 1))


def test_exchange_files_round_trip(tmp_path: Path) -> None:
    exchange = ExchangeFiles(tmp_path)

    written = exchange.write("exports/report.txt", "hello exchange")
    content = exchange.read("exports/report.txt")

    assert written == len(b"hello exchange")
    assert content == "hello exchange"


@pytest.mark.parametrize(
    "bad_path",
    ["../escape.txt", "a/../../escape.txt", "/absolute.txt", "C:/drive.txt"],
)
def test_exchange_rejects_escapes(tmp_path: Path, bad_path: str) -> None:
    exchange = ExchangeFiles(tmp_path)

    with pytest.raises(CommandError):
        exchange.write(bad_path, "nope")
    with pytest.raises(CommandError):
        exchange.read(bad_path)


def test_exchange_read_missing_file_fails(tmp_path: Path) -> None:
    with pytest.raises(CommandError):
        ExchangeFiles(tmp_path).read("missing.txt")


def test_exchange_write_enforces_size_cap(tmp_path: Path) -> None:
    exchange = ExchangeFiles(tmp_path)
    big = "x" * (10 * 1024 * 1024 + 1)

    with pytest.raises(CommandError):
        exchange.write("big.txt", big)


def test_open_link_endpoint_round_trip(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    ok = client.post(
        "/api/v1/commands/open-link",
        json={"url": "https://docs.haruquantai.local/guide"},
        headers=auth_headers,
    )
    rejected = client.post(
        "/api/v1/commands/open-link",
        json={"url": "javascript:alert(1)"},
        headers=auth_headers,
    )

    assert ok.status_code == 200
    assert ok.json()["data"]["url"] == "https://docs.haruquantai.local/guide"
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "COMMAND_REJECTED"


def test_copy_endpoint_round_trip(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/commands/copy", json={"text": "copy me"}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["data"]["text"] == "copy me"


def test_files_endpoints_round_trip(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    write = client.post(
        "/api/v1/files/write",
        json={"path": "imports/note.txt", "content": "hello files"},
        headers=auth_headers,
    )
    read = client.post(
        "/api/v1/files/read", json={"path": "imports/note.txt"}, headers=auth_headers
    )
    escape = client.post(
        "/api/v1/files/read", json={"path": "../secrets.txt"}, headers=auth_headers
    )

    assert write.status_code == 200
    assert write.json()["data"]["bytes"] == len(b"hello files")
    assert read.json()["data"]["content"] == "hello files"
    assert escape.status_code == 422
    assert escape.json()["error"]["code"] == "COMMAND_REJECTED"


def test_exchange_files_exists(tmp_path: Path) -> None:
    exchange = ExchangeFiles(tmp_path)
    assert exchange.exists("missing.txt") == {"exists": False, "size_bytes": None}

    exchange.write("sub/file.txt", "data")
    assert exchange.exists("sub/file.txt") == {
        "exists": True,
        "size_bytes": len(b"data"),
    }

    with pytest.raises(CommandError):
        exchange.exists("../escape.txt")


def test_exchange_files_list(tmp_path: Path) -> None:
    exchange = ExchangeFiles(tmp_path)
    assert exchange.list_files() == []

    exchange.write("root.txt", "root")
    exchange.write("reports/daily.csv", "1,2,3")
    exchange.write("reports/weekly.csv", "4,5,6")

    all_files = exchange.list_files()
    assert len(all_files) == 3
    paths = {f["path"] for f in all_files}
    assert paths == {"root.txt", "reports/daily.csv", "reports/weekly.csv"}

    filtered = exchange.list_files("reports")
    assert len(filtered) == 2
    assert {f["path"] for f in filtered} == {
        "reports/daily.csv",
        "reports/weekly.csv",
    }

    assert exchange.list_files("missing") == []

    with pytest.raises(CommandError):
        exchange.list_files("../escape")


def test_exchange_files_delete(tmp_path: Path) -> None:
    exchange = ExchangeFiles(tmp_path)
    assert not exchange.delete("missing.txt")

    exchange.write("temp.txt", "delete me")
    assert exchange.delete("temp.txt")
    assert not exchange.exists("temp.txt")["exists"]

    (tmp_path / "somedir").mkdir()
    with pytest.raises(CommandError):
        exchange.delete("somedir")

    with pytest.raises(CommandError):
        exchange.delete("../escape.txt")


def test_files_exists_endpoint(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    client.post(
        "/api/v1/files/write",
        json={"path": "status.txt", "content": "ok"},
        headers=auth_headers,
    )
    ok = client.post(
        "/api/v1/files/exists", json={"path": "status.txt"}, headers=auth_headers
    )
    missing = client.post(
        "/api/v1/files/exists", json={"path": "not_there.txt"}, headers=auth_headers
    )
    bad_body = client.post(
        "/api/v1/files/exists", json={"path": 123}, headers=auth_headers
    )
    escape = client.post(
        "/api/v1/files/exists", json={"path": "../secret"}, headers=auth_headers
    )

    assert ok.status_code == 200
    assert ok.json()["data"] == {
        "path": "status.txt",
        "exists": True,
        "size_bytes": 2,
    }
    assert missing.status_code == 200
    assert missing.json()["data"] == {
        "path": "not_there.txt",
        "exists": False,
        "size_bytes": None,
    }
    assert bad_body.status_code == 422
    assert escape.status_code == 422


def test_files_list_endpoint(client: TestClient, auth_headers: dict[str, str]) -> None:
    client.post(
        "/api/v1/files/write",
        json={"path": "listing/one.txt", "content": "1"},
        headers=auth_headers,
    )
    client.post(
        "/api/v1/files/write",
        json={"path": "listing/two.txt", "content": "22"},
        headers=auth_headers,
    )

    all_resp = client.post(
        "/api/v1/files/list", json={"prefix": "listing"}, headers=auth_headers
    )
    assert all_resp.status_code == 200
    assert all_resp.json()["data"]["count"] == 2

    bad_prefix = client.post(
        "/api/v1/files/list", json={"prefix": 123}, headers=auth_headers
    )
    assert bad_prefix.status_code == 422

    escape = client.post(
        "/api/v1/files/list", json={"prefix": "../outside"}, headers=auth_headers
    )
    assert escape.status_code == 422


def test_files_delete_endpoint(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    client.post(
        "/api/v1/files/write",
        json={"path": "to_del.txt", "content": "bye"},
        headers=auth_headers,
    )
    del_ok = client.post(
        "/api/v1/files/delete", json={"path": "to_del.txt"}, headers=auth_headers
    )
    del_missing = client.post(
        "/api/v1/files/delete", json={"path": "to_del.txt"}, headers=auth_headers
    )
    bad_body = client.post(
        "/api/v1/files/delete", json={"path": ["bad"]}, headers=auth_headers
    )
    escape = client.post(
        "/api/v1/files/delete", json={"path": "../secret"}, headers=auth_headers
    )

    assert del_ok.status_code == 200
    assert del_ok.json()["data"] == {"path": "to_del.txt", "deleted": True}
    assert del_missing.status_code == 200
    assert del_missing.json()["data"] == {"path": "to_del.txt", "deleted": False}
    assert bad_body.status_code == 422
    assert escape.status_code == 422
