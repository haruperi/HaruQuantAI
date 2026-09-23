"""Check the ratified post-reset Python architecture boundaries."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def _imports(tree: ast.AST, path: Path, app_root: Path) -> list[str]:
    """Return resolved absolute and relative import module names."""
    names: list[str] = []
    package = ["app", *path.relative_to(app_root).parts[:-1]]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                names.append(node.module or "")
            else:
                prefix = package[: len(package) - node.level + 1]
                if node.module:
                    names.append(".".join([*prefix, node.module]))
                else:
                    names.extend(
                        ".".join([*prefix, alias.name]) for alias in node.names
                    )
    return names


def _init_issues(path: Path, relative: str, tree: ast.Module) -> list[str]:
    """Check that package initialization has no executable statements."""
    if path.name != "__init__.py" or not tree.body:
        return []
    first = tree.body[0]
    if (
        len(tree.body) == 1
        and isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return []
    return [f"{relative}: __init__.py must be empty or docstring-only"]


def _import_issues(
    path: Path, relative: str, app_root: Path, imports: list[str]
) -> list[str]:
    """Check host, kernel, and plugin import direction."""
    issues: list[str] = []
    if path.is_relative_to(app_root / "host"):
        forbidden = ("app.workspace", "app.plugins", "app.services", "app.ui")
        issues.extend(
            f"{relative}: host imports domain or UI module {name}"
            for name in imports
            if name.startswith(forbidden)
        )
    if path.is_relative_to(app_root / "kernel"):
        issues.extend(
            f"{relative}: kernel imports non-stdlib module {name}"
            for name in imports
            if name.split(".", 1)[0] not in sys.stdlib_module_names
        )
    plugins_root = app_root / "plugins"
    if path.is_relative_to(plugins_root):
        family = path.relative_to(plugins_root).parts[0]
        for name in imports:
            if name.startswith("app.workspace"):
                issues.append(f"{relative}: plugin imports workspace module {name}")
            if name.startswith("app.plugins."):
                parts = name.split(".")
                imported_family = parts[2]
                if (
                    imported_family != family
                    and (plugins_root / imported_family).is_dir()
                ):
                    issues.append(f"{relative}: plugin imports sibling module {name}")
                if (
                    imported_family == family
                    and len(parts) > 3
                    and parts[3] != path.stem
                    and (plugins_root / family / f"{parts[3]}.py").is_file()
                ):
                    issues.append(f"{relative}: plugin imports sibling module {name}")
    return issues


def check_repository(root: Path) -> list[str]:
    """Return violations of the current host, kernel, and package rules."""
    app_root = root / "app"
    issues: list[str] = []
    if not app_root.is_dir():
        return ["app/ is missing"]
    for path in sorted(app_root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except (OSError, UnicodeError, SyntaxError) as error:
            issues.append(f"{relative}: cannot parse Python source: {error}")
            continue
        issues.extend(_init_issues(path, relative, tree))
        issues.extend(
            _import_issues(path, relative, app_root, _imports(tree, path, app_root))
        )
    return issues


def main() -> int:
    """Print violations and return a failing exit status when any exist."""
    root = Path(__file__).resolve().parents[1]
    issues = check_repository(root)
    if issues:
        for issue in issues:
            print(issue)
        return 1
    print("Architecture checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
