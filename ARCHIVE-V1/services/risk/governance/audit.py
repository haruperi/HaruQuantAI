"""Risk audit artifact helpers."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _write_json_artifact(
    directory: str | Path, name: str, payload: dict[str, Any]
) -> str:
    target_dir = Path(directory)
    if target_dir.parts and target_dir.parts[0] == "reports":
        target_dir = Path("app/agentic") / "audit" / target_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return str(path)


def write_risk_audit(component_name: str, payload: dict[str, Any]) -> str:
    """Function write_risk_audit provides risk service behavior."""
    return _write_json_artifact(
        "app/agentic/audit/reports/risk",
        f"{component_name}-{_utc_stamp()}.json",
        payload,
    )
