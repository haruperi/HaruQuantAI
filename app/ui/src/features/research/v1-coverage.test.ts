/**
 * V1 coverage manifest (FEAT-UI-28, plan §14.4).
 *
 * Every V1 Edge Lab capability resolves here to a V2 route, a V2 component, an
 * owning domain, a test reference, and an explicit status. This exists so a
 * future frontend rewrite cannot silently drop a V1 capability.
 *
 * Status vocabulary:
 * - `implemented`   — realized inside the V2 Research workbench.
 * - `cross-domain`  — covered in V2 under a different owning domain.
 * - `superseded`    — intentionally replaced by a different V2 mechanism.
 */

import { existsSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import { ROUTE_CONTRACTS_BY_ID } from "@/clients/routes";

import { STAGE_BY_ID } from "./stage-registry";

/** One V1 capability and its V2 disposition. */
interface CoverageEntry {
  readonly v1: string;
  readonly route: string;
  readonly component: string;
  readonly owner: string;
  readonly test: string;
  readonly status: "implemented" | "cross-domain" | "superseded";
  readonly note?: string;
}

/** The V1 Edge Lab route tree, exactly as the plan enumerates it. */
const V1_CAPABILITIES = [
  "data",
  "core_metric",
  "seasonality",
  "edge_profile",
  "scorecard",
  "automation",
  "sqx_import",
  "monte_carlo",
  "discovery",
  "market_structure",
  "unsupervised_structure",
] as const;

const MANIFEST: readonly CoverageEntry[] = [
  {
    v1: "data",
    route: "/workstation/research/experiments/[experimentId]/runs/[runId]/data",
    component: "src/features/research/panels/DataQualityPanel.tsx",
    owner: "Data + Research",
    test: "src/features/research/ResearchWorkbench.test.tsx",
    status: "implemented",
  },
  {
    v1: "core_metric",
    route: "/workstation/research/experiments/[experimentId]/runs/[runId]/metrics",
    component: "src/features/research/panels/MetricsPanel.tsx",
    owner: "Research",
    test: "src/features/research/ResearchWorkbench.test.tsx",
    status: "implemented",
  },
  {
    v1: "seasonality",
    route:
      "/workstation/research/experiments/[experimentId]/runs/[runId]/seasonality",
    component: "src/features/research/panels/SeasonalityPanel.tsx",
    owner: "Research",
    test: "src/features/research/ResearchWorkbench.test.tsx",
    status: "implemented",
  },
  {
    v1: "edge_profile",
    route: "/workstation/research/experiments/[experimentId]/runs/[runId]/studies",
    component: "src/features/research/panels/StudiesPanel.tsx",
    owner: "Research",
    test: "src/features/research/ResearchWorkbench.test.tsx",
    status: "implemented",
    note: "Split into Studies and Market Structure rather than one mega-page.",
  },
  {
    v1: "scorecard",
    route: "/workstation/research/experiments/[experimentId]/runs/[runId]/profile",
    component: "src/features/research/panels/ProfilePanel.tsx",
    owner: "Research",
    test: "src/features/research/ResearchWorkbench.test.tsx",
    status: "implemented",
  },
  {
    v1: "automation",
    route: "/workstation/research/automation",
    component: "src/features/research/ResearchAutomation.tsx",
    owner: "Research gateway",
    test: "tests/api/unit/test_research_workbench_routes.py",
    status: "implemented",
  },
  {
    v1: "sqx_import",
    route: "/workstation/strategies/import/sqx",
    component: "src/features/research/panels/OverviewPanel.tsx",
    owner: "Strategy / Data import",
    test: "src/features/research/ResearchWorkbench.test.tsx",
    status: "cross-domain",
    note: "Research links to the owning workflow and never owns strategy import.",
  },
  {
    v1: "monte_carlo",
    route: "/workstation/optimization/monte-carlo",
    component: "src/features/research/panels/OverviewPanel.tsx",
    owner: "Simulator / Optimization",
    test: "src/features/research/ResearchWorkbench.test.tsx",
    status: "cross-domain",
    note: "Research links to the owned widget rather than duplicating execution.",
  },
  {
    v1: "discovery",
    route: "/workstation/research",
    component: "src/features/research/ResearchDashboard.tsx",
    owner: "Research gateway",
    test: "src/features/research/research-client.test.ts",
    status: "implemented",
    note: "The V1 placeholder becomes a real experiment and run ledger.",
  },
  {
    v1: "market_structure",
    route:
      "/workstation/research/experiments/[experimentId]/runs/[runId]/market-structure",
    component: "src/features/research/panels/MarketStructurePanel.tsx",
    owner: "Research",
    test: "src/features/research/ResearchWorkbench.test.tsx",
    status: "implemented",
  },
  {
    v1: "unsupervised_structure",
    route: "/workstation/research/experiments/[experimentId]/runs/[runId]/modeling",
    component: "src/features/research/panels/ModelingPanel.tsx",
    owner: "Research",
    test: "src/features/research/ResearchWorkbench.test.tsx",
    status: "implemented",
  },
];

/** The sixteen registered V2 Research features and their UI destination. */
const V2_FEATURE_DESTINATIONS: Readonly<Record<string, string>> = {
  "contracts and configuration": "run builder + provenance",
  "deterministic dataset preparation": "data",
  "research-specific features": "features",
  "leakage evidence and splits": "validation",
  "core metric profile": "metrics",
  "seeded statistical validation": "validation",
  "edge discovery and confirmation": "studies",
  "sessions and seasonality": "seasonality",
  "market-structure analysis": "market-structure",
  "deterministic unsupervised insights": "modeling",
  "scorecards and snapshots": "profile",
  "safe artifact persistence": "artifacts",
  "fundamental and sentiment evidence": "intelligence",
  "approved expectancy profile": "expectancy",
  "performance drift evidence": "drift",
  "stress-scenario evidence": "stress",
};

const UI_ROOT = resolve(__dirname, "..", "..", "..");

describe("V1 coverage manifest — plan §14.4", () => {
  it("gives every V1 Edge Lab capability an explicit V2 disposition", () => {
    const covered = new Set(MANIFEST.map((entry) => entry.v1));
    for (const capability of V1_CAPABILITIES) {
      expect(covered.has(capability), `${capability} has no V2 disposition`).toBe(
        true
      );
    }
    expect(MANIFEST).toHaveLength(V1_CAPABILITIES.length);
  });

  it("names a component file that exists for every entry", () => {
    for (const entry of MANIFEST) {
      if (!entry.component.startsWith("src/")) continue;
      expect(
        existsSync(resolve(UI_ROOT, entry.component)),
        `${entry.v1}: missing component ${entry.component}`
      ).toBe(true);
    }
  });

  it("names an owning domain and a test reference for every entry", () => {
    for (const entry of MANIFEST) {
      expect(entry.owner.length, `${entry.v1} has no owner`).toBeGreaterThan(0);
      expect(entry.test.length, `${entry.v1} has no test`).toBeGreaterThan(0);
    }
  });

  it("resolves every research stage route to a registered stage", () => {
    for (const entry of MANIFEST) {
      const match = entry.route.match(/runs\/\[runId\]\/([a-z-]+)$/);
      if (!match) continue;
      expect(
        STAGE_BY_ID[match[1]],
        `${entry.v1}: ${match[1]} is not a registered stage`
      ).toBeDefined();
    }
  });

  it("keeps SQX import and Monte Carlo outside Research ownership", () => {
    const crossDomain = MANIFEST.filter((entry) => entry.status === "cross-domain");
    expect(crossDomain.map((entry) => entry.v1).sort()).toEqual([
      "monte_carlo",
      "sqx_import",
    ]);
    for (const entry of crossDomain) {
      expect(entry.owner).not.toBe("Research");
      expect(entry.route.startsWith("/workstation/research")).toBe(false);
    }
  });

  it("gives every registered V2 Research feature a frontend destination", () => {
    for (const [feature, destination] of Object.entries(V2_FEATURE_DESTINATIONS)) {
      const known =
        STAGE_BY_ID[destination] !== undefined ||
        ["expectancy", "drift", "run builder + provenance"].includes(destination);
      expect(known, `${feature} has no frontend destination`).toBe(true);
    }
    expect(Object.keys(V2_FEATURE_DESTINATIONS)).toHaveLength(16);
  });

  it("backs the workbench with registered backend routes", () => {
    for (const id of [
      "api.research.presets",
      "api.research.dashboard",
      "api.research.create_experiment",
      "api.research.create_run",
      "api.research.run_detail",
      "api.research.run_stage",
      "api.research.run_events",
      "api.research.cancel_run",
      "api.research.compare_runs",
      "api.research.run_artifacts",
      "api.research.create_automation",
      "api.research.expectancy",
      "api.research.drift",
    ]) {
      expect(ROUTE_CONTRACTS_BY_ID[id], `${id} is not registered`).toBeDefined();
    }
  });
});
