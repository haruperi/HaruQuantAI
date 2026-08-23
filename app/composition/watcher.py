"""Asynchronous file watcher for configuration hot reloading."""

import asyncio
import contextlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from app.composition.logging import compute_secret_fingerprint

if TYPE_CHECKING:
    from app.composition.engine import CompositionEngine
    from app.kernel.scope import FeatureScope

logger = logging.getLogger(__name__)


class ConfigFileWatcher:
    """Watches configuration files for changes and triggers dynamic reconciliation.

    Features:
        - Non-blocking async polling with customizable interval.
        - Debounce handling to prevent partial file read race conditions.
        - Clean task cancellation and disposal.
    """

    def __init__(
        self,
        config_path: Path,
        engine: CompositionEngine,
        scope: FeatureScope | None = None,
        poll_interval: float = 0.2,
        debounce: float = 0.05,
    ) -> None:
        """Initialize configuration file watcher.

        Args:
            config_path: Path to TOML configuration file on disk.
            engine: Target CompositionEngine to notify on changes.
            scope: Optional FeatureScope to manage the background task lifecycle.
            poll_interval: Polling frequency in seconds.
            debounce: Wait duration in seconds before triggering reload.
        """
        self._config_path = config_path
        self._engine = engine
        self._scope = scope
        self._poll_interval = poll_interval
        self._debounce = debounce
        self._config_ref = compute_secret_fingerprint(str(config_path))
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._last_mtime: float | None = None

        if self._config_path.is_file():
            self._last_mtime = self._config_path.stat().st_mtime

    @property
    def is_running(self) -> bool:
        """Return whether the watcher loop is active."""
        return self._running

    async def check_and_reload(self) -> bool:
        """Check if file modification time has changed and trigger reconciliation.

        Returns:
            True if reload was triggered and completed, False otherwise.
        """
        if not self._config_path.is_file():
            return False

        current_mtime = self._config_path.stat().st_mtime
        if self._last_mtime is None or current_mtime > self._last_mtime:
            self._last_mtime = current_mtime
            logger.info(
                "Configuration file modification detected, triggering reload",
                extra={
                    "event": "WATCHER_FILE_CHANGED",
                    "fields": {
                        "config_ref": self._config_ref,
                        "mtime": current_mtime,
                    },
                },
            )
            if self._debounce > 0:
                await asyncio.sleep(self._debounce)
            await self._engine.load_and_reconcile_file(self._config_path)
            return True
        return False

    async def _watch_loop(self) -> None:
        """Background polling loop."""
        while self._running:
            try:
                await self.check_and_reload()
                await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError:
                logger.debug(
                    "Configuration watcher loop cancelled",
                    extra={"event": "WATCHER_LOOP_CANCELLED"},
                )
                break
            except Exception as error:
                logger.warning(
                    "Configuration watcher loop error during poll/reload",
                    exc_info=True,
                    extra={
                        "event": "WATCHER_POLL_ERROR",
                        "fields": {
                            "config_ref": self._config_ref,
                            "error_type": type(error).__name__,
                        },
                    },
                )
                await asyncio.sleep(self._poll_interval)

    def start(self) -> None:
        """Start the background configuration watcher task."""
        if not self._running:
            self._running = True
            logger.info(
                "Starting configuration file watcher",
                extra={
                    "event": "WATCHER_START",
                    "fields": {
                        "config_ref": self._config_ref,
                        "poll_interval": self._poll_interval,
                    },
                },
            )
            if self._scope is not None:
                self._task = self._scope.spawn(
                    self._watch_loop(), name="config_file_watcher"
                )
            else:
                loop = asyncio.get_running_loop()
                self._task = loop.create_task(
                    self._watch_loop(), name="config_file_watcher"
                )

    async def stop(self) -> None:
        """Stop the background watcher task and await its completion."""
        self._running = False
        logger.info(
            "Stopping configuration file watcher",
            extra={
                "event": "WATCHER_STOP",
                "fields": {"config_ref": self._config_ref},
            },
        )
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
