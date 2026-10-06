import { test, expect } from "./frontendStructureFixtures";

test("optimization surface retains synthetic canvas and local controls", async ({
  page,
}, info) => {
  await page.goto("/optimizer?tab=results");
  await page.evaluate(async () => {
    const reactPath = "/node_modules/.vite/deps/react.js";
    const domPath = "/node_modules/.vite/deps/react-dom_client.js";
    const modulePath =
      "/app/plugins/optimization/ResultsOptimizationProfile/module.ts";
    const React = (await import(reactPath)).default;
    const { createRoot } = (await import(domPath)).default;
    const { OptimizationSurface } = await import(modulePath);
    const host = document.createElement("div");
    host.style.cssText = "position:fixed;inset:0;z-index:99999;background:#111";
    document.body.append(host);
    createRoot(host).render(
      React.createElement(OptimizationSurface, {
        strategyName: "Isolated fixture",
      }),
    );
  });
  await expect(page.locator("canvas")).toBeVisible();
  await expect(page.locator("canvas")).toHaveAttribute("width", "740");
  await page.getByRole("button", { name: "Heatmap", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Heatmap", exact: true }),
  ).toHaveClass(/bg-indigo-600/);
  await page.getByRole("button", { name: "Scatter", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Scatter", exact: true }),
  ).toHaveClass(/bg-indigo-600/);
  await page.getByRole("button", { name: "3D Surface", exact: true }).click();
  await page.getByRole("button", { name: "Reset View", exact: true }).click();
  await page.screenshot({ path: info.outputPath("optimization-surface.png") });
});
