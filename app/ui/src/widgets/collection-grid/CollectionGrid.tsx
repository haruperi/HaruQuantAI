"use client";

/**
 * Accessible, virtualized CollectionGrid component for FEAT-UI-VIEW_COLLECTIONS.
 *
 * Implements ARIA grid semantics, server-side cursor sorting & filtering controls,
 * bounded snapshot selection tokens, context menu, keyboard focus, 6 grid states,
 * and bounded update coalescing.
 */

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { resolveCollectionGridConfig, type CollectionGridConfig } from "./config";
import {
  type ColumnDefinition,
  type FilterCriterion,
  type GridContextMenuAction,
  type GridError,
  type GridState,
  type SelectionToken,
  type SortCriterion,
} from "./contracts";
import {
  createEmptySelection,
  createSelectAll,
  isRowSelected,
  selectRange,
  toggleRowSelection,
} from "./selection";
import { computeVirtualWindow } from "./virtualizer";

export interface CollectionGridProps<T = Record<string, unknown>> {
  readonly columns: readonly ColumnDefinition<T>[];
  readonly rows: readonly T[];
  readonly totalRows?: number;
  readonly getRowId?: (row: T, index: number) => string;
  readonly state?: GridState;
  readonly error?: GridError | null;
  readonly sortCriterion?: SortCriterion | null;
  readonly onSortChange?: (sort: SortCriterion) => void;
  readonly filters?: readonly FilterCriterion[];
  readonly onFilterChange?: (filters: readonly FilterCriterion[]) => void;
  readonly selectionToken?: SelectionToken;
  readonly onSelectionChange?: (token: SelectionToken) => void;
  readonly onRetry?: () => void;
  readonly onRecoverColumn?: (columnId: string) => void;
  readonly onRowAction?: (row: T, action: string) => void;
  readonly config?: Partial<CollectionGridConfig>;
  readonly className?: string;
  readonly height?: number;
  readonly onVisualBatch?: (batchCount: number) => void;
}

interface ContextMenuState {
  readonly x: number;
  readonly y: number;
  readonly rowId: string;
  readonly columnId: string;
  readonly cellValue: unknown;
}

export function CollectionGrid<T = Record<string, unknown>>({
  columns: initialColumns,
  rows,
  totalRows: explicitTotalRows,
  getRowId = (_row, index) => String(index),
  state = "idle",
  error = null,
  sortCriterion,
  onSortChange,
  filters = [],
  onFilterChange,
  selectionToken,
  onSelectionChange,
  onRetry,
  onRecoverColumn,
  onRowAction,
  config: configOverrides,
  className = "",
  height = 500,
  onVisualBatch,
}: CollectionGridProps<T>): React.JSX.Element {
  const config = useMemo(
    () => resolveCollectionGridConfig(configOverrides),
    [configOverrides],
  );

  const totalRows = explicitTotalRows ?? rows.length;

  // Local column order / visibility / pinned state
  const [columns, setColumns] = useState<readonly ColumnDefinition<T>[]>(initialColumns);
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const [scrollTop, setScrollTop] = useState(0);
  const [focusedRowIndex, setFocusedRowIndex] = useState(0);
  const [lastAnchorIndex, setLastAnchorIndex] = useState(0);
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);

  // Update coalescing tracking
  const visualBatchesRef = useRef(0);
  const coalesceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setColumns(initialColumns);
  }, [initialColumns]);

  // Active selection token
  const currentSelection: SelectionToken = useMemo(
    () => selectionToken ?? createEmptySelection(totalRows),
    [selectionToken, totalRows],
  );

  // Filter out hidden columns and organize by pinned status
  const visibleColumns = useMemo(() => {
    const active = columns.filter((col) => !col.hidden);
    const left = active.filter((col) => col.pinned === "left");
    const center = active.filter((col) => !col.pinned);
    const right = active.filter((col) => col.pinned === "right");
    return [...left, ...center, ...right];
  }, [columns]);

  // Compute virtual window
  const virtualWindow = useMemo(
    () =>
      computeVirtualWindow(
        totalRows,
        config.virtualRowHeight,
        scrollTop,
        height,
        config.overscanCount,
      ),
    [totalRows, config.virtualRowHeight, scrollTop, height, config.overscanCount],
  );

  // Slice visible rows
  const visibleRows = useMemo(() => {
    if (rows.length === 0) return [];
    const start = Math.min(rows.length, virtualWindow.startIndex);
    const end = Math.min(rows.length, virtualWindow.endIndex);
    return rows.slice(start, end);
  }, [rows, virtualWindow.startIndex, virtualWindow.endIndex]);

  // Coalesce visual batches on scroll or data changes
  const notifyVisualBatch = useCallback(() => {
    if (coalesceTimerRef.current !== null) return;
    coalesceTimerRef.current = setTimeout(() => {
      visualBatchesRef.current += 1;
      onVisualBatch?.(visualBatchesRef.current);
      coalesceTimerRef.current = null;
    }, config.updateCoalesceMs);
  }, [config.updateCoalesceMs, onVisualBatch]);

  // Handle scroll
  const handleScroll = useCallback(
    (event: React.UIEvent<HTMLDivElement>) => {
      setScrollTop(event.currentTarget.scrollTop);
      notifyVisualBatch();
    },
    [notifyVisualBatch],
  );

  // Lifecycle cleanup on unmount
  useEffect(() => {
    return () => {
      if (coalesceTimerRef.current !== null) {
        clearTimeout(coalesceTimerRef.current);
        coalesceTimerRef.current = null;
      }
    };
  }, []);

  // Close context menu on outside click or Escape
  useEffect(() => {
    if (!contextMenu) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setContextMenu(null);
    };
    const handleClick = () => setContextMenu(null);
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("click", handleClick);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("click", handleClick);
    };
  }, [contextMenu]);

  // Column reordering
  const moveColumn = useCallback((fromIndex: number, toIndex: number) => {
    setColumns((prev) => {
      const next = [...prev];
      const [moved] = next.splice(fromIndex, 1);
      if (moved !== undefined) {
        next.splice(toIndex, 0, moved);
      }
      return next;
    });
  }, []);

  // Column resize
  const handleResize = useCallback((columnId: string, newWidth: number) => {
    setColumnWidths((prev) => ({
      ...prev,
      [columnId]: Math.max(40, newWidth),
    }));
  }, []);

  // Column pinning toggle
  const togglePin = useCallback((columnId: string) => {
    setColumns((prev) =>
      prev.map((col) => {
        if (col.id !== columnId) return col;
        const nextPin: "left" | "right" | false =
          col.pinned === false || col.pinned === undefined
            ? "left"
            : col.pinned === "left"
              ? "right"
              : false;
        return { ...col, pinned: nextPin };
      }),
    );
  }, []);

  // Column hide toggle
  const toggleHide = useCallback((columnId: string) => {
    setColumns((prev) =>
      prev.map((col) => (col.id === columnId ? { ...col, hidden: !col.hidden } : col)),
    );
  }, []);

  // Header sort toggle
  const handleSortClick = useCallback(
    (column: ColumnDefinition<T>) => {
      if (!column.sortable) return;
      let nextDirection: "asc" | "desc" = "asc";
      if (sortCriterion?.columnId === column.id) {
        nextDirection = sortCriterion.direction === "asc" ? "desc" : "asc";
      }
      onSortChange?.({
        columnId: column.id,
        direction: nextDirection,
        nulls: nextDirection === "asc" ? "last" : "first",
      });
    },
    [sortCriterion, onSortChange],
  );

  // Selection handlers
  const handleSelectAllToggle = useCallback(() => {
    if (currentSelection.selectedCount === totalRows && totalRows > 0) {
      onSelectionChange?.(createEmptySelection(totalRows));
    } else {
      onSelectionChange?.(createSelectAll(totalRows));
    }
  }, [currentSelection.selectedCount, totalRows, onSelectionChange]);

  const handleRowClick = useCallback(
    (index: number, row: T, event: React.MouseEvent) => {
      const id = getRowId(row, index);
      let nextToken: SelectionToken;

      if (event.shiftKey) {
        const visibleIds = rows.map((r, i) => getRowId(r, i));
        nextToken = selectRange(currentSelection, lastAnchorIndex, index, visibleIds, totalRows);
      } else if (event.ctrlKey || event.metaKey) {
        nextToken = toggleRowSelection(currentSelection, id, totalRows);
        setLastAnchorIndex(index);
      } else {
        nextToken = toggleRowSelection(currentSelection, id, totalRows);
        setLastAnchorIndex(index);
      }

      setFocusedRowIndex(index);
      onSelectionChange?.(nextToken);
    },
    [currentSelection, getRowId, lastAnchorIndex, onSelectionChange, rows, totalRows],
  );

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (rows.length === 0) return;

      if (event.key === "ArrowDown") {
        event.preventDefault();
        setFocusedRowIndex((prev) => Math.min(totalRows - 1, prev + 1));
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        setFocusedRowIndex((prev) => Math.max(0, prev - 1));
      } else if (event.key === "Home") {
        event.preventDefault();
        setFocusedRowIndex(0);
      } else if (event.key === "End") {
        event.preventDefault();
        setFocusedRowIndex(totalRows - 1);
      } else if (event.key === " ") {
        event.preventDefault();
        const row = rows[focusedRowIndex];
        if (row !== undefined) {
          const id = getRowId(row, focusedRowIndex);
          onSelectionChange?.(toggleRowSelection(currentSelection, id, totalRows));
        }
      } else if (event.key === "Enter") {
        event.preventDefault();
        const row = rows[focusedRowIndex];
        if (row !== undefined) {
          onRowAction?.(row, "primary");
        }
      }
    },
    [rows, totalRows, focusedRowIndex, getRowId, currentSelection, onSelectionChange, onRowAction],
  );

  // Right-click context menu
  const handleContextMenu = useCallback(
    (row: T, rowIndex: number, column: ColumnDefinition<T>, event: React.MouseEvent) => {
      event.preventDefault();
      const cellValue = column.accessor ? column.accessor(row) : (row as Record<string, unknown>)[column.id];
      setContextMenu({
        x: event.clientX,
        y: event.clientY,
        rowId: getRowId(row, rowIndex),
        columnId: column.id,
        cellValue,
      });
    },
    [getRowId],
  );

  const handleContextMenuAction = useCallback(
    (action: GridContextMenuAction) => {
      if (!contextMenu) return;
      if (action === "copy_cell") {
        navigator.clipboard?.writeText(String(contextMenu.cellValue ?? ""));
      } else if (action === "select_all") {
        onSelectionChange?.(createSelectAll(totalRows));
      } else if (action === "clear_selection") {
        onSelectionChange?.(createEmptySelection(totalRows));
      } else if (action === "filter_by_value") {
        onFilterChange?.([
          ...filters.filter((f) => f.columnId !== contextMenu.columnId),
          { columnId: contextMenu.columnId, operator: "eq", value: contextMenu.cellValue },
        ]);
      }
      setContextMenu(null);
    },
    [contextMenu, totalRows, onSelectionChange, onFilterChange, filters],
  );

  // Render cell helper
  const renderCellContent = (column: ColumnDefinition<T>, row: T) => {
    // Check if plugin column is unavailable
    if (column.kind === "plugin" && column.pluginAvailable === false) {
      return (
        <span className="column-unavailable" role="status">
          <span className="unavailable-badge">Plugin unavailable</span>
          {onRecoverColumn && (
            <button
              type="button"
              className="recover-column-btn"
              onClick={(e) => {
                e.stopPropagation();
                onRecoverColumn(column.id);
              }}
              aria-label={`Recover plugin column ${column.id}`}
            >
              Recover
            </button>
          )}
        </span>
      );
    }

    const rawValue = column.accessor ? column.accessor(row) : (row as Record<string, unknown>)[column.id];

    if (rawValue === null) {
      return <span className="cell-null" aria-label="null">—</span>;
    }
    if (rawValue === undefined) {
      return <span className="cell-undefined" aria-label="undefined">N/A</span>;
    }

    if (column.format) {
      return column.format(rawValue);
    }

    if (column.kind === "date") {
      const d = rawValue instanceof Date ? rawValue : new Date(String(rawValue));
      return Number.isNaN(d.getTime()) ? String(rawValue) : d.toISOString();
    }

    if (column.kind === "boolean") {
      return rawValue ? "true" : "false";
    }

    return String(rawValue);
  };

  const isAllSelected = totalRows > 0 && currentSelection.selectedCount === totalRows;

  return (
    <div
      className={`collection-grid-container ${className}`}
      style={{ height, display: "flex", flexDirection: "column", position: "relative" }}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      role="region"
      aria-label="Collection Grid"
    >
      {/* State banners */}
      {state === "partial" && (
        <div className="grid-banner grid-banner-partial" role="status">
          Notice: Displaying partial dataset stream.
        </div>
      )}
      {state === "stale" && (
        <div className="grid-banner grid-banner-stale" role="status">
          Notice: Collection snapshot is stale.
        </div>
      )}
      {state === "error" && (
        <div className="grid-banner grid-banner-error" role="alert">
          <span>{error?.message ?? "Failed to load collection."}</span>
          {onRetry && (
            <button type="button" onClick={onRetry} className="retry-btn">
              Retry
            </button>
          )}
        </div>
      )}
      {state === "denied" && (
        <div className="grid-banner grid-banner-denied" role="alert">
          Access Denied: You do not have permissions to view this collection.
        </div>
      )}

      {/* Main Table Container */}
      <div
        ref={scrollContainerRef}
        className="grid-scroll-viewport"
        style={{ flex: 1, overflowY: "auto", overflowX: "auto", position: "relative" }}
        onScroll={handleScroll}
        role="grid"
        aria-rowcount={totalRows}
        aria-colcount={visibleColumns.length + 1}
        aria-multiselectable="true"
      >
        {/* Table Header */}
        <div
          className="grid-header-row"
          role="row"
          style={{
            display: "flex",
            position: "sticky",
            top: 0,
            zIndex: 2,
            background: "var(--background-secondary, #1e222d)",
            borderBottom: "1px solid var(--border-color, #2a2e39)",
            minWidth: "100%",
            width: "max-content",
          }}
        >
          {/* Select All checkbox header */}
          <div
            role="columnheader"
            className="grid-header-cell select-header-cell"
            style={{ width: 44, display: "flex", alignItems: "center", justifyContent: "center" }}
          >
            <input
              type="checkbox"
              aria-label="Select all rows"
              checked={isAllSelected}
              onChange={handleSelectAllToggle}
            />
          </div>

          {visibleColumns.map((col, index) => {
            const width = columnWidths[col.id] ?? col.width ?? 120;
            const isSorted = sortCriterion?.columnId === col.id;
            const sortDir = isSorted ? sortCriterion?.direction : undefined;

            return (
              <div
                key={col.id}
                role="columnheader"
                aria-sort={isSorted ? (sortDir === "asc" ? "ascending" : "descending") : "none"}
                className={`grid-header-cell ${col.sortable ? "sortable" : ""} ${col.pinned ? `pinned-${col.pinned}` : ""}`}
                style={{
                  width,
                  minWidth: col.minWidth ?? 60,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "6px 8px",
                  userSelect: "none",
                  position: col.pinned ? "sticky" : undefined,
                  left: col.pinned === "left" ? 44 : undefined,
                  zIndex: col.pinned ? 3 : 2,
                  background: "var(--background-secondary, #1e222d)",
                }}
              >
                <div
                  style={{ display: "flex", alignItems: "center", gap: 4, cursor: col.sortable ? "pointer" : "default" }}
                  onClick={() => handleSortClick(col)}
                >
                  <span className="column-title">{col.header}</span>
                  {isSorted && (
                    <span className="sort-indicator" aria-hidden="true">
                      {sortDir === "asc" ? " ▲" : " ▼"}
                    </span>
                  )}
                </div>

                <div className="header-actions" style={{ display: "flex", gap: 2 }}>
                  {index > 0 && (
                    <button
                      type="button"
                      className="reorder-left-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        moveColumn(index, index - 1);
                      }}
                      aria-label={`Move column ${col.header} left`}
                      title="Move Left"
                    >
                      ◀
                    </button>
                  )}
                  {index < visibleColumns.length - 1 && (
                    <button
                      type="button"
                      className="reorder-right-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        moveColumn(index, index + 1);
                      }}
                      aria-label={`Move column ${col.header} right`}
                      title="Move Right"
                    >
                      ▶
                    </button>
                  )}
                  <button
                    type="button"
                    className="pin-toggle-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      togglePin(col.id);
                    }}
                    aria-label={`Pin column ${col.header}`}
                    title={col.pinned ? `Pinned (${col.pinned})` : "Pin"}
                  >
                    📌
                  </button>
                  <button
                    type="button"
                    className="hide-toggle-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleHide(col.id);
                    }}
                    aria-label={`Hide column ${col.header}`}
                    title="Hide"
                  >
                    👁️
                  </button>
                  <button
                    type="button"
                    className="resize-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleResize(col.id, width + 20);
                    }}
                    aria-label={`Resize column ${col.header}`}
                    title="Widen"
                  >
                    ↔
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Loading Overlay */}
        {state === "loading" && (
          <div
            className="grid-loading-state"
            role="status"
            aria-busy="true"
            style={{ padding: 24, textAlign: "center" }}
          >
            Loading collection data...
          </div>
        )}

        {/* Empty Overlay */}
        {state === "empty" || (state !== "loading" && totalRows === 0) ? (
          <div
            className="grid-empty-state"
            role="status"
            style={{ padding: 32, textAlign: "center", color: "var(--text-muted, #787b86)" }}
          >
            No items available in this collection.
          </div>
        ) : null}

        {/* Virtualized Body */}
        {state !== "loading" && totalRows > 0 && (
          <div role="rowgroup" style={{ position: "relative", minWidth: "100%", width: "max-content" }}>
            {/* Top spacer */}
            <div style={{ height: virtualWindow.topPadding }} />

            {/* Rendered window rows */}
            {visibleRows.map((row, relativeIndex) => {
              const absoluteIndex = virtualWindow.startIndex + relativeIndex;
              const rowId = getRowId(row, absoluteIndex);
              const isSelected = isRowSelected(currentSelection, rowId);
              const isFocused = focusedRowIndex === absoluteIndex;

              return (
                <div
                  key={rowId}
                  role="row"
                  aria-rowindex={absoluteIndex + 1}
                  aria-selected={isSelected}
                  className={`grid-body-row ${isSelected ? "selected" : ""} ${isFocused ? "focused" : ""}`}
                  style={{
                    display: "flex",
                    height: config.virtualRowHeight,
                    alignItems: "center",
                    borderBottom: "1px solid var(--border-color, #1e222d)",
                    background: isSelected
                      ? "var(--selection-bg, rgba(41, 98, 255, 0.15))"
                      : isFocused
                        ? "var(--focus-bg, rgba(255, 255, 255, 0.04))"
                        : "transparent",
                    cursor: "pointer",
                  }}
                  onClick={(e) => handleRowClick(absoluteIndex, row, e)}
                >
                  {/* Row selection checkbox */}
                  <div
                    role="gridcell"
                    className="grid-cell select-cell"
                    style={{ width: 44, display: "flex", alignItems: "center", justifyContent: "center" }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <input
                      type="checkbox"
                      aria-label={`Select row ${absoluteIndex + 1}`}
                      checked={isSelected}
                      onChange={() => onSelectionChange?.(toggleRowSelection(currentSelection, rowId, totalRows))}
                    />
                  </div>

                  {/* Data cells */}
                  {visibleColumns.map((col, colIndex) => {
                    const width = columnWidths[col.id] ?? col.width ?? 120;
                    return (
                      <div
                        key={col.id}
                        role="gridcell"
                        aria-colindex={colIndex + 2}
                        className={`grid-cell ${col.pinned ? `pinned-${col.pinned}` : ""}`}
                        style={{
                          width,
                          minWidth: col.minWidth ?? 60,
                          padding: "4px 8px",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          position: col.pinned ? "sticky" : undefined,
                          left: col.pinned === "left" ? 44 : undefined,
                          background: col.pinned ? "var(--background-secondary, #1e222d)" : undefined,
                        }}
                        onContextMenu={(e) => handleContextMenu(row, absoluteIndex, col, e)}
                      >
                        {renderCellContent(col, row)}
                      </div>
                    );
                  })}
                </div>
              );
            })}

            {/* Bottom spacer */}
            <div style={{ height: virtualWindow.bottomPadding }} />
          </div>
        )}
      </div>

      {/* Floating Context Menu */}
      {contextMenu && (
        <div
          role="menu"
          aria-label="Grid Row Actions"
          className="grid-context-menu"
          style={{
            position: "fixed",
            left: contextMenu.x,
            top: contextMenu.y,
            zIndex: 9999,
            background: "var(--menu-bg, #1e222d)",
            border: "1px solid var(--border-color, #363c4e)",
            borderRadius: 4,
            boxShadow: "0 4px 12px rgba(0,0,0,0.5)",
            padding: "4px 0",
          }}
        >
          <button
            type="button"
            role="menuitem"
            className="context-menu-item"
            style={{ display: "block", width: "100%", padding: "6px 16px", textAlign: "left", background: "none", border: "none", color: "inherit", cursor: "pointer" }}
            onClick={() => handleContextMenuAction("copy_cell")}
          >
            Copy Cell
          </button>
          <button
            type="button"
            role="menuitem"
            className="context-menu-item"
            style={{ display: "block", width: "100%", padding: "6px 16px", textAlign: "left", background: "none", border: "none", color: "inherit", cursor: "pointer" }}
            onClick={() => handleContextMenuAction("filter_by_value")}
          >
            Filter by Value
          </button>
          <div style={{ height: 1, background: "var(--border-color, #2a2e39)", margin: "4px 0" }} />
          <button
            type="button"
            role="menuitem"
            className="context-menu-item"
            style={{ display: "block", width: "100%", padding: "6px 16px", textAlign: "left", background: "none", border: "none", color: "inherit", cursor: "pointer" }}
            onClick={() => handleContextMenuAction("select_all")}
          >
            Select All
          </button>
          <button
            type="button"
            role="menuitem"
            className="context-menu-item"
            style={{ display: "block", width: "100%", padding: "6px 16px", textAlign: "left", background: "none", border: "none", color: "inherit", cursor: "pointer" }}
            onClick={() => handleContextMenuAction("clear_selection")}
          >
            Clear Selection
          </button>
        </div>
      )}
    </div>
  );
}
