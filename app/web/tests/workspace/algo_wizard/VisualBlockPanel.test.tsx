import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  negateHSLCondition,
  type HSLConditionNode,
} from "../../../workspaces/algo_wizard/algoWizardModel";
import { VisualBlockPanel } from "../../../workspaces/algo_wizard/VisualBlockPanel";

describe("VisualBlockPanel (Phase 5.9: I-ServletAlgoWizard)", () => {
  it("renders condition negation, custom blocks, block groups, resource check, and wizard backtest preview", () => {
    const html = renderToStaticMarkup(
      <VisualBlockPanel
        resourceCheck={{
          ready: false,
          missing_symbols: ["GBPUSD"],
          missing_timeframes: ["M5"],
          missing_blocks: ["custom.missing_filter"],
        }}
      />,
    );

    expect(html).toContain("Visual AST Condition &amp; Block Manager");
    expect(html).toContain("comparison.crosses_above");
    expect(html).toContain("custom.rsi_oversold");
    expect(html).toContain("group.momentum_entries");
    expect(html).toContain("MISSING DEPENDENCIES");
    expect(html).toContain("Missing Symbols: GBPUSD");
    expect(html).toContain("Missing Timeframes: M5");
    expect(html).toContain("Missing Blocks: custom.missing_filter");
    expect(html).toContain("No backtest has been run.");
    expect(html).not.toContain("Net PnL:");
  });

  it("negates comparison, not, and De Morgan logical conditions deterministically", () => {
    const crossesAbove: HSLConditionNode = {
      type: "comparison",
      operator: "crosses_above",
    };
    const crossesBelow = negateHSLCondition(crossesAbove);
    expect(crossesBelow.operator).toBe("crosses_below");

    const doubleNegated = negateHSLCondition({
      type: "not",
      condition: crossesAbove,
    });
    expect(doubleNegated).toEqual(crossesAbove);

    const compoundAnd: HSLConditionNode = {
      type: "logical",
      operator: "and",
      conditions: [
        { type: "comparison", operator: "greater_than" },
        { type: "comparison", operator: "equal" },
      ],
    };
    const distributed = negateHSLCondition(compoundAnd, true);
    expect(distributed.type).toBe("logical");
    expect(distributed.operator).toBe("or");
    expect(distributed.conditions?.map((c) => c.operator)).toEqual([
      "less_or_equal",
      "not_equal",
    ]);
  });
});
