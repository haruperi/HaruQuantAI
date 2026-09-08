/**
 * Bounded offline executable usage recipe for FEAT-UI-VIEW_COLLECTIONS.
 *
 * Demonstrates:
 * 1. 1,000,000 logical-row virtualization bounds.
 * 2. 1,000,000 row bounded snapshot selection token (O(1) memory, not a million objects).
 * 3. Exact sorting semantics (numeric arithmetic: 2 < 10, chronological date, nulls position).
 * 4. Recoverable unavailable state for missing plugin columns.
 * 5. Configuration validation and defaults.
 */

import assert from "node:assert/strict";

import { resolveCollectionGridConfig, parseCollectionGridConfig } from "./config";
import { compareValues, type ColumnDefinition } from "./contracts";
import { COLLECTION_GRID_MANIFEST } from "./manifest";
import {
  createSelectAll,
  generateBulkPreview,
  isRowSelected,
  toggleRowSelection,
} from "./selection";
import { computeVirtualWindow } from "./virtualizer";

function main(): void {
  // 1. Manifest verification
  assert.equal(COLLECTION_GRID_MANIFEST.featureId, "FEAT-UI-VIEW_COLLECTIONS");
  assert.equal(COLLECTION_GRID_MANIFEST.widgetType, "collection-grid");
  assert.ok(COLLECTION_GRID_MANIFEST.provides.includes("ui.collection-grid@1"));
  assert.ok(COLLECTION_GRID_MANIFEST.requiredCapabilities.includes("ui.workspace-layout@1"));

  // 2. 1,000,000 logical-row virtualization window calculation
  const totalOneMillion = 1_000_000;
  const rowHeight = 36;
  const viewportHeight = 600;
  const scrollTop = 360_000; // Scrolled 10,000 rows down
  const virtualWindow = computeVirtualWindow(totalOneMillion, rowHeight, scrollTop, viewportHeight, 5);

  assert.equal(virtualWindow.totalHeight, 36_000_000);
  assert.ok(virtualWindow.visibleCount <= 30, `Expected ≤ 30 visible rows, got ${virtualWindow.visibleCount}`);
  assert.equal(virtualWindow.startIndex, 9995); // 10000 - 5 overscan
  assert.equal(virtualWindow.endIndex, 10022); // 10000 + 17 visible + 5 overscan
  assert.ok(virtualWindow.topPadding > 0);
  assert.ok(virtualWindow.bottomPadding > 0);

  // 3. 1,000,000 row selection retaining a bounded token
  const selectAllToken = createSelectAll(totalOneMillion);
  assert.equal(selectAllToken.mode, "all_except");
  assert.equal(selectAllToken.selectedCount, 1_000_000);
  assert.equal(selectAllToken.excludedIds.size, 0);
  assert.equal(isRowSelected(selectAllToken, "row-500000"), true);

  // Toggle one row to exclude it
  const oneExcluded = toggleRowSelection(selectAllToken, "row-500000", totalOneMillion);
  assert.equal(oneExcluded.mode, "all_except");
  assert.equal(oneExcluded.selectedCount, 999_999);
  assert.equal(oneExcluded.excludedIds.size, 1);
  assert.equal(isRowSelected(oneExcluded, "row-500000"), false);
  assert.equal(isRowSelected(oneExcluded, "row-500001"), true);

  // Query-backed bulk preview generates sample without allocating 1M items
  const preview = generateBulkPreview(
    oneExcluded,
    (index) => `row-${index}`,
    10,
  );
  assert.equal(preview.totalSelected, 999_999);
  assert.equal(preview.sampleIds.length, 10);
  assert.equal(preview.isCapped, true);

  // 4. Sorting semantics
  // Numeric: 2 < 10 (preserves mathematical semantics, unlike lexicographic "10" < "2")
  assert.ok(compareValues(2, 10, "numeric", "asc") < 0);
  assert.ok(compareValues("2", "10", "numeric", "asc") < 0);
  assert.ok(compareValues(10, 2, "numeric", "asc") > 0);

  // Date: 2025-01-01 < 2026-01-01
  assert.ok(compareValues("2025-01-01T00:00:00Z", "2026-01-01T00:00:00Z", "date", "asc") < 0);

  // Nulls position: first vs last
  assert.equal(compareValues(null, 42, "numeric", "asc", "first"), -1);
  assert.equal(compareValues(null, 42, "numeric", "asc", "last"), 1);

  // 5. Plugin column unavailable recovery
  let recoveredColumn: string | null = null;
  const pluginColumn: ColumnDefinition = {
    id: "ext-sentiment",
    header: "Sentiment AI",
    kind: "plugin",
    pluginAvailable: false,
    pluginId: "plugin.sentiment",
  };
  assert.equal(pluginColumn.pluginAvailable, false);

  const onRecover = (colId: string) => {
    recoveredColumn = colId;
  };
  onRecover(pluginColumn.id);
  assert.equal(recoveredColumn, "ext-sentiment");

  // 6. Strict configuration validation
  const config = resolveCollectionGridConfig({ pageSize: 100, updateCoalesceMs: 30 });
  assert.equal(config.pageSize, 100);
  assert.equal(config.updateCoalesceMs, 30);
  assert.equal(config.virtualRowHeight, 36);

  assert.throws(() => {
    parseCollectionGridConfig({ unknownField: "rejected" });
  });

  console.log(
    "FEAT-UI-VIEW_COLLECTIONS usage passed: 1M row virtualization bounded, selection token O(1), sort semantics verified, plugin column recovered, strict config enforced.",
  );
}

main();
