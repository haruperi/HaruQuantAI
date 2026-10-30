"""Editor editor contracts and workflows.

Description:
    Restores validated document sessions and performs typed buffer, save and session
    operations. Corrupt stored snapshots are rejected before publication.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Preserve typed editor behavior and host ownership.
Key Capabilities:
    - FR-code-editor-save-as: Publish a new file and persist replacement tab
      identity; collision, preservation, failure and logging cases are tested.
    - FR-code-editor-editor: Observe the associated workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-editor-close-file-tab: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-editor-init: Observe the associated workflow; fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-editor-init-workspace: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-editor-open-file-tab: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-editor-remap-tabs: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-editor-save-all-files: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-editor-save-file: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-editor-sync-session: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-session-restore: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
Python API Usage:
    import app.workspace.code_editor.editor
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import TypeAdapter

from app.core.lib.responses import ErrorCode
from app.workspace.code_editor._common import (
    PROJECT_ROOT,
    CodeEditorError,
    EditorTab,
    resolve_safe_path,
    validate_python_syntax,
    writable_snippet_path,
)
from app.workspace.code_editor._storage import (
    StateStore,
    atomic_create_file,
    atomic_write_batch,
)
from app.workspace.code_editor.requests import (
    SaveAllRequest,
    SaveAsRequest,
    SessionRequest,
)
from app.workspace.code_editor.results import (
    CloseTabResult,
    OpenTabResult,
    SaveAllResult,
    SaveAsResult,
    SavedFile,
    SaveResult,
    Tab,
    WorkspaceInfo,
    WorkspaceState,
    validate_result,
)

logger = logging.getLogger(__name__)


class AppCodeEditor:
    """Manages open document sessions, tabs, and file content persistence."""

    def __init__(self, store: StateStore | None = None) -> None:
        logger.debug("FR-code-editor-editor-init: invoked")
        self._tabs: dict[str, EditorTab] = {}
        self._active_file: str | None = None
        self._store = store or StateStore()
        self._restored = False
        logger.info("FR-code-editor-editor: operation")

    def init_workspace(self) -> WorkspaceInfo:
        """FR-CODEEDITOR-INIT: Initialize workspace state and panel configuration."""
        logger.debug("FR-code-editor-editor-init-workspace: invoked")
        self._restore()
        logger.info("FR-code-editor-editor: operation")
        return {
            "status": "ready",
            "active_file": self._active_file,
            "open_tabs": [tab.to_dict() for tab in self._tabs.values()],
            "recovery_warnings": [
                f"Missing file: {key}; buffer retained for Save As"
                for key in self._tabs
                if not resolve_safe_path(key).is_file()
            ],
            "layout": {
                "navigator_visible": True,
                "split_mode": "single",
                "bottom_panel": "log",
            },
        }

    def open_file_tab(self, file_path: str, *, mode: str = "python") -> OpenTabResult:
        """FR-CODEEDITOR-OPEN-TAB: Open file in tab, reading content from disk."""
        logger.debug("FR-code-editor-editor-open-file-tab: invoked")
        self._restore()
        resolved = resolve_safe_path(file_path)
        rel_path = resolved.relative_to(PROJECT_ROOT).as_posix()

        if rel_path in self._tabs:
            self._active_file = rel_path
            self._persist()
            logger.info("FR-code-editor-editor: operation")
            return {
                "status": "switched",
                "tab": self._tabs[rel_path].to_dict(),
                "active_file": self._active_file,
            }

        if not resolved.exists():
            msg = f"Cannot open file. Path does not exist: {file_path}"
            logger.error("FR-code-editor-editor: operation")
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
        logger.info("FR-code-editor-editor: operation")
        return {
            "status": "opened",
            "tab": tab.to_dict(),
            "active_file": self._active_file,
        }

    def close_file_tab(self, file_path: str, *, force: bool = False) -> CloseTabResult:
        """FR-CODEEDITOR-CLOSE-TAB: Close open tab, checking for unsaved changes."""
        logger.debug("FR-code-editor-editor-close-file-tab: invoked")
        self._restore()
        resolved = resolve_safe_path(file_path)
        rel_path = resolved.relative_to(PROJECT_ROOT).as_posix()

        if rel_path not in self._tabs:
            logger.warning("FR-code-editor-editor: operation")
            return {"status": "not_open", "active_file": self._active_file}

        tab = self._tabs[rel_path]
        if tab.is_dirty and not force:
            logger.warning("FR-code-editor-editor: operation")
            return {
                "status": "unsaved_changes",
                "file_path": rel_path,
                "active_file": self._active_file,
            }

        del self._tabs[rel_path]
        if self._active_file == rel_path:
            self._active_file = next(iter(self._tabs.keys()), None)

        self._persist()
        logger.info("FR-code-editor-editor: operation")
        return {
            "status": "closed",
            "closed_file": rel_path,
            "active_file": self._active_file,
        }

    def save_file(self, file_path: str, content: str) -> SaveResult:
        """FR-CODEEDITOR-SAVE: Save file content to disk and return diagnostics."""
        logger.debug("FR-code-editor-editor-save-file: invoked")
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
        logger.info("FR-code-editor-editor: operation")
        return {
            "status": "saved",
            "file_path": rel_path,
            "bytes_written": len(content.encode("utf-8")),
            "diagnostics": [d.to_dict() for d in diagnostics],
        }

    def save_as(self, source_path: str, target_path: str, content: str) -> SaveAsResult:
        """Save to a new identity; retain a published file if session saving fails."""
        logger.debug("FR-code-editor-save-as: invoked")
        request = SaveAsRequest(
            source_path=source_path, target_path=target_path, content=content
        )
        source = resolve_safe_path(request.source_path)
        target = writable_snippet_path(request.target_path)
        self._restore()
        source_key = next(
            (key for key in self._tabs if resolve_safe_path(key) == source), None
        )
        if source_key is None:
            raise CodeEditorError(
                "Save As requires an open source tab", code=ErrorCode.NOT_FOUND
            )
        raw_target = Path(request.target_path)
        if not raw_target.is_absolute():
            raw_target = PROJECT_ROOT / raw_target
        if (
            target == source
            or target.exists()
            or raw_target.is_symlink()
            or any(resolve_safe_path(key) == target for key in self._tabs)
        ):
            logger.warning("FR-code-editor-save-as: conflict")
            raise CodeEditorError(
                "Save As destination already exists or is open", code=ErrorCode.CONFLICT
            )
        relative = target.relative_to(PROJECT_ROOT).as_posix()
        original = self._tabs[source_key]
        tab = EditorTab(
            file_path=relative,
            title=target.name,
            content=request.content,
            mode=original.mode,
            cursor_position=original.cursor_position.copy(),
        )
        updated = {
            (relative if key == source_key else key): (
                tab if key == source_key else value
            )
            for key, value in self._tabs.items()
        }
        payload = request.content.encode("utf-8")
        diagnostics = (
            validate_python_syntax(request.content) if target.suffix == ".py" else []
        )
        atomic_create_file(target, payload)
        try:
            self._store.write(
                "workspace",
                {
                    "open_tabs": [value.to_dict() for value in updated.values()],
                    "active_file": relative,
                },
            )
        except Exception:
            logger.error("FR-code-editor-save-as: file created; session saving failed")
            raise CodeEditorError(
                "File created; workspace state could not be saved. Original session retained.",
                code=ErrorCode.UNAVAILABLE,
            ) from None
        self._tabs = updated
        self._active_file = relative
        logger.info("FR-code-editor-save-as: completed")
        return {
            "status": "saved_as",
            "source_path": source_key,
            "file_path": relative,
            "tab": tab.to_dict(),
            "active_file": relative,
            "bytes_written": len(payload),
            "diagnostics": [item.to_dict() for item in diagnostics],
        }

    def save_all_files(
        self, files: Sequence[Mapping[str, str]] | None = None
    ) -> SaveAllResult:
        """FR-CODEEDITOR-SAVE-ALL: Atomically save multiple dirty files."""
        logger.debug("FR-code-editor-editor-save-all-files: invoked")
        parsed = SaveAllRequest.model_validate(
            {"files": None if files is None else list(files)}
        )
        self._restore()
        records = (
            [
                {"file_path": item.file_path, "content": item.content}
                for item in parsed.files
            ]
            if parsed.files is not None
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
        saved_records: list[SavedFile] = []
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
        logger.info("FR-code-editor-editor: operation")
        return {
            "status": "saved_all",
            "count": len(saved_records),
            "files": saved_records,
        }

    def sync_session(
        self, tabs: Sequence[Mapping[str, object]], active_file: str | None
    ) -> WorkspaceInfo:
        """FR-CODEEDITOR-SESSION: Persist dirty buffers and the active document."""
        logger.debug("FR-code-editor-editor-sync-session: invoked")
        parsed = SessionRequest.model_validate(
            {"tabs": list(tabs), "active_file": active_file}
        )
        self._restore()
        updated = {}
        for record in parsed.tabs:
            item = {
                "file_path": record.file_path,
                "content": record.content,
                "mode": record.mode,
            }
            path = resolve_safe_path(item["file_path"])
            relative = path.relative_to(PROJECT_ROOT).as_posix()
            if relative in updated:
                raise CodeEditorError("Duplicate session document identity")
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
        self._store.write(
            "workspace",
            {
                "open_tabs": [tab.to_dict() for tab in updated.values()],
                "active_file": active_file,
            },
        )
        self._tabs = updated
        self._active_file = active_file
        return self.init_workspace()

    def _restore(self) -> None:
        if self._restored:
            return
        raw = self._store.read("workspace")
        if raw is None:
            self._restored = True
            return
        state = validate_result(TypeAdapter(WorkspaceState), raw)
        restored = {}
        for item in state["open_tabs"]:
            path = resolve_safe_path(item["file_path"])
            canonical = path.relative_to(PROJECT_ROOT).as_posix()
            if canonical != item["file_path"] or canonical in restored:
                raise CodeEditorError(
                    "Invalid editor stored state", code=ErrorCode.INTERNAL
                )
            tab = EditorTab(**item)
            if not path.is_file():
                tab.is_dirty = True
                logger.warning(
                    "FR-editor-session-recovery: missing file buffer retained"
                )
            restored[canonical] = tab
        if state["active_file"] is not None and state["active_file"] not in restored:
            raise CodeEditorError(
                "Invalid editor stored state", code=ErrorCode.INTERNAL
            )
        self._tabs = restored
        self._active_file = state["active_file"]
        self._restored = True
        logger.info("FR-code-editor-session-restore: completed")

    def _persist(self) -> None:
        self._store.write(
            "workspace",
            {
                "open_tabs": [tab.to_dict() for tab in self._tabs.values()],
                "active_file": self._active_file,
            },
        )

    def reload_disk(self, file_path: str, *, discard_dirty: bool = False) -> Tab:
        """Replace one buffer from disk only with explicit dirty authority."""
        logger.debug("FR-editor-reload: invoked")
        self._restore()
        path = resolve_safe_path(file_path)
        key = path.relative_to(PROJECT_ROOT).as_posix()
        original = self._tabs.get(key)
        if original is None or not path.is_file():
            raise CodeEditorError(
                "Reload requires an open file present on disk", code=ErrorCode.NOT_FOUND
            )
        if original.is_dirty and not discard_dirty:
            logger.warning("FR-editor-reload: dirty confirmation required")
            raise CodeEditorError(
                "Confirm discarding the dirty buffer", code=ErrorCode.CONFLICT
            )
        replacement = EditorTab(
            file_path=key,
            title=path.name,
            content=path.read_text(encoding="utf-8"),
            mode=original.mode,
            cursor_position=original.cursor_position.copy(),
        )
        candidate = {**self._tabs, key: replacement}
        self._store.write(
            "workspace",
            {
                "open_tabs": [t.to_dict() for t in candidate.values()],
                "active_file": key,
            },
        )
        self._tabs = candidate
        self._active_file = key
        logger.info("FR-editor-reload: completed")
        return replacement.to_dict()

    def remap_tabs(self, old_path: str, new_path: str | None) -> None:
        """FR-CODEEDITOR-REMAP: Preserve buffers when paths move or are deleted."""
        logger.debug("FR-code-editor-editor-remap-tabs: invoked")
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
