import { test, expect } from "./frontendStructureFixtures";

test("project configuration preserves local preview controls and modal lifecycle", async ({
  page,
}, info) => {
  await page.goto("/optimizer?tab=progress");
  await page.getByRole("button", { name: "Config", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("Project configuration");
  await page.screenshot({ path: info.outputPath("project-config.png") });
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByRole("button", { name: "Start", exact: true }).click();
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Resume", exact: true }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Stop", exact: true }).click();
  await expect(page.locator(".sqd-task-desc")).toContainText("idle");
  await page.screenshot({ path: info.outputPath("project-progress.png") });
});
