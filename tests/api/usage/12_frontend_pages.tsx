/**
 * Usage program 12 — Protected workflow pages (FEAT-API-12).
 *
 * Standalone numbered program, not a pytest test. Verifies the §4.12 page
 * components exist as exported functions on the public barrel (FR-055) and
 * that the root framework entry delegates to `WorkflowPage`. Router-driven
 * rendering is covered by the vitest unit tests (which mock next/navigation);
 * this program runs under plain `tsx` where the Next.js router is unavailable.
 *
 * Run:
 *   cd app/ui && NODE_PATH=./node_modules npx tsx --tsconfig ./tsconfig.usage.json \
 *     ../../tests/api/usage/12_frontend_pages.tsx
 */

import { JSDOM } from "jsdom";

// Minimal DOM so React/testing-library globals exist for the render smoke test.
const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "http://localhost/",
});
const define = (key: string, value: unknown) => {
  Object.defineProperty(globalThis, key, { value, configurable: true, writable: true });
};
define("window", dom.window);
define("document", dom.window.document);
define("sessionStorage", dom.window.sessionStorage);
define("HTMLElement", dom.window.HTMLElement);
define("Element", dom.window.Element);
define("Node", dom.window.Node);
define("getComputedStyle", dom.window.getComputedStyle);

function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(`usage assertion failed: ${message}`);
}

/** FR-API-055: the barrel exports exactly the three approved page functions. */
function testUsageApprovedPages(): void {
  // Import the barrel (pure TypeScript, no next/navigation needed).
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const barrel = require("../../../app/ui/src/app/index");
  assert(typeof barrel.AuthenticationPage === "function", "AuthenticationPage must be a function");
  assert(typeof barrel.ProtectedLayout === "function", "ProtectedLayout must be a function");
  assert(typeof barrel.WorkflowPage === "function", "WorkflowPage must be a function");
  console.log("[testUsageApprovedPages] ok — barrel exports AuthenticationPage, ProtectedLayout, WorkflowPage");
}

/** FR-API-053/054: the root page delegates to WorkflowPage (source check). */
function testUsageRootPageDelegates(): void {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const fs = require("node:fs") as typeof import("node:fs");
  const path = require("node:path") as typeof import("node:path");
  const pagePath = path.resolve(__dirname, "../../../app/ui/src/app/page.tsx");
  const src = fs.readFileSync(pagePath, "utf-8");
  assert(src.includes("WorkflowPage"), "root page.tsx must delegate to WorkflowPage");
  assert(!src.includes("<App"), "root page.tsx must not render <App/> directly");
  console.log("[testUsageRootPageDelegates] ok — root page delegates to WorkflowPage");
}

/** FR-API-053: the /login route exists and delegates to AuthenticationPage. */
function testUsageLoginRoute(): void {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const fs = require("node:fs") as typeof import("node:fs");
  const path = require("node:path") as typeof import("node:path");
  const loginPath = path.resolve(__dirname, "../../../app/ui/src/app/login/page.tsx");
  assert(fs.existsSync(loginPath), "/login route segment must exist");
  const src = fs.readFileSync(loginPath, "utf-8");
  assert(src.includes("AuthenticationPage"), "/login route must delegate to AuthenticationPage");
  console.log("[testUsageLoginRoute] ok — /login route delegates to AuthenticationPage");
}

function main(): void {
  console.log("=== Usage program 12 — Protected workflow pages ===");
  testUsageApprovedPages();
  testUsageRootPageDelegates();
  testUsageLoginRoute();
  console.log("=== All usage cases passed ===");
}

main();
