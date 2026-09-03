# Markets

## Purpose

Owns the Markets widget presentation and user interactions for `FEAT-UI-02`.
The backend boundary is the D-IFACE market catalogue gateway
(`interfaces.observe-market-catalogue@1`, served at `GET /api/v1/data/markets`)
with optional live enrichment from the observation stream
(`interfaces.observe-market-data@1`). Neither is imported directly: all
traffic flows through the typed UI client.

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

## D-UI feature shape (pipeline §4.8)

| Artifact | Responsibility |
| --- | --- |
| `manifest.ts` | Typed manifest: owning `FEAT-UI-02`, required `interfaces.observe-market-catalogue@1`, optional `interfaces.observe-market-data@1`, placement, dimensions, subscription, effects, accessibility, removal. |
| `config.ts` | Strict Zod configuration (page size, page cap, settling window, persisted-state schema version); unknown fields throw. |
| `feature.tsx` | Lifecycle adapter: strict configuration lifecycle and the explicit invalid-configuration response; the widget renders its own transport states. |
| `MarketsWidget.tsx` | Focused presentation and interaction, including the explicit `unavailable` state on catalogue 503. |
| `index.ts` | Deliberate public exports only. |

## Public API

- `MarketsFeature` (lifecycle adapter) and `MarketsWidget` through `index.ts`.
- Initialization is strictly phased: all sequential MT5 HTTP history and
  calculation batches finish, a visible settling interval (configured,
  default 10 seconds) elapses, and only then does the widget open its single
  TCP-originated snapshot stream.
- Snapshot events update quote-only fields and preserve every initialized
  technical field.
- Unmounting or hiding the browser document aborts the live stream; returning
  to visibility resumes it without repeating the initial history/calculation
  phase.
- An absent catalogue gateway (HTTP 503) renders the explicit `unavailable`
  state; no rows are invented.

## Verification

- `MarketsWidget.test.tsx` provides focused unit evidence.
- `feature.test.tsx` (lifecycle and availability), `manifest.test.ts`,
  `config.test.ts` provide D-UI evidence.
