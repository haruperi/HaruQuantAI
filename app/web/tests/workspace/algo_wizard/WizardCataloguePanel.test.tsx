import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import {
  createAlgoWizardApiClient,
  DEFAULT_WIZARD_CONSTANTS_BUNDLE,
  filterCatalogueBlocks,
} from "../../../workspaces/algo_wizard/algoWizardModel";
import { WizardCataloguePanel } from "../../../workspaces/algo_wizard/WizardCataloguePanel";

describe("WizardCataloguePanel (Phase 5.9: I-ServletConstants)", () => {
  it("renders searchable HSL block categories, parameter metadata, and wizard constants", () => {
    const html = renderToStaticMarkup(
      <WizardCataloguePanel bundle={DEFAULT_WIZARD_CONSTANTS_BUNDLE} />,
    );

    expect(html).toContain("HSL 1.0 Block Catalogue (BlockRegistry)");
    expect(html).toContain("VALUE");
    expect(html).toContain("EXPRESSION");
    expect(html).toContain("CONDITION");
    expect(html).toContain("ACTION");
    expect(html).toContain("RULE");
    expect(html).toContain("indicator.rsi");
    expect(html).toContain("Relative Strength Index (RSI)");
    expect(html).toContain("default=14, min=2, max=200");
    expect(html).toContain("selected_tf_only");
    expect(html).toContain("fixed_per_lot");
    expect(html).toContain("on_bar_open");
  });

  it("filters HSL blocks by node family and search query", () => {
    const expressionOnly = filterCatalogueBlocks(
      DEFAULT_WIZARD_CONSTANTS_BUNDLE.blocks,
      "EXPRESSION",
      "",
    );
    expect(expressionOnly.map((b) => b.semantic_id)).toEqual(["indicator.rsi"]);

    const queried = filterCatalogueBlocks(
      DEFAULT_WIZARD_CONSTANTS_BUNDLE.blocks,
      "ALL",
      "crosses",
    );
    expect(queried.map((b) => b.semantic_id)).toEqual([
      "comparison.crosses_above",
    ]);

    const filteredHtml = renderToStaticMarkup(
      <WizardCataloguePanel
        bundle={DEFAULT_WIZARD_CONSTANTS_BUNDLE}
        initialFamily="CONDITION"
        initialQuery="cross"
      />,
    );
    expect(filteredHtml).toContain("comparison.crosses_above");
    expect(filteredHtml).not.toContain("indicator.rsi");
  });

  it("fetches constants bundle via /constants/getAll client binding", async () => {
    const fetchFn = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          request_id: "req-1",
          data: DEFAULT_WIZARD_CONSTANTS_BUNDLE,
        }),
      ),
    );
    const client = createAlgoWizardApiClient({ fetchFn, baseUrl: "/api" });
    const bundle = await client.getConstantsBundle("req-1");

    expect(fetchFn).toHaveBeenCalledWith(
      "/api/constants/getAll",
      expect.objectContaining({ method: "POST" }),
    );
    expect(bundle.blocks).toHaveLength(5);
  });
});
