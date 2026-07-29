"""Sandbox port, lease attestation, and its deterministic double.

`FR-AGENTIC-046` requires generation to run in an ephemeral, resource-bounded,
credential-free, network-denied environment. Agentic does not implement that
isolation: it declares the port, checks the lease, and refuses when any
property is unattested. Binding a runtime that genuinely provides those
properties is the composition root's obligation.

That division is stated plainly because it bounds what this feature proves. A
test here shows the agent refuses an under-attested lease. It does not show
that the bound runtime is actually isolated — no in-process double could.

What *is* proved in-process is staging containment, which lives in
`artifact_store.py` and depends on no runtime at all.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.agentic.agents.engineering.coder.schemas import (
    build_sandbox_lease,
    build_sandbox_result,
)
from app.utils import derive_stable_id, get_logger

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.agentic.agents.engineering.coder.schemas import (
        GeneratedFile,
        SandboxLease,
        SandboxResult,
    )

logger = get_logger(__name__)

_DEFAULT_CPU_SECONDS = 30
_DEFAULT_MEMORY_BYTES = 512 * 1024 * 1024
_DEFAULT_WALL_CLOCK_SECONDS = 120


@runtime_checkable
class SandboxPort(Protocol):
    """An isolated, attested environment for exercising generated code."""

    def open_lease(self, task_id: str) -> SandboxLease:
        """Open one ephemeral environment and attest its properties.

        Args:
            task_id: Owning task identity.

        Returns:
            The lease describing what the environment guarantees.
        """
        ...

    def run_files(
        self,
        lease: SandboxLease,
        files: tuple[GeneratedFile, ...],
    ) -> SandboxResult:
        """Exercise the generated files inside the leased environment.

        Args:
            lease: Lease the run executes under.
            files: Generated files to compile and test.

        Returns:
            Evidence of what happened.
        """
        ...

    def close_lease(self, lease: SandboxLease) -> None:
        """Destroy the leased environment.

        Args:
            lease: Lease to destroy.
        """
        ...


def lease_refusal(lease: SandboxLease) -> str | None:
    """Report why a lease is not safe to generate under.

    Args:
        lease: Candidate lease.

    Returns:
        The failing condition, or None when every property is attested.
    """
    unattested = lease.unattested_properties()
    if unattested:
        return f"the sandbox lease does not attest: {', '.join(unattested)}"
    return None


class _DeterministicSandbox:
    """In-process double that attests fully and executes nothing.

    It parses generated files rather than running them, and reports the
    declared tests as observed. It is a fixture for exercising the governed
    path, never an isolation mechanism.
    """

    def __init__(
        self,
        staging_root: str,
        *,
        ephemeral: bool = True,
        credential_free: bool = True,
        network_denied: bool = True,
        failing_paths: tuple[str, ...] = (),
    ) -> None:
        """Configure the deterministic double.

        Args:
            staging_root: Directory the environment may write to.
            ephemeral: Whether to attest ephemerality.
            credential_free: Whether to attest absence of secret material.
            network_denied: Whether to attest blocked egress.
            failing_paths: Declared paths reported as failing to compile.
        """
        self._staging_root = staging_root
        self._ephemeral = ephemeral
        self._credential_free = credential_free
        self._network_denied = network_denied
        self._failing_paths = frozenset(failing_paths)
        self.opened: list[str] = []
        self.closed: list[str] = []

    def open_lease(self, task_id: str) -> SandboxLease:
        """Open one ephemeral environment and attest its properties.

        Args:
            task_id: Owning task identity.

        Returns:
            The lease describing what the environment guarantees.
        """
        lease_id = derive_stable_id("id", f"lease:{task_id}")
        self.opened.append(lease_id)
        return build_sandbox_lease(
            {
                "lease_id": lease_id,
                "ephemeral": self._ephemeral,
                "credential_free": self._credential_free,
                "network_denied": self._network_denied,
                "cpu_seconds": _DEFAULT_CPU_SECONDS,
                "memory_bytes": _DEFAULT_MEMORY_BYTES,
                "wall_clock_seconds": _DEFAULT_WALL_CLOCK_SECONDS,
                "staging_root": self._staging_root,
                "runtime_ref": "agentic.deterministic_sandbox.v1",
            },
        )

    def run_files(
        self,
        lease: SandboxLease,
        files: tuple[GeneratedFile, ...],
    ) -> SandboxResult:
        """Parse the generated files and report the declared tests.

        Args:
            lease: Lease the run executes under.
            files: Generated files to compile and test.

        Returns:
            Evidence of what happened.
        """
        failures = tuple(
            f"{item.relative_path} failed to compile"
            for item in files
            if item.relative_path in self._failing_paths
        )
        test_files = tuple(
            item for item in files if item.relative_path.startswith("tests/")
        )
        return build_sandbox_result(
            {
                "result_id": derive_stable_id("id", f"sandbox:{lease.lease_id}"),
                "lease_id": lease.lease_id,
                "compiled": not failures,
                "tests_run": len(test_files),
                "tests_passed": 0 if failures else len(test_files),
                "duration_seconds": 1,
                "network_attempted": False,
                "diagnostics": failures,
            },
        )

    def close_lease(self, lease: SandboxLease) -> None:
        """Record that the leased environment was destroyed.

        Args:
            lease: Lease to destroy.
        """
        self.closed.append(lease.lease_id)


def build_deterministic_sandbox(
    staging_root: str,
    **attestation: object,
) -> SandboxPort:
    """Build the deterministic in-process sandbox double.

    Args:
        staging_root: Directory the environment may write to.
        **attestation: Optional attestation and failure overrides.

    Returns:
        A port satisfying `SandboxPort`.
    """
    logger.debug("Building the deterministic coder sandbox double")
    return _DeterministicSandbox(staging_root, **attestation)  # type: ignore[arg-type]


class _BoundSandbox:
    """Binds an approved external sandbox runtime.

    Constructed only by an approved composition root. Every isolation property
    this class reports comes from the bound runtime; this module verifies
    nothing about the runtime's claims beyond their presence.
    """

    def __init__(self, runtime: object) -> None:
        """Store the injected sandbox runtime.

        Args:
            runtime: Approved sandbox runtime facade.
        """
        self._runtime = runtime

    def open_lease(self, task_id: str) -> SandboxLease:
        """Open one ephemeral environment through the bound runtime.

        Args:
            task_id: Owning task identity.

        Returns:
            The lease the runtime attested.
        """
        return build_sandbox_lease(self._runtime.open_lease(task_id))  # type: ignore[attr-defined]

    def run_files(
        self,
        lease: SandboxLease,
        files: tuple[GeneratedFile, ...],
    ) -> SandboxResult:
        """Exercise the generated files through the bound runtime.

        Args:
            lease: Lease the run executes under.
            files: Generated files to compile and test.

        Returns:
            The evidence the runtime reported.
        """
        payload: Mapping[str, object] = self._runtime.run_files(  # type: ignore[attr-defined]
            lease.lease_id,
            tuple((item.relative_path, item.content) for item in files),
        )
        return build_sandbox_result(payload)

    def close_lease(self, lease: SandboxLease) -> None:
        """Destroy the leased environment through the bound runtime.

        Args:
            lease: Lease to destroy.
        """
        self._runtime.close_lease(lease.lease_id)  # type: ignore[attr-defined]


def build_bound_sandbox(runtime: object) -> SandboxPort:
    """Build the sandbox port bound to an approved external runtime.

    Args:
        runtime: Approved sandbox runtime facade.

    Returns:
        A port satisfying `SandboxPort`.
    """
    logger.debug("Building the bound coder sandbox")
    return _BoundSandbox(runtime)
