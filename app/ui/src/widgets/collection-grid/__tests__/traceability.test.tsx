/**
 * Requirement-mapped acceptance tests for FEAT-UI-VIEW_COLLECTIONS.
 *
 * Tests:
 * - AT-UI-VIEW_COLLECTIONS-001: Column sorting/filtering semantics, explicit null/undefined, plugin column recovery.
 * - AT-UI-VIEW_COLLECTIONS-002: Bounded selection token on 1M rows, context menu, keyboard focus, bulk preview.
 * - AT-UI-VIEW_COLLECTIONS-003: Grid states (loading/empty/partial/stale/error/denied), update coalescing.
 */

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import React, { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CollectionGrid } from "../CollectionGrid";
import {
  compareValues,
  type ColumnDefinition,
  type GridError,
  type SelectionToken,
} from "../contracts";
import {
  createEmptySelection,
  createSelectAll,
  generateBulkPreview,
  isRowSelected,
  toggleRowSelection,
} from "../selection";

afterEach(cleanup);

interface TestItem {
  readonly id: string;
  readonly name: string;
  readonly value: number | null;
  readonly createdAt: string | null;
  readonly active: boolean | undefined;
  readonly pluginScore?: number;
}

const SAMPLE_DATA: readonly TestItem[] = [
  { id: "item-1", name: "Alpha", value: 10, createdAt: "2026-01-01T10:00:00Z", active: true },
  { id: "item-2", name: "Beta", value: 2, createdAt: "2025-06-15T08:00:00Z", active: false },
  { id: "item-3", name: "Gamma", value: null, createdAt: null, active: undefined },
  { id: "item-4", name: "Delta", value: 100, createdAt: "2026-03-01T12:00:00Z", active: true },
];

const COLUMNS: readonly ColumnDefinition<TestItem>[] = [
  { id: "name", header: "Name", kind: "text", sortable: true, filterable: true },
  { id: "value", header: "Value", kind: "numeric", sortable: true, filterable: true },
  { id: "createdAt", header: "Created At", kind: "date", sortable: true },
  { id: "active", header: "Active", kind: "boolean" },
  {
    id: "pluginCol",
    header: "Plugin AI",
    kind: "plugin",
    pluginAvailable: false,
    pluginId: "plugin.ml.score",
  },
];

describe("FEAT-UI-VIEW_COLLECTIONS traceability", () => {
  describe("AT-UI-VIEW_COLLECTIONS-001: Column sorting/filtering and explicit states", () => {
    it("preserves owner numeric sorting semantics (2 < 10, not lexicographic 10 < 2)", () => {
      expect(compareValues(2, 10, "numeric", "asc")).toBeLessThan(0);
      expect(compareValues("2", "10", "numeric", "asc")).toBeLessThan(0);
      expect(compareValues(10, 2, "numeric", "asc")).toBeGreaterThan(0);
      expect(compareValues(10, 10, "numeric", "asc")).toBe(0);
    });

    it("preserves owner chronological date sorting semantics", () => {
      const earlier = "2025-06-15T08:00:00Z";
      const later = "2026-01-01T10:00:00Z";
      expect(compareValues(earlier, later, "date", "asc")).toBeLessThan(0);
      expect(compareValues(later, earlier, "date", "asc")).toBeGreaterThan(0);
    });

    it("preserves owner null placement semantics (first vs last)", () => {
      expect(compareValues(null, 42, "numeric", "asc", "first")).toBe(-1);
      expect(compareValues(null, 42, "numeric", "asc", "last")).toBe(1);
      expect(compareValues(42, null, "numeric", "asc", "first")).toBe(1);
      expect(compareValues(42, null, "numeric", "asc", "last")).toBe(-1);
      expect(compareValues(null, null, "numeric", "asc", "first")).toBe(0);
    });

    it("renders explicit null and undefined cell states", () => {
      render(
        <CollectionGrid<TestItem>
          columns={COLUMNS}
          rows={SAMPLE_DATA}
          getRowId={(row) => row.id}
        />,
      );

      const nullCells = screen.getAllByLabelText("null");
      expect(nullCells.length).toBeGreaterThan(0);
      expect(nullCells[0]).toHaveTextContent("—");

      const undefinedCells = screen.getAllByLabelText("undefined");
      expect(undefinedCells.length).toBeGreaterThan(0);
      expect(undefinedCells[0]).toHaveTextContent("N/A");
    });

    it("renders recoverable unavailable state for missing plugin column with onRecover callback", () => {
      const onRecover = vi.fn();
      render(
        <CollectionGrid<TestItem>
          columns={COLUMNS}
          rows={SAMPLE_DATA}
          getRowId={(row) => row.id}
          onRecoverColumn={onRecover}
        />,
      );

      const recoverButtons = screen.getAllByRole("button", {
        name: "Recover plugin column pluginCol",
      });
      expect(recoverButtons.length).toBeGreaterThan(0);

      fireEvent.click(recoverButtons[0]);
      expect(onRecover).toHaveBeenCalledWith("pluginCol");
    });

    it("supports column pin and hide toggles", () => {
      render(
        <CollectionGrid<TestItem>
          columns={COLUMNS}
          rows={SAMPLE_DATA}
          getRowId={(row) => row.id}
        />,
      );

      const pinButton = screen.getByRole("button", { name: "Pin column Name" });
      fireEvent.click(pinButton);

      const hideButton = screen.getByRole("button", { name: "Hide column Name" });
      fireEvent.click(hideButton);

      expect(screen.queryByText("Name")).toBeNull();
    });

    it("handles interactive column header sort clicks", () => {
      const onSortChange = vi.fn();
      render(
        <CollectionGrid<TestItem>
          columns={COLUMNS}
          rows={SAMPLE_DATA}
          getRowId={(row) => row.id}
          sortCriterion={null}
          onSortChange={onSortChange}
        />,
      );

      fireEvent.click(screen.getByText("Value"));
      expect(onSortChange).toHaveBeenCalledWith({
        columnId: "value",
        direction: "asc",
        nulls: "last",
      });
    });
  });

  describe("AT-UI-VIEW_COLLECTIONS-002: Bounded selection token on 1M rows, context menu, keyboard focus", () => {
    it("retains bounded token when selecting 1,000,000 logical rows without allocating 1M browser objects", () => {
      const oneMillion = 1_000_000;
      const allSelected = createSelectAll(oneMillion);

      expect(allSelected.mode).toBe("all_except");
      expect(allSelected.selectedCount).toBe(oneMillion);
      if (allSelected.mode === "all_except") {
        expect(allSelected.excludedIds.size).toBe(0);
      }
      expect(isRowSelected(allSelected, "row-999999")).toBe(true);

      // Exclude 2 rows
      const withExclusions = toggleRowSelection(
        toggleRowSelection(allSelected, "row-42", oneMillion),
        "row-100",
        oneMillion,
      );
      expect(withExclusions.mode).toBe("all_except");
      expect(withExclusions.selectedCount).toBe(999_998);
      if (withExclusions.mode === "all_except") {
        expect(withExclusions.excludedIds.size).toBe(2);
      }
      expect(isRowSelected(withExclusions, "row-42")).toBe(false);
      expect(isRowSelected(withExclusions, "row-100")).toBe(false);
      expect(isRowSelected(withExclusions, "row-101")).toBe(true);
    });

    it("generates query-backed bulk preview without enumerating 1M items", () => {
      const oneMillion = 1_000_000;
      const token = createSelectAll(oneMillion);
      const preview = generateBulkPreview(
        token,
        (index) => `record-${index}`,
        15,
      );

      expect(preview.totalSelected).toBe(oneMillion);
      expect(preview.sampleIds.length).toBe(15);
      expect(preview.sampleIds[0]).toBe("record-0");
      expect(preview.sampleIds[14]).toBe("record-14");
      expect(preview.isCapped).toBe(true);
    });

    it("supports single, toggle, and select-all UI selections", () => {
      const SelectionHarness = (): React.JSX.Element => {
        const [token, setToken] = useState<SelectionToken>(createEmptySelection(SAMPLE_DATA.length));
        return (
          <CollectionGrid<TestItem>
            columns={COLUMNS}
            rows={SAMPLE_DATA}
            getRowId={(row) => row.id}
            selectionToken={token}
            onSelectionChange={setToken}
          />
        );
      };

      render(<SelectionHarness />);

      // Select first row checkbox
      const row1Checkbox = screen.getByLabelText("Select row 1");
      expect(row1Checkbox).not.toBeChecked();

      fireEvent.click(row1Checkbox);
      expect(row1Checkbox).toBeChecked();

      // Click Select All checkbox
      const selectAllCheckbox = screen.getByLabelText("Select all rows");
      fireEvent.click(selectAllCheckbox);
      expect(selectAllCheckbox).toBeChecked();

      // Click Select All again to clear
      fireEvent.click(selectAllCheckbox);
      expect(selectAllCheckbox).not.toBeChecked();
    });

    it("renders context menu on right click and responds to Escape", () => {
      render(
        <CollectionGrid<TestItem>
          columns={COLUMNS}
          rows={SAMPLE_DATA}
          getRowId={(row) => row.id}
        />,
      );

      const firstCell = screen.getByText("Alpha");
      fireEvent.contextMenu(firstCell, { clientX: 200, clientY: 150 });

      const menu = screen.getByRole("menu", { name: "Grid Row Actions" });
      expect(menu).toBeInTheDocument();
      expect(screen.getByRole("menuitem", { name: "Copy Cell" })).toBeInTheDocument();
      expect(screen.getByRole("menuitem", { name: "Filter by Value" })).toBeInTheDocument();
      expect(screen.getByRole("menuitem", { name: "Select All" })).toBeInTheDocument();

      // Escape key dismisses menu
      fireEvent.keyDown(window, { key: "Escape" });
      expect(screen.queryByRole("menu", { name: "Grid Row Actions" })).toBeNull();
    });

    it("supports keyboard navigation across rows and Space toggle", () => {
      const onSelectionChange = vi.fn();
      render(
        <CollectionGrid<TestItem>
          columns={COLUMNS}
          rows={SAMPLE_DATA}
          getRowId={(row) => row.id}
          onSelectionChange={onSelectionChange}
        />,
      );

      const gridContainer = screen.getByRole("region", { name: "Collection Grid" });

      // Arrow down to move focus
      fireEvent.keyDown(gridContainer, { key: "ArrowDown" });
      // Space key to toggle row selection
      fireEvent.keyDown(gridContainer, { key: " " });

      expect(onSelectionChange).toHaveBeenCalled();
    });
  });

  describe("AT-UI-VIEW_COLLECTIONS-003: Grid states and update coalescing", () => {
    it("renders loading state", () => {
      render(
        <CollectionGrid<TestItem>
          columns={COLUMNS}
          rows={[]}
          state="loading"
        />,
      );

      expect(screen.getByText("Loading collection data...")).toBeInTheDocument();
    });

    it("renders empty state", () => {
      render(
        <CollectionGrid<TestItem>
          columns={COLUMNS}
          rows={[]}
          state="empty"
        />,
      );

      expect(screen.getByText("No items available in this collection.")).toBeInTheDocument();
    });

    it("renders partial state banner", () => {
      render(
        <CollectionGrid<TestItem>
          columns={COLUMNS}
          rows={SAMPLE_DATA}
          state="partial"
        />,
      );

      expect(screen.getByText("Notice: Displaying partial dataset stream.")).toBeInTheDocument();
    });

    it("renders stale state banner", () => {
      render(
        <CollectionGrid<TestItem>
          columns={COLUMNS}
          rows={SAMPLE_DATA}
          state="stale"
        />,
      );

      expect(screen.getByText("Notice: Collection snapshot is stale.")).toBeInTheDocument();
    });

    it("renders error state with retry button", () => {
      const onRetry = vi.fn();
      const error: GridError = { code: "ERR_FETCH", message: "Network timeout" };
      render(
        <CollectionGrid<TestItem>
          columns={COLUMNS}
          rows={[]}
          state="error"
          error={error}
          onRetry={onRetry}
        />,
      );

      expect(screen.getByText("Network timeout")).toBeInTheDocument();
      const retryBtn = screen.getByRole("button", { name: "Retry" });
      fireEvent.click(retryBtn);
      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it("renders denied state", () => {
      render(
        <CollectionGrid<TestItem>
          columns={COLUMNS}
          rows={[]}
          state="denied"
        />,
      );

      expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
    });

    it("coalesces rapid scroll/update bursts within updateCoalesceMs window (≤10 visual batches/s)", async () => {
      vi.useFakeTimers();
      const onVisualBatch = vi.fn();

      render(
        <CollectionGrid<TestItem>
          columns={COLUMNS}
          rows={SAMPLE_DATA}
          config={{ updateCoalesceMs: 100 }}
          onVisualBatch={onVisualBatch}
        />,
      );

      const viewport = screen.getByRole("grid");

      // Fire 20 rapid scroll events
      for (let i = 0; i < 20; i += 1) {
        fireEvent.scroll(viewport, { target: { scrollTop: i * 10 } });
      }

      // Immediate: coalescing timer is active, not called 20 times
      expect(onVisualBatch).toHaveBeenCalledTimes(0);

      // Advance clock past the coalescing delay
      vi.advanceTimersByTime(100);

      // Exactly 1 visual batch fired for the burst!
      expect(onVisualBatch).toHaveBeenCalledTimes(1);
      vi.useRealTimers();
    });
  });
});
