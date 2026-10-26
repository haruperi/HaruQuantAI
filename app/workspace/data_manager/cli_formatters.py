"""ASCII catalog and dashboard formatting for Data Manager CLI commands."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, cast

MAX_UNDERLYING_DISPLAY_LEN: int = 32
TRUNCATE_LEN: int = 30
MAX_DESC_DISPLAY_LEN: int = 26
DESC_TRUNCATE_LEN: int = 24
MAX_SESSION_DESC_LEN: int = 36
SESSION_DESC_TRUNCATE_LEN: int = 34
DAYS_PER_WEEK: int = 7
WEEKDAYS_COUNT: int = 5
MAX_BASKET_DESC_LEN: int = 22
BASKET_DESC_TRUNCATE_LEN: int = 20
MAX_READY_LEN: int = 13
READY_TRUNCATE_LEN: int = 11
MAX_BROKER_DESC_LEN: int = 22
BROKER_DESC_TRUNCATE_LEN: int = 20
_MAX_INLINE_OUTPUTS: int = 2
_MAX_DATE_LEN: int = 10


def _get(item: Any, key: str, default: Any = "") -> Any:
    if isinstance(item, Mapping):
        return cast("Mapping[str, Any]", item).get(key, default)
    return getattr(item, key, default)


def format_dataset_table(saved_datasets: Sequence[Any] | Mapping[str, Any]) -> str:
    """Format ASCII table of saved dataset catalog entries."""
    items: Sequence[Any]
    if (
        isinstance(saved_datasets, Mapping)
        and "data" in saved_datasets
        and isinstance(saved_datasets["data"], Sequence)
    ):
        items = cast("Any", saved_datasets["data"])
    elif isinstance(saved_datasets, Sequence):
        items = saved_datasets
    else:
        items = ()
    count = len(items)
    lines: list[str] = [f"=== Saved Datasets Catalog ({count} items) ==="]
    header_fmt = (
        "| {sym:<14} | {inst:<15} | {brk:<12} | {und:<32} | {tf:<4} "
        "| {tz:<8} | {d_from:<10} | {d_to:<10} | {days:>6} | {recs:>10} "
        "| {src:<16} | {cat:<8} |"
    )
    divider = (
        "|-"
        + "-|-".join(
            ["-" * width for width in (14, 15, 12, 32, 4, 8, 10, 10, 6, 10, 16, 8)]
        )
        + "-|"
    )
    lines.append(
        header_fmt.format(
            sym="Symbol Name",
            inst="Instrument",
            brk="Broker profile",
            und="Underlying Symbol",
            tf="TF",
            tz="Timezone",
            d_from="Date from",
            d_to="Date to",
            days="Days",
            recs="Records",
            src="Source",
            cat="Data type",
        )
    )
    lines.append(divider)
    for ds in items:
        und = str(_get(ds, "underlying", ""))
        if len(und) > MAX_UNDERLYING_DISPLAY_LEN:
            und_preview = und[:TRUNCATE_LEN] + ".."
        else:
            und_preview = und
        lines.append(
            header_fmt.format(
                sym=str(_get(ds, "symbol", "")),
                inst=str(_get(ds, "instrument", "")),
                brk=str(_get(ds, "broker", "")),
                und=und_preview,
                tf=str(_get(ds, "timeframe", "")),
                tz=str(_get(ds, "timezone", "")),
                d_from=str(_get(ds, "date_from", "") or "-"),
                d_to=str(_get(ds, "date_to", "") or "-"),
                days=_get(ds, "total_days", 0),
                recs=f"{int(_get(ds, 'total_records', 0)):,}",
                src=str(_get(ds, "source", "")),
                cat=str(_get(ds, "data_type", "")),
            )
        )
    return "\n".join(lines)


def format_data_dashboard(
    overview: Mapping[str, Any] | Any,
    saved_datasets: Sequence[Any] | Mapping[str, Any],
) -> str:
    """Format complete human-readable dashboard output."""
    metrics: Mapping[str, Any]
    if (
        isinstance(overview, Mapping)
        and "data" in overview
        and isinstance(overview["data"], Mapping)
    ):
        metrics = cast("Mapping[str, Any]", overview["data"])
    elif isinstance(overview, Mapping):
        metrics = cast("Mapping[str, Any]", overview)
    else:
        metrics = dict[str, Any]()
    ds_count = _get(metrics, "datasets_count", 0)
    total_bars = int(_get(metrics, "total_bars", 0))
    inst_count = _get(metrics, "instruments_count", 0)
    sess_count = _get(metrics, "sessions_count", 0)
    bask_count = _get(metrics, "baskets_count", 0)
    act_prov = _get(metrics, "active_providers_count", 0)
    lines = [
        "=== Data Manager: Live Database Overview ===",
        f"Total Datasets:       {ds_count}",
        f"Historical Bars:      {total_bars:,}",
        f"Instruments Catalog:  {inst_count}",
        f"Trading Sessions:     {sess_count}",
        f"Custom Baskets:       {bask_count}",
        f"Active Providers:     {act_prov}",
        "",
        format_dataset_table(saved_datasets),
    ]
    return "\n".join(lines)


def _fmt_scalar(val: Any) -> str:
    """Format scalar number or string cleanly."""
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return f"{val:g}"
    return str(val)


def _extract_field(item: Any, section: str, key: str, default: Any = 0) -> Any:
    """Extract nested dictionary or contract property safely."""
    sec = _get(item, section, {})
    if isinstance(sec, Mapping):
        return cast("Mapping[str, Any]", sec).get(key, default)
    return getattr(sec, key, default)


def _format_commission(item: Any) -> str:
    """Extract human-readable commission summary."""
    single_comm = _get(item, "commission")
    if single_comm is not None and isinstance(single_comm, (int, float)):
        return f"${_fmt_scalar(single_comm)}/lot"
    comm = _get(item, "commissions", {})
    if not isinstance(comm, Mapping):
        return "None"
    rules: Any = cast("Mapping[str, Any]", comm).get("rules") or []
    if isinstance(rules, list) and rules:
        first_rule = cast("Any", rules)[0]
        if isinstance(first_rule, Mapping):
            tiers: Any = cast("Mapping[str, Any]", first_rule).get("tiers") or []
            if isinstance(tiers, list) and tiers:
                tier = cast("Any", tiers)[0]
                if isinstance(tier, Mapping):
                    val = _fmt_scalar(cast("Mapping[str, Any]", tier).get("value", 0))
                    curr = str(
                        cast("Mapping[str, Any]", tier).get("currency", "")
                    ).strip()
                    return f"{val} {curr}".strip()
    return "None"


def _format_swap(item: Any) -> str:
    """Extract swap long/short representation."""
    swap = _get(item, "swap", {})
    if not isinstance(swap, Mapping):
        return "0 / 0"
    l_val = _fmt_scalar(cast("Mapping[str, Any]", swap).get("long", 0))
    s_val = _fmt_scalar(cast("Mapping[str, Any]", swap).get("short", 0))
    return f"{l_val} / {s_val}"


def _format_order_size(item: Any) -> str:
    """Extract order size multiplier and step."""
    ord_sz = _get(item, "order_size", {})
    if isinstance(ord_sz, Mapping) and ord_sz:
        mult = _fmt_scalar(cast("Mapping[str, Any]", ord_sz).get("multiplier", 1))
        step = _fmt_scalar(cast("Mapping[str, Any]", ord_sz).get("step", 0))
        return f"{mult} / {step}"
    vol = _get(item, "volume", {})
    if isinstance(vol, Mapping) and vol:
        mult = _fmt_scalar(cast("Mapping[str, Any]", vol).get("min", 1))
        step = _fmt_scalar(cast("Mapping[str, Any]", vol).get("step", 0))
        return f"{mult} / {step}"
    return "1 / 0"


def format_symbol_table(
    symbols: Sequence[Any] | Mapping[str, Any],
    *,
    limit: int | None = 50,
) -> str:
    """Format ASCII table of symbol catalog entries with StrategyQuant columns."""
    items: Sequence[Any]
    if (
        isinstance(symbols, Mapping)
        and "data" in symbols
        and isinstance(symbols["data"], Sequence)
    ):
        items = cast("Any", symbols["data"])
    elif isinstance(symbols, Sequence):
        items = symbols
    else:
        items = ()
    total_count = len(items)
    displayed_items = items[:limit] if limit is not None else items
    count = len(displayed_items)
    title = (
        f"=== Symbols Catalog (Showing {count} of {total_count} items) ==="
        if (limit is not None and total_count > count)
        else f"=== Symbols Catalog ({total_count} items) ==="
    )
    lines: list[str] = [title]
    header_fmt = (
        "| {sym:<10} | {desc:<26} | {brk:<14} | {pt:>12} | {ts:>10} "
        "| {tstep:>10} | {spd:>14} | {slip:>16} | {comm:<14} | {swap:<16} "
        "| {dtype:<14} | {ord_sz:<20} |"
    )
    divider = (
        "|-"
        + "-|-".join(
            ["-" * width for width in (10, 26, 14, 12, 10, 10, 14, 16, 14, 16, 14, 20)]
        )
        + "-|"
    )
    lines.append(
        header_fmt.format(
            sym="Symbol",
            desc="Description",
            brk="Broker Profile",
            pt="Point Value",
            ts="Tick Size",
            tstep="Tick Step",
            spd="Default Spread",
            slip="Default Slippage",
            comm="Commissions",
            swap="Swap (L/S)",
            dtype="Data Type",
            ord_sz="Order Size Mult/Step",
        )
    )
    lines.append(divider)
    for item in displayed_items:
        sym = str(_get(item, "name", "") or _get(item, "symbol", ""))
        desc = str(_get(item, "description", ""))
        if len(desc) > MAX_DESC_DISPLAY_LEN:
            desc = desc[:DESC_TRUNCATE_LEN] + ".."
        brk = str(_get(item, "broker_name") or _get(item, "broker") or "Default")
        pt_val = _extract_field(item, "price", "contract_size", None)
        if pt_val is None or pt_val == 0:
            pt_val = _extract_field(item, "contract", "point_value", 0)
        if isinstance(pt_val, (int, float)) and pt_val == int(pt_val) and pt_val > 0:
            pt_str = f"{int(pt_val):,}"
        else:
            pt_str = _fmt_scalar(pt_val)
        tick_sz = _fmt_scalar(_extract_field(item, "price", "tick_size", 0))
        tick_st = _fmt_scalar(_extract_field(item, "price", "tick_step", 0))
        def_spread = _fmt_scalar(_extract_field(item, "spread", "default", 0))
        def_slip = _fmt_scalar(_extract_field(item, "spread", "slippage", 0))
        comm_str = _format_commission(item)
        swap_str = _format_swap(item)
        dtype = str(_get(item, "data_type", ""))
        ord_sz_str = _format_order_size(item)
        lines.append(
            header_fmt.format(
                sym=sym,
                desc=desc,
                brk=brk,
                pt=pt_str,
                ts=tick_sz,
                tstep=tick_st,
                spd=def_spread,
                slip=def_slip,
                comm=comm_str,
                swap=swap_str,
                dtype=dtype,
                ord_sz=ord_sz_str,
            )
        )
    return "\n".join(lines)


class SymbolsCLI:
    """Table formatters for the Data Manager catalog."""

    format_symbol_table = staticmethod(format_symbol_table)


def _summarize_windows(windows: Sequence[Any]) -> str:
    """Summarize trading windows schedule concisely."""
    if not windows:
        return "None"
    count = len(windows)
    times: set[str] = set()
    for w in windows:
        s = _get(w, "start_time") or _get(w, "open_time") or "00:00"
        e = _get(w, "end_time") or _get(w, "close_time") or "23:59"
        times.add(f"{str(s)[:5]}-{str(e)[:5]}")
    if len(times) == 1:
        t = next(iter(times))
        if count == DAYS_PER_WEEK and ("00:00-23:59" in t or "00:00-24:00" in t):
            return f"24/7 ({count}d)"
        if count == WEEKDAYS_COUNT:
            return f"Mon-Fri {t} ({count}d)"
        if count == DAYS_PER_WEEK:
            return f"Daily {t} ({count}d)"
        return f"{count}d ({t})"
    return f"{count} windows"


def _summarize_holidays(holidays: Sequence[Any]) -> str:
    """Summarize holidays calendar concisely."""
    if not holidays:
        return "-"
    count = len(holidays)
    if count == 1:
        desc = str(_get(holidays[0], "description", ""))
        return desc or "1 holiday"
    return f"{count} holidays"


def format_session_table(
    sessions: Sequence[Any] | Mapping[str, Any],
) -> str:
    """Format ASCII table of trading session calendar catalog entries."""
    items: Sequence[Any]
    if (
        isinstance(sessions, Mapping)
        and "data" in sessions
        and isinstance(sessions["data"], Sequence)
    ):
        items = cast("Any", sessions["data"])
    elif isinstance(sessions, Sequence):
        items = sessions
    else:
        items = ()
    count = len(items)
    lines: list[str] = [f"=== Trading Sessions Catalog ({count} items) ==="]
    header_fmt = (
        "| {name:<26} | {brk:<14} | {desc:<36} | {tz:<18} | {wins:<24} | {hols:<12} |"
    )
    divider = (
        "|-" + "-|-".join(["-" * width for width in (26, 14, 36, 18, 24, 12)]) + "-|"
    )
    lines.append(
        header_fmt.format(
            name="Session Name",
            brk="Broker Profile",
            desc="Description",
            tz="Timezone",
            wins="Windows",
            hols="Holidays",
        )
    )
    lines.append(divider)
    for item in items:
        name = str(_get(item, "name", ""))
        desc = str(_get(item, "description", ""))
        if len(desc) > MAX_SESSION_DESC_LEN:
            desc = desc[:SESSION_DESC_TRUNCATE_LEN] + ".."
        brk_name = str(_get(item, "broker_name") or "")
        brk_id = _get(item, "broker_id", None)
        if brk_name and brk_name != "Default":
            brk_display = brk_name
        elif brk_id is not None and brk_id not in (-1, 0):
            brk_display = f"Broker {brk_id}"
        else:
            brk_display = "SQ default"
        tz = str(_get(item, "timezone", "UTC"))
        windows = _get(item, "windows", ())
        if not isinstance(windows, Sequence):
            windows = ()
        wins_str = _summarize_windows(cast("Sequence[Any]", windows))
        holidays = _get(item, "holidays", ())
        if not isinstance(holidays, Sequence):
            holidays = ()
        hols_str = _summarize_holidays(cast("Sequence[Any]", holidays))
        lines.append(
            header_fmt.format(
                name=name,
                brk=brk_display,
                desc=desc,
                tz=tz,
                wins=wins_str,
                hols=hols_str,
            )
        )
    return "\n".join(lines)


class SessionsCLI:
    """Table formatters for the Data Manager catalog."""

    format_session_table = staticmethod(format_session_table)


def format_basket_table(
    baskets: Sequence[Any] | Mapping[str, Any],
) -> str:
    """Format ASCII table of stock groups / baskets catalog entries."""
    items: Sequence[Any]
    if (
        isinstance(baskets, Mapping)
        and "data" in baskets
        and isinstance(baskets["data"], Sequence)
    ):
        items = cast("Any", baskets["data"])
    elif isinstance(baskets, Sequence):
        items = baskets
    else:
        items = ()
    count = len(items)
    lines: list[str] = [f"=== Stock Groups / Baskets Catalog ({count} items) ==="]
    header_fmt = (
        "| {name:<32} | {cnt:<12} | {desc:<22} | {syms:>17} "
        "| {down:>12} | {ready:<13} | {d_from:<10} | {d_to:<10} |"
    )
    divider = (
        "|-"
        + "-|-".join(["-" * width for width in (32, 12, 22, 17, 12, 13, 10, 10)])
        + "-|"
    )
    lines.append(
        header_fmt.format(
            name="Name",
            cnt="Count",
            desc="Description",
            syms="Number of symbols",
            down="Downloaded",
            ready="Ready to use?",
            d_from="Date from",
            d_to="Date to",
        )
    )
    lines.append(divider)
    for item in items:
        name = str(_get(item, "name", ""))
        desc = str(_get(item, "description", ""))
        if len(desc) > MAX_BASKET_DESC_LEN:
            desc = desc[:BASKET_DESC_TRUNCATE_LEN] + ".."
        active = _get(item, "active_count", 0)
        total = _get(item, "stocks_count", 0)
        if total == 0:
            total = _get(item, "total_count", 0)
        cnt_str = f"{active} / {total}"
        syms = _get(item, "symbols_count", 0)
        down = _get(item, "downloaded_count", 0)
        down_str = f"{down} / {total}"
        ready_val = _get(item, "ready", False)
        if isinstance(ready_val, str):
            ready_str = (
                ready_val
                if len(ready_val) <= MAX_READY_LEN
                else ready_val[:READY_TRUNCATE_LEN].rstrip() + ".."
            )
        else:
            ready_str = "Yes" if ready_val else "No"
        d_from = str(_get(item, "date_from", "-"))
        d_to = str(_get(item, "date_to", "-"))
        lines.append(
            header_fmt.format(
                name=name,
                cnt=cnt_str,
                desc=desc,
                syms=syms,
                down=down_str,
                ready=ready_str,
                d_from=d_from,
                d_to=d_to,
            )
        )
    return "\n".join(lines)


class BasketsCLI:
    """Table formatters for the Data Manager catalog."""

    format_basket_table = staticmethod(format_basket_table)


def format_broker_table(
    brokers: Sequence[Any] | Mapping[str, Any],
) -> str:
    """Format ASCII table of broker profile catalog entries."""
    items: Sequence[Any]
    if (
        isinstance(brokers, Mapping)
        and "data" in brokers
        and isinstance(brokers["data"], Sequence)
    ):
        items = cast("Any", brokers["data"])
    elif isinstance(brokers, Sequence):
        items = brokers
    else:
        items = ()
    count = len(items)
    lines: list[str] = [f"=== Broker Profiles Catalog ({count} items) ==="]
    header_fmt = (
        "| {name:<26} | {desc:<22} | {pf:<14} | {tz:<16} "
        "| {stocks:>17} | {insts:>22} | {sess:>19} |"
    )
    divider = (
        "|-"
        + "-|-".join(["-" * width for width in (26, 22, 14, 16, 17, 22, 19)])
        + "-|"
    )
    lines.append(
        header_fmt.format(
            name="Name",
            desc="Description",
            pf="Postfix",
            tz="Timezone",
            stocks="Customized stocks",
            insts="Customized instruments",
            sess="Customized sessions",
        )
    )
    lines.append(divider)
    for item in items:
        name = str(_get(item, "name", ""))
        desc = str(_get(item, "description", ""))
        if len(desc) > MAX_BROKER_DESC_LEN:
            desc = desc[:BROKER_DESC_TRUNCATE_LEN] + ".."
        pf = str(_get(item, "postfix", ""))
        tz = str(
            _get(item, "server_timezone", "") or _get(item, "timezone", "") or "UTC"
        )
        stocks = _get(item, "customized_stocks", 0)
        insts = _get(item, "customized_instruments", 0)
        if insts == 0:
            insts = _get(item, "total_instruments", 0)
        sess = _get(item, "customized_sessions", 0)
        if sess == 0:
            sess = _get(item, "total_sessions", 0)
        lines.append(
            header_fmt.format(
                name=name,
                desc=desc,
                pf=pf,
                tz=tz,
                stocks=stocks,
                insts=insts,
                sess=sess,
            )
        )
    return "\n".join(lines)


class BrokersCLI:
    """Table formatters for the Data Manager catalog."""

    format_broker_table = staticmethod(format_broker_table)


class DataCLI:
    """Table formatters for the Data Manager catalog."""

    format_broker_table = staticmethod(format_broker_table)
    format_basket_table = staticmethod(format_basket_table)
    format_session_table = staticmethod(format_session_table)
    format_symbol_table = staticmethod(format_symbol_table)
    format_dataset_table = staticmethod(format_dataset_table)
    format_data_dashboard: Callable[..., str] = staticmethod(format_data_dashboard)


def format_custom_table(
    indicators: Sequence[Any] | Mapping[str, Any], limit: int | None = 50
) -> str:
    """Format ASCII table of external indicator catalog entries."""
    items: Sequence[Any]
    if (
        isinstance(indicators, Mapping)
        and "data" in indicators
        and isinstance(indicators["data"], Sequence)
    ):
        items = cast("Any", indicators["data"])
    elif isinstance(indicators, Sequence):
        items = indicators
    else:
        items = ()
    count = len(items)
    lines: list[str] = [f"=== External Indicators Catalog ({count} items) ==="]
    header_fmt = (
        "| {name:<20} | {values:<16} | {dtype:<12} | {tf:<9} "
        "| {d_from:<12} | {d_to:<12} | {days:>6} | {recs:>10} |"
    )
    divider = (
        "|-"
        + "-|-".join(["-" * width for width in (20, 16, 12, 9, 12, 12, 6, 10)])
        + "-|"
    )
    lines.append(
        header_fmt.format(
            name="Name",
            values="Values",
            dtype="Data type",
            tf="Timeframe",
            d_from="Date from",
            d_to="Date to",
            days="Days",
            recs="Records",
        )
    )
    lines.append(divider)
    visible = items if limit is None else items[:limit]
    for item in visible:
        name = str(_get(item, "name", ""))
        vals = _get(item, "values", [])
        if isinstance(vals, list):
            val_names = [
                v.get("name", "") if isinstance(v, dict) else str(v) for v in vals
            ]
            val_str = (
                ", ".join(val_names)
                if len(val_names) <= _MAX_INLINE_OUTPUTS
                else f"{len(val_names)} outputs"
            )
        else:
            val_str = str(vals)
        dtype = str(_get(item, "data_type", "custom"))
        tf = str(_get(item, "timeframe", "D1"))
        d_from = str(_get(item, "date_from", "") or "-")
        if len(d_from) > _MAX_DATE_LEN:
            d_from = d_from[:_MAX_DATE_LEN]
        d_to = str(_get(item, "date_to", "") or "-")
        if len(d_to) > _MAX_DATE_LEN:
            d_to = d_to[:_MAX_DATE_LEN]
        days = _get(item, "total_days", 0)
        recs = f"{int(_get(item, 'total_records', 0)):,}"
        lines.append(
            header_fmt.format(
                name=name[:20],
                values=val_str[:16],
                dtype=dtype[:12],
                tf=tf[:9],
                d_from=d_from[:12],
                d_to=d_to[:12],
                days=days,
                recs=recs,
            )
        )
    if limit is not None and count > limit:
        lines.append(f"... and {count - limit} more items")
    return "\n".join(lines)


def format_review_table(records: Sequence[Any], columns: Sequence[str]) -> str:
    """Format ASCII table of dated observation records."""
    if not records:
        return "No observations recorded."
    header_cols = ["Timestamp", *columns]
    col_widths = [max(len(str(c)), 12) for c in header_cols]
    col_widths[0] = max(col_widths[0], 25)
    header_fmt = (
        "| " + " | ".join(f"{{{i}:<{w}}}" for i, w in enumerate(col_widths)) + " |"
    )
    divider = "|-" + "-|-".join("-" * w for w in col_widths) + "-|"
    lines = [
        header_fmt.format(*header_cols),
        divider,
    ]
    for row in records:
        ts = str(_get(row, "timestamp", ""))
        vals = _get(row, "values", {})
        cells = [
            ts[: col_widths[0]],
            *(
                str(vals.get(c, ""))[: col_widths[i + 1]]
                if isinstance(vals, dict)
                else ""
                for i, c in enumerate(columns)
            ),
        ]
        lines.append(header_fmt.format(*cells))
    return "\n".join(lines)


class CustomDataCLI:
    """Table formatters for Data Manager custom indicators."""

    format_custom_table = staticmethod(format_custom_table)
    format_review_table = staticmethod(format_review_table)
