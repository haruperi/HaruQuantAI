import { describe, expect, it } from "vitest";
import {
  validateSourceMapping,
  type SourceMapping,
  type MappingScope,
} from "../databank/sourceMappingValidation";
import registry from "../../../../app/plugins/project/README.md?raw";
const root = "../../../../app/plugins/project/";
const rawFiles = import.meta.glob("../../../../app/plugins/project/**/*", {
  eager: true,
  query: "?raw",
  import: "default",
}) as Record<string, string>;
const scopes: MappingScope[] = [
  {
    domain: "project",
    js: 2,
    plugin: "EnginePanel",
    allowFrontendExclusions: true,
    css: 1,
    html: 3,
    excluded: 14,
  },
  {
    domain: "project",
    js: 1,
    plugin: "ProjectSettings",
    allowFrontendExclusions: true,
    css: 0,
    html: 1,
    excluded: 3,
  },
  {
    domain: "project",
    js: 2,
    plugin: "SettingsPanel",
    allowFrontendExclusions: true,
    css: 0,
    html: 1,
    excluded: 1,
  },
  {
    domain: "project",
    js: 2,
    plugin: "ProjectResults",
    allowFrontendExclusions: true,
    css: 1,
    html: 2,
    excluded: 0,
  },
  {
    domain: "project",
    js: 4,
    plugin: "ResultsEquityChart",
    allowFrontendExclusions: true,
    css: 1,
    html: 2,
    excluded: 2,
  },
  {
    domain: "project",
    js: 2,
    plugin: "ResultsOverview",
    allowFrontendExclusions: true,
    css: 1,
    html: 1,
    excluded: 8,
  },
  {
    domain: "project",
    js: 2,
    plugin: "ResultsTradeList",
    allowFrontendExclusions: true,
    css: 1,
    html: 1,
    excluded: 1,
  },
  {
    domain: "project",
    js: 2,
    plugin: "ResultsTradelistViews",
    allowFrontendExclusions: true,
    css: 0,
    html: 1,
    excluded: 3,
  },
  {
    domain: "project",
    js: 2,
    plugin: "ResultsProfileChart",
    allowFrontendExclusions: true,
    css: 0,
    html: 1,
    excluded: 2,
  },
  {
    domain: "project",
    js: 2,
    plugin: "ResultsSourceCode",
    allowFrontendExclusions: true,
    css: 1,
    html: 1,
    excluded: 4,
  },
  {
    domain: "project",
    js: 2,
    plugin: "ResultsSPOverview",
    allowFrontendExclusions: true,
    css: 1,
    html: 2,
    excluded: 13,
  },
  {
    domain: "project",
    js: 1,
    plugin: "ResultsStrategyConfig",
    allowFrontendExclusions: true,
    css: 1,
    html: 1,
    excluded: 3,
  },
  {
    domain: "project",
    js: 2,
    plugin: "ResultsTradeAnalysis",
    allowFrontendExclusions: true,
    css: 1,
    html: 2,
    excluded: 4,
  },
  {
    domain: "project",
    js: 1,
    plugin: "ResultsChart",
    allowFrontendExclusions: true,
    css: 0,
    html: 1,
    excluded: 4,
  },
  {
    domain: "project",
    js: 2,
    plugin: "ResultsPortfolioCorrelation",
    allowFrontendExclusions: true,
    css: 0,
    html: 2,
    excluded: 8,
  },
  {
    domain: "project",
    js: 2,
    plugin: "ResultsRobustnessTests",
    allowFrontendExclusions: true,
    css: 0,
    html: 2,
    excluded: 9,
  },
  {
    domain: "project",
    js: 1,
    plugin: "ResultsStockpicker",
    allowFrontendExclusions: true,
    css: 0,
    html: 1,
    excluded: 4,
  },
];
describe("databank bounded structural inventories", () => {
  for (const scope of scopes)
    it(scope.plugin, () => {
      const prefix = root + scope.plugin + "/";
      const mapping = JSON.parse(
        rawFiles[prefix + "source-map.json"],
      ) as SourceMapping;
      const childRoots = Object.keys(rawFiles)
        .filter(
          (path) =>
            path.startsWith(prefix) &&
            path.endsWith("/source-map.json") &&
            path !== prefix + "source-map.json",
        )
        .map((path) => path.slice(0, -"source-map.json".length));
      const files = Object.keys(rawFiles)
        .filter(
          (path) =>
            path.startsWith(prefix) &&
            !childRoots.some((child) => path.startsWith(child)),
        )
        .map((path) => path.slice(prefix.length));
      expect(validateSourceMapping(mapping, files, registry, scope)).toEqual(
        [],
      );
      const drift = structuredClone(mapping);
      drift.sources[0].sha256 = "invalid";
      expect(validateSourceMapping(drift, files, registry, scope)).toContain(
        "Invalid fingerprint",
      );
      expect(
        validateSourceMapping(
          mapping,
          [...files, "unclassified.ts"],
          registry,
          scope,
        ),
      ).toContain("Unclassified target file: unclassified.ts");
    });
});
