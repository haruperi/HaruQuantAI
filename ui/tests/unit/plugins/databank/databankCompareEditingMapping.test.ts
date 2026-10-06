import { describe, expect, it } from "vitest";
import {
  validateSourceMapping,
  type SourceMapping,
  type MappingScope,
} from "../databank/sourceMappingValidation";
import registry from "../../../../app/plugins/databank/README.md?raw";
const root = "../../../../app/plugins/databank/";
const rawFiles = import.meta.glob("../../../../app/plugins/databank/**/*", {
  eager: true,
  query: "?raw",
  import: "default",
}) as Record<string, string>;
const scopes: MappingScope[] = [
  {
    domain: "databank",
    allowFrontendExclusions: true,
    html: 1,
    js: 4,
    excluded: 1,
    plugin: "ResultsDatabankActions/tools/compareStrategies",
    css: 0,
  },
  {
    domain: "databank",
    allowFrontendExclusions: true,
    html: 0,
    js: 2,
    excluded: 4,
    plugin: "ResultsDatabankActions/tools/edit/editParameters",
    css: 0,
  },
  {
    domain: "databank",
    allowFrontendExclusions: true,
    html: 0,
    js: 2,
    excluded: 0,
    plugin: "ResultsDatabankActions/tools/edit/editStrategy",
    css: 0,
  },
  {
    domain: "databank",
    allowFrontendExclusions: true,
    html: 0,
    js: 1,
    excluded: 0,
    plugin: "ResultsDatabankActions/tools/edit",
    css: 0,
  },
  {
    domain: "databank",
    allowFrontendExclusions: true,
    html: 0,
    js: 2,
    excluded: 3,
    plugin: "ResultsDatabankActions/tools/runCa",
    css: 0,
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
