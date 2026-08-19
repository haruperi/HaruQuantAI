/**
 * Docking layout tree construction for workspace widget sets (FEAT-UI-01,
 * FR-UI-201).
 *
 * Deterministically converts a widget list (with grid-rectangle
 * coordinates) into a serialized Dockview layout using a two-level
 * guillotine partition: widgets whose column ranges overlap chain into a
 * column cluster, clusters sit side by side, and each cluster is cut into
 * row bands that stack vertically with band members side by side. This
 * expresses the reference thumbnails' orientations exactly - including
 * side-by-side columns with different vertical split points (e.g. a
 * three-panel left column beside a two-panel middle column and a
 * full-height ladder) - and still migrates any legacy persisted rectangle
 * set, since the partition falls back to plain banding when every widget
 * overlaps in one cluster. Only the ratios between spans matter, so
 * templates may declare their own nominal column/row counts.
 */
import { Orientation, type SerializedDockview } from "dockview-react";

import type { Widget } from "./contracts";

/** All panels use one host component; params carry the widget id. */
export const DOCK_WIDGET_COMPONENT = "widget";

/** Nominal serialized viewport; Dockview redistributes sizes proportionally. */
const NOMINAL_WIDTH = 1200;
const NOMINAL_HEIGHT = 800;

const DEFAULT_SPAN = 6;
const DEFAULT_ROW_SPAN = 2;

/** A widget plus its defaulted grid rectangle, in start/end form. */
interface Rect {
  widget: Widget;
  col: number;
  row: number;
  colEnd: number;
  rowEnd: number;
}

/** One dock group per widget, named after it so identities stay traceable. */
const groupStateOf = (widget: Widget) => ({
  views: [widget.id],
  id: `group-${widget.id}`,
  activeView: widget.id,
});

type LayoutNode = SerializedDockview["grid"]["root"];

/**
 * Chain rects whose intervals overlap along an axis into consecutive groups.
 *
 * @param rects Rects to partition.
 * @param key Start coordinate along the axis (`col` or `row`).
 * @param endKey End coordinate along the axis (`colEnd` or `rowEnd`).
 * @returns Consecutive clusters; each is the member list plus the merged
 *   interval extent, in axis order.
 */
const clusterBy = (
  rects: Rect[],
  key: "col" | "row",
  endKey: "colEnd" | "rowEnd"
): { members: Rect[]; start: number; end: number }[] => {
  const clusters: { members: Rect[]; start: number; end: number }[] = [];
  for (const rect of [...rects].sort((a, b) => a[key] - b[key] || a.row - b.row || a.col - b.col)) {
    const cluster = clusters[clusters.length - 1];
    // Overlapping (or abutting) starts merge; a gap starts a new cluster.
    if (cluster && rect[key] < cluster.end) {
      cluster.members.push(rect);
      cluster.end = Math.max(cluster.end, rect[endKey]);
    } else {
      clusters.push({ members: [rect], start: rect[key], end: rect[endKey] });
    }
  }
  return clusters;
};

/**
 * Build a serialized Dockview layout for a widget set.
 *
 * Column clusters (widgets whose horizontal ranges overlap) become side by
 * side branches; within a cluster, row bands stack vertically and band
 * members sit side by side. Single-member groups collapse to themselves, so
 * a lone widget yields a bare leaf and a lone band yields the horizontal
 * branch itself. This reproduces the reference simulator's template
 * arrangements at their measured proportions.
 *
 * @param widgets Widgets with optional grid coordinates; order within a
 *   band follows the `col` coordinate.
 * @returns A serialized layout whose panels are keyed by widget id, or null
 *   for an empty widget set (the caller presents the empty state instead).
 */
export function buildDockLayout(widgets: Widget[]): SerializedDockview | null {
  if (widgets.length === 0) return null;

  const rects: Rect[] = widgets.map((widget) => {
    const col = widget.col ?? 1;
    const row = widget.row ?? 1;
    return {
      widget,
      col,
      row,
      colEnd: col + (widget.colSpan ?? DEFAULT_SPAN),
      rowEnd: row + (widget.rowSpan ?? DEFAULT_ROW_SPAN),
    };
  });

  const panels: SerializedDockview["panels"] = {};
  for (const widget of widgets) {
    panels[widget.id] = {
      id: widget.id,
      contentComponent: DOCK_WIDGET_COMPONENT,
      title: widget.title,
      params: { widgetId: widget.id },
    };
  }

  const leafOf = (rect: Rect, size: number): LayoutNode => ({
    type: "leaf",
    data: groupStateOf(rect.widget),
    size,
  });

  /** One column cluster as a vertical stack of horizontal band branches. */
  const columnNode = (cluster: { members: Rect[]; start: number; end: number }): LayoutNode => {
    const bands = clusterBy(cluster.members, "row", "rowEnd");
    // A node's size is interpreted along its parent branch's axis: band
    // children are sized by band height (they stack), band members by their
    // column spans (they sit side by side), and the cluster node itself by
    // the cluster's width extent (clusters sit side by side).
    const bandNodes: LayoutNode[] = bands.map((band) => {
      const sorted = [...band.members].sort((a, b) => a.col - b.col);
      if (sorted.length === 1) return leafOf(sorted[0], band.end - band.start);
      return {
        type: "branch",
        data: sorted.map((rect) => leafOf(rect, rect.colEnd - rect.col)),
        size: band.end - band.start,
      } as LayoutNode;
    });
    if (bandNodes.length === 1) {
      // A lone band node sits directly under the horizontal root (or is the
      // root), so its size axis is the cluster's width extent.
      const lone = bandNodes[0] as { size: number };
      lone.size = cluster.end - cluster.start;
      return lone as LayoutNode;
    }
    return {
      type: "branch",
      data: bandNodes,
      size: cluster.end - cluster.start,
    } as LayoutNode;
  };

  const columns = clusterBy(rects, "col", "colEnd");
  const columnNodes = columns.map(columnNode);

  let root: LayoutNode;
  let orientation: Orientation;
  if (columnNodes.length === 1) {
    // One cluster: a bare leaf or a lone horizontal band stays horizontal;
    // a stack of several bands splits the root vertically.
    root = columnNodes[0];
    const bandCount = clusterBy(columns[0].members, "row", "rowEnd").length;
    orientation = bandCount > 1 ? Orientation.VERTICAL : Orientation.HORIZONTAL;
  } else {
    root = {
      type: "branch",
      data: columnNodes,
      size: columns.reduce((sum, column) => sum + (column.end - column.start), 0),
    } as LayoutNode;
    orientation = Orientation.HORIZONTAL;
  }

  const first = [...rects].sort((a, b) => a.row - b.row || a.col - b.col)[0];

  return {
    grid: {
      root,
      height: NOMINAL_HEIGHT,
      width: NOMINAL_WIDTH,
      orientation,
    },
    panels,
    activeGroup: `group-${first.widget.id}`,
  };
}
