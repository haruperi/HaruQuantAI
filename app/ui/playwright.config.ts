/**
 * Playwright configuration for the Simulation and Analytics workbench journeys.
 *
 * The suite is deliberately narrow and deterministic: Chromium only, one fixed
 * viewport, a frozen clock, and fully stubbed API responses. A browser test
 * that reached a live provider would fail for reasons unrelated to the journey
 * it claims to prove, and a screenshot taken at a moving clock would never
 * compare twice.
 */

import { defineConfig, devices } from "@playwright/test";

/** Frozen wall clock shared by every journey and every screenshot. */
export const FIXED_CLOCK = new Date("2026-03-04T09:00:00.000Z");

/** Fixed viewport so visual comparisons stay stable across machines. */
export const FIXED_VIEWPORT = { width: 1280, height: 800 };

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [["list"]],
  snapshotPathTemplate:
    "{testDir}/__screenshots__/{testFilePath}/{arg}{-projectName}{ext}",
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.01,
      animations: "disabled",
    },
  },
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "on-first-retry",
    viewport: FIXED_VIEWPORT,
    timezoneId: "UTC",
    locale: "en-GB",
    colorScheme: "dark",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], viewport: FIXED_VIEWPORT },
    },
  ],
  webServer: {
    command: "npm run start -- --port 3100",
    url: "http://127.0.0.1:3100",
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
});
