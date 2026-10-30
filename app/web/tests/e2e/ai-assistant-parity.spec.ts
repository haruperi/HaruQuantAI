import { resolve } from "node:path";
import { expect, test } from "@playwright/test";
import { selectLightSkin } from "./shellTestUtils";

const evidence = resolve("..", ".agents/logs/20261006_204945_ai-assistant-ui");

// Host preferences are a test fixture, not an assistant service implementation.
test.beforeEach(async ({ page }) => {
  let revision = 0;
  const values: Record<string, Record<string, unknown>> = {};
  await page.addInitScript(() => {
    const original = window.fetch.bind(window);
    window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).includes("/api/v1/events?")) {
        return Promise.resolve(
          new Response(new ReadableStream<Uint8Array>({ start() {} }), {
            status: 200,
            headers: { "Content-Type": "text/event-stream" },
          }),
        );
      }
      return original(input, init);
    }) as typeof fetch;
  });
  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    let data: unknown = {};
    if (path.endsWith("/auth/login"))
      data = { token: "assistant-ui-test-session" };
    if (path.endsWith("/status")) data = { cpu_count: 8 };
    if (path.endsWith("/settings")) {
      if (route.request().method() === "PUT") {
        const body = route.request().postDataJSON() as {
          changes: Record<string, Record<string, unknown>>;
        };
        for (const [key, fields] of Object.entries(body.changes))
          values[key] = { ...values[key], ...fields };
        revision += 1;
      }
      data = { revision, values };
    }
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ status: "success", data }),
    });
  });
  await page.goto("/aiassistant");
  await expect(page.getByText("Host online", { exact: true })).toBeVisible();
});

test("home presents all eight donor capabilities and gates assistant services", async ({
  page,
}) => {
  const workspace = page.getByRole("region", {
    name: "AI Assistant workspace",
  });
  await expect(workspace.locator(".ai-capability-card h2")).toHaveText([
    "Text to Strategy",
    "Analyze & Research",
    "Build & Automate Workflows",
    "Market & Data Analysis",
    "Custom Analysis Tabs & Code",
    "Plugins & Skills",
    "AlgoCloud",
    "Learn HaruQuantAI & Trading",
  ]);
  await expect(
    workspace.getByRole("button", { name: "Send", exact: true }),
  ).toBeDisabled();
  await expect(workspace.getByLabel("Model", { exact: true })).toBeDisabled();
  await expect(
    workspace.getByText(/Assistant service unavailable\. Drafts/),
  ).toBeVisible();
  await expect(page.locator(".databank-splitter")).toHaveCount(0);
  await page.screenshot({
    path: resolve(evidence, "assistant-desktop-dark.png"),
  });
  await workspace.getByRole("button", { name: "View Usage & Credits" }).click();
  const usage = page.getByRole("dialog", { name: "Usage & Credits" });
  await expect(
    usage.getByRole("button", { name: "Add credits" }),
  ).toBeDisabled();
  await page.keyboard.press("Escape");
  await expect(usage).toHaveCount(0);
});

test("starters prepare drafts, sessions preserve separate drafts, and host actions never execute", async ({
  page,
}) => {
  const requests: string[] = [];
  page.on("request", (request) => requests.push(request.url()));
  await page.getByRole("button", { name: /^Text to Strategy/ }).click();
  await page
    .getByRole("button", { name: /Create an EMA\(12\/26\) cross/ })
    .click();
  const message = page.getByRole("textbox", { name: "Message", exact: true });
  await expect(message).toHaveValue(/Create an EMA/);
  await message.press("Enter");
  await expect(page.getByRole("status")).toContainText(
    "Your draft has been kept",
  );
  await page
    .getByRole("button", { name: /Load strategy from AlgoWizard editor/ })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "requires the assistant service",
  );
  await page.getByRole("button", { name: "New session", exact: true }).click();
  await message.fill("Separate second draft");
  await page.getByRole("tab", { name: "Text to Strategy" }).click();
  await expect(message).toHaveValue(/Create an EMA/);
  await page.getByRole("tab", { name: "Text to Strategy" }).press("ArrowRight");
  await expect(page.getByRole("tab", { name: "New chat 2" })).toBeFocused();
  await expect(message).toHaveValue("Separate second draft");
  await page.getByRole("tab", { name: "New chat 2" }).press("ArrowLeft");
  await page.screenshot({
    path: resolve(evidence, "assistant-capability.png"),
  });
  expect(requests.filter((url) => /\/sqai\//i.test(url))).toEqual([]);
  await page.reload();
  await expect(message).toHaveValue("");
  await expect(page.getByRole("tab", { name: "Text to Strategy" })).toHaveCount(
    0,
  );
});

test("projects, pins, rename and confirmed clearing manage local drafts", async ({
  page,
}) => {
  const message = page.getByRole("textbox", { name: "Message", exact: true });
  await message.fill("Keep this draft");
  await page.getByRole("button", { name: "New project", exact: true }).click();
  await page
    .getByRole("textbox", { name: "Name", exact: true })
    .fill("Research");
  await page.getByRole("button", { name: "Save locally", exact: true }).click();
  await page.getByRole("button", { name: "Session actions" }).click();
  await page.getByLabel("Move chat to project").selectOption("Research");
  await page.getByRole("button", { name: "Session actions" }).click();
  await page
    .getByRole("button", { name: "Rename session", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "Name", exact: true })
    .fill("EURUSD ideas");
  await page.getByRole("button", { name: "Save locally", exact: true }).click();
  await expect(page.getByRole("tab", { name: "EURUSD ideas" })).toBeVisible();
  await page.getByRole("button", { name: "Session actions" }).click();
  await page.getByRole("button", { name: "Pin", exact: true }).click();
  await expect(page.locator(".ai-session-row.selected svg")).toHaveClass(
    /lucide-pin/,
  );
  await page.getByRole("button", { name: "Session actions" }).click();
  await page.getByRole("button", { name: "Clear chat", exact: true }).click();
  await page.getByRole("button", { name: "Keep it" }).click();
  await expect(message).toHaveValue("Keep this draft");
  await message.fill("/clear");
  await message.press("Enter");
  await page.getByRole("button", { name: "Clear draft" }).click();
  await expect(message).toHaveValue("");
  await page.getByRole("button", { name: "Session actions" }).click();
  await page
    .getByRole("button", { name: "Close session", exact: true })
    .click();
  await page.getByRole("button", { name: "Close draft" }).click();
  await expect(page.getByRole("tab")).toHaveCount(1);
  await expect(page.getByRole("tab")).toContainText("New chat");
});

test("attachments stay local and can be removed without uploads", async ({
  page,
}) => {
  const mutationRequests: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (
      url.origin === new URL(page.url()).origin &&
      !["GET", "HEAD"].includes(request.method())
    )
      mutationRequests.push(request.url());
  });
  await page.getByLabel("Choose attachments").setInputFiles({
    name: "sample.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("time,close\n2026-01-01,1.1\n"),
  });
  await expect(page.locator(".ai-attachments")).toContainText("sample.csv");
  await page.getByRole("button", { name: "Files (1)", exact: true }).click();
  await expect(page.locator(".ai-file-row")).toContainText("sample.csv");
  await page
    .getByRole("button", { name: "Remove sample.csv", exact: true })
    .click();
  await expect(
    page.getByText("No files selected.", { exact: true }),
  ).toBeVisible();
  expect(mutationRequests).toEqual([]);
  await page.getByRole("button", { name: "Reports", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "No reports available" }),
  ).toBeVisible();
});

test("Brain exposes unavailable file services and modal keyboard focus", async ({
  page,
}) => {
  const brain = page.getByRole("button", { name: "Brain", exact: true });
  await brain.click();
  const dialog = page.getByRole("dialog", { name: "AI Brain", exact: true });
  await expect(dialog.getByText("MEMORY.md", { exact: true })).toBeVisible();
  await expect(dialog.getByLabel("Brain file editor")).toBeDisabled();
  await dialog.getByRole("button", { name: "Skills", exact: true }).click();
  await expect(dialog.getByRole("button", { name: "Promote" })).toBeDisabled();
  await expect(dialog.getByRole("button", { name: "Discard" })).toBeDisabled();
  await expect(
    dialog.getByRole("button", { name: "Save", exact: true }),
  ).toBeDisabled();
  await page.screenshot({ path: resolve(evidence, "assistant-brain.png") });
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(brain).toBeFocused();
});

test("light skin and narrow view keep the composer and conversations usable", async ({
  page,
}) => {
  await expect(page.getByText("Host online", { exact: true })).toBeVisible();
  await selectLightSkin(page);
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.screenshot({
    path: resolve(evidence, "assistant-desktop-light.png"),
  });
  await page.setViewportSize({ width: 520, height: 700 });
  await expect(
    page.getByRole("textbox", { name: "Message", exact: true }),
  ).toBeVisible();
  const cards = page.locator(".ai-capability-card");
  const first = await cards.nth(0).boundingBox();
  const second = await cards.nth(1).boundingBox();
  expect(first).not.toBeNull();
  expect(second).not.toBeNull();
  expect(second!.x).toBe(first!.x);
  expect(second!.y).toBeGreaterThan(first!.y + first!.height);
  await page
    .getByRole("button", { name: "Conversations", exact: true })
    .click();
  const conversations = page.getByRole("complementary", {
    name: "Assistant conversations",
  });
  await expect(conversations).toBeVisible();
  await conversations
    .getByRole("button", { name: "New chat", exact: true })
    .click();
  await expect(conversations).toBeHidden();
  await expect(page.getByRole("tab", { name: "New chat 2" })).toBeVisible();
  await page
    .getByRole("textbox", { name: "Message", exact: true })
    .fill("Draft on a narrow screen");
  const overflow = await page
    .locator(".ai-workspace")
    .evaluate((element) => element.scrollWidth > element.clientWidth);
  expect(overflow).toBe(false);
  await page.screenshot({
    path: resolve(evidence, "assistant-narrow-light.png"),
  });
});
