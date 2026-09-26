"""Track the 37 boot milestones and supervise injected lifecycle providers.

Startup owns process progress, per-session readiness deadlines, and one shared
restoration task. It publishes real transitions through EventBus and prints
read-only summaries separately. Stage IDs preserve the reference vocabulary;
they do not imply sequential execution or implementation of research features.
Call lifecycle methods on the owning event loop and close before releasing it.
"""

import asyncio
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.host.contracts import BootSnapshot, LifecycleHook, Outcome, StageResult, State
from app.host.events import EventBus
from app.host.logging import get_logger

logger = get_logger(__name__)
MAX_CLIENTS = 256
READINESS_SECONDS = 30

# These are universal lifecycle stages, not a registry of quantitative concepts.
STAGES: tuple[tuple[str, str], ...] = (
    ("B01", "Native process launch"),
    ("B02", "Runtime configuration"),
    ("B03", "Runtime bootstrap"),
    ("B04", "Application main entry"),
    ("B05", "Control server initialization"),
    ("B06", "Client launch"),
    ("B07", "Client layout and window state"),
    ("B08", "Client connection handshake"),
    ("B09", "Hardware diagnostics"),
    ("B10", "Session authentication & User login"),
    ("B11", "Initialization progress display"),
    ("I01", "Initializing database & settings..."),
    ("I02", "Loading customizations..."),
    ("I03", "Compiling snippets..."),
    ("I04", "Loading performance settings..."),
    ("I05", "Initializing building blocks..."),
    ("I06", "Loading plugins..."),
    ("I07", "Initializing stats computer..."),
    ("I08", "Initializing engines..."),
    ("I09", "Loading data..."),
    ("I10", "Loading projects..."),
    ("I11", "Initializing communication channels..."),
    ("I12", "Checking data..."),
    ("I13", "Loading GUI..."),
    ("A01", "Assemble application handlers"),
    ("A02", "Bind application server"),
    ("A03", "Navigate client"),
    ("A04", "Initialize client session"),
    ("A05", "Connect live updates"),
    ("A06", "Load initial state"),
    ("A07", "Assemble navigation and workspaces"),
    ("A08", "Introductory checks"),
    ("A09", "Client readiness acknowledgment"),
    ("A10", "Record client-ready milestone"),
    ("A11", "Restore saved strategies"),
    ("A12", "After-load synchronization"),
    ("A13", "Interactive standby and execution"),
)
PROVIDER_STAGES = frozenset(
    ("I03", "I05", "I07", "I08", "I09", "I10", "I12", "A11", "A12")
)


_PENDING_REASONS = {
    "B06": "awaiting client launch",
    "B07": "awaiting client layout acknowledgment",
    "B08": "awaiting client connection handshake",
    "B10": "session authority ready; awaiting client login",
    "B11": "awaiting client progress-display acknowledgment",
    "A03": "awaiting client navigation",
    "A04": "awaiting client session initialization",
    "A05": "awaiting authenticated live-update connection",
    "A06": "awaiting client initial-state request",
    "A07": "awaiting client navigation/workspace acknowledgment",
    "A08": "awaiting client introductory-check acknowledgment",
    "A09": "awaiting client readiness acknowledgment",
    "A10": "awaiting client-ready milestone",
    "A11": "awaiting client readiness before strategy restoration",
    "A12": "awaiting strategy restoration before after-load synchronization",
    "A13": "awaiting deferred restoration before interactive standby",
}


class Startup:
    """Maintain host progress independently of any one client's authentication.

    results contains the latest StageResult for every stage. clients holds bounded
    session readiness state, while hooks are explicit trusted implementations.
    No provider is discovered or imported by this class. Callers supply validated
    stage IDs and serialize lifecycle operations on the host loop.
    """

    def __init__(self, events: EventBus, hooks: tuple[LifecycleHook, ...] = ()) -> None:
        """Validate hooks and create pending stage records without running work.

        Args:
            events: Event bus owned by the same host/event loop.
            hooks: Unique named hooks for allowed provider stages; empty means
                unavailable.

        Raises:
            ValueError: Hook IDs, stage slots, timeout, or repeat intervals are invalid.
        """
        ids = [hook.id for hook in hooks]
        if len(ids) != len(set(ids)) or any(
            not re.fullmatch(r"[a-z][a-z0-9_.-]{0,99}", h.id)
            or h.stage not in PROVIDER_STAGES
            or h.timeout <= 0
            or (h.interval is not None and h.interval < 1)
            for h in hooks
        ):
            raise ValueError("Invalid lifecycle hooks")
        self.started_at = time.monotonic()
        self.events = events
        self.hooks = hooks
        self.state: State = "OFFLINE"
        self.results = {
            key: StageResult(stage=key, label=label) for key, label in STAGES
        }
        self._began: dict[str, float] = {}
        self._opened: list[LifecycleHook] = []
        self._tasks: set[asyncio.Task[None]] = set()
        self._restore: asyncio.Task[None] | None = None
        self.clients: dict[str, tuple[float, bool]] = {}

    def mark(
        self, stage: str, outcome: Outcome = "succeeded", reason: str = ""
    ) -> None:
        """Replace one stage result, log it, and publish a progress event.

        A non-running outcome first emits running when necessary. Running resets the
        monotonic timer; elapsed_ms records milliseconds since that start. This method
        is a transition operation, not a read-only reporting call.

        Args:
            stage: Known STAGES identifier.
            outcome: New outcome; defaults to succeeded.
            reason: Safe machine-readable explanation without secrets.

        Raises:
            KeyError: stage is not registered.
        """
        if outcome != "running" and self.results[stage].outcome != "running":
            self.mark(stage, "running")
        now = time.monotonic()
        if outcome == "running":
            self._began[stage] = now
        result = self.results[stage].model_copy(
            update={
                "outcome": outcome,
                "reason": reason,
                "elapsed_ms": round((now - self._began.get(stage, now)) * 1000, 3),
            }
        )
        self.results[stage] = result
        logger.info(
            "%s %s: %s",
            stage,
            result.label,
            outcome,
            extra={
                "fields": {
                    "stage": stage,
                    "outcome": outcome,
                    "reason": reason,
                    "elapsed_ms": result.elapsed_ms,
                }
            },
        )
        self.events.publish("boot.progress", result.model_dump())

    def log_summary(self, milestone: str, *, open_browser: bool | None = None) -> None:
        """Log all stage results without changing progress or running providers.

        Includes pending reasons and registered provider counts. Missing restoration
        providers produce scan-unavailable wording, never a fabricated strategy count.
        Does not reset timers, change outcomes, or publish events.

        Args:
            milestone: Caller-supplied log label, normally server_ready or
                client_initialization.
            open_browser: Whether auto-launch was attempted; None omits browser launch
                policy.
        """
        logger.info(
            "Boot summary [%s]: state=%s; stages=%d",
            milestone,
            self.state,
            len(self.results),
        )
        for stage, result in self.results.items():
            reason = result.reason.replace("_", " ") or "completed"
            if result.outcome == "pending":
                reason = (
                    "not reached because boot failed"
                    if self.state == "FAILED"
                    else _PENDING_REASONS.get(stage, "awaiting stage execution")
                )
            elif result.outcome == "running":
                reason = result.reason.replace("_", " ") or "in progress"
            if stage == "B06" and open_browser is not None:
                reason += (
                    "; browser auto-launch attempted"
                    if open_browser
                    else "; browser auto-launch disabled"
                )
            if stage in PROVIDER_STAGES:
                count = sum(hook.stage == stage for hook in self.hooks)
                reason += f"; registered providers={count}"
                if not count:
                    reason += (
                        "; strategy scan unavailable: no restoration provider"
                        if stage == "A11"
                        else "; no implementation registered"
                    )
            logger.info(
                "Boot summary [%s] %s %s: %s - %s",
                milestone,
                stage,
                result.label,
                result.outcome,
                reason,
            )

    def snapshot(self) -> BootSnapshot:
        """Build an immutable wire snapshot of current lifecycle state.

        Returns:
            BootSnapshot containing process state, current event sequence, and all stage
            results.
        """
        return BootSnapshot(
            state=self.state,
            sequence=self.events.sequence,
            stages=tuple(self.results.values()),
        )

    async def step(self, stage: str, action: Callable[[], Awaitable[Any]]) -> Any:
        """Await one operation with observable start and terminal outcomes.

        Cancellation marks cancelled and propagates. Other exceptions mark failed, set
        process state FAILED, and propagate. Resource cleanup belongs to the enclosing
        coordinator, not this helper.

        Args:
            stage: Known stage whose timing and outcome will be recorded.
            action: Async callable invoked exactly once by this call.

        Returns:
            The action result, unchanged.
        """
        self.mark(stage, "running")
        try:
            result = await action()
        except asyncio.CancelledError:
            self.mark(stage, "cancelled", "cancelled")
            raise
        except Exception:
            self.mark(stage, "failed", "operation_failed")
            self.state = "FAILED"
            raise
        self.mark(stage)
        return result

    async def providers(self, stage: str) -> None:
        """Execute matching hooks sequentially within their individual time budgets.

        Optional failures mark the stage failed but allow remaining hooks to run.
        Successful interval hooks get supervised repeat tasks. Hooks are tracked before
        execution so partial acquisition can be cleaned up. Cancellation propagates.
        Calling this method again runs the hooks again; restore owns once-only
        scheduling.

        Args:
            stage: Provider stage to run; absence is logged as unavailable.

        Raises:
            RuntimeError: A required provider fails or times out; its raw error text is
                suppressed.
        """
        selected = [hook for hook in self.hooks if hook.stage == stage]
        self.mark(stage, "running")
        if not selected:
            logger.info(
                "%s %s: registered providers=0; %s",
                stage,
                self.results[stage].label,
                "strategy scan unavailable: no restoration provider"
                if stage == "A11"
                else "no implementation registered",
            )
            self.mark(stage, "unavailable", "no_registered_provider")
            return
        failed = False
        for hook in selected:
            self._opened.append(hook)
            logger.info("%s Provider %s starting", stage, hook.id)
            try:
                async with asyncio.timeout(hook.timeout):
                    await hook.run()
            except asyncio.CancelledError:
                self.mark(stage, "cancelled", "cancelled")
                raise
            except Exception:  # noqa: BLE001 -- isolate failures at the provider boundary.
                failed = True
                logger.warning("%s Provider %s failed", stage, hook.id)
                if hook.required:
                    self.mark(stage, "failed", "required_provider_failed")
                    self.state = "FAILED"
                    raise RuntimeError(
                        "Required provider initialization failed"
                    ) from None
            else:
                logger.info("%s Provider %s completed", stage, hook.id)
                if hook.interval is not None:
                    task = asyncio.create_task(self._periodic(hook))
                    self._tasks.add(task)
                    task.add_done_callback(self._tasks.discard)
        self.mark(
            stage,
            "failed" if failed else "succeeded",
            "optional_provider_failed" if failed else "",
        )

    async def _periodic(self, hook: LifecycleHook) -> None:
        """Repeat a successful hook until cancellation or its first failure.

        Waits before each invocation. A repeat failure logs safely, marks its stage
        failed, and sets process state DEGRADED. Cancellation is propagated to shutdown.

        Args:
            hook: Injected provider with a repeat interval and per-call timeout in
                seconds.
        """
        while True:
            await asyncio.sleep(hook.interval or 1)
            try:
                async with asyncio.timeout(hook.timeout):
                    await hook.run()
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 -- optional task failure is observable, never silent.
                self.state = "DEGRADED"
                logger.warning("%s Periodic provider %s failed", hook.stage, hook.id)
                self.mark(hook.stage, "failed", "periodic_provider_failed")
                return

    def connected(self, key: str) -> None:
        """Track an authenticated session and mark its update channel connected.

        Starts a readiness deadline for new clients; an expired unready entry can
        reconnect. Marks B08/A05 without treating connection as application readiness.

        Args:
            key: Internal session key, not the plaintext bearer credential.

        Raises:
            ValueError: The bounded client collection is full after stale entries are
                pruned.
        """
        if (
            key in self.clients
            and not self.clients[key][1]
            and time.monotonic() - self.clients[key][0] > READINESS_SECONDS
        ):
            del self.clients[key]
        if key not in self.clients:
            if len(self.clients) >= MAX_CLIENTS:
                stale = [
                    k
                    for k, (started, _) in self.clients.items()
                    if time.monotonic() - started > READINESS_SECONDS
                ]
                for old in stale:
                    del self.clients[old]
                if len(self.clients) >= MAX_CLIENTS:
                    raise ValueError("Client capacity exceeded")
            self.clients[key] = (time.monotonic(), False)
        for stage in ("B08", "A05"):
            self.mark(stage)

    def acknowledge(self, key: str) -> None:
        """Accept client readiness and schedule shared restoration once.

        Marks acknowledged client milestones and retains ready status across repeated
        acknowledgments. Creates the restoration task only when none has been created;
        requires a running event loop.

        Args:
            key: Session key previously registered through connected.

        Raises:
            ValueError: An unready client missed the readiness deadline or never
                attached.
        """
        started, ready = self.clients.get(key, (0, False))
        if not ready and time.monotonic() - started > READINESS_SECONDS:
            raise ValueError("Client readiness deadline expired; reconnect")
        self.clients[key] = (started, True)
        for stage in ("B06", "B07", "B11", "A03", "A04", "A07", "A08", "A09", "A10"):
            self.mark(stage, reason="client_acknowledged")
        logger.info(
            "A10 Client ready after %.3f seconds", time.monotonic() - self.started_at
        )
        if self._restore is None:
            self._restore = asyncio.create_task(self.restore())

    async def restore(self) -> None:
        """Run strategy restoration and after-load providers, then report readiness.

        Executes A11/A12 and sets STANDBY or DEGRADED before A13. Required failures
        leave FAILED and produce a complete summary without an unhandled task error.
        Cancellation propagates. Once-only invocation is enforced by acknowledge, not
        by direct calls to this coroutine.
        """
        self.state = "RESTORING"
        try:
            await self.providers("A11")
            await self.providers("A12")
        except Exception:  # noqa: BLE001 -- task boundary preserves fatal state without unobserved exceptions.
            self.state = "FAILED"
            self.log_summary("client_initialization")
            return
        self.state = (
            "DEGRADED"
            if any(result.outcome == "failed" for result in self.results.values())
            else "STANDBY"
        )
        self.mark("A13", reason="host_ready_provider_availability_separate")
        self.log_summary("client_initialization")

    async def close(self) -> None:
        """Cancel supervised work and close acquired providers in reverse order.

        Awaits cancelled tasks, invokes bounded close callbacks, and logs cleanup
        failures while continuing to other providers. Clears acquired hooks and sets
        STOPPED. Does not close the shared event loop or persistence store.
        """
        tasks = list(self._tasks)
        if self._restore is not None:
            tasks.append(self._restore)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for hook in reversed(self._opened):
            if hook.close is not None:
                try:
                    async with asyncio.timeout(hook.timeout):
                        await hook.close()
                    logger.info("Provider %s released", hook.id)
                except Exception:  # noqa: BLE001 -- continue releasing independent resources.
                    logger.error("Provider cleanup failed")  # noqa: TRY400 -- provider exception text may contain secrets.
        self._opened.clear()
        self.state = "STOPPED"
        logger.info("Host shutdown completed")
