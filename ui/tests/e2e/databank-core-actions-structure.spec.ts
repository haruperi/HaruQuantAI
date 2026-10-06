import { test, expect } from "./frontendStructureFixtures";

test("clear cancellation preserves fixtures; confirmation clears current bank only", async ({
  page,
}, info) => {
  await page.goto("/builder");
  await page
    .getByRole("button", { name: "Expand databanks", exact: true })
    .click();
  const pane = page.locator(".sqn-databanks");
  await pane.getByRole("button", { name: "Clear all", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("clear all the reports");
  await page.screenshot({ path: info.outputPath("clear-confirmation.png") });
  await page.keyboard.press("Escape");
  await expect(pane.locator(".sqx-records-count")).toContainText("Records: 40");
  await pane.getByRole("button", { name: "Clear all", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Yes", exact: true })
    .click();
  await expect(
    pane.getByText("No results in databank.", { exact: true }),
  ).toBeVisible();
  await pane.getByRole("tab", { name: "Last generation", exact: true }).click();
  await expect(pane.locator(".sqx-records-count")).toContainText("Records: 18");
});
