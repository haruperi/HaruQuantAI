/**
 * Unit tests for the docking layout tree factory (FEAT-UI-01,
 * FR-UI-024/025/201 in `app/ui/README.md` §4.1).
 */
import { describe, expect, it } from "vitest";

import { buildDockLayout, DOCK_WIDGET_COMPONENT } from "./dockLayout";
import { WORKSPACE_TEMPLATES } from "./templates";
import type { Widget } from "./contracts";

const widget = (over: Partial<Widget> & Pick<Widget, "id" | "type" | "title">): Widget => ({
  col: 1,
  row: 1,
  colSpan: 6,
  rowSpan: 2,
  ...over,
});

/** Walk a serialized grid tree and collect every group view state leaf. */
const collectLeaves = (node: unknown): { views: string[]; id: string }[] => {
  const n = node as { type: string; data: unknown };
  if (n.type === "leaf") return [n.data as { views: string[]; id: string }];
  return (n.data as unknown[]).flatMap(collectLeaves);
};

describe("FR-UI-024/201 structure is valid for every registered template", () => {
  for (const template of WORKSPACE_TEMPLATES) {
    it(`builds a complete layout for ${template.name}`, () => {
      const widgets = template.widgets.map((preset, index) =>
        widget({ id: `${preset.type}-${index}`, type: preset.type, title: preset.title, col: preset.col, row: preset.row, colSpan: preset.colSpan, rowSpan: preset.rowSpan })
      );
      const layout = buildDockLayout(widgets);

      if (widgets.length === 0) {
        expect(layout).toBeNull();
        return;
      }
      if (!layout) throw new Error("expected a layout");

      // Every widget is a panel, and every panel hosts one widget.
      expect(Object.keys(layout.panels).sort()).toEqual(widgets.map((w) => w.id).sort());
      for (const w of widgets) {
        expect(layout.panels[w.id]).toMatchObject({
          id: w.id,
          contentComponent: DOCK_WIDGET_COMPONENT,
          title: w.title,
          params: { widgetId: w.id },
        });
      }

      // Every widget appears in exactly one group leaf, with positive sizes.
      const leaves = collectLeaves(layout.grid.root);
      const leafViewIds = leaves.flatMap((leaf) => leaf.views);
      expect(leafViewIds.sort()).toEqual(widgets.map((w) => w.id).sort());
      expect(leaves.length).toBe(widgets.length);
    });
  }
});

describe("FR-UI-201 partition groups columns first, then bands", () => {
  it("splits side-by-side columns and stacks each column's rows independently", () => {
    const layout = buildDockLayout([
      widget({ id: "a", type: "markets", title: "A", col: 1, row: 1, colSpan: 6, rowSpan: 2 }),
      widget({ id: "b", type: "chart", title: "B", col: 7, row: 1, colSpan: 6, rowSpan: 2 }),
      widget({ id: "c", type: "priceLadder", title: "C", col: 1, row: 3, colSpan: 6, rowSpan: 2 }),
    ]);
    if (!layout) throw new Error("expected a layout");

    // Columns win: [a over c] beside [b], not [a,b] over [c].
    expect(layout.grid.orientation).toBe("HORIZONTAL");
    const root = layout.grid.root as { type: string; data: unknown[] };
    expect(root.type).toBe("branch");
    expect(root.data.length).toBe(2);
    const left = root.data[0] as { type: string; data: unknown[] };
    expect(left.type).toBe("branch");
    const leftBands = left.data.map((band) => collectLeaves(band).map((leaf) => leaf.views[0]));
    expect(leftBands).toEqual([["a"], ["c"]]);
    const right = root.data[1] as { type: string; data: { views: string[] } };
    expect(right.type).toBe("leaf");
    expect(right.data.views).toEqual(["b"]);
  });

  it("uses a horizontal root when a single band holds every widget", () => {
    const layout = buildDockLayout([
      widget({ id: "x", type: "chart", title: "X", col: 1, row: 1, colSpan: 6, rowSpan: 2 }),
      widget({ id: "y", type: "chart", title: "Y", col: 7, row: 1, colSpan: 6, rowSpan: 2 }),
    ]);
    if (!layout) throw new Error("expected a layout");
    expect(layout.grid.orientation).toBe("HORIZONTAL");
    const root = layout.grid.root as { type: string; data: { data: { views: string[] } }[] };
    expect(root.type).toBe("branch");
    expect(root.data.map((leaf) => leaf.data.views[0])).toEqual(["x", "y"]);
  });

  it("returns a bare leaf for a single widget", () => {
    const layout = buildDockLayout([widget({ id: "solo", type: "markets", title: "Solo" })]);
    if (!layout) throw new Error("expected a layout");
    const root = layout.grid.root as { type: string; data: { views: string[] } };
    expect(root.type).toBe("leaf");
    expect(root.data.views).toEqual(["solo"]);
    expect(layout.activeGroup).toBe("group-solo");
  });

  it("returns null for an empty widget set", () => {
    expect(buildDockLayout([])).toBeNull();
  });

  it("expresses side-by-side columns with independent vertical split points", () => {
    // Reference HaruQuant orientation: [Markets/Calendar stacked | Chart |
    // DOM], where the chart keeps its own single-cell column.
    const layout = buildDockLayout([
      widget({ id: "markets", type: "markets", title: "Markets", col: 1, row: 1, colSpan: 3, rowSpan: 2 }),
      widget({ id: "chart", type: "chart", title: "Chart", col: 4, row: 1, colSpan: 5, rowSpan: 2 }),
      widget({ id: "calendar", type: "tradePlan", title: "Calendar", col: 1, row: 3, colSpan: 3, rowSpan: 2 }),
      widget({ id: "dom", type: "priceLadder", title: "DOM", col: 9, row: 1, colSpan: 4, rowSpan: 4 }),
    ]);
    if (!layout) throw new Error("expected a layout");

    expect(layout.grid.orientation).toBe("HORIZONTAL");
    const root = layout.grid.root as { type: string; data: unknown[] };
    expect(root.type).toBe("branch");
    expect(root.data.length).toBe(3);

    const left = root.data[0] as { type: string; data: unknown[] };
    expect(left.type).toBe("branch");
    const leftBands = left.data.map((band) => collectLeaves(band).map((leaf) => leaf.views[0]));
    expect(leftBands).toEqual([["markets"], ["calendar"]]);

    const chartLeaf = root.data[1] as { type: string; data: { views: string[] } };
    expect(chartLeaf.type).toBe("leaf");
    expect(chartLeaf.data.views).toEqual(["chart"]);

    const domLeaf = root.data[2] as { type: string; data: { views: string[] } };
    expect(domLeaf.type).toBe("leaf");
    expect(domLeaf.data.views).toEqual(["dom"]);
  });

  it("treats missing legacy coordinates as row 1 with default spans", () => {
    const layout = buildDockLayout([
      { id: "nocoord", type: "data", title: "No coords" },
      { id: "nocoord2", type: "risk", title: "Also no coords" },
    ]);
    if (!layout) throw new Error("expected a layout");
    expect(Object.keys(layout.panels).sort()).toEqual(["nocoord", "nocoord2"]);
    const leaves = collectLeaves(layout.grid.root);
    expect(leaves.length).toBe(2);
  });
});

describe("FR-UI-195 template orientations match the reference thumbnails", () => {
  const templateWidgets = (id: string) => {
    const template = WORKSPACE_TEMPLATES.find((t) => t.id === id)!;
    return template.widgets.map((preset, index) =>
      widget({
        id: `${preset.type}-${index}`,
        type: preset.type,
        title: preset.title,
        col: preset.col,
        row: preset.row,
        colSpan: preset.colSpan,
        rowSpan: preset.rowSpan,
      })
    );
  };

  it("HaruQuant opens as three equal columns with distinct stack splits and a full-height DOM", () => {
    const layout = buildDockLayout(templateWidgets("haruquant"));
    if (!layout) throw new Error("expected a layout");

    expect(layout.grid.orientation).toBe("HORIZONTAL");
    const root = layout.grid.root as { type: string; data: { type: string; size: number }[] };
    expect(root.type).toBe("branch");
    expect(root.data).toHaveLength(3);
    // Equal thirds: 4/4/4 on the 12-column grid.
    expect(root.data.map((child) => child.size)).toEqual([4, 4, 4]);

    const [left, middle, dom] = root.data as unknown[];
    const bandViews = (column: unknown) =>
      (column as { data: unknown[] }).data.map((band) => collectLeaves(band).map((leaf) => leaf.views[0]));
    // Left: Markets/Calendar/Positions at 8/9/9; middle: Chart/Orders at 17/9.
    expect(bandViews(left)).toEqual([["markets-0"], ["tradePlan-1"], ["positions-3"]]);
    expect((left as { data: { size: number }[] }).data.map((b) => b.size)).toEqual([8, 9, 9]);
    expect(bandViews(middle)).toEqual([["chart-2"], ["tradeLog-4"]]);
    expect((middle as { data: { size: number }[] }).data.map((b) => b.size)).toEqual([17, 9]);
    expect((dom as { type: string; data: { views: string[] } }).type).toBe("leaf");
    expect((dom as { data: { views: string[] } }).data.views).toEqual(["priceLadder-5"]);
  });

  it("MultiCharts + Ladder opens as three stacked rows, the ladder row double-height", () => {
    const layout = buildDockLayout(templateWidgets("multicharts-ladder"));
    if (!layout) throw new Error("expected a layout");

    expect(layout.grid.orientation).toBe("VERTICAL");
    const root = layout.grid.root as { type: string; data: { type: string; size: number; data: unknown[] }[] };
    expect(root.type).toBe("branch");
    expect(root.data).toHaveLength(3);
    expect(root.data.map((band) => band.size)).toEqual([2, 2, 4]);
    const counts = root.data.map((band) => collectLeaves(band).length);
    expect(counts).toEqual([4, 4, 5]);
  });

  it("Options opens as Markets-over-Positions beside a full-height options chain", () => {
    const layout = buildDockLayout(templateWidgets("options"));
    if (!layout) throw new Error("expected a layout");

    expect(layout.grid.orientation).toBe("HORIZONTAL");
    const root = layout.grid.root as { type: string; data: { type: string; size: number }[] };
    expect(root.data).toHaveLength(2);
    expect(root.data.map((child) => child.size)).toEqual([6, 6]);
    const [left, chain] = root.data as unknown[];
    const leftBands = (left as { data: unknown[] }).data.map((band) =>
      collectLeaves(band).map((leaf) => leaf.views[0])
    );
    expect(leftBands).toEqual([["markets-0"], ["positions-2"]]);
    expect((left as { data: { size: number }[] }).data.map((b) => b.size)).toEqual([14, 9]);
    expect((chain as { type: string; data: { views: string[] } }).type).toBe("leaf");
    expect((chain as { data: { views: string[] } }).data.views).toEqual(["optionsGrid-1"]);
  });
});

describe("FR-UI-025 identity", () => {
  it("keys panels and groups by widget id so identity survives rebuilds", () => {
    const layout = buildDockLayout([
      widget({ id: "keep-me", type: "markets", title: "Markets" }),
    ]);
    if (!layout) throw new Error("expected a layout");
    expect(layout.panels["keep-me"].id).toBe("keep-me");
    expect((layout.grid.root as { data: { id: string } }).data.id).toBe("group-keep-me");
  });
});
