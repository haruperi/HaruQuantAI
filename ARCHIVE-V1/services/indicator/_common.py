"""Public indicator tools for HaruQuant.

This module exposes a small, agent-friendly facade over `app.services.indicator`.
The implementation remains in `services`; functions here provide stable names,
plain parameters, and docstrings suitable for application code and agent tool
registration.

The flat public API mirrors the conventions used by `app.services.data`: discovery
helpers such as `list_indicators()`, dynamic lookup through `indicator()`, and
bulk execution through `run_indicators()`. Individual indicator names such as
`ema`, `sma`, `rsi`, `fvg`, and `ob` resolve lazily to callable
private runner objects that support both `tool.ema(data, period)` and
`tool.ema.run(data, period)`.

Public indicator discovery and execution functions:
    list_indicators: List native and SMC indicators matching a glob pattern.
    indicator: Resolve a named indicator or pandas-ta indicator wrapper.
    run_indicators: Run a group or glob pattern of indicators over market data.

Public indicator runners:
    ema: Add exponential moving average columns.
    sma: Add simple moving average columns.
    wma: Add weighted moving average columns.
    rsi: Add relative strength index columns.
    bbands: Add Bollinger Bands columns.
    atr: Add average true range columns.
    hurst: Add Hurst exponent columns.
    fvg: Add fair value gap columns.
    ob: Add order block columns.
    bos_choch: Add break-of-structure and change-of-character columns.
    phl: Add previous high/low columns.

Dynamic service fallback:
    __getattr__: Resolve unknown public attributes from `app.services.indicator`.

Underscore-prefixed functions in this module are private implementation helpers
and are not part of the stable public tools API.

Classes and functions:
    list_indicators: Function. Provides list_indicators behavior for indicator workflows.
    indicator: Function. Provides indicator behavior for indicator workflows.
    run_indicators: Function. Provides run_indicators behavior for indicator workflows.
"""

from __future__ import annotations

import fnmatch
import inspect
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, cast

import pandas as pd

from app.services import resolve_service_attr, service_modules
from app.services.indicator.standard import run_indicator_tool

_SERVICE_MODULES = service_modules("app.services.indicator")

_PARAM_ALIASES = {
    "ema": "span",
    "sma": "window",
    "wma": "window",
    "rsi": "period",
    "bbands": "period",
    "atr": "period",
    "hurst": "period",
    "fvg": None,
    "ob": "swing_length",
    "bos_choch": "swing_length",
    "phl": "timeframe",
    "previous_high_low": "timeframe",
}

_ALIASES = {
    "phl": "previous_high_low",
}

_INDICATORS = {
    "ema": "native",
    "sma": "native",
    "wma": "native",
    "rsi": "native",
    "bbands": "native",
    "atr": "native",
    "hurst": "native",
    "fvg": "smc",
    "ob": "smc",
    "bos_choch": "smc",
    "phl": "smc",
}


def _as_frame(data: Any) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data
    frame = getattr(data, "df", None)
    if isinstance(frame, pd.DataFrame):
        return frame
    raise TypeError("Indicator input must be a pandas DataFrame or tool.Data object.")


def _is_many(value: Any) -> bool:
    return isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict))


def _service_function(name: str) -> Callable[..., pd.DataFrame]:
    service_name = _ALIASES.get(name, name)
    impl_name = f"_{service_name}_impl"
    value = resolve_service_attr(impl_name, _SERVICE_MODULES)
    if not callable(value):
        raise TypeError(
            f"Indicator '{name}' resolved to a non-callable service object."
        )
    return cast(Callable[..., pd.DataFrame], value)


@dataclass(frozen=True)
class _IndicatorRunner:
    """Callable facade for one HaruQuant indicator.

    `_IndicatorRunner` is returned by dynamic indicator exports such as
    `tool.ema`, `tool.rsi`, and `tool.ob`. It is intentionally callable so the
    same object works in regular code, VectorBT-style pipelines, and agent tool
    registries that invoke callable objects directly.

    Args:
        name: Public indicator name to resolve from `app.services.indicator`.

    Attributes:
        name: Public indicator name, for example `ema`, `rsi`, or `bos_choch`.
    """

    name: str

    def __call__(self, data: Any, *args: Any, **kwargs: Any) -> pd.DataFrame:
        """Run this indicator over market data.

        Args:
            data: Market data as a pandas DataFrame or HaruQuant Data-like
                object with a `df` DataFrame attribute.
            *args: Positional arguments forwarded to `run`; the first value is
                typically the period/window.
            **kwargs: Indicator-specific keyword arguments.

        Returns:
            A DataFrame containing the original market data plus any generated
            indicator columns.
        """
        return self.run(data, *args, **kwargs)

    def run(self, data: Any, period: Any = None, **kwargs: Any) -> pd.DataFrame:
        """Run this indicator over market data.

        Args:
            data: Market data as a pandas DataFrame or HaruQuant Data-like
                object with a `df` DataFrame attribute. The frame should include
                the price columns required by the selected indicator, such as
                `close`, or `open`, `high`, `low`, and `close` for OHLC
                indicators.
            period: Optional period, window, span, swing length, or timeframe.
                Lists and tuples run the indicator repeatedly and append one
                output column set per value.
            **kwargs: Indicator-specific options forwarded to the underlying
                service function. `engine` may be `serial` or `threadpool` for
                compatibility with agent and example calls.

        Returns:
            A DataFrame containing the original market data plus any generated
            indicator columns.

        Raises:
            TypeError: If `data` cannot be converted to a DataFrame or the
                resolved service object is not callable.
            ValueError: If an unsupported execution engine is requested.

        Purpose:
            Provide deterministic indicator computation or validation as a focused HaruQuant tool.

        Tool class:
            read_only

        Risk level:
            low

        Approval required:
            none

        Side effects:
            None; returns calculated data or validates inputs only.
        """
        frame = _as_frame(data)
        func = _service_function(self.name)
        service_name = _ALIASES.get(self.name, self.name)
        period_param = _PARAM_ALIASES.get(self.name, "period")

        engine = kwargs.pop("engine", None)
        kwargs.pop("n_workers", None)
        if engine not in (None, "serial", "threadpool"):
            raise ValueError(f"Unsupported indicator engine: {engine}")

        if period is None and period_param and period_param in kwargs:
            period = kwargs.pop(period_param)

        if period_param is None:
            if period is not None and service_name != "fvg":
                kwargs["period"] = period
            return func(frame, **kwargs)

        if period is None:
            return func(frame, **kwargs)

        periods = list(period) if _is_many(period) else [period]
        result = frame.copy()
        for item in periods:
            result = func(result, **{period_param: item}, **kwargs)
        return result


class _TAAccessor:
    """Pandas TA Classic facade that appends generated columns to input data.

    Use `tool.ta.<indicator>(data, period, **kwargs)` to call functions from
    `pandas_ta_classic` through the same DataFrame-in, DataFrame-out pattern as
    native HaruQuant indicators. This object is useful for regular code and for
    agent tools that need dynamic technical indicator access beyond the native
    list.
    """

    def __getattr__(self, name: str) -> Callable[..., pd.DataFrame]:
        """Resolve a pandas-ta indicator by attribute name.

        Args:
            name: Name of a function exposed by `pandas_ta_classic`, for
                example `rsi`, `macd`, or `zlema`.

        Returns:
            A callable that runs the pandas-ta indicator and appends the
            generated Series or DataFrame columns to the input market data.
        """

        def _run(data: Any, period: Any = None, **kwargs: Any) -> pd.DataFrame:
            """Run a dynamically resolved pandas-ta indicator.

            Args:
                data: Market data as a pandas DataFrame or HaruQuant Data-like
                    object with a `df` DataFrame attribute.
                period: Optional indicator length. Iterable values run multiple
                    lengths and append all generated columns.
                **kwargs: Extra keyword arguments accepted by the pandas-ta
                    indicator function.

            Returns:
                A DataFrame containing the original market data plus generated
                pandas-ta columns.
            """
            return self.run(name, data, period=period, **kwargs)

        return _run

    def run(
        self, name: str, data: Any, period: Any = None, **kwargs: Any
    ) -> pd.DataFrame:
        """Run a named pandas-ta indicator over market data.

        Args:
            name: Name of a `pandas_ta_classic` indicator function.
            data: Market data as a pandas DataFrame or HaruQuant Data-like
                object with a `df` DataFrame attribute.
            period: Optional indicator length. Iterable values run multiple
                lengths and append all generated columns.
            **kwargs: Extra keyword arguments accepted by the pandas-ta
                indicator function.

        Returns:
            A DataFrame containing the original market data plus generated
            pandas-ta columns.

        Raises:
            ImportError: If `pandas_ta_classic` is not installed.
            AttributeError: If `name` is not available in `pandas_ta_classic`.
            TypeError: If the pandas-ta indicator returns an unsupported object.

        Purpose:
            Provide deterministic indicator computation or validation as a focused HaruQuant tool.

        Tool class:
            read_only

        Risk level:
            low

        Approval required:
            none

        Side effects:
            None; returns calculated data or validates inputs only.
        """
        try:
            import pandas_ta_classic as ta_lib
        except ImportError as exc:
            raise ImportError(
                "pandas_ta_classic is required for tool.ta indicators."
            ) from exc

        func = getattr(ta_lib, name)
        source = _as_frame(data)
        result = source.copy()
        periods = [period] if period is None or not _is_many(period) else list(period)

        for item in periods:
            call_kwargs = dict(kwargs)
            if item is not None:
                call_kwargs.setdefault("length", item)
            inputs = {
                "close": result["close"] if "close" in result else None,
                "high": result["high"] if "high" in result else None,
                "low": result["low"] if "low" in result else None,
                "open": result["open"] if "open" in result else None,
                "open_": result["open"] if "open" in result else None,
                "volume": result["volume"] if "volume" in result else None,
            }
            parameters = inspect.signature(func).parameters
            accepted = {
                key: value
                for key, value in inputs.items()
                if key in parameters and value is not None
            }
            output = func(**accepted, **call_kwargs)
            if isinstance(output, pd.Series):
                result[output.name or f"{name}_{item}"] = output
            elif isinstance(output, pd.DataFrame):
                for column in output.columns:
                    result[column] = output[column]
            else:
                raise TypeError(
                    f"pandas_ta indicator '{name}' returned unsupported output."
                )

        return result


ta = _TAAccessor()


def _list_indicators_impl(pattern: str = "*") -> list[str]:
    """List public indicator names matching a shell-style pattern.

    This function is agent-tool friendly: pass a simple glob pattern and receive
    a sorted list of indicator names that can be sent to `indicator()` or
    `run_indicators()`.

    Args:
        pattern: Shell-style glob pattern, for example `*ma`, `rsi`, `*bos*`,
            or `*` for all registered native and SMC indicators.

    Returns:
        A sorted list of matching public indicator names.

    Purpose:
        Provide deterministic indicator computation or validation as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; returns calculated data or validates inputs only.
    """
    return sorted(name for name in _INDICATORS if fnmatch.fnmatch(name, pattern))


def _indicator_impl(name: str) -> Any:
    """Resolve an indicator by name.

    Args:
        name: Indicator name. Use a native or SMC name such as `ema`, `rsi`,
            `fvg`, or `bos_choch`; use the `ta:` prefix for pandas-ta
            indicators, for example `ta:rsi` or `ta:macd`.

    Returns:
        A callable runner for native and SMC indicators, or a callable
        pandas-ta wrapper when `name` starts with `ta:`.

    Raises:
        AttributeError: If the indicator name is unknown.

    Purpose:
        Provide deterministic indicator computation or validation as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; returns calculated data or validates inputs only.
    """
    if name.startswith("ta:"):
        return getattr(ta, name.split(":", 1)[1])
    if name in _INDICATORS:
        return _IndicatorRunner(name)
    raise AttributeError(name)


def _run_indicators_impl(
    data: Any, selection: str = "native", period: Any = 20, **kwargs: Any
) -> pd.DataFrame:
    """Run a group or pattern of indicators over market data.

    Args:
        data: Market data as a pandas DataFrame or HaruQuant Data-like object
            with a `df` DataFrame attribute.
        selection: Indicator group or shell-style pattern. Use `native` for
            built-in technical indicators, `smc` for Smart Money Concepts
            indicators, or a glob such as `*ma`.
        period: Period/window/span/swing length applied to each selected
            indicator. For `phl`, non-string periods are converted to `1D`
            because that indicator expects a timeframe string.
        **kwargs: Extra keyword arguments forwarded to each selected indicator.

    Returns:
        A DataFrame containing the original market data plus all generated
        indicator columns.

    Raises:
        TypeError: If `data` cannot be converted to a DataFrame.
        ValueError: If `selection` does not match any registered indicators.

    Purpose:
        Provide deterministic indicator computation or validation as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None; returns calculated data or validates inputs only.
    """
    if selection in {"native", "smc"}:
        names = [name for name, group in _INDICATORS.items() if group == selection]
    else:
        names = _list_indicators_impl(selection)

    if not names:
        raise ValueError(f"No indicators matched selection: {selection}")

    result = _as_frame(data).copy()
    for name in names:
        item_period = "1D" if name == "phl" and not isinstance(period, str) else period
        result = _IndicatorRunner(name).run(result, period=item_period, **kwargs)
    return result


def __getattr__(name: str):
    """Resolve lazy public indicator exports and service fallbacks.

    Args:
        name: Public indicator name or lower-level service attribute name.

    Returns:
        A private indicator runner for registered indicator names, otherwise the
        resolved attribute from `app.services.indicator`.

    Raises:
        AttributeError: If no matching indicator or service attribute exists.
    """
    if name.startswith("_"):
        raise AttributeError(name)
    if name in _PARAM_ALIASES:
        runner = _IndicatorRunner(name)
        globals()[name] = runner
        return runner
    return resolve_service_attr(name, _SERVICE_MODULES)


__all__ = [
    "indicator",
    "list_indicators",
    "run_indicators",
    "ta",
    *_PARAM_ALIASES,
]


def _publish_package_exports() -> None:
    package = sys.modules.get(__package__)
    if package is None:
        return
    for name in __all__:
        if name in globals():
            setattr(package, name, globals()[name])


_publish_package_exports()


def list_indicators(pattern: str = "*", request_id: str | None = None) -> dict:
    """List indicators matching a pattern.

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    return run_indicator_tool(
        "list_indicators",
        lambda: {"indicators": _list_indicators_impl(pattern)},
        request_id=request_id,
    )


def indicator(name: str, request_id: str | None = None) -> dict:
    """Resolve an indicator by name.

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """

    def _operation() -> dict[str, Any]:
        _indicator_impl(name)
        return {"indicator_resolved": True, "name": name}

    return run_indicator_tool("indicator", _operation, request_id=request_id)


def run_indicators(
    data: Any,
    selection: str = "native",
    period: Any = 20,
    request_id: str | None = None,
    **kwargs: Any,
) -> dict:
    """Run a group or pattern of indicators over market data.

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    from app.services.data.frames import _frame_from_records

    def _operation() -> pd.DataFrame:
        frame = (
            _frame_from_records(records=data)
            if isinstance(data, (list, dict))
            else data
        )
        return _run_indicators_impl(frame, selection, period, **kwargs)

    return run_indicator_tool("run_indicators", _operation, request_id=request_id)
