# Phase 0 browser and UI acceptance harness

The executable readiness slice is
`app/ui/e2e/research/phase_00_readiness.spec.ts`. It runs Chromium against the
real Next.js application and a real local ASGI identity provider created by
`tests/harness/phase0_asgi.py`. Both bind loopback only; the provider uses a
temporary SQLite database that is removed when the harness exits.

## Evidence classes

- `REAL_LOCAL_ASGI`: browser traffic crosses the Next.js same-origin rewrite,
  the raw ASGI boundary, the Interfaces identity gateway and the Workspace
  account provider. This label never means external/live provider parity.
- `CONTRACT_STUB`: a component or journey intercepts transport with a declared
  fixture. It may prove UI contract handling but cannot qualify a provider.
- `SCREENSHOT_ONLY`: visual comparison evidence. It cannot substitute for
  contract, provider, authorization, persistence or recovery evidence.

Every future phase checkpoint in `phase-ui-acceptance-matrix.json` is initially
`PLANNED_UNTIL_CHECKPOINT_TASK`. Its owning checkpoint task must record its true
evidence class and cannot claim a nonexistent spec has run.

## Phase 0 readiness oracle

The current harness:

1. opens the dedicated access page;
2. keyboard-reachable registers through the real local provider;
3. verifies the authenticated identity through `/api/v1/auth/me`;
4. selects the Blank template and observes its explicit empty state;
5. reloads and proves both browser session and workspace presentation recovery;
6. checks that visible controls have accessible names and keyboard focus moves to
   an interactive element;
7. records navigation duration and console errors in a bounded JSON attachment.

The structural accessibility check is the Phase 0 bootstrap. Each feature/phase
checkpoint remains responsible for its complete keyboard, focus, label, contrast
and applicable automated accessibility evidence.

## Commands

Build the Next.js production bundle before running the real-provider slice:

```powershell
npm --prefix app/ui run build
npm --prefix app/ui run e2e -- e2e/research/phase_00_readiness.spec.ts
```

The harness has no live-order authority, external network dependency, persistent
workspace, credential requirement or production endpoint fallback.
