"""Asynchronous file watcher for lifecycle-managed configuration hot reload."""

import asyncio
import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.composition.engine import CompositionEngine
    from app.kernel.scope import FeatureScope


class ConfigFileWatcher:
    """Watch a configuration file using an explicitly owned lifecycle scope."""

    def __init__(
        self,
        config_path: Path,
        engine: CompositionEngine,
        scope: FeatureScope,
        poll_interval: float = 0.2,
        debounce: float = 0.05,
    ) -> None:
        self._config_path = config_path
        self._engine = engine
        self._scope = scope
        self._poll_interval = poll_interval
        self._debounce = debounce
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._last_mtime: float | None = None
        if self._config_path.is_file():
            self._last_mtime = self._config_path.stat().st_mtime

    @property
    def is_running(self) -> bool:
        return self._running

    async def check_and_reload(self) -> bool:
        """Reload configuration when file modification time advances."""
        if not self._config_path.is_file():
            return False
        current_mtime = self._config_path.stat().st_mtime
        if self._last_mtime is None or current_mtime > self._last_mtime:
            self._last_mtime = current_mtime
            if self._debounce > 0:
                await asyncio.sleep(self._debounce)
            await self._engine.load_and_reconcile_file(self._config_path)
            return True
        return False

    async def _watch_loop(self) -> None:
        while self._running:
            try:
                await self.check_and_reload()
                await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError:
                break
            except Exception:  # noqa: BLE001
                await asyncio.sleep(self._poll_interval)

    def start(self) -> None:
        """Start the watcher as a task owned by the supplied FeatureScope."""
        if self._running:
            return
        self._running = True
        self._task = self._scope.spawn(self._watch_loop(), name="config_file_watcher")

    async def stop(self) -> None:
        """Stop the watcher without closing the caller-owned scope."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
