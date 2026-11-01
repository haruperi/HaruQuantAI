"""Explicit requirement logs and payload-safe error diagnostics."""

import logging
import math
from unittest.mock import Mock

import pytest
from app.core.host.persistence import HostPersistence
from app.workspace.code_editor._storage import StateStore
from app.workspace.code_editor.errors import CodeEditorError
from app.workspace.code_editor.requests import ExportPackRequest, SaveFileRequest
from app.workspace.code_editor.results import CloseTabResult, validate_result
from app.workspace.code_editor.routes import CodeEditor
from pydantic import TypeAdapter, ValidationError


def test_request_and_result_validation_logs_success_and_rejection(caplog):
    caplog.set_level(logging.DEBUG, logger="app.workspace.code_editor")
    SaveFileRequest(file_path="x.py", content="")
    with pytest.raises(ValidationError):
        ExportPackRequest(
            file_paths=[], archive_path="x.zip", metadata={"private-marker": math.nan}
        )
    validate_result(
        TypeAdapter(CloseTabResult), {"status": "not_open", "active_file": None}
    )
    with pytest.raises(CodeEditorError):
        validate_result(TypeAdapter(CloseTabResult), {"private-marker": True})
    assert "FR-code-editor-validate-request: accepted" in caplog.text
    assert "FR-code-editor-validate-request: rejected JSON" in caplog.text
    assert "FR-code-editor-validate-result: accepted" in caplog.text
    assert "FR-code-editor-validate-result: rejected" in caplog.text
    assert "private-marker" not in caplog.text


def test_search_and_compilation_logs_do_not_copy_source_queries_or_exceptions(caplog):
    caplog.set_level(logging.DEBUG, logger="app.workspace.code_editor")
    editor = CodeEditor()
    assert (
        editor.find_in_files(
            "credential-marker", search_dir="app/extend/absent_contract_test"
        )
        == []
    )
    result = editor.compile_file(
        "app/extend/contract_logging_example.py",
        "raise RuntimeError('credential-marker')",
    )
    assert not result["success"]
    assert result["errors"][0]["message"] == "Runtime import failed"
    assert "FR-code-editor-routes-find-in-files: invoked" in caplog.text
    assert "FR-code-editor-routes-compile-file: invoked" in caplog.text
    assert "credential-marker" not in caplog.text


def test_host_storage_rejection_does_not_log_host_error_details(caplog):
    caplog.set_level(logging.DEBUG, logger="app.workspace.code_editor")
    gateway = Mock(spec=HostPersistence)
    gateway.ensure_code_editor_schema.return_value = {
        "success": False,
        "error": {"message": "credential-marker"},
    }
    with pytest.raises(CodeEditorError):
        StateStore(gateway).read("workspace")
    assert "FR-code-editor-state-gateway: unavailable" in caplog.text
    assert "credential-marker" not in caplog.text
