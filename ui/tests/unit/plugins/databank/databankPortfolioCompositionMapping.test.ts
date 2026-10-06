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
    js: 1,
    plugin: "ResultsDatabankActions/portfolio/merge",
    allowFrontendExclusions: true,
    css: 0,
    html: 0,
    excluded: 3,
  },
  {
    domain: "databank",
    js: 1,
    plugin: "ResultsDatabankActions/portfolio/mergeWF",
    allowFrontendExclusions: true,
    css: 0,
    html: 0,
    excluded: 0,
  },
  {
    domain: "databank",
    js: 1,
    plugin: "ResultsDatabankActions/portfolio/moveToPC",
    allowFrontendExclusions: true,
    css: 0,
    html: 0,
    excluded: 0,
  },
  {
    domain: "databank",
    js: 1,
    plugin: "ResultsDatabankActions/portfolio/moveToPM",
    allowFrontendExclusions: true,
    css: 0,
    html: 0,
    excluded: 0,
  },
  {
    domain: "databank",
    js: 1,
    plugin: "ResultsDatabankActions/portfolio/split",
    allowFrontendExclusions: true,
    css: 0,
    html: 0,
    excluded: 0,
  },
  {
    domain: "databank",
    js: 1,
    plugin: "ResultsDatabankActions/portfolio",
    allowFrontendExclusions: true,
    css: 0,
    html: 0,
    excluded: 0,
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
