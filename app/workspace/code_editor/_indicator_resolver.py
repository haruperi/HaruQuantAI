"""Resolve declared indicator classes within the unified include library."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any

from app.include.indicators.base import BaseIndicator
from app.workspace.code_editor._common import (
    INCLUDE_DIR,
    PROJECT_ROOT,
    CodeEditorError,
    dynamic_import_from_path,
    resolve_safe_path,
)
from app.workspace.code_editor.registry import registry


def _normalize(name: str) -> str:
    return name.replace("_", "").casefold()


def _safe_indicator_path(path: Path) -> Path:
    root = INCLUDE_DIR / "indicators"
    resolved = resolve_safe_path(path, root)
    if resolved.suffix != ".py" or any(
        part.startswith((".", "__")) for part in resolved.relative_to(root).parts
    ):
        raise CodeEditorError("Choose a public Python file in app/include/indicators")
    if not resolved.is_file():
        raise CodeEditorError(f"Indicator file not found: {path}")
    return resolved


def _classes(path: Path) -> dict[str, type[Any]]:
    cached = registry.blocks.get(str(path))
    if cached is None:
        module = dynamic_import_from_path(path)
        cached = {
            name: cls
            for name, cls in vars(module).items()
            if inspect.isclass(cls) and cls.__module__ == module.__name__
        }
    return {
        name: cls
        for name, cls in cached.items()
        if issubclass(cls, BaseIndicator) and not inspect.isabstract(cls)
    }


def resolve_indicator(name: str) -> type[Any]:
    """Prefer live compiled classes; never execute imports outside indicator roots."""
    clean = name.replace("\\", "/").strip()
    root = INCLUDE_DIR / "indicators"
    if clean.endswith(".py") or "/" in clean:
        raw = Path(clean)
        candidate = (
            raw
            if raw.is_absolute()
            else PROJECT_ROOT / raw
            if clean.startswith("app/")
            else root / raw
        )
        path = _safe_indicator_path(candidate)
        classes = _classes(path)
        matching_classes = list(
            dict.fromkeys(
                cls
                for key, cls in classes.items()
                if _normalize(key) == _normalize(path.stem)
            )
        )
        if len(matching_classes) == 1:
            return matching_classes[0]
        if len(set(classes.values())) == 1:
            return next(iter(classes.values()))
        raise CodeEditorError(
            f"Choose an indicator class name; {path.name} declares {len(classes)} concrete indicators"
        )
    if not clean.isidentifier() or clean.startswith("_"):
        raise CodeEditorError(
            "Choose an indicator class name or a confined Python file path"
        )
    target = _normalize(clean)
    candidates: dict[Path, list[str]] = {}
    # Inspect declarations without executing unrelated modules or their dependencies.
    for raw in root.rglob("*.py"):
        if any(part.startswith((".", "__")) for part in raw.relative_to(root).parts):
            continue
        try:
            path = _safe_indicator_path(raw)
        except CodeEditorError:
            continue
        if str(path) in registry.blocks:
            names = list(registry.blocks[str(path)])
        else:
            try:
                tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            except (SyntaxError, UnicodeError) as exc:
                if _normalize(path.stem) == target:
                    raise CodeEditorError(
                        f"Invalid indicator source: {path.name}: {exc}"
                    ) from exc
                continue
            names = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
        matching = [key for key in names if _normalize(key) == target]
        if matching:
            candidates[path] = matching
        elif _normalize(path.stem) == target:
            candidates[path] = []
    if len(candidates) > 1:
        raise CodeEditorError(
            f"Multiple indicators match '{name}'; choose a full indicator file path"
        )
    for path, names in candidates.items():
        classes = _classes(path)
        matched = [cls for key, cls in classes.items() if key in names]
        if len(matched) == 1:
            return matched[0]
        if not names and len(classes) == 1:
            return next(iter(classes.values()))
    raise CodeEditorError(
        f"Indicator '{name}' could not be resolved in indicators library"
    )
