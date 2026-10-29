"""AppCodeEditor — Code Workspace Host and Document Session Manager.

Key Capabilities:
- FR-CODEEDITOR-INIT: Initialize dockable editor layout and document tabs [AppCodeEditor.init_workspace()]
- FR-CODEEDITOR-OPEN-TAB: Open file in an editor tab with dirty tracking [AppCodeEditor.open_file_tab()]
- FR-CODEEDITOR-CLOSE-TAB: Close tab with unsaved change protection [AppCodeEditor.close_file_tab()]
- FR-CODEEDITOR-SAVE: Save file content atomically and update diagnostics [AppCodeEditor.save_file()]
- FR-CODEEDITOR-SAVE-ALL: Atomically save all open dirty tabs [AppCodeEditor.save_all_files()]
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.core.host.logging import get_logger
from app.workspace.code_editor._common import (
    PROJECT_ROOT,
    CodeEditorError,
    EditorTab,
    resolve_safe_path,
    validate_python_syntax,
    writable_snippet_path,
)
from app.workspace.code_editor._storage import StateStore, atomic_write_batch

logger = get_logger(__name__)


class AppCodeEditor:
    """Manages open document sessions, tabs, and file content persistence."""

    def __init__(self, store: StateStore | None = None) -> None:
        self._tabs: dict[str, EditorTab] = {}
        self._active_file: str | None = None
        self._store = store or StateStore()
        self._restored = False
        logger.info("Initialized AppCodeEditor document workspace.")

    def init_workspace(self) -> dict[str, Any]:
        """FR-CODEEDITOR-INIT: Initialize workspace state and panel configuration."""
        self._restore()
        logger.info("Initializing code editor workspace panels and tabs.")
        return {
            "status": "ready",
            "active_file": self._active_file,
            "open_tabs": [tab.to_dict() for tab in self._tabs.values()],
            "layout": {
                "navigator_visible": True,
                "split_mode": "single",
                "bottom_panel": "log",
            },
        }

    def open_file_tab(self, file_path: str, *, mode: str = "python") -> dict[str, Any]:
        """FR-CODEEDITOR-OPEN-TAB: Open file in tab, reading content from disk."""
        self._restore()
        resolved = resolve_safe_path(file_path)
        rel_path = resolved.relative_to(PROJECT_ROOT).as_posix()

        if rel_path in self._tabs:
            self._active_file = rel_path
            self._persist()
            logger.info("Switched to already open tab: %s", rel_path)
            return {
                "status": "switched",
                "tab": self._tabs[rel_path].to_dict(),
                "active_file": self._active_file,
            }

        if not resolved.exists():
            msg = f"Cannot open file. Path does not exist: {file_path}"
            logger.error(msg)
            raise CodeEditorError(msg)

        content = resolved.read_text(encoding="utf-8")
        tab = EditorTab(
            file_path=rel_path,
            title=resolved.name,
            content=content,
            is_dirty=False,
            mode=mode,
        )
        self._tabs[rel_path] = tab
        self._active_file = rel_path
        self._persist()
        logger.info("Opened new editor tab for: %s", rel_path)
        return {
            "status": "opened",
            "tab": tab.to_dict(),
            "active_file": self._active_file,
        }

    def close_file_tab(self, file_path: str, *, force: bool = False) -> dict[str, Any]:
        """FR-CODEEDITOR-CLOSE-TAB: Close open tab, checking for unsaved changes."""
        self._restore()
        resolved = resolve_safe_path(file_path)
        rel_path = resolved.relative_to(PROJECT_ROOT).as_posix()

        if rel_path not in self._tabs:
            logger.warning("Attempted to close non-open tab: %s", rel_path)
            return {"status": "not_open", "active_file": self._active_file}

        tab = self._tabs[rel_path]
        if tab.is_dirty and not force:
            logger.warning("Refusing to close dirty tab without force: %s", rel_path)
            return {
                "status": "unsaved_changes",
                "file_path": rel_path,
                "active_file": self._active_file,
            }

        del self._tabs[rel_path]
        if self._active_file == rel_path:
            self._active_file = next(iter(self._tabs.keys()), None)

        self._persist()
        logger.info(f"Closed tab: {rel_path}. New active file: {self._active_file}")
        return {
            "status": "closed",
            "closed_file": rel_path,
            "active_file": self._active_file,
        }

    def save_file(self, file_path: str, content: str) -> dict[str, Any]:
        """FR-CODEEDITOR-SAVE: Save file content to disk and return diagnostics."""
        self._restore()
        resolved = writable_snippet_path(file_path)
        atomic_write_batch({resolved: content.encode("utf-8")})

        rel_path = resolved.relative_to(PROJECT_ROOT).as_posix()
        diagnostics = (
            validate_python_syntax(content) if resolved.suffix == ".py" else []
        )

        if rel_path in self._tabs:
            tab = self._tabs[rel_path]
            tab.content = content
            tab.is_dirty = False

        self._persist()
        logger.info(
            f"Saved file {rel_path} ({len(content)} chars). Diagnostics: {len(diagnostics)}"
        )
        return {
            "status": "saved",
            "file_path": rel_path,
            "bytes_written": len(content.encode("utf-8")),
            "diagnostics": [d.to_dict() for d in diagnostics],
        }

    def save_all_files(
        self, files: Sequence[Mapping[str, str]] | None = None
    ) -> dict[str, Any]:
        """FR-CODEEDITOR-SAVE-ALL: Atomically save multiple dirty files."""
        self._restore()
        records = (
            list(files)
            if files is not None
            else [
                {"file_path": path, "content": tab.content}
                for path, tab in self._tabs.items()
                if tab.is_dirty
            ]
        )
        pending = {}
        for item in records:
            path = writable_snippet_path(item["file_path"])
            if path in pending:
                raise CodeEditorError("Duplicate destination in Save All")
            pending[path] = item["content"].encode("utf-8")
        atomic_write_batch(pending)
        saved_records = []
        for path, content in pending.items():
            relative = path.relative_to(PROJECT_ROOT).as_posix()
            text = content.decode("utf-8")
            if relative in self._tabs:
                self._tabs[relative].content = text
                self._tabs[relative].is_dirty = False
            saved_records.append(
                {
                    "file_path": relative,
                    "diagnostics": [d.to_dict() for d in validate_python_syntax(text)]
                    if path.suffix == ".py"
                    else [],
                }
            )
        self._persist()
        logger.info("Saved batch of %s documents", len(saved_records))
        return {
            "status": "saved_all",
            "count": len(saved_records),
            "files": saved_records,
        }

    def sync_session(
        self, tabs: Sequence[Mapping[str, Any]], active_file: str | None
    ) -> dict[str, Any]:
        """FR-CODEEDITOR-SESSION: Persist dirty buffers and the active document."""
        self._restore()
        updated = {}
        for item in tabs:
            path = resolve_safe_path(item["file_path"])
            relative = path.relative_to(PROJECT_ROOT).as_posix()
            tab = EditorTab(
                file_path=relative,
                title=path.name,
                content=item["content"],
                mode=item.get("mode", "python"),
            )
            tab.is_dirty = (
                not path.is_file() or path.read_text(encoding="utf-8") != tab.content
            )
            updated[relative] = tab
        if active_file is not None and active_file not in updated:
            raise CodeEditorError("Active document must be an open tab")
        self._tabs = updated
        self._active_file = active_file
        self._persist()
        return self.init_workspace()

    def _restore(self) -> None:
        if self._restored:
            return
        state = self._store.read("workspace") or {}
        self._tabs = {
            item["file_path"]: EditorTab(**item) for item in state.get("open_tabs", [])
        }
        self._active_file = state.get("active_file")
        self._restored = True

    def _persist(self) -> None:
        self._store.write(
            "workspace",
            {
                "open_tabs": [tab.to_dict() for tab in self._tabs.values()],
                "active_file": self._active_file,
            },
        )

    def remap_tabs(self, old_path: str, new_path: str | None) -> None:
        """FR-CODEEDITOR-REMAP: Preserve buffers when paths move or are deleted."""
        self._restore()
        for path in list(self._tabs):
            if path == old_path or path.startswith(old_path + "/"):
                tab = self._tabs.pop(path)
                replacement = new_path + path[len(old_path) :] if new_path else None
                if replacement:
                    tab.file_path = replacement
                    tab.title = replacement.rsplit("/", 1)[-1]
                    self._tabs[replacement] = tab
                if self._active_file == path:
                    self._active_file = replacement
        if self._active_file not in self._tabs:
            self._active_file = next(iter(self._tabs), None)
        self._persist()
