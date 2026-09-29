"""Track five host phases and supervise injected lifecycle providers.

Startup tracks per-session readiness separately from process progress.
It publishes real transitions through EventBus and reports
read-only summaries separately. Stage IDs identify host responsibilities;
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

STAGES: tuple[tuple[str, str], ...] = (
    ("runtime", "Configure runtime"),
    ("services", "Initialize host services"),
    ("packages", "Discover and compose packages"),
    ("transport", "Prepare transport"),
    ("serving", "Start serving"),
)
PROVIDER_STAGES = frozenset(("services", "packages"))


class Startup:
    """Maintain host progress independently of any one client's authentication.

    results contains the latest StageResult for every stage. clients holds bounded
    session readiness state, while hooks are explicit trusted implementations.
    No provider is discovered or imported by this class. Callers supply validated
    stage IDs and serialize lifecycle operations on the host loop.
    """

    def __init__(
        self,
        events: EventBus,
        hooks: tuple[LifecycleHook, ...] = (),
        *,
        runtime_started_at: float | None = None,
    ) -> None:
        """Validate hooks and create pending stage records without running work.

        Args:
            runtime_started_at: Monotonic entrypoint start, or this construction time.
            events: Event bus owned by the same host/event loop.
            hooks: Unique named hooks for allowed provider stages; empty means
                normal.

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
        self.started_at = (
            time.monotonic() if runtime_started_at is None else runtime_started_at
        )
        self.events = events
        self.hooks = hooks
        self.state: State = "OFFLINE"
        self.results = {
            key: StageResult(stage=key, label=label) for key, label in STAGES
        }
        self._began: dict[str, float] = {"runtime": self.started_at}
        self._opened: list[LifecycleHook] = []
        self._tasks: set[asyncio.Task[None]] = set()
        self.clients: dict[str, tuple[float, bool]] = {}

    def mark(
        self, stage: str, outcome: Outcome = "succeeded", reason: str = ""
    ) -> None:
        """Replace one stage result, log it, and publish a progress event.

        Only actual transitions are emitted. Running starts the
        monotonic timer; elapsed_ms records milliseconds since that start. This method
        is a transition operation, not a read-only reporting call.

        Args:
            stage: Known STAGES identifier.
            outcome: New outcome; defaults to succeeded.
            reason: Safe machine-readable explanation without secrets.

        Raises:
            KeyError: stage is not registered.
        """
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
        log = logger.debug if outcome == "running" else logger.info
        log(
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

    def log_summary(self, milestone: str) -> None:
        """Report one concise summary without mutating progress."""
        logger.info(
            "Host %s: state=%s; elapsed_ms=%.3f",
            milestone,
            self.state,
            (time.monotonic() - self.started_at) * 1000,
        )
        logger.debug("Boot snapshot: %s", self.snapshot().model_dump())

    def listening(self) -> None:
        """Publish readiness after the server confirms its listening socket."""
        self.state = (
            "DEGRADED"
            if any(r.outcome == "failed" for r in self.results.values())
            else "SERVER_READY"
        )
        self.mark("serving", reason="listening")

    def snapshot(self) -> BootSnapshot:
        """Build an immutable wire snapshot of current lifecycle state.

        Returns:
            BootSnapshot containing process state, current event sequence, and all stage
            results.
        """
        return BootSnapshot(
            schema_version=2,
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
            if self.results[stage].outcome != "failed":
                self.mark(stage, "failed", "operation_failed")
            self.state = "FAILED"
            raise
        if self.results[stage].outcome == "running":
            self.mark(stage)
        return result

    async def providers(self, stage: str) -> None:
        """Execute matching hooks sequentially within their individual time budgets.

        Optional failures mark the stage failed but allow remaining hooks to run.
        Successful interval hooks get supervised repeat tasks. Hooks are tracked before
        execution so partial acquisition can be cleaned up. Cancellation propagates.
        The coordinator invokes each slot once during initialization.

        Args:
            stage: Host phase whose injected hooks should run.

        Raises:
            RuntimeError: A required provider fails or times out; its raw error text is
                suppressed.
        """
        selected = [hook for hook in self.hooks if hook.stage == stage]
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
        if failed:
            self.mark(stage, "failed", "optional_provider_failed")

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
                if self.state in ("SERVER_READY", "DEGRADED"):
                    self.state = "DEGRADED"
                logger.warning("%s Periodic provider %s failed", hook.stage, hook.id)
                self.mark(hook.stage, "failed", "periodic_provider_failed")
                return

    def connected(self, key: str) -> None:
        """Track an authenticated session and mark its update channel connected.

        Starts a readiness deadline for new clients; an expired unready entry can
        reconnect. Does not change process readiness.

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

    def acknowledge(self, key: str) -> None:
        """Record client initialization without changing process readiness."""
        if key not in self.clients:
            raise ValueError("Client must connect before acknowledgment")
        started, ready = self.clients[key]
        if ready:
            return
        if time.monotonic() - started > READINESS_SECONDS:
            raise ValueError("Client readiness deadline expired; reconnect")
        self.clients[key] = (started, True)
        logger.info("Client initialized after %.3f seconds", time.monotonic() - started)

    async def close(self) -> None:
        """Cancel supervised work and close acquired providers in reverse order.

        Awaits cancelled tasks, invokes bounded close callbacks, and logs cleanup
        failures while continuing to other providers. Clears acquired hooks and sets
        STOPPED. Does not close the shared event loop or persistence store.
        """
        tasks = list(self._tasks)
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
