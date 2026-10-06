import { describe, expect, it, vi } from "vitest";
import {
  label as sourceCodeLabel,
  openSave,
} from "../../../../app/plugins/databank/ResultsDatabankActions/save/sourceCode/module";
import {
  SAVE_MENU,
  openSimulatedSave,
  completeSimulatedSave,
} from "../../../../app/plugins/databank/ResultsDatabankActions/save/module";
describe("retained simulated Save boundary", () => {
  it("routes the flat Source code descriptor through the existing generic opener", () => {
    const open = vi.fn();
    openSave(open);
    expect(sourceCodeLabel).toBe("Source code");
    expect(open).toHaveBeenCalledExactlyOnceWith("Source code");
  });
  it.each(["", "HTML report", "PDF report", "Source code", "  custom  "])(
    "preserves exact format %j without added guard or export",
    (format) => {
      const open = vi.fn();
      const deferred = vi.fn();
      openSimulatedSave(format, open);
      expect(open).toHaveBeenCalledExactlyOnceWith(format);
      completeSimulatedSave(format, deferred);
      expect(deferred).toHaveBeenCalledExactlyOnceWith(`Save: ${format}`);
    },
  );
  it("retains all seven menu choices and order", () => {
    expect(SAVE_MENU).toEqual([
      "Save to SQ X format",
      "HTML report",
      "PDF report",
      "Source code",
      "Export databank contents",
      "Save stats in SQ3 format",
      "Export strategy trades to CSV/XLSX",
    ]);
  });
});
