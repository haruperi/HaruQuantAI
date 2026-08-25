import React from "react";
import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { SelectionProvider, useSelection } from "../selection";

describe("SelectionContext", () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <SelectionProvider>{children}</SelectionProvider>
  );

  it("manages multi-item selection state", () => {
    const { result } = renderHook(() => useSelection("sel-table"), { wrapper });

    expect(result.current.selectedKeys).toEqual([]);
    expect(result.current.isSelected("row-1")).toBe(false);

    act(() => {
      result.current.select(["row-1", "row-2"]);
    });

    expect(result.current.selectedKeys).toEqual(["row-1", "row-2"]);
    expect(result.current.isSelected("row-1")).toBe(true);
    expect(result.current.isSelected("row-3")).toBe(false);

    act(() => {
      result.current.toggle("row-3");
    });

    expect(result.current.isSelected("row-3")).toBe(true);

    act(() => {
      result.current.clear();
    });

    expect(result.current.selectedKeys).toEqual([]);
  });

  it("handles select-all flag", () => {
    const { result } = renderHook(() => useSelection("sel-all-test"), { wrapper });

    act(() => {
      result.current.selectAll(true);
    });

    expect(result.current.isAllSelected).toBe(true);
    expect(result.current.isSelected("any-key")).toBe(true);
  });
});
