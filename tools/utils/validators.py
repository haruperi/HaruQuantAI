"""Generic AI-callable validation tools for HaruQuant agents and workflows.

Exported AI Tools:
    - validate_required_fields
    - validate_input_schema
    - validate_output_schema
    - validate_evidence_pack
    - validate_handoff_payload
    - validate_approval_packet
    - validate_environment_mode
    - validate_data_freshness
    - validate_artifact_reference
    - validate_registry_entry
    - validate_blocked_actions
    - validate_strategy_dataframe
    - validate_trade_actions
    - validate_strategy_actions
    - normalize_signal_columns

Internal Helpers:
    - _metadata
    - _success_response
    - _error_response
    - _validate_schema_subset
    - _parse_datetime
    - indicator and strategy validation helpers

Classes:
    None.
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Sequence

import pandas as pd

from tools.utils.logger import logger
from tools.utils.standard import execute_tool_boundary

if TYPE_CHECKING:
    from tools.strategy.contracts import TradeAction

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "utils"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT_ROOT = PROJECT_ROOT / "data" / "simulation_artifacts"
VALID_ENVIRONMENTS = frozenset(
    {"local", "development", "test", "staging", "production"}
)
VALID_TRADING_MODES = frozenset({"research", "backtest", "paper", "live"})
REQUIRED_OHLC_COLUMNS = ("open", "high", "low", "close")
SIGNAL_COLUMN_DEFAULTS: dict[str, Any] = {
    "entry_signal": 0,
    "exit_signal": 0,
    "pending_signal": 0,
    "cancel_pending_signal": 0,
    "pending_signal_2": 0,
    "cancel_pending_signal_2": 0,
    "price": float("nan"),
    "price_2": float("nan"),
    "stop_loss": float("nan"),
    "take_profit": float("nan"),
    "signal_reason": "",
    "setup_id": "",
    "group_id": "",
}
ACTIVATOR_COLUMN_DEFAULTS: dict[str, bool] = {
    "buy_setup_active": False,
    "sell_setup_active": False,
    "buy_add_active": False,
    "sell_add_active": False,
    "buy_exit_active": False,
    "sell_exit_active": False,
    "buy_pyramid_active": False,
    "sell_pyramid_active": False,
    "buy_martingale_active": False,
    "sell_martingale_active": False,
    "buy_decompose_active": False,
    "sell_decompose_active": False,
    "buy_trail_active": False,
    "sell_trail_active": False,
}


def prepare_ohlcv_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize and validate OHLCV-style data.

    Args:
        frame: Input DataFrame containing OHLCV market data.

    Returns:
        pd.DataFrame: Copy with lowercase column names and numeric OHLCV fields.

    Raises:
        TypeError: If frame is not a DataFrame.
        ValueError: If frame is empty or missing OHLC columns.
    """
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame.")
    if frame.empty:
        raise ValueError("frame must not be empty.")

    result = frame.copy()
    result.columns = [str(column).strip().lower() for column in result.columns]
    missing = set(REQUIRED_OHLC_COLUMNS).difference(result.columns)
    if missing:
        raise ValueError(f"frame is missing required OHLC columns: {sorted(missing)}")

    for column in sorted(set(REQUIRED_OHLC_COLUMNS) | {"volume", "spread"}):
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")

    return result


def ensure_dataframe(data: Any) -> pd.DataFrame:
    """Normalize supported market-data input into a copied DataFrame.

    Args:
        data: DataFrame, list of row dictionaries, dictionary of columns, or an
            object with a ``df`` DataFrame attribute.

    Returns:
        Copied DataFrame safe for mutation.

    Raises:
        TypeError: If input cannot be converted to a DataFrame.
        ValueError: If the resulting DataFrame is empty.
    """
    if isinstance(data, pd.DataFrame):
        frame = data.copy()
    elif isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
        frame = pd.DataFrame(data)
    elif isinstance(data, Mapping):
        frame = pd.DataFrame(data)
    elif isinstance(getattr(data, "df", None), pd.DataFrame):
        frame = data.df.copy()
    else:
        raise TypeError("data must be a pandas DataFrame or DataFrame-like records")

    if frame.empty:
        raise ValueError("data must not be empty")
    return frame


def require_columns(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    """Require all columns to exist in a DataFrame."""
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def require_positive_int(value: int, *, name: str) -> None:
    """Require a value to be a positive integer."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be a positive integer")
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")


def require_positive_float(value: float, *, name: str) -> None:
    """Require a value to be a positive int/float."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric")
    if float(value) <= 0:
        raise ValueError(f"{name} must be greater than zero")


def require_known_warmup_policy(policy: str) -> None:
    """Validate the warmup policy used by an indicator."""
    if policy not in {"nan", "fill", "drop"}:
        raise ValueError("warmup_policy must be one of: nan, fill, drop")


def apply_warmup_policy(
    frame: pd.DataFrame,
    columns: str | Iterable[str],
    *,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
) -> pd.DataFrame:
    """Apply a deterministic warmup policy to indicator output columns."""
    require_known_warmup_policy(warmup_policy)
    column_list = [columns] if isinstance(columns, str) else list(columns)

    if warmup_policy == "nan":
        return frame
    if warmup_policy == "fill":
        if fill_value is None:
            raise ValueError("fill_value is required when warmup_policy='fill'")
        frame[column_list] = frame[column_list].fillna(fill_value)
        return frame
    return frame.dropna(subset=column_list)


def assert_dataframe(data: pd.DataFrame, *, min_rows: int = 1) -> None:
    """Validate a non-empty pandas DataFrame."""
    if not isinstance(data, pd.DataFrame):
        raise ValueError("data must be a pandas DataFrame.")
    if len(data) < min_rows:
        raise ValueError(f"data must contain at least {min_rows} row(s).")


def assert_ohlc_dataframe(data: pd.DataFrame, *, min_rows: int = 1) -> None:
    """Validate required OHLC columns for strategy signal generation."""
    assert_dataframe(data, min_rows=min_rows)
    missing = [column for column in REQUIRED_OHLC_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(f"data is missing required OHLC columns: {missing}.")


def ensure_signal_columns(
    data: pd.DataFrame,
    *,
    include_activators: bool = False,
    include_compat_columns: bool = True,
) -> pd.DataFrame:
    """Return a copy of data with canonical strategy signal columns."""
    assert_dataframe(data)
    out = data.copy(deep=True)
    defaults: dict[str, Any] = dict(SIGNAL_COLUMN_DEFAULTS)
    if include_activators:
        defaults.update(ACTIVATOR_COLUMN_DEFAULTS)
    if include_compat_columns:
        defaults.update({"sl": 0.0, "tp": 0.0})
    for column, default in defaults.items():
        if column not in out.columns:
            out[column] = default
    return out


def ensure_no_signal_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of data with neutral strategy signal columns."""
    out = ensure_signal_columns(data, include_activators=True)
    for column in (
        "entry_signal",
        "exit_signal",
        "pending_signal",
        "cancel_pending_signal",
        "pending_signal_2",
        "cancel_pending_signal_2",
    ):
        out[column] = 0
    for column in ("price", "price_2", "stop_loss", "take_profit"):
        out[column] = float("nan")
    for column in ("signal_reason", "setup_id", "group_id"):
        out[column] = ""
    for column in ACTIVATOR_COLUMN_DEFAULTS:
        out[column] = False
    out["sl"] = 0.0
    out["tp"] = 0.0
    return out


def serialize_dataframe(data: pd.DataFrame) -> dict[str, Any]:
    """Serialize a DataFrame to a JSON-friendly split-orient dictionary."""
    out = data.copy()
    out.index = out.index.map(str)
    return {
        "columns": list(out.columns),
        "index": list(out.index),
        "rows": out.where(pd.notna(out), None).to_dict(orient="records"),
    }


def validate_trade_action_object(
    action: "TradeAction | dict[str, Any]",
) -> dict[str, Any]:
    """Validate a TradeAction or action dictionary and return a serializable dict."""
    from tools.strategy.contracts import TradeAction

    row = action.to_dict() if isinstance(action, TradeAction) else dict(action)
    action_type = str(row.get("action_type", "")).upper()
    if action_type not in {
        "OPEN",
        "CLOSE",
        "REDUCE",
        "MODIFY_SL",
        "MODIFY_TP",
        "MOVE_TO_BREAKEVEN",
        "HOLD",
    }:
        raise ValueError(f"Unsupported action_type: {action_type!r}.")
    symbol = str(row.get("symbol", "") or "").strip()
    if not symbol:
        raise ValueError("Trade action symbol is required.")
    side = row.get("side")
    if action_type in {"OPEN", "CLOSE", "REDUCE"} and side not in {"BUY", "SELL"}:
        raise ValueError(f"Action {action_type} requires side BUY or SELL.")
    volume = row.get("volume")
    if action_type in {"OPEN", "CLOSE", "REDUCE"}:
        if volume is None or float(volume) <= 0:
            raise ValueError(f"Action {action_type} requires positive volume.")
    if action_type in {
        "CLOSE",
        "REDUCE",
        "MODIFY_SL",
        "MODIFY_TP",
        "MOVE_TO_BREAKEVEN",
    }:
        if not row.get("ticket"):
            raise ValueError(f"Action {action_type} requires a ticket.")
    return row


def _metadata(
    tool_name: str, request_id: str | None, execution_ms: float
) -> dict[str, Any]:
    return {
        "tool_name": tool_name,
        "tool_version": TOOL_VERSION,
        "tool_category": TOOL_CATEGORY,
        "tool_risk_level": TOOL_RISK_LEVEL,
        "request_id": request_id,
        "execution_ms": execution_ms,
        "read_only": READ_ONLY,
        "writes_file": WRITES_FILE,
        "modifies_database": MODIFIES_DATABASE,
        "places_trade": PLACES_TRADE,
        "requires_network": REQUIRES_NETWORK,
    }


def _success_response(
    *,
    tool_name: str,
    message: str,
    data: Any,
    request_id: str | None,
    started_at: float,
) -> dict[str, Any]:
    execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
    return {
        "status": "success",
        "message": message,
        "data": data,
        "error": None,
        "metadata": _metadata(tool_name, request_id, execution_ms),
    }


def _error_response(
    *,
    tool_name: str,
    message: str,
    code: str,
    details: str,
    request_id: str | None,
    started_at: float,
) -> dict[str, Any]:
    execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
    return {
        "status": "error",
        "message": message,
        "data": None,
        "error": {"code": code, "details": details},
        "metadata": _metadata(tool_name, request_id, execution_ms),
    }


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _validate_schema_subset(
    payload: Mapping[str, Any], schema: Mapping[str, Any]
) -> list[str]:
    errors = []
    required = schema.get("required", [])
    if required is not None and not isinstance(required, Sequence):
        return ["schema.required must be a sequence."]
    for field in required or []:
        if not isinstance(field, str):
            errors.append("schema.required entries must be strings.")
            continue
        if field not in payload or _is_empty(payload.get(field)):
            errors.append(f"{field} is required.")
    properties = schema.get("properties", {})
    if properties is not None and not isinstance(properties, Mapping):
        return errors + ["schema.properties must be a mapping."]
    for field, spec in (properties or {}).items():
        if not isinstance(spec, Mapping) or field not in payload or "type" not in spec:
            continue
        expected = spec["type"]
        value = payload[field]
        ok = (
            (expected == "string" and isinstance(value, str))
            or (
                expected == "number"
                and isinstance(value, (int, float))
                and not isinstance(value, bool)
            )
            or (
                expected == "integer"
                and isinstance(value, int)
                and not isinstance(value, bool)
            )
            or (expected == "boolean" and isinstance(value, bool))
            or (expected == "object" and isinstance(value, Mapping))
            or (expected == "array" and isinstance(value, list))
        )
        if not ok:
            errors.append(f"{field} must be {expected}.")
    return errors


def _parse_datetime(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty ISO-8601 string.")
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    return (
        parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    ).astimezone(timezone.utc)


def validate_required_fields(
    *,
    payload: Any,
    required_fields: Any,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Validate that a payload contains required non-empty fields."""
    tool_name = "validate_required_fields"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)
    if not isinstance(payload, dict):
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="payload must be a dictionary.",
            request_id=request_id,
            started_at=started_at,
        )
    if not isinstance(required_fields, list) or not all(
        isinstance(i, str) and i.strip() for i in required_fields
    ):
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="required_fields must be a list of non-empty strings.",
            request_id=request_id,
            started_at=started_at,
        )
    missing = [
        f for f in required_fields if f not in payload or _is_empty(payload.get(f))
    ]
    return _success_response(
        tool_name=tool_name,
        message="Required-field validation completed.",
        data={"valid": not missing, "missing_fields": missing},
        request_id=request_id,
        started_at=started_at,
    )


def _schema_tool(
    tool_name: str, payload: Any, schema: Any, request_id: str | None
) -> dict[str, Any]:
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)
    if not isinstance(payload, dict) or not isinstance(schema, dict):
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="payload and schema must be dictionaries.",
            request_id=request_id,
            started_at=started_at,
        )
    errors = _validate_schema_subset(payload, schema)
    return _success_response(
        tool_name=tool_name,
        message="Schema validation completed.",
        data={
            "valid": not errors,
            "errors": errors,
            "checked_fields": sorted((schema.get("properties") or {}).keys()),
        },
        request_id=request_id,
        started_at=started_at,
    )


def validate_input_schema(
    *, payload: Any, schema: Any, request_id: str | None = None
) -> dict[str, Any]:
    """Validate an incoming request payload against a small JSON-schema subset."""
    return _schema_tool("validate_input_schema", payload, schema, request_id)


def validate_output_schema(
    *, payload: Any, schema: Any, request_id: str | None = None
) -> dict[str, Any]:
    """Validate an outgoing response payload against a small JSON-schema subset."""
    return _schema_tool("validate_output_schema", payload, schema, request_id)


def _required_payload_tool(
    tool_name: str,
    payload: Any,
    fields: list[str],
    payload_name: str,
    request_id: str | None,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)
    if not isinstance(payload, dict):
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details=f"{payload_name} must be a dictionary.",
            request_id=request_id,
            started_at=started_at,
        )
    missing = [f for f in fields if f not in payload or _is_empty(payload.get(f))]
    return _success_response(
        tool_name=tool_name,
        message="Payload validation completed.",
        data={"valid": not missing, "missing_fields": missing},
        request_id=request_id,
        started_at=started_at,
    )


def validate_evidence_pack(
    *,
    evidence_pack: Any,
    required_sections: Any = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Validate evidence pack completeness."""
    return _required_payload_tool(
        "validate_evidence_pack",
        evidence_pack,
        required_sections or ["hypothesis", "evidence", "validation"],
        "evidence_pack",
        request_id,
    )


def validate_handoff_payload(
    *, payload: Any, request_id: str | None = None
) -> dict[str, Any]:
    """Validate agent-to-agent handoff payload structure."""
    return _required_payload_tool(
        "validate_handoff_payload",
        payload,
        ["from_agent", "to_agent", "handoff_type", "payload"],
        "payload",
        request_id,
    )


def validate_approval_packet(
    *, packet: Any, request_id: str | None = None
) -> dict[str, Any]:
    """Validate an approval request packet."""
    return _required_payload_tool(
        "validate_approval_packet",
        packet,
        ["request_id", "action", "risk_level", "requested_by", "evidence"],
        "packet",
        request_id,
    )


def validate_registry_entry(
    *,
    entry: Any,
    required_fields: Any = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Validate a registry entry."""
    return _required_payload_tool(
        "validate_registry_entry",
        entry,
        required_fields or ["id", "name", "status"],
        "entry",
        request_id,
    )


def validate_environment_mode(
    *, mode: Any, allowed_modes: Any = None, request_id: str | None = None
) -> dict[str, Any]:
    """Validate a runtime environment or trading mode."""
    tool_name = "validate_environment_mode"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)
    if not isinstance(mode, str) or not mode.strip():
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="mode must be a non-empty string.",
            request_id=request_id,
            started_at=started_at,
        )
    allowed = set(allowed_modes or sorted(VALID_ENVIRONMENTS | VALID_TRADING_MODES))
    if not all(isinstance(i, str) and i.strip() for i in allowed):
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="allowed_modes must contain only non-empty strings.",
            request_id=request_id,
            started_at=started_at,
        )
    ok = mode.strip().lower() in {i.lower() for i in allowed}
    return _success_response(
        tool_name=tool_name,
        message="Environment-mode validation completed.",
        data={
            "valid": ok,
            "mode": mode.strip().lower(),
            "allowed_modes": sorted(allowed),
        },
        request_id=request_id,
        started_at=started_at,
    )


def validate_data_freshness(
    *,
    observed_at: Any,
    max_age_seconds: Any,
    now: Any = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Validate that timestamped data is not stale."""
    tool_name = "validate_data_freshness"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)
    if (
        isinstance(max_age_seconds, bool)
        or not isinstance(max_age_seconds, int)
        or max_age_seconds < 0
    ):
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="max_age_seconds must be a non-negative integer.",
            request_id=request_id,
            started_at=started_at,
        )
    try:
        observed = _parse_datetime(observed_at, "observed_at")
        current = _parse_datetime(now, "now") if now else datetime.now(timezone.utc)
    except ValueError as e:
        return _error_response(
            tool_name=tool_name,
            message="Invalid timestamp input.",
            code="INVALID_INPUT",
            details=str(e),
            request_id=request_id,
            started_at=started_at,
        )
    age = max((current - observed).total_seconds(), 0.0)
    return _success_response(
        tool_name=tool_name,
        message="Data freshness validation completed.",
        data={
            "fresh": age <= max_age_seconds,
            "age_seconds": round(age, 3),
            "max_age_seconds": max_age_seconds,
            "observed_at": observed.isoformat(),
            "checked_at": current.isoformat(),
        },
        request_id=request_id,
        started_at=started_at,
    )


def validate_artifact_reference(
    *,
    path: Any,
    must_exist: Any = True,
    allowed_root: Any = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Validate an artifact path and optional existence requirement."""
    tool_name = "validate_artifact_reference"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)
    if not isinstance(path, str) or not path.strip():
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="path must be a non-empty string.",
            request_id=request_id,
            started_at=started_at,
        )
    if not isinstance(must_exist, bool):
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="must_exist must be a boolean.",
            request_id=request_id,
            started_at=started_at,
        )
    root = (
        Path(allowed_root).resolve()
        if allowed_root
        else DEFAULT_ARTIFACT_ROOT.resolve()
    )
    resolved = Path(path).expanduser().resolve()
    inside = root == resolved or root in resolved.parents
    exists = resolved.exists()
    errors = []
    if not inside:
        errors.append("artifact path must be inside the allowed artifact root.")
    if must_exist and not exists:
        errors.append("artifact does not exist.")
    return _success_response(
        tool_name=tool_name,
        message="Artifact reference validation completed.",
        data={
            "valid": inside and (exists or not must_exist),
            "path": str(resolved),
            "allowed_root": str(root),
            "exists": exists,
            "inside_allowed_root": inside,
            "errors": errors,
        },
        request_id=request_id,
        started_at=started_at,
    )


def validate_blocked_actions(
    *,
    attempted_actions: Any,
    blocked_actions: Any,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Validate that no forbidden actions were attempted."""
    tool_name = "validate_blocked_actions"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)
    if not isinstance(attempted_actions, list) or not isinstance(blocked_actions, list):
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="attempted_actions and blocked_actions must be lists.",
            request_id=request_id,
            started_at=started_at,
        )
    if not all(
        isinstance(i, str) and i.strip() for i in attempted_actions + blocked_actions
    ):
        return _error_response(
            tool_name=tool_name,
            message="Invalid input.",
            code="INVALID_INPUT",
            details="all actions must be non-empty strings.",
            request_id=request_id,
            started_at=started_at,
        )
    blocked = sorted(
        {i.strip() for i in attempted_actions} & {i.strip() for i in blocked_actions}
    )
    return _success_response(
        tool_name=tool_name,
        message="Blocked-action validation completed.",
        data={"valid": not blocked, "blocked_attempts": blocked},
        request_id=request_id,
        started_at=started_at,
    )


def validate_strategy_dataframe(
    data: pd.DataFrame,
    *,
    min_rows: int = 1,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Validate that market data can be consumed by a strategy.

    Use this AI tool before running a vectorized strategy over OHLC data.
    It checks the DataFrame type, minimum row count, and required OHLC columns.
    """

    def operation() -> dict[str, Any]:
        assert_ohlc_dataframe(data, min_rows=min_rows)
        return {"rows": len(data), "columns": list(data.columns), "valid": True}

    return execute_tool_boundary(
        tool_name="validate_strategy_dataframe",
        request_id=request_id,
        operation=operation,
        success_message="Strategy DataFrame is valid.",
    )


def normalize_signal_columns(
    data: pd.DataFrame,
    *,
    include_activators: bool = False,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Add canonical signal columns to a DataFrame and return serialized data.

    Use this AI tool when an agent or workflow needs data normalized to the
    HaruQuant strategy signal schema before backtesting or validation.
    """

    def operation() -> dict[str, Any]:
        normalized = ensure_signal_columns(data, include_activators=include_activators)
        return serialize_dataframe(normalized)

    return execute_tool_boundary(
        tool_name="normalize_signal_columns",
        request_id=request_id,
        operation=operation,
        success_message="Signal columns normalized.",
    )


def validate_trade_actions(
    actions: "list[TradeAction | dict[str, Any]]",
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Validate proposed stateful strategy TradeAction objects.

    Use this AI tool after a stateful strategy proposes actions and before risk
    or execution layers consume those actions. This tool does not execute trades.
    """
    return _validate_trade_action_payloads(
        actions,
        tool_name="validate_trade_actions",
        success_message="Trade actions are valid.",
        request_id=request_id,
    )


def validate_strategy_actions(
    actions: "list[TradeAction | dict[str, Any]]",
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Validate stateful strategy action payloads before risk/execution handoff.

    Use this AI tool when a stateful strategy produces action dictionaries.
    The tool validates shape and safety prerequisites but never executes trades.
    """
    return _validate_trade_action_payloads(
        actions,
        tool_name="validate_strategy_actions",
        success_message="Strategy actions are valid.",
        request_id=request_id,
    )


def _validate_trade_action_payloads(
    actions: "list[TradeAction | dict[str, Any]]",
    *,
    tool_name: str,
    success_message: str,
    request_id: str | None,
) -> dict[str, Any]:
    """Validate trade/action payloads behind public action validation tools."""

    def operation() -> dict[str, Any]:
        if not isinstance(actions, list):
            raise ValueError("actions must be a list.")
        validated = [validate_trade_action_object(action) for action in actions]
        return {"valid": True, "count": len(validated), "actions": validated}

    return execute_tool_boundary(
        tool_name=tool_name,
        request_id=request_id,
        operation=operation,
        success_message=success_message,
    )


__all__ = [
    "ACTIVATOR_COLUMN_DEFAULTS",
    "REQUIRED_OHLC_COLUMNS",
    "SIGNAL_COLUMN_DEFAULTS",
    "apply_warmup_policy",
    "assert_dataframe",
    "assert_ohlc_dataframe",
    "ensure_dataframe",
    "ensure_no_signal_columns",
    "ensure_signal_columns",
    "prepare_ohlcv_data",
    "require_columns",
    "require_known_warmup_policy",
    "require_positive_float",
    "require_positive_int",
    "serialize_dataframe",
    "validate_approval_packet",
    "validate_artifact_reference",
    "validate_blocked_actions",
    "validate_data_freshness",
    "validate_environment_mode",
    "validate_evidence_pack",
    "validate_handoff_payload",
    "validate_input_schema",
    "validate_output_schema",
    "validate_registry_entry",
    "validate_required_fields",
    "validate_strategy_actions",
    "validate_strategy_dataframe",
    "validate_trade_action_object",
    "validate_trade_actions",
]
