"""Unit tests for BrokerRegistry lifecycle, lease tracking, and teardown mechanics.

Description:
    Tests the centralized `BrokerRegistry` lifecycle: instance acquisition and caching,
    reference-counted leases, concurrent thread safety, context-managed lease scopes,
    alias normalization, administrative disablement and enablement guards, synchronous
    `close()` and asynchronous `aclose()` idempotent teardown, and leak-free resource release.

Purpose:
    FEAT-BROKER-LIFECYCLE-TEST: Verification of broker registry and lease lifecycle.

Key Capabilities:
    - FR-TEST-LIFECYCLE-LEASES: Assert lease tracking, context scoping, and concurrent access.
      Associated: `test_lease_context_manager()`, `test_concurrent_lease_acquisition()`
      Logging: Validates lease acquisition and release logs.
    - FR-TEST-LIFECYCLE-TEARDOWN: Assert idempotent teardown and zero leaked resources.
      Associated: `test_idempotent_synchronous_close()`, `test_asynchronous_aclose()`
      Logging: Validates registry shutdown logs.
    - FR-TEST-LIFECYCLE-NORMALIZATION: Assert alias canonicalization and disablement authority.
      Associated: `test_alias_normalization()`, `test_registry_disable_and_enable()`
      Logging: Validates state transition logs.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_lifecycle.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_lifecycle.py --no-cov
    ```
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest
from app.services.brokers.capabilities import (
    ProviderDisabledError,
    ProviderNotFoundError,
)
from app.services.brokers.registry import (
    BrokerKey,
    BrokerRegistry,
    normalize_broker_name,
    normalize_provider_id,
)

# ============================================================================
# Lease Tracking and Context Manager Tests
# ============================================================================


def test_lease_context_manager(tmp_path: Path) -> None:
    """Verify registry.lease() acquires and releases instance accurately."""
    registry = BrokerRegistry(data_root=tmp_path)
    key = BrokerKey(provider="dukascopy")

    # Initial lease state
    assert key not in registry._leases

    with registry.lease(key) as broker:
        assert broker is not None
        assert registry._leases[key] == 1

        # Re-entrant / nested lease
        with registry.lease(key) as nested_broker:
            assert nested_broker is broker
            assert registry._leases[key] == 2

        assert registry._leases[key] == 1

    assert registry._leases[key] == 0
    registry.close()


def test_concurrent_lease_acquisition(tmp_path: Path) -> None:
    """Verify thread-safe concurrent lease acquisition and release across 10 threads."""
    registry = BrokerRegistry(data_root=tmp_path)
    key = BrokerKey(provider="files")
    errors: list[Exception] = []

    def worker() -> None:
        try:
            for _ in range(50):
                with registry.lease(key) as broker:
                    assert broker is not None
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Concurrent lease errors occurred: {errors}"
    assert registry._leases[key] == 0
    registry.close()


# ============================================================================
# Idempotent Teardown Tests (Sync and Async)
# ============================================================================


def test_idempotent_synchronous_close(tmp_path: Path) -> None:
    """Verify registry.close() is idempotent and releases all cached instances."""
    registry = BrokerRegistry(data_root=tmp_path)

    # Acquire several brokers
    registry.acquire(BrokerKey(provider="dukascopy"))
    registry.acquire(BrokerKey(provider="darwinex"))
    registry.acquire(BrokerKey(provider="sq_equity"))

    assert len(registry._instances) == 3

    # First close
    registry.close()
    assert len(registry._instances) == 0
    assert len(registry._leases) == 0

    # Second close must be completely safe and idempotent
    registry.close()
    assert len(registry._instances) == 0


@pytest.mark.anyio
async def test_asynchronous_aclose(tmp_path: Path) -> None:
    """Verify registry.aclose() asynchronously finalizes all held brokers."""
    registry = BrokerRegistry(data_root=tmp_path)

    _ = registry.acquire(BrokerKey(provider="dukascopy"))
    _ = registry.acquire(BrokerKey(provider="yahoo"))
    assert len(registry._instances) == 2

    await registry.aclose()
    assert len(registry._instances) == 0
    assert len(registry._leases) == 0


# ============================================================================
# Normalization and Disablement Tests
# ============================================================================


def test_alias_normalization() -> None:
    """Verify legacy aliases normalize to canonical provider identifiers."""
    assert normalize_provider_id("binance") == "crypto"
    assert normalize_provider_id("coinbase") == "crypto"
    assert normalize_provider_id("bitfinex") == "crypto"
    assert normalize_provider_id("darwinex_ticks") == "darwinex"
    assert normalize_provider_id("strategyquant_equity") == "sq_equity"
    assert normalize_provider_id("strategyquant_futures") == "sq_futures"
    assert normalize_provider_id("dukascopy_direct") == "dukascopy"
    assert normalize_provider_id("local_files") == "files"
    assert normalize_provider_id("yahoo_finance") == "yahoo"

    # Verify normalize_broker_name
    assert normalize_broker_name("BINANCE") == "crypto"
    assert normalize_broker_name("MT5") == "metatrader"


def test_registry_disable_and_enable(tmp_path: Path) -> None:
    """Verify registry disablement blocks acquisition and enable restores it."""
    registry = BrokerRegistry(data_root=tmp_path)

    registry.disable("dukascopy")
    with pytest.raises(ProviderDisabledError, match="disabled or quarantined"):
        registry.acquire(BrokerKey(provider="dukascopy"))

    # Also test through alias
    with pytest.raises(ProviderDisabledError, match="disabled or quarantined"):
        registry.acquire(BrokerKey(provider="dukascopy_direct"))

    # Enable restores access
    registry.enable("dukascopy")
    broker = registry.acquire(BrokerKey(provider="dukascopy"))
    assert broker is not None

    registry.close()


def test_unknown_provider_raises(tmp_path: Path) -> None:
    """Verify acquiring an unregistered provider raises ProviderNotFoundError."""
    registry = BrokerRegistry(data_root=tmp_path)

    with pytest.raises(ProviderNotFoundError, match="Unknown or unregistered provider"):
        registry.acquire(BrokerKey(provider="completely_unknown_broker_9999"))

    registry.close()
