"""CodeEditor — Workspace Operations, Navigation, and Code Compilation Service.

Key Capabilities:
- FR-CODEEDITOR-MENU: Return editor action menus and toolbar configurations [CodeEditor.menu()]
- FR-CODEEDITOR-MAINTABS: List open document tabs and active states [CodeEditor.maintabs()]
- FR-CODEEDITOR-EDITORS: Inspect active editor files with unsaved indicators [CodeEditor.editors()]
- FR-CODEEDITOR-NAVIGATOR: Build hierarchical file tree of snippets [CodeEditor.navigator()]
- FR-CODEEDITOR-RIGHTTABS: Return right panel configuration (Navigator/Editors) [CodeEditor.righttabs()]
- FR-CODEEDITOR-BOTTOMTABS: Return bottom panel configuration (Logs/Search) [CodeEditor.bottomtabs()]
- FR-CODEEDITOR-LOGPANE: Read compilation diagnostic and syntax logs [CodeEditor.logpane()]
- FR-CODEEDITOR-SEARCHPANE: Read find-in-files search results [CodeEditor.searchpane()]
- FR-CODEEDITOR-NEW-FILE: Create new code file on disk [CodeEditor.new_file()]
- FR-CODEEDITOR-NEW-DIR: Create new directory in snippet workspace [CodeEditor.new_dir()]
- FR-CODEEDITOR-CREATE-NEW: Generate snippet from one of 12 templates [CodeEditor.create_new()]
- FR-CODEEDITOR-CLONE: Duplicate existing code file with unique name [CodeEditor.clone()]
- FR-CODEEDITOR-RENAME: Rename source file or directory [CodeEditor.rename_file()]
- FR-CODEEDITOR-DELETE: Safely delete file from workspace [CodeEditor.delete_file()]
- FR-CODEEDITOR-FIND: Search for text/regex across project files [CodeEditor.find_in_files()]
- FR-CODEEDITOR-COMPILE: Validate syntax and dynamically reload snippet [CodeEditor.compile_file()]
- FR-CODEEDITOR-COMPILE-ALL: Batch validate and reload all snippets [CodeEditor.compile_all()]
"""

from __future__ import annotations

import ast
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast, override

from app.host.logging import get_logger
from app.workspace.code_editor._common import (
    INCLUDE_DIR,
    PROJECT_ROOT,
    SNIPPETS_DIR,
    CodeEditorError,
    dynamic_import_source,
    resolve_safe_path,
    validate_python_syntax,
    writable_snippet_path,
)
from app.workspace.code_editor._template_generators import _to_pascal_case
from app.workspace.code_editor.editor import AppCodeEditor
from app.workspace.code_editor.registry import registry, unresolved_symbols
from app.workspace.code_editor.templates import render_template

logger = get_logger(__name__)


class CodeEditor:
    """Service handling code editor actions, file navigation, and snippet validation."""

    def __init__(self, editor: AppCodeEditor | None = None) -> None:
        self.editor = editor or AppCodeEditor()
        self._log_history: list[dict[str, Any]] = []
        self._search_history: list[dict[str, Any]] = []
        logger.info("Initialized CodeEditor service.")

    def menu(self) -> dict[str, Any]:
        """FR-CODEEDITOR-MENU: Display code editor main menu and action toolbar."""
        return {
            "toolbar": [
                {
                    "id": "create_new",
                    "label": "Create New",
                    "action": "dialog:create_new",
                },
                {"id": "save", "label": "Save", "shortcut": "Ctrl+S"},
                {"id": "save_all", "label": "Save All"},
                {"id": "compile", "label": "Compile", "shortcut": "F7"},
                {"id": "compile_all", "label": "Compile All"},
                {"id": "test_indicators", "label": "Test Indicators"},
                {
                    "id": "import_export",
                    "label": "Import/Export",
                    "options": ["import", "export"],
                },
                {"id": "find_in_files", "label": "Find in Files"},
            ]
        }

    def maintabs(self) -> list[dict[str, Any]]:
        """FR-CODEEDITOR-MAINTABS: Manage open editor document tabs."""
        state = self.editor.init_workspace()
        return cast("list[dict[str, Any]]", state.get("open_tabs", []))

    def editors(self) -> list[dict[str, Any]]:
        """FR-CODEEDITOR-EDITORS: List open editor files with dirty indicators."""
        return [
            {
                "file_path": tab["file_path"],
                "title": tab["title"],
                "is_dirty": tab["is_dirty"],
            }
            for tab in self.maintabs()
        ]

    def navigator(self, root_dir: str | None = None) -> dict[str, Any]:
        """FR-CODEEDITOR-NAVIGATOR: Build hierarchical file tree of snippet repository."""
        target_root = resolve_safe_path(root_dir) if root_dir else INCLUDE_DIR
        target_root.mkdir(parents=True, exist_ok=True)

        def _build_tree(folder: Path) -> dict[str, Any]:
            children = []
            for item in sorted(
                folder.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
            ):
                if item.is_symlink():
                    continue
                if item.name.startswith((".", "__pycache__")):
                    continue
                if item.is_dir():
                    children.append(_build_tree(item))
                else:
                    rel_p = item.relative_to(PROJECT_ROOT).as_posix()
                    children.append(
                        {
                            "id": rel_p,
                            "name": item.name,
                            "type": "file",
                            "extension": item.suffix.lstrip("."),
                            "path": rel_p,
                        }
                    )
            return {
                "id": folder.relative_to(PROJECT_ROOT).as_posix(),
                "name": folder.name,
                "type": "directory",
                "children": children,
            }

        tree = _build_tree(target_root)
        logger.info(
            f"Built navigator file tree rooted at {tree.get('name', 'snippets')}."
        )
        return tree

    def righttabs(self) -> dict[str, Any]:
        """FR-CODEEDITOR-RIGHTTABS: Return right panel tabs configuration."""
        return {
            "active_tab": "navigator",
            "tabs": ["navigator", "open_editors"],
        }

    def bottomtabs(self) -> dict[str, Any]:
        """FR-CODEEDITOR-BOTTOMTABS: Return bottom panel tabs configuration."""
        return {
            "active_tab": "log",
            "tabs": ["log", "search"],
        }

    def logpane(self) -> list[dict[str, Any]]:
        """FR-CODEEDITOR-LOGPANE: Return compilation and error logs."""
        return self._log_history

    def searchpane(self) -> list[dict[str, Any]]:
        """FR-CODEEDITOR-SEARCHPANE: Return find-in-files search results."""
        return self._search_history

    def new_file(self, file_path: str, content: str = "") -> dict[str, Any]:
        """FR-CODEEDITOR-NEW-FILE: Create a new source file."""
        resolved = resolve_safe_path(file_path)
        if resolved.exists():
            raise CodeEditorError(f"File already exists: {file_path}")
        return self.editor.save_file(str(resolved), content)

    def new_dir(self, dir_path: str) -> dict[str, Any]:
        """FR-CODEEDITOR-NEW-DIR: Create a new directory."""
        resolved = writable_snippet_path(dir_path)
        resolved.mkdir(parents=True, exist_ok=True)
        rel_p = resolved.relative_to(PROJECT_ROOT).as_posix()
        logger.info("Created new directory: %s", rel_p)
        return {"status": "created", "dir_path": rel_p}

    def create_new(
        self, template_type: str, name: str, category: str = "custom"
    ) -> dict[str, Any]:
        """FR-CODEEDITOR-CREATE-NEW: Generate a new snippet from one of 12 templates."""
        content, rel_path = render_template(template_type, name)
        resolved = resolve_safe_path(rel_path)
        if resolved.exists():
            raise CodeEditorError(
                f"Snippet already exists at {rel_path}. Choose a different name."
            )

        saved = self.editor.save_file(str(resolved), content)
        tab_info = self.editor.open_file_tab(str(resolved))
        logger.info("Created new snippet '%s' from template '%s'.", name, template_type)
        return {
            "status": "created",
            "template_type": template_type,
            "name": name,
            "file_path": saved["file_path"],
            "tab": tab_info["tab"],
        }

    def clone(self, source_path: str, target_path: str) -> dict[str, Any]:
        """FR-CODEEDITOR-CLONE: Duplicate an existing file."""
        src_res = resolve_safe_path(source_path)
        tgt_res = writable_snippet_path(target_path)
        if not src_res.exists():
            raise CodeEditorError(f"Source file does not exist: {source_path}")
        if tgt_res.exists():
            raise CodeEditorError(f"Target file already exists: {target_path}")

        content = src_res.read_text(encoding="utf-8")
        if src_res.suffix == ".py":
            tree = ast.parse(content)
            classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
            if classes:
                old_name = classes[0].name
                new_name = _to_pascal_case(tgt_res.stem)
                if not new_name.isidentifier():
                    raise CodeEditorError(
                        "Clone filename must produce a valid class name"
                    )

                class Rename(ast.NodeTransformer):
                    @override
                    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
                        if node.name == old_name:
                            node.name = new_name
                        return self.generic_visit(node)

                    @override
                    def visit_Name(self, node: ast.Name) -> ast.AST:
                        if node.id == old_name:
                            node.id = new_name
                        return node

                content = ast.unparse(Rename().visit(tree)) + "\n"
        return self.editor.save_file(str(tgt_res), content)

    def rename_file(self, old_path: str, new_path: str) -> dict[str, Any]:
        """FR-CODEEDITOR-RENAME: Rename a file or directory."""
        old_res = writable_snippet_path(old_path)
        new_res = writable_snippet_path(new_path)
        if not old_res.exists():
            raise CodeEditorError(f"Source path does not exist: {old_path}")
        if new_res.exists():
            raise CodeEditorError(f"Destination path already exists: {new_path}")

        if old_res.is_dir() and any(
            p.name.startswith((".", "__")) for p in old_res.rglob("*")
        ):
            raise CodeEditorError("Directory contains protected package files")
        old_res.rename(new_res)
        old_p = old_res.relative_to(PROJECT_ROOT).as_posix()
        new_p = new_res.relative_to(PROJECT_ROOT).as_posix()
        self.editor.remap_tabs(old_p, new_p)
        registry.unregister(str(old_res))
        logger.info("Renamed %s -> %s", old_path, new_path)
        return {"status": "renamed", "old_path": old_p, "new_path": new_p}

    def delete_file(self, file_path: str) -> dict[str, Any]:
        """FR-CODEEDITOR-DELETE: Safely remove file or folder."""
        resolved = writable_snippet_path(file_path)
        if not resolved.exists():
            raise CodeEditorError(f"Target does not exist: {file_path}")

        rel_p = resolved.relative_to(PROJECT_ROOT).as_posix()
        if resolved.is_dir():
            if any(p.name.startswith((".", "__")) for p in resolved.rglob("*")):
                raise CodeEditorError("Directory contains protected package files")
            shutil.rmtree(resolved)
        else:
            resolved.unlink()
        self.editor.remap_tabs(rel_p, None)
        registry.unregister(str(resolved))
        logger.info("Deleted %s", file_path)
        return {"status": "deleted", "file_path": rel_p}

    def find_in_files(
        self,
        query: str,
        *,
        case_sensitive: bool = False,
        regex: bool = False,
        whole_word: bool = False,
        search_dir: str | None = None,
    ) -> list[dict[str, Any]]:
        """FR-CODEEDITOR-FIND: Search for text or patterns across snippets."""
        root = resolve_safe_path(search_dir) if search_dir else SNIPPETS_DIR
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern_str = query
        if not regex:
            pattern_str = re.escape(query)
        if whole_word:
            pattern_str = rf"\b{pattern_str}\b"

        matcher = re.compile(pattern_str, flags)
        matches: list[dict[str, Any]] = []

        if root.exists():
            for p in root.rglob("*.py"):
                try:
                    lines = p.read_text(encoding="utf-8").splitlines()
                    for idx, line in enumerate(lines, start=1):
                        for m in matcher.finditer(line):
                            matches.append(
                                {
                                    "file": p.relative_to(PROJECT_ROOT).as_posix(),
                                    "line": idx,
                                    "column": m.start() + 1,
                                    "text": line.strip(),
                                    "match": m.group(0),
                                }
                            )
                except Exception as exc:
                    logger.debug("Could not read %s: %s", p, exc)

        self._search_history = matches
        logger.info(f"Find in files for '{query}' found {len(matches)} match(es).")
        return matches

    def compile_file(
        self, file_path: str, content: str | None = None
    ) -> dict[str, Any]:
        """FR-CODEEDITOR-COMPILE: Validate syntax and dynamically reload module."""
        resolved = resolve_safe_path(file_path)
        code_str = (
            content if content is not None else resolved.read_text(encoding="utf-8")
        )
        diagnostics = validate_python_syntax(code_str)

        log_entry: dict[str, Any] = {
            "file": resolved.relative_to(PROJECT_ROOT).as_posix(),
            "timestamp": datetime.now(UTC).isoformat(),
            "success": len(diagnostics) == 0,
            "errors": [d.to_dict() for d in diagnostics],
        }

        if not diagnostics:
            log_entry["errors"].extend(unresolved_symbols(code_str, str(resolved)))
            log_entry["success"] = not log_entry["errors"]
        if log_entry["success"]:
            try:
                module = dynamic_import_source(resolved, code_str)
                log_entry["registered_classes"] = registry.register(resolved, module)
                log_entry["module_reloaded"] = True
            except Exception as err:
                log_entry["success"] = False
                log_entry["errors"].append(
                    {
                        "line": 1,
                        "column": 1,
                        "message": f"Runtime import failed: {err}",
                        "severity": "error",
                    }
                )

        self._log_history.insert(0, log_entry)
        logger.info(
            f"Compiled {file_path}. Valid: {log_entry['success']}, Errors: {len(log_entry['errors'])}"
        )
        return log_entry

    def compile_all(self) -> dict[str, Any]:
        """FR-CODEEDITOR-COMPILE-ALL: Batch validate all snippet files."""
        results = []
        for path in list(registry.blocks):
            if not Path(path).exists():
                registry.unregister(path)
        if SNIPPETS_DIR.exists():
            for p in SNIPPETS_DIR.rglob("*.py"):
                if not p.name.startswith("__"):
                    results.append(self.compile_file(str(p)))

        success_count = sum(1 for r in results if r["success"])
        logger.info(
            f"Compile All completed. {success_count}/{len(results)} snippets valid."
        )
        return {
            "status": "completed",
            "total_files": len(results),
            "valid_files": success_count,
            "results": results,
        }
