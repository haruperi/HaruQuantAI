"""Tests for child-only pure-Python sandbox worker."""

from __future__ import annotations

import argparse
import io
import json
import struct
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from app.services.plugins.permissions_sandbox.sandbox_worker import (
    _inside,
    _install_audit,
    _read_frame,
    _redact,
    _run,
    _write_frame,
    main,
)


class _StreamWrapper:
    def __init__(self, buffer: io.BytesIO):
        self.buffer = buffer


def test_read_frame_success():
    payload = json.dumps({"key": "value"}).encode("utf-8")
    header = struct.pack(">I", len(payload))
    stream = _StreamWrapper(io.BytesIO(header + payload))

    with patch.object(sys, "stdin", stream):
        result = _read_frame(limit=1024)
        assert result == {"key": "value"}


def test_read_frame_errors():
    # Incomplete header
    with (
        patch.object(sys, "stdin", _StreamWrapper(io.BytesIO(b"ab"))),
        pytest.raises(ValueError, match="missing framed request"),
    ):
        _read_frame(limit=1024)

    # Exceeds limit
    payload = json.dumps({"k": "v"}).encode("utf-8")
    header = struct.pack(">I", len(payload))
    with (
        patch.object(sys, "stdin", _StreamWrapper(io.BytesIO(header + payload))),
        pytest.raises(ValueError, match="request exceeds protocol bound"),
    ):
        _read_frame(limit=5)

    # Truncated payload
    header = struct.pack(">I", 100)
    with (
        patch.object(sys, "stdin", _StreamWrapper(io.BytesIO(header + b"short"))),
        pytest.raises(ValueError, match="truncated framed request"),
    ):
        _read_frame(limit=1024)

    # Non-dict JSON
    non_dict = json.dumps(["a", "b"]).encode("utf-8")
    header = struct.pack(">I", len(non_dict))
    with (
        patch.object(sys, "stdin", _StreamWrapper(io.BytesIO(header + non_dict))),
        pytest.raises(TypeError, match="must be a JSON object"),
    ):
        _read_frame(limit=1024)


def test_write_frame_success():
    stream = _StreamWrapper(io.BytesIO())
    with patch.object(sys, "stdout", stream):
        _write_frame({"status": "ok"}, limit=1024)

    stream.buffer.seek(0)
    header = stream.buffer.read(4)
    size = struct.unpack(">I", header)[0]
    body = stream.buffer.read(size)
    assert json.loads(body) == {"status": "ok"}


def test_write_frame_exceeds_limit():
    with pytest.raises(ValueError, match="response exceeds protocol bound"):
        _write_frame({"data": "x" * 100}, limit=10)


def test_inside_paths(tmp_path: Path):
    root = tmp_path.resolve()
    child = root / "sub" / "file.py"
    child.parent.mkdir(parents=True, exist_ok=True)
    child.touch()
    assert _inside(root, child) is True

    outside = tmp_path.parent.resolve()
    assert _inside(root, outside) is False


def test_redact():
    secrets = ("secret1", "secret2")
    data = {
        "text": "this is secret1 and secret2",
        "nested": ["secret1 inside list", 123, True, None],
        "safe": "public",
    }
    redacted = _redact(data, secrets)
    assert redacted == {
        "text": "this is [REDACTED] and [REDACTED]",
        "nested": ["[REDACTED] inside list", 123, True, None],
        "safe": "public",
    }


def test_audit_hook_logic(tmp_path: Path):
    root = tmp_path.resolve()
    reads = (root / "reads",)
    writes = (root / "writes",)
    endpoints = frozenset([("example.com", 443)])

    captured_audits = []

    def mock_addaudithook(hook):
        captured_audits.append(hook)

    with patch("sys.addaudithook", side_effect=mock_addaudithook):
        _install_audit(root, reads, writes, endpoints, allow_subprocess=True)

    assert len(captured_audits) == 1
    audit_fn = captured_audits[0]

    # open within root -> allowed
    audit_fn("open", (str(root / "allowed.txt"), "r"))

    # open outside allowed roots -> denied
    with pytest.raises(PermissionError, match="sandbox file access denied"):
        audit_fn("open", (str(Path("C:/Windows/System32/drivers/etc/hosts")), "r"))

    # subprocess -> allowed because allow_subprocess=True
    audit_fn("subprocess.Popen", ("cmd",))

    # other subprocess events -> denied
    with pytest.raises(PermissionError, match="sandbox process access denied"):
        audit_fn("os.system", ("dir",))

    # socket.connect to allowed endpoint -> allowed
    audit_fn("socket.connect", (None, ("example.com", 443)))

    # socket.connect to denied endpoint -> denied
    with pytest.raises(PermissionError, match="sandbox endpoint denied"):
        audit_fn("socket.connect", (None, ("evil.com", 80)))

    # socket.connect invalid address -> denied
    with pytest.raises(PermissionError, match="sandbox socket access denied"):
        audit_fn("socket.connect", (None, "invalid_address"))

    # import non-native -> allowed
    audit_fn("import", ("module", "module.py"))

    # import native extension -> denied
    with pytest.raises(PermissionError, match="native extensions are denied"):
        audit_fn("import", ("native_mod", "native.pyd"))


def test_run_success(tmp_path: Path):
    root = tmp_path.resolve()
    entry = root / "plugin.py"
    entry.write_text(
        "def run(req):\n    return {'result': req['num'] * 2}\n", encoding="utf-8"
    )

    req_payload = json.dumps({"num": 21}).encode("utf-8")
    stdin_stream = _StreamWrapper(
        io.BytesIO(struct.pack(">I", len(req_payload)) + req_payload)
    )
    stdout_stream = _StreamWrapper(io.BytesIO())

    args = argparse.Namespace(
        root=str(root),
        entry="plugin.py",
        read_root=[],
        write_root=[],
        endpoint=[],
        secret_env=[],
        protocol_bytes=1024,
        allow_subprocess=False,
    )

    with (
        patch.object(sys, "stdin", stdin_stream),
        patch.object(sys, "stdout", stdout_stream),
        patch("sys.addaudithook"),
    ):
        exit_code = _run(args)
        assert exit_code == 0

    stdout_stream.buffer.seek(0)
    size = struct.unpack(">I", stdout_stream.buffer.read(4))[0]
    out = json.loads(stdout_stream.buffer.read(size))
    assert out["outcome"] == "SUCCESS"
    assert out["output"] == {"result": 42}


def test_run_invalid_entry_point(tmp_path: Path):
    root = tmp_path.resolve()
    non_py = root / "plugin.txt"
    non_py.write_text("content", encoding="utf-8")

    args = argparse.Namespace(
        root=str(root),
        entry="plugin.txt",
        read_root=[],
        write_root=[],
        endpoint=[],
        secret_env=[],
        protocol_bytes=1024,
        allow_subprocess=False,
    )

    with pytest.raises(ValueError, match="unsafe entry point"):
        _run(args)


def test_run_missing_callable(tmp_path: Path):
    root = tmp_path.resolve()
    entry = root / "plugin.py"
    entry.write_text("x = 10\n", encoding="utf-8")

    req_payload = json.dumps({}).encode("utf-8")
    stdin_stream = _StreamWrapper(
        io.BytesIO(struct.pack(">I", len(req_payload)) + req_payload)
    )

    args = argparse.Namespace(
        root=str(root),
        entry="plugin.py",
        read_root=[],
        write_root=[],
        endpoint=[],
        secret_env=[],
        protocol_bytes=1024,
        allow_subprocess=False,
    )

    with (
        patch.object(sys, "stdin", stdin_stream),
        patch("sys.addaudithook"),
        pytest.raises(TypeError, match="must define run"),
    ):
        _run(args)


def test_main_cli_success(tmp_path: Path):
    root = tmp_path.resolve()
    entry = root / "plugin.py"
    entry.write_text("def run(req):\n    return {'status': 'ok'}\n", encoding="utf-8")

    req_payload = json.dumps({}).encode("utf-8")
    stdin_stream = _StreamWrapper(
        io.BytesIO(struct.pack(">I", len(req_payload)) + req_payload)
    )
    stdout_stream = _StreamWrapper(io.BytesIO())

    test_args = [
        "sandbox_worker.py",
        "--root",
        str(root),
        "--entry",
        "plugin.py",
        "--protocol-bytes",
        "1024",
    ]

    with (
        patch.object(sys, "argv", test_args),
        patch.object(sys, "stdin", stdin_stream),
        patch.object(sys, "stdout", stdout_stream),
        patch("sys.addaudithook"),
    ):
        code = main()
        assert code == 0


def test_main_cli_failure(tmp_path: Path):
    root = tmp_path.resolve()
    stdout_stream = _StreamWrapper(io.BytesIO())

    test_args = [
        "sandbox_worker.py",
        "--root",
        str(root),
        "--entry",
        "nonexistent.py",
        "--protocol-bytes",
        "1024",
    ]

    with (
        patch.object(sys, "argv", test_args),
        patch.object(sys, "stdout", stdout_stream),
    ):
        code = main()
        assert code == 1
