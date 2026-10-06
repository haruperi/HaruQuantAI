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
    allowFrontendExclusions: true,
    html: 3,
    js: 2,
    excluded: 14,
    plugin: "EnginePanel",
    css: 1,
  },
  {
    domain: "project",
    allowFrontendExclusions: true,
    html: 1,
    js: 1,
    excluded: 3,
    plugin: "ProjectSettings",
    css: 0,
  },
  {
    domain: "project",
    allowFrontendExclusions: true,
    html: 1,
    js: 2,
    excluded: 1,
    plugin: "SettingsPanel",
    css: 0,
  },
  {
    domain: "project",
    allowFrontendExclusions: true,
    html: 2,
    js: 2,
    excluded: 0,
    plugin: "ProjectResults",
    css: 1,
  },
  {
    domain: "project",
    allowFrontendExclusions: true,
    html: 2,
    js: 4,
    excluded: 2,
    plugin: "ResultsEquityChart",
    css: 1,
  },
  {
    domain: "project",
    allowFrontendExclusions: true,
    html: 1,
    js: 2,
    excluded: 8,
    plugin: "ResultsOverview",
    css: 1,
  },
  {
    domain: "project",
    allowFrontendExclusions: true,
    html: 1,
    js: 2,
    excluded: 1,
    plugin: "ResultsTradeList",
    css: 1,
  },
  {
    domain: "project",
    allowFrontendExclusions: true,
    html: 1,
    js: 2,
    excluded: 3,
    plugin: "ResultsTradelistViews",
    css: 0,
  },
  {
    domain: "project",
    allowFrontendExclusions: true,
    html: 1,
    js: 2,
    excluded: 2,
    plugin: "ResultsProfileChart",
    css: 0,
  },
  {
    domain: "project",
    allowFrontendExclusions: true,
    html: 1,
    js: 2,
    excluded: 4,
    plugin: "ResultsSourceCode",
    css: 1,
  },
  {
    domain: "project",
    allowFrontendExclusions: true,
    html: 2,
    js: 2,
    excluded: 13,
    plugin: "ResultsSPOverview",
    css: 1,
  },
  {
    domain: "project",
    allowFrontendExclusions: true,
    html: 1,
    js: 1,
    excluded: 3,
    plugin: "ResultsStrategyConfig",
    css: 1,
  },
  {
    domain: "project",
    allowFrontendExclusions: true,
    html: 2,
    js: 2,
    excluded: 4,
    plugin: "ResultsTradeAnalysis",
    css: 1,
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
