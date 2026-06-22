"""Unit tests for app.utils.paths."""

from pathlib import Path

import pytest
from app.utils.errors import SecurityError, ValidationError
from app.utils.paths import ensure_dir, ensure_parent_dir, normalize_path
from pytest_mock import MockerFixture


def test_normalize_path_returns_path_without_creating_target(tmp_path: Path) -> None:
    target = normalize_path("nested/file.txt", base_dir=tmp_path)

    assert isinstance(target, Path)
    assert target == (tmp_path / "nested" / "file.txt").resolve(strict=False)
    assert not target.exists()
    assert not target.parent.exists()


def test_normalize_path_accepts_absolute_path_inside_base(tmp_path: Path) -> None:
    target = tmp_path / "child" / "file.txt"

    normalized = normalize_path(target, base_dir=tmp_path)

    assert normalized == target.resolve(strict=False)


def test_normalize_path_rejects_empty_or_invalid_inputs(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="path"):
        normalize_path("", base_dir=tmp_path)

    with pytest.raises(ValidationError, match="base_dir"):
        normalize_path("file.txt", base_dir="")

    with pytest.raises(ValidationError, match="path"):
        normalize_path(object())  # type: ignore[arg-type]


def test_normalize_path_rejects_traversal_outside_base(tmp_path: Path) -> None:
    with pytest.raises(SecurityError, match="base_dir"):
        normalize_path("../outside.txt", base_dir=tmp_path)

    outside = tmp_path.parent / "outside.txt"
    with pytest.raises(SecurityError, match="base_dir"):
        normalize_path(outside, base_dir=tmp_path)


def test_ensure_dir_creates_missing_directory(tmp_path: Path) -> None:
    directory = ensure_dir("cache/items", base_dir=tmp_path)

    assert directory == (tmp_path / "cache" / "items").resolve(strict=False)
    assert directory.is_dir()


def test_ensure_dir_rejects_traversal_before_creation(tmp_path: Path) -> None:
    with pytest.raises(SecurityError):
        ensure_dir("../escape", base_dir=tmp_path)

    assert not (tmp_path.parent / "escape").exists()


def test_ensure_parent_dir_creates_parent_and_returns_file_path(tmp_path: Path) -> None:
    file_path = ensure_parent_dir("audit/events/event.json", base_dir=tmp_path)

    assert file_path == (tmp_path / "audit" / "events" / "event.json").resolve(
        strict=False,
    )
    assert file_path.parent.is_dir()
    assert not file_path.exists()


def test_ensure_parent_dir_rejects_traversal_before_creation(tmp_path: Path) -> None:
    with pytest.raises(SecurityError):
        ensure_parent_dir("../escape/file.txt", base_dir=tmp_path)

    assert not (tmp_path.parent / "escape").exists()


def test_coerce_path_empty() -> None:
    # Empty Path object simulated via custom subclass
    import sys
    from pathlib import PosixPath, WindowsPath

    if sys.platform == "win32":
        class EmptyPathWin(WindowsPath):
            def __str__(self) -> str:
                return ""
        empty_path = EmptyPathWin(".")
    else:
        class EmptyPathPosix(PosixPath):
            def __str__(self) -> str:
                return ""
        empty_path = EmptyPathPosix(".")

    with pytest.raises(ValidationError, match="path"):
        normalize_path(empty_path, base_dir="data")


def test_safe_join_and_validate_path(tmp_path: Path) -> None:
    from app.utils.paths import safe_join, validate_path_within_root

    # Safe joins
    res = safe_join(tmp_path, "sub", "file.csv")
    assert res == (tmp_path / "sub" / "file.csv").resolve(strict=False)

    # Escapes base_dir
    with pytest.raises(SecurityError):
        safe_join(tmp_path, "../outside.csv")

    # Validate path within root
    res2 = validate_path_within_root(Path("sub/file.csv"), root=tmp_path)
    assert res2 == (tmp_path / "sub" / "file.csv").resolve(strict=False)

    # Escaping root
    with pytest.raises(SecurityError):
        validate_path_within_root("../outside.csv", root=tmp_path)


def test_windows_prefix_formatting() -> None:
    from app.utils.paths import _strip_windows_extended_prefix

    # UNC prefix
    unc_path = Path("\\\\?\\UNC\\server\\share\\file.txt")
    expected = Path("\\\\server\\share\\file.txt")
    assert _strip_windows_extended_prefix(unc_path) == expected

    # standard extended prefix
    ext_path = Path("\\\\?\\C:\\file.txt")
    assert _strip_windows_extended_prefix(ext_path) == Path("C:\\file.txt")


def test_ensure_dir_creation_failure(mocker: MockerFixture) -> None:
    # Mock mkdir to raise OSError
    mocker.patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied"))

    with pytest.raises(ValidationError, match="failed to create directory"):
        ensure_dir("data/raw/temp_dir")

    with pytest.raises(ValidationError, match="failed to create parent directory"):
        ensure_parent_dir("data/raw/temp_dir/file.csv")

