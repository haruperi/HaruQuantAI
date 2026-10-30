"""Routes editor contracts and workflows.

Description:
    Coordinates typed navigation, file commands, search and synchronous compilation.
    Existing generators and registry own their implementations; no jobs are created.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Preserve typed editor behavior and host ownership.
Key Capabilities:
    - FR-code-editor-routes: Observe the associated workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-bottomtabs: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-clone: Observe the associated workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-compile-all: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-compile-file: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-create-new: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-delete-file: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-editors: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-find-in-files: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-init: Observe the associated workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-logpane: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-maintabs: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-menu: Observe the associated workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-navigator: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-new-dir: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-new-file: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-rename-file: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-righttabs: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-searchpane: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-routes-visit-: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
Python API Usage:
    import app.workspace.code_editor.routes
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

from __future__ import annotations

import ast
import logging
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import override

from app.workspace.code_editor._common import (
    INCLUDE_DIR,
    PROJECT_ROOT,
    CodeEditorError,
    dynamic_import_source,
    resolve_safe_path,
    validate_python_syntax,
    writable_snippet_path,
)
from app.workspace.code_editor._template_generators import _to_pascal_case
from app.workspace.code_editor.editor import AppCodeEditor
from app.workspace.code_editor.registry import registry, unresolved_symbols
from app.workspace.code_editor.results import (
    CompileAllResult,
    CompileResult,
    CreatedSnippet,
    DeleteResult,
    DirectoryResult,
    EditorSummary,
    Menu,
    NavigatorItem,
    PanelTabs,
    RenameResult,
    SaveResult,
    SearchMatch,
    Tab,
)
from app.workspace.code_editor.templates import render_template

logger = logging.getLogger(__name__)


class CodeEditor:
    """Service handling code editor actions, file navigation, and snippet validation."""

    def __init__(self, editor: AppCodeEditor | None = None) -> None:
        logger.debug("FR-code-editor-routes-init: invoked")
        self.editor = editor or AppCodeEditor()
        self._log_history: list[CompileResult] = []
        self._search_history: list[SearchMatch] = []
        logger.info("FR-code-editor-routes: operation")

    def menu(self) -> Menu:
        """FR-CODEEDITOR-MENU: Display code editor main menu and action toolbar."""
        logger.debug("FR-code-editor-routes-menu: invoked")
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

    def maintabs(self) -> list[Tab]:
        """FR-CODEEDITOR-MAINTABS: Manage open editor document tabs."""
        logger.debug("FR-code-editor-routes-maintabs: invoked")
        state = self.editor.init_workspace()
        return state["open_tabs"]

    def editors(self) -> list[EditorSummary]:
        """FR-CODEEDITOR-EDITORS: List open editor files with dirty indicators."""
        logger.debug("FR-code-editor-routes-editors: invoked")
        return [
            {
                "file_path": tab["file_path"],
                "title": tab["title"],
                "is_dirty": tab["is_dirty"],
            }
            for tab in self.maintabs()
        ]

    def navigator(self, root_dir: str | None = None) -> NavigatorItem:
        """FR-CODEEDITOR-NAVIGATOR: Build hierarchical file tree of snippet repository."""
        logger.debug("FR-code-editor-routes-navigator: invoked")
        target_root = resolve_safe_path(root_dir) if root_dir else INCLUDE_DIR
        target_root.mkdir(parents=True, exist_ok=True)

        def _build_tree(folder: Path) -> NavigatorItem:
            children: list[NavigatorItem] = []
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
        logger.info("FR-code-editor-routes: operation")
        return tree

    def righttabs(self) -> PanelTabs:
        """FR-CODEEDITOR-RIGHTTABS: Return right panel tabs configuration."""
        logger.debug("FR-code-editor-routes-righttabs: invoked")
        return {
            "active_tab": "navigator",
            "tabs": ["navigator", "open_editors"],
        }

    def bottomtabs(self) -> PanelTabs:
        """FR-CODEEDITOR-BOTTOMTABS: Return bottom panel tabs configuration."""
        logger.debug("FR-code-editor-routes-bottomtabs: invoked")
        return {
            "active_tab": "log",
            "tabs": ["log", "search"],
        }

    def logpane(self) -> list[CompileResult]:
        """FR-CODEEDITOR-LOGPANE: Return compilation and error logs."""
        logger.debug("FR-code-editor-routes-logpane: invoked")
        return self._log_history

    def searchpane(self) -> list[SearchMatch]:
        """FR-CODEEDITOR-SEARCHPANE: Return find-in-files search results."""
        logger.debug("FR-code-editor-routes-searchpane: invoked")
        return self._search_history

    def new_file(self, file_path: str, content: str = "") -> SaveResult:
        """FR-CODEEDITOR-NEW-FILE: Create a new source file."""
        logger.debug("FR-code-editor-routes-new-file: invoked")
        resolved = resolve_safe_path(file_path)
        if resolved.exists():
            raise CodeEditorError(f"File already exists: {file_path}")
        return self.editor.save_file(str(resolved), content)

    def new_dir(self, dir_path: str) -> DirectoryResult:
        """FR-CODEEDITOR-NEW-DIR: Create a new directory."""
        logger.debug("FR-code-editor-routes-new-dir: invoked")
        resolved = writable_snippet_path(dir_path)
        resolved.mkdir(parents=True, exist_ok=True)
        rel_p = resolved.relative_to(PROJECT_ROOT).as_posix()
        logger.info("FR-code-editor-routes: operation")
        return {"status": "created", "dir_path": rel_p}

    def create_new(
        self, template_type: str, name: str, category: str = "custom"
    ) -> CreatedSnippet:
        """FR-CODEEDITOR-CREATE-NEW: Generate a new snippet from one of 12 templates."""
        logger.debug("FR-code-editor-routes-create-new: invoked")
        content, rel_path = render_template(template_type, name, category=category)
        resolved = resolve_safe_path(rel_path)
        if resolved.exists():
            raise CodeEditorError(
                f"Snippet already exists at {rel_path}. Choose a different name."
            )

        saved = self.editor.save_file(str(resolved), content)
        tab_info = self.editor.open_file_tab(str(resolved))
        logger.info("FR-code-editor-routes: operation")
        return {
            "status": "created",
            "template_type": template_type,
            "name": name,
            "file_path": saved["file_path"],
            "tab": tab_info["tab"],
        }

    def clone(self, source_path: str, target_path: str) -> SaveResult:
        """FR-CODEEDITOR-CLONE: Duplicate an existing file."""
        logger.debug("FR-code-editor-routes-clone: invoked")
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
                        logger.debug("FR-code-editor-routes-visit-ClassDef: invoked")
                        if node.name == old_name:
                            node.name = new_name
                        return self.generic_visit(node)

                    @override
                    def visit_Name(self, node: ast.Name) -> ast.AST:
                        logger.debug("FR-code-editor-routes-visit-Name: invoked")
                        if node.id == old_name:
                            node.id = new_name
                        return node

                content = ast.unparse(Rename().visit(tree)) + "\n"
        return self.editor.save_file(str(tgt_res), content)

    def rename_file(self, old_path: str, new_path: str) -> RenameResult:
        """FR-CODEEDITOR-RENAME: Rename a file or directory."""
        logger.debug("FR-code-editor-routes-rename-file: invoked")
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
        logger.info("FR-code-editor-routes: operation")
        return {"status": "renamed", "old_path": old_p, "new_path": new_p}

    def delete_file(self, file_path: str) -> DeleteResult:
        """FR-CODEEDITOR-DELETE: Safely remove file or folder."""
        logger.debug("FR-code-editor-routes-delete-file: invoked")
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
        logger.info("FR-code-editor-routes: operation")
        return {"status": "deleted", "file_path": rel_p}

    def find_in_files(
        self,
        query: str,
        *,
        case_sensitive: bool = False,
        regex: bool = False,
        whole_word: bool = False,
        search_dir: str | None = None,
    ) -> list[SearchMatch]:
        """FR-CODEEDITOR-FIND: Search for text or patterns across snippets."""
        logger.debug("FR-code-editor-routes-find-in-files: invoked")
        root = resolve_safe_path(search_dir) if search_dir else INCLUDE_DIR
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern_str = query
        if not regex:
            pattern_str = re.escape(query)
        if whole_word:
            pattern_str = rf"\b{pattern_str}\b"

        matcher = re.compile(pattern_str, flags)
        matches: list[SearchMatch] = []

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
                    logger.debug("FR-code-editor-routes: operation")

        self._search_history = matches
        logger.info("FR-code-editor-routes: operation")
        return matches

    def compile_file(self, file_path: str, content: str | None = None) -> CompileResult:
        """FR-CODEEDITOR-COMPILE: Validate syntax and dynamically reload module."""
        logger.debug("FR-code-editor-routes-compile-file: invoked")
        resolved = resolve_safe_path(file_path)
        code_str = (
            content if content is not None else resolved.read_text(encoding="utf-8")
        )
        diagnostics = validate_python_syntax(code_str)

        log_entry: CompileResult = {
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
                        "message": str(err)
                        if isinstance(err, CodeEditorError)
                        else "Runtime import failed",
                        "severity": "error",
                    }
                )

        self._log_history.insert(0, log_entry)
        logger.info("FR-code-editor-routes: operation")
        return log_entry

    def compile_all(self) -> CompileAllResult:
        """FR-CODEEDITOR-COMPILE-ALL: Batch validate all snippet files."""
        logger.debug("FR-code-editor-routes-compile-all: invoked")
        results = []
        for path in list(registry.blocks):
            if not Path(path).exists():
                registry.unregister(path)
        if INCLUDE_DIR.exists():
            for p in INCLUDE_DIR.rglob("*.py"):
                if not p.name.startswith((".", "__")):
                    results.append(self.compile_file(str(p)))

        success_count = sum(1 for r in results if r["success"])
        logger.info("FR-code-editor-routes: operation")
        return {
            "status": "completed",
            "total_files": len(results),
            "valid_files": success_count,
            "results": results,
        }
