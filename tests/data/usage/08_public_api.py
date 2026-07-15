"""Run package-root DATA API discovery, success, and failure examples."""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services import data
from app.services.data import generate_synthetic_bars, get_tick_data
from app.services.data.contracts import DataError, SyntheticRequest
from app.utils import generate_id, logger


def _synthetic_bar_request() -> SyntheticRequest:
    """Build one bounded request accepted by the package-root facade."""
    logger.info("Building a package-root synthetic-bar request")
    return SyntheticRequest(
        symbol="SYNTHETIC_BTCUSD",
        data_kind="bars",
        timeframe="H1",
        start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        record_count=3,
        method="gbm",
        seed=7,
        parameters={
            "mu": Decimal("0.05"),
            "sigma": Decimal("0.20"),
            "start_val": Decimal(60000),
        },
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def example_public_api_discovery() -> None:
    """Discover only the intentionally supported package-root operations."""
    logger.info("Discovering the approved DATA package-root API")
    if len(data.__all__) != 23:
        raise AssertionError("DATA package-root export count changed unexpectedly")
    if not all(callable(getattr(data, name)) for name in data.__all__):
        raise AssertionError("DATA package root contains a non-callable export")
    logger.info("Approved DATA operations=%s", tuple(data.__all__))


def example_public_api_typed_success() -> None:
    """Generate a typed dataset through the supported package root."""
    logger.info("Calling a successful typed DATA package-root operation")
    dataset = generate_synthetic_bars(_synthetic_bar_request())
    logger.info(
        "Generated schema=%s records=%d", dataset.schema_id, dataset.record_count
    )


def example_public_api_deterministic_failure() -> None:
    """Observe a stable DataError when a facade precondition is violated."""
    logger.info("Calling a DATA operation with an intentionally wrong data kind")
    try:
        get_tick_data(_synthetic_bar_request())
    except DataError as error:
        if error.code != "VALIDATION_FAILED":
            raise AssertionError("unexpected deterministic failure code") from error
        logger.info("Rejected request with stable code=%s", error.code)
    else:
        raise AssertionError("invalid tick request was accepted")


if __name__ == "__main__":
    example_public_api_discovery()
    example_public_api_typed_success()
    example_public_api_deterministic_failure()
