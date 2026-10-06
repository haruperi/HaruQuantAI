import { describe, expect, it } from "vitest";
import { strategies } from "../../../../app/plugins/databank/fixtures";
import { buildComparisonModel } from "../../../../app/plugins/databank/ResultsDatabankActions/tools/compareStrategies/CompareStrategiesService";

describe("actual local comparison calculations", () => {
  it("uses fixture metrics and retains lower-is-better drawdown semantics", () => {
    const model = buildComparisonModel(strategies[0], strategies[1]);
    expect(model.kpis.find((row) => row.label === "Net profit")?.v1).toBe(
      strategies[0].metrics.netProfit,
    );
    expect(
      model.kpis.find((row) => row.label === "Max drawdown")?.isHigherBetter,
    ).toBe(false);
    expect(
      model.kpis.find((row) => row.label === "Profit factor")?.format(1.2),
    ).toBe("1.20");
  });
  it("places unequal curves on one scale and retains single-point omission", () => {
    const first = {
      ...strategies[0],
      equity: [
        { time: "2025-01-01", value: 100, drawdown: 0 },
        { time: "2025-01-02", value: 200, drawdown: 0 },
      ],
    };
    const second = {
      ...strategies[1],
      equity: [
        { time: "2025-01-01", value: 150, drawdown: 0 },
        { time: "2025-01-02", value: 300, drawdown: 0 },
      ],
    };
    const model = buildComparisonModel(first, second);
    expect(model.points1).toBe("12.0,138.0 668.0,75.0");
    expect(model.points2).toBe("12.0,106.5 668.0,12.0");
    expect(
      buildComparisonModel(
        { ...first, equity: first.equity.slice(0, 1) },
        second,
      ).points1,
    ).toBe("");
  });
});
