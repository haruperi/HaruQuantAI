"""Shared editor ownership and mutation authorization.

Description:
    Protects the shipped include inventory and host files, and maps builtin clones
    into the user tree. No filesystem mutation occurs during policy inspection.
Purpose:
    FEAT-CODE-EDITOR-COMMANDS: Make builtin/user ownership explicit.
Key Capabilities:
    - FR-editor-path-policy: Log policy evaluation and rejection; tests verify
      builtin protection, user mutation and clone destinations.
Python API Usage:
    info = inspect_path("app/include/user/example.py")
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

import json
import logging
from functools import lru_cache
from pathlib import Path

from app.workspace.code_editor.command_models import PathInfo

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def builtin_files() -> frozenset[str]:
    """Load the versioned shipped inventory; malformed authority fails closed."""
    logger.debug("FR-editor-path-policy: inventory")
    value: object = json.loads(
        Path(__file__).with_name("builtin_files.json").read_text(encoding="utf-8-sig")
    )
    if not isinstance(value, list) or any(not isinstance(p, str) for p in value):
        raise ValueError("Invalid builtin inventory")
    return frozenset(value)


def inspect_path(file_path: str | Path) -> PathInfo:
    """Describe ownership, protected descendants and a safe default clone path."""
    from app.workspace.code_editor._common import INCLUDE_DIR, PROJECT_ROOT

    logger.debug("FR-editor-path-policy: evaluated")
    path = Path(file_path)
    path = (PROJECT_ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    relative = path.relative_to(PROJECT_ROOT).as_posix()
    inside = path.is_relative_to(INCLUDE_DIR.resolve())
    builtin = relative in builtin_files()
    protected = (
        not inside
        or path == INCLUDE_DIR.resolve()
        or builtin
        or any(part.startswith((".", "__")) for part in Path(relative).parts)
        or (
            path.is_dir() and any(p.startswith(relative + "/") for p in builtin_files())
        )
    )
    tail = path.relative_to(INCLUDE_DIR).as_posix() if inside else path.name
    tail = tail.removeprefix("user/")
    if tail in (".", ""):
        tail = "snippet.py"
    clone = f"app/include/user/{Path(tail).with_name(path.stem + '_copy' + path.suffix).as_posix()}"
    return PathInfo(
        file_path=relative,
        ownership="builtin" if builtin else "user" if inside else "host",
        protected=protected,
        exists=path.exists(),
        clone_target=clone,
    )
