/// <reference types="vite/client" />
import { describe, expect, it } from 'vitest';
import sourceMap from '../../../../app/plugins/databank/ProjectDatabanks/source-map.json';
import { validateSourceMapping } from './sourceMappingValidation';
import { DatabankSplitter, DatabankPanel } from '../../../../app/plugins/databank/ProjectDatabanks/module';
import { useDatabanksPane } from '../../../../app/plugins/databank/ProjectDatabanks/DatabanksCtrl';
import { useDatabankPanel } from '../../../../app/plugins/databank/ProjectDatabanks/DatabankCtrl';
import registry from '../../../../app/plugins/databank/README.md?raw';
const prefix = '../../../../app/plugins/databank/ProjectDatabanks/';
const rawFiles = import.meta.glob('../../../../app/plugins/databank/ProjectDatabanks/**/*', {
  eager: true,
  query: '?raw',
  import: 'default',
}) as Record<string, string>;
const files = Object.keys(rawFiles).map((path) => path.slice(prefix.length));


describe('ProjectDatabanks structural mapping', () => {
  it('accounts for every source and target with unique exact relative counterparts', () => {
    expect(validateSourceMapping(JSON.parse(JSON.stringify(sourceMap)), files, registry)).toEqual(
      [],
    );
    expect(sourceMap.sources.filter((source) => source.target !== null)).toHaveLength(7);
  });
  it('rejects missing files, casing drift and unclassified target files', () => {
    expect(
      validateSourceMapping(
        sourceMap,
        files.filter((file) => file !== 'views/databanks.tsx'),
        registry,
      ),
    ).toContain('Missing target: views/databanks.tsx');
    expect(
      validateSourceMapping(
        sourceMap,
        files.map((file) => (file === 'views/databanks.tsx' ? 'views/Databanks.tsx' : file)),
        registry,
      ),
    ).not.toEqual([]);
    expect(validateSourceMapping(sourceMap, [...files, 'unknown.ts'], registry)).toContain(
      'Unclassified target file: unknown.ts',
    );
  });
  it('rejects collisions, wrong extensions and absolute paths', () => {
    for (const path of [
      'DatabankService.ts',
      'views/databanks.ts',
      'C:/machine/screen.tsx',
      '../screen.tsx',
    ]) {
      const changed = structuredClone(sourceMap);
      changed.sources.find(
        (source) => source.relative_path === 'views/databanks.html',
      )!.target = path;
      expect(validateSourceMapping(changed, files, registry)).not.toEqual([]);
    }
  });
  it('rejects unresolved ownership, provenance and source IDs', () => {
    expect(validateSourceMapping(sourceMap, files, '')).not.toEqual([]);
    const changed = structuredClone(sourceMap);
    changed.sources[0].catalog_id = 'missing';
    changed.sources[0].sha256 = 'invalid';
    expect(validateSourceMapping(changed, files, registry)).toContain(
      'Unresolved source catalog: missing',
    );
    expect(validateSourceMapping(changed, files, registry)).toContain('Invalid fingerprint');
  });
  it('retains consumed command identities and callable component boundaries', () => {
    for (const component of [DatabankSplitter, DatabankPanel, useDatabanksPane, useDatabankPanel])
      expect(component).toBeTypeOf('function');
  });
});
