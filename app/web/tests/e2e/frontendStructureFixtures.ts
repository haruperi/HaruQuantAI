import { basename } from "node:path";
import { test as base, type Locator } from "@playwright/test";
export { expect } from "@playwright/test";
export type { Page } from "@playwright/test";

/** Isolated host preferences and bounded screenshots for structural regressions. */
export const test = base.extend({
  page: async ({ page }, use, info) => {
    let revision = 0;
    const values: Record<string, Record<string, unknown>> = {};
    await page.addInitScript(() => {
      const original = window.fetch.bind(window);
      window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => {
        if (String(input).includes("/api/v1/events?"))
          return Promise.resolve(
            new Response(new ReadableStream<Uint8Array>({ start() {} }), {
              status: 200,
              headers: { "Content-Type": "text/event-stream" },
            }),
          );
        return original(input, init);
      }) as typeof fetch;
    });
    await page.route("**/api/v1/**", async (route) => {
      const path = new URL(route.request().url()).pathname;
      let data: unknown = {};
      let status = 200;
      if (path.endsWith("/auth/login"))
        data = { token: "isolated-frontend-session" };
      else if (path.endsWith("/status")) data = { cpu_count: 8 };
      else if (path.endsWith("/settings")) {
        if (route.request().method() === "PUT") {
          const body = route.request().postDataJSON() as {
            expected_revision: number;
            changes: Record<string, unknown>;
          };
          if (body.expected_revision !== revision) status = 409;
          else {
            for (const [key, fields] of Object.entries(body.changes))
              values[key] = {
                ...values[key],
                ...(fields as Record<string, unknown>),
              };
            revision++;
          }
        }
        data = { revision, values };
      } else if (!path.endsWith("/app-loaded")) status = 503;
      await route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(
          status === 200
            ? { status: "success", data }
            : {
                status: "error",
                error: {
                  code: "ISOLATED_HOST",
                  message: "Unavailable in the frontend fixture",
                },
              },
        ),
      });
    });
    const screenshot = page.screenshot.bind(page);
    page.screenshot = (options) =>
      screenshot({
        ...options,
        ...(options?.path
          ? { path: info.outputPath(basename(options.path)) }
          : {}),
      });
    const locatorPrototype = Object.getPrototypeOf(page.locator('body')) as {
      screenshot: Locator['screenshot'];
    };
    const locatorScreenshot = locatorPrototype.screenshot;
    locatorPrototype.screenshot = function (this: Locator, options) {
      return locatorScreenshot.call(this, {
        ...options,
        ...(options?.path ? { path: info.outputPath(basename(options.path)) } : {}),
      });
    };
    try {
      await use(page);
    } finally {
      locatorPrototype.screenshot = locatorScreenshot;
    }
  },
});
