import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import {
  createAlgoWizardApiClient,
  DEFAULT_EXPORT_TARGETS,
  DEFAULT_HSL_STRATEGY_DOCUMENT,
} from "../../../workspaces/algo_wizard/algoWizardModel";
import { CloudExportPanel } from "../../../workspaces/algo_wizard/CloudExportPanel";

describe("CloudExportPanel (Phase 5.9: I-ServletAlgoCloud)", () => {
  it("renders all 4 import sources, all 8 export target platforms, code preview, and copy/download actions", () => {
    const html = renderToStaticMarkup(
      <CloudExportPanel
        document={DEFAULT_HSL_STRATEGY_DOCUMENT}
        targets={DEFAULT_EXPORT_TARGETS}
        initialImportSource="databank"
        initialPlatform="mql5"
      />,
    );

    for (const source of ["editor", "file", "databank", "backtest_id"]) {
      expect(html).toContain(source);
    }

    for (const platform of [
      "python",
      "mql4",
      "mql5",
      "easylanguage",
      "ninjatrader",
      "jforex",
      "pseudo_code",
      "hsl_json",
    ]) {
      expect(html).toContain(platform);
    }

    expect(html).toContain("Generate an export to preview its code.");
    expect(html).toContain("unavailable for HSL");
    expect(html).not.toContain("class EMACrossoverStrategy");
  });

  it("calls /algocloud/import and /algocloud/export endpoints via typed client", async () => {
    const fetchFn = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            request_id: "req-cloud",
            data: {
              strategy_id: "hsl_ema_crossover_v1",
              target_platform: "mql4",
              filename: "hsl_ema_crossover_v1.mq4",
              content: "// MQL4 EA",
              sha256: "abc123",
            },
          }),
        ),
      ),
    );
    const client = createAlgoWizardApiClient({ fetchFn });

    await client.importCloudStrategy({
      source: "databank",
      databank_name: "default",
      strategy_name: "EMA Crossover",
    });
    expect(fetchFn).toHaveBeenCalledWith(
      "/algocloud/import",
      expect.objectContaining({ method: "POST" }),
    );

    const exported = await client.exportCloudStrategy(
      DEFAULT_HSL_STRATEGY_DOCUMENT,
      "mql4",
    );
    expect(fetchFn).toHaveBeenCalledWith(
      "/algocloud/export",
      expect.objectContaining({ method: "POST" }),
    );
    expect(exported.filename).toBe("hsl_ema_crossover_v1.mq4");
  });
});

describe("HSL transport boundaries", () => {
  it("rejects backend errors instead of returning undefined success data", async () => {
    const fetchFn = vi.fn(
      async () =>
        new Response(
          JSON.stringify({ error: { message: "Unsupported HSL target" } }),
          { status: 400 },
        ),
    );
    const client = createAlgoWizardApiClient({ fetchFn });
    await expect(
      client.exportCloudStrategy(DEFAULT_HSL_STRATEGY_DOCUMENT, "mql5"),
    ).rejects.toThrow("Unsupported HSL target");
  });
  it("projects actual backend catalogue field names into display metadata", async () => {
    const fetchFn = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            data: {
              revision: "registry-v1",
              timeframes: [
                { code: "H1", label: "1 hour", description: "Hourly" },
              ],
              lifecycle_events: [],
              commission_methods: [
                {
                  method_id: "per_lot",
                  name: "Per lot",
                  unit: "per_lot",
                  default_value: 0,
                },
              ],
              blocks: [
                {
                  semantic_id: "indicator.rsi",
                  registry_id: "rsi",
                  name: "RSI",
                  family: "EXPRESSION",
                  category: "momentum",
                  return_type: "series",
                  required_inputs: ["close"],
                  parameters: [
                    {
                      name: "period",
                      param_type: "int",
                      required: false,
                      default: 14,
                    },
                  ],
                },
              ],
            },
          }),
        ),
    );
    const bundle = await createAlgoWizardApiClient({
      fetchFn,
    }).getConstantsBundle();
    expect(bundle.timeframes[0].key).toBe("H1");
    expect(bundle.blocks[0].label).toBe("RSI");
    expect(bundle.blocks[0].parameters[0].default_value).toBe(14);
    expect(bundle.commission_methods[0].label).toBe("Per lot");
  });
});
