"""Data Manager command registration, execution, and formatting utilities.

Description:
    Owns Data Manager headless parsers, service dispatch, output, and exit codes.
    The main app CLI registers this domain through register_commands().
    Provides ASCII table formatters and dashboard presentation for the
    Data Manager workspace, rendering dataset catalogs and database summaries.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from functools import partial
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.workspace.data_manager.symbols import Symbols

from app.host.logging import get_logger

__all__ = [
    "BasketsCLI",
    "BrokersCLI",
    "DataCLI",
    "SessionsCLI",
    "SymbolsCLI",
    "format_basket_table",
    "format_broker_table",
    "format_data_dashboard",
    "format_dataset_table",
    "format_session_table",
    "format_symbol_table",
    "register_commands",
    "run_command",
]

logger = get_logger(__name__)

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


def _get(item: Any, key: str, default: Any = "") -> Any:
    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def format_dataset_table(saved_datasets: Sequence[Any] | Mapping[str, Any]) -> str:
    """Format ASCII table of saved dataset catalog entries."""
    items: Sequence[Any]
    if (
        isinstance(saved_datasets, Mapping)
        and "data" in saved_datasets
        and isinstance(saved_datasets["data"], Sequence)
    ):
        items = saved_datasets["data"]
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
            [
                "-" * 14,
                "-" * 15,
                "-" * 12,
                "-" * 32,
                "-" * 4,
                "-" * 8,
                "-" * 10,
                "-" * 10,
                "-" * 6,
                "-" * 10,
                "-" * 16,
                "-" * 8,
            ]
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
        metrics = overview["data"]
    elif isinstance(overview, Mapping):
        metrics = overview
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
        return sec.get(key, default)
    return getattr(sec, key, default)


def _format_commission(item: Any) -> str:
    """Extract human-readable commission summary."""
    single_comm = _get(item, "commission")
    if single_comm is not None and isinstance(single_comm, (int, float)):
        return f"${_fmt_scalar(single_comm)}/lot"
    comm = _get(item, "commissions", {})
    if not isinstance(comm, Mapping):
        return "None"
    rules = comm.get("rules") or []
    if isinstance(rules, list) and rules:
        first_rule = rules[0]
        if isinstance(first_rule, Mapping):
            tiers = first_rule.get("tiers") or []
            if isinstance(tiers, list) and tiers:
                tier = tiers[0]
                if isinstance(tier, Mapping):
                    val = _fmt_scalar(tier.get("value", 0))
                    curr = str(tier.get("currency", "")).strip()
                    return f"{val} {curr}".strip()
    return "None"


def _format_swap(item: Any) -> str:
    """Extract swap long/short representation."""
    swap = _get(item, "swap", {})
    if not isinstance(swap, Mapping):
        return "0 / 0"
    l_val = _fmt_scalar(swap.get("long", 0))
    s_val = _fmt_scalar(swap.get("short", 0))
    return f"{l_val} / {s_val}"


def _format_order_size(item: Any) -> str:
    """Extract order size multiplier and step."""
    ord_sz = _get(item, "order_size", {})
    if isinstance(ord_sz, Mapping) and ord_sz:
        mult = _fmt_scalar(ord_sz.get("multiplier", 1))
        step = _fmt_scalar(ord_sz.get("step", 0))
        return f"{mult} / {step}"
    vol = _get(item, "volume", {})
    if isinstance(vol, Mapping) and vol:
        mult = _fmt_scalar(vol.get("min", 1))
        step = _fmt_scalar(vol.get("step", 0))
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
        items = symbols["data"]
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
            [
                "-" * 10,
                "-" * 26,
                "-" * 14,
                "-" * 12,
                "-" * 10,
                "-" * 10,
                "-" * 14,
                "-" * 16,
                "-" * 14,
                "-" * 16,
                "-" * 14,
                "-" * 20,
            ]
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
    """Headless CLI formatter and table presentation for Symbols catalog."""

    @classmethod
    def format_symbol_table(
        cls,
        symbols: Sequence[Any] | Mapping[str, Any],
        *,
        limit: int | None = 50,
    ) -> str:
        """Format ASCII table of symbol catalog entries."""
        logger.debug("Formatting symbols as ASCII table")
        return format_symbol_table(symbols, limit=limit)


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
        items = sessions["data"]
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
        "|-"
        + "-|-".join(
            [
                "-" * 26,
                "-" * 14,
                "-" * 36,
                "-" * 18,
                "-" * 24,
                "-" * 12,
            ]
        )
        + "-|"
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
        wins_str = _summarize_windows(windows)
        holidays = _get(item, "holidays", ())
        if not isinstance(holidays, Sequence):
            holidays = ()
        hols_str = _summarize_holidays(holidays)
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
    """Headless CLI formatter and table presentation for Sessions catalog."""

    @classmethod
    def format_session_table(
        cls,
        sessions: Sequence[Any] | Mapping[str, Any],
    ) -> str:
        """Format ASCII table of trading session calendar catalog entries."""
        logger.debug("Formatting sessions as ASCII table")
        return format_session_table(sessions)


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
        items = baskets["data"]
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
        + "-|-".join(
            [
                "-" * 32,
                "-" * 12,
                "-" * 22,
                "-" * 17,
                "-" * 12,
                "-" * 13,
                "-" * 10,
                "-" * 10,
            ]
        )
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
    """Headless CLI formatter and table presentation for Baskets catalog."""

    @classmethod
    def format_basket_table(
        cls,
        baskets: Sequence[Any] | Mapping[str, Any],
    ) -> str:
        """Format ASCII table of stock groups / baskets catalog entries."""
        logger.debug("Formatting stock groups as ASCII table")
        return format_basket_table(baskets)


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
        items = brokers["data"]
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
        + "-|-".join(
            [
                "-" * 26,
                "-" * 22,
                "-" * 14,
                "-" * 16,
                "-" * 17,
                "-" * 22,
                "-" * 19,
            ]
        )
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
    """Headless CLI formatter and table presentation for Brokers catalog."""

    @classmethod
    def format_broker_table(
        cls,
        brokers: Sequence[Any] | Mapping[str, Any],
    ) -> str:
        """Format ASCII table of broker profile catalog entries."""
        logger.debug("Formatting broker profiles as ASCII table")
        return format_broker_table(brokers)


class DataCLI:
    """Headless CLI formatter and table presentation for Data Manager data."""

    MAX_UNDERLYING_DISPLAY_LEN: int = MAX_UNDERLYING_DISPLAY_LEN
    TRUNCATE_LEN: int = TRUNCATE_LEN

    @classmethod
    def format_broker_table(
        cls,
        brokers: Sequence[Any] | Mapping[str, Any],
    ) -> str:
        """Format ASCII table of broker profile catalog entries."""
        return format_broker_table(brokers)

    @classmethod
    def format_basket_table(
        cls,
        baskets: Sequence[Any] | Mapping[str, Any],
    ) -> str:
        """Format ASCII table of stock groups / baskets catalog entries."""
        return format_basket_table(baskets)

    @classmethod
    def format_session_table(
        cls,
        sessions: Sequence[Any] | Mapping[str, Any],
    ) -> str:
        """Format ASCII table of trading session calendar catalog entries."""
        return format_session_table(sessions)

    @classmethod
    def format_symbol_table(
        cls,
        symbols: Sequence[Any] | Mapping[str, Any],
        *,
        limit: int | None = 50,
    ) -> str:
        """Format ASCII table of symbol catalog entries."""
        return format_symbol_table(symbols, limit=limit)

    @classmethod
    def format_dataset_table(
        cls,
        saved_datasets: Sequence[Any] | Mapping[str, Any],
    ) -> str:
        """Format ASCII table of saved dataset catalog entries."""
        logger.debug(
            "Formatting saved datasets as ASCII table",
        )
        return format_dataset_table(saved_datasets)

    @classmethod
    def format_data_dashboard(
        cls,
        overview: Mapping[str, Any],
        saved_datasets: Sequence[Any] | Mapping[str, Any],
    ) -> str:
        """Format complete human-readable dashboard output."""
        logger.debug("Formatting data overview and dataset table")
        return format_data_dashboard(overview, saved_datasets)


def register_commands(commands: Any) -> None:
    """Register Data Manager parsers and bind the domain command handler."""
    data_manager = commands.add_parser("data-manager", help="Manage workspace data")
    resources = data_manager.add_subparsers(dest="resource", required=True)
    symbol = resources.add_parser("symbol", help="Access the symbols catalog")
    symbol_commands = symbol.add_subparsers(dest="symbol_command", required=True)
    _symbol_mutation_parsers(symbol_commands)
    symbol_list = symbol_commands.add_parser(
        "list", help="List symbols in the local catalog by page"
    )
    symbol_list.add_argument(
        "--page", type=_positive_int, default=1, help="Page number (default: 1)"
    )
    symbol_list.add_argument(
        "--page-size",
        type=_positive_int,
        default=50,
        help="Symbols per page (default: 50)",
    )
    data_manager.set_defaults(handler=partial(run_command, parser=data_manager))


def run_command(
    arguments: argparse.Namespace, *, parser: argparse.ArgumentParser
) -> int:
    """Execute a Data Manager command, emit errors, and return its exit code."""
    result = _run_symbol_command(arguments, parser)
    if result is None:
        return 0
    print(json.dumps(result, allow_nan=False))
    return 0 if result["success"] else 1


def _positive_int(value: str) -> int:
    """Parse a positive pagination argument."""
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _print_symbol_page(result: dict[str, Any], page: int, page_size: int) -> bool:
    """Render one catalog page, returning false for an out-of-range page."""
    symbols = result["data"]
    total = len(symbols)
    pages = max(1, (total + page_size - 1) // page_size)
    if page > pages:
        return False
    start = (page - 1) * page_size
    end = min(start + page_size, total)
    print(
        f"Page {page} of {pages} | Symbols {start + 1 if total else 0}-{end} of {total}"
    )
    print(SymbolsCLI.format_symbol_table(symbols[start:end], limit=None))
    if page < pages:
        print(
            "Next: uv run python -m app.cli data-manager symbol list "
            f"--page {page + 1} --page-size {page_size}"
        )
    return True


def _symbol_mutation_parsers(commands: Any) -> None:
    """Register symbol mutation arguments using service parameter names."""
    add = commands.add_parser("add", help="Create a symbol in the local catalog")
    add.add_argument("--name", required=True, help="Symbol name, e.g. EURUSD")
    add.add_argument("--datasource", required=True, help="Broker profile suffix")
    _symbol_field_arguments(add)
    edit = commands.add_parser(
        "edit", help="Edit an existing symbol in the local catalog"
    )
    edit.add_argument(
        "symbol_names", nargs="+", help="Exact saved symbol names, including suffixes"
    )
    edit.add_argument("--name", default=argparse.SUPPRESS, help="New saved symbol name")
    _symbol_field_arguments(edit)
    delete = commands.add_parser(
        "delete", help="Delete a symbol from the local catalog"
    )
    delete.add_argument(
        "symbol_names", nargs="+", help="Exact saved symbol names, including suffixes"
    )
    clone = commands.add_parser("clone", help="Clone a symbol in the local catalog")
    clone.add_argument("source_symbol", help="Exact saved source symbol name")
    clone.add_argument(
        "new_symbol", help="New symbol name (inherits source datasource)"
    )
    clone.add_argument("--new-datasource", help="Override the source datasource suffix")
    load = commands.add_parser("load", help="Load symbols from a CSV file")
    load.add_argument("csv_path", help="CSV path (quote paths containing spaces)")
    save = commands.add_parser("save", help="Save the full symbol catalog to CSV")
    save.add_argument(
        "csv_path", help="Destination CSV path (existing files are replaced)"
    )


def _symbol_field_arguments(add: Any) -> None:
    """Register shared optional symbol fields without overriding omitted values."""
    for field in (
        "description",
        "exchange",
        "data-type",
        "triple-swap-on",
        "swap-type",
    ):
        add.add_argument(f"--{field}", default=argparse.SUPPRESS)
    for field in (
        "default-spread",
        "pip-size",
        "pip-step",
        "point-value",
        "min-distance",
        "order-size-multiplier",
        "order-size-step",
        "swap-long",
        "swap-short",
        "commission",
    ):
        add.add_argument(f"--{field}", type=float, default=argparse.SUPPRESS)
    add.add_argument("--broker-id", type=int, default=argparse.SUPPRESS)


def _validate_symbol_edit(
    fields: dict[str, Any], names: list[str], parser: Any
) -> None:
    """Require edit values and restrict renaming to one symbol."""
    if not fields:
        parser.error("symbol edit requires at least one field to update")
    if "name" in fields and len(names) > 1:
        parser.error("--name can only rename one symbol at a time")


def _run_symbol_command(
    arguments: argparse.Namespace, parser: Any
) -> dict[str, Any] | None:
    """Dispatch catalog commands and render successful table results."""
    from app.workspace.data_manager.symbols import Symbols

    service = Symbols()
    file_commands = {
        "clone": _clone_symbol,
        "load": _load_symbols,
        "save": _save_symbols,
    }
    if arguments.symbol_command in file_commands:
        return file_commands[arguments.symbol_command](service, arguments)
    if arguments.symbol_command in {"add", "edit"}:
        fields = {
            key: value
            for key, value in vars(arguments).items()
            if key
            not in {"command", "resource", "symbol_command", "symbol_names", "handler"}
        }
        if arguments.symbol_command == "add":
            result = service.add(**fields)
        else:
            _validate_symbol_edit(fields, arguments.symbol_names, parser)
            result = service.edit(arguments.symbol_names, updates=fields)
        if result["success"]:
            print(result["message"])
            rows = (
                [result["data"]]
                if arguments.symbol_command == "add"
                else result["data"]
            )
            print(SymbolsCLI.format_symbol_table(rows, limit=None))
            return None
    elif arguments.symbol_command == "delete":
        result = service.delete(arguments.symbol_names)
        if result["success"]:
            print(result["message"])
            for name in result["data"]:
                print(name)
            return None
    else:
        result = service.list()
        if result["success"]:
            if not _print_symbol_page(result, arguments.page, arguments.page_size):
                parser.error("--page exceeds the number of catalog pages")
            return None
    return result


def _clone_symbol(
    service: Symbols, arguments: argparse.Namespace
) -> dict[str, Any] | None:
    """Clone through the catalog service and display the created symbol."""
    result = service.clone(
        arguments.source_symbol,
        arguments.new_symbol,
        new_datasource=arguments.new_datasource,
    )
    if result["success"]:
        print(result["message"])
        print(SymbolsCLI.format_symbol_table([result["data"]], limit=None))
        return None
    return result


def _load_symbols(
    service: Symbols, arguments: argparse.Namespace
) -> dict[str, Any] | None:
    """Load a CSV and report imported symbols and skipped row errors."""
    result = service.load(arguments.csv_path)
    if not result["success"]:
        return result
    print(result["message"])
    print(SymbolsCLI.format_symbol_table(result["data"]["loaded"]))
    for error in result["data"]["errors"]:
        print(f"Skipped row {error['row']}: {error['error']}")
    return None


def _save_symbols(
    service: Symbols, arguments: argparse.Namespace
) -> dict[str, Any] | None:
    """Export the full catalog and report the destination and count."""
    catalog = service.list()
    if not catalog["success"]:
        return catalog
    result = service.save(catalog["data"], arguments.csv_path)
    if not result["success"]:
        return result
    print(result["message"])
    print(result["data"]["path"])
    return None


if __name__ == "__main__":
    from app.workspace.data_manager.data import Data

    data_svc = Data()
    overview = data_svc.overview()
    saved_datasets = data_svc.list()
    print(DataCLI.format_data_dashboard(overview, saved_datasets))
