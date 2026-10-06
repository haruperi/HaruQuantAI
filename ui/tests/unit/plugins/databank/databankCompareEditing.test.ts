import { describe, expect, it, vi } from "vitest";
import { requestCompareStrategies } from "../../../../app/plugins/databank/ResultsDatabankActions/tools/compareStrategies/module";
import { handleEditItem } from "../../../../app/plugins/databank/ResultsDatabankActions/tools/edit/module";
import { requestRunCa } from "../../../../app/plugins/databank/ResultsDatabankActions/tools/runCa/module";

describe("existing deferred and latent adapters", () => {
  it("preserves exact edit and Run CA deferred labels", () => {
    const deferred = vi.fn();
    expect(handleEditItem("Edit:Parameters", deferred)).toBe(true);
    expect(handleEditItem("Edit:Strategy", deferred)).toBe(true);
    expect(handleEditItem("Edit:Unknown", deferred)).toBe(false);
    requestRunCa(deferred);
    expect(deferred.mock.calls).toEqual([
      ["Tools: Edit:Parameters"],
      ["Tools: Edit:Strategy"],
      ["Tools: Run CA"],
    ]);
  });
  it("retains the latent comparison opening callback without new guards", () => {
    const open = vi.fn();
    requestCompareStrategies(open);
    expect(open).toHaveBeenCalledOnce();
  });
});
