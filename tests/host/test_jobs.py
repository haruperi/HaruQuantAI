"""Unit tests for Hardware Diagnostics, Process Pool Allocation, and Job Admission Manager.

Description:
    Verifies that app/host/jobs.py provides accurate point-in-time hardware
    diagnostics, bounded process pool allocation, budget-guarded task admission,
    execution state lifecycle management, and cooperative task cancellation.

Purpose:
    FEAT-HOST-JOBS: Hardware Diagnostics, Process Pool, and Job Admission Manager.
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import Future

import pytest
from app.host.jobs import (
    Budget,
    BudgetExceededError,
    CapacityExceededError,
    HardwareDiagnostics,
    JobAccess,
    JobManager,
    JobManagerClosedError,
    create_pool,
    diagnostics,
)


def _sample_compute_task(x: int, y: int) -> int:
    """Top-level test task for multiprocessing execution."""
    return x + y


def _sample_failing_task() -> None:
    """Top-level test task that raises an exception for failure lifecycle testing."""
    raise RuntimeError("Intentional compute error for test")


def _sample_slow_task(duration: float) -> str:
    """Top-level test task that sleeps to test cancellation and timeouts."""
    time.sleep(duration)
    return "completed_slow"


def test_hardware_diagnostics_sampling() -> None:
    """Verify FR-HOST-JOBS-HARDWARE-DIAGNOSTICS collects valid host metrics."""
    diag = diagnostics()

    assert isinstance(diag, HardwareDiagnostics)
    assert diag.cpu_count_logical >= 1
    assert diag.cpu_count_physical >= 1
    assert diag.total_ram_bytes > 0
    assert diag.available_ram_bytes > 0
    assert diag.total_ram_gb > 0.0
    assert diag.available_ram_gb > 0.0
    assert diag.os_platform
    assert diag.python_version == sys.version.split()[0]


def test_process_pool_allocation_and_clamping() -> None:
    """Verify FR-HOST-JOBS-POOL-ALLOCATION allocates bounded process pools."""
    attr = "_max_workers"
    # Explicit valid worker count
    pool_2 = create_pool(max_workers=2)
    assert getattr(pool_2, attr) == 2
    pool_2.shutdown(wait=False)

    # Exceeding system CPU count is clamped to available CPUs
    pool_clamped = create_pool(max_workers=99999)
    assert getattr(pool_clamped, attr) <= 256
    pool_clamped.shutdown(wait=False)

    # Non-positive count defaults to available CPUs
    pool_default = create_pool(max_workers=0)
    assert getattr(pool_default, attr) >= 1
    pool_default.shutdown(wait=False)


def test_budget_validation_and_constraints() -> None:
    """Verify FR-HOST-JOBS-BUDGET-ADMISSION enforces budget bounds."""
    # Valid budget
    budget = Budget(workers=2, memory_bytes=1024, timeout_seconds=10.0)
    budget.validate(max_workers=4, max_memory_bytes=4096)

    # Invalid worker count
    with pytest.raises(ValueError, match="Worker count must be at least 1"):
        Budget(workers=0).validate(max_workers=4, max_memory_bytes=4096)

    # Exceeded worker ceiling
    with pytest.raises(BudgetExceededError, match="exceeds max ceiling"):
        Budget(workers=5).validate(max_workers=4, max_memory_bytes=4096)

    # Negative memory
    with pytest.raises(ValueError, match="cannot be negative"):
        Budget(memory_bytes=-1).validate(max_workers=4, max_memory_bytes=4096)

    # Exceeded memory ceiling
    with pytest.raises(BudgetExceededError, match="exceeds ceiling"):
        Budget(memory_bytes=8192).validate(max_workers=4, max_memory_bytes=4096)

    # Non-positive timeout
    with pytest.raises(ValueError, match="strictly positive"):
        Budget(timeout_seconds=0.0).validate(max_workers=4, max_memory_bytes=4096)


def test_job_admission_capacity_and_ledger() -> None:
    """Verify FR-HOST-JOBS-BUDGET-ADMISSION manages capacity ledger atomically."""
    pool = create_pool(max_workers=2)
    manager = JobManager(pool=pool, max_workers=2, max_memory_bytes=2048)

    try:
        # Submit first job reserving 1 worker and 1024 bytes
        b1 = Budget(workers=1, memory_bytes=1024)
        fut1 = manager.submit("owner-a", _sample_compute_task, 10, 20, budget=b1)

        # Capacity status check
        status = manager.capacity_status()
        assert status["reserved_workers"] >= 0
        assert status["available_workers"] <= 2

        # Second job requesting 2 workers should fail due to capacity exhaustion
        b2 = Budget(workers=2, memory_bytes=512)
        with pytest.raises(CapacityExceededError):
            manager.submit("owner-b", _sample_compute_task, 1, 2, budget=b2)

        # Second job requesting memory exceeding available capacity should fail
        b3 = Budget(workers=1, memory_bytes=1500)
        with pytest.raises(CapacityExceededError):
            manager.submit("owner-c", _sample_compute_task, 1, 2, budget=b3)

        assert fut1.result(timeout=10.0) == 30

        # After completion, reservations are released
        time.sleep(0.1)
        assert manager.reserved_workers == 0
        assert manager.reserved_memory_bytes == 0

    finally:
        manager.close(timeout=2.0)


def test_job_execution_lifecycle_and_failure() -> None:
    """Verify FR-HOST-JOBS-EXECUTION-LIFECYCLE handles success and failure transitions."""
    pool = create_pool(max_workers=2)
    manager = JobManager(pool=pool, max_workers=2, max_memory_bytes=4096)

    try:
        # Successful execution
        fut_ok = manager.submit("tester", _sample_compute_task, 40, 2)
        assert fut_ok.result(timeout=10.0) == 42

        # Failed execution
        fut_err = manager.submit("tester", _sample_failing_task)
        with pytest.raises(RuntimeError, match="Intentional compute error"):
            fut_err.result(timeout=10.0)

        # Ensure manager reservations were cleanly restored
        time.sleep(0.1)
        assert manager.reserved_workers == 0
        assert manager.reserved_memory_bytes == 0

    finally:
        manager.close(timeout=2.0)


def test_cooperative_cancellation_and_owner_close() -> None:
    """Verify FR-HOST-JOBS-COOPERATIVE-CANCELLATION cancels jobs and closes queues."""
    pool = create_pool(max_workers=2)
    manager = JobManager(pool=pool, max_workers=2, max_memory_bytes=4096)

    try:
        # Submit slow tasks
        b = Budget(workers=1, memory_bytes=512)
        fut1 = manager.submit("workspace-alpha", _sample_slow_task, 5.0, budget=b)
        fut2 = manager.submit("workspace-beta", _sample_slow_task, 5.0, budget=b)
        assert isinstance(fut1, Future) and isinstance(fut2, Future)

        # Cancel owner-scoped queue for workspace-alpha
        manager.close(owner="workspace-alpha")

        # Global close
        manager.close()

        # Manager should now reject new submissions
        with pytest.raises(JobManagerClosedError):
            manager.submit("workspace-beta", _sample_compute_task, 1, 1)

    finally:
        manager.close(timeout=2.0)


def test_job_access_capability_facade() -> None:
    """Verify JobAccess facade binds owner context and delegates operations."""
    pool = create_pool(max_workers=2)
    manager = JobManager(pool=pool, max_workers=2, max_memory_bytes=4096)
    access = JobAccess(manager, owner="plugin-dukasc")

    try:
        assert access.owner == "plugin-dukasc"
        fut = access.submit(_sample_compute_task, 15, 25)
        assert fut.result(timeout=10.0) == 40

        access.close()
    finally:
        manager.close(timeout=2.0)
