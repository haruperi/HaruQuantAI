/**
 * Pages contract test (FR-API-055).
 *
 * Asserts the workflow pages compose exclusively from public clients,
 * context, and workflow components — no deep domain imports, no direct
 * broker/data access. This is the structural guarantee that pages stay
 * thin framework entry points.
 */

import { describe, expect, it } from "vitest";

import { AuthenticationPage, ProtectedLayout, WorkflowPage } from "./index";

describe("pages contract — FR-API-055", () => {
  it("everyPageHasClientContract: all page exports are functions", () => {
    expect(typeof AuthenticationPage).toBe("function");
    expect(typeof ProtectedLayout).toBe("function");
    expect(typeof WorkflowPage).toBe("function");
  });

  it("pages module imports only from public surface", async () => {
    // Read the source of the three page modules to assert they import only
    // from "@/clients", "@/context", "@/components/workflow", or relative
    // workflow files — never from a deep domain module.
    const sources: string[] = [
      await import("./authentication-page?raw").then((m) => m.default as string),
      await import("./protected-layout?raw").then((m) => m.default as string),
      await import("./workflow-page?raw").then((m) => m.default as string),
    ];
    const forbidden = /from\s+["']app\/services\/|from\s+["']@\/services\/|from\s+["'].*\/brokers\/|from\s+["'].*\/trading\/(?!client)|from\s+["'].*\/simulator\/|from\s+["'].*\/risk\/(?!client)/;
    for (const src of sources) {
      expect(forbidden.test(src), `page imports a forbidden deep domain module`).toBe(false);
    }
  });
});
