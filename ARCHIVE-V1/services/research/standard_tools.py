"""Standardized agent-facing research tools.

Purpose:
    Standardized agent-facing research tools.

Classes:
    None.

Functions:
    _result: Support internal result processing.
    _start: Support internal start processing.
    _frame: Support internal frame processing.
    _records: Support internal records processing.
    _numeric_series: Support internal numeric series processing.
    _ohlc: Support internal ohlc processing.
    _simple_fetch: Support internal simple fetch processing.
    fetch_forexfactory_news: Run fetch forexfactory news processing.
    fetch_forexfactory_calendar: Run fetch forexfactory calendar processing.
    fetch_forexfactory_sentiment: Run fetch forexfactory sentiment processing.
    fetch_forexfactory_instrument_page: Run fetch forexfactory instrument page processing.
    parse_news_items: Run parse news items processing.
    parse_calendar_events: Run parse calendar events processing.
    parse_sentiment_snapshot: Run parse sentiment snapshot processing.
    filter_events_by_symbol: Run filter events by symbol processing.
    classify_news_impact: Run classify news impact processing.
    create_news_blackout_windows: Run create news blackout windows processing.
    calculate_returns: Run calculate returns processing.
    calculate_volatility: Run calculate volatility processing.
    calculate_atr: Run calculate atr processing.
    calculate_adr: Run calculate adr processing.
    calculate_spread_statistics: Run calculate spread statistics processing.
    calculate_session_statistics: Run calculate session statistics processing.
    calculate_seasonality_statistics: Run calculate seasonality statistics processing.
    calculate_regime_features: Run calculate regime features processing.
    calculate_correlation_matrix: Run calculate correlation matrix processing.
    detect_trend_strength: Run detect trend strength processing.
    detect_market_regime: Run detect market regime processing.
    detect_mean_reversion_conditions: Run detect mean reversion conditions processing.
    detect_breakout_conditions: Run detect breakout conditions processing.
    generate_research_hypothesis: Run generate research hypothesis processing.
    score_research_hypothesis: Run score research hypothesis processing.
    check_sample_size: Run check sample size processing.
    check_data_snooping_risk: Run check data snooping risk processing.
    check_lookahead_bias_risk: Run check lookahead bias risk processing.
    check_hypothesis_testability: Run check hypothesis testability processing.
    check_contradictory_evidence: Run check contradictory evidence processing.
    build_research_evidence_pack: Run build research evidence pack processing.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

import numpy as np
import pandas as pd
from app.services.utils.standard import ToolStandardSpec, standard_tool_response

EnvironmentName = Literal["local", "development", "test", "paper", "live"]


def _result(
    *,
    status: str,
    tool_name: str,
    started_at: str,
    request_id: str,
    tool_call_id: str,
    agent_name: str | None,
    environment: str,
    data: dict[str, Any] | None,
    errors: list[str],
    warnings: list[str] | None = None,
    risk_level: str = "low",
) -> dict[str, Any]:
    """Support internal result processing."""
    _ = tool_call_id, agent_name, environment, warnings, started_at
    normalized_status = "success" if status == "success" and not errors else "error"
    return standard_tool_response(
        spec=ToolStandardSpec(
            tool_name=tool_name,
            tool_category="research",
            tool_risk_level=risk_level,
            read_only=True,
        ),
        status=normalized_status,
        message=(
            "Research tool executed successfully."
            if normalized_status == "success"
            else "Research tool execution failed."
        ),
        data=data,
        error=None
        if normalized_status == "success"
        else {
            "code": "TOOL_EXECUTION_FAILED",
            "details": "; ".join(errors) or "Research tool failed.",
        },
        request_id=request_id,
        execution_ms=0.0,
    )


def _start(request_id: str | None) -> tuple[str, str, str]:
    """Support internal start processing."""
    return str(uuid4()), datetime.now(UTC).isoformat(), request_id or str(uuid4())


def _frame(
    records: list[dict[str, Any]] | None = None, data: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Support internal frame processing."""
    if data is not None:
        frame = data.copy()
    elif records is not None:
        frame = pd.DataFrame(records)
    else:
        raise ValueError("records or data is required")
    if not isinstance(frame.index, pd.DatetimeIndex):
        for column in ("timestamp", "time", "datetime", "date"):
            if column in frame.columns:
                frame[column] = pd.to_datetime(frame[column])
                frame = frame.set_index(column)
                break
    return frame.sort_index()


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Support internal records processing."""
    raw = frame.reset_index().to_json(orient="records", date_format="iso")
    import json

    parsed = json.loads(raw)
    return parsed if isinstance(parsed, list) else []


def _numeric_series(values: list[float] | pd.Series) -> pd.Series:
    """Support internal numeric series processing."""
    return pd.to_numeric(pd.Series(values), errors="coerce").dropna().astype(float)


def _ohlc(frame: pd.DataFrame) -> pd.DataFrame:
    """Support internal ohlc processing."""
    out = frame.copy()
    out.columns = [str(column).lower() for column in out.columns]
    required = {"open", "high", "low", "close"}
    missing = sorted(required - set(out.columns))
    if missing:
        raise ValueError(f"missing required OHLC columns: {missing}")
    return out


def _simple_fetch(
    *,
    tool_name: str,
    url: str,
    request_id: str | None,
    agent_name: str | None,
    environment: EnvironmentName,
) -> dict[str, Any]:
    """Support internal simple fetch processing."""
    tool_call_id, started_at, request_id = _start(request_id)
    try:
        import requests

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return _result(
            status="success",
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            tool_call_id=tool_call_id,
            agent_name=agent_name,
            environment=environment,
            data={
                "url": url,
                "status_code": response.status_code,
                "text": response.text,
            },
            errors=[],
        )
    except Exception as exc:
        return _result(
            status="failed",
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            tool_call_id=tool_call_id,
            agent_name=agent_name,
            environment=environment,
            data=None,
            errors=[str(exc)],
        )


def fetch_forexfactory_news(
    *,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Pull the ForexFactory news feed.

    Purpose:
        Pull the ForexFactory news feed.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        Performs one external HTTP GET.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    return _simple_fetch(
        tool_name="fetch_forexfactory_news",
        url="https://www.forexfactory.com/news",
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )


def fetch_forexfactory_calendar(
    *,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Pull the ForexFactory economic calendar.

    Purpose:
        Pull the ForexFactory economic calendar.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        Performs one external HTTP GET.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    return _simple_fetch(
        tool_name="fetch_forexfactory_calendar",
        url="https://www.forexfactory.com/calendar",
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )


def fetch_forexfactory_sentiment(
    *,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Pull the ForexFactory sentiment page.

    Purpose:
        Pull the ForexFactory sentiment page.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        Performs one external HTTP GET.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    return _simple_fetch(
        tool_name="fetch_forexfactory_sentiment",
        url="https://www.forexfactory.com/trades",
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )


def fetch_forexfactory_instrument_page(
    *,
    symbol: str,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Pull a symbol-specific ForexFactory page.

    Purpose:
        Pull a symbol-specific ForexFactory page.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        Performs one external HTTP GET.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    if not symbol:
        tool_call_id, started_at, request_id = _start(request_id)
        return _result(
            status="rejected",
            tool_name="fetch_forexfactory_instrument_page",
            started_at=started_at,
            request_id=request_id,
            tool_call_id=tool_call_id,
            agent_name=agent_name,
            environment=environment,
            data=None,
            errors=["symbol is required"],
        )
    return _simple_fetch(
        tool_name="fetch_forexfactory_instrument_page",
        url=f"https://www.forexfactory.com/markets/{symbol.lower()}",
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )


def parse_news_items(
    *,
    raw_items: list[dict[str, Any]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Normalize raw news items.

    Purpose:
        Normalize raw news items.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    items = [
        {
            "title": str(item.get("title", "")).strip(),
            "published_at": item.get("published_at") or item.get("time"),
            "symbols": item.get("symbols", []),
            "source": item.get("source", "forexfactory"),
            "url": item.get("url"),
        }
        for item in raw_items
    ]
    return _result(
        status="success",
        tool_name="parse_news_items",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"items": items, "count": len(items)},
        errors=[],
    )


def parse_calendar_events(
    *,
    raw_events: list[dict[str, Any]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Normalize economic calendar events.

    Purpose:
        Normalize economic calendar events.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    events = [
        {
            "event_id": str(event.get("event_id") or event.get("id") or uuid4()),
            "currency": str(event.get("currency", "")).upper(),
            "title": str(event.get("title") or event.get("event") or "").strip(),
            "impact": str(event.get("impact", "unknown")).lower(),
            "event_time": event.get("event_time") or event.get("time"),
            "actual": event.get("actual"),
            "forecast": event.get("forecast"),
            "previous": event.get("previous"),
        }
        for event in raw_events
    ]
    return _result(
        status="success",
        tool_name="parse_calendar_events",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"events": events, "count": len(events)},
        errors=[],
    )


def parse_sentiment_snapshot(
    *,
    raw_snapshot: dict[str, Any],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Normalize sentiment positioning.

    Purpose:
        Normalize sentiment positioning.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    long_pct = float(raw_snapshot.get("long_pct", raw_snapshot.get("long", 0.0)) or 0.0)
    short_pct = float(
        raw_snapshot.get("short_pct", raw_snapshot.get("short", 0.0)) or 0.0
    )
    total = long_pct + short_pct
    if total > 0 and total != 100:
        long_pct = long_pct / total * 100
        short_pct = short_pct / total * 100
    data = {
        "symbol": raw_snapshot.get("symbol"),
        "long_pct": long_pct,
        "short_pct": short_pct,
        "sample_size": raw_snapshot.get("sample_size"),
    }
    return _result(
        status="success",
        tool_name="parse_sentiment_snapshot",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data=data,
        errors=[],
    )


def filter_events_by_symbol(
    *,
    events: list[dict[str, Any]],
    symbol: str,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Filter calendar events by symbol currencies.

    Purpose:
        Filter calendar events by symbol currencies.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    currencies = (
        {symbol[:3].upper(), symbol[3:6].upper()}
        if len(symbol) >= 6
        else {symbol.upper()}
    )
    filtered = [
        event
        for event in events
        if str(event.get("currency", "")).upper() in currencies
    ]
    return _result(
        status="success",
        tool_name="filter_events_by_symbol",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"symbol": symbol.upper(), "events": filtered, "count": len(filtered)},
        errors=[],
    )


def classify_news_impact(
    *,
    event: dict[str, Any],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Classify economic news impact.

    Purpose:
        Classify economic news impact.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    text = f"{event.get('impact', '')} {event.get('title', '')}".lower()
    high_terms = {"high", "rate decision", "cpi", "nfp", "fomc", "employment"}
    medium_terms = {"medium", "pmi", "retail sales", "gdp", "inflation"}
    impact = (
        "high"
        if any(term in text for term in high_terms)
        else "medium"
        if any(term in text for term in medium_terms)
        else "low"
    )
    return _result(
        status="success",
        tool_name="classify_news_impact",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"impact": impact, "event": event},
        errors=[],
    )


def create_news_blackout_windows(
    *,
    events: list[dict[str, Any]],
    minutes_before: int = 30,
    minutes_after: int = 30,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Create no-trade windows around news events.

    Purpose:
        Create no-trade windows around news events.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    if minutes_before < 0 or minutes_after < 0:
        return _result(
            status="rejected",
            tool_name="create_news_blackout_windows",
            started_at=started_at,
            request_id=request_id,
            tool_call_id=tool_call_id,
            agent_name=agent_name,
            environment=environment,
            data=None,
            errors=["minutes_before and minutes_after must be non-negative"],
        )
    windows = []
    for event in events:
        raw_time = event.get("event_time") or event.get("time")
        if not raw_time:
            continue
        center = pd.Timestamp(raw_time)
        windows.append(
            {
                "event_id": event.get("event_id"),
                "start": (center - timedelta(minutes=minutes_before)).isoformat(),
                "end": (center + timedelta(minutes=minutes_after)).isoformat(),
                "impact": event.get("impact"),
            }
        )
    return _result(
        status="success",
        tool_name="create_news_blackout_windows",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"windows": windows, "count": len(windows)},
        errors=[],
    )


def calculate_returns(
    *,
    prices: list[float] | None = None,
    records: list[dict[str, Any]] | None = None,
    column: str = "close",
    log: bool = False,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Calculate price returns.

    Purpose:
        Calculate price returns.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    try:
        series = (
            _numeric_series(prices)
            if prices is not None
            else pd.to_numeric(
                _frame(records=records)[column], errors="coerce"
            ).dropna()
        )
        returns = np.log(series / series.shift(1)) if log else series.pct_change()
        frame = pd.DataFrame({"return": returns.dropna()})
        return _result(
            status="success",
            tool_name="calculate_returns",
            started_at=started_at,
            request_id=request_id,
            tool_call_id=tool_call_id,
            agent_name=agent_name,
            environment=environment,
            data={"rows": len(frame), "returns": _records(frame)},
            errors=[],
        )
    except Exception as exc:
        return _result(
            status="rejected",
            tool_name="calculate_returns",
            started_at=started_at,
            request_id=request_id,
            tool_call_id=tool_call_id,
            agent_name=agent_name,
            environment=environment,
            data=None,
            errors=[str(exc)],
        )


def calculate_volatility(
    *,
    returns: list[float],
    window: int = 20,
    annualization_factor: float = 252.0,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Calculate rolling annualized volatility.

    Purpose:
        Calculate rolling annualized volatility.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    if window <= 1:
        return _result(
            status="rejected",
            tool_name="calculate_volatility",
            started_at=started_at,
            request_id=request_id,
            tool_call_id=tool_call_id,
            agent_name=agent_name,
            environment=environment,
            data=None,
            errors=["window must be greater than 1"],
        )
    series = _numeric_series(returns)
    vol = series.rolling(window).std() * np.sqrt(annualization_factor)
    return _result(
        status="success",
        tool_name="calculate_volatility",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"window": window, "volatility": vol.dropna().tolist()},
        errors=[],
    )


def calculate_atr(
    *,
    records: list[dict[str, Any]],
    period: int = 14,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Calculate Average True Range.

    Purpose:
        Calculate Average True Range.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    try:
        frame = _ohlc(_frame(records=records))
        prev_close = frame["close"].shift(1)
        tr = pd.concat(
            [
                (frame["high"] - frame["low"]),
                (frame["high"] - prev_close).abs(),
                (frame["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
        return _result(
            status="success",
            tool_name="calculate_atr",
            started_at=started_at,
            request_id=request_id,
            tool_call_id=tool_call_id,
            agent_name=agent_name,
            environment=environment,
            data={
                "period": period,
                "atr": _records(pd.DataFrame({"atr": atr.dropna()})),
            },
            errors=[],
        )
    except Exception as exc:
        return _result(
            status="rejected",
            tool_name="calculate_atr",
            started_at=started_at,
            request_id=request_id,
            tool_call_id=tool_call_id,
            agent_name=agent_name,
            environment=environment,
            data=None,
            errors=[str(exc)],
        )


def calculate_adr(
    *,
    records: list[dict[str, Any]],
    period: int = 10,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Calculate Average Daily Range.

    Purpose:
        Calculate Average Daily Range.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    try:
        frame = _ohlc(_frame(records=records))
        daily = frame.resample("1D").agg({"high": "max", "low": "min"}).dropna()
        adr = (daily["high"] - daily["low"]).rolling(period).mean()
        return _result(
            status="success",
            tool_name="calculate_adr",
            started_at=started_at,
            request_id=request_id,
            tool_call_id=tool_call_id,
            agent_name=agent_name,
            environment=environment,
            data={
                "period": period,
                "adr": _records(pd.DataFrame({"adr": adr.dropna()})),
            },
            errors=[],
        )
    except Exception as exc:
        return _result(
            status="rejected",
            tool_name="calculate_adr",
            started_at=started_at,
            request_id=request_id,
            tool_call_id=tool_call_id,
            agent_name=agent_name,
            environment=environment,
            data=None,
            errors=[str(exc)],
        )


def calculate_spread_statistics(
    *,
    spreads: list[float],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Calculate spread distribution statistics.

    Purpose:
        Calculate spread distribution statistics.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    series = _numeric_series(spreads)
    data = {
        "count": len(series),
        "mean": float(series.mean()) if len(series) else 0.0,
        "median": float(series.median()) if len(series) else 0.0,
        "min": float(series.min()) if len(series) else 0.0,
        "max": float(series.max()) if len(series) else 0.0,
        "p95": float(series.quantile(0.95)) if len(series) else 0.0,
    }
    return _result(
        status="success",
        tool_name="calculate_spread_statistics",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data=data,
        errors=[],
    )


def calculate_session_statistics(
    *,
    records: list[dict[str, Any]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Calculate session return statistics.

    Purpose:
        Calculate session return statistics.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    frame = _ohlc(_frame(records=records))
    returns = frame["close"].pct_change()
    hours = frame.index.hour
    masks = {
        "asia": (hours >= 0) & (hours < 7),
        "london": (hours >= 7) & (hours < 13),
        "new_york": (hours >= 13) & (hours < 22),
    }
    stats = {
        name: {
            "count": int(mask.sum()),
            "mean_return": float(returns[mask].mean()) if mask.any() else 0.0,
            "volatility": float(returns[mask].std()) if mask.any() else 0.0,
        }
        for name, mask in masks.items()
    }
    return _result(
        status="success",
        tool_name="calculate_session_statistics",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"sessions": stats},
        errors=[],
    )


def calculate_seasonality_statistics(
    *,
    records: list[dict[str, Any]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Calculate calendar seasonality statistics.

    Purpose:
        Calculate calendar seasonality statistics.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    frame = _ohlc(_frame(records=records))
    returns = frame["close"].pct_change()
    data = {
        "hour": returns.groupby(frame.index.hour).mean().dropna().to_dict(),
        "day_of_week": returns.groupby(frame.index.dayofweek).mean().dropna().to_dict(),
        "month": returns.groupby(frame.index.month).mean().dropna().to_dict(),
    }
    return _result(
        status="success",
        tool_name="calculate_seasonality_statistics",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data=data,
        errors=[],
    )


def calculate_regime_features(
    *,
    records: list[dict[str, Any]],
    fast_window: int = 20,
    slow_window: int = 50,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Calculate regime feature rows.

    Purpose:
        Calculate regime feature rows.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    frame = _ohlc(_frame(records=records))
    close = frame["close"]
    fast = close.rolling(fast_window).mean()
    slow = close.rolling(slow_window).mean()
    vol = close.pct_change().rolling(fast_window).std()
    features = pd.DataFrame(
        {"trend_score": (fast - slow) / close, "volatility": vol}
    ).dropna()
    return _result(
        status="success",
        tool_name="calculate_regime_features",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"features": _records(features), "rows": len(features)},
        errors=[],
    )


def calculate_correlation_matrix(
    *,
    series_by_name: dict[str, list[float]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Calculate a correlation matrix.

    Purpose:
        Calculate a correlation matrix.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    frame = pd.DataFrame(
        {
            name: _numeric_series(values).reset_index(drop=True)
            for name, values in series_by_name.items()
        }
    )
    matrix = frame.corr().fillna(0.0).to_dict()
    return _result(
        status="success",
        tool_name="calculate_correlation_matrix",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"correlation_matrix": matrix},
        errors=[],
    )


def detect_trend_strength(
    *,
    records: list[dict[str, Any]],
    fast_window: int = 20,
    slow_window: int = 50,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Detect trend strength from moving averages.

    Purpose:
        Detect trend strength from moving averages.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    frame = _ohlc(_frame(records=records))
    close = frame["close"]
    score = float(
        (
            (close.rolling(fast_window).mean() - close.rolling(slow_window).mean())
            / close
        ).iloc[-1]
    )
    label = (
        "strong_uptrend"
        if score > 0.01
        else "strong_downtrend"
        if score < -0.01
        else "weak_or_range"
    )
    return _result(
        status="success",
        tool_name="detect_trend_strength",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"score": score, "label": label},
        errors=[],
    )


def detect_market_regime(
    *,
    records: list[dict[str, Any]],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Classify market regime.

    Purpose:
        Classify market regime.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    trend = detect_trend_strength(
        records=records,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )
    label = trend["data"]["label"] if trend["status"] == "success" else "no_edge"
    regime = "trend" if "trend" in label else "mean_reversion_or_range"
    trend["tool_name"] = "detect_market_regime"
    trend["data"] = {"regime": regime, "trend_label": label}
    return trend


def detect_mean_reversion_conditions(
    *,
    records: list[dict[str, Any]],
    window: int = 20,
    z_threshold: float = 2.0,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Detect mean-reversion conditions.

    Purpose:
        Detect mean-reversion conditions.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    close = _ohlc(_frame(records=records))["close"]
    z = ((close - close.rolling(window).mean()) / close.rolling(window).std()).iloc[-1]
    active = bool(abs(float(z)) >= z_threshold)
    return _result(
        status="success",
        tool_name="detect_mean_reversion_conditions",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"active": active, "z_score": float(z)},
        errors=[],
    )


def detect_breakout_conditions(
    *,
    records: list[dict[str, Any]],
    window: int = 20,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Detect breakout conditions.

    Purpose:
        Detect breakout conditions.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    frame = _ohlc(_frame(records=records))
    prior_high = frame["high"].rolling(window).max().shift(1).iloc[-1]
    prior_low = frame["low"].rolling(window).min().shift(1).iloc[-1]
    close = frame["close"].iloc[-1]
    direction = "up" if close > prior_high else "down" if close < prior_low else "none"
    return _result(
        status="success",
        tool_name="detect_breakout_conditions",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={
            "active": direction != "none",
            "direction": direction,
            "prior_high": float(prior_high),
            "prior_low": float(prior_low),
        },
        errors=[],
    )


def generate_research_hypothesis(
    *,
    symbol: str,
    strategy_type: str,
    timeframe: str,
    observation: str,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Generate a structured research hypothesis.

    Purpose:
        Generate a structured research hypothesis.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    hypothesis_id = f"hyp_{symbol.upper()}_{timeframe.upper()}_{strategy_type.lower().replace(' ', '_')}"
    data = {
        "hypothesis_id": hypothesis_id,
        "symbol": symbol.upper(),
        "timeframe": timeframe.upper(),
        "strategy_type": strategy_type.lower(),
        "observation": observation,
        "testable_claim": f"{strategy_type} conditions on {symbol.upper()} {timeframe.upper()} produce positive expectancy after costs.",
        "required_evidence": [
            "sample_size",
            "oos_performance",
            "cost_sensitivity",
            "robustness",
        ],
    }
    return _result(
        status="success",
        tool_name="generate_research_hypothesis",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data=data,
        errors=[],
    )


def score_research_hypothesis(
    *,
    evidence: dict[str, Any],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Score research evidence quality.

    Purpose:
        Score research evidence quality.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    score = 0
    score += 25 if int(evidence.get("sample_size", 0)) >= 200 else 0
    score += 25 if float(evidence.get("expectancy", 0.0)) > 0 else 0
    score += 25 if bool(evidence.get("oos_passed", False)) else 0
    score += 25 if bool(evidence.get("robustness_passed", False)) else 0
    return _result(
        status="success",
        tool_name="score_research_hypothesis",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={
            "score": score,
            "rating": "strong" if score >= 75 else "review" if score >= 50 else "weak",
        },
        errors=[],
    )


def check_sample_size(
    *,
    observations: int,
    minimum: int = 200,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Validate sample size sufficiency.

    Purpose:
        Validate sample size sufficiency.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    passed = observations >= minimum
    return _result(
        status="success",
        tool_name="check_sample_size",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"passed": passed, "observations": observations, "minimum": minimum},
        errors=[],
    )


def check_data_snooping_risk(
    *,
    tests_run: int,
    adjusted: bool = False,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Check data-snooping risk.

    Purpose:
        Check data-snooping risk.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    risk = (
        "high"
        if tests_run > 20 and not adjusted
        else "medium"
        if tests_run > 10
        else "low"
    )
    return _result(
        status="success",
        tool_name="check_data_snooping_risk",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"risk": risk, "tests_run": tests_run, "adjusted": adjusted},
        errors=[],
    )


def check_lookahead_bias_risk(
    *,
    field_names: list[str],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Check lookahead-bias risk.

    Purpose:
        Check lookahead-bias risk.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    bad_terms = ("future", "next_", "forward", "label", "target")
    flagged = [
        name for name in field_names if any(term in name.lower() for term in bad_terms)
    ]
    return _result(
        status="success",
        tool_name="check_lookahead_bias_risk",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"risk": "high" if flagged else "low", "flagged_fields": flagged},
        errors=[],
    )


def check_hypothesis_testability(
    *,
    hypothesis: dict[str, Any],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Check whether a hypothesis is testable.

    Purpose:
        Check whether a hypothesis is testable.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    required = ["symbol", "timeframe", "strategy_type", "testable_claim"]
    missing = [field for field in required if not hypothesis.get(field)]
    return _result(
        status="success",
        tool_name="check_hypothesis_testability",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"testable": not missing, "missing_fields": missing},
        errors=[],
    )


def check_contradictory_evidence(
    *,
    supporting: list[str],
    contradicting: list[str],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Check contradictory evidence risk.

    Purpose:
        Check contradictory evidence risk.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    risk = (
        "high"
        if len(contradicting) > len(supporting)
        else "medium"
        if contradicting
        else "low"
    )
    return _result(
        status="success",
        tool_name="check_contradictory_evidence",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data={"risk": risk, "supporting": supporting, "contradicting": contradicting},
        errors=[],
    )


def build_research_evidence_pack(
    *,
    hypothesis: dict[str, Any],
    evidence: dict[str, Any],
    validation: dict[str, Any],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """Build a structured research evidence pack.

    Purpose:
        Build a structured research evidence pack.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        request_id:
            Optional external trace/request ID.
        agent_name:
            Name of the agent calling this tool.
        environment:
            Runtime environment for audit metadata.
        business inputs:
            Function-specific keyword-only inputs described by the signature.

    Returns:
        Standard HaruQuant tool result dictionary.

    Raises:
        Avoid raising for normal business rejections. Return status="rejected"
        or status="failed" in the standard envelope when possible.
    """
    tool_call_id, started_at, request_id = _start(request_id)
    data = {
        "hypothesis": hypothesis,
        "evidence": evidence,
        "validation": validation,
        "created_at": datetime.now(UTC).isoformat(),
    }
    return _result(
        status="success",
        tool_name="build_research_evidence_pack",
        started_at=started_at,
        request_id=request_id,
        tool_call_id=tool_call_id,
        agent_name=agent_name,
        environment=environment,
        data=data,
        errors=[],
    )
