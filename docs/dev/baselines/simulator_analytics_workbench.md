# Baseline — Simulator and Analytics Workbenches Implementation

Work-order source: `docs/dev/HaruQuantAI_V2_Simulator_Analytics_Work_Orders.md`.

The source document `docs/dev/HaruQuantAI_V2_Simulator_Performance_Frontend_Implementation_Plan.md`
is untracked owner-created material. It must not be modified or committed by these tasks.

## Repository State

- Branch: `main`
- Commit: `a10d764cdaadd901abe8d21b333219a534e3a399`
- Commit subject: `fix(tests): resolve pre-push mypy and pytest failures across indicators, trading, api, and simulator`

## Verified Python Baseline (re-run 2026-08-18)

Command:

```powershell
uv run --locked pytest -q
```

Result: exit code 0.

- 6,250 passed
- 21 skipped (credential/opt-in only)
- 1 warning
- Coverage: 86.54% (required threshold 80% reached)

Skips are the 21 baseline credential/opt-in skips (MT5 demo credentials, licensed live
calendar, research live provider, indicators live MT5 usage). No task may increase the
skip count.

## Verified UI Baseline (re-run 2026-08-18)

Commands:

```powershell
cd app/ui
npm run typecheck
npm run lint
npm test -- --run
```

Results:

- `npm run typecheck`: exit code 0.
- `npm run lint`: exit code 0 with five pre-existing
  `react-hooks/exhaustive-deps` and `@next/next/no-img-element` warnings, plus the
  known Next.js `next lint` deprecation notice.
- `npm test -- --run`: 57 test files and 424 tests passed; existing React `act(...)`
  and local-storage warnings remain. No baseline test failure exists.

Baseline warning classes (not failures): React `act(...)`, local storage, Starlette
deprecation, ESLint pre-existing warnings, `next lint` deprecation notice. New tests
must introduce no additional warning class.

## Protected Paths (no task may modify)

| Path | Reason |
|---|---|
| `C:\Users\rharu\AppDev\Haruquant\` | V1 is read-only product reference |
| `docs/dev/HaruQuantAI_V2_Simulator_Performance_Frontend_Implementation_Plan.md` | Owner-created source document |
| `app/services/api/workstation/research/` | Existing `FEAT-API-26` |
| `app/ui/src/features/research/` | Existing `FEAT-UI-28` |
| `app/services/analytics/dashboards/` | Existing `FEAT-ANLT-05` |
| `app/services/api/workstation/simulation/` | Existing routes remain unchanged |
| Applied migration steps | Immutable ledger checksums |

## Rollback

This task only created this baseline file. Rollback is `git revert` of the baseline
commit (or deleting the file); no production code was touched.
