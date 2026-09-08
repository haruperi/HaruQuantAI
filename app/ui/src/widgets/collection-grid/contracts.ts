/**
 * Pure D-UI view and contribution contracts for FEAT-UI-VIEW_COLLECTIONS.
 *
 * Presentation-only interfaces for column definitions, cursor sorting/filtering,
 * bounded snapshot selection tokens, grid states, and context menu actions.
 * Never re-implements numerical or economic policy in the browser.
 */

export type ColumnKind = "numeric" | "date" | "text" | "boolean" | "enum" | "plugin";

export interface ColumnDefinition<T = Record<string, unknown>> {
  readonly id: string;
  readonly header: string;
  readonly kind: ColumnKind;
  readonly width?: number;
  readonly minWidth?: number;
  readonly pinned?: "left" | "right" | false;
  readonly hidden?: boolean;
  readonly sortable?: boolean;
  readonly filterable?: boolean;
  readonly pluginAvailable?: boolean;
  readonly pluginId?: string;
  readonly accessor?: (row: T) => unknown;
  readonly format?: (value: unknown) => string;
}

export type SortDirection = "asc" | "desc";
export type NullsPosition = "first" | "last";

export interface SortCriterion {
  readonly columnId: string;
  readonly direction: SortDirection;
  readonly nulls?: NullsPosition;
}

export type FilterOperator = "eq" | "neq" | "gt" | "gte" | "lt" | "lte" | "contains" | "in";

export interface FilterCriterion {
  readonly columnId: string;
  readonly operator: FilterOperator;
  readonly value: unknown;
}

export interface CursorPagination {
  readonly cursor?: string;
  readonly limit: number;
  readonly totalCount?: number;
  readonly hasMore?: boolean;
}

export type GridState =
  | "idle"
  | "loading"
  | "empty"
  | "partial"
  | "stale"
  | "error"
  | "denied";

export interface GridError {
  readonly code: string;
  readonly message: string;
  readonly retryable?: boolean;
}

/**
 * Bounded selection snapshot token.
 * Selecting 1M logical rows produces an `all_except` token with an empty or bounded
 * exclusion set, strictly avoiding allocating a million browser objects.
 */
export type SelectionToken =
  | {
      readonly mode: "none";
      readonly totalCount: number;
      readonly selectedCount: 0;
    }
  | {
      readonly mode: "explicit";
      readonly selectedIds: ReadonlySet<string>;
      readonly totalCount: number;
      readonly selectedCount: number;
    }
  | {
      readonly mode: "all_except";
      readonly excludedIds: ReadonlySet<string>;
      readonly totalCount: number;
      readonly selectedCount: number;
    };

export interface BulkPreviewRequest {
  readonly token: SelectionToken;
  readonly maxPreviewRows: number;
}

export interface BulkPreviewResponse {
  readonly totalSelected: number;
  readonly sampleIds: readonly string[];
  readonly isCapped: boolean;
}

export type GridContextMenuAction =
  | "copy_cell"
  | "copy_row"
  | "select_all"
  | "clear_selection"
  | "filter_by_value";

export interface ColumnGrouping {
  readonly groupKeys: readonly string[];
}

/**
 * Pure value comparator preserving owner sorting semantics:
 * - Numeric sorts compare numeric magnitudes (e.g. 2 < 10, not lexicographic "10" < "2").
 * - Date sorts compare chronological timestamps (ISO-8601 or Date objects).
 * - Null/undefined values are deterministically ordered according to `nulls: 'first' | 'last'`.
 */
export function compareValues(
  a: unknown,
  b: unknown,
  kind: ColumnKind,
  direction: SortDirection = "asc",
  nulls: NullsPosition = "last",
): number {
  const isANull = a === null || a === undefined;
  const isBNull = b === null || b === undefined;

  if (isANull && isBNull) return 0;
  if (isANull) return nulls === "first" ? -1 : 1;
  if (isBNull) return nulls === "first" ? 1 : -1;

  let comparison = 0;

  if (kind === "numeric") {
    const numA = typeof a === "number" ? a : Number(a);
    const numB = typeof b === "number" ? b : Number(b);
    if (!Number.isNaN(numA) && !Number.isNaN(numB)) {
      comparison = numA - numB;
    } else {
      comparison = String(a).localeCompare(String(b));
    }
  } else if (kind === "date") {
    const timeA = a instanceof Date ? a.getTime() : new Date(String(a)).getTime();
    const timeB = b instanceof Date ? b.getTime() : new Date(String(b)).getTime();
    if (!Number.isNaN(timeA) && !Number.isNaN(timeB)) {
      comparison = timeA - timeB;
    } else {
      comparison = String(a).localeCompare(String(b));
    }
  } else if (kind === "boolean") {
    const boolA = Boolean(a);
    const boolB = Boolean(b);
    comparison = boolA === boolB ? 0 : boolA ? 1 : -1;
  } else {
    comparison = String(a).localeCompare(String(b));
  }

  return direction === "asc" ? comparison : -comparison;
}
