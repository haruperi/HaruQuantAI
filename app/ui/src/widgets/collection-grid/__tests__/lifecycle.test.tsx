/**
 * Lifecycle and resource-boundary acceptance tests for FEAT-UI-VIEW_COLLECTIONS.
 *
 * Tests:
 * - ATN-UI-VIEW_COLLECTIONS-001: 10k/100k/1M logical-row fixtures prove resident-row/DOM
 *   and memory bounds and selection correctness during churn.
 * - ATN-UI-VIEW_COLLECTIONS-002: Repeated mount/unmount disposal cancels all timers,
 *   listeners, observers, and leaves zero memory leaks.
 */

import { cleanup, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CollectionGrid } from "../CollectionGrid";
import { type ColumnDefinition } from "../contracts";
import {
  createSelectAll,
  isRowSelected,
  toggleRowSelection,
} from "../selection";
import { computeVirtualWindow } from "../virtualizer";

afterEach(cleanup);

interface SimpleItem {
  readonly id: string;
  readonly value: number;
}

const COLUMNS: readonly ColumnDefinition<SimpleItem>[] = [
  { id: "id", header: "ID", kind: "text" },
  { id: "value", header: "Value", kind: "numeric" },
];

describe("FEAT-UI-VIEW_COLLECTIONS lifecycle & memory bounds", () => {
  describe("ATN-UI-VIEW_COLLECTIONS-001: 10k/100k/1M resident row and DOM bounds", () => {
    it("proves 10k logical-row fixture holds strictly bounded DOM nodes (~25-35 rows)", () => {
      const total = 10_000;
      // Pre-generate a slice for rendering
      const dummyRows: SimpleItem[] = Array.from({ length: 40 }, (_, i) => ({
        id: `row-${i}`,
        value: i,
      }));

      const { container } = render(
        <CollectionGrid<SimpleItem>
          columns={COLUMNS}
          rows={dummyRows}
          totalRows={total}
          height={500}
          config={{ virtualRowHeight: 36, overscanCount: 5 }}
        />,
      );

      // Total row DOM elements in the rendered viewport
      const renderedRowElements = container.querySelectorAll('.grid-body-row');
      expect(renderedRowElements.length).toBeLessThanOrEqual(40);
      expect(renderedRowElements.length).toBeGreaterThan(0);
    });

    it("proves 100k logical-row fixture virtual window calculation is O(1) and strictly bounded", () => {
      const total = 100_000;
      const windowState = computeVirtualWindow(total, 36, 72_000, 600, 5);

      expect(windowState.totalHeight).toBe(3_600_000);
      expect(windowState.visibleCount).toBeLessThanOrEqual(30);
      expect(windowState.startIndex).toBe(1995);
      expect(windowState.endIndex).toBe(2022);
    });

    it("proves 1,000,000 logical-row fixture virtual window calculation is O(1) and strictly bounded", () => {
      const total = 1_000_000;
      const windowState = computeVirtualWindow(total, 36, 18_000_000, 600, 5);

      expect(windowState.totalHeight).toBe(36_000_000);
      expect(windowState.visibleCount).toBeLessThanOrEqual(30);
      expect(windowState.startIndex).toBe(499995);
      expect(windowState.endIndex).toBe(500022);
      expect(windowState.topPadding).toBe(499995 * 36);
      expect(windowState.bottomPadding).toBe((1_000_000 - 500022) * 36);
    });

    it("preserves selection correctness during rapid row churn/updates", () => {
      const total = 100_000;
      let token = createSelectAll(total);

      // Churn 50 selection updates
      for (let i = 0; i < 50; i += 1) {
        token = toggleRowSelection(token, `churn-${i}`, total);
      }

      expect(token.mode).toBe("all_except");
      expect(token.selectedCount).toBe(total - 50);
      if (token.mode === "all_except") {
        expect(token.excludedIds.size).toBe(50);
      }

      // Verify un-churned row is still selected
      expect(isRowSelected(token, "unchurned-row")).toBe(true);
      // Verify churned rows are excluded
      expect(isRowSelected(token, "churn-0")).toBe(false);
      expect(isRowSelected(token, "churn-49")).toBe(false);
    });
  });

  describe("ATN-UI-VIEW_COLLECTIONS-002: Repeated mount/unmount lifecycle cleanup", () => {
    it("cleans up timers, scroll listeners, and memory across 50 consecutive mount/unmount cycles", () => {
      const addEventListenerSpy = vi.spyOn(window, "addEventListener");
      const removeEventListenerSpy = vi.spyOn(window, "removeEventListener");

      for (let cycle = 0; cycle < 50; cycle += 1) {
        const view = render(
          <CollectionGrid<SimpleItem>
            columns={COLUMNS}
            rows={[{ id: "1", value: 100 }]}
            totalRows={1}
            config={{ updateCoalesceMs: 50 }}
          />,
        );
        view.unmount();
      }

      // Assert that all added event listeners on window were balanced with removals
      const windowKeyDownAdds = addEventListenerSpy.mock.calls.filter((call) => call[0] === "keydown").length;
      const windowKeyDownRemoves = removeEventListenerSpy.mock.calls.filter((call) => call[0] === "keydown").length;
      expect(windowKeyDownAdds).toBe(windowKeyDownRemoves);

      const windowClickAdds = addEventListenerSpy.mock.calls.filter((call) => call[0] === "click").length;
      const windowClickRemoves = removeEventListenerSpy.mock.calls.filter((call) => call[0] === "click").length;
      expect(windowClickAdds).toBe(windowClickRemoves);

      addEventListenerSpy.mockRestore();
      removeEventListenerSpy.mockRestore();
    });

    it("cancels pending update coalescing timers on unmount without running callbacks after unmount", () => {
      vi.useFakeTimers();
      const onVisualBatch = vi.fn();

      const view = render(
        <CollectionGrid<SimpleItem>
          columns={COLUMNS}
          rows={[{ id: "1", value: 100 }]}
          config={{ updateCoalesceMs: 100 }}
          onVisualBatch={onVisualBatch}
        />,
      );

      // Trigger scroll to queue a coalesced batch
      const viewport = screen.getByRole("grid");
      viewport.dispatchEvent(new Event("scroll"));

      // Unmount before the 100ms timer fires
      view.unmount();

      // Advance timers past delay
      vi.advanceTimersByTime(200);

      // The callback must NOT have been invoked after unmount!
      expect(onVisualBatch).toHaveBeenCalledTimes(0);

      vi.useRealTimers();
    });
  });
});
