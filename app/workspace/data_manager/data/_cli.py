"""CLI formatters and command execution for Data Manager datasets service."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, cast

from .feature import Data

__all__ = [
    "DataCLI",
    "format_data_dashboard",
    "format_dataset_table",
    "main",
]


MAX_UNDERLYING_DISPLAY_LEN: int = 32
TRUNCATE_LEN: int = 30


def _get(item: Any, key: str, default: Any = "") -> Any:
    from collections.abc import Mapping

    if isinstance(item, Mapping):
        return item.get(key, default)
    return getattr(item, key, default)


def format_dataset_table(saved_datasets: Sequence[Any] | Mapping[str, Any]) -> str:
    """Format ASCII table of saved dataset catalog entries."""
    from collections.abc import Mapping

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
    from collections.abc import Mapping

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


def _get_symbols_table() -> Callable[..., str]:
    from app.workspace.data_manager.symbols import format_symbol_table

    return format_symbol_table


def _get_sessions_table() -> Callable[..., str]:
    from app.workspace.data_manager.sessions import format_session_table

    return format_session_table


def _get_baskets_table() -> Callable[..., str]:
    from app.workspace.data_manager.baskets import format_basket_table

    return format_basket_table


def _get_brokers_table() -> Callable[..., str]:
    from app.workspace.data_manager.brokers import format_broker_table

    return format_broker_table


class DataCLI:
    """Table formatters for the Data Manager catalog."""

    @staticmethod
    def format_symbol_table(*args: Any, **kwargs: Any) -> str:
        return _get_symbols_table()(*args, **kwargs)

    @staticmethod
    def format_session_table(*args: Any, **kwargs: Any) -> str:
        return _get_sessions_table()(*args, **kwargs)

    @staticmethod
    def format_basket_table(*args: Any, **kwargs: Any) -> str:
        return _get_baskets_table()(*args, **kwargs)

    @staticmethod
    def format_broker_table(*args: Any, **kwargs: Any) -> str:
        return _get_brokers_table()(*args, **kwargs)

    format_dataset_table = staticmethod(format_dataset_table)
    format_data_dashboard: Callable[..., str] = staticmethod(format_data_dashboard)


def main() -> None:
    """Print the data overview and datasets dashboard."""
    data_svc = Data()
    overview = data_svc.overview()
    saved_datasets = data_svc.list()
    print(DataCLI.format_data_dashboard(overview, saved_datasets))


if __name__ == "__main__":
    main()
