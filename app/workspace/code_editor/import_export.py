"""Import export editor contracts and workflows.

Description:
    Exports saved Python sources and imports preflighted archives. Host storage
    ownership is unchanged; archive-format compatibility is not expanded.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Preserve typed editor behavior and host ownership.
Key Capabilities:
    - FR-code-editor-import-export: Observe the associated workflow; fixed-label logs
      are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-import-export-export: Observe the associated workflow; fixed-label
      logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-import-export-imported-files: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
    - FR-code-editor-import-export-overwrite-confirm: Observe the associated workflow;
      fixed-label logs are
      verified by the contract logging tests or HTTP integration checks.
Python API Usage:
    import app.workspace.code_editor.import_export
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

from __future__ import annotations

import json
import logging
import zipfile
from collections.abc import Mapping, Sequence
from io import BytesIO
from pathlib import Path

from app.core.lib.errors import JSONValue
from app.workspace.code_editor._common import (
    PROJECT_ROOT,
    CodeEditorError,
    writable_snippet_path,
)
from app.workspace.code_editor._storage import atomic_write_batch
from app.workspace.code_editor.requests import ExportPackRequest, ImportPackRequest
from app.workspace.code_editor.results import (
    ArchiveEntry,
    ExportResult,
    ImportResult,
    NavigatorItem,
    PackageManifest,
)
from app.workspace.code_editor.routes import CodeEditor

logger = logging.getLogger(__name__)

MAX_ARCHIVE_SIZE = 10 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 500
MAX_UNCOMPRESSED_SIZE = 25 * 1024 * 1024


class ImportExport:
    """Handles archiving, export, and conflict-resolved import of extension snippets."""

    def list_exportable(self, filter_text: str = "") -> NavigatorItem:
        """FR-CODEEDITOR-EXPORT-LIST: List user-owned snippets for export."""
        logger.debug("FR-code-editor-import-export: list_exportable invoked")
        return CodeEditor().navigator(ownership="user", filter_text=filter_text)

    def export(
        self,
        file_paths: Sequence[str],
        archive_path: Path | str,
        metadata: Mapping[str, JSONValue] | None = None,
    ) -> ExportResult:
        """FR-CODEEDITOR-EXPORT: Export snippets and manifest into a zip archive."""
        logger.debug("FR-code-editor-import-export-export: invoked")
        ExportPackRequest.model_validate(
            {
                "file_paths": list(file_paths),
                "archive_path": str(archive_path),
                "metadata": None if metadata is None else dict(metadata),
            }
        )
        dest_archive = Path(archive_path).resolve()
        if dest_archive.suffix.lower() not in {".zip", ".sxp"}:
            raise CodeEditorError("Choose a .zip or .sxp archive destination")
        if dest_archive.is_relative_to(PROJECT_ROOT):
            writable_snippet_path(dest_archive)
        sources = [writable_snippet_path(path) for path in file_paths]
        if not sources or any(
            not path.is_file() or path.suffix != ".py" for path in sources
        ):
            raise CodeEditorError("Select existing Python snippet files to export")

        manifest: PackageManifest = {
            "version": "1.0",
            "metadata": dict(metadata or {}),
            "files": [],
        }

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for resolved in sources:
                rel_arc = resolved.relative_to(PROJECT_ROOT).as_posix()
                zf.write(resolved, arcname=rel_arc)
                manifest["files"].append(rel_arc)

            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        atomic_write_batch({dest_archive: buffer.getvalue()})

        logger.info("FR-code-editor-import-export: operation")
        return {
            "status": "exported",
            "archive_path": str(dest_archive),
            "file_count": len(manifest["files"]),
            "files": manifest["files"],
        }

    def imported_files(self, archive_path: Path | str) -> list[ArchiveEntry]:
        """FR-CODEEDITOR-IMPORTED: Preview files inside an archive and identify collisions."""
        logger.debug("FR-code-editor-import-export-imported-files: invoked")
        src_archive = Path(archive_path).resolve()
        if not src_archive.exists():
            raise CodeEditorError(f"Archive not found: {archive_path}")

        records: list[ArchiveEntry] = []
        with zipfile.ZipFile(src_archive, "r") as zf:
            for item in zf.infolist():
                if item.filename == "manifest.json" or item.is_dir():
                    continue
                item_name = Path(item.filename).as_posix()
                dest_file = writable_snippet_path(item_name)
                if dest_file.suffix != ".py":
                    raise CodeEditorError(
                        "Extension packages may contain only Python snippets"
                    )
                records.append(
                    {
                        "filename": item_name,
                        "file_size": item.file_size,
                        "exists_locally": dest_file.exists(),
                    }
                )

        logger.info("FR-code-editor-import-export: operation")
        return records

    def overwrite_confirm(
        self,
        archive_path: Path | str,
        resolution_rules: Mapping[str, str] | None = None,
    ) -> ImportResult:
        """FR-CODEEDITOR-OVERWRITE: Extract files honoring resolution rules (overwrite/skip/rename)."""
        logger.debug("FR-code-editor-import-export-overwrite-confirm: invoked")
        src_archive = Path(archive_path).resolve()
        if not src_archive.exists():
            raise CodeEditorError(f"Archive not found: {archive_path}")

        request = ImportPackRequest.model_validate(
            {
                "archive_path": str(archive_path),
                "resolution_rules": None
                if resolution_rules is None
                else dict(resolution_rules),
            }
        )
        rules = request.resolution_rules or {}
        extracted: list[str] = []
        skipped: list[str] = []

        pending: dict[Path, bytes] = {}
        seen: set[Path] = set()
        with zipfile.ZipFile(src_archive, "r") as zf:
            for item in zf.infolist():
                if item.filename == "manifest.json" or item.is_dir():
                    continue
                item_name = Path(item.filename).as_posix()
                dest_file = writable_snippet_path(item_name)
                if dest_file.suffix != ".py" or dest_file in seen:
                    raise CodeEditorError(
                        "Archive must contain unique Python snippet paths"
                    )
                seen.add(dest_file)
                rule = rules.get(item_name, "overwrite")
                if rule not in {"overwrite", "skip", "rename"}:
                    raise CodeEditorError(f"Unknown conflict rule: {rule}")
                if dest_file.exists():
                    if rule == "skip":
                        skipped.append(item_name)
                        continue
                    if rule == "rename":
                        original = dest_file
                        index = 1
                        while dest_file.exists() or dest_file in pending:
                            suffix = "_imported" if index == 1 else f"_imported_{index}"
                            dest_file = original.with_name(
                                f"{original.stem}{suffix}{original.suffix}"
                            )
                            index += 1
                if dest_file in pending:
                    raise CodeEditorError("Archive destinations collide")
                payload = zf.read(item)
                compile(payload.decode("utf-8"), str(dest_file), "exec")
                pending[dest_file] = payload
        atomic_write_batch(pending)
        extracted = [p.relative_to(PROJECT_ROOT).as_posix() for p in pending]
        compiler = CodeEditor()
        reload_results = [compiler.compile_file(str(path)) for path in pending]

        logger.info("FR-code-editor-import-export: operation")
        return {
            "status": "completed",
            "extracted_count": len(extracted),
            "skipped_count": len(skipped),
            "extracted": extracted,
            "skipped": skipped,
            "reload_results": reload_results,
        }
