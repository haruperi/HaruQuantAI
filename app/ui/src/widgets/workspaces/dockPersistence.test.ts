/** Security and topology tests for the Dockview persistence boundary. */

import { describe, expect, it } from "vitest";

import { sanitizeDockLayout } from "./dockPersistence";

const panel = (id: string) => ({
  id,
  contentComponent: "widget",
  title: id.toUpperCase(),
  params: { widgetId: id },
});

describe("sanitizeDockLayout", () => {
  it("preserves bounded split, tab, and in-window floating topology", () => {
    const safe = sanitizeDockLayout(
      {
        grid: {
          width: 1200,
          height: 800,
          orientation: "HORIZONTAL",
          root: {
            type: "leaf",
            size: 8,
            data: {
              id: "main",
              views: ["a", "b"],
              activeView: "b",
            },
          },
        },
        panels: { a: panel("a"), b: panel("b"), c: panel("c") },
        activeGroup: "main",
        floatingGroups: [
          {
            data: { id: "floating", views: ["c"], activeView: "c" },
            position: { width: 400, height: 300, left: 20, top: 30 },
          },
        ],
      },
      ["a", "b", "c"],
    );

    expect(safe?.panels).toEqual({
      a: panel("a"),
      b: panel("b"),
      c: panel("c"),
    });
    expect(safe?.grid.root).toMatchObject({
      type: "leaf",
      data: { id: "main", views: ["a", "b"], activeView: "b" },
    });
    expect(safe?.floatingGroups).toHaveLength(1);
    expect(safe?.popoutGroups).toBeUndefined();
  });

  it("removes hostile nested fields and keeps valid sibling panels", () => {
    const safe = sanitizeDockLayout(
      {
        provider: { token: "SECRET" },
        grid: {
          width: 1200,
          height: 800,
          orientation: "HORIZONTAL",
          root: {
            type: "leaf",
            data: {
              id: "main",
              views: ["safe", "hostile"],
              activeView: "safe",
              provider: { token: "SECRET" },
            },
          },
        },
        panels: {
          safe: {
            ...panel("safe"),
            provider: { token: "SECRET" },
            params: { widgetId: "safe" },
          },
          hostile: {
            ...panel("hostile"),
            params: { widgetId: "hostile", provider: { token: "SECRET" } },
          },
        },
        popoutGroups: [
          {
            data: { id: "popout", views: ["safe"] },
            url: "https://example.invalid/?token=SECRET",
            position: null,
          },
        ],
      },
      ["safe", "hostile"],
    );

    expect(Object.keys(safe?.panels ?? {})).toEqual(["safe"]);
    expect(safe?.grid.root).toMatchObject({
      type: "leaf",
      data: { views: ["safe"] },
    });
    expect(JSON.stringify(safe)).not.toContain("SECRET");
    expect(safe?.popoutGroups).toBeUndefined();
  });

  it("rejects over-deep and non-finite layouts", () => {
    let root: unknown = {
      type: "leaf",
      data: { id: "group-a", views: ["a"] },
    };
    for (let depth = 0; depth < 18; depth += 1) {
      root = { type: "branch", data: [root] };
    }
    const layout = {
      grid: {
        width: 1200,
        height: 800,
        orientation: "HORIZONTAL",
        root,
      },
      panels: { a: panel("a") },
    };
    expect(sanitizeDockLayout(layout, ["a"])).toBeNull();
    expect(
      sanitizeDockLayout(
        {
          ...layout,
          grid: { ...layout.grid, width: Number.POSITIVE_INFINITY },
        },
        ["a"],
      ),
    ).toBeNull();
  });

  it("omits contradictory constraints and drops off-window floats", () => {
    const safe = sanitizeDockLayout(
      {
        grid: {
          width: 1200,
          height: 800,
          orientation: "HORIZONTAL",
          root: {
            type: "leaf",
            data: { id: "main", views: ["a", "b"] },
          },
        },
        panels: {
          a: {
            ...panel("a"),
            minimumWidth: 100,
            maximumWidth: 50,
            minimumHeight: 40,
            maximumHeight: 80,
          },
          b: panel("b"),
          c: panel("c"),
        },
        floatingGroups: [
          {
            data: { id: "off-window", views: ["c"] },
            position: { width: 400, height: 300, left: -999, top: -999 },
          },
        ],
      },
      ["a", "b", "c"],
    );

    expect(safe?.panels.a).toEqual({
      ...panel("a"),
      minimumHeight: 40,
      maximumHeight: 80,
    });
    expect(safe?.panels.b).toEqual(panel("b"));
    expect(safe?.grid.root).toMatchObject({
      type: "leaf",
      data: { views: ["a", "b"] },
    });
    expect(safe?.floatingGroups).toBeUndefined();
  });
});
