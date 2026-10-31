import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import {
  createAlgoWizardApiClient,
  DEFAULT_HSL_STRATEGY_DOCUMENT,
  DEFAULT_WIZARD_EXAMPLES,
} from "../../../workspaces/algo_wizard/algoWizardModel";
import {
  allocateSanitizedStrategyName,
  WizardWorkspace,
} from "../../../workspaces/algo_wizard/WizardWorkspace";

describe("WizardWorkspace (Phase 5.9: I-AppWizard)", () => {
  it("coordinates example loader, StrategyNames sanitization/uniqueness, Retester handoff, and sub-panels", () => {
    const html = renderToStaticMarkup(
      <WizardWorkspace
        initialDocument={DEFAULT_HSL_STRATEGY_DOCUMENT}
        existingStrategyNames={[
          "EMA Crossover Strategy",
          "EMA Crossover Strategy (2)",
        ]}
        examples={DEFAULT_WIZARD_EXAMPLES}
        retesterHandoff={{
          strategy_id: "hsl_ema_crossover_v1",
          name: "EMA Crossover Strategy",
          document_hash: "sha256-xyz",
          hsl_document: DEFAULT_HSL_STRATEGY_DOCUMENT,
          compiled_rule_count: 2,
          status: "READY",
        }}
      />,
    );

    expect(html).toContain("AlgoWizard HSL 1.0 Strategy Studio");
    expect(html).toContain("EMA Crossover Strategy (3)");
    expect(html).toContain("/AlgoWizard/examples/examples.json");
    expect(html).toContain("/algowizard/loadExample");
    expect(html).toContain("/algowizard/saveToRetester");
    expect(html).toContain("Retester Ready: hsl_ema_crossover_v1");
    expect(html).toContain("HSL 1.0 Block Catalogue (BlockRegistry)");
    expect(html).toContain("Visual AST Condition &amp; Block Manager");
    expect(html).toContain("Cloud Strategy Import &amp; Multi-Target Code Export");
  });

  it("sanitizes illegal characters and allocates collision-free names via StrategyNames", () => {
    expect(
      allocateSanitizedStrategyName("My/Strategy:V1", [
        "MyStrategyV1",
        "MyStrategyV1 (4)",
      ]),
    ).toBe("MyStrategyV1 (5)");

    expect(allocateSanitizedStrategyName("///", ["New Strategy"])).toBe(
      "New Strategy (2)",
    );
  });

  it("calls /AlgoWizard/examples/examples.json, /algowizard/loadExample, and /algowizard/saveToRetester", async () => {
    const fetchFn = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            request_id: "req-wz",
            data: DEFAULT_WIZARD_EXAMPLES,
          }),
        ),
      ),
    );
    const client = createAlgoWizardApiClient({ fetchFn });

    await client.listExamples();
    expect(fetchFn).toHaveBeenCalledWith(
      "/AlgoWizard/examples/examples.json",
      expect.objectContaining({ method: "GET" }),
    );

    await client.loadExample("ema_crossover");
    expect(fetchFn).toHaveBeenCalledWith(
      "/algowizard/loadExample",
      expect.objectContaining({ method: "POST" }),
    );

    await client.saveToRetester(DEFAULT_HSL_STRATEGY_DOCUMENT);
    expect(fetchFn).toHaveBeenCalledWith(
      "/algowizard/saveToRetester",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
