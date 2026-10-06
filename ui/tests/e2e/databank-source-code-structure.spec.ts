import { test, expect } from "./frontendStructureFixtures";
test("Source code remains one flat simulated Save choice without native format submenus", async ({
  page,
}, info) => {
  await page.goto("/builder");
  await page
    .getByRole("button", { name: "Expand databanks", exact: true })
    .click();
  const pane = page.locator(".sqn-databanks");
  const downloads: string[] = [];
  page.on("download", (d) => downloads.push(d.suggestedFilename()));
  await pane.getByRole("button", { name: "Save", exact: true }).click();
  const menu = pane.getByRole("menu", { name: "Save menu", exact: true });
  await expect(menu.getByRole("menuitem")).toHaveCount(7);
  await menu
    .getByRole("menuitem", { name: "Source code", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("heading")).toHaveText("Save / Source code");
  await expect(dialog.getByRole("combobox")).toHaveCount(0);
  await page.screenshot({ path: info.outputPath("flat-source-code-save.png") });
  await dialog.getByRole("button", { name: "Save", exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await page
    .getByRole("button", { name: "Notifications", exact: true })
    .click();
  await expect(page.locator(".notifications")).toContainText(
    "Save: Source code deferred — UI prototype (no engine connected)",
  );
  await expect(pane.locator(".sqx-records-count")).toContainText("Records: 40");
  expect(downloads).toEqual([]);
});
