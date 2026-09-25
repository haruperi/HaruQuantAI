import { expect, test, type Page } from "@playwright/test";
import { resolve } from "node:path";
const evidence = resolve(
  process.cwd(),
  "../../.agents/logs/2026-09-25T135524_algowizard-ui-parity/verification",
);
const workspace = (page: Page) =>
  page.getByRole("region", { name: "AlgoWizard workspace" });
async function openEMA(page: Page) {
  await workspace(page)
    .getByRole("button", { name: "Open EMA Cross", exact: true })
    .click();
}
test.beforeEach(async ({ page }) => {
  await page.goto("/algowizard");
});

test("empty state, new strategy options, modal cancellation and screenshots", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1891, height: 1026 });
  const aw = workspace(page);
  await expect(
    aw.getByRole("heading", { name: "No strategies loaded" }),
  ).toBeVisible();
  await aw.screenshot({ path: resolve(evidence, "empty.png") });
  await aw.getByRole("button", { name: "New Strategy", exact: true }).click();
  const dialog = page.getByRole("dialog", {
    name: "New strategy",
    exact: true,
  });
  await expect(
    dialog.getByRole("radio", { name: "Simple Editor", exact: true }),
  ).toBeChecked();
  await dialog.screenshot({ path: resolve(evidence, "new-strategy.png") });
  await dialog.getByLabel("Strategy name:").fill("Test strategy");
  await dialog.getByRole("radio", { name: "Full Editor", exact: true }).check();
  await dialog.getByRole("switch").check();
  await dialog.getByRole("button", { name: "Select", exact: true }).click();
  await expect(
    aw.getByRole("tab", { name: "Trading signals", exact: true }),
  ).toBeVisible();
  await expect(
    aw.getByRole("button", { name: "Test strategy", exact: true }).first(),
  ).toBeVisible();
  await aw.getByRole("button", { name: "New", exact: true }).click();
  await page.getByRole("dialog").press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("EMA rule editing, history, menus, independent drafts and dirty close", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1895, height: 1024 });
  const aw = workspace(page);
  await openEMA(page);
  await aw.screenshot({ path: resolve(evidence, "ema-editor.png") });
  await aw.getByRole("button", { name: "Files", exact: true }).click();
  await aw.screenshot({ path: resolve(evidence, "files-menu.png") });
  await expect(
    aw.getByRole("menuitem", { name: "Save changes", exact: true }),
  ).toBeDisabled();
  await page.keyboard.press("Escape");
  await aw
    .getByRole("button", {
      name: "EMA(FastEMA)[1] crosses above EMA(SlowEMA)[1]",
      exact: true,
    })
    .click();
  await page.getByLabel("Selected expression").fill("Close[1] > EMA(25)[1]");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Select", exact: true })
    .click();
  await expect(
    aw.getByRole("button", { name: "Close[1] > EMA(25)[1]", exact: true }),
  ).toBeVisible();
  await aw.getByRole("button", { name: "Undo", exact: true }).click();
  await expect(
    aw.getByRole("button", {
      name: "EMA(FastEMA)[1] crosses above EMA(SlowEMA)[1]",
      exact: true,
    }),
  ).toBeVisible();
  await aw.getByRole("button", { name: "Redo", exact: true }).click();
  await aw.getByRole("button", { name: "Examples", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: /Inside Bar Breakout/ })
    .click();
  await expect(
    aw.getByRole("button", {
      name: "High[1] < High[2] AND Low[1] > Low[2]",
      exact: true,
    }),
  ).toHaveCount(2);
  await aw.getByRole("button", { name: "EMACross *", exact: true }).click();
  await expect(
    aw.getByRole("button", { name: "Close[1] > EMA(25)[1]", exact: true }),
  ).toBeVisible();
  await aw
    .getByRole("button", { name: "Close strategy EMACross", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Cancel", exact: true })
    .click();
  await expect(
    aw.getByRole("button", { name: "EMACross *", exact: true }),
  ).toBeVisible();
  await aw
    .getByRole("button", { name: "Close strategy EMACross", exact: true })
    .click();
  await page.getByRole("button", { name: "Don't save", exact: true }).click();
  await expect(
    aw.getByRole("button", { name: "Close strategy EMACross", exact: true }),
  ).toHaveCount(0);
});

test("rule types, action editor, variables and settings save/cancel", async ({
  page,
}) => {
  const aw = workspace(page);
  await openEMA(page);
  await aw.getByRole("button", { name: "Add rule", exact: true }).click();
  await page.getByLabel("Rule name").fill("Risk guard");
  await page.getByLabel("Rule type").selectOption("If - Then - Else");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Add", exact: true })
    .click();
  await expect(aw.getByText("ELSE", { exact: true })).toBeVisible();
  await aw
    .getByRole("button", { name: "Add action(s)", exact: true })
    .first()
    .click();
  await page.getByLabel("Selected expression").fill("Close all positions");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Select", exact: true })
    .click();
  await expect(
    aw.getByRole("button", { name: "Close all positions", exact: true }),
  ).toBeVisible();
  await aw.getByRole("button", { name: "Simple", exact: true }).click();
  await expect(
    page.getByRole("dialog", { name: "Cannot switch to Simple Editor" }),
  ).toBeVisible();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Close", exact: true })
    .click();
  await aw
    .getByRole("button", { name: "7 / 0 configurable", exact: true })
    .click();
  await page.getByRole("button", { name: "Add variable", exact: true }).click();
  await page.getByLabel("Variable name").fill("Threshold");
  await page.getByLabel("Default value").fill("25");
  await page
    .getByRole("button", { name: "Save variable", exact: true })
    .click();
  await page
    .getByRole("dialog", { name: "Variables", exact: true })
    .getByRole("button", { name: "Save", exact: true })
    .click();
  await expect(
    aw.getByRole("button", { name: "8 / 0 configurable", exact: true }),
  ).toBeVisible();
  await aw.getByRole("button", { name: "Settings", exact: true }).click();
  await page
    .getByLabel("Symbol", { exact: true })
    .selectOption("EURUSD_dukascopy");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Cancel", exact: true })
    .click();
  await expect(aw.locator(".aw-preview-info")).toContainText(
    "AUDUSD_dukascopy",
  );
  await aw.getByRole("button", { name: "Settings", exact: true }).click();
  await page
    .getByLabel("Symbol", { exact: true })
    .selectOption("EURUSD_dukascopy");
  for (const name of [
    "Trading options",
    "ATM",
    "Money management",
    "Advanced",
    "Data",
  ])
    await page
      .getByRole("dialog")
      .getByRole("button", { name, exact: true })
      .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Save", exact: true })
    .click();
  await expect(aw.locator(".aw-preview-info")).toContainText(
    "EURUSD_dukascopy",
  );
});

test("resources create, edit, duplicate and confirmed delete", async ({
  page,
}) => {
  const aw = workspace(page);
  await aw.getByRole("button", { name: "Random groups", exact: true }).click();
  await aw.getByRole("button", { name: "Create new", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByLabel("Name", { exact: true })
    .fill("Trend signals");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Save", exact: true })
    .click();
  await aw
    .getByRole("button", { name: "Add condition(s)", exact: true })
    .click();
  await page.getByLabel("Selected expression").fill("RSI(14)[1] > 50");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Select", exact: true })
    .click();
  await expect(
    aw.getByRole("button", { name: "RSI(14)[1] > 50", exact: true }),
  ).toBeVisible();
  await aw.getByRole("button", { name: "Duplicate", exact: true }).click();
  await expect(
    aw.getByRole("button", { name: "Trend signals 2", exact: true }),
  ).toBeVisible();
  await aw.getByRole("button", { name: "Delete", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Delete", exact: true })
    .click();
  await expect(
    aw.getByRole("button", { name: "Trend signals 2", exact: true }),
  ).toHaveCount(0);
  await aw
    .getByRole("button", { name: "‹ Back to editor", exact: true })
    .click();
  await expect(
    aw.getByRole("heading", { name: "No strategies loaded" }),
  ).toBeVisible();
});

test("mock backtest cancel/result navigation, source and AI flows", async ({
  page,
}) => {
  const aw = workspace(page);
  await openEMA(page);
  await aw.getByRole("button", { name: "Run backtest", exact: true }).click();
  await aw.getByRole("button", { name: "Stop backtest", exact: true }).click();
  await expect(
    aw.getByText("Mock backtest canceled", { exact: true }),
  ).toBeVisible();
  await aw.getByRole("button", { name: "Run backtest", exact: true }).click();
  await expect(
    aw.getByRole("button", { name: "Open backtest results", exact: true }),
  ).toBeVisible();
  await aw
    .getByRole("button", { name: "Open backtest results", exact: true })
    .click();
  for (const name of [
    "Equity chart",
    "List of trades",
    "Trading analysis",
    "Settings",
    "Overview",
  ])
    await aw.getByRole("button", { name, exact: true }).click();
  await expect(
    aw.getByText(
      "Demonstration results — fixed fixtures, no strategy execution.",
      { exact: true },
    ),
  ).toBeVisible();
  await aw.getByRole("button", { name: "Source code", exact: true }).click();
  await expect(page.getByLabel("Source preview")).toContainText("EMACross");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Close", exact: true })
    .click();
  await aw.getByRole("button", { name: "AI Wizard", exact: true }).click();
  await page.getByLabel("Message AI Wizard").fill("An EMA crossover");
  await aw.getByRole("button", { name: "Send", exact: true }).click();
  await expect(aw.getByText("An EMA crossover", { exact: true })).toBeVisible();
  await aw
    .getByRole("button", { name: "Open example strategy", exact: true })
    .click();
  await expect(
    aw.getByRole("button", { name: "Close strategy EMACross 2", exact: true }),
  ).toBeVisible();
});

test("file export, valid reimport, invalid file and Retester staging", async ({
  page,
}) => {
  const aw = workspace(page);
  await openEMA(page);
  await aw.getByRole("button", { name: "Files", exact: true }).click();
  const pending = page.waitForEvent("download");
  await aw
    .getByRole("menuitem", { name: "Save to file...", exact: true })
    .click();
  const downloaded = await pending;
  const path = await downloaded.path();
  expect(downloaded.suggestedFilename()).toBe("EMACross.aw.json");
  await aw.locator("input[type=file]").setInputFiles(path!);
  await expect(
    aw.getByRole("button", { name: "Close strategy EMACross 2", exact: true }),
  ).toBeVisible();
  await aw
    .locator("input[type=file]")
    .setInputFiles({
      name: "invalid.json",
      mimeType: "application/json",
      buffer: Buffer.from("{}"),
    });
  await expect(aw.getByRole("alert")).toContainText(
    "Invalid prototype strategy",
  );
  await aw.getByRole("button", { name: "Files", exact: true }).click();
  await aw
    .getByRole("menuitem", { name: "Save to Retester", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Save", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toContainText("EMACross 2");
});

test("Simple editor and cloud picker expose distinct working panels", async ({
  page,
}) => {
  const aw = workspace(page);
  await aw.getByRole("button", { name: "New Strategy", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Select", exact: true })
    .click();
  await expect(
    aw.getByRole("heading", { name: "Buy", exact: true }),
  ).toBeVisible();
  await expect(
    aw.getByRole("heading", { name: "Sell short", exact: true }),
  ).toBeVisible();
  await aw
    .getByRole("button", { name: "Add exit condition(s)", exact: true })
    .first()
    .click();
  await page.getByLabel("Selected expression").fill("RSI(14)[1] > 80");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Select", exact: true })
    .click();
  await expect(
    aw.getByRole("button", { name: "RSI(14)[1] > 80", exact: true }),
  ).toBeVisible();
  await aw.screenshot({ path: resolve(evidence, "simple-editor.png") });
  await aw.getByRole("button", { name: "Full", exact: true }).click();
  await expect(
    aw.getByRole("tab", { name: "Trading signals", exact: true }),
  ).toBeVisible();
  await aw.getByRole("button", { name: "New", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("radio", { name: "Stockpicker strategy (cloud)", exact: true })
    .check();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Select", exact: true })
    .click();
  await aw.getByRole("button", { name: "Position score", exact: true }).click();
  await page.getByLabel("Maximum stocks").fill("7");
  await page.getByLabel("Score formula").fill("RSI(20)[1]");
  await aw.getByRole("button", { name: "Long", exact: true }).click();
  await expect(
    aw.getByRole("heading", { name: "Buy when", exact: true }),
  ).toBeVisible();
  await aw.getByRole("button", { name: "Position score", exact: true }).click();
  await expect(page.getByLabel("Maximum stocks")).toHaveValue("7");
});

test("block operations and fuzzy rules keep editable state and history", async ({
  page,
}) => {
  const aw = workspace(page);
  await openEMA(page);
  const original = "EMA(FastEMA)[1] crosses above EMA(SlowEMA)[1]";
  await aw
    .getByRole("button", { name: `Menu for ${original}`, exact: true })
    .click();
  await aw.getByRole("menuitem", { name: "Duplicate", exact: true }).click();
  await expect(
    aw.getByRole("button", { name: `Menu for ${original}`, exact: true }),
  ).toHaveCount(2);
  await aw
    .getByRole("button", { name: `Menu for ${original}`, exact: true })
    .last()
    .click();
  await aw.getByRole("menuitem", { name: "Negate", exact: true }).click();
  await expect(
    aw.getByRole("button", { name: `Menu for NOT (${original})`, exact: true }),
  ).toBeVisible();
  await aw.getByRole("button", { name: "Add rule", exact: true }).click();
  await page.getByLabel("Rule type").selectOption("Fuzzy Logic Signals");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Add", exact: true })
    .click();
  await aw.getByRole("button", { name: "Add signal", exact: true }).click();
  await aw
    .getByRole("button", { name: "Add condition(s)", exact: true })
    .click();
  await page.getByLabel("Search blocks").fill("RSI");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "RSI", exact: true })
    .click();
  await page.getByLabel("Period", { exact: true }).fill("20");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Select", exact: true })
    .click();
  await expect(
    aw.getByRole("button", { name: "RSI(20)[1]", exact: true }),
  ).toBeVisible();
  await aw
    .getByRole("button", { name: "Rule menu Rule 4", exact: true })
    .click();
  await aw.getByRole("menuitem", { name: "Delete rule", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Delete", exact: true })
    .click();
  await expect(
    aw.getByRole("tab", { name: "Rule 4", exact: true }),
  ).toHaveCount(0);
  await aw.getByRole("button", { name: "Undo", exact: true }).click();
  await expect(
    aw.getByRole("tab", { name: "Rule 4", exact: true }),
  ).toBeVisible();
});

test("chart uniqueness, debug values, variable rename, resource import and links", async ({
  page,
}) => {
  const aw = workspace(page);
  await openEMA(page);
  await aw
    .getByRole("button", { name: "Single chart strategy", exact: true })
    .click();
  await page.getByRole("button", { name: "Add chart", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Save", exact: true })
    .click();
  await expect(page.getByRole("dialog").getByRole("alert")).toHaveText(
    "All subcharts must have unique settings.",
  );
  await page.getByLabel("Timeframe for Subchart 1").selectOption("H4");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Save", exact: true })
    .click();
  await expect(
    aw.getByRole("button", { name: "2 charts", exact: true }),
  ).toBeVisible();
  await aw.getByRole("button", { name: "Off, no values", exact: true }).click();
  await page.getByLabel("Enable debug values").check();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Save", exact: true })
    .click();
  await expect(
    aw.getByRole("button", { name: "On, fixture values", exact: true }),
  ).toBeVisible();
  await aw
    .getByRole("button", { name: "7 / 0 configurable", exact: true })
    .click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "FastEMA", exact: true })
    .click();
  await page.getByLabel("Variable name").fill("FastAverage");
  await page
    .getByRole("button", { name: "Save variable", exact: true })
    .click();
  await page
    .getByRole("dialog", { name: "Variables", exact: true })
    .getByRole("button", { name: "Save", exact: true })
    .click();
  await expect(
    aw.getByRole("button", {
      name: "EMA(FastAverage)[1] crosses above EMA(SlowEMA)[1]",
      exact: true,
    }),
  ).toBeVisible();
  await aw.getByRole("button", { name: "Custom blocks", exact: true }).click();
  const resource = {
    format: "haruquantai.algowizard.resources",
    version: 1,
    items: [
      {
        id: "x",
        name: "Imported block",
        category: "Signals",
        kind: "Custom blocks",
        content: ["RSI(10)[1] > 50"],
      },
    ],
  };
  await aw
    .locator(".aw-resource-page input[type=file]")
    .setInputFiles({
      name: "resources.json",
      mimeType: "application/json",
      buffer: Buffer.from(JSON.stringify(resource)),
    });
  await aw.getByRole("button", { name: "Imported block", exact: true }).click();
  await expect(
    aw.getByRole("button", { name: "RSI(10)[1] > 50", exact: true }),
  ).toBeVisible();
  await expect(
    aw.getByRole("link", { name: "Help", exact: true }),
  ).toHaveAttribute("href", "https://help.algowizard.io/index.html");
  await expect(
    aw.getByRole("link", { name: "Help", exact: true }),
  ).toHaveAttribute("target", "_blank");
});
