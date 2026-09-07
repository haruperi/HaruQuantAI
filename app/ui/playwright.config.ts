/**
 * Playwright configuration for the Simulation and Analytics workbench journeys.
 *
 * Chromium, viewport, locale and clock inputs are deterministic. Individual
 * specs declare whether they use contract stubs or the real local ASGI harness;
 * Phase 0 readiness always uses the latter and never reaches an external target.
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
  webServer: [
    {
      command:
        "uv run --frozen python tests/harness/phase0_asgi.py --port 8765",
      cwd: "../..",
      url: "http://127.0.0.1:8765/api/v1/auth/me",
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: "npm run build && npm run start -- --port 3100",
      env: {
        ...process.env,
        BACKEND_URL: "http://127.0.0.1:8765",
      },
      url: "http://127.0.0.1:3100",
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
    },
  ],
});
