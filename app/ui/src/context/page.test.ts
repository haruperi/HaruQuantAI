/**
 * Unit tests for bounded page context (FR-API-043).
 *
 * The provider validates eagerly and synchronously during render, so invalid
 * input surfaces as a thrown `PageContextError`. Each case renders through a
 * `renderHook` wrapper so the provider runs inside React's renderer.
 */

import { describe, expect, it, vi } from "vitest";

import { renderHook } from "@testing-library/react";

import {
  PageContextProvider,
  usePageContext,
} from "./page";
import { PageContextError } from "./errors";

const base = {
  route: "/workspace",
  user_id: "u_1",
  page_name: "Workspace",
};

/** Wrap a provider invocation in a renderHook-compatible component. */
function withProvider(
  props: Omit<Parameters<typeof PageContextProvider>[0], "children">
) {
  return ({ children }: { children: React.ReactNode }) =>
    PageContextProvider({ ...props, children });
}

describe("PageContextProvider — FR-API-043", () => {
  it("secretsAreRejected: rejects a sensitive-looking identifier", () => {
    expect(() =>
      renderHook(() => usePageContext(), {
        wrapper: withProvider({ ...base, visible_entity_ids: ["password"] }),
      })
    ).toThrow(PageContextError);
  });

  it("rejects sensitive keys across fragments", () => {
    for (const bad of ["api_key", "sessionToken", "my-secret"]) {
      expect(() =>
        renderHook(() => usePageContext(), {
          wrapper: withProvider({ ...base, approved_actions: [bad] }),
        })
      ).toThrow(PageContextError);
    }
  });

  it("visibleIdsCappedAt200: rejects more than 200 visible ids", () => {
    const ids = Array.from({ length: 201 }, (_, i) => `id_${i}`);
    expect(() =>
      renderHook(() => usePageContext(), {
        wrapper: withProvider({ ...base, visible_entity_ids: ids }),
      })
    ).toThrow(/200/);
  });

  it("accepts exactly 200 visible ids", () => {
    const ids = Array.from({ length: 200 }, (_, i) => `id_${i}`);
    const { result } = renderHook(() => usePageContext(), {
      wrapper: withProvider({ ...base, visible_entity_ids: ids }),
    });
    expect(result.current?.visible_entity_ids).toHaveLength(200);
  });

  it("actionsDeduplicated: collapses duplicate actions", () => {
    const { result } = renderHook(() => usePageContext(), {
      wrapper: withProvider({
        ...base,
        approved_actions: ["trade", "trade", "view"],
      }),
    });
    expect(result.current?.approved_actions).toEqual(["trade", "view"]);
  });

  it("rejects an empty entity id", () => {
    expect(() =>
      renderHook(() => usePageContext(), {
        wrapper: withProvider({
          ...base,
          visible_entity_ids: ["valid", "  "],
        }),
      })
    ).toThrow(PageContextError);
  });

  it("rejects a route that does not start with /", () => {
    expect(() =>
      renderHook(() => usePageContext(), {
        wrapper: withProvider({ ...base, route: "workspace" }),
      })
    ).toThrow(PageContextError);
  });

  it("returns null when no provider is mounted", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    const { result } = renderHook(() => usePageContext());
    expect(result.current).toBeNull();
    spy.mockRestore();
  });
});
