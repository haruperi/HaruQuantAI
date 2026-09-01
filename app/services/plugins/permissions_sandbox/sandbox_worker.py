"""Child-only pure-Python plugin runner with one framed JSON exchange."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import runpy
import struct
import sys
from pathlib import Path
from typing import Any

_FRAME_HEADER_BYTES = 4
_SOCKET_ADDRESS_ITEMS = 2


def _read_frame(limit: int) -> dict[str, Any]:
    """Read one bounded canonical JSON object.

    Returns:
        Decoded request object.

    Raises:
        TypeError: The decoded JSON value is not an object.
        ValueError: Framing is incomplete or exceeds its bound.
    """
    header = sys.stdin.buffer.read(_FRAME_HEADER_BYTES)
    if len(header) != _FRAME_HEADER_BYTES:
        raise ValueError("missing framed request")
    size = struct.unpack(">I", header)[0]
    if size > limit:
        raise ValueError("request exceeds protocol bound")
    payload = sys.stdin.buffer.read(size)
    if len(payload) != size:
        raise ValueError("truncated framed request")
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise TypeError("request must be a JSON object")
    return value


def _write_frame(value: dict[str, Any], limit: int) -> None:
    """Write exactly one canonical JSON response.

    Raises:
        ValueError: The encoded response exceeds its bound.
    """
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(payload) > limit:
        raise ValueError("response exceeds protocol bound")
    sys.stdout.buffer.write(struct.pack(">I", len(payload)) + payload)
    sys.stdout.buffer.flush()


def _inside(root: Path, candidate: Path) -> bool:
    """Return whether a resolved path stays inside an already resolved root."""
    try:
        candidate.resolve().relative_to(root)
    except ValueError:
        return False
    return True


def _install_audit(  # noqa: C901
    root: Path,
    reads: tuple[Path, ...],
    writes: tuple[Path, ...],
    endpoints: frozenset[tuple[str, int]],
    allow_subprocess: bool,
) -> None:
    """Install a non-removable audit hook before untrusted code is loaded."""
    standard_library = Path(os.__file__).resolve().parent
    runtime_root = Path(sys.base_prefix).resolve()
    allowed_roots = (root, *reads, *writes, standard_library, runtime_root)

    def audit(event: str, args: tuple[object, ...]) -> None:
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
            candidate = Path(os.fsdecode(args[0])).resolve()
            if not any(_inside(item, candidate) for item in allowed_roots):
                raise PermissionError("sandbox file access denied")
        elif event in {"subprocess.Popen", "os.system", "os.posix_spawn", "os.spawn"}:
            if not allow_subprocess or event != "subprocess.Popen":
                raise PermissionError("sandbox process access denied")
        elif event == "socket.connect":
            address = args[1] if len(args) > 1 else None
            if not isinstance(address, tuple) or len(address) < _SOCKET_ADDRESS_ITEMS:
                raise PermissionError("sandbox socket access denied")
            host, port = str(address[0]).casefold(), int(address[1])
            if (host, port) not in endpoints:
                raise PermissionError("sandbox endpoint denied")
        elif event == "import" and len(args) > 1:
            origin = args[1]
            if isinstance(origin, str) and origin.lower().endswith(
                (".pyd", ".so", ".dll")
            ):
                raise PermissionError("native extensions are denied")

    sys.addaudithook(audit)


def _redact(value: object, secrets: tuple[str, ...]) -> object:
    """Redact resolved values recursively.

    Returns:
        Secret-safe value with its original JSON-compatible shape.
    """
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, "[REDACTED]")
        return value
    if isinstance(value, list):
        return [_redact(item, secrets) for item in value]
    if isinstance(value, dict):
        return {str(key): _redact(item, secrets) for key, item in value.items()}
    return value


def _run(args: argparse.Namespace) -> int:
    """Run the constrained plugin callable and emit its response.

    Returns:
        Zero after a valid response is emitted.

    Raises:
        TypeError: The plugin callable or output has an invalid shape.
        ValueError: The entry point or protocol is invalid.
    """
    root = Path(args.root).resolve(strict=True)
    entry = (root / args.entry).resolve(strict=True)
    if not _inside(root, entry) or entry.suffix != ".py":
        raise ValueError("unsafe entry point")
    reads = tuple(Path(value).resolve(strict=False) for value in args.read_root)
    writes = tuple(Path(value).resolve(strict=False) for value in args.write_root)
    endpoints = frozenset(
        (host.casefold(), int(port))
        for host, port in (item.rsplit(":", 1) for item in args.endpoint)
    )
    secrets = tuple(
        value for value in (os.environ.get(name) for name in args.secret_env) if value
    )
    request = _read_frame(args.protocol_bytes)
    _install_audit(root, reads, writes, endpoints, args.allow_subprocess)
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        namespace = runpy.run_path(str(entry), run_name="__hq_plugin__")
        callback = namespace.get("run")
        if not callable(callback):
            raise TypeError("plugin entry point must define run(input)")
        output = callback(request)
    if not isinstance(output, dict):
        raise TypeError("plugin output must be a JSON object")
    _write_frame(
        {"outcome": "SUCCESS", "output": _redact(output, secrets)}, args.protocol_bytes
    )
    return 0


def main() -> int:
    """Run the child protocol with secret-safe failures.

    Returns:
        Process exit status.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--root", required=True)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--read-root", action="append", default=[])
    parser.add_argument("--write-root", action="append", default=[])
    parser.add_argument("--endpoint", action="append", default=[])
    parser.add_argument("--secret-env", action="append", default=[])
    parser.add_argument("--protocol-bytes", required=True, type=int)
    parser.add_argument("--allow-subprocess", action="store_true")
    args = parser.parse_args()
    try:
        return _run(args)
    except (
        OSError,
        TypeError,
        ValueError,
        PermissionError,
        json.JSONDecodeError,
    ) as error:
        _write_frame(
            {
                "outcome": "FAILURE",
                "code": "PLUGIN_SANDBOX_EXECUTION_FAILED",
                "detail": type(error).__name__,
            },
            args.protocol_bytes,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
