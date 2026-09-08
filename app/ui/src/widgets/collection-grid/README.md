# Collection Grid (`FEAT-UI-VIEW_COLLECTIONS`)

## Purpose

Own `ui.collection-grid@1`: an accessible, virtualized tabular presentation view over
large typed collections with server-side cursor sorting/filtering, bounded snapshot selection
tokens, context menus, keyboard focus navigation, 6 grid states, and bounded update coalescing.
No numerical or economic policy is reimplemented in the browser.

## Public API

- `COLLECTION_GRID_MANIFEST`: declares typed widget identity, provides `ui.collection-grid@1`,
  requires `ui.workspace-layout@1` and `ui.typed-backend@1`, optional `plugins.render-panels@1`.
- `CollectionGrid`: high-performance React component rendering virtualized collections with
  stable-ID typed columns, column operations (pin, reorder, resize, hide, group), explicit
  `null` (`"—"`) and `undefined` (`"N/A"`) states, recoverable missing plugin column cells,
  floating context menu, and keyboard navigation.
- `CollectionGridFeature`: lifecycle container validating configuration against `collectionGridConfigSchema`
  and rendering explicit configuration errors instead of silently applying invalid state.
- `computeVirtualWindow`: pure deterministic virtualization calculation bounding resident DOM rows
  to the visible viewport slice regardless of whether the collection has 10, 100k, or 1,000,000 rows.
- `SelectionToken` & helpers (`createEmptySelection`, `createSelectAll`, `createSelectAllExcept`,
  `createExplicitSelection`, `isRowSelected`, `toggleRowSelection`, `selectRange`, `generateBulkPreview`):
  bounded selection snapshot model guaranteeing that selecting 1,000,000 rows produces an `all_except`
  token with minimal memory (O(1) memory for full selection), strictly preventing the allocation of a
  million browser objects.
- `compareValues`: pure sorting utility preserving exact owner sorting semantics (arithmetic numeric
  comparison: 2 < 10, chronological ISO date comparison, explicit nulls-first / nulls-last ordering).

## Interactive Usage

1. `FR-TRC-UI-VIEW_COLLECTIONS-001`: Render typed columns with server-side cursor sorting and filtering.
   Numeric sorts preserve magnitude; date sorts preserve chronological order; nulls adhere to policy.
   Missing plugin columns render a recoverable unavailable badge with a recovery action.
2. `FR-TRC-UI-VIEW_COLLECTIONS-002`: Select individual rows, toggle with Ctrl/Cmd, range-select with Shift,
   or select all. Selecting 1,000,000 rows produces a bounded `all_except` token without allocating
   a million objects. Right-click opens an accessible context menu. Navigate with Arrow keys, Home, End,
   and Space to toggle selection.
3. `FR-TRC-UI-VIEW_COLLECTIONS-003`: Displays explicit `idle`, `loading`, `empty`, `partial`, `stale`,
   `error`, and `denied` states. Streaming updates and rapid filter bursts are coalesced within
   `updateCoalesceMs` (default 50 ms) to guarantee at most 10 visual batches per second.

Run the bounded offline companion:

```powershell
npm --prefix app/ui run usage -- src/widgets/collection-grid/_usage.tsx
```

Expected output confirms: 1M row virtualization bounded, selection token O(1), sort semantics verified,
plugin column recovered, strict config enforced. It requires no credentials, network, or live backend.

## Verification

- `__tests__/traceability.test.tsx`: requirement-mapped acceptance tests for `AT-UI-VIEW_COLLECTIONS-001`
  (stable columns, sorting/filtering semantics, explicit null/undefined, column recovery),
  `AT-UI-VIEW_COLLECTIONS-002` (bounded selection token on 1M rows, context menu, keyboard focus),
  and `AT-UI-VIEW_COLLECTIONS-003` (grid states, update coalescing ≤10 batches/s).
- `__tests__/lifecycle.test.tsx`: lifecycle and boundary tests for `ATN-UI-VIEW_COLLECTIONS-001`
  (resident DOM node bounds on 10k, 100k, and 1,000,000 row fixtures) and `ATN-UI-VIEW_COLLECTIONS-002`
  (repeated mount/unmount disposal of timers, scroll listeners, and buffers without memory leaks).

## Failure and Removal

Invalid feature configuration renders an accessible error alert and is rejected. Unmounting the grid
cancels pending coalescing timers, clears scroll and resize listeners, and frees window buffers.
Closing the panel preserves backing domain datasets and server jobs.
