import { expect, test } from "@playwright/test";

import {
  attachPhase0Evidence,
  countAccessibleControls,
} from "./support/phase0";

test("real provider authentication, blank workspace, and recovery", async ({
  page,
}, testInfo) => {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const httpFailures: Array<{ status: number; path: string }> = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() < 400) return;
    httpFailures.push({
      status: response.status(),
      path: new URL(response.url()).pathname,
    });
  });

  await page.goto("/login");
  await expect(page.getByRole("main", { name: "Authentication" })).toBeVisible();
  await page.getByRole("tab", { name: "Register" }).click();
  await page.getByLabel("Username").fill("phase0_harness_user");
  await page.getByLabel("Password").fill("Phase0Harness123!");
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page).toHaveURL(/\/$/);

  const identityResponse = await page.request.get("/api/v1/auth/me");
  expect(identityResponse.status()).toBe(200);
  const identity = (await identityResponse.json()) as {
    data: { username: string };
  };
  expect(identity.data.username).toBe("phase0_harness_user");

  await expect(
    page.getByRole("button", {
      name: "Create workspace from the Blank template",
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Create workspace from the Blank template" })
    .click();
  await expect(page.getByRole("heading", { name: "Your workspace is empty" })).toBeVisible();

  await page.reload();
  await expect(page.getByRole("heading", { name: "Your workspace is empty" })).toBeVisible();
  expect((await page.request.get("/api/v1/auth/me")).status()).toBe(200);

  await page.keyboard.press("Tab");
  const activeTag = await page.evaluate(() => document.activeElement?.tagName);
  expect(["BUTTON", "A", "INPUT"]).toContain(activeTag);
  const accessibleControlCount = await countAccessibleControls(page);
  expect(accessibleControlCount).toBeGreaterThan(0);

  const navigationDurationMs = await page.evaluate(() => {
    const [entry] = performance.getEntriesByType("navigation");
    return entry?.duration ?? 0;
  });
  expect(navigationDurationMs).toBeLessThan(15_000);
  expect(httpFailures.filter(({ status, path }) => status === 401 && path === "/api/v1/auth/me")).toHaveLength(1);
  const expectedUnavailableResponses = httpFailures.filter(
    ({ status }) => status === 503,
  );
  expect(new Set(expectedUnavailableResponses.map(({ path }) => path))).toEqual(
    new Set([
      "/api/v1/settings",
      "/api/v1/trading/account-profile",
      "/api/v1/trading/execution-sessions",
    ]),
  );
  expect(httpFailures).toHaveLength(expectedUnavailableResponses.length + 1);
  expect(pageErrors).toEqual([]);
  expect(
    consoleErrors.filter(
      (message) =>
        message !==
        "Failed to load resource: the server responded with a status of 401 (Unauthorized)" &&
        message !==
        "Failed to load resource: the server responded with a status of 503 (Service Unavailable)",
    ),
  ).toEqual([]);

  await attachPhase0Evidence(testInfo, {
    providerMode: "REAL_LOCAL_ASGI",
    authenticatedUser: identity.data.username,
    navigationDurationMs,
    accessibleControlCount,
    consoleErrors,
    expectedUnavailableResponses,
    recovery: "PASS",
  });
});
