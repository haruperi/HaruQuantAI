"""Extract database state, migration schemas, and frontend UI coupling graphs.

Traces to: P2-T03, Gate G2
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

EXCLUDE_DIRS = {
    ".dev",
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    "out",
    "build",
    "dist",
}

STATE_KINDS = {
    "migration_order",
    "table_owner",
    "foreign_key",
    "shared_writer",
    "schema_id",
    "class_path",
    "cache",
    "persisted_registry",
    "idempotency",
    "audit",
}

FRONTEND_KINDS = {
    "typescript_import",
    "dynamic_import",
    "next_route",
    "navigation",
    "widget_registry",
    "api_client",
    "feature_store",
    "backend_assumption",
}

MIN_PATH_SEGMENTS = 2

TABLE_CREATE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", re.IGNORECASE
)
FK_RE = re.compile(r"REFERENCES\s+([a-zA-Z0-9_]+)\s*\(([a-zA-Z0-9_]+)\)", re.IGNORECASE)
TS_IMPORT_RE = re.compile(
    r"""import\s+(?:(?:(?:\*\s+as\s+\w+)|(?:\{[^}]*\})|(?:\w+))\s+from\s+)?['"]([^'"]+)['"]"""
)
TS_DYN_IMPORT_RE = re.compile(r"""import\s*\(\s*['"]([^'"]+)['"]\s*\)""")
PYTHON_PATH_RE = re.compile(r"\b(app\.[a-zA-Z0-9_\.]+)\b")


def get_git_commit(root: Path) -> str:
    """Get current git commit hash, falling back to 'unknown' if not a git repo.

    Args:
        root: Repository root path.

    Returns:
        Git commit hash or 'unknown'.
    """
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except subprocess.SubprocessError, OSError:
        return "unknown"


def _parse_sql_tables(
    rel_str: str, content: str, state_edges: list[dict[str, Any]]
) -> None:
    """Extract CREATE TABLE statements and foreign key constraints."""
    for match in TABLE_CREATE_RE.finditer(content):
        tbl_name = match.group(1)
        lineno = content[: match.start()].count("\n") + 1
        state_kind = "table_owner"
        if "audit" in tbl_name:
            state_kind = "audit"
        elif "cache" in tbl_name:
            state_kind = "cache"
        elif "idempotency" in tbl_name:
            state_kind = "idempotency"
        elif "registry" in tbl_name:
            state_kind = "persisted_registry"

        state_edges.append(
            {
                "source": rel_str,
                "kind": state_kind,
                "lineno": lineno,
                "name": tbl_name,
                "target": None,
            }
        )

    for match in FK_RE.finditer(content):
        ref_table = match.group(1)
        ref_col = match.group(2)
        lineno = content[: match.start()].count("\n") + 1
        state_edges.append(
            {
                "source": rel_str,
                "kind": "foreign_key",
                "lineno": lineno,
                "name": ref_table,
                "target": ref_col,
            }
        )


def extract_state_edges(
    root_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Scan migration and persistence files for state edges and paths.

    Args:
        root_path: Repository root path.

    Returns:
        Tuple of (state_edges, serialized_python_paths).
    """
    state_edges: list[dict[str, Any]] = []
    serialized_python_paths: list[dict[str, Any]] = []

    for p in root_path.rglob("*.py"):
        rel_parts = p.relative_to(root_path).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        rel_str = p.relative_to(root_path).as_posix()

        try:
            content = p.read_text(encoding="utf-8")
        except OSError:
            continue

        for match in PYTHON_PATH_RE.finditer(content):
            target_path = match.group(1)
            if target_path.count(".") >= MIN_PATH_SEGMENTS:
                lineno = content[: match.start()].count("\n") + 1
                serialized_python_paths.append(
                    {
                        "source": rel_str,
                        "lineno": lineno,
                        "path": target_path,
                    }
                )

        if "migration" in rel_str or "persistence" in rel_str or "schema" in rel_str:
            _parse_sql_tables(rel_str, content, state_edges)
            if "step" in content.lower() or "version" in content.lower():
                state_edges.append(
                    {
                        "source": rel_str,
                        "kind": "migration_order",
                        "lineno": 1,
                        "name": Path(rel_str).stem,
                        "target": None,
                    }
                )

    return state_edges, serialized_python_paths


def _scan_ts_routes_and_widgets(
    p: Path, rel_str: str, ui_root: Path, frontend_edges: list[dict[str, Any]]
) -> None:
    """Extract Next.js route declarations and widget registry components."""
    if "app/ui/src/app" in rel_str and p.name.startswith("page."):
        route_name = "/" + "/".join(
            p.parent.relative_to(ui_root / "src" / "app").parts
        ).replace("\\", "/")
        if route_name == "/.":
            route_name = "/"
        frontend_edges.append(
            {
                "source": rel_str,
                "kind": "next_route",
                "lineno": 1,
                "target": route_name,
            }
        )

    if "app/ui/src/widgets" in rel_str:
        widget_name = p.stem
        frontend_edges.append(
            {
                "source": rel_str,
                "kind": "widget_registry",
                "lineno": 1,
                "target": widget_name,
            }
        )


def _scan_ts_imports_and_calls(
    p: Path, rel_str: str, content: str, frontend_edges: list[dict[str, Any]]
) -> None:
    """Extract TS imports, dynamic imports, API client calls, and store usages."""
    for match in TS_IMPORT_RE.finditer(content):
        imp_target = match.group(1)
        lineno = content[: match.start()].count("\n") + 1
        frontend_edges.append(
            {
                "source": rel_str,
                "kind": "typescript_import",
                "lineno": lineno,
                "target": imp_target,
            }
        )

    for match in TS_DYN_IMPORT_RE.finditer(content):
        imp_target = match.group(1)
        lineno = content[: match.start()].count("\n") + 1
        frontend_edges.append(
            {
                "source": rel_str,
                "kind": "dynamic_import",
                "lineno": lineno,
                "target": imp_target,
            }
        )

    if "/api/" in content or "fetch(" in content or "client." in content:
        api_matches = re.findall(r"""['"](/api/v1/[a-zA-Z0-9_\-\/]+)['"]""", content)
        for api_endpoint in set(api_matches):
            frontend_edges.append(
                {
                    "source": rel_str,
                    "kind": "api_client",
                    "lineno": 1,
                    "target": api_endpoint,
                }
            )

    if "useStore" in content or "createContext" in content or "useReducer" in content:
        frontend_edges.append(
            {
                "source": rel_str,
                "kind": "feature_store",
                "lineno": 1,
                "target": p.stem,
            }
        )
    if "useRouter" in content or "next/link" in content or "<Link" in content:
        frontend_edges.append(
            {
                "source": rel_str,
                "kind": "navigation",
                "lineno": 1,
                "target": "router_navigation",
            }
        )


def extract_frontend_edges(root_path: Path) -> list[dict[str, Any]]:
    """Scan Next.js and TypeScript files in app/ui for frontend coupling edges.

    Args:
        root_path: Repository root path.

    Returns:
        List of frontend coupling edges.
    """
    frontend_edges: list[dict[str, Any]] = []
    ui_root = root_path / "app" / "ui"

    if not ui_root.exists():
        return frontend_edges

    for p in ui_root.rglob("*"):
        if not p.is_file():
            continue
        rel_parts = p.relative_to(root_path).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        rel_str = p.relative_to(root_path).as_posix()
        ext = p.suffix

        if ext not in (".ts", ".tsx", ".js", ".jsx"):
            continue

        try:
            content = p.read_text(encoding="utf-8")
        except OSError:
            continue

        _scan_ts_routes_and_widgets(p, rel_str, ui_root, frontend_edges)
        _scan_ts_imports_and_calls(p, rel_str, content, frontend_edges)

    return frontend_edges


def scan_state_and_frontend(root_path: Path) -> dict[str, Any]:
    """Extract complete state and frontend coupling graphs.

    Args:
        root_path: Repository root path.

    Returns:
        Dictionary containing state edges, frontend edges, and serialized paths.
    """
    state_edges, serialized_paths = extract_state_edges(root_path)
    frontend_edges = extract_frontend_edges(root_path)
    unexplained: list[dict[str, Any]] = []

    state_edges.sort(
        key=lambda s: (
            s["source"],
            s["kind"],
            s["lineno"],
            s.get("name") or "",
            s.get("target") or "",
        )
    )
    frontend_edges.sort(
        key=lambda f: (f["source"], f["kind"], f["lineno"], f.get("target") or "")
    )
    serialized_paths.sort(key=lambda p: (p["source"], p["lineno"], p["path"]))

    commit_hash = get_git_commit(root_path)

    return {
        "schema_version": 1,
        "commit": commit_hash,
        "state_edges": state_edges,
        "frontend_edges": frontend_edges,
        "serialized_python_paths": serialized_paths,
        "unexplained": unexplained,
    }


def main() -> int:
    """CLI entry point for state and frontend graph extraction.

    Returns:
        Exit code (0 on success).
    """
    parser = argparse.ArgumentParser(
        description="Extract state and frontend coupling graphs."
    )
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    root_path = Path(args.root).resolve()
    output_path = Path(args.output).resolve()

    graph = scan_state_and_frontend(root_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
