import { describe, expect, it, vi } from "vitest";
import {
  PORTFOLIO_MENU,
  dispatchPortfolioAction,
} from "../../../../app/plugins/databank/ResultsDatabankActions/portfolio/module";
describe("retained deferred portfolio dispatch", () => {
  it("keeps five menu choices in original order", () => {
    expect(PORTFOLIO_MENU).toEqual([
      "Merge strategies",
      "Split strategies",
      "Merge WF results",
      "Move to Portfolio Composer",
      "Move to Portfolio Master",
    ]);
  });
  it.each([
    "Merge strategies",
    "Split strategies",
    "Merge WF results",
    "Move to Portfolio Composer",
    "Move to Portfolio Master",
    "unknown",
    "  raw  ",
    "",
    undefined,
  ])("preserves exact notice for %j without a new guard", (item) => {
    const deferred = vi.fn();
    dispatchPortfolioAction(item, deferred);
    expect(deferred).toHaveBeenCalledExactlyOnceWith(`Portfolio: ${item}`);
  });
});
