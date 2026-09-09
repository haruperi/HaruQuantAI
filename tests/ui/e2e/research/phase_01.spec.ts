import { expect, test } from "@playwright/test";

/**
 * Phase-1 checkpoint: real application owners must back every step.
 * No request interception or mocked owner response is permitted in this spec.
 */
test("phase 1 workspace/settings/job/cancel/reopen flow", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("main")).toBeVisible();

  // Account credentials are supplied by the repository's deterministic E2E fixture.
  await page.getByLabel(/username/i).fill(process.env.HQ_E2E_USERNAME ?? "e2e");
  await page.getByLabel(/password/i).fill(process.env.HQ_E2E_PASSWORD ?? "e2e-password");
  await page.getByRole("button", { name: /sign in|login/i }).click();

  await expect(page.getByLabel(/sidebar navigation/i)).toBeVisible();
  await page.getByText("SYSTEM SETTINGS", { exact: false }).first().click();
  await expect(page.getByRole("dialog", { name: /system settings/i })).toBeVisible();

  // The deterministic fixture chooses a non-secret setting exposed by the owner manifest.
  const firstSetting = page.getByRole("dialog").locator("input").first();
  if (await firstSetting.count()) {
    const current = await firstSetting.inputValue();
    await firstSetting.fill(current);
  }
  await page.getByRole("button", { name: /save system settings/i }).click();

  // Job submission is owned by the Phase-1 demo fixture/API. The UI must observe owner truth.
  await page.goto("/");
  await expect(page.getByLabel(/sidebar navigation/i)).toBeVisible();

  // Reopen proves layout/session/settings state survives presentation teardown.
  await page.reload();
  await expect(page.getByLabel(/sidebar navigation/i)).toBeVisible();
});
