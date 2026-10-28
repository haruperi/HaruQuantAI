"""Unit tests for CodeEditorImportExport package archiving and extraction."""

from pathlib import Path

import pytest
from app.workspace.code_editor._common import PROJECT_ROOT
from app.workspace.code_editor.import_export import ImportExport


@pytest.fixture
def impexp():
    return ImportExport()


def test_export_inspect_and_import(impexp: ImportExport, tmp_path: Path):
    """Verify exporting snippet files to zip, inspecting, and extracting with overwrite."""
    # Create test source snippet
    sample_rel = "app/include/blocks/indicators/custom/test_export_sample.py"
    sample_abs = PROJECT_ROOT / sample_rel
    sample_abs.parent.mkdir(parents=True, exist_ok=True)
    sample_abs.write_text("# Test export content\n", encoding="utf-8")

    archive_path = tmp_path / "test_package.zip"

    try:
        # 1. Export
        exp_res = impexp.export([sample_rel], archive_path, metadata={"author": "Test"})
        assert exp_res["status"] == "exported"
        assert archive_path.exists()

        # 2. Inspect archive
        preview = impexp.imported_files(archive_path)
        assert len(preview) == 1
        assert preview[0]["filename"] == sample_rel
        assert preview[0]["exists_locally"] is True

        # 3. Import with skip rule
        imp_skip = impexp.overwrite_confirm(archive_path, {sample_rel: "skip"})
        assert imp_skip["skipped_count"] == 1
        assert imp_skip["extracted_count"] == 0

        # 4. Import with rename rule
        imp_rename = impexp.overwrite_confirm(archive_path, {sample_rel: "rename"})
        assert imp_rename["extracted_count"] == 1
        renamed_path = (
            PROJECT_ROOT
            / "app/include/blocks/indicators/custom/test_export_sample_imported.py"
        )
        assert renamed_path.exists()
        renamed_path.unlink()

        # 5. Import with overwrite rule
        imp_ow = impexp.overwrite_confirm(archive_path, {sample_rel: "overwrite"})
        assert imp_ow["extracted_count"] == 1
    finally:
        if sample_abs.exists():
            sample_abs.unlink()
