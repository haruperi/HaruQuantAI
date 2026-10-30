import { test, expect } from "./frontendStructureFixtures";
const formats = [
  "Save to SQ X format",
  "HTML report",
  "PDF report",
  "Source code",
  "Export databank contents",
  "Save stats in SQ3 format",
  "Export strategy trades to CSV/XLSX",
];
test("all Save choices retain generic fields and deferred completion without downloads or selection guards", async ({
  page,
}, info) => {
  await page.goto("/builder");
  await page
    .getByRole("button", { name: "Expand databanks", exact: true })
    .click();
  const pane = page.locator(".sqn-databanks");
  const downloads: string[] = [];
  page.on("download", (d) => downloads.push(d.suggestedFilename()));
  for (const format of formats) {
    await pane.getByRole("button", { name: "Save", exact: true }).click();
    await pane.getByRole("menuitem", { name: format, exact: true }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog.getByRole("heading")).toHaveText(`Save / ${format}`);
    await expect(dialog.getByRole("textbox").nth(1)).toHaveValue("Strategy");
    await expect(dialog.getByRole("textbox").nth(2)).toHaveValue("");
    await dialog.getByRole("textbox").nth(1).fill("Prefix");
    await dialog.getByRole("textbox").nth(2).fill("Suffix");
    if (format === "HTML report")
      await page.screenshot({ path: info.outputPath("simulated-save.png") });
    await dialog.getByRole("button", { name: "Save", exact: true }).click();
    await expect(dialog).toHaveCount(0);
    await expect(pane.locator(".sqx-records-count")).toContainText(
      "Records: 40",
    );
  }
  await page
    .getByRole("button", { name: "Notifications", exact: true })
    .click();
  for (const format of formats)
    await expect(page.locator(".notifications")).toContainText(
      `Save: ${format} deferred — UI prototype (no engine connected)`,
    );
  expect(downloads).toEqual([]);
});
test("Save cancel, Browse, Escape and backdrop reset the transient draft", async ({
  page,
}) => {
  await page.goto("/builder");
  await page
    .getByRole("button", { name: "Expand databanks", exact: true })
    .click();
  const pane = page.locator(".sqn-databanks");
  for (const dismissal of ["Cancel", "Browse", "Escape", "backdrop"]) {
    await pane.getByRole("button", { name: "Save", exact: true }).click();
    await pane
      .getByRole("menuitem", { name: "HTML report", exact: true })
      .click();
    const dialog = page.getByRole("dialog");
    await expect(dialog.getByRole("textbox").nth(1)).toHaveValue("Strategy");
    await dialog.getByRole("textbox").nth(1).fill("Discard");
    if (dismissal === "Escape") await page.keyboard.press("Escape");
    else if (dismissal === "backdrop")
      await page.locator(".modal-backdrop").click({ position: { x: 5, y: 5 } });
    else
      await dialog
        .getByRole("button", { name: dismissal, exact: true })
        .click();
    await expect(dialog).toHaveCount(0);
    await expect(pane.locator(".sqx-records-count")).toContainText(
      "Records: 40",
    );
  }
});
