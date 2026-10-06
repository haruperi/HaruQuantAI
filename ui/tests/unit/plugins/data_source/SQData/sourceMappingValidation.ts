import sourceMap from '../../../../../app/plugins/data_source/SQData/Equity/source-map.json';

export type SourceMapping = typeof sourceMap;

/** Validate the pilot's bounded structural contract, independently of rendering. */
export function validateSourceMapping(
  mapping: SourceMapping,
  targetFiles: readonly string[],
  registry: string,
): string[] {
  const errors: string[] = [];
  const fail = (message: string): void => {
    errors.push(message);
  };
  const relative = (path: string): boolean =>
    path.length > 0 &&
    !path.startsWith('/') &&
    !path.includes('\\') &&
    !path.includes(':') &&
    !path.split('/').some((part) => part === '..' || part === '.' || part === '');
  if (mapping.schema_version !== 1) fail('Unsupported mapping version');
  if (
    !['Equity', 'Futures'].some(provider => mapping.donor_root === `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQ${provider}Data` && mapping.target_root === `HARUQUANTAI_ROOT/ui/app/plugins/data_source/SQData/${provider}`)
  )
    fail('Invalid logical roots');
  if (!/^[a-f0-9]{40}$/.test(mapping.source_head)) fail('Invalid source commit');
  if (
    mapping.clean_room.contains_proprietary_source ||
    mapping.clean_room.contains_sensitive_data ||
    mapping.clean_room.contains_personal_data ||
    !mapping.clean_room.paraphrased_behavior_only
  )
    fail('Invalid clean-room policy');
  const catalog = new Set(mapping.source_catalog.map((entry) => entry.id));
  if (catalog.size !== mapping.source_catalog.length) fail('Duplicate source catalog ID');
  for (const entry of mapping.source_catalog) {
    if (entry.locator !== mapping.donor_root) fail('Invalid catalog locator');
  }
  for (const id of [mapping.owner.feature, ...mapping.owner.requirements, mapping.owner.decision]) {
    if (!registry.includes(id)) fail(`Unresolved owner ID: ${id}`);
  }
  const sources = new Set<string>();
  const targets = new Set<string>();
  const counts = { html: 0, js: 0, css: 0, excluded: 0 };
  const files = new Set(targetFiles);
  for (const source of mapping.sources) {
    if (!relative(source.relative_path) || sources.has(source.relative_path))
      fail(`Invalid/duplicate source: ${source.relative_path}`);
    sources.add(source.relative_path);
    if (!catalog.has(source.catalog_id)) fail(`Unresolved source catalog: ${source.catalog_id}`);
    if (source.artifact_locator !== `${mapping.donor_root}/${source.relative_path}`)
      fail('Invalid artifact locator');
    if (!/^[a-f0-9]{64}$/.test(source.sha256)) fail('Invalid fingerprint');
    if (
      !source.location ||
      !source.inspection_method ||
      !source.relation ||
      !source.limitation ||
      !/^\d{4}-\d{2}-\d{2}$/.test(source.access_date)
    )
      fail('Incomplete source provenance');
    const extension = source.relative_path.split('.').at(-1);
    const emptyTemplate = source.relative_path === 'update/updatePopup.html' && source.byte_size === 0;
    const counterpart = !emptyTemplate && (extension === 'html' || extension === 'js' || extension === 'css');
    if (counterpart) {
      const expected = source.relative_path.replace(
        /\.(html|js)$/,
        extension === 'html' ? '.tsx' : '.ts',
      );
      if (source.classification !== 'counterpart' || source.target !== expected)
        fail(`Incorrect counterpart: ${source.relative_path}`);
      counts[extension]++;
    } else {
      if (source.classification !== 'excluded' || source.target !== null) fail('Invalid exclusion');
      counts.excluded++;
    }
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
  for (const file of files) {
    if (!targets.has(file)) fail(`Unclassified target file: ${file}`);
  }
  if (counts.html !== 2 || counts.js !== 6 || counts.css !== 1 || counts.excluded !== 2)
    fail('Incomplete scoped donor inventory');
  return errors;
}
