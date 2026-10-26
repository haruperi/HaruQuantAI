# Data Manager activity logs

`app.workspace.data_manager.logs.Logs` maintains process-local download/update
messages and active task progress. Share one instance across workspace producers
and readers. History is empty after restart; no database table is required.

```python
from app.workspace.data_manager import Logs

logs = Logs()  # Publishes through the existing global host event bus.
logs.record_progress("download:AAPL", progress=25, message="Downloaded 2020")
logs.list(task_id="download:AAPL", limit=100, offset=0)
logs.list_active()
logs.record_progress("download:AAPL", progress=100, message="Completed")
logs.clear()
```

All four methods return standard response envelopes. `list()` returns `entries`,
`total`, `limit`, and `offset`; entries are newest first. Each entry contains an
ID, UTC timestamp, task ID, plain-text message, level, and progress. Supported
levels are `debug`, `info`, `warning`, `error`, and `critical`.

Progress from zero to below 100 tracks an active task; 100 or a negative value
removes it. Empty messages update progress without adding history. Clearing
history preserves active tasks and does not cancel work or erase host event replay.

History retains up to 10,000 message characters by default. Oversized messages
are truncated; oldest whole entries are evicted to keep structured records intact.
Active tasks are tracked independently. Pagination supports 1–1,000 entries.

The `logs` event channel carries `datamanager.logs.progress` (workspace marker,
progress update, and optional entry) and `datamanager.logs.cleared` (workspace
marker and cleared count). The constructor accepts an injected `EventBus` for
isolated use. Consumers must render message text safely rather than treating it
as HTML.

The backend owns one instance for its entire lifespan. Stock group background
updates record start, constituent progress, completion and failure/cancellation.
The Log tab loads history and active tasks, subscribes to host events, and polls
for recovery after disconnects. Clear is confirmed by the backend and preserves
active tasks. HTTP routes remain in `app/workspace/data_manager/http.py`:

- `GET /api/v1/data/logs?limit=100&offset=0&task_id=...`
- `GET /api/v1/data/logs/active`
- `POST /api/v1/data/logs/clear`

CLI commands use the running backend and a CLI session from
`HARUQUANTAI_SESSION_TOKEN`. No independent history is created in the CLI process.
Use `uv run python -m app.cli data-manager log list`, `list-active`, or `clear`.
CLI sessions require `data:read` for reads and `data:write` for clear; UI session
permissions continue to apply. No public endpoint records or fabricates progress.
