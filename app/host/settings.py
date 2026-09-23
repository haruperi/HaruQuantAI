"""File-backed host settings with change events.

Settings live in ``data/user/settings.json`` (owner decision 2026-09-23),
are written atomically (temporary file + replace, so a crash never leaves a
half-written store), and every successful change publishes a
``settings.changed`` event on the host event hub so subscribed clients can
hot-reload — the web-satellite analog of the SQX constants push (ledger
SQX144-EV-000014).

Values are a single shallow JSON object; there is no schema beyond that:
feature-specific interpretation belongs to the features, not the store.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.host.envelope import success_payload
from app.host.events import SETTINGS_CHANNEL
from app.host.http import envelope_response, read_json_body, request_id_of

DEFAULT_SETTINGS_PATH = Path("data/user/settings.json")


class SettingsError(Exception):
    """Raised when settings cannot be loaded (corrupt or unreadable file)."""


class SettingsStore:
    """JSON object settings persisted atomically at one path.

    The store loads once at construction and fails closed on a corrupt or
    non-object file (raising :class:`SettingsError`) rather than silently
    resetting user preferences.
    """

    def __init__(self, path: Path) -> None:
        """Create a store and load any existing file at ``path``.

        Args:
            path: Settings file location; parent directories are created on
                first save, not at construction.

        Raises:
            SettingsError: If the file exists but is unreadable or not a
                JSON object.
        """
        self._path = path
        self._values: dict[str, Any] = {}
        self.load()

    def load(self) -> dict[str, Any]:
        """Load settings from disk; a missing file yields empty settings.

        Raises:
            SettingsError: If the file exists but is not a JSON object.
        """
        if not self._path.is_file():
            self._values = {}
            return self._values
        try:
            raw: Any = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as err:
            raise SettingsError(f"Cannot read settings at {self._path}: {err}") from err
        if not isinstance(raw, dict):
            raise SettingsError(f"Settings at {self._path} must be a JSON object")
        self._values = raw
        return self._values

    def get_all(self) -> dict[str, Any]:
        """Return the current settings values."""
        return dict(self._values)

    def patch(self, changes: dict[str, Any], *, bus: Any = None) -> dict[str, Any]:
        """Shallow-merge ``changes`` into settings, persist, and notify.

        Top-level keys in ``changes`` replace existing values wholesale
        (nested objects are not deep-merged). The save is atomic (temporary
        file + replace).

        Args:
            changes: JSON-object merge patch.
            bus: Optional :class:`~app.host.events.EventBus`; when given, a
                ``settings.changed`` event with the new values is published.

        Returns:
            The full settings values after the merge.
        """
        self._values = {**self._values, **changes}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._path.with_suffix(".json.tmp")
        temp_path.write_text(
            json.dumps(self._values, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        Path(temp_path).replace(self._path)
        if bus is not None:
            bus.publish(SETTINGS_CHANNEL, self.get_all())
        return self.get_all()


async def get_settings(request: Request) -> JSONResponse:
    """Handle ``GET /api/v1/settings``."""
    request_id = request_id_of(request)
    store: SettingsStore = request.app.state.services.settings
    return envelope_response(request_id, success_payload(request_id, store.get_all()))


async def put_settings(request: Request) -> JSONResponse:
    """Handle ``PUT /api/v1/settings`` (JSON object merge patch)."""
    body = await read_json_body(request)
    request_id = request_id_of(request)
    store: SettingsStore = request.app.state.services.settings
    values = store.patch(body, bus=request.app.state.services.events)
    return envelope_response(request_id, success_payload(request_id, values))
