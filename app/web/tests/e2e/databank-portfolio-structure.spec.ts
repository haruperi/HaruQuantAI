import { test, expect } from "./frontendStructureFixtures";
const actions = [
  "Merge strategies",
  "Split strategies",
  "Merge WF results",
  "Move to Portfolio Composer",
  "Move to Portfolio Master",
];
for (const selected of [false, true]) {
  test(`portfolio actions remain deferred and preserve rows/route with ${selected ? "multiple" : "no"} selection`, async ({
    page,
  }, info) => {
    await page.goto("/builder");
    await page
      .getByRole("button", { name: "Expand databanks", exact: true })
      .click();
    const pane = page.locator(".sqn-databanks");
    const boxes = pane.getByRole("checkbox", { name: /^Select Strategy / });
    if (selected) {
      await boxes.nth(0).check();
      await boxes.nth(1).check();
    }
    const rows = await pane.locator("tbody tr").count();
    for (const action of actions) {
      await pane
        .getByRole("button", { name: "Portfolio", exact: true })
        .click();
      await pane.getByRole("menuitem", { name: action, exact: true }).click();
      await expect(page.getByRole("dialog")).toHaveCount(0);
      await expect(page).toHaveURL(/\/builder(?:\?|$)/);
      await expect(pane.locator("tbody tr")).toHaveCount(rows);
      await expect(pane.locator(".sqx-records-count")).toContainText(
        "Records: 40",
      );
      if (selected) {
        await expect(boxes.nth(0)).toBeChecked();
        await expect(boxes.nth(1)).toBeChecked();
      }
    }
    await page
      .getByRole("button", { name: "Notifications", exact: true })
      .click();
    for (const action of actions)
      await expect(page.locator(".notifications")).toContainText(
        `Portfolio: ${action} deferred — UI prototype (no engine connected)`,
      );
    await page.screenshot({
      path: info.outputPath(
        `deferred-portfolio-${selected ? "multiple" : "none"}.png`,
      ),
    });
  });
}
