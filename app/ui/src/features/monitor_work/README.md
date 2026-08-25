# Monitor Work (`FEAT-UI-MONITOR_WORK`)

Owning README: `app/ui/README.md` (§4.13). Completable slice:
- `FR-UI-TRACK_PROGRESS` (job progress tracking with indeterminate discrimination)
- `FR-UI-STREAM_ACTIVITY` (ordered activity logging with sequence, gap, and staleness markers)
- `FR-UI-PRESENT_FAILURES` (structured failure presentation with retryability and causal references)

`FR-UI-CONTROL_JOBS` and `FR-UI-NOTIFY_OUTCOMES` are mock-build lines completing at the Stage 14 Orchestration de-mock gate (14.10).

## Capabilities and Widgets Owned

- Capability: `ui.monitor-work@1`
- Widgets:
  - `job_progress` (`app/ui/src/widgets/job_progress`): presents bounded task progress, stages, messages, and structured failure cards when errors occur.
  - `activity_log` (`app/ui/src/widgets/activity_log`): presents ordered event logs, sequence gaps, truncation notifications, and staleness banners.

## State Decision (UI Migration Plan §8.3)

React Context (`MonitorWorkClientProvider`) + local widget state only. No cross-feature shared stores or global state mutation.

## Mock-Stage Streaming Rule (UI Migration Plan §8.4)

At the mock stage, activity logging operates over bounded typed snapshot payloads (`ActivitySnapshot`) with sequence metadata and an explicit "awaiting live feed — de-mock stage" status. No simulated intervals or fake streaming timers are used.

## Usage Evidence

- Model & pure functions: `app/ui/src/features/monitor_work/__tests__/monitor_work.test.tsx`
- Widgets: `app/ui/src/widgets/job_progress/__tests__/job_progress.test.tsx`, `app/ui/src/widgets/activity_log/__tests__/activity_log.test.tsx`
- Python contract & subscription protocol: `tests/ui/unit/test_monitor_work.py`
