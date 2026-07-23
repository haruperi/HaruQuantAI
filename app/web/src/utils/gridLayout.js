/**
 * Explicit grid placement helpers.
 *
 * Widgets carry real coordinates - `col` (1-12) and `row` (1-based) - instead of
 * relying on CSS auto-placement. That is what makes a widget stay where it is
 * dropped: with auto-packing, a widget dropped on blank canvas always re-packs
 * back against the preceding widgets, so empty space can never be occupied.
 */

export const GRID_COLUMNS = 12;
export const GRID_GAP = 8;
export const GRID_ROW_HEIGHT = 250;

export const MIN_COL_SPAN = 2;
export const MAX_COL_SPAN = GRID_COLUMNS;
export const MIN_ROW_SPAN = 1;
export const MAX_ROW_SPAN = 6;

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

/** Normalises a widget to a rectangle, tolerating legacy records with no col/row. */
export const rectOf = (widget) => {
  const colSpan = clamp(widget.colSpan || 6, MIN_COL_SPAN, MAX_COL_SPAN);
  const rowSpan = clamp(widget.rowSpan || 2, MIN_ROW_SPAN, MAX_ROW_SPAN);
  return {
    col: clamp(widget.col || 1, 1, GRID_COLUMNS - colSpan + 1),
    row: Math.max(widget.row || 1, 1),
    colSpan,
    rowSpan
  };
};

const overlaps = (a, b) =>
  a.col < b.col + b.colSpan &&
  b.col < a.col + a.colSpan &&
  a.row < b.row + b.rowSpan &&
  b.row < a.row + a.rowSpan;

/** True when `rect` can sit at its coordinates without touching any other widget. */
export const isAreaFree = (widgets, rect, ignoreId) =>
  rect.col >= 1 &&
  rect.col + rect.colSpan - 1 <= GRID_COLUMNS &&
  rect.row >= 1 &&
  !widgets.some((w) => String(w.id) !== String(ignoreId) && overlaps(rect, rectOf(w)));

/**
 * Assigns coordinates to any widget that lacks them by replaying auto-packing
 * once. Lets existing saved workspaces upgrade to explicit placement in place.
 */
export const ensureCoordinates = (widgets) => {
  if (widgets.every((w) => w.col && w.row)) return widgets;

  const placed = [];
  for (const widget of widgets) {
    if (widget.col && widget.row) {
      placed.push(widget);
      continue;
    }
    const { colSpan, rowSpan } = rectOf(widget);
    placed.push({ ...widget, colSpan, rowSpan, ...findFreeCell(placed, colSpan, rowSpan) });
  }
  return placed;
};

/** Scans top-left to bottom-right for the first gap that fits the given size. */
export const findFreeCell = (widgets, colSpan, rowSpan) => {
  for (let row = 1; row < 200; row++) {
    for (let col = 1; col <= GRID_COLUMNS - colSpan + 1; col++) {
      if (isAreaFree(widgets, { col, row, colSpan, rowSpan })) return { col, row };
    }
  }
  return { col: 1, row: 1 };
};

/** Converts a pointer position inside the grid to 1-based grid coordinates. */
export const cellFromPoint = (container, clientX, clientY) => {
  const rect = container.getBoundingClientRect();
  const styles = window.getComputedStyle(container);
  const padLeft = parseFloat(styles.paddingLeft) || 0;
  const padTop = parseFloat(styles.paddingTop) || 0;

  const innerWidth = container.clientWidth - padLeft - (parseFloat(styles.paddingRight) || 0);
  const colUnit = (innerWidth + GRID_GAP) / GRID_COLUMNS;
  const rowUnit = GRID_ROW_HEIGHT + GRID_GAP;

  const x = clientX - rect.left - padLeft;
  const y = clientY - rect.top - padTop + container.scrollTop;

  return {
    col: clamp(Math.floor(x / colUnit) + 1, 1, GRID_COLUMNS),
    row: Math.max(Math.floor(y / rowUnit) + 1, 1)
  };
};

/** Total rows occupied, so the grid can reserve a spare row of drop space. */
export const usedRowCount = (widgets) =>
  widgets.reduce((max, w) => {
    const r = rectOf(w);
    return Math.max(max, r.row + r.rowSpan - 1);
  }, 0);
