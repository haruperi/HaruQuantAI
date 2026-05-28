from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from tools.utils.validators import (
    prepare_ohlcv_data,
    validate_approval_packet,
    validate_artifact_reference,
    validate_blocked_actions,
    validate_data_freshness,
    validate_environment_mode,
    validate_evidence_pack,
    validate_handoff_payload,
    validate_input_schema,
    validate_output_schema,
    validate_registry_entry,
    validate_required_fields,
)


def assert_schema(result: dict) -> None:
    assert set(result) == {"status", "message", "data", "error", "metadata"}
    assert result["metadata"]["tool_name"]
    assert isinstance(result["metadata"]["execution_ms"], float)


def test_validate_required_fields_success():
    result = validate_required_fields(
        payload={"symbol": "EURUSD"}, required_fields=["symbol"], request_id="req-test"
    )
    assert_schema(result)
    assert result["data"]["valid"] is True
    assert result["metadata"]["request_id"] == "req-test"


def test_validate_required_fields_invalid_payload():
    result = validate_required_fields(payload=[], required_fields=["symbol"])  # type: ignore[arg-type]
    assert_schema(result)
    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_validate_input_schema_type_mismatch():
    result = validate_input_schema(
        payload={"bars": "500"},
        schema={"required": ["bars"], "properties": {"bars": {"type": "integer"}}},
    )
    assert_schema(result)
    assert result["data"]["valid"] is False


def test_validate_approval_packet_missing_field():
    result = validate_approval_packet(
        packet={"request_id": "req", "action": "run_backtest"}
    )
    assert_schema(result)
    assert "risk_level" in result["data"]["missing_fields"]


def test_validate_environment_mode_allowed_and_blocked():
    assert validate_environment_mode(mode="paper")["data"]["valid"] is True
    assert (
        validate_environment_mode(mode="live", allowed_modes=["paper"])["data"]["valid"]
        is False
    )


def test_validate_data_freshness():
    now = datetime.now(timezone.utc)
    result = validate_data_freshness(
        observed_at=(now - timedelta(seconds=10)).isoformat(),
        now=now.isoformat(),
        max_age_seconds=30,
    )
    assert_schema(result)
    assert result["data"]["fresh"] is True


def test_validate_artifact_reference(tmp_path: Path):
    root = tmp_path / "artifacts"
    root.mkdir()
    file_path = root / "report.json"
    file_path.write_text("{}", encoding="utf-8")
    result = validate_artifact_reference(
        path=str(file_path), allowed_root=str(root), must_exist=True
    )
    assert_schema(result)
    assert result["data"]["valid"] is True


def test_validate_blocked_actions_detects_intersection():
    result = validate_blocked_actions(
        attempted_actions=["read_data", "place_order"], blocked_actions=["place_order"]
    )
    assert_schema(result)
    assert result["data"]["blocked_attempts"] == ["place_order"]


def test_prepare_ohlcv_data_helper_success_and_errors():
    frame = pd.DataFrame(
        {
            "Open": [1],
            "High": [2],
            "Low": [0.5],
            "Close": [1.5],
            "Volume": ["10"],
        }
    )
    prepared = prepare_ohlcv_data(frame)
    assert prepared["volume"].iloc[0] == 10
    with pytest.raises(TypeError):
        prepare_ohlcv_data([])  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        prepare_ohlcv_data(pd.DataFrame())
    with pytest.raises(ValueError):
        prepare_ohlcv_data(pd.DataFrame({"open": [1]}))


def test_schema_and_payload_validator_edge_paths():
    invalid_required = validate_required_fields(
        payload={"symbol": "EURUSD"}, required_fields=["symbol", ""]
    )
    assert invalid_required["status"] == "error"

    bad_schema = validate_input_schema(payload={}, schema={"required": "symbol"})
    assert bad_schema["data"]["valid"] is False

    bad_properties = validate_output_schema(payload={}, schema={"properties": []})
    assert bad_properties["data"]["valid"] is False

    evidence = validate_evidence_pack(evidence_pack=[])
    handoff = validate_handoff_payload(payload={})
    registry = validate_registry_entry(entry={})
    assert evidence["status"] == "error"
    assert "from_agent" in handoff["data"]["missing_fields"]
    assert "id" in registry["data"]["missing_fields"]


def test_environment_freshness_artifact_and_blocked_invalid_inputs(tmp_path: Path):
    assert validate_environment_mode(mode="")["status"] == "error"
    assert (
        validate_environment_mode(mode="paper", allowed_modes=[1])["status"] == "error"
    )
    assert (
        validate_data_freshness(observed_at="now", max_age_seconds=-1)["status"]
        == "error"
    )
    assert (
        validate_data_freshness(observed_at="not-a-date", max_age_seconds=1)["status"]
        == "error"
    )

    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    root = tmp_path / "root"
    root.mkdir()
    artifact = validate_artifact_reference(
        path=str(outside), allowed_root=str(root), must_exist=True
    )
    assert artifact["data"]["inside_allowed_root"] is False
    assert (
        validate_artifact_reference(path=str(outside), must_exist="yes")["status"]
        == "error"
    )

    blocked = validate_blocked_actions(attempted_actions="read", blocked_actions=[])
    bad_names = validate_blocked_actions(attempted_actions=[""], blocked_actions=[])
    assert blocked["status"] == "error"
    assert bad_names["status"] == "error"
