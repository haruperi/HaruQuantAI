import { test, expect } from "./frontendStructureFixtures";

test("editing remains deferred and Compare/Run CA menu leaves remain inactive", async ({
  page,
}, info) => {
  await page.goto("/builder");
  await page
    .getByRole("button", { name: "Expand databanks", exact: true })
    .click();
  const pane = page.locator(".sqn-databanks");
  await pane.getByRole("button", { name: "Tools", exact: true }).click();
  for (const name of ["Compare", "Run CA"]) {
    await pane.getByRole("menuitem", { name, exact: true }).click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
  }
  await pane.getByRole("menuitem", { name: "Edit", exact: true }).hover();
  await pane.getByRole("menuitem", { name: "Parameters", exact: true }).click();
  await page
    .getByRole("button", { name: "Notifications", exact: true })
    .click();
  await expect(page.locator(".notifications")).toContainText(
    "Tools: Edit:Parameters deferred — UI prototype (no engine connected)",
  );
  await page.screenshot({ path: info.outputPath("deferred-edit.png") });
});

test("isolated existing comparison modal retains pickers, collapse and close", async ({
  page,
}, info) => {
  await page.goto("/builder");
  await page.evaluate(async () => {
    const reactPath = "/node_modules/.vite/deps/react.js";
    const domPath = "/node_modules/.vite/deps/react-dom_client.js";
    const componentPath =
      "/app/plugins/databank/ResultsDatabankActions/tools/compareStrategies/module.ts";
    const fixturePath = "/app/plugins/databank/fixtures.ts";
    const React = (await import(reactPath)).default;
    const { createRoot } = (await import(domPath)).default;
    const { CompareStrategiesModal } = await import(componentPath);
    const { strategies } = await import(fixturePath);
    const host = document.createElement("div");
    document.body.append(host);
    const root = createRoot(host);
    root.render(
      React.createElement(CompareStrategiesModal, {
        isOpen: true,
        strategies,
        onClose: () => root.unmount(),
      }),
    );
  });
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("Compare last settings of two strategies");
  await dialog.locator("select").nth(1).selectOption("str-3");
  await expect(dialog.locator("select").nth(1)).toHaveValue("str-3");
  await dialog.getByRole("link", { name: "Collapse all", exact: true }).click();
  await expect(dialog.locator("polyline")).toHaveCount(0);
  await dialog.getByRole("link", { name: "Expand all", exact: true }).click();
  await expect(dialog.locator("polyline")).toHaveCount(2);
  await page.screenshot({ path: info.outputPath("comparison-modal.png") });
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
});
