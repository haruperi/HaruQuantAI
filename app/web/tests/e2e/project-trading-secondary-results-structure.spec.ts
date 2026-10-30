import { test, expect } from "./frontendStructureFixtures";

test("money draft survives panel switches and secondary report selection remains local", async ({
  page,
}, info) => {
  await page.goto("/optimizer?tab=settings");
  await page
    .getByRole("tab", { name: "Money management", exact: true })
    .click();
  await page.getByLabel("Initial capital", { exact: true }).fill("12500");
  await page.getByRole("tab", { name: "Results", exact: true }).click();
  await page.getByRole("tab", { name: "Trade analysis", exact: true }).click();
  await page.getByRole("button", { name: "Close Time", exact: true }).click();
  await expect(
    page.getByRole("img", { name: "Profit by close time", exact: true }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Profile chart", exact: true }).click();
  await page
    .getByLabel("Profile chart", { exact: true })
    .selectOption("GBPUSD / H1 / TPO profile");
  await expect(
    page.getByRole("img", { name: "GBPUSD / H1 / TPO profile", exact: true }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Trade analysis", exact: true }).click();
  await expect(
    page.getByRole("img", { name: "Profit by close time", exact: true }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Source Code", exact: true }).click();
  await page.getByLabel("Source code type").selectOption("XML");
  await expect(page.getByLabel("Source code", { exact: true })).toContainText(
    "Format: XML",
  );
  await page.screenshot({ path: info.outputPath("secondary-source.png") });
  await page.getByRole("tab", { name: "Full settings", exact: true }).click();
  await expect(page.getByLabel("Initial capital", { exact: true })).toHaveValue(
    "12500",
  );
  await page.screenshot({ path: info.outputPath("money-management.png") });
});

test("source clipboard denial and temporary success feedback retain existing messages", async ({
  page,
}, info) => {
  await page.goto("/builder?tab=results");
  await page.getByRole("tab", { name: "Source Code", exact: true }).click();
  await page.evaluate(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async () => {
          throw new Error("Denied by test fixture");
        },
      },
    });
  });
  await page
    .getByRole("button", { name: "Copy to clipboard", exact: true })
    .click();
  await expect(page.getByRole("alert")).toHaveText(
    "Clipboard access unavailable. Select the preview and copy manually.",
  );
  await page.screenshot({ path: info.outputPath("clipboard-denied.png") });
  await page.evaluate(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: async () => {} },
    });
  });
  await page
    .getByRole("button", { name: "Copy to clipboard", exact: true })
    .click();
  await expect(
    page.getByText("Copied to clipboard", { exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(
    page.getByText("Copied to clipboard", { exact: true }),
  ).toHaveCount(0, { timeout: 4000 });
});
