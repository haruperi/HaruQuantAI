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

    expect(html).toContain("hsl_ema_crossover_v1.py");
    expect(html).toContain("Copy Code");
    expect(html).toContain("Download hsl_ema_crossover_v1.py");
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
