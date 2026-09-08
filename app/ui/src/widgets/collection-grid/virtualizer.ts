/**
 * Pure, deterministic virtualization calculation for FEAT-UI-VIEW_COLLECTIONS.
 *
 * Guarantees O(1) computation and strictly bounded resident window rows
 * regardless of whether total logical rows are 10, 100k, or 1,000,000.
 */

export interface VirtualWindow {
  readonly startIndex: number;
  readonly endIndex: number; // exclusive
  readonly visibleCount: number;
  readonly topPadding: number;
  readonly bottomPadding: number;
  readonly totalHeight: number;
}

export function computeVirtualWindow(
  totalRows: number,
  rowHeight: number,
  scrollTop: number,
  containerHeight: number,
  overscan: number = 5,
): VirtualWindow {
  if (totalRows <= 0 || rowHeight <= 0 || containerHeight <= 0) {
    return {
      startIndex: 0,
      endIndex: 0,
      visibleCount: 0,
      topPadding: 0,
      bottomPadding: 0,
      totalHeight: 0,
    };
  }

  const safeScrollTop = Math.max(0, scrollTop);
  const totalHeight = totalRows * rowHeight;

  const rawStartIndex = Math.floor(safeScrollTop / rowHeight);
  const rawVisibleCount = Math.ceil(containerHeight / rowHeight);

  const startIndex = Math.max(0, rawStartIndex - overscan);
  const endIndex = Math.min(totalRows, rawStartIndex + rawVisibleCount + overscan);
  const visibleCount = Math.max(0, endIndex - startIndex);

  const topPadding = startIndex * rowHeight;
  const bottomPadding = Math.max(0, (totalRows - endIndex) * rowHeight);

  return {
    startIndex,
    endIndex,
    visibleCount,
    topPadding,
    bottomPadding,
    totalHeight,
  };
}
