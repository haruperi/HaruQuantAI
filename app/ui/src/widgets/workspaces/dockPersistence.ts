/**
 * Bounded Dockview persistence boundary for FEAT-UI-01.
 *
 * Dockview serializes open-ended panel params and popout metadata. Workspace
 * persistence accepts only the minimum local widget topology and reconstructs
 * every object so credentials and unknown nested fields cannot survive.
 */

import { Orientation, type SerializedDockview } from "dockview-react";

import { DOCK_WIDGET_COMPONENT } from "./dockLayout";

const MAX_PANELS = 64;
const MAX_FLOATING_GROUPS = 16;
const MAX_TREE_DEPTH = 16;
const MAX_TREE_NODES = 128;
const MAX_STRING_LENGTH = 256;
const MAX_DIMENSION = 100_000;

type JsonRecord = Record<string, unknown>;
interface SafePanel {
  id: string;
  contentComponent: string;
  title?: string;
  params: { widgetId: string };
  minimumWidth?: number;
  minimumHeight?: number;
  maximumWidth?: number;
  maximumHeight?: number;
}

interface SafeTabGroup {
  id: string;
  label?: string;
  color?: string;
  collapsed: boolean;
  panelIds: string[];
}

interface SafeGroupState {
  views: string[];
  activeView?: string;
  id: string;
  hideHeader?: boolean;
  headerPosition?: "top" | "bottom" | "left" | "right";
  tabGroups?: SafeTabGroup[];
}

type SafeLayoutNode =
  | { type: "leaf"; data: SafeGroupState; size?: number; visible?: boolean }
  | { type: "branch"; data: SafeLayoutNode[]; size?: number; visible?: boolean };

interface SafeGrid {
  root: SafeLayoutNode;
  height: number;
  width: number;
  orientation: Orientation;
}

interface SafeFloatingGroup {
  data?: SafeGroupState;
  grid?: SafeGrid;
  position: ReturnType<typeof sanitizePosition> & {};
}

function recordOf(value: unknown): JsonRecord | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as JsonRecord)
    : null;
}

function boundedString(value: unknown): string | null {
  return typeof value === "string" &&
    value.length > 0 &&
    value.length <= MAX_STRING_LENGTH
    ? value
    : null;
}

function dimension(value: unknown): number | null {
  return typeof value === "number" &&
    Number.isFinite(value) &&
    value > 0 &&
    value <= MAX_DIMENSION
    ? value
    : null;
}

function coordinate(value: unknown): number | null {
  return typeof value === "number" &&
    Number.isFinite(value) &&
    value >= 0 &&
    value <= MAX_DIMENSION
    ? value
    : null;
}

function sanitizePanel(
  key: string,
  value: unknown,
  widgetIds: ReadonlySet<string>,
): SafePanel | null {
  const source = recordOf(value);
  if (source === null || !widgetIds.has(key) || source.id !== key) return null;
  if (source.contentComponent !== DOCK_WIDGET_COMPONENT) return null;
  const params = recordOf(source.params);
  if (
    params === null ||
    Object.keys(params).some((name) => name !== "widgetId") ||
    params.widgetId !== key
  ) {
    return null;
  }

  const panel: SafePanel = {
    id: key,
    contentComponent: DOCK_WIDGET_COMPONENT,
    params: { widgetId: key },
  };
  if ("title" in source) {
    const title = boundedString(source.title);
    if (title === null) return null;
    panel.title = title;
  }
  const minimumWidth = dimension(source.minimumWidth);
  const minimumHeight = dimension(source.minimumHeight);
  const maximumWidth = dimension(source.maximumWidth);
  const maximumHeight = dimension(source.maximumHeight);
  if (
    minimumWidth === null ||
    maximumWidth === null ||
    minimumWidth <= maximumWidth
  ) {
    if (minimumWidth !== null) panel.minimumWidth = minimumWidth;
    if (maximumWidth !== null) panel.maximumWidth = maximumWidth;
  }
  if (
    minimumHeight === null ||
    maximumHeight === null ||
    minimumHeight <= maximumHeight
  ) {
    if (minimumHeight !== null) panel.minimumHeight = minimumHeight;
    if (maximumHeight !== null) panel.maximumHeight = maximumHeight;
  }
  return panel;
}

function sanitizeTabGroups(
  value: unknown,
  views: ReadonlySet<string>,
): SafeTabGroup[] | undefined {
  if (!Array.isArray(value) || value.length > MAX_PANELS) return undefined;
  const groups = value.flatMap((item) => {
    const source = recordOf(item);
    if (source === null) return [];
    const id = boundedString(source.id);
    if (
      id === null ||
      typeof source.collapsed !== "boolean" ||
      !Array.isArray(source.panelIds) ||
      source.panelIds.length > MAX_PANELS
    ) {
      return [];
    }
    const panelIds = source.panelIds.filter(
      (panelId): panelId is string =>
        typeof panelId === "string" && views.has(panelId),
    );
    if (panelIds.length === 0) return [];
    const group: SafeTabGroup = {
      id,
      collapsed: source.collapsed,
      panelIds,
    };
    const label = boundedString(source.label);
    if (label !== null) group.label = label;
    const color = boundedString(source.color);
    if (color !== null) group.color = color;
    return [group];
  });
  return groups.length > 0 ? groups : undefined;
}

function sanitizeGroup(
  value: unknown,
  panelIds: ReadonlySet<string>,
  groupIds: Set<string>,
): SafeGroupState | null {
  const source = recordOf(value);
  if (source === null || !Array.isArray(source.views)) return null;
  const id = boundedString(source.id);
  if (id === null || groupIds.has(id) || source.views.length > MAX_PANELS) {
    return null;
  }
  const views = [
    ...new Set(
      source.views.filter(
        (view): view is string =>
          typeof view === "string" && panelIds.has(view),
      ),
    ),
  ];
  if (views.length === 0) return null;

  const group: SafeGroupState = { id, views };
  if (typeof source.activeView === "string" && views.includes(source.activeView)) {
    group.activeView = source.activeView;
  }
  if (typeof source.hideHeader === "boolean") group.hideHeader = source.hideHeader;
  if (
    source.headerPosition === "top" ||
    source.headerPosition === "bottom" ||
    source.headerPosition === "left" ||
    source.headerPosition === "right"
  ) {
    group.headerPosition = source.headerPosition;
  }
  const tabGroups = sanitizeTabGroups(source.tabGroups, new Set(views));
  if (tabGroups !== undefined) group.tabGroups = tabGroups;
  groupIds.add(id);
  return group;
}

function sanitizeNode(
  value: unknown,
  panelIds: ReadonlySet<string>,
  groupIds: Set<string>,
  depth: number,
  budget: { remaining: number },
): SafeLayoutNode | null {
  if (depth > MAX_TREE_DEPTH || budget.remaining <= 0) return null;
  budget.remaining -= 1;
  const source = recordOf(value);
  if (source === null) return null;

  let node: SafeLayoutNode | null = null;
  if (source.type === "leaf") {
    const data = sanitizeGroup(source.data, panelIds, groupIds);
    if (data !== null) node = { type: "leaf", data };
  } else if (source.type === "branch" && Array.isArray(source.data)) {
    if (source.data.length > MAX_TREE_NODES) return null;
    const children = source.data.flatMap((child) => {
      const parsed = sanitizeNode(
        child,
        panelIds,
        groupIds,
        depth + 1,
        budget,
      );
      return parsed === null ? [] : [parsed];
    });
    if (children.length === 1) node = children[0];
    else if (children.length > 1) node = { type: "branch", data: children };
  }
  if (node === null) return null;

  const size = dimension(source.size);
  if (size !== null) node.size = size;
  if (typeof source.visible === "boolean") node.visible = source.visible;
  return node;
}

function sanitizeGrid(
  value: unknown,
  panelIds: ReadonlySet<string>,
  groupIds: Set<string>,
): SafeGrid | null {
  const source = recordOf(value);
  if (source === null) return null;
  const width = dimension(source.width);
  const height = dimension(source.height);
  if (
    width === null ||
    height === null ||
    (source.orientation !== Orientation.HORIZONTAL &&
      source.orientation !== Orientation.VERTICAL)
  ) {
    return null;
  }
  const root = sanitizeNode(
    source.root,
    panelIds,
    groupIds,
    0,
    { remaining: MAX_TREE_NODES },
  );
  return root === null
    ? null
    : { root, width, height, orientation: source.orientation };
}

function sanitizePosition(value: unknown): { width: number; height: number } &
  ({ left: number; top: number } | { right: number; top: number } |
    { left: number; bottom: number } | { right: number; bottom: number }) | null {
  const source = recordOf(value);
  if (source === null) return null;
  const width = dimension(source.width);
  const height = dimension(source.height);
  const horizontal =
    coordinate(source.left) !== null
      ? { left: coordinate(source.left) as number }
      : coordinate(source.right) !== null
        ? { right: coordinate(source.right) as number }
        : null;
  const vertical =
    coordinate(source.top) !== null
      ? { top: coordinate(source.top) as number }
      : coordinate(source.bottom) !== null
        ? { bottom: coordinate(source.bottom) as number }
        : null;
  if (width === null || height === null || horizontal === null || vertical === null) {
    return null;
  }
  return { width, height, ...horizontal, ...vertical };
}

function sanitizeFloatingGroups(
  value: unknown,
  panelIds: ReadonlySet<string>,
  groupIds: Set<string>,
): SafeFloatingGroup[] {
  if (!Array.isArray(value) || value.length > MAX_FLOATING_GROUPS) return [];
  const groups: SafeFloatingGroup[] = [];
  for (const item of value) {
    const source = recordOf(item);
    if (source === null) continue;
    const position = sanitizePosition(source.position);
    if (position === null) continue;
    if ("data" in source && !("grid" in source)) {
      const data = sanitizeGroup(source.data, panelIds, groupIds);
      if (data !== null) groups.push({ data, position });
      continue;
    }
    if ("grid" in source && !("data" in source)) {
      const grid = sanitizeGrid(source.grid, panelIds, groupIds);
      if (grid !== null) groups.push({ grid, position });
    }
  }
  return groups;
}

/**
 * Sanitize one serialized Dockview layout for the supplied workspace widgets.
 *
 * @param value Untrusted serialized layout.
 * @param widgetIds Widget IDs owned by the target workspace.
 * @returns A minimal safe Dockview layout, or null when no valid topology remains.
 */
export function sanitizeDockLayout(
  value: unknown,
  widgetIds: readonly string[],
): SerializedDockview | null {
  if (widgetIds.length > MAX_PANELS) return null;
  const source = recordOf(value);
  const rawPanels = source === null ? null : recordOf(source.panels);
  if (
    source === null ||
    rawPanels === null ||
    Object.keys(rawPanels).length > MAX_PANELS
  ) {
    return null;
  }
  const workspaceIds = new Set(
    widgetIds.filter((id) => boundedString(id) !== null),
  );
  const panels: Record<string, SafePanel> = {};
  for (const [key, rawPanel] of Object.entries(rawPanels)) {
    const panel = sanitizePanel(key, rawPanel, workspaceIds);
    if (panel !== null) panels[key] = panel;
  }
  const panelIds = new Set(Object.keys(panels));
  if (panelIds.size === 0) return null;

  const groupIds = new Set<string>();
  const grid = sanitizeGrid(source.grid, panelIds, groupIds);
  if (grid === null) return null;
  const floatingGroups = sanitizeFloatingGroups(
    source.floatingGroups,
    panelIds,
    groupIds,
  );
  const referenced = new Set<string>();
  const collect = (node: SafeLayoutNode): void => {
    if (node.type === "leaf") {
      node.data.views.forEach((id) => referenced.add(id));
      return;
    }
    node.data.forEach(collect);
  };
  collect(grid.root);
  for (const floating of floatingGroups) {
    if (floating.data !== undefined) {
      floating.data.views.forEach((id) => referenced.add(id));
    } else if (floating.grid !== undefined) {
      collect(floating.grid.root);
    }
  }
  for (const id of Object.keys(panels)) {
    if (!referenced.has(id)) delete panels[id];
  }
  if (Object.keys(panels).length === 0) return null;

  const result: {
    grid: SafeGrid;
    panels: Record<string, SafePanel>;
    activeGroup?: string;
    floatingGroups?: SafeFloatingGroup[];
  } = { grid, panels };
  if (typeof source.activeGroup === "string" && groupIds.has(source.activeGroup)) {
    result.activeGroup = source.activeGroup;
  }
  if (floatingGroups.length > 0) result.floatingGroups = floatingGroups;
  return result as unknown as SerializedDockview;
}
