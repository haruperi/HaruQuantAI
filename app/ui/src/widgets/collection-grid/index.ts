/**
 * Public surface for FEAT-UI-VIEW_COLLECTIONS (Navigate large typed collections accessibly).
 */

export { COLLECTION_GRID_MANIFEST } from "./manifest";
export {
  collectionGridConfigSchema,
  DEFAULT_COLLECTION_GRID_CONFIG,
  parseCollectionGridConfig,
  resolveCollectionGridConfig,
  type CollectionGridConfig,
} from "./config";
export {
  compareValues,
  type BulkPreviewRequest,
  type BulkPreviewResponse,
  type ColumnDefinition,
  type ColumnGrouping,
  type ColumnKind,
  type CursorPagination,
  type FilterCriterion,
  type FilterOperator,
  type GridContextMenuAction,
  type GridError,
  type GridState,
  type NullsPosition,
  type SelectionToken,
  type SortCriterion,
  type SortDirection,
} from "./contracts";
export {
  computeVirtualWindow,
  type VirtualWindow,
} from "./virtualizer";
export {
  createEmptySelection,
  createExplicitSelection,
  createSelectAll,
  createSelectAllExcept,
  generateBulkPreview,
  isRowSelected,
  selectRange,
  toggleRowSelection,
} from "./selection";
export {
  CollectionGrid,
  type CollectionGridProps,
} from "./CollectionGrid";
export {
  CollectionGridFeature,
  type CollectionGridFeatureProps,
} from "./feature";
