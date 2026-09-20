# Implementation Plan: Workspace Audit Remediation — Example Isolation, Truthful Notification Receipts, FIP-26 Closure

> **Task ID:** `TASK-WORKSPACE-REMEDIATION-1`
> **Iteration:** `1`
> **Branch:** `backend`
> **Baseline Commit:** `663cc6119b5650bd5801410519381f74a442190c` (uncommitted workspace domain on top)

---

## User Review Required

> [!IMPORTANT]
> - **Offline receipt semantics change:** Unconfigured or disabled channels will return `delivered=False` with a `"skipped: ..."` error instead of fabricated `delivered=True`. This is deliberate per FIP-20 fail-closed truthfulness. Pause-gate registration remains unconditional for `require_user_action=True` messages even when delivery is skipped.
> - **WEBHOOK & SOUND dispatchers will be implemented:** Mirroring the Telegram `urllib` POST pattern and Windows `winsound` pattern to satisfy capability claims.
> - **Example Live-DB Removal:** Raw `sqlite3.connect` and feature-authored SQL in `tests/examples/01_workspace.py` will be removed, restoring full offline isolation and preventing any secret exposure.
> - **No commit is made by the agent:** The final commit is executed only after the owner replies `APPROVED: COMMIT` following walkthrough review (`AGENTS.md` §6).

---

## Open Questions

- None. All requirements are bounded and unambiguous.

---

## 1. Goal, Requirements & Usage Evidence

- **Problem Statement & Goal:** Close the final findings of the 2026-09-20 D-WORKSPACE audit re-verification:
  1. The consolidated usage example directly opens the real database via raw `sqlite3.connect` and hand-written SQL (`tests/examples/01_workspace.py:172-190`), breaking determinism/offline isolation and risking credential leakage.
  2. Notification receipts are not truthful: `SOUND` and `WEBHOOK` channels lack dispatch logic, and unconfigured channels report `delivered=True` without sending anything.
  3. Complete FIP-26 evidence chain with task history (`.agents/logs/2026-09-20T000000_workspace-remediation-1/`) and refreshed SHA-256 fingerprints across all 8 acceptance manifests.
- **Ratified Requirements:** `FR-WORKSPACE-004`, `FIP-08`, `FIP-14`, `FIP-20`, `FIP-26`.
- **Usage Evidence:** `tests/examples/01_workspace.py` runs 100% offline and deterministically with zero reference to repository `data/database` paths, printing truthful delivery receipts.

---

## 2. Proposed Changes & Implementation Order

### Component: Notifications Truthfulness

#### [MODIFY] [app/services/workspace/notifications.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/workspace/notifications.py)
- Implement `_dispatch_sound(title, body, metadata) -> tuple[bool, str | None]`: non-blocking `winsound.MessageBeep` on Windows (`sys.platform == "win32"`), or `(False, "skipped: sound channel unavailable on this platform")` on non-Windows.
- Implement `_dispatch_webhook(recipient, title, body, metadata) -> tuple[bool, str | None]`: HTTP POST using `urllib.request.urlopen` (`timeout=10.0`, `# noqa: S310`), handling `HTTPError`/`URLError`/`OSError`/`TimeoutError`. Returns `(False, "skipped: webhook URL not configured")` if URL is empty.
- Update `_dispatch_telegram` and `_dispatch_email`: change unconfigured early-returns from `return True, None` to `return False, "skipped: telegram bot token not configured"` / `return False, "skipped: SMTP server not configured"`.
- Update `send_notification`: add `SOUND` and `WEBHOOK` branches respecting `enable_sound` and `enable_webhooks` config flags. Keep `require_user_action` pause-gate registration unconditional so human-in-the-loop workflows are never blocked.

### Component: Example Isolation

#### [MODIFY] [tests/examples/01_workspace.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/examples/01_workspace.py)
- Delete lines 172-190 (the `db_file` and `sqlite3.connect` loop). Use deterministic default models.
- Remove `import sqlite3`.
- Confirm zero remaining references to repo-relative `data/database/haruquantai.db`.

### Component: Tests & Main Verification

#### [MODIFY] [tests/services/workspace/test_notifications.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/services/workspace/test_notifications.py)
- Update unconfigured receipt assertions to expect `delivered is False` with `"skipped:"` in `receipt.error`.
- Add tests for `SOUND` and `WEBHOOK` dispatchers.
#### [MODIFY] [tests/test_main.py](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/tests/test_main.py)
- Align line 295 `SOUND` receipt assertion to platform-truthful behavior (`delivered is True` on win32; `False` with `"skipped:"` on other platforms).

### Component: Documentation & FIP-26 Evidence

#### [MODIFY] [app/services/workspace/README.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/app/services/workspace/README.md)
- Update `FR-WORKSPACE-004` and Section 9 to describe explicit skipped receipts for unconfigured channels.
#### [NEW] [.agents/logs/2026-09-20T000000_workspace-remediation-1/implementation-plan.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/.agents/logs/2026-09-20T000000_workspace-remediation-1/implementation-plan.md)
- Store canonical task implementation plan.
#### [NEW] [.agents/logs/2026-09-20T000000_workspace-remediation-1/walkthrough.md](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/.agents/logs/2026-09-20T000000_workspace-remediation-1/walkthrough.md)
- Post-implementation walkthrough.
#### [MODIFY] [docs/dev/evidence/features/FEAT-WORKSPACE-*/acceptance.json](file:///c:/Users/rharu/AppDev/HaruQuantAI-backend/docs/dev/evidence/features/)
- Recompute SHA-256 digests across all 8 feature manifests and refresh verification timestamps.

---

## 3. Verification Plan

### Automated Tests
- Run affected notification and lifecycle tests:
  ```bash
  uv run pytest --no-cov tests/services/workspace/test_notifications.py tests/test_main.py -q
  ```
- Run full domain test suite:
  ```bash
  uv run pytest --no-cov tests/contracts/ tests/services/persistence/ tests/services/workspace/ tests/test_main.py -q
  ```

### Usage Evidence Run
- Run example:
  ```bash
  uv run python -m tests.examples.01_workspace
  ```
  Expected: exit 0; 0 occurrences of `data/database/haruquantai.db`; truthful delivery outputs.

### CI Qualification Suite
- Run unified check runner:
  ```bash
  uv run python scripts/ci_check.py
  ```
  Expected: exit 0, Ruff clean, Mypy clean, AST checks passed, coverage >= 80%.

---

## 4. Rollback & Contingency

```text
ALLOWED_WRITE_PATHS:
- app/services/workspace/notifications.py
- app/services/workspace/README.md
- tests/services/workspace/test_notifications.py
- tests/test_main.py
- tests/examples/01_workspace.py
- docs/dev/evidence/features/FEAT-WORKSPACE-SETTINGS/acceptance.json
- docs/dev/evidence/features/FEAT-WORKSPACE-JOBS/acceptance.json
- docs/dev/evidence/features/FEAT-WORKSPACE-SCHEDULER/acceptance.json
- docs/dev/evidence/features/FEAT-WORKSPACE-NOTIFICATIONS/acceptance.json
- docs/dev/evidence/features/FEAT-WORKSPACE-DIAGNOSTICS/acceptance.json
- docs/dev/evidence/features/FEAT-WORKSPACE-WORKERS/acceptance.json
- docs/dev/evidence/features/FEAT-WORKSPACE-RESOURCES/acceptance.json
- docs/dev/evidence/features/FEAT-WORKSPACE-PLUGINS/acceptance.json
- .agents/logs/2026-09-20T000000_workspace-remediation-1/implementation-plan.md
- .agents/logs/2026-09-20T000000_workspace-remediation-1/walkthrough.md
END_ALLOWED_WRITE_PATHS:
```
