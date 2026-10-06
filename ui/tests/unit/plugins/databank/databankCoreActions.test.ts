import { describe, expect, it, vi } from "vitest";
import {
  confirmClearAll,
  getCurrentDatabankStrategy,
  requestClearAllConfirmation,
  refreshDatabank,
} from "../../../../app/plugins/databank/ResultsDatabankActions/module";
import { strategies } from "../../../../app/plugins/databank/fixtures";

describe("existing core databank behavior", () => {
  it("preserves current strategy precedence and empty fallback", () => {
    const [first, second] = strategies;
    expect(
      getCurrentDatabankStrategy([first, second], first.id, [second]),
    ).toBe(first);
    expect(getCurrentDatabankStrategy([first], "missing", [second])).toBe(
      second,
    );
    expect(getCurrentDatabankStrategy([], undefined, [])).toBeUndefined();
  });
  it("confirms clearing without adding selection guards", () => {
    const open = vi.fn();
    const remove = vi.fn();
    const notify = vi.fn();
    requestClearAllConfirmation(open);
    expect(open).toHaveBeenCalledOnce();
    expect(remove).not.toHaveBeenCalled();
    const ids = ["one", "two"];
    confirmClearAll(ids, remove, notify);
    expect(remove).toHaveBeenCalledWith(ids);
    expect(notify).toHaveBeenCalledWith("Databank cleared");
  });
  it("retains notification-only refresh", () => {
    const notify = vi.fn();
    refreshDatabank(notify);
    expect(notify).toHaveBeenCalledExactlyOnceWith("Databank reloaded");
  });
});
