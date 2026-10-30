"""Restore and gateway failures use isolated temporary host storage."""

import json
import math
from unittest.mock import Mock

import pytest
from app.core.host.persistence import HostPersistence
from app.core.lib.responses import ErrorCode
from app.workspace.code_editor._storage import StateStore
from app.workspace.code_editor.editor import AppCodeEditor
from app.workspace.code_editor.errors import CodeEditorError
from app.workspace.code_editor.indicator_tester import IndicatorTester


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"open_tabs": [{}], "active_file": None},
        {"open_tabs": [], "active_file": "missing.py"},
    ],
)
def test_corrupt_workspace_is_not_published_or_rewritten(payload):
    store = StateStore()
    store.write("workspace", payload)
    editor = AppCodeEditor(store)
    with pytest.raises(CodeEditorError):
        editor.init_workspace()
    assert editor._tabs == {}
    assert editor._restored is False
    assert store.read("workspace") == payload


@pytest.mark.parametrize("payload", ["not JSON", "[]", '{"value": NaN}'])
def test_invalid_stored_json_is_rejected_without_replacement(payload):
    store = StateStore()
    store.gateway.ensure_code_editor_schema()
    store.gateway.create_records(
        "code_editor_state", [{"id": "workspace", "payload": payload}]
    )
    with pytest.raises(CodeEditorError) as rejected:
        store.read("workspace")
    assert rejected.value.category is ErrorCode.INTERNAL
    rows = store.gateway.read_records("code_editor_state", filters={"id": "workspace"})
    assert rows["data"]["records"][0]["payload"] == payload


def test_invalid_outgoing_state_is_rejected_before_host_schema_or_writes():
    gateway = Mock(spec=HostPersistence)
    store = StateStore(gateway)
    with pytest.raises(CodeEditorError):
        store.write("workspace", {"value": math.nan})
    gateway.ensure_code_editor_schema.assert_not_called()
    gateway.transaction.assert_not_called()


@pytest.mark.parametrize(
    "response", [{}, {"success": False}, {"success": True, "data": []}]
)
def test_host_failure_is_categorized_without_raw_details(response):
    gateway = Mock(spec=HostPersistence)
    gateway.ensure_code_editor_schema.return_value = response
    with pytest.raises(CodeEditorError) as rejected:
        StateStore(gateway).read("workspace")
    assert rejected.value.category is ErrorCode.UNAVAILABLE
    assert str(rejected.value) == "Editor persistence unavailable"
    gateway.read_records.assert_not_called()


def test_indicator_config_identity_and_window_are_validated_before_restore():
    store = StateStore()
    tester = IndicatorTester(store)
    config = tester.new_indy_test("SMA")
    store.write("indicator:other", config)
    with pytest.raises(CodeEditorError):
        tester.load_test_config("other")
    assert "other" not in tester._tests
    config["bar_count"] = 0
    store.write("indicator:" + config["test_id"], config)
    restarted = IndicatorTester(store)
    with pytest.raises(CodeEditorError):
        restarted.load_test_config(config["test_id"])
    assert restarted._tests == {}


def test_valid_workspace_and_indicator_documents_roundtrip_through_host():
    store = StateStore()
    assert AppCodeEditor(store).init_workspace()["open_tabs"] == []
    editor = AppCodeEditor(store)
    editor.sync_session([], None)
    assert store.read("workspace") == {"open_tabs": [], "active_file": None}
    tester = IndicatorTester(store)
    config = tester.new_indy_test("MACD")
    tester.save_test_config(config["test_id"], "Review")
    loaded = IndicatorTester(store).load_test_config(config["test_id"])["config"]
    assert loaded["params"] == config["params"]
    assert json.loads(json.dumps(loaded)) == loaded
