/// <reference types="vite/client" />
import { describe, expect, it } from 'vitest';
import sourceMap from '../../../../../app/plugins/data_source/Yahoo/source-map.json';
import { validateSourceMapping } from './sourceMappingValidation';
import { yahooProvider } from '../../../../../app/plugins/data_source/Yahoo/module';
import { useYahooAdd } from '../../../../../app/plugins/data_source/Yahoo/add/addPopupCtrl';
import { YahooAddDialog } from '../../../../../app/plugins/data_source/Yahoo/add/module';
import { YahooDownloadDialog } from '../../../../../app/plugins/data_source/Yahoo/download/module';
import { useYahooDownload } from '../../../../../app/plugins/data_source/Yahoo/download/downloadPopupCtrl';
const prefix = '../../../../../app/plugins/data_source/Yahoo/';
const rawFiles = import.meta.glob('../../../../../app/plugins/data_source/Yahoo/**/*', {
  eager: true,
  query: '?raw',
  import: 'default',
}) as Record<string, string>;
const files = Object.keys(rawFiles).map((path) => path.slice(prefix.length));
const registry = rawFiles[`${prefix}README.md`];

describe('Yahoo structural mapping', () => {
  it('accounts for every source and target with unique exact relative counterparts', () => {
    expect(validateSourceMapping(JSON.parse(JSON.stringify(sourceMap)), files, registry)).toEqual(
      [],
    );
    expect(sourceMap.sources.filter((source) => source.target !== null)).toHaveLength(9);
  });
  it('rejects missing files, casing drift and unclassified target files', () => {
    expect(
      validateSourceMapping(
        sourceMap,
        files.filter((file) => file !== 'add/addPopup.tsx'),
        registry,
      ),
    ).toContain('Missing target: add/addPopup.tsx');
    expect(
      validateSourceMapping(
        sourceMap,
        files.map((file) => (file === 'add/addPopup.tsx' ? 'import/YahooAddDialog.tsx' : file)),
        registry,
      ),
    ).not.toEqual([]);
    expect(validateSourceMapping(sourceMap, [...files, 'unknown.ts'], registry)).toContain(
      'Unclassified target file: unknown.ts',
    );
  });
  it('rejects collisions, wrong extensions and absolute paths', () => {
    for (const path of [
      'YahooService.ts',
      'add/addPopup.ts',
      'C:/machine/screen.tsx',
      '../screen.tsx',
    ]) {
      const changed = structuredClone(sourceMap);
      changed.sources.find(
        (source) => source.relative_path === 'add/addPopup.html',
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
    expect(yahooProvider.commands.map((command) => command.id)).toEqual([
      'yahoo-add', 'yahoo-download',
    ]);
    for (const component of [YahooAddDialog, useYahooAdd, YahooDownloadDialog, useYahooDownload])
      expect(component).toBeTypeOf('function');
  });
});
