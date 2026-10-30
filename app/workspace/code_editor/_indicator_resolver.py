"""Indicator resolver editor contracts and workflows.

Description:
    Resolves canonical or compiled indicator classes only within authorized roots.
    Dynamic introspection stays behind the class-resolution boundary.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Preserve typed editor behavior and host ownership.
Key Capabilities:
    - FR-code-editor-indicator-resolver-resolve-indicator: Observe the associated
      workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
Python API Usage:
    import app.workspace.code_editor._indicator_resolver
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

from __future__ import annotations

import ast
import inspect
import logging
from pathlib import Path

from app.include.blocks.indicators.base import BaseIndicator
from app.workspace.code_editor._common import (
    INCLUDE_DIR,
    PROJECT_ROOT,
    CodeEditorError,
    dynamic_import_from_path,
    resolve_safe_path,
)
from app.workspace.code_editor.registry import registry

logger = logging.getLogger(__name__)


INDICATOR_ROOTS: tuple[Path, ...] = (INCLUDE_DIR / "blocks" / "indicators",)


def _normalize(name: str) -> str:
    return name.replace("_", "").casefold()


def _safe_indicator_path(path: Path) -> Path:
    raw_str = str(path).replace("\\", "/")
    if path.is_absolute():
        resolved_candidate = path.resolve()
    elif raw_str.startswith("app/"):
        resolved_candidate = (PROJECT_ROOT / path).resolve()
    else:
        resolved_candidate = None

    if resolved_candidate is not None:
        for root in INDICATOR_ROOTS:
            root_res = root.resolve()
            if resolved_candidate.is_relative_to(root_res):
                resolved = resolve_safe_path(resolved_candidate, root_res)
                if resolved.suffix == ".py" and not any(
                    part.startswith((".", "__"))
                    for part in resolved.relative_to(root_res).parts
                ):
                    if resolved.is_file():
                        return resolved
                    raise CodeEditorError(f"Indicator file not found: {path}")
        raise CodeEditorError(
            "Choose a public Python file in app/include/blocks/indicators"
        )

    # Relative path without leading app/
    found_candidates: list[Path] = []
    for root in INDICATOR_ROOTS:
        try:
            cand = resolve_safe_path(path, root)
            if (
                cand.is_file()
                and cand.suffix == ".py"
                and not any(
                    part.startswith((".", "__"))
                    for part in cand.relative_to(root.resolve()).parts
                )
            ):
                found_candidates.append(cand)
        except CodeEditorError, ValueError:
            pass

    if len(found_candidates) == 1:
        return found_candidates[0]
    if len(found_candidates) > 1:
        raise CodeEditorError(f"Multiple indicators match '{path}'")

    raise CodeEditorError(f"Indicator file not found: {path}")


def _classes(path: Path) -> dict[str, type[BaseIndicator]]:
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


def resolve_indicator(name: str) -> type[BaseIndicator]:
    """Prefer live compiled classes; never execute imports outside indicator roots."""
    logger.debug("FR-code-editor-indicator-resolver-resolve-indicator: invoked")
    clean = name.replace("\\", "/").strip()
    if "::" in clean:
        file_name, class_name = clean.rsplit("::", 1)
        if not class_name.isidentifier() or class_name.startswith("_"):
            raise CodeEditorError("Invalid indicator class identity")
        classes = _classes(_safe_indicator_path(Path(file_name)))
        if class_name not in classes:
            raise CodeEditorError("Indicator class is not declared by this file")
        return classes[class_name]
    if clean.endswith(".py") or "/" in clean:
        raw = Path(clean)
        path = _safe_indicator_path(raw)
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
    for root in INDICATOR_ROOTS:
        if not root.exists():
            continue
        for raw in root.rglob("*.py"):
            rel_parts = raw.relative_to(root).parts
            if any(part.startswith((".", "__")) for part in rel_parts):
                continue
            path = raw
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
                names = [
                    node.name for node in tree.body if isinstance(node, ast.ClassDef)
                ]
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
