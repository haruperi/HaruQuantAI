import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import {
  createAlgoWizardApiClient,
  DEFAULT_HSL_STRATEGY_DOCUMENT,
  sortRulesByPriority,
  type HSLRuleNode,
} from "../../../workspaces/algo_wizard/algoWizardModel";
import { StrategyDocumentPanel } from "../../../workspaces/algo_wizard/StrategyDocumentPanel";

describe("StrategyDocumentPanel (Phase 5.9: I-ServletStrategy)", () => {
  it("renders validation status, parameters vs variables, priority-ordered rules, and lifecycle controls", () => {
    const html = renderToStaticMarkup(
      <StrategyDocumentPanel
        document={DEFAULT_HSL_STRATEGY_DOCUMENT}
        status="RUNNING"
        revision={3}
        validation={{ valid: true, issues: [] }}
      />,
    );

    expect(html).toContain("EMA Crossover Strategy");
    expect(html).toContain("ID: hsl_ema_crossover_v1");
    expect(html).toContain("Revision: r3");
    expect(html).toContain("Status: RUNNING");
    expect(html).toContain("Validation Status: VALID");
    expect(html).toContain("fast_period");
    expect(html).toContain("slow_period");
    expect(html).toContain("entry_count");
    expect(html).toContain("session_active");
    expect(html).toContain("Start Strategy");
    expect(html).toContain("Stop Strategy");
    expect(html).toContain("Remove Strategy");
  });

  it("renders validation issues when HSL document is invalid and sorts rules by (priority, id)", () => {
    const unorderedRules: HSLRuleNode[] = [
      {
        ...DEFAULT_HSL_STRATEGY_DOCUMENT.strategy.rules[1],
        id: "rule_b",
        priority: 20,
      },
      {
        ...DEFAULT_HSL_STRATEGY_DOCUMENT.strategy.rules[0],
        id: "rule_c",
        priority: 10,
      },
      {
        ...DEFAULT_HSL_STRATEGY_DOCUMENT.strategy.rules[0],
        id: "rule_a",
        priority: 10,
      },
    ];
    const sorted = sortRulesByPriority(unorderedRules);
    expect(sorted.map((r) => r.id)).toEqual(["rule_a", "rule_c", "rule_b"]);

    const invalidHtml = renderToStaticMarkup(
      <StrategyDocumentPanel
        document={{
          ...DEFAULT_HSL_STRATEGY_DOCUMENT,
          strategy: {
            ...DEFAULT_HSL_STRATEGY_DOCUMENT.strategy,
            rules: unorderedRules,
          },
        }}
        status="ERROR"
        validation={{
          valid: false,
          issues: [
            {
              code: "WIZARD_LOOKAHEAD_SHIFT_INVALID",
              message: "Negative shift -1 is prohibited",
              path: "strategy.rules[0].when.left.context.shift",
            },
          ],
        }}
      />,
    );

    expect(invalidHtml).toContain("Validation Status: INVALID");
    expect(invalidHtml).toContain("WIZARD_LOOKAHEAD_SHIFT_INVALID");
    expect(invalidHtml.indexOf("rule_a")).toBeLessThan(
      invalidHtml.indexOf("rule_b"),
    );
  });

  it("calls /strategy/start, /strategy/stop, and /strategy/remove endpoints via client", async () => {
    const fetchFn = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            request_id: "req-strat",
            data: {
              strategy_id: "hsl_ema_crossover_v1",
              status: "RUNNING",
              removed: true,
            },
          }),
        ),
      ),
    );
    const client = createAlgoWizardApiClient({ fetchFn });

    await client.startStrategy("hsl_ema_crossover_v1");
    expect(fetchFn).toHaveBeenCalledWith(
      "/strategy/start",
      expect.objectContaining({ method: "POST" }),
    );

    await client.stopStrategy("hsl_ema_crossover_v1");
    expect(fetchFn).toHaveBeenCalledWith(
      "/strategy/stop",
      expect.objectContaining({ method: "POST" }),
    );

    await client.removeStrategy("hsl_ema_crossover_v1");
    expect(fetchFn).toHaveBeenCalledWith(
      "/strategy/remove",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
