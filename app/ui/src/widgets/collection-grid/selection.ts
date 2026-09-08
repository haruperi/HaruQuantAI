/**
 * Pure bounded selection model for FEAT-UI-VIEW_COLLECTIONS.
 *
 * Guarantees that selecting 1,000,000 rows stores a bounded snapshot token
 * with an exclusion set (O(1) memory for full selection), never instantiating
 * a million browser objects.
 */

import type { BulkPreviewResponse, SelectionToken } from "./contracts";

export function createEmptySelection(totalCount: number = 0): SelectionToken {
  return {
    mode: "none",
    totalCount: Math.max(0, totalCount),
    selectedCount: 0,
  };
}

export function createSelectAll(totalCount: number): SelectionToken {
  const safeTotal = Math.max(0, totalCount);
  return {
    mode: "all_except",
    excludedIds: new Set<string>(),
    totalCount: safeTotal,
    selectedCount: safeTotal,
  };
}

export function createSelectAllExcept(
  excludedIds: Iterable<string>,
  totalCount: number,
): SelectionToken {
  const safeTotal = Math.max(0, totalCount);
  const set = new Set<string>(excludedIds);
  const selectedCount = Math.max(0, safeTotal - set.size);
  return {
    mode: "all_except",
    excludedIds: set,
    totalCount: safeTotal,
    selectedCount,
  };
}

export function createExplicitSelection(
  selectedIds: Iterable<string>,
  totalCount: number,
): SelectionToken {
  const safeTotal = Math.max(0, totalCount);
  const set = new Set<string>(selectedIds);
  if (set.size === 0) {
    return createEmptySelection(safeTotal);
  }
  return {
    mode: "explicit",
    selectedIds: set,
    totalCount: safeTotal,
    selectedCount: set.size,
  };
}

export function isRowSelected(token: SelectionToken, id: string): boolean {
  if (token.mode === "none") return false;
  if (token.mode === "explicit") return token.selectedIds.has(id);
  return !token.excludedIds.has(id);
}

export function toggleRowSelection(
  token: SelectionToken,
  id: string,
  totalCount: number = token.totalCount,
): SelectionToken {
  const safeTotal = Math.max(0, totalCount);

  if (token.mode === "none") {
    return createExplicitSelection([id], safeTotal);
  }

  if (token.mode === "explicit") {
    const nextSet = new Set<string>(token.selectedIds);
    if (nextSet.has(id)) {
      nextSet.delete(id);
      if (nextSet.size === 0) {
        return createEmptySelection(safeTotal);
      }
      return {
        mode: "explicit",
        selectedIds: nextSet,
        totalCount: safeTotal,
        selectedCount: nextSet.size,
      };
    }
    nextSet.add(id);
    return {
      mode: "explicit",
      selectedIds: nextSet,
      totalCount: safeTotal,
      selectedCount: nextSet.size,
    };
  }

  // mode === "all_except"
  const nextExcluded = new Set<string>(token.excludedIds);
  if (nextExcluded.has(id)) {
    nextExcluded.delete(id);
  } else {
    nextExcluded.add(id);
  }

  return {
    mode: "all_except",
    excludedIds: nextExcluded,
    totalCount: safeTotal,
    selectedCount: Math.max(0, safeTotal - nextExcluded.size),
  };
}

export function selectRange(
  token: SelectionToken,
  fromIndex: number,
  toIndex: number,
  visibleIds: readonly string[],
  totalCount: number = token.totalCount,
): SelectionToken {
  const safeTotal = Math.max(0, totalCount);
  const start = Math.max(0, Math.min(fromIndex, toIndex));
  const end = Math.min(visibleIds.length - 1, Math.max(fromIndex, toIndex));

  const rangeIds: string[] = [];
  for (let i = start; i <= end; i += 1) {
    const id = visibleIds[i];
    if (id !== undefined) {
      rangeIds.push(id);
    }
  }

  if (token.mode === "all_except") {
    const nextExcluded = new Set<string>(token.excludedIds);
    for (const id of rangeIds) {
      nextExcluded.delete(id);
    }
    return {
      mode: "all_except",
      excludedIds: nextExcluded,
      totalCount: safeTotal,
      selectedCount: Math.max(0, safeTotal - nextExcluded.size),
    };
  }

  const nextSelected = new Set<string>(token.mode === "explicit" ? token.selectedIds : []);
  for (const id of rangeIds) {
    nextSelected.add(id);
  }

  return {
    mode: "explicit",
    selectedIds: nextSelected,
    totalCount: safeTotal,
    selectedCount: nextSelected.size,
  };
}

/**
 * Generate a query-backed bulk preview without instantiating or scanning 1M items.
 * Bounded by maxPreviewRows (e.g. 100).
 */
export function generateBulkPreview(
  token: SelectionToken,
  resolveIdByIndex: (index: number) => string | undefined,
  maxPreviewRows: number = 100,
): BulkPreviewResponse {
  const totalSelected = token.selectedCount;
  if (totalSelected === 0 || token.mode === "none") {
    return { totalSelected: 0, sampleIds: [], isCapped: false };
  }

  const sampleIds: string[] = [];
  const limit = Math.min(maxPreviewRows, totalSelected);

  if (token.mode === "explicit") {
    for (const id of token.selectedIds) {
      sampleIds.push(id);
      if (sampleIds.length >= limit) break;
    }
  } else {
    // mode === "all_except"
    // Inspect items from start until limit valid items collected
    const scanLimit = Math.min(token.totalCount, limit + token.excludedIds.size + 20);
    for (let index = 0; index < scanLimit && sampleIds.length < limit; index += 1) {
      const id = resolveIdByIndex(index);
      if (id !== undefined && !token.excludedIds.has(id)) {
        sampleIds.push(id);
      }
    }
  }

  return {
    totalSelected,
    sampleIds,
    isCapped: totalSelected > sampleIds.length,
  };
}
