# Markets

## Purpose

Owns the Markets widget presentation and user interactions for `FEAT-UI-02`.
Backend orchestration remains in `app/services/api/workstation/markets/`.

Initial metadata and technical overlays come from bounded HTTP reads. The
owner-supplied Bid is presented as Last Price, raw owner-supplied spread is
converted only for display into integer MT5 points, and a per-symbol Age column
shows elapsed whole seconds from the broker quote time after the first live
snapshot. Initial HTTP-only rows retain an unavailable Age. These replace
separate Bid and Ask columns, while live freshness updates come from one
authenticated multi-symbol SSE connection whose authoritative source is the
one-second MQL5 TCP bridge. Trade text is green for live, yellow for stale, and
red for not-live evidence, with an accessible status label. The widget performs
no market calculation and does not change trading authority based on color.
An active widget reloads authoritative watchlist data after the Watchlist widget
emits a successful-mutation invalidation, causing the existing SSE lifecycle to
replace its backend-to-EA symbol demand without a page refresh.

## Public API

- `MarketsWidget` through `index.ts`.
- Initialization is strictly phased: all sequential MT5 HTTP history and
  calculation batches finish, a visible 10-second settling interval elapses,
  and only then does the widget open its single TCP-originated snapshot stream.
- Snapshot events update quote-only fields and preserve every initialized
  technical field.
- Unmounting or hiding the browser document aborts the live stream; returning
  to visibility resumes it without repeating the initial history/calculation
  phase.

## Verification

- `MarketsWidget.test.tsx` provides focused unit evidence.
