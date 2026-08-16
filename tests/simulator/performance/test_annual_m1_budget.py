"""Published annual-M1 and multi-symbol incremental performance gate."""

from __future__ import annotations

import ctypes
import hashlib
import importlib
import os
import platform
import time

from app.services.simulator import (
    create_realism_stream,
    get_realism_performance_budgets,
    sample_realism_stream,
)


def _rss_mib() -> float:
    """Return process peak RSS in MiB using the platform-native unit."""
    if os.name != "nt":
        resource = importlib.import_module("resource")
        value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return value / 1024

    class _ProcessMemoryCounters(ctypes.Structure):
        """Windows PROCESS_MEMORY_COUNTERS layout."""

        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("page_fault_count", ctypes.c_ulong),
            ("peak_working_set_size", ctypes.c_size_t),
            ("working_set_size", ctypes.c_size_t),
            ("quota_peak_paged_pool_usage", ctypes.c_size_t),
            ("quota_paged_pool_usage", ctypes.c_size_t),
            ("quota_peak_non_paged_pool_usage", ctypes.c_size_t),
            ("quota_non_paged_pool_usage", ctypes.c_size_t),
            ("pagefile_usage", ctypes.c_size_t),
            ("peak_pagefile_usage", ctypes.c_size_t),
        ]

    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    get_current_process = ctypes.windll.kernel32.GetCurrentProcess  # type: ignore[attr-defined]
    get_current_process.restype = ctypes.c_void_p
    get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo  # type: ignore[attr-defined]
    get_process_memory_info.argtypes = (
        ctypes.c_void_p,
        ctypes.POINTER(_ProcessMemoryCounters),
        ctypes.c_ulong,
    )
    get_process_memory_info.restype = ctypes.c_int
    handle = get_current_process()
    success = get_process_memory_info(handle, ctypes.byref(counters), counters.cb)
    if not success:
        raise OSError("GetProcessMemoryInfo failed")
    return float(counters.peak_working_set_size) / (1024 * 1024)


def _sample(count: int, symbols: int) -> tuple[float, float, str]:
    """Measure deterministic bounded streaming draws without retaining events."""
    streams = [
        create_realism_stream({"seed": 17, "symbol": f"SYMBOL-{index}"}, "latency")
        for index in range(symbols)
    ]
    before = _rss_mib()
    digest = hashlib.sha256()
    started = time.perf_counter()
    for index in range(count):
        value = sample_realism_stream(streams[index % symbols])
        if index % 10_000 == 0:
            digest.update(str(value).encode())
    elapsed = time.perf_counter() - started
    return elapsed, max(0.0, _rss_mib() - before), digest.hexdigest()


def test_annual_m1_incremental_budget() -> None:
    """FR-SIM-241: enforce published annual and ten-symbol sampling budgets."""
    budgets = get_realism_performance_budgets()
    annual_events = int(str(budgets["annual_m1_events"]))
    multi_events = int(str(budgets["multi_symbol_events"]))
    symbols = int(str(budgets["multi_symbol_count"]))
    annual_elapsed, annual_rss, annual_hash = _sample(annual_events, 1)
    multi_elapsed, multi_rss, multi_hash = _sample(multi_events, symbols)
    profile = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
    }
    print(
        "SIM_PERFORMANCE",
        {
            "profile": profile,
            "annual": {
                "events": annual_events,
                "seconds": annual_elapsed,
                "rss_mib": annual_rss,
                "dataset_hash": annual_hash,
            },
            "multi_symbol": {
                "symbols": symbols,
                "events": multi_events,
                "seconds": multi_elapsed,
                "rss_mib": multi_rss,
                "dataset_hash": multi_hash,
            },
        },
    )
    assert annual_elapsed <= float(budgets["annual_wall_seconds"])
    assert multi_elapsed <= float(budgets["multi_symbol_wall_seconds"])
    assert annual_rss <= float(budgets["peak_rss_growth_mib"])
    assert multi_rss <= float(budgets["peak_rss_growth_mib"])
