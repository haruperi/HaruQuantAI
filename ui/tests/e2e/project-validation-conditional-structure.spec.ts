import { test, expect } from "./frontendStructureFixtures";

test("conditional dispatcher preserves hidden branch selections and nonportfolio guard", async ({
  page,
}, info) => {
  await page.goto("/builder");
  await page.evaluate(async () => {
    const reactPath = "/node_modules/.vite/deps/react.js";
    const domPath = "/node_modules/.vite/deps/react-dom_client.js";
    const componentPath =
      "/app/plugins/project/ProjectWorkbench/results/tabs/ConditionalTabs.tsx";
    const resultPath =
      "/app/plugins/project/ProjectWorkbench/results/resultsModel.ts";
    const React = (await import(reactPath)).default;
    const { createRoot } = (await import(domPath)).default;
    const { ConditionalTabs } = await import(componentPath);
    const { demoResult } = await import(resultPath);
    const result = { ...demoResult("str-1", "Strategy 001"), portfolio: true };
    const host = document.createElement("div");
    host.id = "conditional-fixture";
    host.style.cssText =
      "position:fixed;inset:70px 60px;z-index:10000;background:#292929;color:#ccc;overflow:auto";
    const controls = document.createElement("div");
    document.body.append(host);
    const content = document.createElement("div");
    content.style.cssText = "position:relative;height:calc(100% - 32px)";
    controls.style.cssText = "position:relative;z-index:1;height:32px";
    host.append(controls, content);
    const root = createRoot(content);
    for (const id of [
      "correlation",
      "monteCarloTests",
      "stockpicker",
      "tradesOnChart",
      "unknown",
      "nonportfolio",
    ]) {
      const button = document.createElement("button");
      button.textContent = "Fixture " + id;
      button.onclick = () =>
        root.render(
          React.createElement(ConditionalTabs, {
            id: id === "nonportfolio" ? "correlation" : id,
            result:
              id === "nonportfolio" ? { ...result, portfolio: false } : result,
          }),
        );
      controls.append(button);
    }
    root.render(
      React.createElement(ConditionalTabs, { id: "correlation", result }),
    );
  });
  const fixture = page.locator("#conditional-fixture");
  await fixture.getByLabel("Correlation by").selectOption("Week");
  await expect(fixture).toContainText("0.36");
  await fixture
    .getByRole("button", { name: "Fixture monteCarloTests", exact: true })
    .click();
  await fixture.getByLabel("Test choice").selectOption("Randomly skip trades");
  await expect(fixture).toContainText("95%");
  await fixture
    .getByRole("button", { name: "Fixture correlation", exact: true })
    .click();
  await expect(fixture.getByLabel("Correlation by")).toHaveValue("Week");
  await fixture
    .getByRole("button", { name: "Fixture monteCarloTests", exact: true })
    .click();
  await expect(fixture.getByLabel("Test choice")).toHaveValue(
    "Randomly skip trades",
  );
  await page.screenshot({
    path: info.outputPath("conditional-mock-preview.png"),
  });
  await fixture
    .getByRole("button", { name: "Fixture stockpicker", exact: true })
    .click();
  await expect(fixture).toContainText("NVDA");
  await fixture
    .getByRole("button", { name: "Fixture tradesOnChart", exact: true })
    .click();
  await expect(fixture.getByRole("img")).toBeVisible();
  await fixture
    .getByRole("button", { name: "Fixture unknown", exact: true })
    .click();
  await expect(fixture).toContainText("Trades on chart / stored mock data");
  await fixture
    .getByRole("button", { name: "Fixture nonportfolio", exact: true })
    .click();
  await expect(fixture).toContainText("Strategy is not a portfolio.");
});
test("cross checks snapshots and disabled links retain session-only behavior", async ({
  page,
}, info) => {
  await page.goto("/builder?tab=settings");
  await page
    .getByRole("tab", { name: "Cross checks (robustness)", exact: true })
    .click();
  const panel = page.locator(".cross-checks");
  await panel
    .getByRole("button", { name: "Load cross checks", exact: true })
    .click();
  await expect(panel.getByRole("status")).toHaveText(
    "No local demo snapshot saved yet.",
  );
  const check = panel.getByRole("checkbox", {
    name: "What If simulations",
    exact: true,
  });
  await check.check();
  await panel
    .getByRole("button", { name: "Save cross checks", exact: true })
    .click();
  await check.uncheck();
  await panel
    .getByRole("button", { name: "Load cross checks", exact: true })
    .click();
  await expect(check).toBeChecked();
  await panel
    .getByRole("checkbox", { name: "Disable all cross checks", exact: true })
    .check();
  await expect(check).toBeDisabled();
  await panel
    .getByRole("button", { name: "3 simulation(s)", exact: true })
    .click();
  await page.getByLabel("Enable cross check", { exact: true }).focus();
  await page.keyboard.press("Space");
  await expect(
    page.getByLabel("Enable cross check", { exact: true }),
  ).not.toBeChecked();
  await page.screenshot({
    path: info.outputPath("cross-checks-disabled-dialog.png"),
  });
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await panel
    .getByRole("checkbox", { name: "Disable all cross checks", exact: true })
    .uncheck();
  await expect(check).not.toBeChecked();
  await panel
    .getByRole("button", { name: "Load cross checks", exact: true })
    .click();
  await expect(check).toBeChecked();
});
test("ranking task controls and notes preserve local drafts and browser formatting", async ({
  page,
}, info) => {
  await page.goto("/optimizer?tab=settings");
  await page.getByRole("tab", { name: "Ranking", exact: true }).click();
  const ranking = page.locator("#ranking-settings");
  await expect(ranking).toContainText(
    "Maximum optimizations to store in databank",
  );
  await expect(
    ranking.getByText("Stop generation when", { exact: true }),
  ).toHaveCount(0);
  await ranking
    .getByRole("button", { name: "+ Add criterion", exact: true })
    .click();
  const methods = ranking.getByLabel("Fitness method", { exact: true });
  const count = await methods.count();
  expect(count).toBeGreaterThan(1);
  const choice = await methods
    .first()
    .locator("option")
    .last()
    .getAttribute("value");
  expect(choice).not.toBeNull();
  await methods.first().selectOption(choice!);
  for (let i = 0; i < count; i++)
    await expect(methods.nth(i)).toHaveValue(choice!);
  await ranking
    .getByRole("button", { name: "Remove criterion", exact: true })
    .last()
    .click();
  await expect(methods).toHaveCount(count - 1);
  await page.getByRole("tab", { name: "Notes", exact: true }).click();
  const notes = page.getByRole("textbox", { name: "Notes", exact: true });
  await notes.fill("Local review");
  await page.getByRole("button", { name: "Bold", exact: true }).click();
  await expect(notes).toBeFocused();
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toBe("Link URL");
    await dialog.dismiss();
  });
  await page.getByRole("button", { name: "Link", exact: true }).click();
  await page
    .locator(".notesToolbar")
    .getByRole("button", { name: "Save", exact: true })
    .click();
  await expect(page.getByText("Saved (demo)", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Results", exact: true }).click();
  await page.getByRole("tab", { name: "Full settings", exact: true }).click();
  await expect(notes).toHaveText("Local review");
  await page.screenshot({ path: info.outputPath("notes-session-draft.png") });
});
