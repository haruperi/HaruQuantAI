export interface SourceMapping {
  schema_version: number;
  donor_root: string;
  target_root: string;
  source_head: string;
  review: { reference: string; state: string; version: number };
  owner: {
    domain: string;
    feature: string;
    decision: string;
    requirements: string[];
  };
  clean_room: {
    contains_proprietary_source: boolean;
    contains_sensitive_data: boolean;
    contains_personal_data: boolean;
    paraphrased_behavior_only: boolean;
  };
  source_catalog: { id: string; locator: string; family: string }[];
  sources: {
    catalog_id: string;
    artifact_locator: string;
    relative_path: string;
    location: string;
    inspection_method: string;
    relation: string;
    limitation: string;
    access_date: string;
    sha256: string;
    target: string | null;
    classification: string;
  }[];
  target_only: { path: string; reason: string }[];
}
export interface MappingScope {
  plugin: string;
  domain?: string;
  html: number;
  js: number;
  css: number;
  excluded: number;
  allowFrontendExclusions?: boolean;
}
/** Validate bounded inventories; completed cohorts remain strict by default. */
export function validateSourceMapping(
  mapping: SourceMapping,
  targetFiles: readonly string[],
  registry: string,
  scope: MappingScope = {
    plugin: "ProjectDatabanks",
    html: 2,
    js: 4,
    css: 1,
    excluded: 0,
  },
): string[] {
  const errors: string[] = [];
  const fail = (message: string): void => {
    errors.push(message);
  };
  const relative = (path: string): boolean =>
    path.length > 0 &&
    !path.startsWith("/") &&
    !path.includes(String.fromCharCode(92)) &&
    !path.includes(":") &&
    !path
      .split("/")
      .some((part) => part === ".." || part === "." || part === "");
  const domain = scope.domain ?? "databank";
  if (mapping.schema_version !== 1) fail("Unsupported mapping version");
  if (
    mapping.donor_root !==
      `SQX_REFERENCE_ROOT/internal/plugins/${scope.plugin}` ||
    mapping.target_root !==
      `HARUQUANTAI_ROOT/ui/app/plugins/${domain}/${scope.plugin}`
  )
    fail("Invalid logical roots");
  if (!/^[a-f0-9]{40}$/.test(mapping.source_head))
    fail("Invalid source commit");
  if (
    mapping.clean_room.contains_proprietary_source !== false ||
    mapping.clean_room.contains_sensitive_data !== false ||
    mapping.clean_room.contains_personal_data !== false ||
    mapping.clean_room.paraphrased_behavior_only !== true
  )
    fail("Invalid clean-room policy");
  if (
    !mapping.review.reference.startsWith("HARUQUANTAI_ROOT/.agents/logs/") ||
    mapping.review.state !== "owner-approved-plan" ||
    mapping.review.version < 1
  )
    fail("Invalid plan review");
  const catalog = new Set(mapping.source_catalog.map((entry) => entry.id));
  if (catalog.size !== mapping.source_catalog.length)
    fail("Duplicate source catalog ID");
  for (const entry of mapping.source_catalog)
    if (entry.locator !== mapping.donor_root || !entry.family)
      fail("Invalid catalog locator");
  const ownerIds = new Set(
    registry.match(/\b(?:FEAT|FR|DEC)-[A-Za-z0-9_-]+\b/g) ?? [],
  );
  for (const id of [
    mapping.owner.feature,
    ...mapping.owner.requirements,
    mapping.owner.decision,
  ])
    if (!ownerIds.has(id)) fail(`Unresolved owner ID: ${id}`);
  const sources = new Set<string>();
  const targets = new Set<string>();
  const counts = { html: 0, js: 0, css: 0, excluded: 0 };
  const files = new Set(targetFiles);
  if (files.size !== targetFiles.length) fail("Duplicate target inventory");
  for (const source of mapping.sources) {
    if (!relative(source.relative_path) || sources.has(source.relative_path))
      fail(`Invalid/duplicate source: ${source.relative_path}`);
    sources.add(source.relative_path);
    if (!catalog.has(source.catalog_id))
      fail(`Unresolved source catalog: ${source.catalog_id}`);
    if (
      source.artifact_locator !==
      `${mapping.donor_root}/${source.relative_path}`
    )
      fail("Invalid artifact locator");
    if (!/^[a-f0-9]{64}$/.test(source.sha256)) fail("Invalid fingerprint");
    if (
      !source.location ||
      !source.inspection_method ||
      !source.relation ||
      !source.limitation ||
      !/^\d{4}-\d{2}-\d{2}$/.test(source.access_date)
    )
      fail("Incomplete source provenance");
    const extension = source.relative_path.split(".").at(-1);
    const frontend =
      extension === "html" || extension === "js" || extension === "css";
    if (source.classification === "excluded") {
      if (
        source.target !== null ||
        (frontend && !scope.allowFrontendExclusions)
      )
        fail(`Invalid exclusion: ${source.relative_path}`);
      counts.excluded++;
    } else if (frontend) {
      const expected = source.relative_path.replace(
        /\.(html|js)$/,
        extension === "html" ? ".tsx" : ".ts",
      );
      if (source.classification !== "counterpart" || source.target !== expected)
        fail(`Incorrect counterpart: ${source.relative_path}`);
      counts[extension]++;
    } else fail("Invalid exclusion");
    if (source.target !== null) {
      if (!relative(source.target) || targets.has(source.target))
        fail(`Invalid/duplicate target: ${source.target}`);
      if (!files.has(source.target)) fail(`Missing target: ${source.target}`);
      targets.add(source.target);
    }
  }
  for (const entry of mapping.target_only) {
    if (!relative(entry.path) || targets.has(entry.path) || !entry.reason)
      fail(`Invalid target-only entry: ${entry.path}`);
    if (!files.has(entry.path)) fail(`Missing target-only file: ${entry.path}`);
    targets.add(entry.path);
  }
  for (const file of files)
    if (!targets.has(file)) fail(`Unclassified target file: ${file}`);
  if (
    counts.html !== scope.html ||
    counts.js !== scope.js ||
    counts.css !== scope.css ||
    counts.excluded !== scope.excluded
  )
    fail("Incomplete scoped donor inventory");
  return errors;
}
