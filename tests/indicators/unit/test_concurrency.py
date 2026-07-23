"""NFR-INDI-010: thread safety through immutability and no shared mutable state."""

from concurrent.futures import ThreadPoolExecutor
from types import MappingProxyType

from app.services.indicators import (
    ema,
    get_capability_matrix,
    get_indicator,
    list_indicators,
    rsi,
    sma,
)
from app.services.indicators.core import registry

from tests.indicators.helpers import close_dataset

_PRICES = [
    1.10,
    1.11,
    1.12,
    1.11,
    1.13,
    1.14,
    1.13,
    1.15,
    1.16,
    1.15,
    1.17,
    1.18,
    1.17,
    1.19,
    1.20,
    1.19,
]
_WORKERS = 4
_SUBMISSIONS = 12


def test_parallel_calculations_produce_identical_checksums() -> None:
    """NFR-INDI-010: concurrent calculations are byte-identical to serial ones."""
    data = close_dataset(_PRICES)
    expected = {
        "sma": sma(data, period=3).manifest,
        "ema": ema(data, period=3).manifest,
        "rsi": rsi(data, period=3).manifest,
    }

    def calculate(indicator_id: str) -> tuple[str, str, str]:
        """Calculate one indicator and return its identity material.

        Args:
            indicator_id: One of ``sma``, ``ema``, or ``rsi``.

        Returns:
            The indicator ID, its output checksum, and its parameter hash.
        """
        functions = {"sma": sma, "ema": ema, "rsi": rsi}
        result = functions[indicator_id](data, period=3)
        return (
            indicator_id,
            result.manifest.output_checksum,
            result.manifest.parameter_hash,
        )

    requests = ["sma", "ema", "rsi"] * (_SUBMISSIONS // 3)
    with ThreadPoolExecutor(max_workers=_WORKERS) as pool:
        outcomes = list(pool.map(calculate, requests))

    assert len(outcomes) == _SUBMISSIONS
    for indicator_id, output_checksum, parameter_hash in outcomes:
        assert output_checksum == expected[indicator_id].output_checksum
        assert parameter_hash == expected[indicator_id].parameter_hash


def test_parallel_calculations_do_not_mutate_shared_input() -> None:
    """NFR-INDI-010: the shared input dataset survives concurrent reads intact."""
    data = close_dataset(_PRICES)
    before = data.model_dump(mode="json")

    def calculate(period: int) -> str:
        """Calculate one SMA and return its input checksum.

        Args:
            period: The rolling period to calculate.

        Returns:
            The manifest input checksum.
        """
        return sma(data, period=period).manifest.input_checksum

    with ThreadPoolExecutor(max_workers=_WORKERS) as pool:
        checksums = set(pool.map(calculate, [2, 3, 4, 5] * 3))

    assert len(checksums) == 1
    assert data.model_dump(mode="json") == before


def test_parallel_registry_reads_are_stable() -> None:
    """NFR-INDI-010: registry reads are immutable and stable under concurrency."""
    serial_ids = tuple(spec.indicator_id for spec in list_indicators())
    serial_matrix_size = len(get_capability_matrix())

    def read(_attempt: int) -> tuple[tuple[str, ...], int, str]:
        """Perform one concurrent registry read.

        Args:
            _attempt: Unused submission counter.

        Returns:
            Listed indicator IDs, capability-matrix size, and one resolved ID.
        """
        return (
            tuple(spec.indicator_id for spec in list_indicators()),
            len(get_capability_matrix()),
            get_indicator("sma").indicator_id,
        )

    with ThreadPoolExecutor(max_workers=_WORKERS) as pool:
        outcomes = list(pool.map(read, range(_SUBMISSIONS)))

    for listed, matrix_size, resolved in outcomes:
        assert listed == serial_ids
        assert matrix_size == serial_matrix_size
        assert resolved == "sma"


def test_registry_storage_is_immutable() -> None:
    """NFR-INDI-010: the registry exposes no mutable handle to callers."""
    assert isinstance(registry._REGISTRY, MappingProxyType)
    assert isinstance(registry._REGISTRY_ORDER, tuple)
    assert isinstance(list_indicators(), tuple)
    assert isinstance(get_capability_matrix(), tuple)
