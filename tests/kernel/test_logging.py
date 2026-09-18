"""Security, concurrency, filesystem, and failure evidence for custom logging."""

from __future__ import annotations

import asyncio
import contextvars
import io
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import UUID

import pytest
from app.kernel.logging import (
    LoggingConfig,
    LoggingHandle,
    bind_correlation,
    configure_logging,
    get_correlation_context,
    get_logger,
    sanitize,
)

MEMORY = LoggingConfig(log_directory=None, console=False)


def test_import_and_logger_construction_are_inert(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    script = """
import logging, pathlib, threading, sys
sys.path.insert(0, sys.argv[1])
before = (list(logging.root.handlers), dict(logging.Logger.manager.loggerDict),
          list(threading.enumerate()), list(pathlib.Path('.').iterdir()))
from app.kernel.logging import get_logger
get_logger('app.test').bind(operation='import').critical('must not emit')
after = (list(logging.root.handlers), dict(logging.Logger.manager.loggerDict),
         list(threading.enumerate()), list(pathlib.Path('.').iterdir()))
assert before == after
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", script, str(root)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert not result.stdout and not result.stderr


@pytest.mark.parametrize("colorize", [False, True])
def test_console_format_colors_caller_and_context(colorize: bool) -> None:
    stream = io.StringIO()
    logger = get_logger("app.example").bind(component="service")
    with configure_logging(
        replace(MEMORY, console=True, level=10, colorize=colorize), stream=stream
    ) as handle:
        line = sys._getframe().f_lineno + 1
        logger.debug("debug")
        logger.info("info", count=3)
        logger.warning("warning")
        logger.error("error")
        logger.critical("critical")
        snapshot = handle.snapshot()
        assert snapshot[0]["caller"] == {
            "function": "test_console_format_colors_caller_and_context",
            "line": line,
        }
        assert snapshot[1]["context"] == {"component": "service", "count": 3}
    text = stream.getvalue()
    assert len(text.splitlines()) == 5
    plain = re.sub(r"\x1b\[[0-9;]+m", "", text)
    assert re.match(
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \| DEBUG \| app.example:", plain
    )
    for code, level in [
        ("36", "DEBUG"),
        ("32", "INFO"),
        ("33", "WARNING"),
        ("31", "ERROR"),
        ("1;31", "CRITICAL"),
    ]:
        assert (f"\x1b[{code}m{level}\x1b[0m" in text) is colorize
        assert (f"\x1b[{code}m{level.lower()}\x1b[0m" in text) is colorize
    assert not stream.closed
    assert not handle.health()["writer_alive"]


def test_console_omits_empty_context() -> None:
    stream = io.StringIO()
    logger = get_logger("app.empty")
    with configure_logging(
        replace(MEMORY, console=True, level=10, colorize=False), stream=stream
    ):
        logger.info("plain message")
        logger.info("message with context", request_id="REQ-1")
    lines = stream.getvalue().splitlines()
    assert len(lines) == 2
    assert lines[0].endswith(" - plain message")
    assert lines[0].count(" | ") == 2
    assert not lines[0].endswith(" | {}")
    assert lines[1].endswith(' - message with context | {"request_id":"REQ-1"}')
    assert lines[1].count(" | ") == 3


def test_redaction_in_every_sink_and_exception_forensics(tmp_path: Path) -> None:
    stream = io.StringIO()
    config = replace(
        MEMORY,
        log_directory=tmp_path,
        console=True,
        colorize=False,
        secrets=("unlabelled-value",),
    )
    with configure_logging(config, stream=stream) as handle:
        logger = get_logger("app.safe")
        logger.info(
            "Bearer abc.def password='hello world' https://user:pass@host/ "
            "unlabelled-value\nFORGED\x1b[31m",
            password="field-value",
            nested={"api_key": "nested-value"},
        )
        try:
            raise ValueError("exception-secret")
        except ValueError:
            logger.exception("operation_failed")
        assert handle.flush()
        records = handle.snapshot()
    output = stream.getvalue() + json.dumps(records)
    output += "".join(path.read_text() for path in tmp_path.glob("*.jsonl"))
    for secret in [
        "abc.def",
        "hello world",
        "user:pass",
        "unlabelled-value",
        "field-value",
        "nested-value",
        "exception-secret",
    ]:
        assert secret not in output
    assert len(stream.getvalue().splitlines()) == 2
    assert "\x1b" not in stream.getvalue()
    assert records[1]["context"]["exception"]["type"] == "ValueError"
    assert records[1]["context"]["exception"]["frames"]
    assert json.loads((tmp_path / "errors.jsonl").read_text())["purpose"] == "errors"


def test_sanitizer_handles_cycles_limits_and_hostile_objects() -> None:
    class Hostile:
        def __repr__(self) -> str:
            raise AssertionError("Must not inspect arbitrary objects")

        def __str__(self) -> str:
            raise AssertionError("Must not stringify arbitrary objects")

    cycle: list[object] = []
    cycle.append(cycle)
    assert sanitize(cycle) == ["[CYCLE]"]
    assert sanitize(Hostile()) == "[UNSUPPORTED OBJECT]"
    assert sanitize(float("nan")) == "[NONFINITE]"
    assert sanitize(1 << 1000) == "[LARGE INTEGER]"
    assert sanitize("x" * 3000) == "[OVERSIZED TEXT]"
    assert sanitize({1: "ignored", "password" * 400: "secret"}) == {
        "[OVERSIZED TEXT]": "[REDACTED]",
        "_truncated": True,
    }
    assert len(sanitize(list(range(100)))) == 33  # type: ignore[arg-type]
    nested: object = 1
    for _ in range(20):
        nested = [nested]
    assert "[LIMIT]" in json.dumps(sanitize(nested))
    tree = {f"branch_{n}": list(range(100)) for n in range(100)}
    assert len(json.dumps(sanitize(tree))) < 3000


def test_diagnostics_and_record_size_are_bounded_and_defensive() -> None:
    with configure_logging(replace(MEMORY, capture_capacity=2)) as handle:
        logger = get_logger()
        logger.debug("filtered")
        for number in range(5):
            logger.info("record", number=number)
        records = handle.snapshot()
        assert [r["context"]["number"] for r in records] == [3, 4]
        records[-1]["context"]["number"] = 99
        assert handle.snapshot()[-1]["context"]["number"] == 4
        logger.info("large", **{f"item_{n}": "x" * 2000 for n in range(32)})
        record = handle.snapshot()[-1]
        assert record["context"] == {"_truncated": True}
        assert len(json.dumps(record).encode()) < 16384


def test_async_and_thread_correlation_isolation_and_reset() -> None:
    async def scenario() -> None:
        logger = get_logger()
        gate = asyncio.Event()

        async def job(identity: str) -> None:
            with bind_correlation(request_id=identity):
                await gate.wait()
                logger.info("async")
                await asyncio.to_thread(logger.info, "thread")

        tasks = [asyncio.create_task(job(identity)) for identity in ("one", "two")]
        gate.set()
        await asyncio.gather(*tasks)

    with configure_logging(MEMORY) as handle:
        asyncio.run(scenario())
        assert get_correlation_context() == {}
        with pytest.raises(ValueError), bind_correlation(request_id="temporary"):
            raise ValueError
        assert get_correlation_context() == {}
        with bind_correlation(request_id="parent"):
            with ThreadPoolExecutor(max_workers=2) as pool:
                context = contextvars.copy_context()
                pool.submit(context.run, get_logger().info, "copied").result()
                pool.submit(get_logger().info, "isolated").result()
        records = handle.snapshot()
    assert sorted(r["context"]["request_id"] for r in records[:4]) == [
        "one",
        "one",
        "two",
        "two",
    ]
    assert records[4]["context"]["request_id"] == "parent"
    assert "request_id" not in records[5]["context"]


def test_blocked_sink_never_blocks_producer_and_queue_drops_are_counted() -> None:
    entered, release = threading.Event(), threading.Event()

    class Blocked(io.StringIO):
        def write(self, text: str) -> int:
            entered.set()
            assert release.wait(5)
            return super().write(text)

    stream = Blocked()
    with configure_logging(
        replace(MEMORY, console=True, queue_capacity=1), stream=stream
    ) as handle:
        try:
            logger = get_logger()
            logger.info("in sink")
            assert entered.wait(2)
            # Progress is proved while sink is still blocked, without timing guesses.
            logger.info("queued")
            logger.info("dropped")
            assert handle.health()["dropped"] == 1
            assert handle.snapshot()[-1]["message"] == "dropped"
            assert not handle.flush(0)
            with pytest.raises(TimeoutError):
                handle.close(0)
        finally:
            release.set()
        handle.close()
        assert handle.flush()
    assert len(stream.getvalue().splitlines()) == 2


def test_sink_failure_and_recursive_logging_are_contained() -> None:
    class Broken(io.StringIO):
        def write(self, text: str) -> int:
            get_logger().error("recursive")
            raise OSError("secret filesystem path")

    with configure_logging(replace(MEMORY, console=True), stream=Broken()) as handle:
        get_logger().info("safe")
        assert handle.flush()
        assert handle.health()["sink_failures"] == 2
        assert handle.health()["last_error"] == "console_write_failed"
        assert len(handle.snapshot()) == 1


def test_routes_rotation_zip_retention_and_unrelated_file_preservation(
    tmp_path: Path,
) -> None:
    unrelated = tmp_path / "application.jsonl.keep.zip"
    unrelated.write_bytes(b"keep")
    expired = tmp_path / ("application.jsonl.1-" + "a" * 32 + ".zip")
    expired.write_bytes(b"old")
    age = time.time() - 3 * 86400
    os.utime(expired, (age, age))
    config = replace(
        MEMORY, log_directory=tmp_path, max_bytes=512, backup_count=2, retention_days=1
    )
    with configure_logging(config) as handle:
        logger = get_logger()
        for index in range(12):
            logger.info("rotation", index=index)
        logger.info("audit event", purpose="audit")
        logger.error("error event")
        assert handle.flush()
        assert handle.health()["sink_failures"] == 0
    assert unrelated.read_bytes() == b"keep"
    assert not expired.exists()
    archives = [p for p in tmp_path.glob("application.jsonl.*.zip") if p != unrelated]
    assert len(archives) == 2
    for archive in archives:
        with zipfile.ZipFile(archive) as bundle:
            assert bundle.testzip() is None
            for line in bundle.read("application.jsonl").splitlines():
                assert json.loads(line)["message"] == "rotation"
    assert json.loads((tmp_path / "audit.jsonl").read_text())["purpose"] == "audit"
    assert json.loads((tmp_path / "errors.jsonl").read_text())["purpose"] == "errors"
    assert not (tmp_path / ".logging.lock").exists()


def test_failed_compression_preserves_active_file(tmp_path: Path) -> None:
    config = replace(MEMORY, log_directory=tmp_path, max_bytes=256)
    with configure_logging(config) as handle:
        logger = get_logger()
        logger.info("first")
        assert handle.flush()
        original = (tmp_path / "application.jsonl").read_bytes()
        with patch(
            "app.kernel.logging.zipfile.ZipFile", side_effect=OSError("failure")
        ):
            logger.info("second")
            assert handle.flush()
        assert (tmp_path / "application.jsonl").read_bytes() == original
        assert handle.health()["sink_failures"] == 1
    assert not list(tmp_path.glob("*.tmp"))


def test_configuration_failure_rollback_and_generation_restore(tmp_path: Path) -> None:
    stdlib = logging.getLogger("app")
    original = (stdlib.level, stdlib.propagate, list(stdlib.handlers))
    config = replace(MEMORY, log_directory=tmp_path)
    with configure_logging(config) as old:
        get_logger().info("old")
        with pytest.raises(FileExistsError), configure_logging(config):
            pytest.fail("Concurrent directory writer admitted")
        assert (tmp_path / ".logging.lock").exists()
        broken_dir = tmp_path / "bad"
        broken_dir.mkdir()
        (broken_dir / "errors.jsonl").mkdir()
        with (
            pytest.raises(OSError),
            configure_logging(replace(config, log_directory=broken_dir)),
        ):
            pytest.fail("Broken sink admitted")
        assert not (broken_dir / ".logging.lock").exists()
        with configure_logging(MEMORY) as new:
            with pytest.raises(RuntimeError, match="reverse order"):
                old.close()
            get_logger().info("new")
        get_logger().info("restored")
        assert [r["message"] for r in old.snapshot()] == ["old", "restored"]
        assert [r["message"] for r in new.snapshot()] == ["new"]
    assert (stdlib.level, stdlib.propagate, stdlib.handlers) == original


@pytest.mark.parametrize(
    "change",
    [
        {"namespace": ""},
        {"level": 99},
        {"queue_capacity": 0},
        {"capture_capacity": 1000000},
        {"max_bytes": 0},
        {"retention_days": 0},
        {"backup_count": 0},
        {"purposes": ("application", "../escape")},
        {"secrets": ("",)},
    ],
)
def test_invalid_configuration_has_no_filesystem_effect(
    tmp_path: Path, change: dict[str, Any]
) -> None:
    directory = tmp_path / "uncreated"
    config = replace(MEMORY, log_directory=directory, **change)
    with pytest.raises(ValueError), configure_logging(config):
        pytest.fail("Invalid config admitted")
    assert not directory.exists()


def test_flush_and_close_timeout_validation() -> None:
    with configure_logging(MEMORY) as handle:
        for timeout in (-1, float("inf"), float("nan")):
            with pytest.raises(ValueError):
                handle.flush(timeout)
            with pytest.raises(ValueError):
                handle.close(timeout)


def test_bindings_are_snapshots_and_nested_correlation_restores() -> None:
    nested = {"value": 1}
    logger = get_logger().bind(nested=nested, owner="binding")
    nested["value"] = 2
    with configure_logging(MEMORY) as handle:
        with bind_correlation(owner="outer"):
            with bind_correlation(owner="inner"):
                logger.info("override", owner="call", purpose="../bad")
            logger.info("outer")
        logger.exception("no active exception")
        records = handle.snapshot()
    assert [r["context"]["owner"] for r in records] == ["call", "outer", "binding"]
    assert records[0]["context"]["nested"] == {"value": 1}
    assert records[0]["purpose"] == "application"
    assert records[-1]["context"]["exception"] == {"type": None, "frames": []}


def test_many_threads_publish_complete_independent_records() -> None:
    def publish(identity: int) -> None:
        with bind_correlation(worker=identity):
            for index in range(20):
                get_logger().info("parallel", index=index)

    with configure_logging(replace(MEMORY, capture_capacity=128)) as handle:
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(publish, range(4)))
        assert handle.flush()
        records = handle.snapshot()
        assert handle.health()["dropped"] == 0
        assert handle.health()["completed"] == 80
    assert {(r["context"]["worker"], r["context"]["index"]) for r in records} == {
        (worker, index) for worker in range(4) for index in range(20)
    }


def test_thread_start_failure_preserves_previous_generation(tmp_path: Path) -> None:
    config = replace(MEMORY, log_directory=tmp_path)
    with configure_logging(MEMORY) as old:
        with patch("threading.Thread.start", side_effect=RuntimeError("start failed")):
            with pytest.raises(RuntimeError), configure_logging(config):
                pytest.fail("Broken writer admitted")
        assert not (tmp_path / ".logging.lock").exists()
        get_logger().info("still active")
        assert old.snapshot()[-1]["message"] == "still active"
    with configure_logging(config) as recovered:
        get_logger().info("recovered")
        assert recovered.flush()


def test_cleanup_attempts_every_sink_after_close_failure(tmp_path: Path) -> None:
    from app.kernel.logging import _FileSink

    original = _FileSink.close
    closed: list[str] = []

    def fail_after_close(sink: _FileSink) -> None:
        original(sink)
        closed.append(sink.path.name)
        if sink.path.name == "application.jsonl":
            raise OSError("close failure")

    with patch.object(_FileSink, "close", fail_after_close):
        with configure_logging(replace(MEMORY, log_directory=tmp_path)) as handle:
            get_logger().info("message")
    assert set(closed) == {"application.jsonl", "errors.jsonl", "audit.jsonl"}
    assert handle.health()["last_error"] == "file_close_failed"
    assert not (tmp_path / ".logging.lock").exists()


def test_redaction_does_not_expand_recursively_or_hide_sensitive_keys() -> None:
    assert (
        sanitize("R" * 2000, secrets=("R", "E", "D", "A", "C", "T"))
        == "[OVERSIZED TEXT]"
    )
    result = sanitize({"password": "hidden-value"}, secrets=("password",))
    assert "hidden-value" not in json.dumps(result)
    assert sanitize("-----BEGIN PRIVATE KEY-----") == "[REDACTED]"
    assert sanitize("sk_live_1234567890123456") == "[REDACTED]"


@pytest.mark.parametrize("suffix", [".zip", ".zip.tmp"])
def test_archive_collision_preserves_existing_files(
    tmp_path: Path, suffix: str
) -> None:
    existing = tmp_path / ("application.jsonl.1-" + "a" * 32 + suffix)
    existing.write_bytes(b"preserve")
    config = replace(MEMORY, log_directory=tmp_path, max_bytes=256)
    with configure_logging(config) as handle:
        get_logger().info("original")
        assert handle.flush()
        active = (tmp_path / "application.jsonl").read_bytes()
        with (
            patch("app.kernel.logging.time.time_ns", return_value=1),
            patch("app.kernel.logging.uuid4", return_value=UUID("a" * 32)),
        ):
            get_logger().info("rotation collision")
            assert handle.flush()
        assert handle.health()["sink_failures"] == 1
        assert (tmp_path / "application.jsonl").read_bytes() == active
    assert existing.read_bytes() == b"preserve"


def test_additional_logging_edge_cases(tmp_path: Path) -> None:
    """Verify boolean sanitization, dropped queue records, and symlink rejection."""
    # 1. Test boolean sanitization
    assert sanitize(True) is True
    assert sanitize(False) is False
    assert sanitize({"flag": True, "active": False}) == {"flag": True, "active": False}

    # 2. Test submitting to non-accepting handle
    config = LoggingConfig(log_directory=None, console=False)
    handle = LoggingHandle(config)
    handle._accepting = False
    handle.submit({"dummy": "record"})
    assert handle.health()["dropped"] == 1

    # 3. Test symlink rejection if OS supports symlinks
    real_file = tmp_path / "real.jsonl"
    real_file.touch()
    link_file = tmp_path / "application.jsonl"
    try:
        os.symlink(real_file, link_file)
        file_config = LoggingConfig(log_directory=tmp_path)
        with pytest.raises(ValueError, match="symbolic link"):
            from app.kernel.logging import _FileSink

            _FileSink(tmp_path, "application", file_config)
    except OSError, NotImplementedError:
        pass
