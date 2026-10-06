/// <reference types="vite/client" />
import { describe, expect, it } from 'vitest';
import sourceMap from '../../../../../app/plugins/data_source/MetaTrader/source-map.json';
import { validateSourceMapping } from './sourceMappingValidation';
import { mt5Provider } from '../../../../../app/plugins/data_source/MetaTrader/module';
import { useMt5ApiImport } from '../../../../../app/plugins/data_source/MetaTrader/import/DataSourceMt5ApiImportCtrl';
import { ImportPopup } from '../../../../../app/plugins/data_source/MetaTrader/import/module';
const prefix = '../../../../../app/plugins/data_source/MetaTrader/';
const rawFiles = import.meta.glob('../../../../../app/plugins/data_source/MetaTrader/**/*', {
  eager: true,
  query: '?raw',
  import: 'default',
}) as Record<string, string>;
const files = Object.keys(rawFiles).map((path) => path.slice(prefix.length));
const registry = rawFiles[`${prefix}README.md`];

describe('MetaTrader structural mapping', () => {
  it('accounts for every source and target with unique exact relative counterparts', () => {
    expect(validateSourceMapping(JSON.parse(JSON.stringify(sourceMap)), files, registry)).toEqual(
      [],
    );
    expect(sourceMap.sources.filter((source) => source.target !== null)).toHaveLength(6);
  });
  it('rejects missing files, casing drift and unclassified target files', () => {
    expect(
      validateSourceMapping(
        sourceMap,
        files.filter((file) => file !== 'import/importPopup.tsx'),
        registry,
      ),
    ).toContain('Missing target: import/importPopup.tsx');
    expect(
      validateSourceMapping(
        sourceMap,
        files.map((file) => (file === 'import/importPopup.tsx' ? 'import/ImportPopup.tsx' : file)),
        registry,
      ),
    ).not.toEqual([]);
    expect(validateSourceMapping(sourceMap, [...files, 'unknown.ts'], registry)).toContain(
      'Unclassified target file: unknown.ts',
    );
  });
  it('rejects collisions, wrong extensions and absolute paths', () => {
    for (const path of [
      'DataSourceMt5Api.ts',
      'import/importPopup.ts',
      'C:/machine/screen.tsx',
      '../screen.tsx',
    ]) {
      const changed = structuredClone(sourceMap);
      changed.sources.find(
        (source) => source.relative_path === 'import/importPopup.html',
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
    expect(mt5Provider.commands.map((command) => command.id)).toEqual([
      'mt5-import',
    ]);
    for (const component of [ImportPopup, useMt5ApiImport])
      expect(component).toBeTypeOf('function');
  });
});
