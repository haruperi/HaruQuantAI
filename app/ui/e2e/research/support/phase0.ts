import type { Page, TestInfo } from "@playwright/test";

/** Evidence emitted by the Phase 0 real-provider browser readiness slice. */
export interface Phase0BrowserEvidence {
  readonly providerMode: "REAL_LOCAL_ASGI";
  readonly authenticatedUser: string;
  readonly navigationDurationMs: number;
  readonly accessibleControlCount: number;
  readonly consoleErrors: readonly string[];
  readonly expectedUnavailableResponses: ReadonlyArray<{
    readonly status: number;
    readonly path: string;
  }>;
  readonly recovery: "PASS";
}

/** Return visible interactive controls that have a usable accessible name. */
export async function countAccessibleControls(page: Page): Promise<number> {
  return page.locator("button:visible, input:visible, [role=tab]:visible").evaluateAll(
    (elements) =>
      elements.filter((element) => {
        const labelledBy = element.getAttribute("aria-labelledby");
        const label =
          element.getAttribute("aria-label") ??
          element.getAttribute("title") ??
          element.textContent?.trim() ??
          (element instanceof HTMLInputElement
            ? element.labels?.[0]?.textContent?.trim()
            : "");
        return Boolean(labelledBy || label);
      }).length,
  );
}

/** Attach bounded, secret-safe JSON evidence to the Playwright report. */
export async function attachPhase0Evidence(
  testInfo: TestInfo,
  evidence: Phase0BrowserEvidence,
): Promise<void> {
  await testInfo.attach("phase0-readiness", {
    body: Buffer.from(JSON.stringify(evidence, null, 2)),
    contentType: "application/json",
  });
}
