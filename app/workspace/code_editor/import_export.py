"""CodeEditorImportExport — Snippet Extension Packager and Importer.

Key Capabilities:
- FR-CODEEDITOR-EXPORT: Bundle snippets and metadata into zip packages [ImportExport.export()]
- FR-CODEEDITOR-IMPORTED: Inspect package contents and detect conflicts [ImportExport.imported_files()]
- FR-CODEEDITOR-OVERWRITE: Extract package applying overwrite and skip policies [ImportExport.overwrite_confirm()]
"""

from __future__ import annotations

import json
import zipfile
from collections.abc import Mapping, Sequence
from io import BytesIO
from pathlib import Path
from typing import Any

from app.core.host.logging import get_logger
from app.workspace.code_editor._common import (
    PROJECT_ROOT,
    CodeEditorError,
    writable_snippet_path,
)
from app.workspace.code_editor._storage import atomic_write_batch
from app.workspace.code_editor.routes import CodeEditor

logger = get_logger(__name__)


class ImportExport:
    """Handles archiving, export, and conflict-resolved import of extension snippets."""

    def export(
        self,
        file_paths: Sequence[str],
        archive_path: Path | str,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """FR-CODEEDITOR-EXPORT: Export snippets and manifest into a zip archive."""
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

        manifest: dict[str, Any] = {
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

        logger.info(
            f"Exported {len(manifest['files'])} snippet(s) to archive: {dest_archive.name}"
        )
        return {
            "status": "exported",
            "archive_path": str(dest_archive),
            "file_count": len(manifest["files"]),
            "files": manifest["files"],
        }

    def imported_files(self, archive_path: Path | str) -> list[dict[str, Any]]:
        """FR-CODEEDITOR-IMPORTED: Preview files inside an archive and identify collisions."""
        src_archive = Path(archive_path).resolve()
        if not src_archive.exists():
            raise CodeEditorError(f"Archive not found: {archive_path}")

        records: list[dict[str, Any]] = []
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

        logger.info(
            f"Inspected archive {src_archive.name}: found {len(records)} entry(ies)."
        )
        return records

    def overwrite_confirm(
        self,
        archive_path: Path | str,
        resolution_rules: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """FR-CODEEDITOR-OVERWRITE: Extract files honoring resolution rules (overwrite/skip/rename)."""
        src_archive = Path(archive_path).resolve()
        if not src_archive.exists():
            raise CodeEditorError(f"Archive not found: {archive_path}")

        rules = dict(resolution_rules or {})
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

        logger.info(
            f"Extracted {len(extracted)} file(s), skipped {len(skipped)} from {src_archive.name}."
        )
        return {
            "status": "completed",
            "extracted_count": len(extracted),
            "skipped_count": len(skipped),
            "extracted": extracted,
            "skipped": skipped,
            "reload_results": reload_results,
        }
